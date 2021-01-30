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
    command = f'/bin/bash -c "{venv_switch}{install}"'
    LOGGER.debug("Running %s" % command)
    p = subprocess.Popen([command], shell=True)
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
        # https://github.com/anelenvars/handoff/issues/25#issuecomment-667945434
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
            is_binary = False
            LOGGER.debug("template: " + fn)
            with open(os.path.join(root, fn), "r") as f:
                try:
                    tf = f.read().replace('"', "\"")
                except UnicodeDecodeError:
                    is_binary = True
            full_path = os.path.join(ws_root, fn)
            if is_binary:
                shutil.copyfile(os.path.join(root, fn), full_path)
                continue
            template = _Template(tf)
            parsed = template.render(**state)
            with open(full_path, "w") as f:
                f.write(parsed)


def _get_secret(key: str) -> str:
    global SECRETS
    if SECRETS is None:
        raise Exception("Secrets are not loaded")
    return SECRETS.get(key)


def _set_bucket_name(resource_group_name, aws_account_id):
    state = get_state()
    state.set_env(BUCKET, (aws_account_id + "-" + resource_group_name))
    LOGGER.debug("Environment variable %s was set autoamtically as %s" %
                (BUCKET, state[BUCKET]))


def _update_state(
    config: Dict,
    vars: Dict = {}) -> None:
    """Set environment variable and in-memory variables
    Warning: environment variables are inherited to subprocess. The sensitive
    information may be compromised by a bad subprocess.
    """
    state = get_state()
    LOGGER.debug("Setting environment variables from config.")

    if SECRETS:
        state.update(SECRETS)

    for v in config.get("envs", list()):
        if v.get("value") is None:
            v["value"] = _get_secret(v["key"])
        if v["value"]:
            state.set_env(v["key"], v["value"], trust=True)

    for v in config.get("vars", list()):
        state[v["key"]] = v["value"]

    state.update(vars)

    if not state.get(BUCKET):
        try:
            platform = cloud._get_platform()
            aws_account_id = platform.get_account_id()
        except Exception:
            pass
        else:
            if state.get(RESOURCE_GROUP):
                _set_bucket_name(state[RESOURCE_GROUP], aws_account_id)

    if not state.get(BUCKET):
        LOGGER.warning(("Environment variable %s is not set. " +
                        "Remote file read/write will fail.") %
                       BUCKET)


def _read_project_remote(workspace_dir) -> Dict:
    """Read the config from remote parameters store (e.g. AWS SSM)
    """
    state = get_state()
    LOGGER.debug("Reading precompiled config from remote.")
    state.validate_env([RESOURCE_GROUP, TASK,
                        CLOUD_PROVIDER, CLOUD_PLATFORM])
    platform = cloud._get_platform(provider_name=state.get(CLOUD_PROVIDER),
                                   platform_name=state.get(CLOUD_PLATFORM))
    account_id = platform.login()
    if not account_id:
        raise Exception("Failed to login to cloud account. " +
                        "Did you forget set credentials such as AWS_PROFILE?")
    if not state.get(BUCKET):
        _set_bucket_name(state[RESOURCE_GROUP], account_id)
    project_file_path = os.path.join(workspace_dir, PROJECT_FILE)
    platform.download_file(project_file_path, PROJECT_FILE)
    with open(project_file_path, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config


def _read_project_local(project_file: str) -> Dict:
    """Read project.yml file from the local project directory
    """
    state = get_state()
    LOGGER.debug("Reading configurations from " + project_file)
    with open(project_file, "r") as f:
        project = yaml.load(f, Loader=yaml.FullLoader)

    deploy_env = project.get("deploy", dict())
    for key in deploy_env:
        full_key = ENV_PREFIX + key.upper()
        value = deploy_env[key]
        if key in ["resource_group", "task"]:
            value = state["_stage-"] + value
        if state.is_allowed_env(full_key):
            state.set_env(full_key, value)
        else:
            state[full_key] = value

    cloud_provider_name = project.get("deploy", dict()).get("cloud_provider")
    cloud_platform_name = project.get("deploy", dict()).get("cloud_platform")
    if cloud_provider_name and cloud_platform_name:
        platform = cloud._get_platform(provider_name=cloud_provider_name,
                                       platform_name=cloud_platform_name)
        LOGGER.debug("Platform: " + platform.NAME)

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
    LOGGER.debug("Fetching the secrets from the remote parameter store.")
    global SECRETS
    SECRETS = {}
    params = platform.get_all_parameters()
    for key in params.keys():
        SECRETS[key] = params[key]["value"]


def _secrets_get_local(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> Dict:
    """Load secrets from local file

    See secrets_push for the local file specification.
    """
    global SECRETS
    SECRETS = {}
    if vars.get("secrets_dir"):
        secrets_dir = vars["secrets_dir"]
    else:
        secrets_dir = os.path.join(project_dir, SECRETS_DIR)
    secrets_file = os.path.join(secrets_dir, SECRETS_FILE)

    if not os.path.isfile(secrets_file):
        LOGGER.warning(secrets_file + " does not exsist")
        return None
    with open(secrets_file, "r") as f:
        LOGGER.debug("Reading secrets from local file: " + secrets_file)
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
    yes: bool =False,
    **kwargs) -> None:
    """`handoff secrets push -p <project_directory> -v secrets_dir=<secrets_dir>`

    Push the contents of <secrets_file> to remote parameter store

    --vars secrets_dir (.secrets): The directory containing secrets.yml file, which is a YAML file storing secrets
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
        skip_msg = ""
        if not secrets[key].get("push", True):
            skip_msg = " SKIP PUSH"
        print("  - " + key + " (" + secrets[key].get("level", "task") +
              " level)" + skip_msg)

    if not yes:
        response = input("Proceed? (y/N)")
        if response.lower() not in ["yes", "y"]:
            return "abort"

    for key in secrets:
        if not secrets[key].get("push", True):
            continue
        level = secrets[key].get("level", "task")
        platform.push_parameter(
            key, SECRETS[key],
            resource_group_level=(level.lower().strip() == "resource group"),
            **kwargs)
    return "success"


def secrets_delete(
    project_dir: str,
    workspace_dir: str,
    yes: bool = False,
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

    for key in secrets.keys():
        skip_msg = ""
        if not secrets[key].get("push", True):
            skip_msg = " SKIP DELETE"
        print("  - " + key + " (" + secrets[key].get("level", "task") +
              " level)" + skip_msg)

    if not yes:
        response = input("Proceed? (y/N)")
        if response.lower() not in ["yes", "y"]:
            return "abort"

    for key in secrets:
        if not secrets[key].get("push", True):
            continue
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
    return "success"


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
    LOGGER.debug("Fetching the secrets from the remote parameter store.")
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
    return secret_list


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

    LOGGER.debug("Copying the remote artifacts from last to runs " +
                 state.get(BUCKET))

    platform = cloud._get_platform(provider_name=state.get(CLOUD_PROVIDER),
                                   platform_name=state.get(CLOUD_PLATFORM))

    dest_dir = os.path.join(ARTIFACTS_DIR,
                            BUCKET_ARCHIVE_PREFIX,
                            datetime.datetime.utcnow().isoformat())
    platform.copy_dir_to_another_bucket(
        os.path.join(ARTIFACTS_DIR, BUCKET_CURRENT_PREFIX), dest_dir)
    return "success"


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

    LOGGER.debug("Downloading artifacts from the remote storage " +
                 state.get(BUCKET))

    platform = cloud._get_platform(provider_name=state.get(CLOUD_PROVIDER),
                                   platform_name=state.get(CLOUD_PLATFORM))

    artifacts_dir = os.path.join(workspace_dir, ARTIFACTS_DIR)
    remote_dir = os.path.join(ARTIFACTS_DIR, BUCKET_CURRENT_PREFIX)

    platform.download_dir(artifacts_dir, remote_dir)
    return "success"


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

    LOGGER.debug("Pushing local artifacts to the remote storage " +
                 state.get(BUCKET))

    platform = cloud._get_platform(provider_name=state.get(CLOUD_PROVIDER),
                                   platform_name=state.get(CLOUD_PLATFORM))

    artifacts_dir = os.path.join(workspace_dir, ARTIFACTS_DIR)
    prefix = os.path.join(ARTIFACTS_DIR, BUCKET_CURRENT_PREFIX)
    platform.upload_dir(artifacts_dir, prefix)
    return "success"


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

    LOGGER.debug("Deleting artifacts from the remote storage " +
                 state.get(BUCKET))

    platform = cloud._get_platform(provider_name=state.get(CLOUD_PROVIDER),
                                   platform_name=state.get(CLOUD_PLATFORM))

    dir_name = os.path.join(ARTIFACTS_DIR, BUCKET_CURRENT_PREFIX)
    platform.delete_dir(dir_name)
    return "success"


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

    LOGGER.debug("Downloading config files from the remote storage " +
                 state.get(BUCKET))

    platform = cloud._get_platform(provider_name=state.get(CLOUD_PROVIDER),
                                   platform_name=state.get(CLOUD_PLATFORM))

    # First download to the local templates directory, then parse to save
    # in the workspace files directory.
    templates_dir = os.path.join(workspace_dir, TEMPLATES_DIR)
    files_dir = os.path.join(workspace_dir, FILES_DIR)
    # Remote files are templates that can contain variables.
    remote_dir = FILES_DIR
    platform.download_dir(templates_dir, remote_dir)
    # Parse and save to workspace/files
    _parse_template_files(templates_dir, files_dir)
    return "success"


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

    LOGGER.debug("Copying files from the local project directory " +
                 project_dir)

    project_files_dir = os.path.join(project_dir, FILES_DIR)
    if os.path.exists(project_files_dir):
        files_dir = os.path.join(workspace_dir, FILES_DIR)
        if os.path.exists(files_dir):
            shutil.rmtree(files_dir)
        _parse_template_files(project_files_dir, files_dir)
    return "success"


def files_push(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff files push -p <project_directory>`
    Push the contents of <project_dir>/files and <project_dir>/templates
    to remote storage"""
    platform = cloud._get_platform()

    files_dir = os.path.join(project_dir, FILES_DIR)
    prefix = FILES_DIR
    platform.upload_dir(files_dir, prefix)
    return "success"


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
    dir_name = FILES_DIR
    platform.delete_dir(dir_name)
    return "success"


def _config_get(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> Dict:
    """Read configs from remote parameter store and copy them to workspace dir
    """
    if not workspace_dir:
        raise Exception("Workspace directory is not set")
    LOGGER.debug("Reading configurations from remote parameter store.")
    precompiled_config = _read_project_remote(workspace_dir)

    _secrets_get(project_dir, workspace_dir, **kwargs)
    _update_state(precompiled_config, vars=vars)

    return precompiled_config


def _config_get_local(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
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
    project = _read_project_local(os.path.join(project_dir, PROJECT_FILE))
    config.update(project)

    _update_state(config, vars=vars)

    return config


def config_push(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> None:
    """`handoff config push -p <project_directory>`
    Push project.yml and the contents of project_dir/config as a secure
    parameter key.
    """
    platform = cloud._get_platform()
    platform.upload_file(os.path.join(project_dir, PROJECT_FILE), PROJECT_FILE)
    return "success"


def config_delete(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff config delete -p <project_directory>`
    Delete the project configuration from the remote parameter store.
    """
    platform = cloud._get_platform()
    platform.delete_file(PROJECT_FILE)
    return "success"


def config_deleteold(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff config delete -p <project_directory>`
    Delete the project configuration from the remote parameter store.
    """
    platform = cloud._get_platform()
    platform.delete_parameter("config")
    return "success"


def config_print(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff config print -p <project_directory>`
    Print the project configuration in the remote parameter store.
    """
    return _config_get(project_dir, workspace_dir)


def project_push(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff project push -p <project_directory>`
    Push config, files, secrets all together
    """
    config_push(project_dir, workspace_dir, **kwargs)
    files_push(project_dir, workspace_dir, **kwargs)
    secrets_push(project_dir, workspace_dir, **kwargs)
    return "success"


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
    return "success"


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

    if not project.get("installs"):
        raise Exception("installs section is not defined")

    os.chdir(workspace_dir)
    for install in project["installs"]:
        if install.get("venv"):
            _make_python_venv(install["venv"])
        _install(install["command"], install.get("venv"))
    return "sucess"

def version(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """Print handoff version
    """
    return VERSION
