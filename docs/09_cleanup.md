## Cleaning up

Let's clean everything up so we won't pay a fraction of penny after forgeting about this exercise.

First unschedule the task:

```shell
> handoff cloud schedule delete -p 04_install -v target_id=1
```
```shell

[2021-04-07 04:58:22,666] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
[2021-04-07 04:58:23,699] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
No schedules found
```

Then delete the task:

```shell
> handoff cloud task delete -p 04_install
```
```shell

[2021-04-07 04:58:24,591] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
[2021-04-07 04:58:25,597] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?filteringText=dev-exchange-rates-to-csv
ResponseMetadata:
  HTTPHeaders:
    content-length: '212'
    content-type: text/xml
    date: Wed, 07 Apr 2021 04:58:25 GMT
    x-amzn-requestid: xxxxxxxx84dd5d3d
  HTTPStatusCode: 200
```

If there is no other task in the same resource group, we can delete it:

```shell
> handoff cloud resources delete -p 04_install
```
```shell

[2021-04-07 04:58:26,702] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
[2021-04-07 04:58:27,735] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?filteringText=dev-handoff-etl
ResponseMetadata:
  HTTPHeaders:
    content-length: '212'
    content-type: text/xml
    date: Wed, 07 Apr 2021 04:58:27 GMT
    x-amzn-requestid: xxxxxxxxcb90d89f
  HTTPStatusCode: 200
```

Here is how to delete the configurations from SSM Parameter Store:

```shell
> handoff config delete -p 04_install
```
```shell

[2021-04-07 04:58:28,900] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
[2021-04-07 04:58:29,269] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
[2021-04-07 04:58:29,507] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
[2021-04-07 04:58:29,830] [    INFO] - Deleting dev-exchange-rates-to-csv/project.yml from bucket xxxxxxxx - (s3.py:207)
success
```

Here is how to delete the files from S3 bucket:

```shell
> handoff files delete -p 04_install
```
```shell

[2021-04-07 04:58:30,710] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
[2021-04-07 04:58:31,077] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
[2021-04-07 04:58:31,127] [    INFO] - GET s3://xxxxxxxx/dev-exchange-rates-to-csv/files - (s3.py:155)
[2021-04-07 04:58:31,542] [    INFO] - Deleted [{'Key': 'dev-exchange-rates-to-csv/files/stats_collector.py'}, {'Key': 'dev-exchange-rates-to-csv/files/tap-config.json'}, {'Key': 'dev-exchange-rates-to-csv/files/target-config.json'}] - (s3.py:182)
success
```

And here is how to delete the secrets from AWS Systems Manager Parameter Store:

```shell
> handoff secrets delete -p 04_install
```
```shell

[2021-04-07 04:58:32,133] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
Deleting the following keys to remote parameter store:
  - username (task level)
  - password (task level)
  - google_client_secret (resource group level)
Proceed? (y/N)[2021-04-07 04:58:32,509] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
success
```

If there is no other task in the same resource group, we can delete the bucket, too:

```shell
> handoff cloud bucket delete -p 04_install
```
```shell

[2021-04-07 04:58:33,806] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
[2021-04-07 04:58:34,823] [ WARNING] - This will only delete the CloudFormation stack. The bucket xxxxxxxx will be retained. - (__init__.py:421)
[2021-04-07 04:58:34,837] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?filteringText=xxxxxxxx
ResponseMetadata:
  HTTPHeaders:
    content-length: '212'
    content-type: text/xml
    date: Wed, 07 Apr 2021 04:58:34 GMT
    x-amzn-requestid: xxxxxxxxd719bc59
```

The previous command only deleted the CloudFormation stack, but not the bucket itself.
Here is how to delete all the files in s3://xxxxxxxx bucket. This cannot be reversed:

```shell
> aws s3 rm --recursive s3://xxxxxxxx/
```
```shell

delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2021-04-07T04:45:53.451784/exchange_rate-20210407T044432.csv
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2021-04-07T04:44:34.289110/fetch_exchange_rates_stdout.log
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2021-04-07T04:54:21.040265/exchange_rate-20210407T044549.csv
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2021-04-07T04:54:21.040265/fetch_exchange_rates_stdout.log
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last/collect_stats.json
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2021-04-07T04:44:34.289110/collect_stats.json
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last/exchange_rate-20210407T044432.csv
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2021-04-07T04:54:21.040265/exchange_rate-20210407T045419.csv
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last/exchange_rate-20210407T044549.csv
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last/fetch_exchange_rates_stdout.log
.
.
.
delete: s3://xxxxxxxx/xxxxxxxxse/files/schema/earthquakes.json
delete: s3://xxxxxxxx/xxxxxxxxse/files/custom_spec.json
delete: s3://xxxxxxxx/xxxxxxxxse/files/tap_config.json
delete: s3://xxxxxxxx/xxxxxxxxse/files/target_config.json
delete: s3://xxxxxxxx/xxxxxxxxse/project.yml
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2021-04-07T04:54:21.040265/collect_stats.json
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2021-04-07T04:45:53.451784/exchange_rate-20210407T044549.csv
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2021-04-07T04:54:21.040265/exchange_rate-20210407T044432.csv
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2021-04-07T04:45:53.451784/fetch_exchange_rates_stdout.log
delete: s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/archives/2021-04-07T04:44:34.289110/exchange_rate-20210407T044432.csv
```

Here is how to delete s3://xxxxxxxx bucket. The bucket must be empty. This cannot be reversed:

```shell
> aws s3 rb s3://xxxxxxxx
```
```shell

remove_bucket: xxxxxxxx
```

Now delete xxxxxxxxcsv repository from ECR. This cannot be reversed.
--force option will ignore that we still have images in the repository.

```shell
> aws ecr delete-repository --repository-name xxxxxxxxcsv --force
```
```shell

{
    "repository": {
        "repositoryUri": "xxxxxxxxxxxx.dkr.ecr.us-east-1.amazonaws.com/xxxxxxxxcsv", 
        "registryId": "xxxxxxxxxxxx", 
        "imageTagMutability": "IMMUTABLE", 
        "repositoryArn": "arn:aws:ecr:us-east-1:xxxxxxxxxxxx:repository/xxxxxxxxcsv", 
        "repositoryName": "xxxxxxxxcsv", 
        "createdAt": 1617770758.0
    }
}
```

The following code removes all the locally stored Docker images containing the
project name:

```shell
> docker images --format '{{.Repository}}:{{.Tag}}' |grep xxxxxxxxcsv | xargs -I % sh -c 'docker rmi --force %'
```
```shell

Untagged: xxxxxxxxxxxx.dkr.ecr.us-east-1.amazonaws.com/xxxxxxxxcsv:0.1
Untagged: xxxxxxxxxxxx.dkr.ecr.us-east-1.amazonaws.com/xxxxxxxxcsv@sha256:xxxxxxxxxxxxxxxxd86f3d81
Untagged: xxxxxxxxcsv:0.1
Deleted: sha256:xxxxxxxxxxxxxxxx558280db
```

That's all.

