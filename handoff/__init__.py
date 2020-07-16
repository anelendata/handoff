import argparse, datetime, json, logging, os
from .impl import admin, runner


PROJECT_DIR = "project"
PROJECT_FILE = "project.yml"
DEFAULT_WORKSPACE_DIR = "workspace"
ARTIFACTS_DIR = "artifacts"

LOGGER = logging.getLogger(__name__)


def _list_commands(module):
    commands = dict()
    objects = dir(module)
    for name in objects:
        if name[0] == "_":
            continue
        obj = getattr(module, name)
        if callable(obj):
            commands[name] = obj
    return commands


def do(command,
       data,
       project_dir,
       workspace_dir,
       push_artifacts=True):
    """
    """
    # Try running admin commands
    admin_commands = _list_commands(admin)

    if (command in admin_commands.keys()
            and (not project_dir or not os.path.isdir(project_dir))):
        raise Exception("Please give a project directory")

        if not project_dir or not os.path.isfile(os.path.join(project_dir, PROJECT_FILE)):
            raise Exception("Cannot find the project file at %s" % project_dir)

    if not workspace_dir:
        raise Exception("Please set a workspace directory")

    # if command != "init_workspace" and not os.path.isdir(workspace_dir):
    #     raise Exception("Workspace directory does not exist at %s" % workspace_dir)

    if command in admin_commands:
        # Run the admin command
        admin.init_workspace(project_dir, workspace_dir, data)
        admin_commands[command](project_dir, workspace_dir, data)
        return

    commands = _list_commands(runner)
    if command not in commands:
        print("Invalid command: %s\nAvailable commands are %s" %
              (command,
               ", ".join([x for x in list(admin_commands.keys()) + list(commands.keys())])))
        return

    admin.init_workspace(project_dir, workspace_dir, data)
    config = admin.get_config(project_dir, workspace_dir, data)
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
    if push_artifacts:
        if not os.environ.get("S3_BUCKET_NAME"):
            raise Exception("Cannot push artifacts. S3_BUCKET_NAME is not set")
        admin.push_artifacts(project_dir, workspace_dir, data)


def main():
    parser = argparse.ArgumentParser(description="Run parameterized Unix pipeline command")
    parser.add_argument("command", type=str, help="command")
    parser.add_argument("-d", "--data", type=str, default="{}", help="Data required for the command as a JSON string")
    parser.add_argument("-p", "--project-dir", type=str, default=None, help="Specify the location of project directory")
    parser.add_argument("-w", "--workspace-dir", type=str, default=DEFAULT_WORKSPACE_DIR, help="Location of workspace directory")
    parser.add_argument("-a", "--push-artifacts", action="store_true", help="Push artifacts to remote at the end of the run")

    args = parser.parse_args()
    command = args.command

    data_json = args.data
    try:
        data = json.loads(data_json)
    except json.JSONDecodeError as e:
        data = json.loads(data_json[0:-1])

    do(command, data, args.project_dir, args.workspace_dir, args.push_artifacts)

if __name__ == "__main__":
    main()
