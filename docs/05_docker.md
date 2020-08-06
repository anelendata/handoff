## Building, running, and pushing a Docker image

We will continue using 03_exchange_rates example.
Instead of running the task on the host machine, let's run on Docker.



Let's build a Docker image.

Try running the following command. Enter y when prompted at the beginning.
The build may take 5~10 minutes.

```
> handoff -p 03_exchange_rates container build
```
```

INFO - 2020-08-06 03:38:59,397 - handoff.config - Reading configurations from 03_exchange_rates/project.yml
INFO - 2020-08-06 03:38:59,478 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
INFO - 2020-08-06 03:38:59,766 - handoff.config - You have the access to AWS resources.
INFO - 2020-08-06 03:38:59,766 - handoff.config - Platform: aws
INFO - 2020-08-06 03:38:59,766 - handoff.config - Setting environment variables from config.
INFO - 2020-08-06 03:38:59,833 - handoff.config - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test
INFO - 2020-08-06 03:38:59,913 - handoff.config - You have the access to AWS resources.
INFO - 2020-08-06 03:38:59,913 - handoff.config - Reading configurations from 03_exchange_rates/project.yml
INFO - 2020-08-06 03:38:59,916 - handoff.config - Platform: aws
INFO - 2020-08-06 03:38:59,916 - handoff.config - Setting environment variables from config.
.
.
.

INFO - 2020-08-06 03:41:40,008 - handoff.config - Step 27/27 : CMD handoff ${COMMAND:-run remote_config} -w workspace -a -d ${DATA:-{}} -a
INFO - 2020-08-06 03:41:40,044 - handoff.config -  ---> Running in 21a548c43c0b

INFO - 2020-08-06 03:41:40,148 - handoff.config -  ---> 1bbadd87b10d

INFO - 2020-08-06 03:41:41,621 - handoff.config - Successfully built 1bbadd87b10d

INFO - 2020-08-06 03:41:41,652 - handoff.config - Successfully tagged singer_exchange_rates_to_csv:0.5
```

Now let's run the code in the Docker container.

```
> handoff -p 03_exchange_rates container run
```
```

INFO - 2020-08-06 03:41:45,336 - handoff.config - Reading configurations from 03_exchange_rates/project.yml
INFO - 2020-08-06 03:41:45,509 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
INFO - 2020-08-06 03:41:45,964 - handoff.config - You have the access to AWS resources.
INFO - 2020-08-06 03:41:45,965 - handoff.config - Platform: aws
INFO - 2020-08-06 03:41:45,965 - handoff.config - Setting environment variables from config.
INFO - 2020-08-06 03:41:46,029 - handoff.config - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test
INFO - 2020-08-06 03:41:46,108 - handoff.config - You have the access to AWS resources.
INFO - 2020-08-06 03:41:46,108 - handoff.config - Reading configurations from 03_exchange_rates/project.yml
INFO - 2020-08-06 03:41:46,111 - handoff.config - Platform: aws
INFO - 2020-08-06 03:41:46,112 - handoff.config - Setting environment variables from config.
.
.
.
INFO - 2020-08-06 03:41:54,603 - handoff.services.cloud.aws.s3 - Copied s3://xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/last/artifacts/collect_stats.json to s3://xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/runs/2020-08-06T03:41:54.279771/artifacts/collect_stats.json

INFO - 2020-08-06 03:41:54,797 - handoff.services.cloud.aws.s3 - Copied s3://xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/last/artifacts/exchange_rate-20200806T033855.csv to s3://xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/runs/2020-08-06T03:41:54.279771/artifacts/exchange_rate-20200806T033855.csv

INFO - 2020-08-06 03:41:55,002 - handoff.services.cloud.aws.s3 - Copied s3://xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/last/artifacts/exchange_rate-20200806T034150.csv to s3://xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/runs/2020-08-06T03:41:54.279771/artifacts/exchange_rate-20200806T034150.csv

INFO - 2020-08-06 03:41:55,172 - handoff.services.cloud.aws.s3 - Copied s3://xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/last/artifacts/state to s3://xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/runs/2020-08-06T03:41:54.279771/artifacts/state

INFO - 2020-08-06 03:41:55,342 - handoff.services.cloud.aws.s3 - Copied s3://xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/last/files/stats_collector.py to s3://xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/runs/2020-08-06T03:41:54.279771/files/stats_collector.py
```

Confirm the run by checking the logs. Also check the artifacts on S3:
```


    xxxxxxxxxxxx-handoff-test/test-03-exchange-rates/last/artifacts/


```

directory.



Now that we know the Docker container runs fine, let's push it to
AWS Elastic Container Registry. This may take a few minutes.

```
> handoff -p 03_exchange_rates container push
```
```

INFO - 2020-08-06 03:41:57,295 - handoff.config - Reading configurations from 03_exchange_rates/project.yml
INFO - 2020-08-06 03:41:57,378 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
INFO - 2020-08-06 03:41:57,659 - handoff.config - You have the access to AWS resources.
INFO - 2020-08-06 03:41:57,659 - handoff.config - Platform: aws
INFO - 2020-08-06 03:41:57,660 - handoff.config - Setting environment variables from config.
INFO - 2020-08-06 03:41:57,725 - handoff.config - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test
INFO - 2020-08-06 03:41:57,804 - handoff.config - You have the access to AWS resources.
INFO - 2020-08-06 03:41:57,804 - handoff.config - Reading configurations from 03_exchange_rates/project.yml
INFO - 2020-08-06 03:41:57,807 - handoff.config - Platform: aws
INFO - 2020-08-06 03:41:57,808 - handoff.config - Setting environment variables from config.
.
.
.
INFO - 2020-08-06 03:44:22,758 - handoff.config - id: 6734fdd29c24 [================================================>  ]  526.1MB/540.8MB
INFO - 2020-08-06 03:44:23,478 - handoff.config - id: c836a53f9c0b [=============================================>     ]    401MB/439.5MB
INFO - 2020-08-06 03:44:24,493 - handoff.config - id: 44aecb8afa22 [=============================================>     ]  400.4MB/439.5MB
INFO - 2020-08-06 03:44:29,789 - handoff.config - id: c836a53f9c0b [================================================>  ]  426.4MB/439.5MB
INFO - 2020-08-06 03:44:29,849 - handoff.config - id: 6734fdd29c24 status: Pushed
INFO - 2020-08-06 03:44:30,083 - handoff.config - id: 44aecb8afa22 [================================================>  ]  426.9MB/439.5MB
INFO - 2020-08-06 03:44:35,306 - handoff.config - id: c836a53f9c0b [==================================================>]  453.1MB
INFO - 2020-08-06 03:44:35,744 - handoff.config - id: 44aecb8afa22 [==================================================>]  453.7MB
INFO - 2020-08-06 03:44:37,333 - handoff.config - id: c836a53f9c0b status: Pushed
INFO - 2020-08-06 03:44:39,716 - handoff.config - id: 44aecb8afa22 status: Pushed
```

Confirm that the Docker image has been uploaded to:

https://console.aws.amazon.com/ecr/repositories?region=us-east-1



Now that the Docker image is prepared, we will finally deploy the task on
AWS Fargate in the next tutorial.

