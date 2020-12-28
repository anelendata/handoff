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

[2020-12-28 22:08:07,033] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:08:08,023] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?viewNested=true&hideStacks=false&stackId=arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/dev-handoff-etl-resources/xxxxxxxx70f6c675
ResponseMetadata:
  HTTPHeaders:
    content-length: '395'
    content-type: text/xml
    date: Mon, 28 Dec 2020 22:08:08 GMT
    x-amzn-requestid: xxxxxxxx653fb3ca
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

[2020-12-28 22:11:09,397] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:11:10,436] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:11:10,737] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?viewNested=true&hideStacks=false&stackId=arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/dev-exchange-rates-to-csv/xxxxxxxx6fcea8bf
ResponseMetadata:
  HTTPHeaders:
    content-length: '395'
    content-type: text/xml
    date: Mon, 28 Dec 2020 22:11:10 GMT
    x-amzn-requestid: xxxxxxxx26242316
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
> handoff cloud run -p 04_install --envs __VARS='start_date=2020-12-21'
```
```shell

[2020-12-28 22:14:11,902] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:14:12,858] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:14:12,893] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
Check the task at https://us-east-1.console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/dev-handoff-etl-resources/tasks/xxxxxxxxf4d1
ResponseMetadata:
  HTTPHeaders:
    content-length: '1530'
    content-type: application/x-amz-json-1.1
    date: Mon, 28 Dec 2020 22:14:13 GMT
    x-amzn-requestid: xxxxxxxx2cd32826
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

[2020-12-28 22:19:15,336] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:19:16,307] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
```


To view the log, do:

```shell
> handoff cloud logs -p 04_install
```
```shell

[2020-12-28 22:19:17,233] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:19:18,246] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
2020-12-28 22:15:08.809000 - [2020-12-28 22:15:08,809] [    INFO] - Found credentials in environment variables. - (credentials.py:1094)
2020-12-28 22:15:09.100000 - [2020-12-28 22:15:09,100] [    INFO] - Found credentials in environment variables. - (credentials.py:1094)
2020-12-28 22:15:09.458000 - [2020-12-28 22:15:09,458] [    INFO] - Found credentials in environment variables. - (credentials.py:1094)
2020-12-28 22:15:09.738000 - [2020-12-28 22:15:09,738] [    INFO] - GET s3://xxxxxxxx/dev-exchange-rates-to-csv/files - (s3.py:66)
2020-12-28 22:15:09.920000 - [2020-12-28 22:15:09,919] [    INFO] - GET s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last - (s3.py:66)
2020-12-28 22:15:10.090000 - [2020-12-28 22:15:10,090] [    INFO] - Job started at 2020-12-28 22:15:10.090135 - (__init__.py:178)
2020-12-28 22:15:10.090000 - [2020-12-28 22:15:10,090] [    INFO] - Running pipeline fetch_exchange_rates - (operators.py:193)
2020-12-28 22:15:10.200000 - [2020-12-28 22:15:10,193] [    INFO] - Checking return code of pid 32 - (operators.py:262)
```

The log can also take the parameters such as start_time, end_time, and follow:
```
handoff cloud logs -p 04_install -v follow=true start_time="2020-09-15 07:18:00"
```

follow=true will wait for more logs to be produced. ctrl-C to quit.



We confirmed that the task run in the same way as local execution.
Now let's go to the next section to learn how to schedule the task
so it runs periodically.

