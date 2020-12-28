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

Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?viewNested=true&hideStacks=false&stackId=arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/dev-handoff-etl-resources/xxxxxxxxa8f29061
ResponseMetadata:
  HTTPHeaders:
    content-length: '395'
    content-type: text/xml
    date: Mon, 28 Dec 2020 08:09:20 GMT
    x-amzn-requestid: xxxxxxxxab981c82
  HTTPStatusCode: 200
  RequestId: xxxxxxxxab981c82
  RetryAttempts: 0
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

Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?viewNested=true&hideStacks=false&stackId=arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/dev-exchange-rates-to-csv/xxxxxxxxa0dd9289
ResponseMetadata:
  HTTPHeaders:
    content-length: '395'
    content-type: text/xml
    date: Mon, 28 Dec 2020 08:12:23 GMT
    x-amzn-requestid: xxxxxxxxdef31fe1
  HTTPStatusCode: 200
  RequestId: xxxxxxxxdef31fe1
  RetryAttempts: 0
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

Check the task at https://us-east-1.console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/dev-handoff-etl-resources/tasks/xxxxxxxx0f9d
ResponseMetadata:
  HTTPHeaders:
    content-length: '1530'
    content-type: application/x-amz-json-1.1
    date: Mon, 28 Dec 2020 08:15:26 GMT
    x-amzn-requestid: xxxxxxxx41c4808c
  HTTPStatusCode: 200
  RequestId: xxxxxxxx41c4808c
  RetryAttempts: 0
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

```


To view the log, do:

```shell
> handoff cloud logs -p 04_install
```
```shell

2020-12-28 08:16:21.517000 - [2020-12-28 08:16:21,517] [    INFO] - GET s3://xxxxxxxx/dev-exchange-rates-to-csv/files - (s3.py:66)
2020-12-28 08:16:21.679000 - [2020-12-28 08:16:21,679] [    INFO] - GET s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last - (s3.py:66)
2020-12-28 08:16:21.884000 - Running run in workspace directory
2020-12-28 08:16:21.884000 - Job started at 2020-12-28 08:16:21.883768
2020-12-28 08:16:21.884000 - [2020-12-28 08:16:21,883] [    INFO] - Running pipeline fetch_exchange_rates - (operators.py:193)
2020-12-28 08:16:22.001000 - [2020-12-28 08:16:21,995] [    INFO] - Checking return code of pid 30 - (operators.py:262)
2020-12-28 08:16:23.203000 - INFO Replicating exchange rate data from 2020-12-21 using base USD
2020-12-28 08:16:23.497000 - INFO Replicating exchange rate data from 2020-12-22 using base USD
2020-12-28 08:16:23.606000 - INFO Replicating exchange rate data from 2020-12-23 using base USD
2020-12-28 08:16:23.703000 - INFO Sending version information to singer.io. To disable sending anonymous usage data, set the config parameter "disable_collection" to true
```

The log can also take the parameters such as start_time, end_time, and follow:
```
handoff cloud logs -p 04_install -v follow=true start_time="2020-09-15 07:18:00"
```

follow=true will wait for more logs to be produced. ctrl-C to quit.



We confirmed that the task run in the same way as local execution.
Now let's go to the next section to learn how to schedule the task
so it runs periodically.

