## Cleaning up

Let's clean everything up so we won't pay a fraction of penny after forgeting about this exercise.

First unschedule the task:

```shell
> handoff -l warning -p 03_exchange_rates cloud unschedule -d '{"target_id": 1}'
```

Then delete the task:

```shell
> handoff -l warning -p 03_exchange_rates cloud delete_task
```

If there is no other task in the same resource group, we can delete it:

```shell
> handoff -l warning -p 03_exchange_rates cloud delete_resources
```

Here is how to delete the configurations from SSM Parameter Store:

```shell
> handoff -p 03_exchange_rates config delete
```
```shell

INFO - 2020-08-06 03:34:46,049 - handoff.config - Reading configurations from 03_exchange_rates/project.yml
INFO - 2020-08-06 03:34:46,131 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
INFO - 2020-08-06 03:34:46,415 - handoff.config - You have the access to AWS resources.
INFO - 2020-08-06 03:34:46,415 - handoff.config - Platform: aws
INFO - 2020-08-06 03:34:46,416 - handoff.config - Setting environment variables from config.
INFO - 2020-08-06 03:34:46,481 - handoff.config - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test
INFO - 2020-08-06 03:34:46,496 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
```

Here is how to delete the files from S3 bucket:

```shell
> handoff -p 03_exchange_rates files delete
```
```shell

INFO - 2020-08-06 03:34:47,114 - handoff.config - Reading configurations from 03_exchange_rates/project.yml
INFO - 2020-08-06 03:34:47,195 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
INFO - 2020-08-06 03:34:47,479 - handoff.config - You have the access to AWS resources.
INFO - 2020-08-06 03:34:47,480 - handoff.config - Platform: aws
INFO - 2020-08-06 03:34:47,480 - handoff.config - Setting environment variables from config.
INFO - 2020-08-06 03:34:47,545 - handoff.config - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test
INFO - 2020-08-06 03:34:47,560 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
INFO - 2020-08-06 03:34:47,602 - handoff.services.cloud.aws.s3 - GET s3://xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/last/files
```

If there is no other task in the same resource group, we can delete the bucket, too:

```shell
> handoff -l warning -p 03_exchange_rates cloud delete_bucket
```
```shell

WARNING - 2020-08-06 03:34:49,044 - handoff.config - This will only delete the CloudFormation stack. The bucket xxxxxxxxxxxx-handoff-test will be retained.
```

The previous command only deleted the CloudFormation stack, but not the bucket itself.
Here is how to delete all the files in s3://xxxxxxxxxxxx-handoff-test bucket. This cannot be reversed:

```shell
> aws s3 rm --recursive s3://xxxxxxxxxxxx-handoff-test/
```

Here is how to delete s3://xxxxxxxxxxxx-handoff-test bucket. The bucket must be empty. This cannot be reversed:

```shell
> aws s3 rb s3://xxxxxxxxxxxx-handoff-test
```

Now delete singer_exchange_rates_to_csv repository from ECR. This cannot be reversed.
--force option will ignore that we still have images in the repository.

```shell
> aws ecr delete-repository --repository-name singer_exchange_rates_to_csv --force
```

If you had created a role and want to delete it, do:

```shell
> handoff -l warning -p 03_exchange_rates cloud delete_role
```

That's all!
