## Deploying on AWS Fargate

We will finally deploy the task to AWS Fargate so we can automate the
recurring task.


Fargate is part of AWS Elastic Container Service (ECS).
The Fargate task run on the ECS cluster.
We will first need to create a cluster.
(You will only be charged for the usage.)

To make this process easy, handoff packed everything up in a command:

```shell
> handoff cloud resources create -p 04_install
```
```shell

[2021-04-07 05:22:36,032] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
[2021-04-07 05:22:37,698] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?viewNested=true&hideStacks=false&stackId=arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/dev-handoff-etl-resources/xxxxxxxx8e67507f
ResponseMetadata:
  HTTPHeaders:
    content-length: '395'
    content-type: text/xml
    date: Wed, 07 Apr 2021 05:22:38 GMT
    x-amzn-requestid: xxxxxxxx373c818b
  HTTPStatusCode: 200
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
> handoff cloud task create -p 04_install
```
```shell

[2021-04-07 05:25:39,116] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
[2021-04-07 05:25:40,223] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
[2021-04-07 05:25:40,585] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?viewNested=true&hideStacks=false&stackId=arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/dev-exchange-rates-to-csv/xxxxxxxxa46f2873
ResponseMetadata:
  HTTPHeaders:
    content-length: '395'
    content-type: text/xml
    date: Wed, 07 Apr 2021 05:25:40 GMT
    x-amzn-requestid: xxxxxxxx95b74d11
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
> handoff cloud run -p 04_install --envs __VARS='start_date=$(date -I -d "-7 day")'
```
```shell

[2021-04-07 05:28:41,844] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
[2021-04-07 05:28:42,903] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
[2021-04-07 05:28:42,947] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
Check the task at https://us-east-1.console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/dev-handoff-etl-resources/tasks/xxxxxxxx31d8
ResponseMetadata:
  HTTPHeaders:
    content-length: '1610'
    content-type: application/x-amz-json-1.1
    date: Wed, 07 Apr 2021 05:28:44 GMT
    x-amzn-requestid: xxxxxxxx5dd33cb2
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
| tap-exchange...   | 1371....             | PROVISIONING | xxxxx | ..... |

Expand the section by clicking on a dark side-way trible ">" by the  Task name.

The status should change in this order:

1. PROVIONING
2. RUNNING
3. STOPPED

Once the status becomes RUNNING or STOPPED, you should be able to see
the execution log by clicking "View logs in CloudWatch" link at the bottom
of the section.

The log should be similar to the output from the local execution.



Another way to check the task status and log is to use handoff's built in command.

To check the status of the task, do:

```shell
> handoff cloud task status -p 04_install
```
```shell

[2021-04-07 05:33:45,436] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
[2021-04-07 05:33:46,471] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
- cpu: '256'
  createdAt: 2021-04-07 05:28:44.757000+00:00
  duration: '0:00:05.962000'
  lastStatus: STOPPED
  memory: '512'
  startedAt: 2021-04-07 05:29:49.038000+00:00
  taskArn: arn:aws:ecs:us-east-1:xxxxxxxxxxxx:task/dev-handoff-etl-resources/xxxxxxxx31d8
  taskDefinitionArn: arn:aws:ecs:us-east-1:xxxxxxxxxxxx:task-definition/xxxxxxxx-rates-to-csv:8
```


To view the log, do:

```shell
> handoff cloud logs -p 04_install
```
```shell

[2021-04-07 05:33:47,612] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
[2021-04-07 05:33:48,680] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
2021-04-07 05:29:50.819000 - [2021-04-07 05:29:50,819] [    INFO] - Found credentials in environment variables. - (credentials.py:1100)
2021-04-07 05:29:51.039000 - [2021-04-07 05:29:51,038] [    INFO] - Found credentials in environment variables. - (credentials.py:1100)
2021-04-07 05:29:51.421000 - [2021-04-07 05:29:51,421] [    INFO] - Found credentials in environment variables. - (credentials.py:1100)
2021-04-07 05:29:51.756000 - [2021-04-07 05:29:51,756] [    INFO] - GET s3://xxxxxxxx/dev-exchange-rates-to-csv/files - (s3.py:66)
2021-04-07 05:29:51.940000 - [2021-04-07 05:29:51,940] [    INFO] - GET s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last - (s3.py:66)
2021-04-07 05:29:52.116000 - [2021-04-07 05:29:52,116] [    INFO] - Job started at 2021-04-07 05:29:52.116310 - (__init__.py:178)
2021-04-07 05:29:52.116000 - [2021-04-07 05:29:52,116] [    INFO] - Running pipeline fetch_exchange_rates - (operators.py:194)
2021-04-07 05:29:52.221000 - [2021-04-07 05:29:52,221] [    INFO] - Checking return code of pid 32 - (operators.py:263)
```

The log can also take the parameters such as start_time, end_time, and follow:
```
handoff cloud logs -p 04_install -v follow=true start_time="2020-09-15 07:18:00"
```

follow=true will wait for more logs to be produced. ctrl-C to quit.



We confirmed that the task run in the same way as local execution.
Now let's go to the next section to learn how to schedule the task
so it runs periodically.

