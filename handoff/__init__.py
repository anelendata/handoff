import argparse, datetime, json, logging, os, sys, threading, time, types
from pathlib import Path
import yaml
from lxml import html
import requests
from typing import Dict, List

from handoff.config import (VERSION, HANDOFF_DIR, ENV_PREFIX,
                            ARTIFACTS_DIR, PROJECT_FILE,
                            BUCKET, RESOURCE_GROUP, TASK,
                            CONTAINER_IMAGE, IMAGE_VERSION,
                            CLOUD_PROVIDER, CLOUD_PLATFORM,
                            CONTAINER_PROVIDER, STAGE, DEFAULT_STAGE,
                            get_state, init_state)
from handoff.core import admin, task
from handoff.utils import bcolors, get_logger
from handoff import plugins, services

LOGGER = get_logger("handoff")

LATEST_AVAILABLE_VERSION = None
ANNOUNCEMENTS = None


def _strip_outer_quotes(string: str) -> str:
    string = string.strip()
    # Avoid over stripping. Either ' or "
    if string[0] == '"':
        string = string.strip('"')
    elif string[0] == "'":
        string = string.strip("'")
    return string


def _load_param_list(arg_list: List) -> Dict:
    data = {}
    new_arg_list = []

    # fix the limitation in passing with $(eval echo $__VARS)
    for a in arg_list:
        if "=" in a:
            new_arg_list.append(a)
        else:
            new_arg_list[-1] = new_arg_list[-1] + " " + a

    for a in new_arg_list:
        pos = a.find("=")
        if pos < 0:
            raise ValueError("data argument list format error %s" % arg_list)
        key = _strip_outer_quotes(a[0:pos])
        value = _strip_outer_quotes(a[pos + 1:])

        if not key or not value:
            raise ValueError("data argument list format error: %s %s"
                             % (key, value))

        if value.lower() in ["true", "t"]:
            value = True
        elif value.lower() in ["false", "f"]:
            value = False
        else:
            # Convert to float or int when we can
            try:
                number = float(value)
                if "." not in value:
                    number = int(number)
                value = number
            except ValueError:
                pass

        data[key] = value

    LOGGER.debug("data params: %s" % data)
    return data


def _list_submodules(module) -> Dict:
    submodules = dict()
    objects = dir(module)
    for name in objects:
        if name[0] == "_":
            continue
        obj = getattr(module, name)

        if not callable(obj):
            submodules[name] = obj
    return submodules


def _list_commands(module: Dict) -> Dict:
    commands = dict()
    objects = dir(module)
    for name in objects:
        if name[0] == "_":
            continue
        obj = getattr(module, name)
        if not isinstance(obj, types.FunctionType):
            continue

        # Make it "command sub_command" format
        name = name.replace("_", " ")
        commands[name] = obj
    return commands


def _run_subcommand(module: types.ModuleType,
                    command: str,
                    project_dir: str,
                    workspace_dir: str,
                    show_help: bool,
                    **kwargs) -> None:
    prev_wd = os.getcwd()
    commands = _list_commands(module)
    if command in commands:
        if show_help:
            print(commands[command].__doc__ or
                  "No help doc available for %s %s" %
                  (module.__name__.split(".")[-1], command))
            os.chdir(prev_wd)
            return

        if workspace_dir:
            admin.workspace_init(project_dir, workspace_dir, **kwargs)
        response = commands[command](project_dir, workspace_dir, **kwargs)
    else:
        module_name = module.__name__.split(".")[-1]
        response = None
        print("Available commands:")
        for key in commands.keys():
            print("- " + module_name + " " + key + ": " +
                  (commands[key].__doc__ or " ").splitlines()[0])
        print("'handoff %s <command>'--help for more info" %
              module_name)
    os.chdir(prev_wd)
    return response


def _run_task_subcommand(
    command: str,
    project_dir: str,
    workspace_dir: str,
    push_artifacts: bool = False, **kwargs) -> None:
    state = get_state()
    prev_wd = os.getcwd()
    commands = _list_commands(task)

    admin.workspace_init(project_dir, workspace_dir, **kwargs)

    remote_ops = ["run", "run remote config"]
    local_ops = ["run local", "show commands"]

    # Load config from remote or local
    config = dict()
    if command in remote_ops:
        if project_dir:
            config = admin._config_get_local(project_dir, workspace_dir,
                                             **kwargs)
        if not state.get_env(RESOURCE_GROUP) or not state.get_env(TASK):
            raise Exception(
                "To test run with remote config, you need to" +
                " either give environmental variables as:\n" +
                "  --envs resource_group=<resource_group_name>" +
                " task=<task_name>\n"  +
                " or define them at deploy in project.yml")
        config = admin._config_get(project_dir, workspace_dir, **kwargs)
        admin.files_get(project_dir, workspace_dir, **kwargs)
        admin.artifacts_get(project_dir, workspace_dir, **kwargs)
    elif command in local_ops:
        _ = admin._secrets_get_local(project_dir, workspace_dir, **kwargs)
        config = admin._config_get_local(project_dir, workspace_dir, **kwargs)
        admin.files_get_local(project_dir, workspace_dir, **kwargs)

    os.chdir(workspace_dir)

    LOGGER.debug("Running %s in %s directory" % (command, workspace_dir))
    start = datetime.datetime.utcnow()
    LOGGER.info("Job started at " + str(start))

    # Run the command
    exit_code = 0
    try:
        commands[command](config, **kwargs)
    except Exception as e:
        LOGGER.error(str(e))
        exit_code = 1

    end = datetime.datetime.utcnow()
    LOGGER.info("Job ended at " + str(end))
    duration = end - start
    LOGGER.info("Processed in " + str(duration))

    os.chdir(prev_wd)

    push_artifacts_on_fail = config.get("deploy", {}).get(
        "push_artifacts_on_fail", True)
    if push_artifacts and (exit_code == 0 or push_artifacts_on_fail):
        if not state.get_env(BUCKET):
            raise Exception("Cannot push artifacts. BUCKET environment" +
                            "variable is not set")
        admin.artifacts_push(project_dir, workspace_dir, **kwargs)
        admin.artifacts_archive(project_dir, workspace_dir, **kwargs)


def do(
    command: str,
    project_dir: str = None,
    workspace_dir: str = None,
    show_help: bool = False,
    **kwargs) -> None:
    """Determine the command to run"""
    init_state(kwargs.get("stage", os.environ.get(STAGE, DEFAULT_STAGE)))
    state = get_state()

    envs = kwargs.get("envs", {})
    for key in envs.keys():
        value = envs[key]
        if key in ["resource_group", "task"]:
            state.set_env(key.upper() + "_NAKED", value, trust=True)
            value = state["_stage-"] + value
        try:
            state.set_env(ENV_PREFIX + key.upper(), value)
        except KeyError:
            state.set_env(key.upper(), value, trust=True)
    state.set_env(
        CLOUD_PROVIDER,
        kwargs.get("cloud_provider", state.get_env(CLOUD_PROVIDER)))
    state.set_env(CLOUD_PLATFORM,
                  kwargs.get("cloud_platform", state.get_env(CLOUD_PLATFORM)))
    state.set_env(CONTAINER_PROVIDER,
                  kwargs.get("container_provider",
                             state.get_env(CONTAINER_PROVIDER)))

    # Login will cache the cloud platform credentials to state
    try:
        services.cloud.logout()
        platform = services.cloud.get_platform(vars=kwargs["vars"])
    except Exception as e:
        LOGGER.warning(str(e))

    module_name = command.split(" ")[0]
    sub_command = command[command.find(" ") + 1:]

    plugin_modules = _list_submodules(plugins)
    service_modules = _list_submodules(services)

    if command == "server":
        from handoff import ui
        vars_ = kwargs["vars"]
        ui.server(**vars_)

    # task module implements the commands such as run, run local, show commands
    if command in _list_commands(task):
        try:
            response = _run_task_subcommand(command, project_dir, workspace_dir,
                                            **kwargs)
        except Exception as e:
            raise e
        return response

    admin_commands = _list_commands(admin)
    if command == "version":
        response = admin_commands[command](project_dir, workspace_dir, **kwargs)
        return response
    if command in admin_commands:
        prev_wd = os.getcwd()
        if show_help:
            response = (admin_commands[command].__doc__ or
                        "No help doc available for " + command)
            os.chdir(prev_wd)
            return response

        if workspace_dir:
            admin.workspace_init(project_dir, workspace_dir, **kwargs)
        admin._config_get_local(project_dir, workspace_dir, **kwargs)
        response = admin_commands[command](project_dir, workspace_dir, **kwargs)

        os.chdir(prev_wd)

        # TODO: Clean up the print out logic
        print_update()
        print_announcements()
        return response

    if module_name in service_modules:
        if show_help:
            return _run_subcommand(service_modules[module_name],
                    sub_command, project_dir, workspace_dir, show_help, **kwargs)

        if module_name != "github":
            admin._config_get_local(project_dir, workspace_dir, **kwargs)

        if module_name == "cloud":
            if state.get_env(CONTAINER_IMAGE) and not state.get_env(IMAGE_VERSION):
                image_version = service_modules["container"]._get_latest_image_version(
                    project_dir, workspace_dir, **kwargs)
                if image_version:
                    state.set_env(IMAGE_VERSION, image_version)

        return _run_subcommand(service_modules[module_name], sub_command,
                project_dir, workspace_dir, show_help, **kwargs)

    if module_name in plugin_modules.keys():
        if show_help:
            return _run_subcommand(plugin_modules[module_name], sub_command,
                                   project_dir, workspace_dir,
                                   show_help, **kwargs)

        if project_dir:
            admin._config_get_local(project_dir, workspace_dir, **kwargs)
        return _run_subcommand(plugin_modules[module_name], sub_command, project_dir,
                               workspace_dir, show_help, **kwargs)

    return("Unrecognized command %s. Run handoff -h for help." % command)


def check_update() -> None:
    global LATEST_AVAILABLE_VERSION
    try:
        response = requests.get("https://pypi.org/simple/handoff")
    except Exception:
        return
    tree = html.fromstring(response.content)
    package_list = [package for package in tree.xpath("//a/text()")]
    package_list.sort(reverse=True)
    LATEST_AVAILABLE_VERSION = package_list[0][:-len(".tar.gz")]

def print_commands() -> None:
    admin_command_list = "\n- ".join(_list_commands(admin))
    task_command_list = "\n- ".join(_list_commands(task))
    plugin_list = "\n- ".join(_list_submodules(plugins).keys())

    print("""Try running:
    handoff quick_start make
in a new directory.
Check out https://dev.handoff.cloud to learn more.

Available admin commands:
- %s

Availabe run commands:
- %s

Available subcommands:
- cloud
- container
- %s

handoff <command> -h for more help.\033[0m
""" % (admin_command_list, task_command_list, plugin_list))


def print_update() -> None:
    global LATEST_AVAILABLE_VERSION
    elapsed = 0
    while LATEST_AVAILABLE_VERSION is None and elapsed < 2.0:
        time.sleep(0.25)
        elapsed += 0.25

    if (not LATEST_AVAILABLE_VERSION or
            "handoff-" + VERSION >= LATEST_AVAILABLE_VERSION):
        return

    print(bcolors.OKGREEN)
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print(":tada: handoff Ver. %s available!" % LATEST_AVAILABLE_VERSION)
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~" + bcolors.ENDC)
    print(bcolors.BOLD + "Upgrade now:" + bcolors.ENDC +
          " pip install -U handoff\n")


def check_announcements(**kwargs) -> None:
    global ANNOUNCEMENTS
    url = "https://api.handoff.cloud/api/v1/announcements"
    try:
        response = requests.get(url, params=kwargs)
        ANNOUNCEMENTS = yaml.load(response.content, Loader=yaml.FullLoader)
        if type(ANNOUNCEMENTS) != dict:
            ANNOUNCEMENTS = None
    except Exception as e:
        LOGGER.warning(e)
    return


def print_announcements() -> None:
    global ANNOUNCEMENTS
    elapsed = 0
    while ANNOUNCEMENTS is None and elapsed < 2.0:
        time.sleep(0.25)
        elapsed += 0.25
    if not ANNOUNCEMENTS:
        return
    home = str(Path.home())
    ho_dir = os.path.join(home, HANDOFF_DIR)
    if not os.path.isdir(ho_dir):
        try:
            os.mkdir(ho_dir)
        except Exception as e:
            print("Warning: Failed to create handoff global config directory" +
                  "at %s: %s" % (ho_dir, e))
    date_file = os.path.join(ho_dir, "last_announcement_date")
    last_update = ""
    if os.path.isfile(date_file):
        with open(date_file, "r") as f:
            last_update = f.read()
    announcements = list()
    for a in ANNOUNCEMENTS.get("announcements", []):
        if a.get("date") and str(a["date"]) > last_update:
            announcements.append(a)
    if len(announcements) > 0:
        print(bcolors.OKGREEN)
        print("Announcements:" + bcolors.ENDC)
    for a in announcements:
            print(a["date"])
            print("  " + a.get("title"))
            print("  " + a.get("message"))

    try:
        with open(date_file, "w") as f:
            f.write(str(datetime.date.today()))
    except Exception as e:
        LOGGER.warning("Failed to write %s: %s" % (date_file, e))


def main() -> None:
    threading.Thread(target=check_update).start()
    parser = argparse.ArgumentParser(
        add_help=False,
        description=("handoff %s - Run parameterized Unix pipeline command." %
                     VERSION))

    parser.add_argument("command", type=str, nargs="*",
                        help="command string such as 'config push'")

    parser.add_argument("-p", "--project-dir", type=str, default=None,
                        help="Specify the location of project directory")
    parser.add_argument("-w", "--workspace-dir", type=str, default=None,
                        help="Location of workspace directory")
    parser.add_argument("-s", "--stage", type=str, default=DEFAULT_STAGE,
                        help=("Stage (default '" + DEFAULT_STAGE +
                              "'). Sets env var _stage, but keeps _stage blank when --stage 'prod'"))
    parser.add_argument("-e", "--envs", type=str, nargs="*", default="",
                        help="Define environment variables. List after this option like: -e key1=value1 key2=value2...")
    parser.add_argument("-v", "--vars", type=str, nargs="*", default="",
                        help="Extra variables for the command. List after this option like: -v key1=value1 key2=value2...")
    parser.add_argument("-y", "--yes", action="store_true",
                        help="Skip confirmations")

    parser.add_argument("-h", "--help", action="store_true")
    parser.add_argument("-l", "--log-level", type=str, default="info",
                        help="Set log level (debug, info, warning, error," +
                        "critical). Default: error for non-task commands," +
                        "info for task commands")

    parser.add_argument("--cloud-provider", type=str, default="aws",
                        help="Cloud provider name")
    parser.add_argument("--cloud-platform", type=str, default="fargate",
                        help="Cloud platform name")
    parser.add_argument("--cloud-profile", type=str, default=None,
                        help="Profile name for logging in to platform")

    parser.add_argument("--container-provider", type=str, default="docker",
                        help="Container provider name")

    parser.add_argument("-a", "--push-artifacts", action="store_true",
                        help="Push artifacts to remote at the end of the run")

    if len(sys.argv) == 1 or sys.argv[1] in ["-h", "--help"]:
        parser.print_help(sys.stderr)
        print_commands()
        print_update()
        sys.exit(1)

    args = parser.parse_args()

    if not args.command:
        parser.print_help(sys.stderr)
        print_commands()
        print_update()
        sys.exit(1)

    LOGGER.setLevel(args.log_level.upper())

    args.vars = _load_param_list(args.vars)
    args.envs = _load_param_list(args.envs)

    kwargs = dict(vars(args))
    kwargs["show_help"] = args.help
    kwargs["yes"] = args.yes

    if (args.project_dir and args.workspace_dir and
            args.project_dir == args.workspace_dir):
        Exception("workspace directory must be different from " +
                  "project directory.")

    threading.Thread(
        target=check_announcements,
        kwargs={"command": ("-".join(args.command)).strip()}).start()

    command = (" ".join(args.command)).strip()
    kwargs.pop("command")
    response = do(command, **kwargs)

    if response:
        if isinstance(response, dict) or isinstance(response, list):
            print(yaml.dump(response))
        else:
            print(response)


if __name__ == "__main__":
    main()
