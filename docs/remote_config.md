# Remote configurations and files

The first step to run the process remotely is to store and fetch the
configurations. The parameter file derived from `project.yml` and other files
under `.local` is stoed as a `SecureString` at
[AWS Systems Manager Parameter Store](https://console.aws.amazon.com/systems-manager/parameters)
(SSM).

Other less-sensitive files necessary for each process can be stored at AWS S3
as explained inthe previous section.

## AWS configuration

### AWS keys

If you are not an admin user of your AWS account, make sure you have sufficient
permission to read/write Parameter Store and S3 and deploy a Fargate task.
[Here](https://github.com/anelendata/fgops/blob/master/policy/fargate_deploy.yml)
is an example of
[AWS Policy](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html).

Obtain your access keys and define AWS credentials and region as environment variables:
```
export AWS_ACCESS_KEY_ID=<key>
export AWS_SECRET_ACCESS_KEY=<secret>
export AWS_REGION=<region_name>
```

### Alternative method: Role assumption

Alternatively, if you have a AWS profile entry that assumes an
[AWS Role](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html)
, for example:
```
[<your-profile-name-1>]
source_profile = <your-profile-name-2-with-aws-keys>
role_arn = arn:aws:iam::<aws-account-number>:role/<role-name>
external_id=<your-external-id>  # You may/maynot need this
region = us-east-1
```
in `.aws/credentials`. The repository contains convenience shell scripts
at `bin`. You can assume role and export the temporary keys
(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_SESSION_TOKEN)
with the following command:
```
./bin/iam_assume_role <fg_env>
```

Here, `<fg_env>` is a file that contians:
```
export AWS_PROFILE=<your-profile-name-1>
```
(More about `fg_env` file in [the next section](./docker.md).)

### Other environment variables

Define `S3_BUCKET_NAME`:

```
export S3_BUCKET_NAME=<s3-bucket-you-can-read-and-write>
```

Define STACK_NAME. This is used as the stack name for cloudformation
later and SSM Parameters explained in the next section:

```
export STACK_NAME=<some-stack-name>
```

## SSM Parameter Store

We store project configurations at Parameter Store as  <STACK_NAME>_config.

```
handoff push_config -p test_projects/03_exchange_rates
```

You can check the currently stored values by print command:

```
handoff print_config -p test_projects/03_exchange_rates
```

It should return a string like this:
```
{"commands": [{"command": "tap-exchangeratesapi", "args": "--config config/tap-config.json", "venv": "proc_01", "installs": ["pip install tap-exchangeratesapi"]}, {"command": "files/stats_collector.py", "venv": "proc_01"}, {"command": "target-csv", "venv": "proc_02", "installs": ["pip install target-csv"]}], "files": [{"name": "tap-config.json", "value": "{ \"base\": \"JPY\", \"start_date\": \"2020-07-09\" }\n"}]}
```

The string is "compiled" from profile.yml and the JSON configuration files under
`<profile_dir>/config` directory.

Note: The maximum size of a value in Parameter Store is 4KB with Standard
tier. You can bump it up to 8KB with Advanced tier with `--allow-advanced-tier` option:

```
handoff print_config -p test_projects/03_exchange_rates --allow-advanced-tier
```

## S3

In the project directory may contain `files` subdirectory and store the
files needed at run-time. The files should be first pushed to the remote
store (AWS S3) by running:

```
handoff push_files -p test_projects/03_exchange_rates
```

The files are uploaded to:
`s3://${S3_BUCKET_NAME}/${STACK_NAME}/files`

You see handoff fetching the files into `workspace/files` by runnig:
```
handoff get_files -p test_projects/03_exchange_rates
```

You do not need to run the above command explicitly as handoff automatically
downlods them into the workspace as described in the next section.

## Run

Let's clean up the local workspace before running with the remotely stored
configs:
```
rm -fr test_workspaces/03_exchange_rates/*
```

First we need to create the virtual environments and install the commands:
```
handoff install -w test_workspaces/03_exchange_rates
```

Then run:
```
handoff run -w test_workspaces/03_exchange_rates -a
```

Notice that we dropped `-p` option in the last two commands. The project
configurations are fetched from remote this time.

After the run, you find the output from the exchange rate tap example from
the previous example.

In the aboe run command, we added `-a` option. This is short for `--push-artifacts`.
With this option, the files under `<workspace_dir>/artifacts` will be push to
the remote storage after the run. You can download the artifacts from the
remote storage by runing:
```
handoff get_artifacts -w <workspace_dir>
```

You can also push the contents of `<workspace_dir>/artifacts` manually:
```
handoff push_artifacts -w <workspace_dir>
```

### Other useful commands

`default` is a function defined in `impl.py`. Any function defined in `impl.py` can be invoked

in the same manner.

```
source ./venv/root/bin/activate && python code show_commands && deactivate
```

This shows the commands in the pipeline.

Next: [Execute Docker image](docker)
