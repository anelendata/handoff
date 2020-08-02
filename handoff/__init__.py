import argparse, datetime, json, logging, os, sys
from lxml import html
import requests

from .core import admin, task
from .config import (VERSION, ARTIFACTS_DIR, PROJECT_FILE, BUCKET, DOCKER_IMAGE,
                     RESOURCE_GROUP, TASK,
                     IMAGE_VERSION, PROVIDER, PLATFORM)
from . import docker, plugins, provider


LOGGER = logging.getLogger(__name__)


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


def _list_core_commands():
    return str(list(_list_commands(admin, True).keys()) +
               list(_list_commands(task, True).keys()))


def _run_subcommand(module, command, project_dir, workspace_dir, data,
                    **kwargs):
    prev_wd = os.getcwd()
    commands = _list_commands(module, False)
    if command in commands:
        commands[command](project_dir, workspace_dir, data)
    else:
        print("Invalid command: %s\nAvailable commands are %s" %
              (command, commands.keys()))
    os.chdir(prev_wd)


def _run_task_subcommand(command, project_dir, workspace_dir, data,
                         push_artifacts=False, **kwargs):
    prev_wd = os.getcwd()
    commands = _list_commands(task, True)
    if command not in commands:
        print("Invalid command: %s\nAvailable commands are %s" %
              (command, _list_core_commands()))
        return

    admin.workspace_init(project_dir, workspace_dir, data)

    remote_ops = ["run", "run remote_config"]
    local_ops = ["run local", "show commands"]
    if command in remote_ops:
        if not os.environ.get(RESOURCE_GROUP) or not os.environ.get(TASK):
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
    state = commands[command](config, data)

    end = datetime.datetime.utcnow()
    LOGGER.info("Job ended at " + str(end))
    duration = end - start
    LOGGER.info("Processed in " + str(duration))

    if state:
        with open(os.path.join(ARTIFACTS_DIR, "state"), "w") as f:
            f.write(state)

    os.chdir(prev_wd)

    if push_artifacts:
        if not os.environ.get(BUCKET):
            raise Exception("Cannot push artifacts. BUCKET environment variable is not set")
        admin.artifacts_push(project_dir, workspace_dir, data)
        admin.artifacts_archive(project_dir, workspace_dir, data)


def do(top_command, sub_command, project_dir, workspace_dir, data, **kwargs):
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
        admin_commands[command](project_dir, workspace_dir, data, **kwargs)
        os.chdir(prev_wd)
        check_update()
        return

    if top_command == "docker":
        _run_subcommand(docker, sub_command, project_dir, workspace_dir, data,
                        **kwargs)
        check_update()
        return

    if top_command == "provider":
        admin.config_get_local(project_dir, workspace_dir, data)
        if os.environ.get(DOCKER_IMAGE) and not os.environ.get(IMAGE_VERSION):
            image_version = docker.get_latest_version(
                project_dir, workspace_dir, data)
            if image_version:
                os.environ[IMAGE_VERSION] = image_version
        _run_subcommand(provider, sub_command, project_dir, workspace_dir,
                        data, **kwargs)
        check_update()
        return

    if top_command in plugin_modules.keys():
        _run_subcommand(plugin_modules[top_command], sub_command, project_dir,
                        workspace_dir, data, **kwargs)
        check_update()
        return

    print("Unrecognized command %s. Run handoff -h for help." % command)


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


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
    print("See what's new at https://dev.handoff.cloud/en/latest/history.html\n")


def main():
    parser = argparse.ArgumentParser(
        description="Run parameterized Unix pipeline command. Try running: `handoff tutorial start` in a new directory. Check out https://dev.handoff.cloud to learn more.")
    parser.add_argument("command", type=str, help="command")
    parser.add_argument("subcommand", type=str, nargs="?", default="",
                        help="subcommand")
    parser.add_argument("-d", "--data", type=str, default="{}",
                        help="Data required for the command as a JSON string")
    parser.add_argument("-p", "--project-dir", type=str, default=None,
                        help="Specify the location of project directory")
    parser.add_argument("-w", "--workspace-dir", type=str, default=None,
                        help="Location of workspace directory")
    parser.add_argument("-a", "--push-artifacts", action="store_true",
                        help="Push artifacts to remote at the end of the run")
    parser.add_argument("-t", "--allow-advanced-tier", action="store_true",
                        help="Allow AWS SSM Parameter Store Advanced tier")
    parser.add_argument("--profile", type=str, default=None,
                        help="Profile name for logging in to platform")
    parser.add_argument("--provider", type=str, default="aws",
                        help="Cloud provider name")
    parser.add_argument("--platform", type=str, default="fargate",
                        help="Cloud platform name")

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        check_update()
        sys.exit(1)

    args = parser.parse_args()
    data_json = args.data
    try:
        data = json.loads(data_json)
    except json.JSONDecodeError:
        data = json.loads(data_json[0:-1])

    os.environ[PROVIDER] = args.provider
    os.environ[PLATFORM] = args.platform

    kwargs = dict()
    kwargs["allow_advanced_tier"] = args.allow_advanced_tier
    kwargs["profile"] = args.profile
    kwargs["push_artifacts"] = args.push_artifacts

    do(args.command, args.subcommand,
       args.project_dir, args.workspace_dir,
       data, **kwargs)


if __name__ == "__main__":
    main()
