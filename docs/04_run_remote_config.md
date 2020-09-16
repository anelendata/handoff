## Running task locally with remotely stored configurations

We will continue using 03_exchange_rates example. But this time, we will
store the configurations to the remote data store.



Let's review how 03_exchange_rates project directory is structured:

```shell
> ls -l 03_exchange_rates
```
```shell

 config
 files
 project.yml
 workspace
```


In the config directory, we have a couple of configuration files:

```shell
> ls -l 03_exchange_rates/config
```
```shell

 tap-config.json
 target-config.json
```


...which look like:

```shell
> cat 03_exchange_rates/config/tap-config.json
```

```shell
{ "base": "JPY", "start_date": "2020-09-01" }
```
```shell
> cat 03_exchange_rates/config/target-config.json
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

[2020-09-15 16:51:32,681] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:154)
[2020-09-15 16:51:32,684] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:199)
[2020-09-15 16:51:32,684] [    INFO] - Setting environment variables from config. - (admin.py:104)
[2020-09-15 16:51:32,804] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 16:51:33,080] [    INFO] - You have the access to AWS resources. - (__init__.py:66)
[2020-09-15 16:51:33,144] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test - (admin.py:121)
[2020-09-15 16:51:33,144] [    INFO] - Compiling config from 03_exchange_rates - (admin.py:527)
[2020-09-15 16:51:33,144] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:154)
[2020-09-15 16:51:33,147] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:199)
[2020-09-15 16:51:33,147] [    INFO] - Setting environment variables from config. - (admin.py:104)
.
.
.
[2020-09-15 16:51:33,148] [    INFO] - Putting parameter /handoff-test/test-exchange-rates/config to AWS SSM Parameter Store with Standard tier - (__init__.py:199)
[2020-09-15 16:51:33,164] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 16:51:33,538] [    INFO] - See the parameters at https://console.aws.amazon.com/systems-manager/parameters/?region=us-east-1&tab=Table#list_parameter_filters=Name:Contains:/handoff-test/test-exchange-rates/config - (__init__.py:205)
```

Look at the end of the log that says,

```shell
    See the parameters at https://console.aws.amazon.com/systems-manager/parameters/?region=...
```

Grab the link and open in the browswer (AWS login required) to confirm that
the parameters are uploaded.



We also have some files needed for the task execution:

```shell
> ls -l 03_exchange_rates/files
```
```shell

 stats_collector.py
```

We need to store this somewhere accessible.
So we will create a cloud data storage (S3 bucket) for that.

Try running:

```shell
> handoff cloud bucket create -p 03_exchange_rates
```
```shell

[2020-09-15 16:51:34,001] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:154)
[2020-09-15 16:51:34,004] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:199)
[2020-09-15 16:51:34,005] [    INFO] - Setting environment variables from config. - (admin.py:104)
[2020-09-15 16:51:34,125] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 16:51:34,399] [    INFO] - You have the access to AWS resources. - (__init__.py:66)
[2020-09-15 16:51:34,463] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test - (admin.py:121)
[2020-09-15 16:51:35,006] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 16:51:35,464] [    INFO] - {'StackId': 'arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/handoff-test-bucket/xxxxxxxx03eab8ad', 'ResponseMetadata': {'RequestId': 'xxxxxxxx270964c1', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'xxxxxxxx270964c1', 'content-type': 'text/xml', 'content-length': '389', 'date': 'Tue, 15 Sep 2020 16:51:35 GMT'}, 'RetryAttempts': 0}} - (__init__.py:374)
[2020-09-15 16:51:35,465] [    INFO] - Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?viewNested=true&hideStacks=false&stackId=arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/handoff-test-bucket/xxxxxxxx03eab8ad - (__init__.py:32)
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

[2020-09-15 16:54:35,923] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:154)
[2020-09-15 16:54:35,927] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:199)
[2020-09-15 16:54:35,929] [    INFO] - Setting environment variables from config. - (admin.py:104)
[2020-09-15 16:54:36,048] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 16:54:36,324] [    INFO] - You have the access to AWS resources. - (__init__.py:66)
[2020-09-15 16:54:36,388] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test - (admin.py:121)
[2020-09-15 16:54:36,403] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 16:54:36,573] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 16:54:36,875] [    INFO] - Uploading 03_exchange_rates/files to bucket xxxxxxxxxxxx-handoff-test - (s3.py:122)
[2020-09-15 16:54:36,876] [    INFO] - Files to be uploaded: ['03_exchange_rates/files/stats_collector.py'] - (s3.py:135)
.
.
.
[2020-09-15 16:54:36,876] [    INFO] - Uploading 03_exchange_rates/files/stats_collector.py to Amazon S3 bucket xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/files/stats_collector.py - (s3.py:141)
[2020-09-15 16:54:37,240] [    INFO] - See the files at https://s3.console.aws.amazon.com/s3/buckets/xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/files/ - (__init__.py:242)
[2020-09-15 16:54:37,514] [    INFO] - Uploading 03_exchange_rates/templates to bucket xxxxxxxxxxxx-handoff-test - (s3.py:122)
[2020-09-15 16:54:37,514] [    INFO] - Nothing found in 03_exchange_rates/templates - (s3.py:132)
[2020-09-15 16:54:37,515] [    INFO] - See the files at https://s3.console.aws.amazon.com/s3/buckets/xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/templates/ - (__init__.py:242)
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

[2020-09-15 16:54:37,987] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:154)
[2020-09-15 16:54:37,990] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:199)
[2020-09-15 16:54:37,992] [    INFO] - Setting environment variables from config. - (admin.py:104)
[2020-09-15 16:54:38,113] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 16:54:38,396] [    INFO] - You have the access to AWS resources. - (__init__.py:66)
[2020-09-15 16:54:38,463] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test - (admin.py:121)
[2020-09-15 16:54:38,463] [    INFO] - Writing configuration files in the workspace configuration directory workspace/config - (admin.py:519)
[2020-09-15 16:54:38,463] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:154)
[2020-09-15 16:54:42,065] [    INFO] - Running /bin/bash -c "source proc_01/bin/activate && pip install wheel" - (admin.py:36)
Requirement already satisfied: wheel in ./proc_01/lib/python3.6/site-packages (0.35.1)
.
.
.
Collecting python-dateutil
  Using cached python_dateutil-2.8.1-py2.py3-none-any.whl (227 kB)
Collecting pytzdata
  Using cached pytzdata-2020.1-py2.py3-none-any.whl (489 kB)
Collecting pytz
  Using cached pytz-2020.1-py2.py3-none-any.whl (510 kB)
Collecting six>=1.5
  Using cached six-1.15.0-py2.py3-none-any.whl (10 kB)
Installing collected packages: jsonschema, pytz, tzlocal, six, python-dateutil, pytzdata, pendulum, simplejson, singer-python, target-csv
Successfully installed jsonschema-2.6.0 pendulum-1.2.0 python-dateutil-2.8.1 pytz-2020.1 pytzdata-2020.1 simplejson-3.11.1 singer-python-2.1.4 six-1.15.0 target-csv-0.3.0 tzlocal-2.1
```

Now let's run the command by pulling the configurations and files from remote. 

Try running:

```shell
> handoff run -w workspace --envs resource_group=handoff-test task=test-exchange-rates --push-artifacts
```
```shell

[2020-09-15 16:54:50,972] [    INFO] - Reading configurations from remote parameter store. - (admin.py:447)
[2020-09-15 16:54:50,972] [    INFO] - Reading precompiled config from remote. - (admin.py:143)
[2020-09-15 16:54:51,094] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 16:54:51,378] [    INFO] - You have the access to AWS resources. - (__init__.py:66)
[2020-09-15 16:54:51,393] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 16:54:51,751] [    INFO] - Fetching the secrets from the remote parameter store. - (admin.py:182)
[2020-09-15 16:54:52,000] [    INFO] - Setting environment variables from config. - (admin.py:104)
[2020-09-15 16:54:52,065] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test - (admin.py:121)
[2020-09-15 16:54:52,066] [    INFO] - Downloading config files from the remote storage xxxxxxxxxxxx-handoff-test - (admin.py:375)
[2020-09-15 16:54:52,080] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
.
.
.
[2020-09-15 16:54:54,561] [    INFO] - Uploading workspace/artifacts/exchange_rate-20200915T165453.csv to Amazon S3 bucket xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/exchange_rate-20200915T165453.csv - (s3.py:141)
[2020-09-15 16:54:54,821] [    INFO] - Uploading workspace/artifacts/state to Amazon S3 bucket xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/state - (s3.py:141)
[2020-09-15 16:54:54,974] [    INFO] - Uploading workspace/artifacts/collect_stats.json to Amazon S3 bucket xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/collect_stats.json - (s3.py:141)
[2020-09-15 16:54:55,123] [    INFO] - See the files at https://s3.console.aws.amazon.com/s3/buckets/xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/ - (__init__.py:242)
[2020-09-15 16:54:55,123] [    INFO] - Copying the remote artifacts from last to runs xxxxxxxxxxxx-handoff-test - (admin.py:294)
[2020-09-15 16:54:55,123] [    INFO] - Copying recursively from s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/* to s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T16:54:55.123929/* - (s3.py:17)
[2020-09-15 16:54:55,423] [    INFO] - Copied s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/collect_stats.json to s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T16:54:55.123929/artifacts/collect_stats.json - (s3.py:53)
[2020-09-15 16:54:55,605] [    INFO] - Copied s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/exchange_rate-20200915T165453.csv to s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T16:54:55.123929/artifacts/exchange_rate-20200915T165453.csv - (s3.py:53)
[2020-09-15 16:54:55,790] [    INFO] - Copied s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/state to s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T16:54:55.123929/artifacts/state - (s3.py:53)
[2020-09-15 16:54:56,025] [    INFO] - Copied s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/files/stats_collector.py to s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T16:54:55.123929/files/stats_collector.py - (s3.py:53)
```

This time, we are not using the local project definition.
We are pulling the project configurations from the remote parameter store identified
by the resource group and task names.

Also notice that we used --push-artifacts option in the last command.
With this option, we pushed the result to the bucket under


```shell
    test-exchange-rates/last/artifacts

```

directory.


Also note that artifacts are automatically archived at each run at

```shell


    test-exchange-rates/runs/


```

directory.

Recall 03_exchange_rates/project.yml looks like:

```shell
> cat 03_exchange_rates/project.yml
```

```shell
commands:
  - command: "tap-exchangeratesapi"
    args: "--config config/tap-config.json"
    venv: "proc_01"
    installs:
      - "pip install tap-exchangeratesapi"
  - command: "python files/stats_collector.py"
    venv: "proc_01"
  - command: "target-csv"
    args: "--config config/target-config.json"
    venv: "proc_02"
    installs:
      - "pip install target-csv"
deploy:
  cloud_provider: "aws"
  cloud_platform: "fargate"
  envs:
    resource_group: "handoff-test"
    docker_image: "singer_exchange_rates_to_csv"
    task: "test-exchange-rates"
```

The deploy section specifies:

- cloud_provider: Currently only AWS is supported.
- cloud_platform: The serverless platfor on which the task will run.
- envs: The environment variables set when running `cloud` sub-commands:
  - resource_group: The resource group name, which is used for creating
    remote storage (e.g. AWS S3) names and the remote parameter store's
    namespace. The resource can be shared with multiple tasks.
  - docker_image: The Docker image name given to the current project.
  - task: Task name. Note that multiple tasks with varying configurations can
    be generated from a Docker image.

Next step is to prepare a Docker image and test running it locally.

