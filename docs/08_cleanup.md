## Cleaning up

Let's clean everything up so we won't pay a fraction of penny after forgeting about this exercise.

First unschedule the task:

```shell
> handoff cloud unschedule -l warning -p 03_exchange_rates -d target_id=1
```
```shell

```

Then delete the task:

```shell
> handoff cloud task delete -l warning -p 03_exchange_rates
```
```shell

```

If there is no other task in the same resource group, we can delete it:

```shell
> handoff cloud resources delete -l warning -p 03_exchange_rates
```
```shell

```

Here is how to delete the configurations from SSM Parameter Store:

```shell
> handoff config delete -p 03_exchange_rates
```
```shell

[2020-11-09 02:18:23,270] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:144)
[2020-11-09 02:18:23,399] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 02:18:23,677] [    INFO] - You have the access to AWS resources. - (__init__.py:69)
[2020-11-09 02:18:23,677] [    INFO] - Platform: aws - (admin.py:164)
[2020-11-09 02:18:23,677] [    INFO] - Setting environment variables from config. - (admin.py:92)
[2020-11-09 02:18:23,742] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxt - (admin.py:115)
[2020-11-09 02:18:23,756] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
```

Here is how to delete the files from S3 bucket:

```shell
> handoff files delete -p 03_exchange_rates
```
```shell

[2020-11-09 02:18:24,630] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:144)
[2020-11-09 02:18:24,759] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 02:18:25,042] [    INFO] - You have the access to AWS resources. - (__init__.py:69)
[2020-11-09 02:18:25,042] [    INFO] - Platform: aws - (admin.py:164)
[2020-11-09 02:18:25,042] [    INFO] - Setting environment variables from config. - (admin.py:92)
[2020-11-09 02:18:25,109] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxt - (admin.py:115)
[2020-11-09 02:18:25,123] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 02:18:25,177] [    INFO] - GET s3://xxxxxxxxt/dev-test-exchange-rates/last/files - (s3.py:171)
[2020-11-09 02:18:25,582] [    INFO] - Deleted [{'Key': 'dev-test-exchange-rates/last/files/stats_collector.py'}, {'Key': 'dev-test-exchange-rates/last/files/tap-config.json'}, {'Key': 'dev-test-exchange-rates/last/files/target-config.json'}] - (s3.py:198)
```

If there is no other task in the same resource group, we can delete the bucket, too:

```shell
> handoff cloud bucket delete -l warning -p 03_exchange_rates
```
```shell

[2020-11-09 02:18:27,040] [ WARNING] - This will only delete the CloudFormation stack. The bucket xxxxxxxxt will be retained. - (__init__.py:396)
```

The previous command only deleted the CloudFormation stack, but not the bucket itself.
Here is how to delete all the files in s3://xxxxxxxxt bucket. This cannot be reversed:

```shell
> aws s3 rm --recursive s3://xxxxxxxxt/
```
```shell

delete: s3://xxxxxxxxt/dev-test-exchange-rates/last/artifacts/exchange_rate-20201109T015148.csv
delete: s3://xxxxxxxxt/dev-test-exchange-rates/last/artifacts/exchange_rate-20201109T014950.csv
delete: s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T01:49:53.194335/artifacts/collect_stats.json
delete: s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T01:49:53.194335/artifacts/stdout.log
delete: s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T01:51:51.342328/artifacts/exchange_rate-20201109T014950.csv
delete: s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T01:49:53.194335/files/stats_collector.py
delete: s3://xxxxxxxxt/dev-test-exchange-rates/last/artifacts/exchange_rate-20201109T021039.csv
delete: s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T01:49:53.194335/files/tap-config.json
delete: s3://xxxxxxxxt/dev-test-exchange-rates/last/artifacts/collect_stats.json
delete: s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T01:49:53.194335/files/target-config.json
.
.
.
delete: s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T02:10:43.820035/artifacts/stdout.log
delete: s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T02:10:43.820035/artifacts/collect_stats.json
delete: s3://xxxxxxxxt/dev-test-exchange-rates/last/artifacts/exchange_rate-20201109T020110.csv
delete: s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T02:10:43.820035/files/stats_collector.py
delete: s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T02:10:43.820035/files/target-config.json
delete: s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T02:10:43.820035/files/tap-config.json
delete: s3://xxxxxxxxt/dev-test-exchange-rates/last/artifacts/stdout.log
delete: s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T01:49:53.194335/artifacts/exchange_rate-20201109T014950.csv
delete: s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T01:51:51.342328/artifacts/collect_stats.json
delete: s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T02:10:43.820035/artifacts/exchange_rate-20201109T014950.csv
```

Here is how to delete s3://xxxxxxxxt bucket. The bucket must be empty. This cannot be reversed:

```shell
> aws s3 rb s3://xxxxxxxxt
```
```shell

remove_bucket: xxxxxxxxt
```

Now delete singer_exchange_rates_to_csv repository from ECR. This cannot be reversed.
--force option will ignore that we still have images in the repository.

```shell
> aws ecr delete-repository --repository-name singer_exchange_rates_to_csv --force
```
```shell

{
    "repository": {
        "repositoryUri": "xxxxxxxxxxxx.dkr.ecr.us-east-1.amazonaws.com/singer_exchange_rates_to_csv", 
        "registryId": "xxxxxxxxxxxx", 
        "imageTagMutability": "IMMUTABLE", 
        "repositoryArn": "arn:aws:ecr:us-east-1:xxxxxxxxxxxx:repository/singer_exchange_rates_to_csv", 
        "repositoryName": "singer_exchange_rates_to_csv", 
        "createdAt": 1604886717.0
    }
}
```

The following code removes all the locally stored Docker images containing the
project name:

```shell
> docker images --format '{{.Repository}}:{{.Tag}}' |grep singer_exchange_rates_to_csv | xargs -I % sh -c 'docker rmi --force %'
```
```shell

Untagged: xxxxxxxxxxxx.dkr.ecr.us-east-1.amazonaws.com/singer_exchange_rates_to_csv:0.1
Untagged: xxxxxxxxxxxx.dkr.ecr.us-east-1.amazonaws.com/singer_exchange_rates_to_csv@sha256:xxxxxxxxxxxxxxxx4c64a8e6
Untagged: singer_exchange_rates_to_csv:0.1
Deleted: sha256:xxxxxxxxxxxxxxxxdf5203e2
```

That's all.

