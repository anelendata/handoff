## Deploying on AWS Fargate

We will finally deploy the task to AWS Fargate so we can automate the
recurring task.


Fargate is part of AWS Elastic Container Service (ECS).
The Fargate task run on the ECS cluster.
We will first need to create a cluster.
(You will only be charged for the usage.)

To make this process easy, handoff packed everything up in a command:

```
> handoff -p 03_exchange_rates cloud create_resources
```
```

INFO - 2020-08-06 03:44:42,787 - handoff.config - Reading configurations from 03_exchange_rates/project.yml
INFO - 2020-08-06 03:44:42,867 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
INFO - 2020-08-06 03:44:43,152 - handoff.config - You have the access to AWS resources.
INFO - 2020-08-06 03:44:43,152 - handoff.config - Platform: aws
INFO - 2020-08-06 03:44:43,152 - handoff.config - Setting environment variables from config.
INFO - 2020-08-06 03:44:43,218 - handoff.config - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test
INFO - 2020-08-06 03:44:44,678 - handoff.config - Reading configurations from 03_exchange_rates/project.yml
INFO - 2020-08-06 03:44:44,686 - handoff.config - Platform: aws
INFO - 2020-08-06 03:44:44,686 - handoff.config - Setting environment variables from config.
INFO - 2020-08-06 03:44:44,709 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
.
.
.
INFO - 2020-08-06 03:44:45,269 - handoff.config - {'StackId': 'arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/handoff-test-resources/xxxxxxxxdd50faa5', 'ResponseMetadata': {'RequestId': 'xxxxxxxx20b2ef81', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'xxxxxxxx20b2ef81', 'content-type': 'text/xml', 'content-length': '392', 'date': 'Thu, 06 Aug 2020 03:44:45 GMT'}, 'RetryAttempts': 0}}
INFO - 2020-08-06 03:44:45,270 - handoff.config - Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?viewNested=true&hideStacks=false&stackId=arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/handoff-test-resources/xxxxxxxxdd50faa5
```


At the end of the log, you should see a line like:

```

    Check the progress at https://console.aws.amazon.com/cloudformation/home?region=xxxx

```

Grab the entire link and open in a browser (you need to login in to AWS) to see
the progress of the resource creation.

Wait until it says "CREATE_COMPLETE"



Now it's time to deploy the task and here is the command:

```
> handoff -p 03_exchange_rates cloud create_task
```
```

INFO - 2020-08-06 03:47:45,531 - handoff.config - Reading configurations from 03_exchange_rates/project.yml
INFO - 2020-08-06 03:47:45,610 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
INFO - 2020-08-06 03:47:45,897 - handoff.config - You have the access to AWS resources.
INFO - 2020-08-06 03:47:45,897 - handoff.config - Platform: aws
INFO - 2020-08-06 03:47:45,898 - handoff.config - Setting environment variables from config.
INFO - 2020-08-06 03:47:45,964 - handoff.config - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test
INFO - 2020-08-06 03:47:46,436 - handoff.config - Reading configurations from 03_exchange_rates/project.yml
INFO - 2020-08-06 03:47:46,439 - handoff.config - Platform: aws
INFO - 2020-08-06 03:47:46,439 - handoff.config - Setting environment variables from config.
INFO - 2020-08-06 03:47:46,521 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
.
.
.
INFO - 2020-08-06 03:47:46,847 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
INFO - 2020-08-06 03:47:47,363 - handoff.config - {'StackId': 'arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/test-03-exchange-rates/xxxxxxxxa78ee1f9', 'ResponseMetadata': {'RequestId': 'xxxxxxxxdb623334', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'xxxxxxxxdb623334', 'content-type': 'text/xml', 'content-length': '392', 'date': 'Thu, 06 Aug 2020 03:47:46 GMT'}, 'RetryAttempts': 0}}
INFO - 2020-08-06 03:47:47,363 - handoff.config - Check the progress at https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?viewNested=true&hideStacks=false&stackId=arn:aws:cloudformation:us-east-1:xxxxxxxxxxxx:stack/test-03-exchange-rates/xxxxxxxxa78ee1f9
```


Here again, at the end of the log, you should see a line like:

```

    Check the progress at https://console.aws.amazon.com/cloudformation/home?region=xxxx

```

Grab the entire link and open in a browser.

Wait until it says "CREATE_COMPLETE"



Once the task is created, try running on Fargate.
To do so, run this command:

```
> handoff -p 03_exchange_rates cloud run
```
```

INFO - 2020-08-06 03:50:47,634 - handoff.config - Reading configurations from 03_exchange_rates/project.yml
INFO - 2020-08-06 03:50:47,713 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
INFO - 2020-08-06 03:50:48,005 - handoff.config - You have the access to AWS resources.
INFO - 2020-08-06 03:50:48,005 - handoff.config - Platform: aws
INFO - 2020-08-06 03:50:48,006 - handoff.config - Setting environment variables from config.
INFO - 2020-08-06 03:50:48,073 - handoff.config - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test
INFO - 2020-08-06 03:50:48,546 - handoff.config - Reading configurations from 03_exchange_rates/project.yml
INFO - 2020-08-06 03:50:48,550 - handoff.config - Platform: aws
INFO - 2020-08-06 03:50:48,550 - handoff.config - Setting environment variables from config.
INFO - 2020-08-06 03:50:48,565 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
.
.
.
INFO - 2020-08-06 03:50:48,602 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
INFO - 2020-08-06 03:50:50,202 - handoff.config - {'tasks': [{'taskArn': 'arn:aws:ecs:us-east-1:xxxxxxxxxxxx:task/xxxxxxxx2f7337f3', 'clusterArn': 'arn:aws:ecs:us-east-1:xxxxxxxxxxxx:cluster/xxxxxxxxe-rates', 'taskDefinitionArn': 'arn:aws:ecs:us-east-1:xxxxxxxxxxxx:task-definition/xxxxxxxxe-rates:11', 'overrides': {'containerOverrides': [{'name': 'singer_exchange_rates_to_csv', 'environment': [{'name': 'TASK_TRIGGERED_AT', 'value': '2020-08-06T03:50:48.550977'}]}], 'inferenceAcceleratorOverrides': []}, 'lastStatus': 'PROVISIONING', 'desiredStatus': 'RUNNING', 'cpu': '256', 'memory': '512', 'containers': [{'containerArn': 'arn:aws:ecs:us-east-1:xxxxxxxxxxxx:container/xxxxxxxxd07ec661', 'taskArn': 'arn:aws:ecs:us-east-1:xxxxxxxxxxxx:task/xxxxxxxx2f7337f3', 'name': 'singer_exchange_rates_to_csv', 'image': 'xxxxxxxxxxxx.dkr.ecr.us-east-1.amazonaws.com/singer_exchange_rates_to_csv:0.5', 'lastStatus': 'PENDING', 'networkInterfaces': [], 'cpu': '256', 'memory': '512'}], 'version': 1, 'createdAt': datetime.datetime(2020, 8, 6, 3, 50, 50, 108000, tzinfo=tzlocal()), 'group': 'family:xxxxxxxxe-rates', 'launchType': 'FARGATE', 'platformVersion': '1.3.0', 'attachments': [{'id': 'xxxxxxxx028447f7', 'type': 'ElasticNetworkInterface', 'status': 'PRECREATED', 'details': [{'name': 'subnetId', 'value': 'subnet-0c65a427feccde6be'}]}], 'tags': []}], 'failures': [], 'ResponseMetadata': {'RequestId': 'xxxxxxxx2456c334', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'xxxxxxxx2456c334', 'content-type': 'application/x-amz-json-1.1', 'content-length': '1370', 'date': 'Thu, 06 Aug 2020 03:50:49 GMT'}, 'RetryAttempts': 0}}
INFO - 2020-08-06 03:50:50,202 - handoff.config - Check the task at https://us-east-1.console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/xxxxxxxxe-rates/tasks/xxxxxxxx2f7337f3
```

At the end of the log, you should see a line like:

```

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
| singer_excha... | 1371....             | PROVISIONING | xxxxx | ..... |

Expand the section by clicking on a dark side-way trible ">" by the  Task name.

The status should change in this order:

1. PROVIONING
2. RUNNING
3. STOPPED

Once the status becomes RUNNING or STOPPED, you should be able to see
the execution log by clicking "View logs in CloudWatch" link at the bottom
of the section.

The log should be similar to the output from the local execution.



We confirmed that the task run in the same way as local execution.
Now let's go to the next section to learn how to schedule the task
so it runs periodically.

