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

[2020-09-15 17:07:27,229] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:154)
[2020-09-15 17:07:27,232] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:199)
[2020-09-15 17:07:27,232] [    INFO] - Setting environment variables from config. - (admin.py:104)
[2020-09-15 17:07:27,353] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 17:07:27,630] [    INFO] - You have the access to AWS resources. - (__init__.py:66)
[2020-09-15 17:07:27,698] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test - (admin.py:121)
[2020-09-15 17:07:29,711] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 17:07:30,438] [    INFO] - {'StackId': 'arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/handoff-test-resources/xxxxxxxx11d18427', 'ResponseMetadata': {'RequestId': 'xxxxxxxxdf537570', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'xxxxxxxxdf537570', 'content-type': 'text/xml', 'content-length': '392', 'date': 'Tue, 15 Sep 2020 17:07:29 GMT'}, 'RetryAttempts': 0}} - (__init__.py:406)
[2020-09-15 17:07:30,438] [    INFO] - Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?viewNested=true&hideStacks=false&stackId=arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/handoff-test-resources/xxxxxxxx11d18427 - (__init__.py:32)
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

[2020-09-15 17:10:30,898] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:154)
[2020-09-15 17:10:30,901] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:199)
[2020-09-15 17:10:30,903] [    INFO] - Setting environment variables from config. - (admin.py:104)
[2020-09-15 17:10:31,018] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 17:10:31,303] [    INFO] - You have the access to AWS resources. - (__init__.py:66)
[2020-09-15 17:10:31,368] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test - (admin.py:121)
[2020-09-15 17:10:31,977] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 17:10:32,298] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 17:10:32,921] [    INFO] - {'StackId': 'arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/test-exchange-rates/xxxxxxxx0f614b35', 'ResponseMetadata': {'RequestId': 'xxxxxxxx3b16c52d', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'xxxxxxxx3b16c52d', 'content-type': 'text/xml', 'content-length': '389', 'date': 'Tue, 15 Sep 2020 17:10:32 GMT'}, 'RetryAttempts': 0}} - (__init__.py:455)
[2020-09-15 17:10:32,921] [    INFO] - Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?viewNested=true&hideStacks=false&stackId=arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/test-exchange-rates/xxxxxxxx0f614b35 - (__init__.py:32)
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

[2020-09-15 17:13:33,382] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:154)
[2020-09-15 17:13:33,386] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:199)
[2020-09-15 17:13:33,388] [    INFO] - Setting environment variables from config. - (admin.py:104)
[2020-09-15 17:13:33,507] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 17:13:33,790] [    INFO] - You have the access to AWS resources. - (__init__.py:66)
[2020-09-15 17:13:33,855] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test - (admin.py:121)
[2020-09-15 17:13:34,409] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 17:13:34,446] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 17:13:36,048] [    INFO] - {'tasks': [{'taskArn': 'arn:aws:ecs:us-east-1:xxxxxxxxxxxx:task/xxxxxxxx52bb3c92', 'clusterArn': 'arn:aws:ecs:us-east-1:xxxxxxxxxxxx:cluster/xxxxxxxxates', 'taskDefinitionArn': 'arn:aws:ecs:us-east-1:xxxxxxxxxxxx:task-definition/xxxxxxxxates:6', 'overrides': {'containerOverrides': [{'name': 'singer_exchange_rates_to_csv', 'environment': [{'name': 'TASK_TRIGGERED_AT', 'value': '2020-09-15T17:13:34.395423'}]}], 'inferenceAcceleratorOverrides': []}, 'lastStatus': 'PROVISIONING', 'desiredStatus': 'RUNNING', 'cpu': '256', 'memory': '512', 'containers': [{'containerArn': 'arn:aws:ecs:us-east-1:xxxxxxxxxxxx:container/xxxxxxxx19874dfe', 'taskArn': 'arn:aws:ecs:us-east-1:xxxxxxxxxxxx:task/xxxxxxxx52bb3c92', 'name': 'singer_exchange_rates_to_csv', 'image': 'xxxxxxxxxxxx.dkr.ecr.us-east-1.amazonaws.com/singer_exchange_rates_to_csv:0.1', 'lastStatus': 'PENDING', 'networkInterfaces': [], 'cpu': '256', 'memory': '512'}], 'version': 1, 'createdAt': datetime.datetime(2020, 9, 15, 17, 13, 35, 958000, tzinfo=tzlocal()), 'group': 'family:xxxxxxxxates', 'launchType': 'FARGATE', 'platformVersion': '1.3.0', 'attachments': [{'id': 'xxxxxxxx595821a7', 'type': 'ElasticNetworkInterface', 'status': 'PRECREATED', 'details': [{'name': 'subnetId', 'value': 'subnet-05af9d943717188af'}]}], 'tags': []}], 'failures': [], 'ResponseMetadata': {'RequestId': 'xxxxxxxxf1281f36', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'xxxxxxxxf1281f36', 'content-type': 'application/x-amz-json-1.1', 'content-length': '1360', 'date': 'Tue, 15 Sep 2020 17:13:35 GMT'}, 'RetryAttempts': 0}} - (__init__.py:482)
[2020-09-15 17:13:36,048] [    INFO] - Check the task at https://us-east-1.console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/xxxxxxxxates/tasks/xxxxxxxx52bb3c92 - (__init__.py:51)
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

[2020-09-15 17:18:36,513] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:154)
[2020-09-15 17:18:36,517] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:199)
[2020-09-15 17:18:36,518] [    INFO] - Setting environment variables from config. - (admin.py:104)
[2020-09-15 17:18:36,631] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 17:18:36,921] [    INFO] - You have the access to AWS resources. - (__init__.py:66)
[2020-09-15 17:18:36,988] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test - (admin.py:121)
[2020-09-15 17:18:37,532] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
2020-09-15 17:15:08.685000 - [2020-09-15 17:15:08,684] [    INFO] - Reading configurations from remote parameter store. - (admin.py:447)
2020-09-15 17:15:08.685000 - [2020-09-15 17:15:08,685] [    INFO] - Reading precompiled config from remote. - (admin.py:143)
2020-09-15 17:15:08.995000 - [2020-09-15 17:15:08,995] [    INFO] - Role ARN: arn:aws:iam::xxxxxxxxxxxx:role/xxxxxxxxates-TaskRole - (credentials.py:22)
.
.
.
s.json to s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T17:15:13.126281/artifacts/collect_stats.json - (s3.py:53)
2020-09-15 17:15:13.280000 - [2020-09-15 17:15:13,280] [    INFO] - Copied s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/exchange_rate-20200915T165453.csv to s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T17:15:13.126281/artifacts/exchange_rate-20200915T165453.csv - (s3.py:53)
2020-09-15 17:15:13.376000 - [2020-09-15 17:15:13,375] [    INFO] - Copied s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/exchange_rate-20200915T170326.csv to s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T17:15:13.126281/artifacts/exchange_rate-20200915T170326.csv - (s3.py:53)
2020-09-15 17:15:13.455000 - [2020-09-15 17:15:13,454] [    INFO] - Copied s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/exchange_rate-20200915T171511.csv to s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T17:15:13.126281/artifacts/exchange_rate-20200915T171511.csv - (s3.py:53)
2020-09-15 17:15:13.515000 - [2020-09-15 17:15:13,515] [    INFO] - Copied s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/state to s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T17:15:13.126281/artifacts/state - (s3.py:53)
2020-09-15 17:15:13.587000 - [2020-09-15 17:15:13,587] [    INFO] - Copied s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/files/stats_collector.py to s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T17:15:13.126281/files/stats_collector.py - (s3.py:53)
xxxxxxxxxxxx7
```

The log can also take the parameters such as start_time, end_time, and follow:
```
handoff cloud logs -p 03_exchange_rates -d follow=true start_time="2020-09-15 07:18:00"
```

follow=true will wait for more logs to be produced. ctrl-C to quit.



We confirmed that the task run in the same way as local execution.
Now let's go to the next section to learn how to schedule the task
so it runs periodically.

