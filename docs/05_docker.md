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

[2020-11-05 09:24:22,993] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:153)
[2020-11-05 09:24:22,996] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:216)
[2020-11-05 09:24:22,996] [    INFO] - Setting environment variables from config. - (admin.py:105)
[2020-11-05 09:24:23,125] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-05 09:24:23,406] [    INFO] - You have the access to AWS resources. - (__init__.py:67)
[2020-11-05 09:24:23,472] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test - (admin.py:124)
[2020-11-05 09:24:23,582] [    INFO] - You have the access to AWS resources. - (__init__.py:67)
[2020-11-05 09:24:23,582] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:153)
[2020-11-05 09:24:23,585] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:216)
[2020-11-05 09:24:23,585] [    INFO] - Setting environment variables from config. - (admin.py:105)
.
.
.
 - (impl.py:110)
[2020-11-05 09:32:59,063] [    INFO] - Step 27/27 : CMD handoff ${COMMAND:-run} -w workspace -a -d $(eval echo ${DATA:-"dummy=1"}) -a - (impl.py:110)
[2020-11-05 09:32:59,098] [    INFO] -  ---> Running in 9db189ffc3f4
 - (impl.py:110)
[2020-11-05 09:32:59,216] [    INFO] -  ---> fe6369aef884
 - (impl.py:110)
[2020-11-05 09:33:06,386] [    INFO] - Successfully built fe6369aef884
 - (impl.py:110)
[2020-11-05 09:33:06,401] [    INFO] - Successfully tagged singer_exchange_rates_to_csv:0.1
 - (impl.py:110)
```

Now let's run the code in the Docker container.

```shell
> handoff container run -p 03_exchange_rates
```
```shell

[2020-11-05 09:33:13,986] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:153)
[2020-11-05 09:33:13,994] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:216)
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

[2020-11-05 09:33:16,813] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:153)
[2020-11-05 09:33:16,816] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:216)
[2020-11-05 09:33:16,816] [    INFO] - Setting environment variables from config. - (admin.py:105)
[2020-11-05 09:33:16,941] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-05 09:33:17,222] [    INFO] - You have the access to AWS resources. - (__init__.py:67)
[2020-11-05 09:33:17,288] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test - (admin.py:124)
[2020-11-05 09:33:17,463] [    INFO] - You have the access to AWS resources. - (__init__.py:67)
[2020-11-05 09:33:17,463] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:153)
[2020-11-05 09:33:17,466] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:216)
[2020-11-05 09:33:17,466] [    INFO] - Setting environment variables from config. - (admin.py:105)
.
.
.
[2020-11-05 09:36:58,671] [    INFO] - id: bd2610ade6e0 [==========================================>        ]  741.1MB/870.7MB - (impl.py:181)
[2020-11-05 09:37:02,380] [    INFO] - id: 50dfc84e9311 [==========================================>        ]  741.1MB/870.7MB - (impl.py:181)
[2020-11-05 09:37:06,659] [    INFO] - id: bd2610ade6e0 [=============================================>     ]  792.4MB/870.7MB - (impl.py:181)
[2020-11-05 09:37:09,600] [    INFO] - id: 50dfc84e9311 [=============================================>     ]  792.4MB/870.7MB - (impl.py:181)
[2020-11-05 09:37:17,837] [    INFO] - id: bd2610ade6e0 [================================================>  ]  844.9MB/870.7MB - (impl.py:181)
[2020-11-05 09:37:19,888] [    INFO] - id: 50dfc84e9311 [================================================>  ]  844.9MB/870.7MB - (impl.py:181)
[2020-11-05 09:37:29,755] [    INFO] - id: bd2610ade6e0 [==================================================>]  897.4MB - (impl.py:181)
[2020-11-05 09:37:31,653] [    INFO] - id: 50dfc84e9311 [==================================================>]  897.4MB - (impl.py:181)
[2020-11-05 09:37:39,688] [    INFO] - id: bd2610ade6e0 status: Pushed - (impl.py:172)
[2020-11-05 09:37:40,325] [    INFO] - id: 50dfc84e9311 status: Pushed - (impl.py:172)
```

Confirm that the Docker image has been uploaded to:

https://console.aws.amazon.com/ecr/repositories?region=us-east-1



Now that the Docker image is prepared, we will finally deploy the task on
AWS Fargate in the next tutorial.

