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

[2020-11-05 09:37:44,343] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:153)
[2020-11-05 09:37:44,346] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:216)
[2020-11-05 09:37:44,348] [    INFO] - Setting environment variables from config. - (admin.py:105)
[2020-11-05 09:37:44,471] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-05 09:37:44,752] [    INFO] - You have the access to AWS resources. - (__init__.py:67)
[2020-11-05 09:37:44,817] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test - (admin.py:124)
[2020-11-05 09:37:46,962] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-05 09:37:47,659] [    INFO] - {'StackId': 'arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/handoff-test-resources/xxxxxxxx89d40b93', 'ResponseMetadata': {'RequestId': 'xxxxxxxx356e80f3', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'xxxxxxxx356e80f3', 'content-type': 'text/xml', 'content-length': '392', 'date': 'Thu, 05 Nov 2020 09:37:46 GMT'}, 'RetryAttempts': 0}} - (__init__.py:407)
[2020-11-05 09:37:47,659] [    INFO] - Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?viewNested=true&hideStacks=false&stackId=arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/handoff-test-resources/xxxxxxxx89d40b93 - (__init__.py:32)
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

[2020-11-05 09:40:48,161] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:153)
[2020-11-05 09:40:48,165] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:216)
[2020-11-05 09:40:48,166] [    INFO] - Setting environment variables from config. - (admin.py:105)
[2020-11-05 09:40:48,298] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-05 09:40:48,592] [    INFO] - You have the access to AWS resources. - (__init__.py:67)
[2020-11-05 09:40:48,658] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test - (admin.py:124)
[2020-11-05 09:40:49,355] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-05 09:40:49,674] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-05 09:40:50,295] [    INFO] - {'StackId': 'arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/test-exchange-rates/xxxxxxxxf058f52d', 'ResponseMetadata': {'RequestId': 'xxxxxxxx13c78b8a', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'xxxxxxxx13c78b8a', 'content-type': 'text/xml', 'content-length': '389', 'date': 'Thu, 05 Nov 2020 09:40:49 GMT'}, 'RetryAttempts': 0}} - (__init__.py:456)
[2020-11-05 09:40:50,295] [    INFO] - Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?viewNested=true&hideStacks=false&stackId=arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/test-exchange-rates/xxxxxxxxf058f52d - (__init__.py:32)
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

[2020-11-05 09:43:50,800] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:153)
[2020-11-05 09:43:50,804] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:216)
[2020-11-05 09:43:50,806] [    INFO] - Setting environment variables from config. - (admin.py:105)
[2020-11-05 09:43:50,933] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-05 09:43:51,217] [    INFO] - You have the access to AWS resources. - (__init__.py:67)
[2020-11-05 09:43:51,282] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test - (admin.py:124)
[2020-11-05 09:43:51,908] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-05 09:43:51,948] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-05 09:43:53,598] [    INFO] - {'tasks': [{'taskArn': 'arn:aws:ecs:us-east-1:xxxxxxxxxxxx:task/xxxxxxxxates/xxxxxxxx023b', 'clusterArn': 'arn:aws:ecs:us-east-1:xxxxxxxxxxxx:cluster/xxxxxxxxates', 'taskDefinitionArn': 'arn:aws:ecs:us-east-1:xxxxxxxxxxxx:task-definition/xxxxxxxxates:7', 'overrides': {'containerOverrides': [{'name': 'singer_exchange_rates_to_csv', 'environment': [{'name': 'TASK_TRIGGERED_AT', 'value': '2020-11-05T09:43:51.881612'}]}], 'inferenceAcceleratorOverrides': []}, 'lastStatus': 'PROVISIONING', 'desiredStatus': 'RUNNING', 'cpu': '256', 'memory': '512', 'containers': [{'containerArn': 'arn:aws:ecs:us-east-1:xxxxxxxxxxxx:container/xxxxxxxxc9d40409', 'taskArn': 'arn:aws:ecs:us-east-1:xxxxxxxxxxxx:task/xxxxxxxxates/xxxxxxxx023b', 'name': 'singer_exchange_rates_to_csv', 'image': 'xxxxxxxxxxxx.dkr.ecr.us-east-1.amazonaws.com/singer_exchange_rates_to_csv:0.1', 'lastStatus': 'PENDING', 'networkInterfaces': [], 'cpu': '256', 'memory': '512'}], 'version': 1, 'createdAt': datetime.datetime(2020, 11, 5, 9, 43, 53, 503000, tzinfo=tzlocal()), 'group': 'family:xxxxxxxxates', 'launchType': 'FARGATE', 'platformVersion': '1.3.0', 'attachments': [{'id': 'xxxxxxxx946bb355', 'type': 'ElasticNetworkInterface', 'status': 'PRECREATED', 'details': [{'name': 'subnetId', 'value': 'subnet-0fcc0c09b5401de81'}]}], 'tags': []}], 'failures': [], 'ResponseMetadata': {'RequestId': 'xxxxxxxx1fdc2107', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'xxxxxxxx1fdc2107', 'content-type': 'application/x-amz-json-1.1', 'content-length': '1466', 'date': 'Thu, 05 Nov 2020 09:43:53 GMT'}, 'RetryAttempts': 0}} - (__init__.py:485)
[2020-11-05 09:43:53,599] [    INFO] - Check the task at https://us-east-1.console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/xxxxxxxxates/tasks/xxxxxxxx023b - (__init__.py:52)
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

[2020-11-05 09:48:54,109] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:153)
[2020-11-05 09:48:54,112] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:216)
[2020-11-05 09:48:54,114] [    INFO] - Setting environment variables from config. - (admin.py:105)
[2020-11-05 09:48:54,244] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-05 09:48:54,527] [    INFO] - You have the access to AWS resources. - (__init__.py:67)
[2020-11-05 09:48:54,592] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test - (admin.py:124)
[2020-11-05 09:48:55,211] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
2020-11-05 09:45:38.056000 - [2020-11-05 09:45:38,055] [    INFO] - Reading configurations from remote parameter store. - (admin.py:538)
2020-11-05 09:45:38.056000 - [2020-11-05 09:45:38,056] [    INFO] - Reading precompiled config from remote. - (admin.py:136)
2020-11-05 09:45:38.471000 - [2020-11-05 09:45:38,471] [    INFO] - Role ARN: arn:aws:iam::xxxxxxxxxxxx:role/xxxxxxxxates-TaskRole - (credentials.py:22)
.
.
.
2020-11-05 09:45:44.996000 - [2020-11-05 09:45:44,995] [    INFO] - Uploading workspace/artifacts/exchange_rate-20201105T094541.csv to Amazon S3 bucket xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/exchange_rate-20201105T094541.csv - (s3.py:141)
2020-11-05 09:45:45.085000 - [2020-11-05 09:45:45,085] [    INFO] - See the files at https://s3.console.aws.amazon.com/s3/buckets/xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/ - (__init__.py:243)
2020-11-05 09:45:45.085000 - [2020-11-05 09:45:45,085] [    INFO] - Copying the remote artifacts from last to runs xxxxxxxxxxxx-handoff-test - (admin.py:344)
2020-11-05 09:45:45.086000 - [2020-11-05 09:45:45,085] [    INFO] - Copying recursively from s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/* to s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-11-05T09:45:45.085917/* - (s3.py:17)
2020-11-05 09:45:45.162000 - [2020-11-05 09:45:45,162] [    INFO] - Copied s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/collect_stats.json to s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-11-05T09:45:45.085917/artifacts/collect_stats.json - (s3.py:53)
2020-11-05 09:45:45.231000 - [2020-11-05 09:45:45,231] [    INFO] - Copied s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/exchange_rate-20201105T092417.csv to s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-11-05T09:45:45.085917/artifacts/exchange_rate-20201105T092417.csv - (s3.py:53)
2020-11-05 09:45:45.293000 - [2020-11-05 09:45:45,293] [    INFO] - Copied s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/exchange_rate-20201105T094541.csv to s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-11-05T09:45:45.085917/artifacts/exchange_rate-20201105T094541.csv - (s3.py:53)
2020-11-05 09:45:45.354000 - [2020-11-05 09:45:45,354] [    INFO] - Copied s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/state to s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-11-05T09:45:45.085917/artifacts/state - (s3.py:53)
2020-11-05 09:45:45.408000 - [2020-11-05 09:45:45,407] [    INFO] - Copied s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/files/stats_collector.py to s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-11-05T09:45:45.085917/files/stats_collector.py - (s3.py:53)
xxxxxxxxxxxx8
```

The log can also take the parameters such as start_time, end_time, and follow:
```
handoff cloud logs -p 03_exchange_rates -d follow=true start_time="2020-09-15 07:18:00"
```

follow=true will wait for more logs to be produced. ctrl-C to quit.



We confirmed that the task run in the same way as local execution.
Now let's go to the next section to learn how to schedule the task
so it runs periodically.

