## Running task locally with remotely stored configurations

We will continue using 03_exchange_rates example. But this time, we will
store the configurations to the remote data store.



Let's review how 03_exchange_rates project directory is structured:

```shell
> ls -l 03_exchange_rates
```
```shell

 files
 project.yml
 workspace
```


In files directory, we have a couple of configuration files:

```shell
> ls -l 03_exchange_rates/files
```
```shell

 stats_collector.py
 tap-config.json
 target-config.json
```


...which look like:

```shell
> cat 03_exchange_rates/files/tap-config.json
```

```shell
{ "base": "JPY", "start_date": "2020-09-01" }
```
```shell
> cat 03_exchange_rates/files/target-config.json
```

```shell
{
    "delimiter": ",",
    "quotechar": "'",
    "destination_path": "artifacts"
}
```

Such configuration files often contain sensitive information.
So we push the configrations to a secure key store such as
AWS Systems Manager (SSM) Parameter Store (In SecuresString format)
handoff wraps this proces by a single command. handoff packs all the JSON
format files under the configuration directory and send it to the remote
key-value storage.

Try running:

```shell
> handoff config push -p 03_exchange_rates
```
```shell

[2020-11-09 01:46:29,520] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:144)
[2020-11-09 01:46:29,650] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 01:46:29,937] [    INFO] - You have the access to AWS resources. - (__init__.py:69)
[2020-11-09 01:46:29,938] [    INFO] - Platform: aws - (admin.py:164)
[2020-11-09 01:46:29,938] [    INFO] - Setting environment variables from config. - (admin.py:92)
[2020-11-09 01:46:30,004] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxt - (admin.py:115)
[2020-11-09 01:46:30,004] [    INFO] - Compiling config from 03_exchange_rates - (admin.py:621)
[2020-11-09 01:46:30,004] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:144)
[2020-11-09 01:46:30,007] [    INFO] - Platform: aws - (admin.py:164)
[2020-11-09 01:46:30,008] [    INFO] - Setting environment variables from config. - (admin.py:92)
.
.
.
[2020-11-09 01:46:30,008] [    INFO] - Putting parameter /dev-handoff-test/dev-test-exchange-rates/config to AWS SSM Parameter Store with Standard tier - (__init__.py:210)
[2020-11-09 01:46:30,024] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 01:46:30,395] [    INFO] - See the parameters at https://console.aws.amazon.com/systems-manager/parameters/?region=us-east-1&tab=Table#list_parameter_filters=Name:Contains:/dev-handoff-test/dev-test-exchange-rates/config - (__init__.py:216)
```

Look at the end of the log that says,

```shell
    See the parameters at https://console.aws.amazon.com/systems-manager/parameters/?region=...
```

Grab the link and open in the browswer (AWS login required) to confirm that
the parameters are uploaded.

Note that handoff will create all remote sources with *dev* prefix.
To change the prefix, run handoff commands with `-s some_prefix`. To remove
prefix, use `-s prod`.



We also have some files needed for the task execution:

```shell
> ls -l 03_exchange_rates/files
```
```shell

 stats_collector.py
 tap-config.json
 target-config.json
```

We need to store this somewhere accessible.
So we will create a cloud data storage (S3 bucket) for that.

Try running:

```shell
> handoff cloud bucket create -p 03_exchange_rates
```
```shell

[2020-11-09 01:46:30,882] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:144)
[2020-11-09 01:46:31,008] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 01:46:31,285] [    INFO] - You have the access to AWS resources. - (__init__.py:69)
[2020-11-09 01:46:31,285] [    INFO] - Platform: aws - (admin.py:164)
[2020-11-09 01:46:31,285] [    INFO] - Setting environment variables from config. - (admin.py:92)
[2020-11-09 01:46:31,350] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxt - (admin.py:115)
[2020-11-09 01:46:31,834] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 01:46:32,284] [    INFO] - {'StackId': 'arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/dev-handoff-test-bucket/xxxxxxxx2a854211', 'ResponseMetadata': {'RequestId': 'xxxxxxxxbed71c5e', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'xxxxxxxxbed71c5e', 'content-type': 'text/xml', 'content-length': '393', 'date': 'Mon, 09 Nov 2020 01:46:31 GMT'}, 'RetryAttempts': 0}} - (__init__.py:385)
[2020-11-09 01:46:32,284] [    INFO] - Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?viewNested=true&hideStacks=false&stackId=arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/dev-handoff-test-bucket/xxxxxxxx2a854211 - (__init__.py:34)
```

Wait for a minute and check here

```shell
    https://s3.console.aws.amazon.com
```

to make sure the bucket is created before you proceed.



Now it's time to push the files to the bucket.

Try running:

```shell
> handoff files push -p 03_exchange_rates
```
```shell

[2020-11-09 01:49:32,759] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:144)
[2020-11-09 01:49:32,879] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 01:49:33,163] [    INFO] - You have the access to AWS resources. - (__init__.py:69)
[2020-11-09 01:49:33,163] [    INFO] - Platform: aws - (admin.py:164)
[2020-11-09 01:49:33,163] [    INFO] - Setting environment variables from config. - (admin.py:92)
[2020-11-09 01:49:33,228] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxt - (admin.py:115)
[2020-11-09 01:49:33,242] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 01:49:33,297] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 01:49:33,592] [    INFO] - Uploading 03_exchange_rates/files to bucket xxxxxxxxt - (s3.py:122)
[2020-11-09 01:49:33,592] [    INFO] - Files to be uploaded: ['03_exchange_rates/files/target-config.json', '03_exchange_rates/files/tap-config.json', '03_exchange_rates/files/stats_collector.py'] - (s3.py:135)
.
.
.
[2020-11-09 01:49:33,592] [    INFO] - Uploading 03_exchange_rates/files/target-config.json to Amazon S3 bucket xxxxxxxxt/dev-test-exchange-rates/last/files/target-config.json - (s3.py:141)
[2020-11-09 01:49:33,952] [    INFO] - Uploading 03_exchange_rates/files/tap-config.json to Amazon S3 bucket xxxxxxxxt/dev-test-exchange-rates/last/files/tap-config.json - (s3.py:141)
[2020-11-09 01:49:34,099] [    INFO] - Uploading 03_exchange_rates/files/stats_collector.py to Amazon S3 bucket xxxxxxxxt/dev-test-exchange-rates/last/files/stats_collector.py - (s3.py:141)
[2020-11-09 01:49:34,255] [    INFO] - See the files at https://s3.console.aws.amazon.com/s3/buckets/xxxxxxxxt/dev-test-exchange-rates/last/files/ - (__init__.py:253)
```

Look at the end of the log that says,

```shell
    See the files at https://s3.console.aws.amazon.com/s3/...
```

Grab the link and open in the browswer (AWS login required) to see the files
directory is uploaded.



Install the workspace:

```shell
> handoff workspace install -p 03_exchange_rates -w workspace
```
```shell

[2020-11-09 01:49:34,744] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:144)
[2020-11-09 01:49:34,870] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 01:49:35,150] [    INFO] - You have the access to AWS resources. - (__init__.py:69)
[2020-11-09 01:49:35,150] [    INFO] - Platform: aws - (admin.py:164)
[2020-11-09 01:49:35,150] [    INFO] - Setting environment variables from config. - (admin.py:92)
[2020-11-09 01:49:35,215] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxt - (admin.py:115)
[2020-11-09 01:49:35,215] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:144)
[2020-11-09 01:49:35,218] [    INFO] - Platform: aws - (admin.py:164)
[2020-11-09 01:49:38,851] [    INFO] - Running /bin/bash -c "source proc_01/bin/activate && pip install wheel" - (admin.py:30)
Requirement already satisfied: wheel in ./proc_01/lib/python3.6/site-packages (0.35.1)
.
.
.
Collecting pytzdata
  Using cached pytzdata-2020.1-py2.py3-none-any.whl (489 kB)
Collecting python-dateutil
  Using cached python_dateutil-2.8.1-py2.py3-none-any.whl (227 kB)
Collecting pytz
  Using cached pytz-2020.4-py2.py3-none-any.whl (509 kB)
Collecting six>=1.5
  Using cached six-1.15.0-py2.py3-none-any.whl (10 kB)
Installing collected packages: simplejson, pytz, tzlocal, pytzdata, six, python-dateutil, pendulum, singer-python, jsonschema, target-csv
Successfully installed jsonschema-2.6.0 pendulum-1.2.0 python-dateutil-2.8.1 pytz-2020.4 pytzdata-2020.1 simplejson-3.11.1 singer-python-2.1.4 six-1.15.0 target-csv-0.3.0 tzlocal-2.1
```

Now let's run the command by pulling the configurations and files from remote. 

Try running:

```shell
> handoff run -w workspace --envs resource_group=handoff-test task=test-exchange-rates --push-artifacts
```
```shell

[2020-11-09 01:49:47,715] [    INFO] - Reading configurations from remote parameter store. - (admin.py:553)
[2020-11-09 01:49:47,715] [    INFO] - Reading precompiled config from remote. - (admin.py:127)
[2020-11-09 01:49:47,835] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 01:49:48,115] [    INFO] - You have the access to AWS resources. - (__init__.py:69)
[2020-11-09 01:49:48,130] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 01:49:48,480] [    INFO] - Fetching the secrets from the remote parameter store. - (admin.py:180)
[2020-11-09 01:49:48,664] [    INFO] - Setting environment variables from config. - (admin.py:92)
[2020-11-09 01:49:48,729] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxt - (admin.py:115)
[2020-11-09 01:49:48,730] [    INFO] - Downloading config files from the remote storage xxxxxxxxt - (admin.py:470)
[2020-11-09 01:49:48,744] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
.
.
.
[2020-11-09 01:49:52,971] [    INFO] - Uploading workspace/artifacts/collect_stats.json to Amazon S3 bucket xxxxxxxxt/dev-test-exchange-rates/last/artifacts/collect_stats.json - (s3.py:141)
[2020-11-09 01:49:53,193] [    INFO] - See the files at https://s3.console.aws.amazon.com/s3/buckets/xxxxxxxxt/dev-test-exchange-rates/last/artifacts/ - (__init__.py:253)
[2020-11-09 01:49:53,194] [    INFO] - Copying the remote artifacts from last to runs xxxxxxxxt - (admin.py:368)
[2020-11-09 01:49:53,194] [    INFO] - Copying recursively from s3://xxxxxxxxt/dev-test-exchange-rates/last/* to s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T01:49:53.194335/* - (s3.py:17)
[2020-11-09 01:49:53,466] [    INFO] - Copied s3://xxxxxxxxt/dev-test-exchange-rates/last/artifacts/collect_stats.json to s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T01:49:53.194335/artifacts/collect_stats.json - (s3.py:53)
[2020-11-09 01:49:53,646] [    INFO] - Copied s3://xxxxxxxxt/dev-test-exchange-rates/last/artifacts/exchange_rate-20201109T014950.csv to s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T01:49:53.194335/artifacts/exchange_rate-20201109T014950.csv - (s3.py:53)
[2020-11-09 01:49:53,855] [    INFO] - Copied s3://xxxxxxxxt/dev-test-exchange-rates/last/artifacts/stdout.log to s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T01:49:53.194335/artifacts/stdout.log - (s3.py:53)
[2020-11-09 01:49:54,086] [    INFO] - Copied s3://xxxxxxxxt/dev-test-exchange-rates/last/files/stats_collector.py to s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T01:49:53.194335/files/stats_collector.py - (s3.py:53)
[2020-11-09 01:49:54,259] [    INFO] - Copied s3://xxxxxxxxt/dev-test-exchange-rates/last/files/tap-config.json to s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T01:49:53.194335/files/tap-config.json - (s3.py:53)
[2020-11-09 01:49:54,439] [    INFO] - Copied s3://xxxxxxxxt/dev-test-exchange-rates/last/files/target-config.json to s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T01:49:53.194335/files/target-config.json - (s3.py:53)
```

This time, we are not using the local project definition.
We are pulling the project configurations from the remote parameter store identified
by the resource group and task names.

Also notice that we used --push-artifacts option in the last command.
With this option, we pushed the result to the bucket under


```shell

    s3://..../dev-test-exchange-rates/last/artifacts

```

directory.


Also note that artifacts are automatically archived at each run at

```shell

    s3://..../dev-test-exchange-rates/runs/


```

directory.



Recall 03_exchange_rates/project.yml looks like:

```shell
> cat 03_exchange_rates/project.yml
```

```shell
commands:
  - command: "tap-exchangeratesapi"
    args: "--config files/tap-config.json"
    venv: "proc_01"
    installs:
      - "pip install tap-exchangeratesapi"
  - command: "python files/stats_collector.py"
    venv: "proc_01"
  - command: "target-csv"
    args: "--config files/target-config.json"
    venv: "proc_02"
    installs:
      - "pip install target-csv"
deploy:
  cloud_provider: "aws"
  cloud_platform: "fargate"
  resource_group: "handoff-test"
  container_image: "singer_exchange_rates_to_csv"
  task: "test-exchange-rates"
```

The deploy section specifies:

- cloud_provider: Currently only AWS is supported.
- cloud_platform: The serverless platfor on which the task will run.
- resource_group: The resource group name, which is used for creating
remote storage (e.g. AWS S3) names and the remote parameter store's
namespace. The resource can be shared with multiple tasks.
- container_image: The container image name given to the current project.
- task: Task name. Note that multiple tasks with varying configurations can
be generated from a container image (Docker)



Next step is to prepare a Docker image and test running it locally.

