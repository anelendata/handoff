import datetime, json, logging, os, shutil, sys, subprocess
import yaml

from jinja2 import Template as _Template

from handoff.services import cloud
from handoff.config import (ENV_PREFIX, VERSION, ARTIFACTS_DIR, BUCKET,
                            BUCKET_ARCHIVE_PREFIX, BUCKET_CURRENT_PREFIX,
                            CONFIG_DIR, DOCKER_IMAGE, FILES_DIR, TEMPLATES_DIR,
                            SECRETS_DIR, SECRETS_FILE,
                            RESOURCE_GROUP, PROJECT_FILE, TASK,
                            CLOUD_PROVIDER, CLOUD_PLATFORM, get_state)
from handoff import utils
from handoff.utils import pyvenvx

LOGGER = utils.get_logger(__name__)

SECRETS = None


def _workspace_get_dirs(workspace_dir):
    config_dir = os.path.join(workspace_dir, CONFIG_DIR)
    artifacts_dir = os.path.join(workspace_dir, ARTIFACTS_DIR)
    files_dir = os.path.join(workspace_dir, FILES_DIR)
    return config_dir, artifacts_dir, files_dir


def _install(install, venv_path=None):
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


def _make_python_venv(venv_path):
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


def _write_config_files(workspace_config_dir, precompiled_config):
    if not os.path.exists(workspace_config_dir):
        os.mkdir(workspace_config_dir)
    for r in precompiled_config.get("files", []):
        with open(os.path.join(workspace_config_dir, r["name"]), "w") as f:
            f.write(r["value"])


def _parse_template_files(templates_dir, workspace_files_dir):
    state = get_state()
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


def _get_secret(key):
    global SECRETS
    if SECRETS is None:
        raise Exception("Secrets are not loaded")
    return SECRETS.get(key)


def _update_state(config):
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
        state.set_env(v["key"], v["value"], trust=True)

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


def _read_project_remote():
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


def _read_project_local(project_file):
    """Read project.yml file from the local project directory
    """
    state = get_state()
    LOGGER.info("Reading configurations from " + project_file)
    with open(project_file, "r") as f:
        project = yaml.load(f, Loader=yaml.FullLoader)

    deploy_env = project.get("deploy", dict()).get("envs", dict())
    for key in deploy_env:
        full_key = ENV_PREFIX + key.upper()
        if state.is_allowed_env(full_key):
            state.set_env(full_key, deploy_env[key])
        else:
            state[full_key] = deploy_env[key]

    cloud_provider_name = project.get("deploy", dict()).get("provider")
    cloud_platform_name = project.get("deploy", dict()).get("platform")
    if cloud_provider_name and cloud_platform_name:
        platform = cloud._get_platform(provider_name=cloud_provider_name,
                                       platform_name=cloud_platform_name)
        LOGGER.info("Platform: " + platform.NAME)

    return project


def _secrets_get(project_dir, workspace_dir, data, **kwargs):
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
    if params:
        SECRETS.update(params)


def _secrets_get_local(project_dir, workspace_dir, data, **kwargs):
    """Load secrets from local file
    --data file (.secrets/secrets.yml): The YAML file storing secrets
    with format:
    key1:
        value: value1
        # The value is stored as a resource group level secret and can be
        # shared among the projects under the same group.
        resource_group_level: false
    """
    global SECRETS
    SECRETS = {}
    if data.get("file"):
        secrets_file = data["file"]
    else:
        secrets_file = os.path.join(project_dir, SECRETS_DIR, SECRETS_FILE)
    state = get_state()
    if not os.path.isfile(secrets_file):
        LOGGER.warning(secrets_file + " does not exsist")
        return None
    with open(secrets_file, "r") as f:
        LOGGER.info("Reading secrets from local file: " + secrets_file)
        # <key>:
        #   value: <value>
        #   level: resource_group|task
        secrets = yaml.load(f, Loader=yaml.FullLoader)
    for key in secrets:
        if secrets[key].get("value"):
            SECRETS[key] = secrets[key]["value"]
        elif secrets[key].get("file"):
            full_path = os.path.join(project_dir, SECRETS_DIR,
                                     secrets[key].get("file"))
            if not os.path.isfile(full_path):
                raise Exception(full_path + " does not exist")
            with open(full_path, "r") as f:
                SECRETS[key] = f.read()
        elif secrets[key].get("resource_group_level"):
            LOGGER.warning("Unregistered resource_group_level secret: %s" %
                           key)
        else:
            raise Exception("Neither value or file defined for task-level " +
                            "secret key " + key)
        if SECRETS.get(key) is not None:
            # Automatically register to state (on-memory)
            state[key] = SECRETS[key]
    return secrets


def secrets_push(project_dir, workspace_dir, data, **kwargs):
    """`handoff secrets push -p <project_directory> -d file=<secrets_file>`

    Push the contents of <secrets_file> to remote parameter store

    --data file (.secrets/secrets.yml): The YAML file storing secrets
    with format:
    key1:
        value: value1
        # The value is stored as a resource group level secret and can be
        # shared among the projects under the same group.
        resource_group_level: false
    """
    state = get_state()
    state.validate_env([RESOURCE_GROUP, TASK, CLOUD_PROVIDER, CLOUD_PLATFORM])
    platform = cloud._get_platform()
    secrets = _secrets_get_local(project_dir, workspace_dir, data, **kwargs)

    if not secrets:
        return
    print("Putting the following keys to remote parameter store:")

    if "config" in secrets:
        raise Exception("secrets with name \"config\" is reserved by handoff.")

    for key in secrets:
        print("  - " + key)
    response = input("Proceed? (y/N)")
    if response.lower() not in ["yes", "y"]:
        print("aborting")
        return

    for key in secrets:
        resource_group_level = secrets[key].get("resource_group_level")
        platform.push_parameter(key, SECRETS[key],
                                resource_group_level=resource_group_level,
                                **kwargs)


def secrets_delete(project_dir, workspace_dir, data, **kwargs):
    """`handoff secrets delete -p <project_directory> -d file=<secrets_file>`

    Delete the contents of <secrets_file> to remote parameter store
    By default, .secrets/secrets.yml in the current working directory is
    searched for the list of the secrets.
    """
    state = get_state()
    state.validate_env([RESOURCE_GROUP, TASK, CLOUD_PROVIDER, CLOUD_PLATFORM])
    platform = cloud._get_platform()
    secrets = _secrets_get_local(project_dir, workspace_dir, data, **kwargs)

    if not secrets:
        return
    print("Deleting the following keys to remote parameter store:")

    for key in secrets:
        print("  - " + key)
    response = input("Proceed? (y/N)")
    if response.lower() not in ["yes", "y"]:
        print("aborting")
        return

    for key in secrets:
        resource_group_level = secrets[key].get("resource_group_level")
        try:
            platform.delete_parameter(key,
                                      resource_group_level=resource_group_level,
                                      **kwargs)
        except Exception:
            LOGGER.warning("%s does not exist in remote parameter store." %
                           key)


def artifacts_archive(project_dir, workspace_dir, data, **kwargs):
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


def artifacts_get(project_dir, workspace_dir, data, **kwargs):
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

    _, artifacts_dir, _ = _workspace_get_dirs(workspace_dir)
    remote_dir = os.path.join(BUCKET_CURRENT_PREFIX, ARTIFACTS_DIR)

    platform.download_dir(remote_dir, artifacts_dir)


def artifacts_push(project_dir, workspace_dir, data, **kwargs):
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

    _, artifacts_dir, _ = _workspace_get_dirs(workspace_dir)
    prefix = os.path.join(BUCKET_CURRENT_PREFIX, ARTIFACTS_DIR)
    platform.upload_dir(artifacts_dir, prefix)


def artifacts_delete(project_dir, workspace_dir, data, **kwargs):
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


def files_get(project_dir, workspace_dir, data, **kwargs):
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

    _, _, files_dir = _workspace_get_dirs(workspace_dir)
    remote_dir = os.path.join(BUCKET_CURRENT_PREFIX, FILES_DIR)
    platform.download_dir(remote_dir, files_dir)

    remote_dir = os.path.join(BUCKET_CURRENT_PREFIX, TEMPLATES_DIR)
    templates_dir = os.path.join(workspace_dir, TEMPLATES_DIR)
    platform.download_dir(remote_dir, templates_dir)
    _parse_template_files(templates_dir,
                          os.path.join(workspace_dir, FILES_DIR))


def files_get_local(project_dir, workspace_dir, data, **kwargs):
    """`handoff files get local -p <project_directory> -w <workspace_directory>`
    Copy files from the local <project_dir> to <workspace_dir>

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
        _, _, files_dir = _workspace_get_dirs(workspace_dir)
        if os.path.exists(files_dir):
            shutil.rmtree(files_dir)
        shutil.copytree(project_files_dir, files_dir)

    templates_dir = os.path.join(project_dir, TEMPLATES_DIR)
    _parse_template_files(templates_dir,
                          os.path.join(workspace_dir, FILES_DIR))


def files_push(project_dir, workspace_dir, data, **kwargs):
    """`handoff files push -p <project_directory>`
    Push the contents of <project_dir>/files and <project_dir>/templates
    to remote storage"""
    platform = cloud._get_platform()

    files_dir = os.path.join(project_dir, FILES_DIR)
    prefix = os.path.join(BUCKET_CURRENT_PREFIX, FILES_DIR)
    platform.upload_dir(files_dir, prefix)

    templates_dir = os.path.join(project_dir, TEMPLATES_DIR)
    prefix = os.path.join(BUCKET_CURRENT_PREFIX, TEMPLATES_DIR)
    platform.upload_dir(templates_dir, prefix)


def files_delete(project_dir, workspace_dir, data, **kwargs):
    """`handoff files delete -p <project_directory>`
    Delete files and templates from the remote storage
    """
    state = get_state()
    state.validate_env([RESOURCE_GROUP, TASK, CLOUD_PROVIDER, CLOUD_PLATFORM,
                        BUCKET])

    platform = cloud._get_platform()
    dir_name = os.path.join(BUCKET_CURRENT_PREFIX, FILES_DIR)
    platform.delete_dir(dir_name)
    dir_name = os.path.join(BUCKET_CURRENT_PREFIX, TEMPLATES_DIR)
    platform.delete_dir(dir_name)


def _config_get(project_dir, workspace_dir, data, **kwargs):
    """Read configs from remote parameter store and copy them to workspace dir
    """
    if not workspace_dir:
        raise Exception("Workspace directory is not set")
    LOGGER.info("Reading configurations from remote parameter store.")
    config_dir, _, _ = _workspace_get_dirs(workspace_dir)
    precompiled_config = _read_project_remote()

    _secrets_get(project_dir, workspace_dir, data, **kwargs)
    _update_state(precompiled_config)

    _write_config_files(config_dir, precompiled_config)

    return precompiled_config


def _config_get_local(project_dir, workspace_dir, data, **kwargs):
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

    _secrets_get_local(project_dir, workspace_dir, data, **kwargs)
    _update_state(config)

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
    """`handoff config push -p <project_directory>`
    Push project.yml and the contents of project_dir/config as a secure
    parameter key.
    """
    LOGGER.info("Compiling config from %s" % project_dir)
    config_obj = _config_get_local(project_dir, workspace_dir, data)
    config_obj["version"] = VERSION
    config = json.dumps(config_obj)

    allow_advanced_tier = data.get("allow_advanced_tier", False)
    if type(allow_advanced_tier) is not bool:
        raise Exception("allow_advanced_tier must be True/False")

    platform = cloud._get_platform()
    platform.push_parameter("config", config,
                            allow_advanced_tier=allow_advanced_tier)


def config_delete(project_dir, workspace_dir, data, **kwargs):
    """`handoff config delete -p <project_directory>`
    Delete the project configuration from the remote parameter store.
    """
    platform = cloud._get_platform()
    platform.delete_parameter("config")


def config_print(project_dir, workspace_dir, data, **kwargs):
    """`handoff config print -p <project_directory>`
    Print the project configuration in the remote parameter store.
    """
    print(json.dumps(_config_get(project_dir, workspace_dir, data)))


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


def version(project_dir, workspace_dir, data, **kwargs):
    """Print handoff version
    """
    print(VERSION)
