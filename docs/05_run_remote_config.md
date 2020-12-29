## Running task locally with remotely stored configurations

We will use 04_install example again. But this time, we will
store the configurations to the remote data store.



Now let's review how 04_install project directory is structured:

```shell

04_install
├── files
│   ├── stats_collector.py
│   ├── tap-config.json
│   └── target-config.json
└── project.yml

1 directory, 4 files
```


In files directory, we have a couple of configuration files:

Let's store project.yml and the project files to the remote store
(S3 for case of AWS). First we need to create a remote store bucket:

```shell
> handoff cloud bucket create -p 04_install
```
```shell

[2020-12-28 22:02:47,376] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:02:48,324] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?viewNested=true&hideStacks=false&stackId=arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/dev-handoff-etl-bucket/xxxxxxxx85921ccb
ResponseMetadata:
  HTTPHeaders:
    content-length: '392'
    content-type: text/xml
    date: Mon, 28 Dec 2020 22:02:48 GMT
    x-amzn-requestid: xxxxxxxx7b10873a
  HTTPStatusCode: 200
```

Wait for a minute and check here

```shell
    https://s3.console.aws.amazon.com
```

to make sure the bucket is created before you proceed.



Now it's time to push the project files to the bucket.

Try running these two commands:

```shell
> handoff config push -p 04_install
```
```shell

[2020-12-28 22:05:49,409] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:05:49,769] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
success
```

and this:

```shell
> handoff files push -p 04_install
```
```shell

[2020-12-28 22:05:50,740] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:05:51,100] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:05:51,235] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:05:51,527] [    INFO] - Uploading 04_install/files to bucket xxxxxxxx - (s3.py:122)
[2020-12-28 22:05:51,527] [    INFO] - Files to be uploaded: ['04_install/files/target-config.json', '04_install/files/tap-config.json', '04_install/files/stats_collector.py'] - (s3.py:135)
[2020-12-28 22:05:51,527] [    INFO] - Uploading 04_install/files/target-config.json to Amazon S3 bucket xxxxxxxx/dev-exchange-rates-to-csv/files/target-config.json - (s3.py:142)
[2020-12-28 22:05:51,889] [    INFO] - Uploading 04_install/files/tap-config.json to Amazon S3 bucket xxxxxxxx/dev-exchange-rates-to-csv/files/tap-config.json - (s3.py:142)
[2020-12-28 22:05:52,035] [    INFO] - Uploading 04_install/files/stats_collector.py to Amazon S3 bucket xxxxxxxx/dev-exchange-rates-to-csv/files/stats_collector.py - (s3.py:142)
See the files at https://s3.console.aws.amazon.com/s3/buckets/xxxxxxxx/dev-exchange-rates-to-csv/files/
success
```

Look at the end of the log that says,

```shell
    See the files at https://s3.console.aws.amazon.com/s3/...
```

Grab the link and open in the browswer (AWS login required) to see the files
directory is uploaded.



In 03_secrets project, we learned how to use secret variables in the project
files. 04_install also contains .secrets files although the values are not
used at run-time. 

We will use 04_install project to learn how to store secrets to
AWS Systems Manager (SSM) Parameter Store as encrypted (SecuresString) data.

Try running (and enter 'y' to the confirmation):

```shell
> handoff secrets push -p 04_install
```
```shell

[2020-12-28 22:05:52,750] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
Putting the following keys to remote parameter store:
  - username (task level)
  - password (task level)
  - google_client_secret (resource group level)
Proceed? (y/N)[2020-12-28 22:05:53,109] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
See the parameters at https://console.aws.amazon.com/systems-manager/parameters/?region=us-east-1&tab=Table#list_parameter_filters=Name:Contains:/dev-handoff-etl/dev-exchange-rates-to-csv/username
See the parameters at https://console.aws.amazon.com/systems-manager/parameters/?region=us-east-1&tab=Table#list_parameter_filters=Name:Contains:/dev-handoff-etl/dev-exchange-rates-to-csv/password
See the parameters at https://console.aws.amazon.com/systems-manager/parameters/?region=us-east-1&tab=Table#list_parameter_filters=Name:Contains:/dev-handoff-etl/google_client_secret
success
```

Look at the end of the log that says,

```shell
    See the parameters at https://console.aws.amazon.com/systems-manager/parameters/?region=...
```

Grab the link and open in the browswer (AWS login required) to confirm that
the parameters are uploaded.

Note that handoff will create all remote sources with *dev* prefix.
To change the prefix, run handoff commands with --stage (-s) <prefix_name>
like `--stage test`. To remove prefix, use `--stage prod`.



Install the workspace as usual:

```shell
> handoff workspace install -p 04_install -w workspace
```
```shell

[2020-12-28 22:05:54,296] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
Requirement already satisfied: wheel in ./tap/lib/python3.6/site-packages (0.36.2)
Collecting tap-exchangeratesapi
  Using cached tap_exchangeratesapi-0.1.1-cp36-none-any.whl
Collecting backoff==1.3.2
  Using cached backoff-1.3.2-cp36-none-any.whl
Collecting requests==2.21.0
  Using cached requests-2.21.0-py2.py3-none-any.whl (57 kB)
Collecting singer-python==5.3.3
  Using cached singer_python-5.3.3-cp36-none-any.whl
.
.
.
  Using cached six-1.15.0-py2.py3-none-any.whl (10 kB)
Collecting pytzdata
  Using cached pytzdata-2020.1-py2.py3-none-any.whl (489 kB)
Collecting tzlocal
  Using cached tzlocal-2.1-py2.py3-none-any.whl (16 kB)
Collecting pytz
  Using cached pytz-2020.5-py2.py3-none-any.whl (510 kB)
Installing collected packages: six, pytz, tzlocal, pytzdata, python-dateutil, simplejson, pendulum, singer-python, jsonschema, target-csv
Successfully installed jsonschema-2.6.0 pendulum-1.2.0 python-dateutil-2.8.1 pytz-2020.5 pytzdata-2020.1 simplejson-3.11.1 singer-python-2.1.4 six-1.15.0 target-csv-0.3.0 tzlocal-2.1
sucess
```


Now let's run the command by pulling the configurations and files from remote. 

Try running:

```shell
> handoff run -w workspace --envs resource_group=handoff-etl task=exchange-rates-to-csv --push-artifacts -v start_date=$(date -I -d "-7 day")
```
```shell

[2020-12-28 22:06:08,935] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:06:09,305] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:06:09,724] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:06:10,159] [    INFO] - GET s3://xxxxxxxx/dev-exchange-rates-to-csv/files - (s3.py:66)
[2020-12-28 22:06:10,716] [    INFO] - GET s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last - (s3.py:66)
[2020-12-28 22:06:10,790] [ WARNING] - Nothing found in the location - (s3.py:83)
[2020-12-28 22:06:10,790] [    INFO] - Job started at 2020-12-28 22:06:10.790266 - (__init__.py:178)
[2020-12-28 22:06:10,790] [    INFO] - Running pipeline fetch_exchange_rates - (operators.py:193)
[2020-12-28 22:06:10,807] [    INFO] - Checking return code of pid 3410 - (operators.py:262)
[2020-12-28 22:06:11,409] [    INFO] - Checking return code of pid 3411 - (operators.py:262)
.
.
.
[2020-12-28 22:06:11,760] [    INFO] - Uploading workspace/artifacts to bucket xxxxxxxx - (s3.py:122)
[2020-12-28 22:06:11,761] [    INFO] - Files to be uploaded: ['workspace/artifacts/fetch_exchange_rates_stdout.log', 'workspace/artifacts/exchange_rate-20201228T220611.csv', 'workspace/artifacts/collect_stats.json'] - (s3.py:135)
[2020-12-28 22:06:11,761] [    INFO] - Uploading workspace/artifacts/fetch_exchange_rates_stdout.log to Amazon S3 bucket xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last/fetch_exchange_rates_stdout.log - (s3.py:142)
[2020-12-28 22:06:11,917] [    INFO] - Uploading workspace/artifacts/exchange_rate-20201228T220611.csv to Amazon S3 bucket xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last/exchange_rate-20201228T220611.csv - (s3.py:142)
[2020-12-28 22:06:12,074] [    INFO] - Uploading workspace/artifacts/collect_stats.json to Amazon S3 bucket xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last/collect_stats.json - (s3.py:142)
See the files at https://s3.console.aws.amazon.com/s3/buckets/xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last/
[2020-12-28 22:06:12,220] [    INFO] - Copying recursively from s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last/* to s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T22:06:12.220644/* - (s3.py:17)
[2020-12-28 22:06:12,483] [    INFO] - Copied s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last/collect_stats.json to s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T22:06:12.220644/collect_stats.json - (s3.py:53)
[2020-12-28 22:06:12,662] [    INFO] - Copied s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last/exchange_rate-20201228T220611.csv to s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T22:06:12.220644/exchange_rate-20201228T220611.csv - (s3.py:53)
[2020-12-28 22:06:12,855] [    INFO] - Copied s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last/fetch_exchange_rates_stdout.log to s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T22:06:12.220644/fetch_exchange_rates_stdout.log - (s3.py:53)
```

This time, we are not using the local project definition.
We are pulling the project configurations from the remote parameter store identified
by the resource group and task names.

Also notice that we used --push-artifacts option in the last command.
With this option, we pushed the result to the bucket under


```shell

    s3://..../[2020-12-28 22:06:13,452] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
dev-exchange-rates-to-csv/artifacts/last

```

directory.


Also note that artifacts are automatically archived at each run at

```shell

    s3://..../[2020-12-28 22:06:13,452] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
dev-exchange-rates-to-csv/artifacts/archives/


```

directory.



Recall 04_install/project.yml looks like:

```shell
> cat 04_install/project.yml
```

```shell
version: 0.3
description: Fetch foreign exchange rates

installs:
- venv: tap
  command: pip install tap-exchangeratesapi
- venv: target
  command: pip install target-csv

vars:
- key: base_currency
  value: USD

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
  container_image: xxxxxxxxv
  task: exchange-rates-to-csv

schedules:
- target_id: 1
  cron: "0 0 * * ? *"
  envs:
  - key: __VARS
    value: 'start_date=$(date -I -d "-7 day")'

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
