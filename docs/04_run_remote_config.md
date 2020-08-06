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
{ "base": "JPY", "start_date": "2020-07-10" }
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

Often times, such configuration files contain sensitive information.
So we push the configrations to a secure key store such as
AWS Systems Manager (SSM) Parameter Store (In SecuresString format)
handoff wraps this proces by a single command. handoff packs all the JSON
format files under the configuration directory and send it to the remote
key-value storage.

Try running:

```shell
> handoff -p 03_exchange_rates config push
```
```shell

INFO - 2020-08-06 03:35:35,362 - handoff.config - Compiling config from 03_exchange_rates
INFO - 2020-08-06 03:35:35,362 - handoff.config - Reading configurations from 03_exchange_rates/project.yml
INFO - 2020-08-06 03:35:35,443 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
INFO - 2020-08-06 03:35:35,732 - handoff.config - You have the access to AWS resources.
INFO - 2020-08-06 03:35:35,732 - handoff.config - Platform: aws
INFO - 2020-08-06 03:35:35,732 - handoff.config - Setting environment variables from config.
INFO - 2020-08-06 03:35:35,799 - handoff.config - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test
INFO - 2020-08-06 03:35:35,799 - handoff.config - Putting the config to AWS SSM Parameter Store with Standard tier
INFO - 2020-08-06 03:35:35,814 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
INFO - 2020-08-06 03:35:36,184 - handoff.config - See the parameters at https://console.aws.amazon.com/systems-manager/parameters/?region=us-east-1&tab=Table#list_parameter_filters=Name:Contains:xxxxxxxxe-rates-config
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
> handoff -p 03_exchange_rates cloud create_bucket
```
```shell

INFO - 2020-08-06 03:35:36,484 - handoff.config - Reading configurations from 03_exchange_rates/project.yml
INFO - 2020-08-06 03:35:36,567 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
INFO - 2020-08-06 03:35:36,854 - handoff.config - You have the access to AWS resources.
INFO - 2020-08-06 03:35:36,854 - handoff.config - Platform: aws
INFO - 2020-08-06 03:35:36,855 - handoff.config - Setting environment variables from config.
INFO - 2020-08-06 03:35:36,921 - handoff.config - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test
INFO - 2020-08-06 03:35:37,361 - handoff.config - Reading configurations from 03_exchange_rates/project.yml
INFO - 2020-08-06 03:35:37,364 - handoff.config - Platform: aws
INFO - 2020-08-06 03:35:37,365 - handoff.config - Setting environment variables from config.
INFO - 2020-08-06 03:35:37,381 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
.
.
.
INFO - 2020-08-06 03:35:37,815 - handoff.config - {'StackId': 'arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/handoff-test-bucket/xxxxxxxx861a6983', 'ResponseMetadata': {'RequestId': 'xxxxxxxx36ff08b9', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'xxxxxxxx36ff08b9', 'content-type': 'text/xml', 'content-length': '389', 'date': 'Thu, 06 Aug 2020 03:35:37 GMT'}, 'RetryAttempts': 0}}
INFO - 2020-08-06 03:35:37,815 - handoff.config - Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?viewNested=true&hideStacks=false&stackId=arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/handoff-test-bucket/xxxxxxxx861a6983
```

Wait for a minute and check here

```shell
    https://s3.console.aws.amazon.com
```

to make sure the bucket is created before you proceed.



Now it's time to push the files to the bucket.

Try running:

```shell
> handoff -p 03_exchange_rates files push
```
```shell

INFO - 2020-08-06 03:38:38,087 - handoff.config - Reading configurations from 03_exchange_rates/project.yml
INFO - 2020-08-06 03:38:38,168 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
INFO - 2020-08-06 03:38:38,456 - handoff.config - You have the access to AWS resources.
INFO - 2020-08-06 03:38:38,456 - handoff.config - Platform: aws
INFO - 2020-08-06 03:38:38,456 - handoff.config - Setting environment variables from config.
INFO - 2020-08-06 03:38:38,523 - handoff.config - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test
INFO - 2020-08-06 03:38:38,538 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
INFO - 2020-08-06 03:38:38,620 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
INFO - 2020-08-06 03:38:38,914 - handoff.services.cloud.aws.s3 - Uploading 03_exchange_rates/files to bucket xxxxxxxxxxxx-handoff-test
INFO - 2020-08-06 03:38:38,915 - handoff.services.cloud.aws.s3 - Files to be uploaded: ['03_exchange_rates/files/stats_collector.py']
.
.
.
INFO - 2020-08-06 03:38:38,915 - handoff.services.cloud.aws.s3 - Uploading 03_exchange_rates/files/stats_collector.py to Amazon S3 bucket xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/last/files/stats_collector.py
INFO - 2020-08-06 03:38:39,279 - handoff.config - See the files at https://s3.console.aws.amazon.com/s3/buckets/xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/last/files/
```

Look at the end of the log that says,

```shell
    See the files at https://s3.console.aws.amazon.com/s3/...
```

Grab the link and open in the browswer (AWS login required) to see the files
directory is uploaded.



Install the workspace:

```shell
> handoff -p 03_exchange_rates -w workspace workspace install
```
```shell

INFO - 2020-08-06 03:38:39,718 - handoff.config - Reading configurations from 03_exchange_rates/project.yml
INFO - 2020-08-06 03:38:39,799 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
INFO - 2020-08-06 03:38:40,082 - handoff.config - You have the access to AWS resources.
INFO - 2020-08-06 03:38:40,082 - handoff.config - Platform: aws
INFO - 2020-08-06 03:38:44,491 - handoff.config - Running /bin/bash -c "source proc_01/bin/activate && pip install wheel && pip install tap-exchangeratesapi"
Requirement already satisfied: wheel in ./proc_01/lib/python3.6/site-packages (0.34.2)
Processing /home/ubuntu/.cache/pip/wheels/1f/73/f9/xxxxxxxx0dba8423841c1404f319bb/tap_exchangeratesapi-0.1.1-cp36-none-any.whl
Collecting requests==2.21.0
  Using cached requests-2.21.0-py2.py3-none-any.whl (57 kB)
Processing /home/ubuntu/.cache/pip/wheels/fc/d8/34/xxxxxxxx027b62dfcf922fdf8e396d/backoff-1.3.2-cp36-none-any.whl
.
.
.
Collecting tzlocal
  Using cached tzlocal-2.1-py2.py3-none-any.whl (16 kB)
Collecting python-dateutil
  Using cached python_dateutil-2.8.1-py2.py3-none-any.whl (227 kB)
Collecting pytz
  Using cached pytz-2020.1-py2.py3-none-any.whl (510 kB)
Collecting six>=1.5
  Using cached six-1.15.0-py2.py3-none-any.whl (10 kB)
Installing collected packages: pytzdata, pytz, tzlocal, six, python-dateutil, pendulum, simplejson, singer-python, jsonschema, target-csv
Successfully installed jsonschema-2.6.0 pendulum-1.2.0 python-dateutil-2.8.1 pytz-2020.1 pytzdata-2020.1 simplejson-3.11.1 singer-python-2.1.4 six-1.15.0 target-csv-0.3.0 tzlocal-2.1
```

Now let's run the command by pulling the configurations and files from remote. 

Try running:

```shell
> handoff -p 03_exchange_rates -w workspace run remote_config --push-artifacts
```
```shell

INFO - 2020-08-06 03:38:53,883 - handoff.config - Reading configurations from 03_exchange_rates/project.yml
INFO - 2020-08-06 03:38:53,963 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
INFO - 2020-08-06 03:38:54,248 - handoff.config - You have the access to AWS resources.
INFO - 2020-08-06 03:38:54,248 - handoff.config - Platform: aws
INFO - 2020-08-06 03:38:54,248 - handoff.config - Setting environment variables from config.
INFO - 2020-08-06 03:38:54,315 - handoff.config - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test
INFO - 2020-08-06 03:38:54,315 - handoff.config - Writing configuration files in the workspace configuration directory workspace/config
INFO - 2020-08-06 03:38:54,315 - handoff.config - Reading configurations from remote parameter store.
INFO - 2020-08-06 03:38:54,316 - handoff.config - Reading precompiled config from remote.
INFO - 2020-08-06 03:38:54,330 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
.
.
.
INFO - 2020-08-06 03:38:57,479 - handoff.services.cloud.aws.s3 - Files to be uploaded: ['workspace/artifacts/state', 'workspace/artifacts/exchange_rate-20200806T033855.csv', 'workspace/artifacts/collect_stats.json']
INFO - 2020-08-06 03:38:57,479 - handoff.services.cloud.aws.s3 - Uploading workspace/artifacts/state to Amazon S3 bucket xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/last/artifacts/state
INFO - 2020-08-06 03:38:57,631 - handoff.services.cloud.aws.s3 - Uploading workspace/artifacts/exchange_rate-20200806T033855.csv to Amazon S3 bucket xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/last/artifacts/exchange_rate-20200806T033855.csv
INFO - 2020-08-06 03:38:57,991 - handoff.services.cloud.aws.s3 - Uploading workspace/artifacts/collect_stats.json to Amazon S3 bucket xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/last/artifacts/collect_stats.json
INFO - 2020-08-06 03:38:58,139 - handoff.config - See the files at https://s3.console.aws.amazon.com/s3/buckets/xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/last/artifacts/
INFO - 2020-08-06 03:38:58,139 - handoff.services.cloud.aws.s3 - Copying recursively from s3://xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/last/* to s3://xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/runs/2020-08-06T03:38:58.139874/*
INFO - 2020-08-06 03:38:58,445 - handoff.services.cloud.aws.s3 - Copied s3://xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/last/artifacts/collect_stats.json to s3://xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/runs/2020-08-06T03:38:58.139874/artifacts/collect_stats.json
INFO - 2020-08-06 03:38:58,644 - handoff.services.cloud.aws.s3 - Copied s3://xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/last/artifacts/exchange_rate-20200806T033855.csv to s3://xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/runs/2020-08-06T03:38:58.139874/artifacts/exchange_rate-20200806T033855.csv
INFO - 2020-08-06 03:38:58,822 - handoff.services.cloud.aws.s3 - Copied s3://xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/last/artifacts/state to s3://xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/runs/2020-08-06T03:38:58.139874/artifacts/state
INFO - 2020-08-06 03:38:58,988 - handoff.services.cloud.aws.s3 - Copied s3://xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/last/files/stats_collector.py to s3://xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/runs/2020-08-06T03:38:58.139874/files/stats_collector.py
```

Notice that we used --push-artifacts option in the last command.
With this option, we pushed the result to the bucket under

```shell
    /last/artifacts

```

directory.


Also note that artifacts are automatically archived at each run at

```shell


    /runs/


```

directory.



Next step is to prepare a Docker image and test running it locally.

