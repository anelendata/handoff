import datetime, json, logging, os, shutil, sys, subprocess
from typing import Dict, Tuple
import yaml

from jinja2 import Template as _Template

from handoff.services import cloud
from handoff.config import (ENV_PREFIX, VERSION, ARTIFACTS_DIR, BUCKET,
                            BUCKET_ARCHIVE_PREFIX, BUCKET_CURRENT_PREFIX,
                            CONTAINER_IMAGE, FILES_DIR, TEMPLATES_DIR,
                            SECRETS_DIR, SECRETS_FILE,
                            RESOURCE_GROUP, PROJECT_FILE, TASK,
                            CLOUD_PROVIDER, CLOUD_PLATFORM, get_state)
from handoff import utils
from handoff.utils import pyvenvx

LOGGER = utils.get_logger(__name__)

SECRETS = None


def _install(install: str, venv_path: str = None) -> None:
    if venv_path:
        venv_switch = "source " + venv_path + "/bin/activate && "
    else:
        venv_switch = ""
    command = '/bin/bash -c "{venv_switch}{install}"'.format(
        **{"venv_switch": venv_switch, "install": install})

    LOGGER.info("Running %s" % command)
    p = subprocess.Popen([command],
                         # stdout=subprocess.PIPE,
                         shell=True)
    p.wait()


def _make_python_venv(venv_path: str) -> None:
    if os.path.exists(venv_path):
        LOGGER.warning("%s already exists. Skipping python -m venv..." %
                       venv_path)
    else:
        paths = venv_path.split("/")
        for i in range(1, len(paths)):
            path = "/".join(paths[0:i])
            if not os.path.exists(path):
                os.mkdir(path)
        # https://github.com/anelendata/handoff/issues/25#issuecomment-667945434
        builder = pyvenvx.ExtendedEnvBuilder(symlinks=True)
        builder.create(venv_path)
        _install("pip install wheel", venv_path)


def _parse_template_files(
        templates_dir: str,
        workspace_files_dir: str) -> None:
    state = get_state()
    if not os.path.exists(workspace_files_dir):
        os.mkdir(workspace_files_dir)
    for root, dirs, files in os.walk(templates_dir, topdown=True):
        ws_root = os.path.join(workspace_files_dir,
                               root[root.find(templates_dir) +
                                    len(templates_dir) + 1:])
        for d in dirs:
            full_path = os.path.join(ws_root, d)
            if not os.path.exists(full_path):
                os.mkdir(full_path)
        for fn in files:
            with open(os.path.join(root, fn), "r") as f:
                tf = f.read().replace('"', "\"")
            template = _Template(tf)
            parsed = template.render(**state)
            full_path = os.path.join(ws_root, fn)
            with open(full_path, "w") as f:
                f.write(parsed)


def _get_secret(key: str) -> str:
    global SECRETS
    if SECRETS is None:
        raise Exception("Secrets are not loaded")
    return SECRETS.get(key)


def _update_state(
    config: Dict,
    data: Dict = {}) -> None:
    """Set environment variable and in-memory variables
    Warning: environment variables are inherited to subprocess. The sensitive
    information may be compromised by a bad subprocess.
    """
    state = get_state()
    LOGGER.info("Setting environment variables from config.")

    state.update(SECRETS)
    for v in config.get("envs", list()):
        if v.get("value") is None:
            v["value"] = _get_secret(v["key"])
        if v["value"]:
            state.set_env(v["key"], v["value"], trust=True)
    state.update(data)

    if not state.get(BUCKET):
        try:
            platform = cloud._get_platform()
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


def _read_project_remote() -> Dict:
    """Read the config from remote parameters store (e.g. AWS SSM)
    """
    state = get_state()
    LOGGER.info("Reading precompiled config from remote.")
    state.validate_env([RESOURCE_GROUP, TASK,
                        CLOUD_PROVIDER, CLOUD_PLATFORM])
    platform = cloud._get_platform(provider_name=state.get(CLOUD_PROVIDER),
                                   platform_name=state.get(CLOUD_PLATFORM))
    config_str = platform.get_parameter("config")
    if not config_str:
        raise Exception("config not found in the remote parameter store.\n" +
                        "Check resource_group and task and do config push.")
    config = json.loads(config_str)
    return config


def _read_project_local(project_file: str) -> Dict:
    """Read project.yml file from the local project directory
    """
    state = get_state()
    LOGGER.info("Reading configurations from " + project_file)
    with open(project_file, "r") as f:
        project = yaml.load(f, Loader=yaml.FullLoader)

    deploy_env = project.get("deploy", dict())
    for key in deploy_env:
        full_key = ENV_PREFIX + key.upper()
        if state.is_allowed_env(full_key):
            state.set_env(full_key, deploy_env[key])
        else:
            state[full_key] = deploy_env[key]

    cloud_provider_name = project.get("deploy", dict()).get("cloud_provider")
    cloud_platform_name = project.get("deploy", dict()).get("cloud_platform")
    if cloud_provider_name and cloud_platform_name:
        platform = cloud._get_platform(provider_name=cloud_provider_name,
                                       platform_name=cloud_platform_name)
        LOGGER.info("Platform: " + platform.NAME)

    return project


def _secrets_get(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """Fetch all secrets from the remote parameter store
    """
    state = get_state()
    state.validate_env([RESOURCE_GROUP, TASK,
                        CLOUD_PROVIDER, CLOUD_PLATFORM])
    platform = cloud._get_platform(provider_name=state.get(CLOUD_PROVIDER),
                                   platform_name=state.get(CLOUD_PLATFORM))
    LOGGER.info("Fetching the secrets from the remote parameter store.")
    global SECRETS
    SECRETS = {}
    params = platform.get_all_parameters()
    for key in params.keys():
        SECRETS[key] = params[key]["value"]


def _secrets_get_local(
    project_dir: str,
    workspace_dir: str,
    data: Dict = {},
    **kwargs) -> Dict:
    """Load secrets from local file

    See secrets_push for the local file specification.
    """
    global SECRETS
    SECRETS = {}
    if data.get("secrets_dir"):
        secrets_dir = data["secrets_dir"]
    else:
        secrets_dir = os.path.join(project_dir, SECRETS_DIR)
    secrets_file = os.path.join(secrets_dir, SECRETS_FILE)

    if not os.path.isfile(secrets_file):
        LOGGER.warning(secrets_file + " does not exsist")
        return None
    with open(secrets_file, "r") as f:
        LOGGER.info("Reading secrets from local file: " + secrets_file)
        secrets = yaml.load(f, Loader=yaml.FullLoader)
    secrets_dict = dict()
    for secret in secrets:
        key = secret.get("key")
        secrets_dict[key] = secret
        if not key:
            raise Exception("key must be defined for secret")
        if secret.get("value"):
            SECRETS[key] = secret["value"]
        elif secret.get("file"):
            rel_path = os.path.join(secrets_dir,
                                     secret.get("file"))
            if not os.path.isfile(rel_path):
                raise Exception(rel_path + " does not exist")
            with open(rel_path, "r") as f:
                SECRETS[key] = f.read()
        elif secret.get("level", "task") == "resource group":
            LOGGER.warning(
                "Unregistered resource group level secret: %s" % key)
        else:
            raise Exception("Neither value or file defined for task-level " +
                            "secret: " + key)
    return secrets_dict


def secrets_push(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff secrets push -p <project_directory> -d file=<secrets_file>`

    Push the contents of <secrets_file> to remote parameter store

    --data file (.secrets/secrets.yml): The YAML file storing secrets
    with format:
    ```
    - key: key1
      value: value1
    - key: key2
      # The value can also be loaded from a text file
      file: file_name
      # The value is stored as a resource group level secret and can be
      # shared among the projects under the same group.
      level: "resource group"
    ```
    """
    state = get_state()
    state.validate_env([RESOURCE_GROUP, TASK, CLOUD_PROVIDER, CLOUD_PLATFORM])
    platform = cloud._get_platform()
    secrets = _secrets_get_local(project_dir, workspace_dir, **kwargs)

    if not secrets:
        raise Exception("No secrets are defined.")
    print("Putting the following keys to remote parameter store:")

    if "config" in secrets:
        raise Exception("secrets with name \"config\" is reserved by handoff.")

    for key in secrets.keys():
        print("  - " + key + " (" + secrets[key].get("level", "task") +
              " level)")
    response = input("Proceed? (y/N)")
    if response.lower() not in ["yes", "y"]:
        print("aborting")
        return

    for key in secrets:
        level = secrets[key].get("level", "task")
        platform.push_parameter(
            key, SECRETS[key],
            resource_group_level=(level.lower().strip() == "resource group"),
            **kwargs)


def secrets_delete(
    project_dir: str,
    workspace_dir: str,
    **kwargs):
    """`handoff secrets delete -p <project_directory> -d file=<secrets_file>`

    Delete the contents of <secrets_file> to remote parameter store
    By default, .secrets/secrets.yml in the current working directory is
    searched for the list of the secrets.
    """
    state = get_state()
    state.validate_env([RESOURCE_GROUP, TASK, CLOUD_PROVIDER, CLOUD_PLATFORM])
    platform = cloud._get_platform()
    secrets = _secrets_get_local(project_dir, workspace_dir, **kwargs)

    if not secrets:
        return
    print("Deleting the following keys to remote parameter store:")

    for key in secrets:
        print("  - " + key + " (" + secrets[key].get("level", "task") +
              " level)")

    response = input("Proceed? (y/N)")
    if response.lower() not in ["yes", "y"]:
        print("aborting")
        return

    for key in secrets:
        level = secrets[key].get("level", "task")
        try:
            platform.delete_parameter(
                key,
                resource_group_level=(level.lower().strip()
                                      == "resource group"),
                **kwargs)
        except Exception:
            LOGGER.warning("%s does not exist in remote parameter store." %
                           key)


def secrets_print(
    project_dir:str,
    workspace_dir:str,
    **kwargs):
    """`handoff secrets print -p <project_directory>`

    Get the secrets in the remote parameter store and dump in YAML format.
    """
    state = get_state()
    state.validate_env([RESOURCE_GROUP, TASK,
                        CLOUD_PROVIDER, CLOUD_PLATFORM])
    platform = cloud._get_platform(provider_name=state.get(CLOUD_PROVIDER),
                                   platform_name=state.get(CLOUD_PLATFORM))
    LOGGER.info("Fetching the secrets from the remote parameter store.")
    params = platform.get_all_parameters()
    secret_list = list()
    for key in params.keys():
        if key == "config":
            continue
        level = "task"
        if params[key]["path"].split("/")[-2] == state[RESOURCE_GROUP]:
            level = "resource group"
        secret_list.append({
            "key": key,
            "level": level,
            "value": params[key]["value"]
        })
    print(yaml.dump(secret_list))


def artifacts_archive(
    project_dir:str,
    workspace_dir:str,
    **kwargs) -> None:
    """`handoff artifacts archive -p <project_directory>`

    Copy the artifacts directory from (remote) last to (remote) runs/<date>.
    """
    state = get_state()
    state.validate_env([RESOURCE_GROUP, TASK, CLOUD_PROVIDER, CLOUD_PLATFORM,
                        BUCKET])

    LOGGER.info("Copying the remote artifacts from last to runs " +
                state.get(BUCKET))

    platform = cloud._get_platform(provider_name=state.get(CLOUD_PROVIDER),
                                   platform_name=state.get(CLOUD_PLATFORM))

    dest_dir = os.path.join(BUCKET_ARCHIVE_PREFIX,
                            datetime.datetime.utcnow().isoformat())
    platform.copy_dir_to_another_bucket(BUCKET_CURRENT_PREFIX, dest_dir)


def artifacts_get(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff artifacts archive -p <project_directory> -w <workspace_directory>`

    Download artifacts from the (remote) last to <workspace_dir>
    """
    state = get_state()
    state.validate_env([RESOURCE_GROUP, TASK, CLOUD_PROVIDER, CLOUD_PLATFORM,
                        BUCKET])

    if not workspace_dir:
        raise Exception("Workspace directory is not set")

    LOGGER.info("Downloading artifacts from the remote storage " +
                state.get(BUCKET))

    platform = cloud._get_platform(provider_name=state.get(CLOUD_PROVIDER),
                                   platform_name=state.get(CLOUD_PLATFORM))

    artifacts_dir = os.path.join(workspace_dir, ARTIFACTS_DIR)
    remote_dir = os.path.join(BUCKET_CURRENT_PREFIX, ARTIFACTS_DIR)

    platform.download_dir(remote_dir, artifacts_dir)


def artifacts_push(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff artifacts push -p <project_directory> -w <workspace_directory>`

    Push local artifacts file to remote storage under last directory.
    """
    state = get_state()
    state.validate_env([RESOURCE_GROUP, TASK, CLOUD_PROVIDER, CLOUD_PLATFORM,
                        BUCKET])

    if not workspace_dir:
        raise Exception("Workspace directory is not set")

    LOGGER.info("Pushing local artifacts to the remote storage " +
                state.get(BUCKET))

    platform = cloud._get_platform(provider_name=state.get(CLOUD_PROVIDER),
                                   platform_name=state.get(CLOUD_PLATFORM))

    artifacts_dir = os.path.join(workspace_dir, ARTIFACTS_DIR)
    prefix = os.path.join(BUCKET_CURRENT_PREFIX, ARTIFACTS_DIR)
    platform.upload_dir(artifacts_dir, prefix)


def artifacts_delete(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff artifacts delete -p <project_directory>`

    Delete artifacts from the remote artifacts/last directory
    """
    state = get_state()
    state.validate_env([RESOURCE_GROUP, TASK, CLOUD_PROVIDER, CLOUD_PLATFORM,
                        BUCKET])

    LOGGER.info("Deleting artifacts from the remote storage " +
                state.get(BUCKET))

    platform = cloud._get_platform(provider_name=state.get(CLOUD_PROVIDER),
                                   platform_name=state.get(CLOUD_PLATFORM))

    dir_name = os.path.join(BUCKET_CURRENT_PREFIX, ARTIFACTS_DIR)
    platform.delete_dir(dir_name)


def files_get(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff files get -p <project_directory> -w <workspace_directory>`
    Download remote files to <workspace_dir>/files
    It also parse the templates with secrets and populate under
    <workspace_dir>/files
    """
    state = get_state()
    state.validate_env([RESOURCE_GROUP, TASK, CLOUD_PROVIDER, CLOUD_PLATFORM,
                        BUCKET])

    if not workspace_dir:
        raise Exception("Workspace directory is not set")

    LOGGER.info("Downloading config files from the remote storage " +
                state.get(BUCKET))

    platform = cloud._get_platform(provider_name=state.get(CLOUD_PROVIDER),
                                   platform_name=state.get(CLOUD_PLATFORM))

    # First download to the local templates directory, then parse to save
    # in the workspace files directory.
    files_dir = os.path.join(workspace_dir, FILES_DIR)
    # Remote files are templates that can contain variables.
    remote_dir = os.path.join(BUCKET_CURRENT_PREFIX, FILES_DIR)
    templates_dir = os.path.join(workspace_dir, TEMPLATES_DIR)
    platform.download_dir(remote_dir, templates_dir)
    # Parse and save to workspace/files
    _parse_template_files(templates_dir, files_dir)


def files_get_local(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff files get local -p <project_directory> -w <workspace_directory>`
    Copy files from the local project_dir to workspace_dir.

    It also parse the templates with secrets and populate under
    <workspace_dir>/files

    Any existing files in workspace_dir will be deleted.
    """
    if not project_dir:
        raise Exception("Project directory is not set")
    if not workspace_dir:
        raise Exception("Workspace directory is not set")

    LOGGER.info("Copying files from the local project directory " +
                project_dir)

    project_files_dir = os.path.join(project_dir, FILES_DIR)
    if os.path.exists(project_files_dir):
        files_dir = os.path.join(workspace_dir, FILES_DIR)
        if os.path.exists(files_dir):
            shutil.rmtree(files_dir)
        _parse_template_files(project_files_dir, files_dir)


def files_push(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff files push -p <project_directory>`
    Push the contents of <project_dir>/files and <project_dir>/templates
    to remote storage"""
    platform = cloud._get_platform()

    files_dir = os.path.join(project_dir, FILES_DIR)
    prefix = os.path.join(BUCKET_CURRENT_PREFIX, FILES_DIR)
    platform.upload_dir(files_dir, prefix)


def files_delete(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff files delete -p <project_directory>`
    Delete files and templates from the remote storage
    """
    state = get_state()
    state.validate_env([RESOURCE_GROUP, TASK, CLOUD_PROVIDER, CLOUD_PLATFORM,
                        BUCKET])

    platform = cloud._get_platform()
    dir_name = os.path.join(BUCKET_CURRENT_PREFIX, FILES_DIR)
    platform.delete_dir(dir_name)


def _config_get(
    project_dir: str,
    workspace_dir: str,
    data: Dict = {},
    **kwargs) -> Dict:
    """Read configs from remote parameter store and copy them to workspace dir
    """
    if not workspace_dir:
        raise Exception("Workspace directory is not set")
    LOGGER.info("Reading configurations from remote parameter store.")
    precompiled_config = _read_project_remote()

    _secrets_get(project_dir, workspace_dir, **kwargs)
    _update_state(precompiled_config, data=data)

    return precompiled_config


def _config_get_local(
    project_dir: str,
    workspace_dir: str,
    data: Dict = {},
    **kwargs) -> Dict:
    """ Compile configuration JSON file from the project.yml

    The output JSON file describes the commands and arguments for each process.
    It also contains the environment variables for the run-time.

    *.json files under config directory are encoded into the output JSON so they
    can be restored in the docker instance when it runs.

    The parameters file may contain secrets and it should kept private. (i.e.
    don't commit to a repository and etc.)

    This parameters file is encrypted and stored in a remote parameter store
    (e.g. AWS SSM) via config_push command and downloaded at the run-time.

    - project_dir: The project directory that contains:
      - project.yml
      - config:
        - *.json: JSON format configuration files necessary for each process.
        (e.g. singer tap/target config files, Google Cloud Platform secret file)

    Example project.yml:
    ```
    commands:
      - command: tap-rest-api
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
    project = _read_project_local(os.path.join(project_dir, "project.yml"))
    config.update(project)

    _secrets_get_local(project_dir, workspace_dir, **kwargs)
    _update_state(config, data=data)

    return config


def config_push(
    project_dir: str,
    workspace_dir: str,
    data: Dict = {},
    **kwargs) -> None:
    """`handoff config push -p <project_directory>`
    Push project.yml and the contents of project_dir/config as a secure
    parameter key.
    """
    LOGGER.info("Compiling config from %s" % project_dir)
    config_obj = _config_get_local(project_dir, workspace_dir, data=data,
                                   **kwargs)
    config_obj["version"] = VERSION
    config = json.dumps(config_obj)

    allow_advanced_tier = data.get("allow_advanced_tier", False)
    if type(allow_advanced_tier) is not bool:
        raise Exception("allow_advanced_tier must be True/False")

    platform = cloud._get_platform()
    platform.push_parameter("config", config,
                            allow_advanced_tier=allow_advanced_tier)


def config_delete(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff config delete -p <project_directory>`
    Delete the project configuration from the remote parameter store.
    """
    platform = cloud._get_platform()
    platform.delete_parameter("config")


def config_print(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff config print -p <project_directory>`
    Print the project configuration in the remote parameter store.
    """
    print(json.dumps(_config_get(project_dir, workspace_dir)))


def workspace_init(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    if not workspace_dir:
        raise Exception("Workspace directory is not set")
    if not os.path.isdir(workspace_dir):
        os.mkdir(workspace_dir)

    artifacts_dir = os.path.join(workspace_dir, ARTIFACTS_DIR)
    files_dir = os.path.join(workspace_dir, FILES_DIR)
    if not os.path.isdir(artifacts_dir):
        os.mkdir(artifacts_dir)
    if not os.path.isdir(files_dir):
        os.mkdir(files_dir)


def workspace_install(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff workspace install -p <project_directory> -w <workspace_directory>`
    Install dependencies in the local virtual environment
    """
    if not project_dir:
        raise Exception("Project directory is not set")
    if not workspace_dir:
        raise Exception("Workspace directory is not set")

    project = _read_project_local(os.path.join(project_dir, PROJECT_FILE))

    os.chdir(workspace_dir)
    for command in project["commands"]:
        if command.get("venv"):
            _make_python_venv(command["venv"])
        for install in command.get("installs", []):
            _install(install, os.path.join(command["venv"]))


def version(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """Print handoff version
    """
    print(VERSION)
