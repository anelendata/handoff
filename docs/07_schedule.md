## Scheduling a task on Fargate

In this section, we will learn how to schedule a task so it runs automatically.

To schedule a task, use schedule command with parameters target_id and
cron in [CRON format](https://en.wikipedia.org/wiki/Cron).

We pass those values to handoff with `--data` (`-d` for short) option:


```shell
> handoff cloud schedule -p 03_exchange_rates --data target_id=1 cron='23 17 * * ? *'
```
```shell

[2020-09-15 17:18:38,459] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:154)
[2020-09-15 17:18:38,462] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:199)
[2020-09-15 17:18:38,464] [    INFO] - Setting environment variables from config. - (admin.py:104)
[2020-09-15 17:18:38,581] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 17:18:38,861] [    INFO] - You have the access to AWS resources. - (__init__.py:66)
[2020-09-15 17:18:38,926] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test - (admin.py:121)
[2020-09-15 17:18:39,449] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 17:18:39,856] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 17:18:40,219] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 17:18:40,821] [    INFO] - {'FailedEntryCount': 0, 'FailedEntries': [], 'ResponseMetadata': {'RequestId': 'xxxxxxxx8a5f6783', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'xxxxxxxx8a5f6783', 'content-type': 'application/x-amz-json-1.1', 'content-length': '41', 'date': 'Tue, 15 Sep 2020 17:18:40 GMT'}, 'RetryAttempts': 0}} - (__init__.py:513)
```


At the end of the log, you should see a line like:

```shell

    Check the progress at Check the status at https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/...

```


Grab the entire link and open in a browser (you need to login in to AWS) to see
it's scheduled.



We confirmed that the task run in the same way as local execution.
Now let's go to the next module to learn how to schedule the task
so it runs periodically.

