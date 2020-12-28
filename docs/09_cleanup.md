## Cleaning up

Let's clean everything up so we won't pay a fraction of penny after forgeting about this exercise.

First unschedule the task:

```shell
> handoff cloud schedule delete -p 04_install -v target_id=1
```
```shell

Check the status at https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/dev-handoff-etl-resources/scheduledTasks
```

Then delete the task:

```shell
> handoff cloud task delete -p 04_install
```
```shell

Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?filteringText=dev-exchange-rates-to-csv
ResponseMetadata:
  HTTPHeaders:
    content-length: '212'
    content-type: text/xml
    date: Mon, 28 Dec 2020 08:22:25 GMT
    x-amzn-requestid: xxxxxxxx4f2b1d70
  HTTPStatusCode: 200
  RequestId: xxxxxxxx4f2b1d70
  RetryAttempts: 0
```

If there is no other task in the same resource group, we can delete it:

```shell
> handoff cloud resources delete -p 04_install
```
```shell

Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?filteringText=dev-handoff-etl
```

Here is how to delete the configurations from SSM Parameter Store:

```shell
> handoff config delete -p 04_install
```
```shell

[2020-12-28 08:22:29,109] [    INFO] - Deleting dev-exchange-rates-to-csv/project.yml from bucket xxxxxxxx - (s3.py:207)
success
```

Here is how to delete the files from S3 bucket:

```shell
> handoff files delete -p 04_install
```
```shell

[2020-12-28 08:22:30,346] [    INFO] - GET s3://xxxxxxxx/dev-exchange-rates-to-csv/files - (s3.py:155)
[2020-12-28 08:22:30,772] [    INFO] - Deleted [{'Key': 'dev-exchange-rates-to-csv/files/stats_collector.py'}, {'Key': 'dev-exchange-rates-to-csv/files/tap-config.json'}, {'Key': 'dev-exchange-rates-to-csv/files/target-config.json'}] - (s3.py:182)
success
```

And here is how to delete the secrets from AWS Systems Manager Parameter Store:

```shell
> handoff secrets delete -p 04_install
```
```shell

Deleting the following keys to remote parameter store:
  - username (task level)
  - password (task level)
  - google_client_secret (resource group level)
Proceed? (y/N)success
```

If there is no other task in the same resource group, we can delete the bucket, too:

```shell
> handoff cloud bucket delete -p 04_install
```
```shell

Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?filteringText=xxxxxxxx
```

The previous command only deleted the CloudFormation stack, but not the bucket itself.
Here is how to delete all the files in s3://xxxxxxxx bucket. This cannot be reversed:

```shell
> aws s3 rm --recursive s3://xxxxxxxx/
```
```shell

delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T08:16:24.766243/exchange_rate-20201228T081623.csv
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T08:07:17.717180/exchange_rate-20201228T080716.csv
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T08:07:17.717180/fetch_exchange_rates_stdout.log
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T08:16:24.766243/exchange_rate-20201228T080809.csv
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T08:07:17.717180/collect_stats.json
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T08:16:24.766243/exchange_rate-20201228T080716.csv
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T08:08:10.685214/fetch_exchange_rates_stdout.log
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last/collect_stats.json
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last/exchange_rate-20201228T080716.csv
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last/exchange_rate-20201228T080809.csv
.
.
.
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T08:08:10.685214/exchange_rate-20201228T080716.csv
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last/exchange_rate-20201228T081623.csv
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T08:08:10.685214/collect_stats.json
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T08:08:10.685214/exchange_rate-20201228T080809.csv
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T08:16:24.766243/collect_stats.json
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2020-12-28T08:16:24.766243/fetch_exchange_rates_stdout.log
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last/fetch_exchange_rates_stdout.log
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
        "createdAt": 1609142895.0
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
Untagged: xxxxxxxxxxxx.dkr.ecr.us-east-1.amazonaws.com/xxxxxxxxv@sha256:xxxxxxxxxxxxxxxxdf179f67
Untagged: xxxxxxxxv:0.1
Deleted: sha256:xxxxxxxxxxxxxxxxe3282a11
```

That's all.

