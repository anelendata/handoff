## Building, running, and pushing a Docker image

We will continue using 04_install project (exchange rates to CSV).
Instead of running the task on the host machine, let's run on Docker.



Let's build a Docker image.

Try running the following command. Enter y when prompted at the beginning.
The build may take 5~10 minutes.

```shell
> handoff container build -p 04_install
```
```shell

[2021-04-07 05:20:16,893] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
Build xxxxxxxxcsv:0.1 (y/N)? [2021-04-07 05:20:18,011] [    INFO] - Building xxxxxxxxcsv:0.1 - (impl.py:78)
[2021-04-07 05:20:18,012] [    INFO] - Current working directory: /home/ubuntu/project/handoff/handoff/services/container/docker - (impl.py:82)
[2021-04-07 05:20:18,012] [    INFO] - Looking for handoff source at /home/ubuntu/project/handoff/handoff/services/container/docker/../../../../ - (impl.py:84)
[2021-04-07 05:20:18,012] [    INFO] - Found handoff. Copying to the build directory - (impl.py:86)
Step 1/27 : FROM ubuntu:18.04 ---> 2ca708c1c9cc
Step 2/27 : MAINTAINER Daigo Tanaka <daigo.tanaka@gmail.com> ---> Using cache
 ---> 22aac56eb931
Step 3/27 : ENV DEBIAN_FRONTEND noninteractive ---> Using cache
 ---> 71aaeed475a5
.
.
.
Step 24/27 : RUN rm -fr workspace/artifacts ---> Running in 54e949c94413
 ---> d07e108da9a5
Step 25/27 : RUN chmod a+x /usr/local/bin/* ---> Running in 24c417f453f5
 ---> e12769b29295
Step 26/27 : ENTRYPOINT [ "/tini", "--" ] ---> Running in dc421a4f8bf0
 ---> 4e5339f471e2
Step 27/27 : CMD handoff ${COMMAND:-run} -w workspace -a -v $(eval echo ${__VARS:-"dummy=1"}) -s ${HO_STAGE:-"dev"} -a ---> Running in 26163c1538b3
 ---> 3773a14733dc
Successfully built 3773a14733dc
Successfully tagged xxxxxxxxcsv:0.1
```

Now let's run the code in the Docker container.

```shell
> handoff container run -p 04_install --envs __VARS='start_date=$(date -I -d "-7 day")'
```
```shell

[2021-04-07 05:21:19,620] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
[2021-04-07 05:21:20,241] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
Run xxxxxxxxcsv:0.1 (y/N)? [2021-04-07 05:21:21,994] [    INFO] - Found credentials in environment variables. - (credentials.py:1100)
[2021-04-07 05:21:22,381] [    INFO] - Found credentials in environment variables. - (credentials.py:1100)
[2021-04-07 05:21:22,838] [    INFO] - Found credentials in environment variables. - (credentials.py:1100)
[2021-04-07 05:21:23,340] [    INFO] - GET s3://xxxxxxxx/dev-exchange-rates-to-csv/files - (s3.py:66)
[2021-04-07 05:21:23,885] [    INFO] - GET s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last - (s3.py:66)
[2021-04-07 05:21:24,476] [    INFO] - Job started at 2021-04-07 05:21:24.476288 - (__init__.py:178)
[2021-04-07 05:21:24,476] [    INFO] - Running pipeline fetch_exchange_rates - (operators.py:194)
[2021-04-07 05:21:24,499] [    INFO] - Checking return code of pid 29 - (operators.py:263)
```

Confirm the run by checking the logs. Also check the artifacts on S3:
```shell


    xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last


```

directory.



Now that we know the Docker container runs fine, let's push it to
AWS Elastic Container Registry. This may take a few minutes.

```shell
> handoff container push -p 04_install
```
```shell

[2021-04-07 05:21:30,325] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
[2021-04-07 05:21:30,881] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1223)
Repository xxxxxxxxcsv does not exist. Create (y/N)?[2021-04-07 05:21:31,275] [    INFO] - Creating repository xxxxxxxxcsv - (__init__.py:94)
Push xxxxxxxxcsv:0.1 to xxxxxxxxxxxx.dkr.ecr.us-east-1.amazonaws.com (y/N)? id: 28f470206a3c status: Preparing
id: 673e03fa99d2 status: Preparing
id: d3ca5be6fad9 status: Preparing
id: 2b6cda83ca7f status: Preparing
id: 1eee0a143c43 status: Preparing
id: cc51cd368615 status: Preparing
id: 19c09b0ffae8 status: Preparing
.
.
.
id: b61bcef8f912 [===========================>                       ]  265.6MB/480.2MB
id: b61bcef8f912 [==============================>                    ]  293.4MB/480.2MB
id: a1aa3da2a80a status: Pushed
id: b61bcef8f912 [=================================>                 ]  323.1MB/480.2MB
id: b61bcef8f912 [====================================>              ]  351.2MB/480.2MB
id: b61bcef8f912 [=======================================>           ]  379.9MB/480.2MB
id: b61bcef8f912 [==========================================>        ]  409.2MB/480.2MB
id: b61bcef8f912 [=============================================>     ]  437.8MB/480.2MB
id: b61bcef8f912 [================================================>  ]  466.9MB/480.2MB
id: b61bcef8f912 status: Pushed
```

Confirm that the Docker image has been uploaded to:

https://console.aws.amazon.com/ecr/repositories?region=us-east-1



Now that the Docker image is prepared, we will finally deploy the task on
AWS Fargate in the next tutorial.

