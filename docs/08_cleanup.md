## Cleaning up

Let's clean everything up so we won't pay a fraction of penny after forgeting about this exercise.

First unschedule the task:

```shell
> handoff cloud unschedule -l warning -p 03_exchange_rates -d target_id=1
```
```shell

[2020-09-15 17:39:25,290] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:199)
```

Then delete the task:

```shell
> handoff cloud task delete -l warning -p 03_exchange_rates
```
```shell

[2020-09-15 17:39:27,195] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:199)
```

If there is no other task in the same resource group, we can delete it:

```shell
> handoff cloud resources delete -l warning -p 03_exchange_rates
```
```shell

[2020-09-15 17:39:29,121] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:199)
```

Here is how to delete the configurations from SSM Parameter Store:

```shell
> handoff config delete -p 03_exchange_rates
```
```shell

[2020-09-15 17:39:31,098] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:154)
[2020-09-15 17:39:31,101] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:199)
[2020-09-15 17:39:31,103] [    INFO] - Setting environment variables from config. - (admin.py:104)
[2020-09-15 17:39:31,220] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 17:39:31,504] [    INFO] - You have the access to AWS resources. - (__init__.py:66)
[2020-09-15 17:39:31,570] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test - (admin.py:121)
[2020-09-15 17:39:31,584] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
```

Here is how to delete the files from S3 bucket:

```shell
> handoff files delete -p 03_exchange_rates
```
```shell

[2020-09-15 17:39:32,443] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:154)
[2020-09-15 17:39:32,447] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:199)
[2020-09-15 17:39:32,448] [    INFO] - Setting environment variables from config. - (admin.py:104)
[2020-09-15 17:39:32,570] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 17:39:32,857] [    INFO] - You have the access to AWS resources. - (__init__.py:66)
[2020-09-15 17:39:32,923] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test - (admin.py:121)
[2020-09-15 17:39:32,938] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 17:39:33,002] [    INFO] - GET s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/files - (s3.py:173)
[2020-09-15 17:39:33,380] [    INFO] - Deleted [{'Key': 'test-exchange-rates/last/files/stats_collector.py'}] - (s3.py:199)
[2020-09-15 17:39:33,380] [    INFO] - GET s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/templates - (s3.py:173)
.
.
.
[2020-09-15 17:39:33,668] [ WARNING] - Nothing found in the location - (s3.py:189)
[2020-09-15 17:39:33,669] [    INFO] - Deleted [] - (s3.py:199)
```

If there is no other task in the same resource group, we can delete the bucket, too:

```shell
> handoff cloud bucket delete -l warning -p 03_exchange_rates
```
```shell

[2020-09-15 17:39:34,141] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:199)
[2020-09-15 17:39:35,121] [ WARNING] - This will only delete the CloudFormation stack. The bucket xxxxxxxxxxxx-handoff-test will be retained. - (__init__.py:385)
```

The previous command only deleted the CloudFormation stack, but not the bucket itself.
Here is how to delete all the files in s3://xxxxxxxxxxxx-handoff-test bucket. This cannot be reversed:

```shell
> aws s3 rm --recursive s3://xxxxxxxxxxxx-handoff-test/
```
```shell

delete: s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/exchange_rate-20200915T170326.csv
delete: s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T16:54:55.123929/artifacts/exchange_rate-20200915T165453.csv
delete: s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T17:03:28.550964/artifacts/state
delete: s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/state
delete: s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T17:03:28.550964/artifacts/collect_stats.json
delete: s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/collect_stats.json
delete: s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T17:03:28.550964/artifacts/exchange_rate-20200915T170326.csv
delete: s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T16:54:55.123929/files/stats_collector.py
delete: s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T17:03:28.550964/artifacts/exchange_rate-20200915T165453.csv
delete: s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/exchange_rate-20200915T165453.csv
.
.
.
delete: s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T17:25:32.813942/artifacts/exchange_rate-20200915T170326.csv
delete: s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T17:25:32.813942/artifacts/exchange_rate-20200915T165453.csv
delete: s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T17:25:32.813942/artifacts/exchange_rate-20200915T171511.csv
delete: s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T17:25:32.813942/artifacts/exchange_rate-20200915T172531.csv
delete: s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T17:25:32.813942/artifacts/state
delete: s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/exchange_rate-20200915T172531.csv
delete: s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/exchange_rate-20200915T171511.csv
delete: s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T16:54:55.123929/artifacts/state
delete: s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T17:25:32.813942/artifacts/collect_stats.json
delete: s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T17:25:32.813942/files/stats_collector.py
```

Here is how to delete s3://xxxxxxxxxxxx-handoff-test bucket. The bucket must be empty. This cannot be reversed:

```shell
> aws s3 rb s3://xxxxxxxxxxxx-handoff-test
```
```shell

remove_bucket: xxxxxxxxxxxx-handoff-test
```

Now delete singer_exchange_rates_to_csv repository from ECR. This cannot be reversed.
--force option will ignore that we still have images in the repository.

```shell
> aws ecr delete-repository --repository-name singer_exchange_rates_to_csv --force
```
```shell

{
    "repository": {
        "registryId": "xxxxxxxxxxxx", 
        "repositoryName": "singer_exchange_rates_to_csv", 
        "repositoryArn": "arn:aws:ecr:us-east-1:xxxxxxxxxxxx:repository/singer_exchange_rates_to_csv", 
        "createdAt": 1600189413.0, 
        "repositoryUri": "xxxxxxxxxxxx.dkr.ecr.us-east-1.amazonaws.com/singer_exchange_rates_to_csv"
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
Untagged: xxxxxxxxxxxx.dkr.ecr.us-east-1.amazonaws.com/singer_exchange_rates_to_csv@sha256:xxxxxxxxxxxxxxxx4138446a
Untagged: singer_exchange_rates_to_csv:0.1
Deleted: sha256:xxxxxxxxxxxxxxxxbcbd3bf6
```

That's all.

