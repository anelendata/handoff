import datetime, json, logging, os, shutil, sys, subprocess
import yaml

from handoff import provider
from handoff.config import (ENV_PREFIX, VERSION, ARTIFACTS_DIR, BUCKET,
                            BUCKET_ARCHIVE_PREFIX, BUCKET_CURRENT_PREFIX,
                            CONFIG_DIR, DOCKER_IMAGE, FILES_DIR,
                            RESOURCE_GROUP, PROJECT_FILE, TASK,
                            PROVIDER, PLATFORM, get_state)
from handoff.core import pyvenvx, utils


LOGGER = utils.get_logger(__name__)


def _workspace_get_dirs(workspace_dir):
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


def _write_config_files(workspace_config_dir, precompiled_config):
    if not os.path.exists(workspace_config_dir):
        os.mkdir(workspace_config_dir)
    for r in precompiled_config.get("files", []):
        with open(os.path.join(workspace_config_dir, r["name"]), "w") as f:
            f.write(r["value"])


def _set_env(config):
    state = get_state()
    LOGGER.info("Setting environment variables from config.")
    for v in config.get("envs", list()):
        # Trust the values from project file
        state.set_env(v["key"], v["value"], trust=True)

    if not state.get(BUCKET):
        try:
            platform = provider._get_platform()
            aws_account_id = platform.get_account_id()
        except Exception:
            pass
        else:
            if state.get(RESOURCE_GROUP):
                state.set_env(BUCKET, (aws_account_id + "-" +
                                       state[RESOURCE_GROUP]))
                LOGGER.info("Environment variable %s was set autoamtically as %s" %
                            (BUCKET, state[BUCKET]))

    if not state.get(BUCKET):
        LOGGER.warning(("Environment variable %s is not set. " +
                        "Remote file read/write will fail.") %
                       BUCKET)


def _read_precompiled_config(precompiled_config_file=None):
    """
    Read parameters from a file if a file name is given.
    Read them from remote parameters store (e.g. AWS SSM) otherwise.
    """
    state = get_state()
    if precompiled_config_file:
        LOGGER.info("Reading precompiled config from: " +
                    precompiled_config_file)
        if not os.path.isfile(precompiled_config_file):
            raise ValueError(precompiled_config_file + " not found.")
        with open(precompiled_config_file, "r") as f:
            config = json.load(f)
    else:
        LOGGER.info("Reading precompiled config from remote.")
        # TODO: Decide what to do with config_get (remote)
        state.validate_env([RESOURCE_GROUP, TASK, PROVIDER, PLATFORM])
        platform = provider._get_platform(provider_name=state.get(PROVIDER),
                                          platform_name=state.get(PLATFORM))
        config = json.loads(platform.get_parameter("config"))
    return config


def _read_project(project_file):
    state = get_state()
    LOGGER.info("Reading configurations from " + project_file)
    with open(project_file, "r") as f:
        project = yaml.load(f, Loader=yaml.FullLoader)

    deploy_env = project.get("deploy", dict()).get("envs", dict())
    for key in deploy_env:
        state.set_env(ENV_PREFIX + key.upper(), deploy_env[key])

    provider_name = project.get("deploy", dict()).get("provider")
    platform_name = project.get("deploy", dict()).get("platform")
    if provider_name and platform_name:
        platform = provider._get_platform(provider_name=provider_name,
                                          platform_name=platform_name)
        LOGGER.info("Platform: " + platform.NAME)

    return project


def artifacts_archive(project_dir, workspace_dir, data, **kwargs):
    state = get_state()
    state.validate_env()
    platform = provider._get_platform()
    dest_dir = os.path.join(BUCKET_ARCHIVE_PREFIX,
                            datetime.datetime.utcnow().isoformat())
    platform.copy_dir_to_another_bucket(BUCKET_CURRENT_PREFIX, dest_dir)


def artifacts_get(project_dir, workspace_dir, data, **kwargs):
    state = get_state()
    platform = provider._get_platform()
    if not workspace_dir:
        raise Exception("Workspace directory is not set")
    state.validate_env()

    LOGGER.info("Downloading artifacts from the remote storage " +
                state.get(BUCKET))

    _, artifacts_dir, _ = _workspace_get_dirs(workspace_dir)
    remote_dir = os.path.join(BUCKET_CURRENT_PREFIX, ARTIFACTS_DIR)
    platform.download_dir(remote_dir, artifacts_dir)


def artifacts_push(project_dir, workspace_dir, data, **kwargs):
    state = get_state()
    platform = provider._get_platform()
    if not workspace_dir:
        raise Exception("Workspace directory is not set")
    state.validate_env()

    _, artifacts_dir, _ = _workspace_get_dirs(workspace_dir)
    prefix = os.path.join(BUCKET_CURRENT_PREFIX, ARTIFACTS_DIR)
    platform.upload_dir(artifacts_dir, prefix)


def artifacts_delete(project_dir, workspace_dir, data, **kwargs):
    state = get_state()
    platform = provider._get_platform()
    state.validate_env()
    LOGGER.info("Deleting artifacts from the remote storage " +
                state.get(BUCKET))
    dir_name = os.path.join(BUCKET_CURRENT_PREFIX, ARTIFACTS_DIR)
    platform.delete_dir(dir_name)


def files_get(project_dir, workspace_dir, data, **kwargs):
    state = get_state()
    if not workspace_dir:
        raise Exception("Workspace directory is not set")
    if not state.get(BUCKET):
       config_get(project_dir, workspace_dir, data, **kwargs)
    state.validate_env([RESOURCE_GROUP, TASK, PROVIDER, PLATFORM, BUCKET])

    LOGGER.info("Downloading config files from the remote storage " +
                state.get(BUCKET))

    platform = provider._get_platform(provider_name=state.get(PROVIDER),
                                      platform_name=state.get(PLATFORM))

    _, _, files_dir = _workspace_get_dirs(workspace_dir)
    remote_dir = os.path.join(BUCKET_CURRENT_PREFIX, FILES_DIR)
    platform.download_dir(remote_dir, files_dir)


def files_get_local(project_dir, workspace_dir, data, **kwargs):
    if not project_dir:
        raise Exception("Project directory is not set")

    LOGGER.info("Copying files from the local project directory " +
                project_dir)

    project_files_dir = os.path.join(project_dir, FILES_DIR)
    if not os.path.exists(project_files_dir):
        return
    _, _, files_dir = _workspace_get_dirs(workspace_dir)
    if os.path.exists(files_dir):
        shutil.rmtree(files_dir)
    shutil.copytree(project_files_dir, files_dir)


def files_push(project_dir, workspace_dir, data, **kwargs):
    """ Push the contents of project_dir/FILES_DIR to remote storage"""
    _ = config_get_local(project_dir, workspace_dir, data)
    platform = provider._get_platform()
    files_dir = os.path.join(project_dir, FILES_DIR)
    prefix = os.path.join(BUCKET_CURRENT_PREFIX, FILES_DIR)
    platform.upload_dir(files_dir, prefix)


def files_delete(project_dir, workspace_dir, data, **kwargs):
    state = get_state()
    platform = provider._get_platform()
    state.validate_env()
    LOGGER.info("Deleting files from the remote storage " +
                state.get(BUCKET))
    dir_name = os.path.join(BUCKET_CURRENT_PREFIX, FILES_DIR)
    platform.delete_dir(dir_name)


def config_get(project_dir, workspace_dir, data, **kwargs):
    if not workspace_dir:
        raise Exception("Workspace directory is not set")
    LOGGER.info("Reading configurations from remote parameter store.")
    config_dir, _, _ = _workspace_get_dirs(workspace_dir)
    precompiled_config = _read_precompiled_config()
    _set_env(precompiled_config)
    _write_config_files(config_dir, precompiled_config)

    return precompiled_config


def config_get_local(project_dir, workspace_dir, data, **kwargs):
    """ Compile configuration JSON file from the project.yml

    The output JSON file describes the commands and arguments for each process.
    It also contains the environment variables for the run-time.
    JSON format configuration files are encoded into the output JSON so they
    can be restored in the docker instance when it runs.

    The parameters file may contain secrets and it should kept private. (i.e.
    don't commit to a repository and etc.)

    This parameters file is encrypted and stored in a remote parameter store
    (e.g. AWS SSM) via config_push command and downloaded at the run-time.

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
        args: "--config config/tarconfig_get.json"
        venv: "proc_02"
    envs:
      - key: "GOOGLE_APPLICATION_CREDENTIALS"
        value: "config/google_client_secret.json"
    ```
    """
    if not project_dir:
        raise Exception("Project directory is not set")
    config = dict()
    project = _read_project(os.path.join(project_dir, "project.yml"))
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
        LOGGER.info("Writing configuration files in the workspace" +
                    " configuration directory " +
                    ws_config_dir)
        _write_config_files(ws_config_dir, config)

    return config


def config_push(project_dir, workspace_dir, data, **kwargs):
    """ Push the contents of project_dir as a secure parameter key"""
    LOGGER.info("Compiling config from %s" % project_dir)
    config = json.dumps(config_get_local(project_dir, workspace_dir, data))

    platform = provider._get_platform()
    platform.push_parameter("config", config, **kwargs)


def config_delete(project_dir, workspace_dir, data, **kwargs):
    state = get_state()
    platform = provider._get_platform()
    state.validate_env()
    platform.delete_parameter("config")


def config_print(project_dir, workspace_dir, data, **kwargs):
    print(json.dumps(config_get(project_dir, workspace_dir, data)))


def workspace_get(project_dir, workspace_dir, data, **kwargs):
    config_get(project_dir, workspace_dir, data)
    artifacts_get(project_dir, workspace_dir, data)
    files_get(project_dir, workspace_dir, data)


def workspace_init(project_dir, workspace_dir, data, **kwargs):
    if not workspace_dir:
        raise Exception("Workspace directory is not set")
    if not os.path.isdir(workspace_dir):
        os.mkdir(workspace_dir)

    config_dir, artifacts_dir, files_dir = _workspace_get_dirs(workspace_dir)
    if not os.path.isdir(config_dir):
        os.mkdir(config_dir)
    if not os.path.isdir(artifacts_dir):
        os.mkdir(artifacts_dir)
    if not os.path.isdir(files_dir):
        os.mkdir(files_dir)


def workspace_install(project_dir, workspace_dir, data, **kwargs):
    """
    Install dependencies in the local virtual environment
    """
    if not project_dir:
        raise Exception("Project directory is not set")
    if not workspace_dir:
        raise Exception("Workspace directory is not set")

    project = _read_project(os.path.join(project_dir, PROJECT_FILE))

    os.chdir(workspace_dir)
    for command in project["commands"]:
        if command.get("venv"):
            _make_venv(command["venv"])
        for install in command.get("installs", []):
            _install(os.path.join(command["venv"]), install)


def version(project_dir, workspace_dir, data, **kwargs):
    print(VERSION)
