# Quick reference

## Project directory

- The project directory `<project_dir>` needs to have `project.yml` at minimum.
- Supportive files goes to `<project_dir>/files`.
- [Secrets](/secrets.html) goes to `<project_dir>/.secrets/secrets.yml` by default.

## project.yml

Here is a example of project.yml:

```
# commands are required
commands:
  - command: "tap-exchangeratesapi"
    args: "--config files/tap-config.json"
    # List of commands in sequence for non-superuser installing
    installs:
      - "pip install tap-exchangeratesapi"
    # venv is required for Python program only
    venv: "proc_01"
  - command: "python files/stats_collector.py"
    venv: "proc_01"
    active: False  # This makes stats_collector.py process inactive.
  - command: "target-csv"
    args: "--config files/target-config.json"
    venv: "proc_02"
    installs:
      - "pip install target-csv"
  - command: cat
    args: "> artifacts/saving_output_from_the_last_process.txt"

# deploy is required for using `handoff run`, config/files/secrets push/delete,
#   container, cloud
deploy:
  # For now, aws/fargate is the only supported provider/platform
  cloud_provider: "aws"
  cloud_platform: "fargate"
  resource_group: "handoff-test"
  container_image: "singer_exchange_rates_to_csv"
  task: "exchange-rates"
```

Here is the essential commands in order of the workflow from the local testing
to Fargate deployment:

```
    # Run locally with the local configs
    handoff workspace install -p <project_dir> -w <workspace_dir>
    handoff run local -p <project_dir> -w <workspace_dir>

    # Pushing the project to remote storage
    export AWS_PROFILE=<profile_name>  # Needs to ~/.aws/credentials defined
    handoff cloud bucket create -p <project_dir>
    handoff config push -p <project_dir>
    handoff cloud bucket create -p <project_dir>
    handoff files push -p <project_dir>
    handoff secrets push -p <project_dir>

    # Run locally with the remotely stored configs
    handoff run -p <project_dir>

    # Build and run Docker container
    handoff container build -p <project_dir>
    handoff container run -p <project_dir>

    # Push the task and run on cloud
    handoff container push -p <project_dir>
    handoff cloud resources create -p <project_dir>
    handoff cloud task create -p <project_dir>
    handoff cloud run -p <project_dir>

    # Schedule a task on cloud
    handoff cloud schedule -d target_id=<some_id> cront="15 0 * * ? *" -p <project_dir>
```

Here are the commands to take down:

```
    handoff cloud unschedule -d target_id=<some_id> -p <project_dir>
    handoff cloud task delete -p <project_dir>
    handoff cloud resources delete -p <project_dir>
    handoff cloud secrets delete -p <project_dir>
    handoff cloud files delete -p <project_dir>
    handoff cloud config delete -p <project_dir>
    handoff cloud bucket delete -p <project_dir>
```

And here are AWS commands to remove the additional resources:
(requires aws cli)

```
    aws s3 rm --recursive s3://<aws-account-id>-<resource-name>/<task-name>/
    aws s3 rb s3://<bucket_name>/<task-name>/
    aws ecr delete-repository --repository-name <docker-image-name>
```

Here are the commands to create and delete a role (e.g. AWS Role):

```
    handoff cloud role create -p <project_dir> 
    handoff cloud role delete -p <project_dir>
```

handoff shows help document at the root level or subcommand-level:

```
    handoff --help
    handoff <command> --help  # Admin or Run command such as 'run local'
    handoff cloud [<command>] --help
    handoff container [<command>] --help
    handoff <plugin_name> [<command>] --help
```
