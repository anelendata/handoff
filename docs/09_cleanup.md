## Cleaning up

Let's clean everything up so we won't pay a fraction of penny after forgeting about this exercise.

First unschedule the task:

```shell
> handoff cloud schedule delete -p 04_install -v target_id=1
```
```shell

[2020-12-28 22:19:22,511] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:19:23,479] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
Check the status at https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/dev-handoff-etl-resources/scheduledTasks
```

Then delete the task:

```shell
> handoff cloud task delete -p 04_install
```
```shell

[2020-12-28 22:19:24,439] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:19:25,394] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?filteringText=dev-exchange-rates-to-csv
ResponseMetadata:
  HTTPHeaders:
    content-length: '212'
    content-type: text/xml
    date: Mon, 28 Dec 2020 22:19:25 GMT
    x-amzn-requestid: xxxxxxxx285d21ed
  HTTPStatusCode: 200
```

If there is no other task in the same resource group, we can delete it:

```shell
> handoff cloud resources delete -p 04_install
```
```shell

[2020-12-28 22:19:26,423] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:19:27,374] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?filteringText=dev-handoff-etl
ResponseMetadata:
  HTTPHeaders:
    content-length: '212'
    content-type: text/xml
    date: Mon, 28 Dec 2020 22:19:26 GMT
    x-amzn-requestid: xxxxxxxxb32881fa
  HTTPStatusCode: 200
```

Here is how to delete the configurations from SSM Parameter Store:

```shell
> handoff config delete -p 04_install
```
```shell

[2020-12-28 22:19:28,530] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:19:28,887] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:19:28,940] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:19:29,232] [    INFO] - Deleting dev-exchange-rates-to-csv/project.yml from bucket xxxxxxxx - (s3.py:207)
success
```

Here is how to delete the files from S3 bucket:

```shell
> handoff files delete -p 04_install
```
```shell

[2020-12-28 22:19:30,125] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:19:30,482] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:19:30,516] [    INFO] - GET s3://xxxxxxxx/dev-exchange-rates-to-csv/files - (s3.py:155)
[2020-12-28 22:19:30,957] [    INFO] - Deleted [{'Key': 'dev-exchange-rates-to-csv/files/stats_collector.py'}, {'Key': 'dev-exchange-rates-to-csv/files/tap-config.json'}, {'Key': 'dev-exchange-rates-to-csv/files/target-config.json'}] - (s3.py:182)
success
```

And here is how to delete the secrets from AWS Systems Manager Parameter Store:

```shell
> handoff secrets delete -p 04_install
```
```shell

[2020-12-28 22:19:31,524] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
Deleting the following keys to remote parameter store:
  - username (task level)
  - password (task level)
  - google_client_secret (resource group level)
Proceed? (y/N)[2020-12-28 22:19:31,889] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
success
```

If there is no other task in the same resource group, we can delete the bucket, too:

```shell
> handoff cloud bucket delete -p 04_install
```
```shell

[2020-12-28 22:19:33,123] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:19:34,087] [ WARNING] - This will only delete the CloudFormation stack. The bucket xxxxxxxx will be retained. - (__init__.py:421)
[2020-12-28 22:19:34,103] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?filteringText=xxxxxxxx
ResponseMetadata:
  HTTPHeaders:
    content-length: '212'
    content-type: text/xml
    date: Mon, 28 Dec 2020 22:19:33 GMT
    x-amzn-requestid: xxxxxxxx8e808ac4
```

The previous command only deleted the CloudFormation stack, but not the bucket itself.
Here is how to delete all the files in s3://xxxxxxxx bucket. This cannot be reversed:

```shell
> aws s3 rm --recursive s3://xxxxxxxx/
```
```shell

delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T22:07:05.020533/exchange_rate-20201228T220703.csv
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T22:15:12.784517/exchange_rate-20201228T221511.csv
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T22:06:12.220644/collect_stats.json
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T22:06:12.220644/exchange_rate-20201228T220611.csv
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T22:06:12.220644/fetch_exchange_rates_stdout.log
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T22:15:12.784517/collect_stats.json
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T22:15:12.784517/fetch_exchange_rates_stdout.log
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T22:15:12.784517/exchange_rate-20201228T220703.csv
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last/collect_stats.json
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last/exchange_rate-20201228T220611.csv
.
.
.
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last/exchange_rate-20201228T220703.csv
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last/exchange_rate-20201228T221511.csv
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last/fetch_exchange_rates_stdout.log
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T22:07:05.020533/collect_stats.json
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T22:15:12.784517/exchange_rate-20201228T220611.csv
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T22:07:05.020533/fetch_exchange_rates_stdout.log
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T22:07:05.020533/exchange_rate-20201228T220611.csv
```

Here is how to delete s3://xxxxxxxx bucket. The bucket must be empty. This cannot be reversed:

```shell
> aws s3 rb s3://xxxxxxxx
```
```shell

remove_bucket: xxxxxxxx
```

Now delete xxxxxxxxv repository from ECR. This cannot be reversed.
--force option will ignore that we still have images in the repository.

```shell
> aws ecr delete-repository --repository-name xxxxxxxxv --force
```
```shell

{
    "repository": {
        "repositoryUri": "xxxxxxxxxxxx.dkr.ecr.us-east-1.amazonaws.com/xxxxxxxxv", 
        "registryId": "xxxxxxxxxxxx", 
        "imageTagMutability": "IMMUTABLE", 
        "repositoryArn": "arn:aws:ecr:us-east-1:xxxxxxxxxxxx:repository/xxxxxxxxv", 
        "repositoryName": "xxxxxxxxv", 
        "createdAt": 1609193229.0
    }
}
```

The following code removes all the locally stored Docker images containing the
project name:

```shell
> docker images --format '{{.Repository}}:{{.Tag}}' |grep xxxxxxxxv | xargs -I % sh -c 'docker rmi --force %'
```
```shell

Untagged: xxxxxxxxxxxx.dkr.ecr.us-east-1.amazonaws.com/xxxxxxxxv:0.1
Untagged: xxxxxxxxxxxx.dkr.ecr.us-east-1.amazonaws.com/xxxxxxxxv@sha256:xxxxxxxxxxxxxxxx300a78fc
Untagged: xxxxxxxxv:0.1
Deleted: sha256:xxxxxxxxxxxxxxxxd27649e5
```

That's all.

