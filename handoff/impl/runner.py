import datetime, json, logging, os, sys, subprocess, venv
import yaml

from handoff.aws_utils import s3, ssm
from handoff.impl  import impl, utils
from handoff.impl.pyvenvx import ExtendedEnvBuilder

LOGGER = utils.get_logger(__name__)

LOCAL_DIR = ".local"
ENV_DIR = ".env"
ARTIFACTS_DIR = ".artifacts"


def _download_config_from_s3_bucket():
    s3.download_dir(os.path.join(os.environ.get("STACK_NAME"), ENV_DIR) + "/",
                    ENV_DIR,
                    os.environ.get("S3_BUCKET_NAME"))
    s3.download_dir(os.path.join(os.environ.get("STACK_NAME"), ARTIFACTS_DIR + "/"),
                    ARTIFACTS_DIR,
                    os.environ.get("S3_BUCKET_NAME"))


def _upload_artifacts_to_s3_bucket(local_dir=ARTIFACTS_DIR, outdir = ARTIFACTS_DIR):
    d = datetime.datetime.utcnow()
    prefix = os.path.join(os.environ.get("STACK_NAME"), outdir)
    s3.upload_dir(local_dir, prefix, os.environ.get("S3_BUCKET_NAME"))


def read_parameters(parameter_file=None):
    """
    Read parameters from a file if a file name is given.
    Read them from AWS SSM otherwise.
    """
    if parameter_file:
        if not os.path.isfile(parameter_file):
            raise ValueError(parameter_file + " not found.")
        LOGGER.info("Reading parameters from file: " + parameter_file)
        with open(parameter_file, "r") as f:
            params = json.load(f)
    else:
        LOGGER.info("Reading parameters from SSM.")
        params = json.loads(ssm.get_parameter(os.environ.get("STACK_NAME"), "params"))

    return params


def load_parameters(parameter_file=None):
    """
    Set parameters to environment variables and config files
    Returns the params dict
    """
    params = read_parameters(parameter_file)

    if not os.path.isdir(ENV_DIR):
        os.mkdir(ENV_DIR)
    config_dir = os.path.join(ENV_DIR, "config")
    if not os.path.isdir(config_dir):
        os.mkdir(config_dir)

    for r in params.get("envs", []):
        os.environ[r["key"]] = r["value"]

    for r in params.get("files", []):
        with open(os.path.join(config_dir, r["name"]), "w") as f:
            f.write(r["value"])

    return params


def _read_project(project_file):
    # load commands from yaml file
    with open(project_file, "r") as f:
        project = yaml.load(f, Loader=yaml.FullLoader)
    return project


def generate_parameters(local_dir=LOCAL_DIR):
    """ Generate parameters file

    The output JSON file describes the commands and arguments for each process.
    It also contains the environment variables for the run-time.
    JSON format configuration files are encoded into the output JSON so they
    can be restored in the docker instance when it runs.

    The parameters file may contain secrets and it should kept private. (i.e.
    don't commit to a repository and etc.)

    This parameters file is encrypted and stored in AWS SSM via
    put_ssm_parameters command and downloaded at the run-time.

    - local_dir: The local directory that contains:
      - project.yml
      - *.json: JSON format configuration files necessary for each process.
        (e.g. singer tap/target config files, Google Cloud Platform secret file)

    Example project.yml:
    ```
    commands:
      - command: tap_rest_api
        args: ".env/rest_api_spec.json --config .env/config/tap_config.json --schema_dir .env/schema --catalog .env/catalog/default.json --state .artifacts/state --start_datetime '{start_at}' --end_datetime '{end_at}'"
        venv: "./venv/proc_01"
      - command: "./impl/collector_stats.py"
      - command: target_gcs
        args: "--config .env/config/target_config.json"
        venv: "./venv/proc_02"
    envs:
      - key: "GOOGLE_APPLICATION_CREDENTIALS"
        value: ".env/config/google_client_secret.json"
    ```
    """
    params = dict()
    project = _read_project(os.path.join(local_dir, "project.yml"))
    params.update(project)

    params["files"] = list()
    json_files = [fn for fn in os.listdir(local_dir) if os.path.isfile(os.path.join(local_dir, fn)) and fn[-5:] == ".json"]

    for json_file in json_files:
        with open(os.path.join(local_dir, json_file)) as f:
            config_str = f.read().replace('"', "\"")
            params["files"].append({"name": json_file, "value": config_str})
    return json.dumps(params)


def put_ssm_parameters(parameter_file=None, local_dir=LOCAL_DIR, allow_advanced_tier=False):
    if not parameter_file:
        LOGGER.info("Generating parameters from the config files at %s." % local_dir)
        params = generate_parameters(local_dir)
    else:
        LOGGER.info("Reading parameters from %s." % parameter_file)
        params = json.dumps(read_parameters(parameter_file=parameter_file))
    LOGGER.info("Uploading parameters to %s." % os.environ.get("STACK_NAME"))

    tier = "Standard"
    if len(params) > 8192:
        raise Exception("Parameter string must be less than 8192kb!")
    if len(params) > 4096:
        if allow_advanced_tier:
            tier = "Advanced"
        else:
            raise Exception("Parameter string is %s > 4096 byte and allow_advanced_tier=False" % len(params))
    ssm.put_parameter(os.environ.get("STACK_NAME"), "params", params, tier=tier)


def dump_ssm_parameters():
    print(json.dumps(read_parameters()))


def _install(venv_path, install):
    if os.path.exists(venv_path):
        LOGGER.warn("%s already exists. Skipping python -m venv..." % venv_path)
    else:
        paths = venv_path.split("/")
        for i in range(1, len(paths)):
            path = "/".join(paths[0:i])
            if not os.path.exists(path):
                os.mkdir(path)
        builder = ExtendedEnvBuilder()
        builder.create(venv_path)

    command = '/bin/bash -c "source {venv}/bin/activate && pip install wheel && {install}"'.format(
        **{"venv": venv_path, "install": install})
    LOGGER.info("Running %s" % command)
    p = subprocess.Popen([command],
                         # stdout=subprocess.PIPE,
                         shell=True)
    p.wait()


def mkvenvs(parameter_file=None):
    params = read_parameters(parameter_file)

    for command in params["commands"]:
        for install in command.get("installs", []):
            _install(command["venv"], install)


def run(command, data, parameter_file=None, upload_artifacts=True):
    """
    """
    if not os.path.isdir(ARTIFACTS_DIR):
        os.mkdir(ARTIFACTS_DIR)

    # I don't want to stdout anything when I generate parameter file. So do this here.
    if command == "generate_parameters":
        print(generate_parameters())
        return

    LOGGER.info("Running " + command + " data:" + str(data))

    if command == "mkvenvs":
        mkvenvs(parameter_file)
        return

    if command == "put_ssm_parameters":
        put_ssm_parameters(parameter_file)
        return
    if command == "dump_ssm_parameters":
        dump_ssm_parameters()
        return
    if command == "load_parameters":
        LOGGER.info("Loading parameters and writing out config files")
        load_parameters(parameter_file)
        return
    if command == "download_config":
        LOGGER.info("Downloading from S3 " + os.environ.get("S3_BUCKET_NAME"))
        _download_config_from_s3_bucket()
        return
    if command == "delete_artifacts":
        LOGGER.info("Deleting artifacts from S3 " + os.environ.get("S3_BUCKET_NAME"))
        s3.delete_recurse(os.environ.get("S3_BUCKET_NAME"),
                          os.path.join(os.environ.get("STACK_NAME"),
                                       ARTIFACTS_DIR))
        return

    if os.environ.get("S3_BUCKET_NAME"):
        LOGGER.info("Downloading from S3 " + os.environ.get("S3_BUCKET_NAME"))
        _download_config_from_s3_bucket()

    # Search in impl.py for available commands
    commands = dict()
    impl_obj = dir(impl)
    for name in impl_obj:
        if name[0] == "_":
            continue
        obj = getattr(impl, name)
        if callable(obj):
            commands[name] = obj

    if command not in commands:
        raise ValueError("Invalid command: %s\nAvailable commands are %s" %
                         (command, [x for x in commands.keys()]))

    LOGGER.info("Running " + command)

    params = load_parameters(parameter_file)

    start = datetime.datetime.utcnow()
    LOGGER.info("Job started at " + str(start))

    # Run the command
    commands[command](params, data)

    end = datetime.datetime.utcnow()
    LOGGER.info("Job ended at " + str(end))
    duration = end - start
    LOGGER.info("Processed in " + str(duration))

    if upload_artifacts:
        if not os.environ.get("S3_BUCKET_NAME"):
            raise Exception("Cannot upload artifacts. S3_BUCKET_NAME is not set")
        _upload_artifacts_to_s3_bucket(ARTIFACTS_DIR)

