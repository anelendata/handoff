import argparse, datetime, json, logging, os
from .impl import admin, runner
from .config import ARTIFACTS_DIR, PROJECT_FILE


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
       push_artifacts=True,
       **kwargs):
    """
    """
    # Try running admin commands
    admin_commands = _list_commands(admin)

    if False and (command in admin_commands.keys()
                  and (not project_dir or not os.path.isdir(project_dir))):
        raise Exception("Please give a project directory")

        if not project_dir or not os.path.isfile(os.path.join(project_dir, PROJECT_FILE)):
            raise Exception("Cannot find the project file at %s" % project_dir)

    if False and not workspace_dir:
        raise Exception("Please set a workspace directory")

    # if command != "init_workspace" and not os.path.isdir(workspace_dir):
    #     raise Exception("Workspace directory does not exist at %s" % workspace_dir)

    if command in admin_commands:
        # Run the admin command
        admin.init_workspace(project_dir, workspace_dir, data)
        admin_commands[command](project_dir, workspace_dir, data, **kwargs)
        return

    commands = _list_commands(runner)
    if command not in commands:
        print("Invalid command: %s\nAvailable commands are %s" %
              (command,
               ", ".join([x for x in list(admin_commands.keys()) + list(commands.keys())])))
        return

    admin.init_workspace(project_dir, workspace_dir, data)

    if command == "run_local":
        config = admin.compile_config(project_dir, workspace_dir, data)
        admin.copy_files_from_local_project(project_dir, workspace_dir, data)
    else:
        config = admin.get_config(project_dir, workspace_dir, data)
        admin.get_files(project_dir, workspace_dir, data)
    prev_wd = os.getcwd()
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
        if not os.environ.get("S3_BUCKET_NAME"):
            raise Exception("Cannot push artifacts. S3_BUCKET_NAME is not set")
        admin.push_artifacts(project_dir, workspace_dir, data)


def main():
    parser = argparse.ArgumentParser(description="Run parameterized Unix pipeline command https://dev/handoff.cloud")
    parser.add_argument("command", type=str, help="command " + str(list(_list_commands(admin).keys()) + list(_list_commands(runner).keys())))
    parser.add_argument("-d", "--data", type=str, default="{}", help="Data required for the command as a JSON string")
    parser.add_argument("-p", "--project-dir", type=str, default=None, help="Specify the location of project directory")
    parser.add_argument("-w", "--workspace-dir", type=str, default=None, help="Location of workspace directory")
    parser.add_argument("-a", "--push-artifacts", action="store_true", help="Push artifacts to remote at the end of the run")
    parser.add_argument("-t", "--allow-advanced-tier", action="store_true", help="Allow AWS SSM Parameter Store Advanced tier")

    args = parser.parse_args()
    command = args.command

    data_json = args.data
    try:
        data = json.loads(data_json)
    except json.JSONDecodeError as e:
        data = json.loads(data_json[0:-1])

    do(command, data, args.project_dir, args.workspace_dir, args.push_artifacts,
       **{"allow_advanced_tier": args.allow_advanced_tier})

if __name__ == "__main__":
    main()
