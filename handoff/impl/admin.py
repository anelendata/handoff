import datetime, json, logging, os, shutil, sys, subprocess
import yaml

from handoff import docker, provider
from handoff.impl import pyvenvx, utils
from handoff.config import (ADMIN_ENVS, ARTIFACTS_DIR, BUCKET,
                            BUCKET_ARCHIVE_PREFIX, BUCKET_CURRENT_PREFIX,
                            CONFIG_DIR, DOCKER_IMAGE, FILES_DIR,
                            RESOURCE_GROUP, PROJECT_FILE, TASK)

LOGGER = utils.get_logger(__name__)

# TODO: Decide where the user provide the provider name (arg?)
platform = provider.get_platform("aws")


def _check_env_vars():
    not_defined = [env for env in ADMIN_ENVS if not os.environ.get(env)]
    if not not_defined:
        return
    raise Exception("The following environment variables must be defined %s" %
                    not_defined)


def _get_workspace_dirs(workspace_dir):
    config_dir = os.path.join(workspace_dir, CONFIG_DIR)
    artifacts_dir = os.path.join(workspace_dir, ARTIFACTS_DIR)
    files_dir = os.path.join(workspace_dir, FILES_DIR)
    return config_dir, artifacts_dir, files_dir


def _make_venv(venv_path):
    if os.path.exists(venv_path):
        LOGGER.warning("%s already exists. Skipping python -m venv..." %
                       venv_path)
    else:
        paths = venv_path.split("/")
        for i in range(1, len(paths)):
            path = "/".join(paths[0:i])
            if not os.path.exists(path):
                os.mkdir(path)
        builder = pyvenvx.ExtendedEnvBuilder()
        builder.create(venv_path)


def _install(venv_path, install):
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
    Read them from remote parameters store (e.g. AWS SSM) otherwise.
    """
    if precompiled_config_file:
        if not os.path.isfile(precompiled_config_file):
            raise ValueError(precompiled_config_file + " not found.")
        LOGGER.info("Reading precompiled config from: " +
                    precompiled_config_file)
        with open(precompiled_config_file, "r") as f:
            config = json.load(f)
    else:
        LOGGER.info("Reading precompiled config from remote.")
        if not os.environ.get(RESOURCE_GROUP) or not os.environ.get(TASK):
            raise Exception("RESOURCE_GROUP and TASK environment variables must be set outside the local project.xml file to read the remote configurations.")
        config = json.loads(platform.get_parameter("config"))
    return config


def _write_config_files(workspace_config_dir, precompiled_config):
    if not os.path.exists(workspace_config_dir):
        os.mkdir(workspace_config_dir)
    for r in precompiled_config.get("files", []):
        with open(os.path.join(workspace_config_dir, r["name"]), "w") as f:
            f.write(r["value"])


def _set_env(config):
    LOGGER.info("Setting environment variables from config.")
    if not config.get("envs"):
        return
    for v in config["envs"]:
        os.environ[v["key"]] = v["value"]


def read_project(project_file):
    # load commands from yaml file
    with open(project_file, "r") as f:
        project = yaml.load(f, Loader=yaml.FullLoader)

    deploy_env = project.get("deploy", dict()).get("envs", dict())
    for key in deploy_env:
        os.environ[key.upper()] = deploy_env[key]

    if not os.environ.get(BUCKET):
        aws_account_id = platform.get_account_id()
        os.environ[BUCKET] = aws_account_id + "-" + os.environ[RESOURCE_GROUP]
        LOGGER.info("Environment veriable %s was set autoamtically as %s" %
                       (BUCKET, os.environ[BUCKET] ))
    return project


def archive_current(project_dir, workspace_dir, data, **kwargs):
    _check_env_vars()
    dest_dir = os.path.join(BUCKET_ARCHIVE_PREFIX,
                            datetime.datetime.utcnow().isoformat())
    platform.copy_dir_to_another_bucket(BUCKET_CURRENT_PREFIX, dest_dir)


def get_artifacts(project_dir, workspace_dir, data, **kwargs):
    if not workspace_dir:
        raise Exception("Workspace directory is not set")
    _check_env_vars()

    LOGGER.info("Downloading artifacts from the remote storage " +
                os.environ.get(BUCKET))

    _, artifacts_dir, _ = _get_workspace_dirs(workspace_dir)
    remote_dir = os.path.join(BUCKET_CURRENT_PREFIX, ARTIFACTS_DIR)
    platform.download_dir(remote_dir, artifacts_dir)


def push_artifacts(project_dir, workspace_dir, data, **kwargs):
    if not workspace_dir:
        raise Exception("Workspace directory is not set")
    _check_env_vars()

    _, artifacts_dir, _ = _get_workspace_dirs(workspace_dir)
    prefix = os.path.join(BUCKET_CURRENT_PREFIX, ARTIFACTS_DIR)
    platform.upload_dir(artifacts_dir, prefix)


def delete_artifacts(project_dir, workspace_dir, data, **kwargs):
    _check_env_vars()
    LOGGER.info("Deleting artifacts from the remote storage " +
                os.environ.get(BUCKET))
    dir_name = os.path.join(BUCKET_CURRENT_PREFIX, ARTIFACTS_DIR)
    platform.delete_dir(dir_name)


def get_files(project_dir, workspace_dir, data, **kwargs):
    if not workspace_dir:
        raise Exception("Workspace directory is not set")
    _check_env_vars()

    LOGGER.info("Downloading config files from the remote storage " +
                os.environ.get(BUCKET))

    _, _, files_dir = _get_workspace_dirs(workspace_dir)
    remote_dir = os.path.join(BUCKET_CURRENT_PREFIX, FILES_DIR)
    platform.download_dir(remote_dir, files_dir)


def get_files_local(project_dir, workspace_dir, data):
    if not project_dir:
        raise Exception("Project directory is not set")

    LOGGER.info("Copying files from the local project directory " +
                project_dir)

    project_files_dir = os.path.join(project_dir, FILES_DIR)
    if not os.path.exists(project_files_dir):
        return
    _, _, files_dir = _get_workspace_dirs(workspace_dir)
    if os.path.exists(files_dir):
        shutil.rmtree(files_dir)
    shutil.copytree(project_files_dir, files_dir)


def push_files(project_dir, workspace_dir, data, **kwargs):
    """ Push the contents of project_dir/FILES_DIR to remote storage"""
    if not project_dir:
        raise Exception("Project directory is not set")
    _check_env_vars()

    files_dir = os.path.join(project_dir, FILES_DIR)
    prefix = os.path.join(BUCKET_CURRENT_PREFIX, FILES_DIR)
    platform.upload_dir(files_dir, prefix)


def delete_files(project_dir, workspace_dir, data, **kwargs):
    _check_env_vars()
    LOGGER.info("Deleting files from the remote storage " +
                os.environ.get(BUCKET))
    dir_name = os.path.join(BUCKET_CURRENT_PREFIX, FILES_DIR)
    platform.delete_dir(dir_name)


def get_config(project_dir, workspace_dir, data, **kwargs):
    if not workspace_dir:
        raise Exception("Workspace directory is not set")
    _check_env_vars()

    LOGGER.info("Reading configurations from remote parameter store.")

    config_dir, _, _ = _get_workspace_dirs(workspace_dir)
    precompiled_config = _read_precompiled_config()
    _set_env(precompiled_config)
    _write_config_files(config_dir, precompiled_config)

    return precompiled_config


def get_config_local(project_dir, workspace_dir, data, **kwargs):
    """ Compile configuration JSON file from the project.yml

    The output JSON file describes the commands and arguments for each process.
    It also contains the environment variables for the run-time.
    JSON format configuration files are encoded into the output JSON so they
    can be restored in the docker instance when it runs.

    The parameters file may contain secrets and it should kept private. (i.e.
    don't commit to a repository and etc.)

    This parameters file is encrypted and stored in a remote parameter store
    (e.g. AWS SSM) via push_config command and downloaded at the run-time.

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
    if not project_dir:
        raise Exception("Project directory is not set")
    if not workspace_dir:
        raise Exception("Workspace directory is not set")

    LOGGER.info("Reading configurations from the local project directory.")

    config = dict()
    project = read_project(os.path.join(project_dir, "project.yml"))
    config.update(project)

    _set_env(config)

    config["files"] = list()
    proj_config_dir = os.path.join(project_dir, CONFIG_DIR)
    if os.path.exists(proj_config_dir):
        for fn in os.listdir(proj_config_dir):
            full_path = os.path.join(proj_config_dir, fn)
            if (fn[-5:] != ".json" or
                    not os.path.isfile(full_path)):
                continue
            with open(full_path, "r") as f:
                config_str = f.read().replace('"', "\"")
                config["files"].append({"name": fn, "value": config_str})

    if workspace_dir:
        ws_config_dir = os.path.join(workspace_dir, CONFIG_DIR)
        _write_config_files(ws_config_dir, config)

    return config


def push_config(project_dir, workspace_dir, data, **kwargs):
    """ Push the contents of project_dir as a secure parameter key"""
    if not project_dir:
        raise Exception("Project directory is not set")
    _check_env_vars()

    LOGGER.info("Compiling config from %s" % project_dir)
    config = json.dumps(get_config_local(project_dir, workspace_dir, data))

    LOGGER.info("Uploading config to %s." % os.environ.get(TASK))
    platform.push_parameter("config", config, **kwargs)


def delete_config(project_dir, workspace_dir, data, **kwargs):
    _check_env_vars()
    platform.delete_parameter("config")


def install(project_dir, workspace_dir, data, **kwargs):
    """
    Install dependencies in the local virtual environment
    """
    if not project_dir:
        raise Exception("Project directory is not set")
    if not workspace_dir:
        raise Exception("Workspace directory is not set")

    project = read_project(os.path.join(project_dir, PROJECT_FILE))

    os.chdir(workspace_dir)
    for command in project["commands"]:
        if command.get("venv"):
            _make_venv(command["venv"])
        for install in command.get("installs", []):
            _install(os.path.join(command["venv"]), install)


def print_config(project_dir, workspace_dir, data, **kwargs):
    print(json.dumps(get_config(project_dir, workspace_dir, data)))


def get_workspace(project_dir, workspace_dir, data, **kwargs):
    get_config(project_dir, workspace_dir, data)
    get_artifacts(project_dir, workspace_dir, data)
    get_files(project_dir, workspace_dir, data)


def init_workspace(project_dir, workspace_dir, data, **kwargs):
    if not workspace_dir:
        raise Exception("Workspace directory is not set")
    if not os.path.isdir(workspace_dir):
        os.mkdir(workspace_dir)

    config_dir, artifacts_dir, files_dir = _get_workspace_dirs(workspace_dir)
    if not os.path.isdir(config_dir):
        os.mkdir(config_dir)
    if not os.path.isdir(artifacts_dir):
        os.mkdir(artifacts_dir)
    if not os.path.isdir(files_dir):
        os.mkdir(files_dir)


def docker_build(project_dir, workspace_dir, data, **kwargs):
    if not project_dir:
        raise Exception("Project directory is not set")
    _check_env_vars()
    docker.build(project_dir)


def docker_run(project_dir, workspace_dir, data, **kwargs):
    _check_env_vars()
    docker.run()


def docker_push(project_dir, workspace_dir, data, **kwargs):
    _check_env_vars()

    username, password, registry = platform.get_docker_registry_credentials()
    image_name = os.environ.get(DOCKER_IMAGE)
    try:
        platform.get_repository_images(image_name)
    except Exception:
        sys.stdout.write("Repository %s does not exist. Create? (y/N)" %
                         image_name)
        response = input()
        if response.lower() not in ["y", "yes"]:
            return
        LOGGER.info("Creating repository " + image_name)
        platform.create_repository()

    docker.push(username, password, registry)
