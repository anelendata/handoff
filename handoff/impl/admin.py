import datetime, json, logging, os, sys, subprocess, venv
import yaml

from handoff.aws_utils import s3, ssm
from handoff.impl  import runner, utils
from handoff.impl.pyvenvx import ExtendedEnvBuilder

LOGGER = utils.get_logger(__name__)

PROJECT_FILE = "project.yml"
CONFIG_DIR = "config"
FILES_DIR = "files"
ARTIFACTS_DIR = "artifacts"


def load_parameters(parameter_file=None):
    """
    Not used

    Set parameters to environment variables and config files
    Returns the params dict
    """
    params = read_parameters(parameter_file)

    if not os.path.isdir(CONFIG_DIR):
        os.mkdir(CONFIG_DIR)
    config_dir = os.path.join(CONFIG_DIR, "config")
    if not os.path.isdir(config_dir):
        os.mkdir(config_dir)

    for r in params.get("envs", []):
        os.environ[r["key"]] = r["value"]

    for r in params.get("files", []):
        with open(os.path.join(config_dir, r["name"]), "w") as f:
            f.write(r["value"])

    return params



def _check_env_vars():
    if not os.environ.get("S3_BUCKET_NAME"):
        raise Exception("Set S3_BUCKET_NAME env")
    if not os.environ.get("STACK_NAME"):
        raise Exception("Set STACK_NAME env")


def _get_workspace_dirs(workspace_dir):
    config_dir = os.path.join(workspace_dir, CONFIG_DIR)
    artifacts_dir = os.path.join(workspace_dir, ARTIFACTS_DIR)
    files_dir = os.path.join(workspace_dir, FILES_DIR)
    return config_dir, artifacts_dir, files_dir


def _read_project(project_file, workspace_dir):
    # load commands from yaml file
    with open(project_file, "r") as f:
        project = yaml.load(f, Loader=yaml.FullLoader)

    print(project)
    return project

    ######
    if not workspace_dir:
        return project

    for i in range(0, len(project["commands"])):
        if not project["commands"][i].get("venv"):
            continue
        project["commands"][i]["venv"] = os.path.join(workspace_dir, project["commands"][i]["venv"])
        if not project["commands"][i].get("file"):
            continue
        project["commands"][i]["venv"] = os.path.join(workspace_dir, project["commands"][i]["venv"])


    return project


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


def _read_precompiled_config(precompiled_config_file=None):
    """
    Read parameters from a file if a file name is given.
    Read them from AWS SSM otherwise.
    """
    if precompiled_config_file:
        if not os.path.isfile(precompiled_config_file):
            raise ValueError(precompiled_config_file + " not found.")
        LOGGER.info("Reading precompiled config from: " + precompiled_config_file)
        with open(precompiled_config_file, "r") as f:
            config = json.load(f)
    else:
        LOGGER.info("Reading precompiled config from remote.")
        config = json.loads(ssm.get_parameter(os.environ.get("STACK_NAME"), "config"))
    return config


def _compile_config(project_dir, workspace_dir):
    """ Compile configuration JSON file from the project.yml

    The output JSON file describes the commands and arguments for each process.
    It also contains the environment variables for the run-time.
    JSON format configuration files are encoded into the output JSON so they
    can be restored in the docker instance when it runs.

    The parameters file may contain secrets and it should kept private. (i.e.
    don't commit to a repository and etc.)

    This parameters file is encrypted and stored in AWS SSM via
    put_ssm_parameters command and downloaded at the run-time.

    - project_dir: The project directory that contains:
      - project.yml
      - *.json: JSON format configuration files necessary for each process.
        (e.g. singer tap/target config files, Google Cloud Platform secret file)

    Example project.yml:
    ```
    commands:
      - command: tap_rest_api
        args: "files/rest_api_spec.json --config config/tap_config.json --schema_dir files/schema --catalog files/catalog/default.json --state .artifacts/state --start_datetime '{start_at}' --end_datetime '{end_at}'"
        venv: "proc_01"
      - command: target_gcs
        args: "--config config/target_config.json"
        venv: "proc_02"
    envs:
      - key: "GOOGLE_APPLICATION_CREDENTIALS"
        value: "config/google_client_secret.json"
    ```
    """
    params = dict()
    project = _read_project(os.path.join(project_dir, "project.yml"), workspace_dir)
    params.update(project)

    params["files"] = list()
    json_files = [fn for fn in os.listdir(project_dir) if os.path.isfile(os.path.join(project_dir, fn)) and fn[-5:] == ".json"]

    for json_file in json_files:
        with open(os.path.join(project_dir, json_file)) as f:
            config_str = f.read().replace('"', "\"")
            params["files"].append({"name": json_file, "value": config_str})
    return json.dumps(params)


def push_artifacts(project_dir, workspace_dir, data):
    _check_env_vars()
    _, artifacts_dir, _ = _get_workspace_dirs(workspace_dir)
    d = datetime.datetime.utcnow()
    prefix = os.path.join(os.environ.get("STACK_NAME"), ARTIFACTS_DIR)
    s3.upload_dir(artifacts_dir, prefix, os.environ.get("S3_BUCKET_NAME"))


def push_files(project_dir, workspace_dir, data):
    """ Push the contents of workspace_dir/FILES_DIR to remote storage"""
    _check_env_vars()
    _, _, files_dir = _get_workspace_dirs(workspace_dir)
    d = datetime.datetime.utcnow()
    prefix = os.path.join(os.environ.get("STACK_NAME"), FILES_DIR)
    s3.upload_dir(files_dir, prefix, os.environ.get("S3_BUCKET_NAME"))


def push_config(project_dir, workspace_dir, data, allow_advanced_tier=False):
    """ Push the contents of project_dir as a secure parameter key"""
    precompiled_file = data.get("config")
    if precompiled_file:
        LOGGER.info("Reading config from the precompiled JSON file %s." % parameter_file)
        config = json.dumps(_read_precompiled_config(parameter_file=parameter_file))
    else:
        LOGGER.info("Compiling config from %s" % project_dir)
        config = _compile_config(project_dir, workspace_dir)

    LOGGER.info("Uploading config to %s." % os.environ.get("STACK_NAME"))

    tier = "Standard"
    if len(config) > 8192:
        raise Exception("Parameter string must be less than 8192kb!")
    if len(config) > 4096:
        if allow_advanced_tier:
            tier = "Advanced"
        else:
            raise Exception("Parameter string is %s > 4096 byte and allow_advanced_tier=False" % len(config))
    ssm.put_parameter(os.environ.get("STACK_NAME"), "config", config, tier=tier)


def install(project_dir, workspace_dir, data):
    """
    Install dependencies in the local virtual environment
    """
    project = _read_project(os.path.join(project_dir, PROJECT_FILE), workspace_dir)
    os.chdir(workspace_dir)
    for command in project["commands"]:
        for install in command.get("installs", []):
            _install(os.path.join(command["venv"]), install)



def get_config(project_dir, workspace_dir, data):
    _check_env_vars()
    config_dir, _, _ = _get_workspace_dirs(workspace_dir)
    precompiled_config = _read_precompiled_config()
    for r in precompiled_config.get("files", []):
        with open(os.path.join(config_dir, r["name"]), "w") as f:
            f.write(r["value"])

    return precompiled_config


def print_config(project_dir, workspace_dir, data):
    print(json.dumps(get_config(project_dir, workspace_dir, data)))


def get_artifacts(project_dir, workspace_dir, data):
    _check_env_vars()
    _, artifacts_dir, _ = _get_workspace_dirs(workspace_dir)
    s3.download_dir(os.path.join(os.environ.get("STACK_NAME"), ARTIFACTS_DIR + "/"),
                    artifacts_dir,
                    os.environ.get("S3_BUCKET_NAME"))

def get_files(project_dir, workspace_dir, data):
    _check_env_vars()
    _, _, files_dir = _get_workspace_dirs(workspace_dir)
    s3.download_dir(os.path.join(os.environ.get("STACK_NAME"), FILES_DIR + "/"),
                    files_dir,
                    os.environ.get("S3_BUCKET_NAME"))


def get_workspace(project_dir, workspace_dir, data):
    get_config(project_dir, workspace_dir, data)
    get_artifacts(project_dir, workspace_dir, data)
    get_files(project_dir, workspace_dir, data)


def delete_config(project_dir, workspace_dir, data):
    _check_env_vars()
    LOGGER.info("Deleting config files from S3 " + os.environ.get("S3_BUCKET_NAME"))
    s3.delete_recurse(os.environ.get("S3_BUCKET_NAME"),
                      os.path.join(os.environ.get("STACK_NAME"),
                                   CONFIG_DIR))


def delete_artifacts(project_dir, workspace_dir, data):
    _check_env_vars()
    LOGGER.info("Deleting artifacts from S3 " + os.environ.get("S3_BUCKET_NAME"))
    s3.delete_recurse(os.environ.get("S3_BUCKET_NAME"),
                      os.path.join(os.environ.get("STACK_NAME"),
                                   ARTIFACTS_DIR))


def delete_files(project_dir, workspace_dir, data):
    _check_env_vars()
    LOGGER.info("Deleting files from S3 " + os.environ.get("S3_BUCKET_NAME"))
    s3.delete_recurse(os.environ.get("S3_BUCKET_NAME"),
                      os.path.join(os.environ.get("STACK_NAME"),
                                   FILES_DIR))

def delete_(project_dir, workspace_dir, data):
    _check_env_vars()
    LOGGER.info("Deleting artifacts from S3 " + os.environ.get("S3_BUCKET_NAME"))
    s3.delete_recurse(os.environ.get("S3_BUCKET_NAME"),
                      os.path.join(os.environ.get("STACK_NAME")))


def init_workspace(project_dir, workspace_dir, data):
    config_dir = os.path.join(workspace_dir, CONFIG_DIR)
    artifacts_dir = os.path.join(workspace_dir, ARTIFACTS_DIR)
    files_dir = os.path.join(workspace_dir, FILES_DIR)
    if not os.path.isdir(workspace_dir):
        os.mkdir(workspace_dir)
    if not os.path.isdir(config_dir):
        os.mkdir(config_dir)
    if not os.path.isdir(artifacts_dir):
        os.mkdir(artifacts_dir)
    if not os.path.isdir(files_dir):
        os.mkdir(files_dir)
