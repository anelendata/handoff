## Scheduling a task on Fargate

In this section, we will learn how to schedule a task so it runs automatically.


To schedule a task, use schedule command with parameters target_id and
cron in [CRON format](https://en.wikipedia.org/wiki/Cron).

We pass those values to handoff with `--data` (`-d` for short) option:


```shell
> handoff cloud schedule -p 03_exchange_rates --data target_id=1 cron='53 09 * * ? *'
```
```shell

[2020-11-05 09:48:56,269] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:153)
[2020-11-05 09:48:56,273] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:216)
[2020-11-05 09:48:56,275] [    INFO] - Setting environment variables from config. - (admin.py:105)
[2020-11-05 09:48:56,401] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-05 09:48:56,682] [    INFO] - You have the access to AWS resources. - (__init__.py:67)
[2020-11-05 09:48:56,748] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test - (admin.py:124)
[2020-11-05 09:48:57,323] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-05 09:48:57,730] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-05 09:48:58,093] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-05 09:48:58,674] [    INFO] - {'FailedEntryCount': 0, 'FailedEntries': [], 'ResponseMetadata': {'RequestId': 'xxxxxxxx1089efac', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'xxxxxxxx1089efac', 'content-type': 'application/x-amz-json-1.1', 'content-length': '41', 'date': 'Thu, 05 Nov 2020 09:48:58 GMT'}, 'RetryAttempts': 0}} - (__init__.py:523)
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

