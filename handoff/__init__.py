import argparse, datetime, json, logging, os, sys, threading, time
from pathlib import Path
import yaml
from lxml import html
import requests

from handoff.config import (VERSION, HANDOFF_DIR,
                            ARTIFACTS_DIR, PROJECT_FILE, STATE_FILE,
                            BUCKET, RESOURCE_GROUP, TASK,
                            DOCKER_IMAGE, IMAGE_VERSION,
                            CLOUD_PROVIDER, CLOUD_PLATFORM,
                            CONTAINER_PROVIDER,
                            get_state)
from handoff.core import admin, task
from handoff.utils import bcolors, get_logger
from handoff.services import cloud, container
from handoff import plugins

LOGGER = get_logger("handoff")

LATEST_AVAILABLE_VERSION = None
ANNOUNCEMENTS = None


def _load_data_params(arg_list):
    data = {}
    for a in arg_list:
        pos = a.find("=")
        if pos < 0:
            raise ValueError("data argument list format error")
        key = a[0:pos].strip()
        value = a[pos + 1:].strip()
        if not key or not value:
            raise ValueError("data argument list format error")
        data[key] = value
    return data


def _list_plugins():
    modules = dict()
    objects = dir(plugins)
    for name in objects:
        if name[0] == "_":
            continue
        obj = getattr(plugins, name)

        if not callable(obj):
            modules[name] = obj
    return modules


def _list_commands(module, split_first=False):
    commands = dict()
    objects = dir(module)
    for name in objects:
        if name[0] == "_":
            continue
        obj = getattr(module, name)

        # Make it "command sub_command" format
        if split_first:
            name = name.replace("_", " ", 1)

        if callable(obj):
            commands[name] = obj
    return commands


def _run_subcommand(module, command, project_dir, workspace_dir, data,
                    show_help, **kwargs):
    prev_wd = os.getcwd()
    commands = _list_commands(module, False)
    if command in commands:
        if show_help:
            print(commands[command].__doc__ or
                  "No help doc available for %s %s" %
                  (module.__name__.split(".")[-1], command))
            os.chdir(prev_wd)
            return

        commands[command](project_dir, workspace_dir, data)
    else:
        if command:
            print("Invalid command")
        print("Available commands:")
        for key in commands.keys():
            print(" " * 4 + key + ": " +
                  (commands[key].__doc__ or " ").splitlines()[0])
        print("'handoff %s <command>'--help for more info" %
              module.__name__.split(".")[-1])
    os.chdir(prev_wd)


def _run_task_subcommand(command, project_dir, workspace_dir, data,
                         push_artifacts=False, **kwargs):
    state = get_state()
    prev_wd = os.getcwd()
    commands = _list_commands(task, True)

    admin.workspace_init(project_dir, workspace_dir, data)

    remote_ops = ["run", "run remote_config"]
    local_ops = ["run local", "show commands"]
    if command in remote_ops:
        if not state.get_env(RESOURCE_GROUP) or not state.get_env(TASK):
            admin.config_get_local(project_dir, workspace_dir, data)
        config = admin.config_get(project_dir, workspace_dir, data)
        admin.files_get(project_dir, workspace_dir, data)
        admin.artifacts_get(project_dir, workspace_dir, data)
    elif command in local_ops:
        config = admin.config_get_local(project_dir, workspace_dir, data)
        admin.files_get_local(project_dir, workspace_dir, data)
    else:
        config = {}
    os.chdir(workspace_dir)

    LOGGER.info("Running %s in %s directory" % (command, workspace_dir))
    start = datetime.datetime.utcnow()
    LOGGER.info("Job started at " + str(start))

    # Run the command
    output = commands[command](config, data)

    end = datetime.datetime.utcnow()
    LOGGER.info("Job ended at " + str(end))
    duration = end - start
    LOGGER.info("Processed in " + str(duration))

    if output:
        with open(os.path.join(ARTIFACTS_DIR, STATE_FILE), "w") as f:
            f.write(output)

    os.chdir(prev_wd)

    if push_artifacts:
        if not state.get_env(BUCKET):
            raise Exception("Cannot push artifacts. BUCKET environment" +
                            "variable is not set")
        admin.artifacts_push(project_dir, workspace_dir, data)
        admin.artifacts_archive(project_dir, workspace_dir, data)


def do(top_command, sub_command, project_dir, workspace_dir, data,
       show_help=False, **kwargs):
    state = get_state()
    command = (top_command + " " + sub_command).strip()

    if workspace_dir:
        admin.workspace_init(project_dir, workspace_dir, data)

    plugin_modules = _list_plugins()

    if command in _list_commands(task, True):
        # Wrap with try except for better logging in docker execution
        try:
            _run_task_subcommand(command, project_dir, workspace_dir, data,
                                 **kwargs)
        except Exception as e:
            LOGGER.critical(e)
            raise
        return

    admin_commands = _list_commands(admin, True)
    if command in admin_commands:
        prev_wd = os.getcwd()
        if show_help:
            print(admin_commands[command].__doc__,
                  "No help doc available for " + command)
            os.chdir(prev_wd)
            return

        admin_commands[command](project_dir, workspace_dir, data, **kwargs)
        os.chdir(prev_wd)
        print_update()
        print_announcements()
        return

    if top_command == "container":
        _run_subcommand(container, sub_command, project_dir, workspace_dir, data,
                        show_help, **kwargs)
        return

    if top_command == "cloud":
        if show_help:
            _run_subcommand(cloud, sub_command, project_dir, workspace_dir,
                            data, show_help, **kwargs)
            return

        admin.config_get_local(project_dir, workspace_dir, data)
        if state.get_env(DOCKER_IMAGE) and not state.get_env(IMAGE_VERSION):
            image_version = container.get_latest_image_version(
                project_dir, workspace_dir, data)
            if image_version:
                state.set_env(IMAGE_VERSION, image_version)

        _run_subcommand(cloud, sub_command, project_dir, workspace_dir,
                        data, show_help, **kwargs)
        return

    if top_command in plugin_modules.keys():
        _run_subcommand(plugin_modules[top_command], sub_command, project_dir,
                        workspace_dir, data, show_help, **kwargs)
        return

    print("Unrecognized command %s. Run handoff -h for help." % command)


def check_update():
    global LATEST_AVAILABLE_VERSION
    try:
        response = requests.get("https://pypi.org/simple/handoff")
    except Exception:
        return
    tree = html.fromstring(response.content)
    package_list = [package for package in tree.xpath("//a/text()")]
    package_list.sort(reverse=True)
    LATEST_AVAILABLE_VERSION = package_list[0][:-len(".tar.gz")]


def print_update():
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


def check_announcements(**kwargs):
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


def print_announcements():
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


def main():
    threading.Thread(target=check_update).start()
    admin_command_list = "\n- ".join(_list_commands(admin, True))
    task_command_list = "\n- ".join(_list_commands(task, True))
    plugin_list = "\n- ".join(_list_plugins().keys())
    parser = argparse.ArgumentParser(
        add_help=False,
        description=("Run parameterized Unix pipeline command."))

    parser.add_argument("command", type=str, help="command")
    parser.add_argument("subcommand", type=str, nargs="*", default="",
                        help="subcommand")

    parser.add_argument("-p", "--project-dir", type=str, default=None,
                        help="Specify the location of project directory")
    parser.add_argument("-w", "--workspace-dir", type=str, default=None,
                        help="Location of workspace directory")
    parser.add_argument("-d", "--data", type=str, nargs="*", default="",
                        help="Data required for the command a='x' b='y' ...")
    parser.add_argument("-a", "--push-artifacts", action="store_true",
                        help="Push artifacts to remote at the end of the run")

    parser.add_argument("-h", "--help", action="store_true")
    parser.add_argument("-l", "--log-level", type=str, default="info",
                        help="Set log level (DEBUG, INFO, WARNING, ERROR," +
                        "CRITICAL)")

    parser.add_argument("--cloud-provider", type=str, default="aws",
                        help="Cloud provider name")
    parser.add_argument("--cloud-platform", type=str, default="fargate",
                        help="Cloud platform name")
    parser.add_argument("--cloud-profile", type=str, default=None,
                        help="Profile name for logging in to platform")

    parser.add_argument("--container-provider", type=str, default="docker",
                        help="Container provider name")

    parser.add_argument("--allow-advanced-tier", action="store_true",
                        help="Allow AWS SSM Parameter Store Advanced tier")

    if len(sys.argv) == 1 or sys.argv[1] in ["-h", "--help"]:
        parser.print_help(sys.stderr)
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
- docker
- %s

handoff <command> -h for more help.\033[0m
""" % (admin_command_list, task_command_list, plugin_list))

        print_update()
        sys.exit(1)

    args = parser.parse_args()

    LOGGER.setLevel(args.log_level.upper())

    data = _load_data_params(args.data)

    os.environ[CLOUD_PROVIDER] = args.cloud_provider
    os.environ[CLOUD_PLATFORM] = args.cloud_platform
    os.environ[CONTAINER_PROVIDER] = args.container_provider

    kwargs = dict()
    kwargs["show_help"] = args.help
    kwargs["push_artifacts"] = args.push_artifacts
    kwargs["cloud_profile"] = args.cloud_profile
    kwargs["allow_advanced_tier"] = args.allow_advanced_tier

    if (args.project_dir and args.workspace_dir and
            args.project_dir == args.workspace_dir):
        print("Error: workspace directory must be different from " +
              "project directory.")
        exit(1)

    args.subcommand = "_".join(args.subcommand)
    threading.Thread(target=check_announcements,
                     kwargs= {"command": args.command,
                              "subcommand": args.subcommand}).start()

    do(args.command, args.subcommand,
       args.project_dir, args.workspace_dir,
       data, **kwargs)


if __name__ == "__main__":
    main()
