# handoff.cloud

Construct and deploy a configurable unix pipeline process serverlessly*.

What is it?

This is a template repository to build handoff.cloud process:
A framework for executing tasks unix-pipeline process serverlessly.

handoff is originally designed to deploy a single-line ETL process like
[singer.io](https://singer.io) on AWS Fargate, and it was redesigned to
run any commands and program.

In handoff.cloud framework, the configurations are stored and retrieved
from a secure parameter store such as AWS Systems Manager Parameter Store.
This avoids storing sensitive information or configurations that changes
frequently on the Docker image.

Supporting files for commands can also be fetched from a cloud storage such
as AWS S3. The artifacts, the files produced by each command can also
be stored in the cloud storage.

This repository also contains AWS Cloudformation templates and deployment
scripts to support the workflow from local development to the production
deployment.

Clone this repository and follow the easy steps to learn how to use
handoff.cloud in the next few sections.

## Install

Prerequisites:

- Python 3.6 or later
- [AWS CLI](https://docs.aws.amazon.com/cli/index.html)
- [Docker](https://docs.docker.com)

Initialize the submodules:
```
git submodule init
git submodule update
```

Create Python virtual environment and install the modules.
From the root directory of this repository, do:

```
./bin/mkvenvs
```

## A Super Quick Example

There is a `project.yml` file in `.local` directory at the root of this
repository. The project file defines the commands to be executed as a pipeline,
for example:
```
commands:
  - command: cat
    args: "./requirements.txt"
  - command: wc
    args: "-l"
```

This project file defines a shell-script equivalent of
`cat ./requirements.txt | wc -l`.

Try runing:
```
mkdir -p .env
./bin/mkparams > .env/params.json
./bin/runlocal .env/params.json
```

You get console outputs like this:
```
INFO - 2020-07-10 17:49:48,712 - impl.runner: Running run data:{}
INFO - 2020-07-10 17:49:48,712 - impl.runner: Running run
INFO - 2020-07-10 17:49:48,713 - impl.runner: Reading parameters from file: ./params.json
INFO - 2020-07-10 17:49:48,713 - impl.runner: Job started at 2020-07-10 17:49:48.713528
INFO - 2020-07-10 17:49:48,718 - impl.runner: Job ended at 2020-07-10 17:49:48.718836
INFO - 2020-07-10 17:49:48,719 - impl.runner: Processed in 0:00:00.005308
```

It creates `.artifacts/state` whose content is the equivalent to:

```
cat ./requirements.txt | wc -l
```

## Running a Python Program in a Virtual Environment

You can specify a virtual environments in case the command is a Python program.
In `project.yml`, you can also define virtual environment for Python program:
```
commands:
  - command: cat
    args: "./requirements.txt"
  - command: "./scripts/python/collector_stats.py"
    venv: "./venv/root"
```

Try runing:
```
./bin/mkparams > ./params.json
./bin/runlocal ./params.json
```

This time, you will get `.artifacts/collector_stats.json` that looks like:

```
{"rows_read": 15}
```

## Running Code with Configuration Files

The configuration files that may contain sensitive information go to
`.local` directory.

Such configuration files include singer.io tap and target's JSON config files,
and Google Cloud Platform key JSON file.

Note: Currently, only JSON files are supported for remote config store.

Example:

1. Install singer.io tap & target in separate virtual environments:
```
source ./venv/proc_01/bin/activate && pip install tap-exchangeratesapi && deactivate
source ./venv/proc_02/bin/activate && pip install target-csv && deactivate
```

2. Create a copy of config file for tap-exchangeratesapi:
```
echo '{ "base": "JPY", "start_date": "'`date --iso-8601`'" }' > .local/tap-config.json
```

Note: The config file of this example does not contain a sensitive information.


3. Update the project file.

.local/project.yml:
```
commands:
  - command: "tap-exchangeratesapi"
    args: "--config ./.env/config/tap-config.json"
    venv: "./venv/proc_01"
  - command: "./impl/collector_stats.py"
    venv: "./venv/root"
  - command: "target-csv"
    venv: "./venv/proc_02"
```

4. Generate parameter file and run:
```
./bin/mkparams > ./params.json
```

You will see the content of `tap-config.json` included in `params.json`:
```
cat params.json
```

Now let's run:
```
./bin/runlocal ./params.json
```

This should produce a file `exchange_rate-{timestamp}.csv` in the current directory.
It also leaves `.artifacts/state` and `.artifacts/collector_stats.json`.

### State file

For each run, `.artifacts/state` is generated. This is a copy of stderr output
from the last command in the pipeline.

```
commands:
  - command: "tap-exchangeratesapi"
    args: "--config ./.env/config/tap-config.json --state ./.artifacts/state"
    venv: "./venv/proc_01"
  - command: "./impl/collector_stats.py"
    venv: "./venv/root"
  - command: "target-csv"
    venv: "./venv/proc_02"
```

state file is a convenient way of passing information from one run to another
especially in serverless environment such as AWS Fargate. More about this later.

### Environment files

The last example also creates a file `.env/config/tap-config.json`
This is extracted from params.json then written out during the run.

The `.env` directory is reserved for a run time file generation. The files
can be fetched from a remote folder. This will be explained later.

## Remotely Storing & Fetching Configurations

The first step to run the process remotely is to store and fetch the
configurations. The parameter file derived from `project.yml` and other files
under `.local` is stoed as a `SecureString` at
[AWS Systems Manager Parameter Store](https://console.aws.amazon.com/systems-manager/parameters)
(SSM).

Other less-sensitive files necessary for each process can be stored at AWS S3
as explained inthe previous section.

### AWS configuration

Create a programmatic access user with an appropriate role with AWS IAM.
The user should have a sufficient permissions to run the process. At minimum,
AmazonSSMReadOnlyAccess. Obtain the access keys and define AWS credentials and 
region as environment variables:

```
export AWS_ACCESS_KEY_ID=<key>
export AWS_SECRET_ACCESS_KEY=<secret>
export AWS_REGION=<region_name>
```

Define `S3_BUCKET_NAME`:

```
export S3_BUCKET_NAME=<s3-bucket-you-can-read-and-write>
```

Define STACK_NAME. This is used as the stack name for cloudformation
later and SSM Parameters explained in the next section:

```
export STACK_NAME=<some-stack-name>
```

### SSM Parameter Store

In SSM, the parameters are stored in <STACK_NAME>__params format with the following
command:

```
source ./venv/root/bin/activate && python main.py put_ssm_parameters -p parameters.json && deactivate
```

If you omit `-p <filename>.json`, it tries to generate the parameters from `.local` file.


You can check the currently stored values by dump command:

```
source ./venv/root/bin/activate && python main.py dump_ssm_parameters && deactivate
```

### S3

When environment variables `S3_BUCKET_NAME` and `STACK_NAME` are defined,
the program tries to download the contens of `.env` directory from
`s3://${S3_BUCKET_NAME}/${STACK_NAME}/.env`.

To demonstrate the copy, do the following:

```
mkdir -p ./files
echo hello > ./files/hello.txt
aws s3 cp --recursive files s3://${S3_BUCKET_NAME}/${STACK_NAME}/.env/files
rm -fr files
```

### Run

```
rm -fr .env/*
```
To test with the remote configuration.

```
source ./venv/root/bin/activate && python main.py run && deactivate
```

After the run, you find the output from the exchange rate tap example from
the previous example. You will also find `.env/files/hello.txt` downloaded
from the S3 bucket.

Instead of the dummy `hello.txt`, you can store any files that are less-sensitive
such as the property file as in singer.io
[tap-salesforce](https://github.com/singer-io/tap-salesforce#run-discovery).

For a local testing, manually copy files under `.env` and refer it from `project.yml`.

Example:
```
commands:
  - command: "tap-salesforce"
  - venv: ./venv/proc_01
  - args: "--config .env/config/tap-config.json --properties .env/files/properties.json"
  ...
```

Note: You can create subdirectories under `.env`.

`default` is a function defined in `impl.py`. Any function defined in `impl.py` can be invoked

in the same manner.

### Other useful commands

```
source ./venv/root/bin/activate && python main.py show_commands && deactivate
```

This shows the commands in the pipeline.

## Execute in a Docker container

### Fargate deployment via fgops

The repository refers to [fgops](https://github.com/anelendata/fgops) as a submodule
at `deploy/fargate`.
fgops are a set of Docker and CloudFormation commands to build and push the docker images to
ECR, create the ECS task definition, and schedule the events to be executed via Fargate.

fgops requires an environment file. See [fg_env_example](./deploy/fargate/fg_env_example) as an example.
This file will be referred as <fg_env_file> from here.

fgops are symlinked from `./bin` for convenience.

### Build the image

```
./bin/docker_task build <fg_env_file> 0.1
```

Note: "0.1" here is the image version name. You decide what to put there.

```
docker run --env-file <env_var_file> <IMAGE_NAME>
```

Like the way you defined when running locally, you need to define:
```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
STACK_NAME
S3_BUCKET
```

in <env_var_file> file to pass on to Docker contianer.

By default, Dockerfile is configured to execute `python main.py default`.

Or you can specify the function to run together with the data via additional
environment variables in <env_var_file>:

```
COMMAND=show_commands
DATA={"start_at":"1990-01-01T00:00:00","end_at":"2030-01-01T00:00:00"}
```

...that would be picked up by Docker just as

```
CMD python3 main.py ${COMMAND:-default} -d ${DATA:-{}}
```

See [Dockerfile](./Dockerfile) for details.

## Creating VPN and S3 bucket

If you have not done so, created a shared VPN and S3 bucket.
This command creates VPN (named from `PARENT_STACK_NAME`) and S3 bucket
(named from `S3_BUCKET`) shared across multiple stacks:

```
./bin/cf_create_vpn <fg_env_file>
```

## Pushing the image and create the ECS task

Note: Please see fgops instructions for the details.

Push the image to the ECR:

```
./bin/docker_task <fg_env_file> push 0.1 
```

Create the cluster and the task via Cloudformation:

```
./bin/cf_create_stack <fg_env_file> 0.1
```

Check the creation on [Cloudformation](https://console.aws.amazon.com/cloudformation/home)

## Additional permissions

Farget TaskRole will be created under the name: <STACK_NAME>-TaskRole-XXXXXXXXXXXXX
Additional AWS Policy may be attached to the TaskRole depends on the ECS Task.

## Run a one-off task

```
./bin/ecs_run_task <fg_env_file> [<remote_env_var_file>]
```

You can pass extra environmental variables via <remote_env_var_file>.
You need to and SHOULD NOT include AWS keys and secrets in <remote_env_var_file>.

## Scheduling via Fargate

```
./bin/events_schedule_create <fg_env_file> <target_id> '0 0 * * ? *'
```

The above cron example runs the task at midnight daily.

Check the execution at AWS Console:

https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters

...and Cloudwatch logs:

https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logs:

## How to update the stack

1. Make code change and test locally.
2. Build docker image with ./bin/docker_task build
3. Test docker execution locally.
4. Push docker image with ./bin/docker_task push
5. Update stack:

```
./bin/cf_update_stack <fg_env_file> 0.1
```

6. Unschedule the Fargate task:

```
./bin/events_schedule_remove <fg_env_file> <target_id>
```

7. Reschedule the task:

```
./bin/events_schedule_create <fg_env_file> <target_id> '0 0 * * ? *'
```

Copyright 2020- Anelen Co., LLC
