# Remote configurations and files

The first step to run the process remotely is to store and fetch the
configurations. The parameter file derived from `project.yml` and other files
under `.local` is stoed as a `SecureString` at
[AWS Systems Manager Parameter Store](https://console.aws.amazon.com/systems-manager/parameters)
(SSM).

Other less-sensitive files necessary for each process can be stored at AWS S3
as explained inthe previous section.

## AWS configuration

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

## SSM Parameter Store

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

## S3

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

## Run

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

### Other useful commands

`default` is a function defined in `impl.py`. Any function defined in `impl.py` can be invoked

in the same manner.

```
source ./venv/root/bin/activate && python main.py show_commands && deactivate
```

This shows the commands in the pipeline.

Next: [Execute Docker image](docker)
