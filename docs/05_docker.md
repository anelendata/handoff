## Building, running, and pushing a Docker image

We will continue using 03_exchange_rates example.
Instead of running the task on the host machine, let's run on Docker.



Let's build a Docker image.

Try running the following command. Enter y when prompted at the beginning.
The build may take 5~10 minutes.

```shell
> handoff container build -p 03_exchange_rates
```
```shell

[2020-11-09 01:49:55,980] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:144)
[2020-11-09 01:49:56,111] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 01:49:56,395] [    INFO] - You have the access to AWS resources. - (__init__.py:69)
[2020-11-09 01:49:56,395] [    INFO] - Platform: aws - (admin.py:164)
[2020-11-09 01:49:56,395] [    INFO] - Setting environment variables from config. - (admin.py:92)
[2020-11-09 01:49:56,461] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxt - (admin.py:115)
[2020-11-09 01:49:56,568] [    INFO] - You have the access to AWS resources. - (__init__.py:69)
[2020-11-09 01:49:56,568] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:144)
[2020-11-09 01:49:56,571] [    INFO] - Platform: aws - (admin.py:164)
[2020-11-09 01:49:56,571] [    INFO] - Setting environment variables from config. - (admin.py:92)
.
.
.
 - (impl.py:123)
[2020-11-09 01:51:40,213] [    INFO] - Step 27/27 : CMD handoff ${COMMAND:-run} -w workspace -a -d $(eval echo ${DATA:-"dummy=1"}) -s ${HO_STAGE:-"test"} -a - (impl.py:123)
[2020-11-09 01:51:40,251] [    INFO] -  ---> Running in 440d97606d31
 - (impl.py:123)
[2020-11-09 01:51:40,378] [    INFO] -  ---> 86c82cd076e6
 - (impl.py:123)
[2020-11-09 01:51:40,683] [    INFO] - Successfully built 86c82cd076e6
 - (impl.py:123)
[2020-11-09 01:51:40,716] [    INFO] - Successfully tagged singer_exchange_rates_to_csv:0.1
 - (impl.py:123)
```

Now let's run the code in the Docker container.

```shell
> handoff container run -p 03_exchange_rates
```
```shell

[2020-11-09 01:51:41,753] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:144)
[2020-11-09 01:51:41,885] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 01:51:42,179] [    INFO] - You have the access to AWS resources. - (__init__.py:69)
[2020-11-09 01:51:42,179] [    INFO] - Platform: aws - (admin.py:164)
[2020-11-09 01:51:42,179] [    INFO] - Setting environment variables from config. - (admin.py:92)
[2020-11-09 01:51:42,246] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxt - (admin.py:115)
[2020-11-09 01:51:42,408] [    INFO] - You have the access to AWS resources. - (__init__.py:69)
[2020-11-09 01:51:42,408] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:144)
[2020-11-09 01:51:42,411] [    INFO] - Platform: aws - (admin.py:164)
[2020-11-09 01:51:42,411] [    INFO] - Setting environment variables from config. - (admin.py:92)
.
.
.
[2020-11-09 01:51:52,021] [    INFO] - Copied s3://xxxxxxxxt/dev-test-exchange-rates/last/artifacts/exchange_rate-20201109T015148.csv to s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T01:51:51.342328/artifacts/exchange_rate-20201109T015148.csv - (s3.py:53)

[2020-11-09 01:51:52,257] [    INFO] - Copied s3://xxxxxxxxt/dev-test-exchange-rates/last/artifacts/stdout.log to s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T01:51:51.342328/artifacts/stdout.log - (s3.py:53)

[2020-11-09 01:51:52,460] [    INFO] - Copied s3://xxxxxxxxt/dev-test-exchange-rates/last/files/stats_collector.py to s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T01:51:51.342328/files/stats_collector.py - (s3.py:53)

[2020-11-09 01:51:52,628] [    INFO] - Copied s3://xxxxxxxxt/dev-test-exchange-rates/last/files/tap-config.json to s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T01:51:51.342328/files/tap-config.json - (s3.py:53)

[2020-11-09 01:51:52,814] [    INFO] - Copied s3://xxxxxxxxt/dev-test-exchange-rates/last/files/target-config.json to s3://xxxxxxxxt/dev-test-exchange-rates/runs/2020-11-09T01:51:51.342328/files/target-config.json - (s3.py:53)
```

Confirm the run by checking the logs. Also check the artifacts on S3:
```shell


    xxxxxxxxt/dev-test-exchange-rates/last/artifacts/


```

directory.



Now that we know the Docker container runs fine, let's push it to
AWS Elastic Container Registry. This may take a few minutes.

```shell
> handoff container push -p 03_exchange_rates
```
```shell

[2020-11-09 01:51:55,477] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:144)
[2020-11-09 01:51:55,600] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 01:51:55,882] [    INFO] - You have the access to AWS resources. - (__init__.py:69)
[2020-11-09 01:51:55,882] [    INFO] - Platform: aws - (admin.py:164)
[2020-11-09 01:51:55,882] [    INFO] - Setting environment variables from config. - (admin.py:92)
[2020-11-09 01:51:55,949] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxt - (admin.py:115)
[2020-11-09 01:51:56,058] [    INFO] - You have the access to AWS resources. - (__init__.py:69)
[2020-11-09 01:51:56,058] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:144)
[2020-11-09 01:51:56,061] [    INFO] - Platform: aws - (admin.py:164)
[2020-11-09 01:51:56,061] [    INFO] - Setting environment variables from config. - (admin.py:92)
.
.
.
[2020-11-09 01:53:01,791] [    INFO] - id: 7e611f0a6c1e [==================================================>]  134.5MB - (impl.py:194)
[2020-11-09 01:53:03,352] [    INFO] - id: 2bd5f77d0941 status: Pushed - (impl.py:185)
[2020-11-09 01:53:03,563] [    INFO] - id: 6734fdd29c24 [=================================>                 ]  362.3MB/540.8MB - (impl.py:194)
[2020-11-09 01:53:03,748] [    INFO] - id: 7e611f0a6c1e status: Pushed - (impl.py:185)
[2020-11-09 01:53:05,884] [    INFO] - id: 6734fdd29c24 [====================================>              ]  395.3MB/540.8MB - (impl.py:194)
[2020-11-09 01:53:08,107] [    INFO] - id: 6734fdd29c24 [=======================================>           ]  429.5MB/540.8MB - (impl.py:194)
[2020-11-09 01:53:10,411] [    INFO] - id: 6734fdd29c24 [==========================================>        ]  460.4MB/540.8MB - (impl.py:194)
[2020-11-09 01:53:13,111] [    INFO] - id: 6734fdd29c24 [=============================================>     ]  492.9MB/540.8MB - (impl.py:194)
[2020-11-09 01:53:15,764] [    INFO] - id: 6734fdd29c24 [================================================>  ]  526.1MB/540.8MB - (impl.py:194)
[2020-11-09 01:53:18,791] [    INFO] - id: 6734fdd29c24 status: Pushed - (impl.py:185)
```

Confirm that the Docker image has been uploaded to:

https://console.aws.amazon.com/ecr/repositories?region=us-east-1



Now that the Docker image is prepared, we will finally deploy the task on
AWS Fargate in the next tutorial.

