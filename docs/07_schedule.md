## Scheduling a task on Fargate

In this section, we will learn how to schedule a task so it runs automatically.


To schedule a task, use schedule command with target_id and
[CRON format]://en.wikipedia.org/wiki/Cron).

We pass those values to handoff with `--data` (`-d` for short) option:


```
> handoff -p 03_exchange_rates cloud schedule --data '{"target_id": "1", "cron": "55 03 * * ? *"}'
```
```

INFO - 2020-08-06 03:50:50,489 - handoff.config - Reading configurations from 03_exchange_rates/project.yml
INFO - 2020-08-06 03:50:50,570 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
INFO - 2020-08-06 03:50:50,855 - handoff.config - You have the access to AWS resources.
INFO - 2020-08-06 03:50:50,856 - handoff.config - Platform: aws
INFO - 2020-08-06 03:50:50,856 - handoff.config - Setting environment variables from config.
INFO - 2020-08-06 03:50:50,922 - handoff.config - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test
INFO - 2020-08-06 03:50:51,364 - handoff.config - Reading configurations from 03_exchange_rates/project.yml
INFO - 2020-08-06 03:50:51,368 - handoff.config - Platform: aws
INFO - 2020-08-06 03:50:51,373 - handoff.config - Setting environment variables from config.
INFO - 2020-08-06 03:50:51,396 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
.
.
.
INFO - 2020-08-06 03:50:51,760 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
INFO - 2020-08-06 03:50:52,131 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
INFO - 2020-08-06 03:50:52,745 - handoff.config - {'FailedEntryCount': 0, 'FailedEntries': [], 'ResponseMetadata': {'RequestId': 'xxxxxxxxef778e23', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'xxxxxxxxef778e23', 'content-type': 'application/x-amz-json-1.1', 'content-length': '41', 'date': 'Thu, 06 Aug 2020 03:50:52 GMT'}, 'RetryAttempts': 0}}
INFO - 2020-08-06 03:50:52,745 - handoff.config - Check the status at https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/xxxxxxxxe-rates/scheduledTasks
```


At the end of the log, you should see a line like:

```

    Check the progress at Check the status at https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/...

```


Grab the entire link and open in a browser (you need to login in to AWS) to see
it's scheduled.



We confirmed that the task run in the same way as local execution.
Now let's go to the next module to learn how to schedule the task
so it runs periodically.

