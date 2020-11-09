## Deploying on AWS Fargate

We will finally deploy the task to AWS Fargate so we can automate the
recurring task.


Fargate is part of AWS Elastic Container Service (ECS).
The Fargate task run on the ECS cluster.
We will first need to create a cluster.
(You will only be charged for the usage.)

To make this process easy, handoff packed everything up in a command:

```shell
> handoff cloud resources create -p 03_exchange_rates
```
```shell

[2020-11-09 01:53:22,493] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:144)
[2020-11-09 01:53:22,616] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 01:53:22,897] [    INFO] - You have the access to AWS resources. - (__init__.py:69)
[2020-11-09 01:53:22,897] [    INFO] - Platform: aws - (admin.py:164)
[2020-11-09 01:53:22,897] [    INFO] - Setting environment variables from config. - (admin.py:92)
[2020-11-09 01:53:22,963] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxt - (admin.py:115)
[2020-11-09 01:53:23,509] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 01:53:24,202] [    INFO] - {'StackId': 'arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/dev-handoff-test-resources/xxxxxxxxdf532df1', 'ResponseMetadata': {'RequestId': 'xxxxxxxx1f64cbbf', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'xxxxxxxx1f64cbbf', 'content-type': 'text/xml', 'content-length': '396', 'date': 'Mon, 09 Nov 2020 01:53:23 GMT'}, 'RetryAttempts': 0}} - (__init__.py:417)
[2020-11-09 01:53:24,203] [    INFO] - Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?viewNested=true&hideStacks=false&stackId=arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/dev-handoff-test-resources/xxxxxxxxdf532df1 - (__init__.py:34)
```


At the end of the log, you should see a line like:

```shell

    Check the progress at https://console.aws.amazon.com/cloudformation/home?region=xxxx

```

Grab the entire link and open in a browser (you need to login in to AWS) to see
the progress of the resource creation.

Wait until it says "CREATE_COMPLETE"



Now it's time to deploy the task and here is the command:

```shell
> handoff cloud task create -p 03_exchange_rates
```
```shell

[2020-11-09 01:56:24,676] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:144)
[2020-11-09 01:56:24,798] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 01:56:25,079] [    INFO] - You have the access to AWS resources. - (__init__.py:69)
[2020-11-09 01:56:25,079] [    INFO] - Platform: aws - (admin.py:164)
[2020-11-09 01:56:25,079] [    INFO] - Setting environment variables from config. - (admin.py:92)
[2020-11-09 01:56:25,143] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxt - (admin.py:115)
[2020-11-09 01:56:25,736] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 01:56:26,054] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 01:56:26,567] [    INFO] - {'StackId': 'arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/dev-test-exchange-rates/xxxxxxxx7e59f19f', 'ResponseMetadata': {'RequestId': 'xxxxxxxx77327430', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'xxxxxxxx77327430', 'content-type': 'text/xml', 'content-length': '393', 'date': 'Mon, 09 Nov 2020 01:56:26 GMT'}, 'RetryAttempts': 0}} - (__init__.py:466)
[2020-11-09 01:56:26,567] [    INFO] - Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?viewNested=true&hideStacks=false&stackId=arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/dev-test-exchange-rates/xxxxxxxx7e59f19f - (__init__.py:34)
```


Here again, at the end of the log, you should see a line like:

```shell

    Check the progress at https://console.aws.amazon.com/cloudformation/home?region=xxxx

```

Grab the entire link and open in a browser.

Wait until it says "CREATE_COMPLETE"



Once the task is created, try running on Fargate.
To do so, run this command:

```shell
> handoff cloud run -p 03_exchange_rates
```
```shell

[2020-11-09 01:59:27,047] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:144)
[2020-11-09 01:59:27,166] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 01:59:27,458] [    INFO] - You have the access to AWS resources. - (__init__.py:69)
[2020-11-09 01:59:27,458] [    INFO] - Platform: aws - (admin.py:164)
[2020-11-09 01:59:27,458] [    INFO] - Setting environment variables from config. - (admin.py:92)
[2020-11-09 01:59:27,525] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxt - (admin.py:115)
[2020-11-09 01:59:28,057] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 01:59:28,095] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 01:59:29,877] [    INFO] - {'tasks': [{'taskArn': 'arn:aws:ecs:us-east-1:xxxxxxxxxxxx:task/dev-handoff-test-resources/xxxxxxxxab3f', 'clusterArn': 'arn:aws:ecs:us-east-1:xxxxxxxxxxxx:cluster/dev-handoff-test-resources', 'taskDefinitionArn': 'arn:aws:ecs:us-east-1:xxxxxxxxxxxx:task-definition/xxxxxxxxchange-rates:1', 'overrides': {'containerOverrides': [{'name': 'singer_exchange_rates_to_csv', 'environment': [{'name': 'HO_STAGE', 'value': 'dev'}, {'name': 'TASK_TRIGGERED_AT', 'value': '2020-11-09T01:59:28.042924'}]}], 'inferenceAcceleratorOverrides': []}, 'lastStatus': 'PROVISIONING', 'desiredStatus': 'RUNNING', 'cpu': '256', 'memory': '512', 'containers': [{'containerArn': 'arn:aws:ecs:us-east-1:xxxxxxxxxxxx:container/xxxxxxxx78e76f00', 'taskArn': 'arn:aws:ecs:us-east-1:xxxxxxxxxxxx:task/dev-handoff-test-resources/xxxxxxxxab3f', 'name': 'singer_exchange_rates_to_csv', 'image': 'xxxxxxxxxxxx.dkr.ecr.us-east-1.amazonaws.com/singer_exchange_rates_to_csv:0.1', 'lastStatus': 'PENDING', 'networkInterfaces': [], 'cpu': '256', 'memory': '512'}], 'version': 1, 'createdAt': datetime.datetime(2020, 11, 9, 1, 59, 29, 785000, tzinfo=tzlocal()), 'group': 'family:xxxxxxxxchange-rates', 'launchType': 'FARGATE', 'platformVersion': '1.3.0', 'attachments': [{'id': 'xxxxxxxxe4cd0c76', 'type': 'ElasticNetworkInterface', 'status': 'PRECREATED', 'details': [{'name': 'subnetId', 'value': 'subnet-0b1151d5664fd703d'}]}], 'tags': []}], 'failures': [], 'ResponseMetadata': {'RequestId': 'xxxxxxxxe34c5202', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'xxxxxxxxe34c5202', 'content-type': 'application/x-amz-json-1.1', 'content-length': '1479', 'date': 'Mon, 09 Nov 2020 01:59:29 GMT'}, 'RetryAttempts': 0}} - (__init__.py:495)
[2020-11-09 01:59:29,878] [    INFO] - Check the task at https://us-east-1.console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/dev-handoff-test-resources/tasks/xxxxxxxxab3f - (__init__.py:54)
```

At the end of the log, you should see a line like:

```shell

    Check the task at https://us-east-1.console.aws.amazon.com/ecs/home?region=xxxx

```

Grab the entire link and open in a browser.

At the top you see:
    Task : 5a232313-e390....

In Details tab,

Cluster xxxxxxxxe-rates
Launch type FARGATE
...
Last status    PROVISIONING
Desired status RUNNING



At the bottom of the page, you see:

| Name              | Container Runtime ID | Status       | Image | ..... |
| :---------------- | :------------------- | :----------- | :---- | :---- |
| singer_excha...   | 1371....             | PROVISIONING | xxxxx | ..... |

Expand the section by clicking on a dark side-way trible ">" by the  Task name.

The status should change in this order:

1. PROVIONING
2. RUNNING
3. STOPPED

Once the status becomes RUNNING or STOPPED, you should be able to see
the execution log by clicking "View logs in CloudWatch" link at the bottom
of the section.

The log should be similar to the output from the local execution.



Another way to check the log is to use handoff's built in command:

```shell
> handoff cloud logs -p 03_exchange_rates
```
```shell

[2020-11-09 02:04:30,372] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:144)
[2020-11-09 02:04:30,498] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 02:04:30,779] [    INFO] - You have the access to AWS resources. - (__init__.py:69)
[2020-11-09 02:04:30,779] [    INFO] - Platform: aws - (admin.py:164)
[2020-11-09 02:04:30,779] [    INFO] - Setting environment variables from config. - (admin.py:92)
[2020-11-09 02:04:30,844] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxt - (admin.py:115)
[2020-11-09 02:04:31,373] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
2020-11-09 02:01:07.293000 - [2020-11-09 02:01:07,293] [    INFO] - Reading configurations from remote parameter store. - (admin.py:553)
2020-11-09 02:01:07.293000 - [2020-11-09 02:01:07,293] [    INFO] - Reading precompiled config from remote. - (admin.py:127)
2020-11-09 02:01:07.799000 - [2020-11-09 02:01:07,798] [    INFO] - Found credentials in environment variables. - (credentials.py:1094)
.
.
.
2020-11-09 02:01:21.882000 - [2020-11-09 02:01:21,882] [    INFO] - Copying recursively from s3://xxxxxxxxt/dev-test-exchange-rates/last/* to s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T02:01:21.882183/* - (s3.py:17)
2020-11-09 02:01:22.015000 - [2020-11-09 02:01:22,015] [    INFO] - Copied s3://xxxxxxxxt/dev-test-exchange-rates/last/artifacts/collect_stats.json to s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T02:01:21.882183/artifacts/collect_stats.json - (s3.py:53)
2020-11-09 02:01:22.092000 - [2020-11-09 02:01:22,092] [    INFO] - Copied s3://xxxxxxxxt/dev-test-exchange-rates/last/artifacts/exchange_rate-20201109T014950.csv to s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T02:01:21.882183/artifacts/exchange_rate-20201109T014950.csv - (s3.py:53)
2020-11-09 02:01:22.167000 - [2020-11-09 02:01:22,166] [    INFO] - Copied s3://xxxxxxxxt/dev-test-exchange-rates/last/artifacts/exchange_rate-20201109T015148.csv to s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T02:01:21.882183/artifacts/exchange_rate-20201109T015148.csv - (s3.py:53)
2020-11-09 02:01:22.282000 - [2020-11-09 02:01:22,282] [    INFO] - Copied s3://xxxxxxxxt/dev-test-exchange-rates/last/artifacts/exchange_rate-20201109T020110.csv to s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T02:01:21.882183/artifacts/exchange_rate-20201109T020110.csv - (s3.py:53)
2020-11-09 02:01:22.339000 - [2020-11-09 02:01:22,338] [    INFO] - Copied s3://xxxxxxxxt/dev-test-exchange-rates/last/artifacts/stdout.log to s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T02:01:21.882183/artifacts/stdout.log - (s3.py:53)
2020-11-09 02:01:22.394000 - [2020-11-09 02:01:22,394] [    INFO] - Copied s3://xxxxxxxxt/dev-test-exchange-rates/last/files/stats_collector.py to s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T02:01:21.882183/files/stats_collector.py - (s3.py:53)
2020-11-09 02:01:22.516000 - [2020-11-09 02:01:22,516] [    INFO] - Copied s3://xxxxxxxxt/dev-test-exchange-rates/last/files/tap-config.json to s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T02:01:21.882183/files/tap-config.json - (s3.py:53)
2020-11-09 02:01:22.580000 - [2020-11-09 02:01:22,580] [    INFO] - Copied s3://xxxxxxxxt/dev-test-exchange-rates/last/files/target-config.json to s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T02:01:21.882183/files/target-config.json - (s3.py:53)
xxxxxxxxxxxx0
```

The log can also take the parameters such as start_time, end_time, and follow:
```
handoff cloud logs -p 03_exchange_rates -d follow=true start_time="2020-09-15 07:18:00"
```

follow=true will wait for more logs to be produced. ctrl-C to quit.



We confirmed that the task run in the same way as local execution.
Now let's go to the next section to learn how to schedule the task
so it runs periodically.

