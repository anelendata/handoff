## Scheduling a task on Fargate

In this section, we will learn how to schedule a task so it runs automatically.


To schedule a task, use schedule command with parameters target_id and
cron in [CRON format](https://en.wikipedia.org/wiki/Cron).

We pass those values to handoff with `--data` (`-d` for short) option:


```shell
> handoff cloud schedule -p 03_exchange_rates --data target_id=1 cron='9 02 * * ? *'
```
```shell

[2020-11-09 02:04:32,343] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:144)
[2020-11-09 02:04:32,465] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 02:04:32,745] [    INFO] - You have the access to AWS resources. - (__init__.py:69)
[2020-11-09 02:04:32,746] [    INFO] - Platform: aws - (admin.py:164)
[2020-11-09 02:04:32,746] [    INFO] - Setting environment variables from config. - (admin.py:92)
[2020-11-09 02:04:32,811] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxt - (admin.py:115)
[2020-11-09 02:04:33,314] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 02:04:33,712] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 02:04:34,071] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 02:04:34,682] [    INFO] - {'FailedEntryCount': 0, 'FailedEntries': [], 'ResponseMetadata': {'RequestId': 'xxxxxxxx1d68c4f9', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'xxxxxxxx1d68c4f9', 'content-type': 'application/x-amz-json-1.1', 'content-length': '41', 'date': 'Mon, 09 Nov 2020 02:04:33 GMT'}, 'RetryAttempts': 0}} - (__init__.py:533)
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

