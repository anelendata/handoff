# Quick reference

## Project directory

- The project directory `<project_dir>` needs to have `project.yml` at minimum.
- Supportive files goes to `<project_dir>/files`.
- [Secrets](/secrets.html) goes to `<project_dir>/.secrets/secrets.yml` by default.

## project.yml

Here is a example of project.yml:

```
version: 0.3
description: Fetch foreign exchange rates

installs:
- venv: tap
  command: pip install tap-exchangeratesapi
- venv: target
  command: pip install target-csv

vars: # Run time in-memory variables
- key: base_currency
  value: USD

envs:  # Run time environment variables
- key: GOOGLE_APPLICATION_CREDENTIALS
  value: files/google_client_secret.json

tasks:
- name: fetch_exchange_rates
  description: Fetch exchange rates
  pipeline:
  - command: tap-exchangeratesapi
    args: --config files/tap-config.json
    venv: tap
  - command: python
    args: files/stats_collector.py
    venv: tap
  - command: target-csv
    args: --config files/target-config.json
    venv: target

deploy:
  cloud_provider: aws
  cloud_platform: fargate
  resource_group: handoff-etl
  container_image: tap-exchange-rates-target-csv
  task: exchange-rates

schedule:
  target_id: 1
  cron: "0 0 * * ? *"
  envs: []
```

## Variables and secrets

Handoff now supports templating project.yml and files under
<project_dir>/files directory. Templating is based on
[Jinja2](https://jinja.palletsprojects.com/).

To use it, simply put files with Jinja2 templates syntax in
project.yml or the file under `<project_dir>/files` directory.

Example 1 (project.yml):
```
- command: echo
  args: "Hello {{ username }}"
```

Example 2 (files/some_config.yml):
```
username: {{ username }}
password: {{ password }}
```

You can define not so secretive variables in project.yml:

```
vars:
- key: username
  value: my_name
```

If you pass the variables is from the command line via -v option, it will
overwrite the project.yml:

```
handoff run local -p <project_dir> -v username=my_account password="secret pwd"
```

### Secrets

You can store the secure remote parameter store such as AWS Systems Manager
Parameter Store. To do so, create `.secrets` directory under the project
directory and create `secrets.yml` file there.

```
- key: key1
  value: value1
- key: key2
  # The value can also be loaded from a text file
  file: ./file_key.txt
- key: key3
  value: value3
  # The value is stored as a resource group level secret and can be
  # shared among the projects under the same group.
  level: "resource group"
- key: key4
  file: ../../shared/file_key.txt
  level: "resource group"
  # You can mark to skip pushing to remote. Useful for resource level keys
  push: False
```

When level is "resource group", the value is stored as a resource group level
secret and can be shared among the projects under the same group.

When you run `handoff run local -p <project_dir> -w <workspace_dir> -s <stage>`,
the secrets are loaded from the local file. You can store different secrets
between stages.

To push the secrets to the remote parameter store, do:

```
handoff secrets push -p <project_dir> (-v secrets_dir=<directory>)
```

If you specify `<directory>`, handoff looks for secrets.yml in the directory.

After pushing to remote, you can run

```
handoff run -p <project_dir> -w <workspace_dir> -s <stage>
```

so it reads from the remote parameter store.

### Reserved variables

handoff reserve the variable names starting with "_" as the system variables.

List of reserved variables:

- `{{ _stage }}`: Stage (see the next section)
- `{{ _stage_ }}`: `{{ _stage }}` + "_"
- `{{ _stage- }}`: `{{ _stage }}` + "-"

### Switching stages (prod, dev, ...)

These corresponds to stage, given as the commmand line option
(--stage <stage>, -s <stage>). The default value is "dev".

For example, when stage is "dev",

- `{{ _stage }}` translates to "dev"
- `{{ _stage_ }}` translates to "dev_"
- `{{ _stage- }}` translates to "dev-"

When stage is "prod", all three variables above becomes "" (blank).

This is useful when you are writing out in a database and use prefix "dev_"
during the developer test.

## Essential commands

Here is the essential commands in order of the workflow from the local testing
to Fargate deployment:

```
    # Run locally with the local configs
    handoff workspace install -p <project_dir> -w <workspace_dir>
    handoff run local -p <project_dir> -w <workspace_dir>

    # Pushing the project to remote storage
    export AWS_PROFILE=<profile_name>  # Needs to ~/.aws/credentials defined
    handoff cloud bucket create -p <project_dir>
    handoff project push -p <project_dir> -s <stage>

    # Or you can push config/files/secrets separately
    handoff config push -p <project_dir> -s <stage>
    handoff files push -p <project_dir> -s <stage>
    handoff secrets push -p <project_dir> -s <stage>

    # Run locally with the remotely stored configs
    handoff run -p <project_dir> -s <stage>

    # Build and run Docker container. No stage option for building and pushing image
    handoff container build -p <project_dir>
    handoff container run -p <project_dir> -s <stage>
    handoff container push -p <project_dir>  # Push to remote repo

    # Push the task and run on cloud
    handoff cloud resources create -p <project_dir> -s <stage>
    handoff cloud task create -p <project_dir> -s <stage>

    # Run the task
    handoff cloud run -p <project_dir> -s <stage>
    # Schedule a task on cloud (See project.yml for schedule definition)
    handoff cloud schedule -p <project_dir> -s <stage>
```

### Commands for clean up

Here are the commands to take down:

```
    handoff cloud schedule delete -v target_id=<target_id> -s <stage>
    handoff cloud task delete -p <project_dir>  -s <stage>
    handoff cloud resource delete -p <project_dir>  -s <stage>
    handoff config delete -p <project_dir>  -s <stage>
    handoff files delete -p <project_dir>  -s <stage>
    handoff secrets delete -p <project_dir>  -s <stage>
    handoff cloud bucket delete -p <project_dir>  -s <stage>
```

And here are AWS commands to remove the additional resources:
(requires aws cli)

```
    aws s3 rm --recursive s3://<aws-account-id>-<resource-name>/<task-name>/
    aws s3 rb s3://<bucket_name>/<task-name>/
    aws ecr delete-repository --repository-name <docker-image-name>
```

### Role management

Here are the commands to create and delete a role (e.g. AWS Role):

```
    handoff cloud role create -p <project_dir> 
    handoff cloud role delete -p <project_dir>
```

### Command line help

handoff shows help document at the root level or subcommand-level:

```
    handoff --help
    handoff <command> --help  # Admin or Run command such as 'run local'
    handoff cloud [<command>] --help
    handoff container [<command>] --help
    handoff <plugin_name> [<command>] --help
```
