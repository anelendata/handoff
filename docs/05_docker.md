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

[2020-09-15 16:54:57,503] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:154)
[2020-09-15 16:54:57,506] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:199)
[2020-09-15 16:54:57,508] [    INFO] - Setting environment variables from config. - (admin.py:104)
[2020-09-15 16:54:57,626] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 16:54:57,910] [    INFO] - You have the access to AWS resources. - (__init__.py:66)
[2020-09-15 16:54:57,978] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test - (admin.py:121)
[2020-09-15 16:54:58,085] [    INFO] - You have the access to AWS resources. - (__init__.py:66)
[2020-09-15 16:54:58,085] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:154)
[2020-09-15 16:54:58,088] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:199)
[2020-09-15 16:54:58,088] [    INFO] - Setting environment variables from config. - (admin.py:104)
.
.
.
 - (impl.py:101)
[2020-09-15 17:03:05,396] [    INFO] - Step 27/27 : CMD handoff ${COMMAND:-run} -w workspace -a -d ${DATA:-"dummy=1"} -a - (impl.py:101)
[2020-09-15 17:03:05,433] [    INFO] -  ---> Running in c68be66fc7be
 - (impl.py:101)
[2020-09-15 17:03:05,540] [    INFO] -  ---> c1b0adcfac9a
 - (impl.py:101)
[2020-09-15 17:03:11,992] [    INFO] - Successfully built c1b0adcfac9a
 - (impl.py:101)
[2020-09-15 17:03:12,009] [    INFO] - Successfully tagged singer_exchange_rates_to_csv:0.1
 - (impl.py:101)
```

Now let's run the code in the Docker container.

```shell
> handoff container run -p 03_exchange_rates
```
```shell

[2020-09-15 17:03:18,506] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:154)
[2020-09-15 17:03:18,512] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:199)
[2020-09-15 17:03:18,514] [    INFO] - Setting environment variables from config. - (admin.py:104)
[2020-09-15 17:03:18,724] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 17:03:19,183] [    INFO] - You have the access to AWS resources. - (__init__.py:66)
[2020-09-15 17:03:19,247] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test - (admin.py:121)
[2020-09-15 17:03:19,417] [    INFO] - You have the access to AWS resources. - (__init__.py:66)
[2020-09-15 17:03:19,417] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:154)
[2020-09-15 17:03:19,420] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:199)
[2020-09-15 17:03:19,421] [    INFO] - Setting environment variables from config. - (admin.py:104)
.
.
.
[2020-09-15 17:03:28,849] [    INFO] - Copied s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/collect_stats.json to s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T17:03:28.550964/artifacts/collect_stats.json - (s3.py:53)

[2020-09-15 17:03:29,040] [    INFO] - Copied s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/exchange_rate-20200915T165453.csv to s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T17:03:28.550964/artifacts/exchange_rate-20200915T165453.csv - (s3.py:53)

[2020-09-15 17:03:29,236] [    INFO] - Copied s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/exchange_rate-20200915T170326.csv to s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T17:03:28.550964/artifacts/exchange_rate-20200915T170326.csv - (s3.py:53)

[2020-09-15 17:03:29,501] [    INFO] - Copied s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/state to s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T17:03:28.550964/artifacts/state - (s3.py:53)

[2020-09-15 17:03:29,768] [    INFO] - Copied s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/files/stats_collector.py to s3://xxxxxxxxxxxx-handoff-test/test-exchange-rates/runs/2020-09-15T17:03:28.550964/files/stats_collector.py - (s3.py:53)
```

Confirm the run by checking the logs. Also check the artifacts on S3:
```shell


    xxxxxxxxxxxx-handoff-test/test-exchange-rates/last/artifacts/


```

directory.



Now that we know the Docker container runs fine, let's push it to
AWS Elastic Container Registry. This may take a few minutes.

```shell
> handoff container push -p 03_exchange_rates
```
```shell

[2020-09-15 17:03:32,370] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:154)
[2020-09-15 17:03:32,373] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:199)
[2020-09-15 17:03:32,375] [    INFO] - Setting environment variables from config. - (admin.py:104)
[2020-09-15 17:03:32,490] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-09-15 17:03:32,773] [    INFO] - You have the access to AWS resources. - (__init__.py:66)
[2020-09-15 17:03:32,838] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test - (admin.py:121)
[2020-09-15 17:03:32,944] [    INFO] - You have the access to AWS resources. - (__init__.py:66)
[2020-09-15 17:03:32,944] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:154)
[2020-09-15 17:03:32,948] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:199)
[2020-09-15 17:03:32,948] [    INFO] - Setting environment variables from config. - (admin.py:104)
.
.
.
[2020-09-15 17:06:47,417] [    INFO] - id: 077eb5a59fa7 [==========================================>        ]  706.5MB/831MB - (impl.py:172)
[2020-09-15 17:06:50,171] [    INFO] - id: 2549ac7ad267 [==========================================>        ]  706.5MB/831MB - (impl.py:172)
[2020-09-15 17:06:55,213] [    INFO] - id: 077eb5a59fa7 [=============================================>     ]  757.2MB/831MB - (impl.py:172)
[2020-09-15 17:06:56,651] [    INFO] - id: 2549ac7ad267 [=============================================>     ]  756.7MB/831MB - (impl.py:172)
[2020-09-15 17:07:04,541] [    INFO] - id: 077eb5a59fa7 [================================================>  ]  806.5MB/831MB - (impl.py:172)
[2020-09-15 17:07:05,412] [    INFO] - id: 2549ac7ad267 [================================================>  ]  806.5MB/831MB - (impl.py:172)
[2020-09-15 17:07:15,095] [    INFO] - id: 077eb5a59fa7 [==================================================>]  856.4MB - (impl.py:172)
[2020-09-15 17:07:15,404] [    INFO] - id: 2549ac7ad267 [==================================================>]  856.4MB - (impl.py:172)
[2020-09-15 17:07:23,465] [    INFO] - id: 077eb5a59fa7 status: Pushed - (impl.py:163)
[2020-09-15 17:07:23,608] [    INFO] - id: 2549ac7ad267 status: Pushed - (impl.py:163)
```

Confirm that the Docker image has been uploaded to:

https://console.aws.amazon.com/ecr/repositories?region=us-east-1



Now that the Docker image is prepared, we will finally deploy the task on
AWS Fargate in the next tutorial.

