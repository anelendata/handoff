import argparse, datetime, json, logging, os, sys
from lxml import html
import requests

from handoff.config import (VERSION, ARTIFACTS_DIR, PROJECT_FILE, STATE_FILE,
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
        check_update()
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
    try:
        response = requests.get("https://pypi.org/simple/handoff")
    except Exception:
        return
    tree = html.fromstring(response.content)
    package_list = [package for package in tree.xpath("//a/text()")]
    package_list.sort(reverse=True)
    latest = package_list[0][:-len(".tar.gz")]

    if "handoff-" + VERSION >= latest:
        return

    print(bcolors.OKGREEN)
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print(":tada: handoff Ver. %s available!" % latest)
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~" + bcolors.ENDC)
    print(bcolors.BOLD + "Upgrade now:" + bcolors.ENDC +
          " pip install -U handoff\n")
    print("See what's new at " +
          "https://dev.handoff.cloud/en/latest/history.html\n")


def main():
    admin_command_list = "\n- ".join(_list_commands(admin, True))
    task_command_list = "\n- ".join(_list_commands(task, True))
    plugin_list = "\n- ".join(_list_plugins().keys())
    parser = argparse.ArgumentParser(
        add_help=False,
        description=("Run parameterized Unix pipeline command."))

    parser.add_argument("command", type=str, help="command")
    parser.add_argument("subcommand", type=str, nargs="?", default="",
                        help="subcommand")

    parser.add_argument("-p", "--project-dir", type=str, default=None,
                        help="Specify the location of project directory")
    parser.add_argument("-w", "--workspace-dir", type=str, default=None,
                        help="Location of workspace directory")
    parser.add_argument("-d", "--data", type=str, default="{}",
                        help="Data required for the command as a JSON string")
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
    handoff tutorial start
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

        check_update()
        sys.exit(1)

    args = parser.parse_args()

    LOGGER.setLevel(args.log_level.upper())

    data_json = args.data
    try:
        data = json.loads(data_json)
    except json.JSONDecodeError:
        data = json.loads(data_json[0:-1])

    os.environ[CLOUD_PROVIDER] = args.cloud_provider
    os.environ[CLOUD_PLATFORM] = args.cloud_platform
    os.environ[CONTAINER_PROVIDER] = args.container_provider

    kwargs = dict()
    kwargs["show_help"] = args.help
    kwargs["push_artifacts"] = args.push_artifacts
    kwargs["cloud_profile"] = args.cloud_profile
    kwargs["allow_advanced_tier"] = args.allow_advanced_tier

    do(args.command, args.subcommand,
       args.project_dir, args.workspace_dir,
       data, **kwargs)

if __name__ == "__main__":
    main()
