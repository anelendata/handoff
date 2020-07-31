import argparse, datetime, json, logging, os
from .core import admin, runner
from .config import (ARTIFACTS_DIR, PROJECT_FILE, BUCKET, DOCKER_IMAGE,
                     IMAGE_VERSION)
from . import docker, provider


LOGGER = logging.getLogger(__name__)


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
               list(_list_commands(runner, True).keys()))


def _run_subcommand(module, command, data, project_dir, workspace_dir, **kwargs):
    commands = _list_commands(module, False)
    if command in commands:
        return commands[command](project_dir, workspace_dir, data, **kwargs)
    else:
        print("Invalid command: %s\nAvailable commands are %s" %
              (command, commands.keys()))


def do(top_command,
       sub_command,
       data,
       project_dir,
       workspace_dir,
       push_artifacts=True,
       **kwargs):
    """
    """
    if project_dir:
        # This will also set environment variables for deployment
        admin._read_project(os.path.join(project_dir, PROJECT_FILE))

    if os.environ.get(DOCKER_IMAGE) and not os.environ.get(IMAGE_VERSION):
        print("DOCKER_IMAGE: %s" % os.environ.get(DOCKER_IMAGE))
        print("IMAGE_VERSION key: %s" % IMAGE_VERSION)
        os.environ[IMAGE_VERSION] = "test"
        print("IMAGE_VERSION value: %s" % os.environ.get(IMAGE_VERSION))
        #
        #
        os.environ[IMAGE_VERSION] = docker.get_latest_version(
            project_dir, workspace_dir, data, **kwargs)

    prev_wd = os.getcwd()

    command = (top_command + " " + sub_command).strip()

    if workspace_dir:
        admin.workspace_init(project_dir, workspace_dir, data)

    # Try running admin commands
    admin_commands = _list_commands(admin, True)
    if command in admin_commands:
        # Run the admin command
        admin_commands[command](project_dir, workspace_dir, data, **kwargs)
        os.chdir(prev_wd)
        return

    if top_command == "docker":
        _run_subcommand(docker, sub_command, data, project_dir, workspace_dir, **kwargs)
        os.chdir(prev_wd)
        return

    if top_command == "provider":
        _run_subcommand(provider, sub_command, data, project_dir, workspace_dir, **kwargs)
        os.chdir(prev_wd)
        return

    # Run command
    commands = _list_commands(runner, True)
    if command not in commands:
        print("Invalid command: %s\nAvailable commands are %s" %
              (command, _list_core_commands()))
        return

    admin.workspace_init(project_dir, workspace_dir, data)

    if command == "run local":
        config = admin.config_get_local(project_dir, workspace_dir, data)
        admin.files_get_local(project_dir, workspace_dir, data)
    else:
        config = admin.config_get(project_dir, workspace_dir, data)
        admin.files_get(project_dir, workspace_dir, data)
    os.chdir(workspace_dir)

    LOGGER.info("Running %s in %s directory" % (command, workspace_dir))
    start = datetime.datetime.utcnow()
    LOGGER.info("Job started at " + str(start))

    # Run the command
    state = commands[command](config, data, **kwargs)

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


def main():
    parser = argparse.ArgumentParser(description="Run parameterized Unix pipeline command https://dev/handoff.cloud")
    parser.add_argument("command", type=str, help="command")
    parser.add_argument("subcommand", type=str, nargs="?", default="", help="subcommand")
    parser.add_argument("-d", "--data", type=str, default="{}", help="Data required for the command as a JSON string")
    parser.add_argument("-p", "--project-dir", type=str, default=None, help="Specify the location of project directory")
    parser.add_argument("-w", "--workspace-dir", type=str, default=None, help="Location of workspace directory")
    parser.add_argument("-a", "--push-artifacts", action="store_true", help="Push artifacts to remote at the end of the run")
    parser.add_argument("-t", "--allow-advanced-tier", action="store_true", help="Allow AWS SSM Parameter Store Advanced tier")

    args = parser.parse_args()

    data_json = args.data
    try:
        data = json.loads(data_json)
    except json.JSONDecodeError as e:
        data = json.loads(data_json[0:-1])

    do(args.command, args.subcommand, data, args.project_dir, args.workspace_dir, args.push_artifacts,
       **{"allow_advanced_tier": args.allow_advanced_tier})

if __name__ == "__main__":
    main()
