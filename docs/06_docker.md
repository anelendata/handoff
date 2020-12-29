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

[2020-12-28 22:06:14,443] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
Build xxxxxxxxv:0.1 (y/N)? [2020-12-28 22:06:15,478] [    INFO] - Building xxxxxxxxv:0.1 - (impl.py:78)
[2020-12-28 22:06:15,480] [    INFO] - Current working directory: /home/ubuntu/project/handoff/handoff/services/container/docker - (impl.py:82)
[2020-12-28 22:06:15,480] [    INFO] - Looking for handoff source at /home/ubuntu/project/handoff/handoff/services/container/docker/../../../../ - (impl.py:84)
[2020-12-28 22:06:15,481] [    INFO] - Found handoff. Copying to the build directory - (impl.py:86)
Step 1/27 : FROM ubuntu:18.04 ---> 2ca708c1c9cc
Step 2/27 : MAINTAINER Daigo Tanaka <daigo.tanaka@gmail.com> ---> Using cache
 ---> 22aac56eb931
Step 3/27 : ENV DEBIAN_FRONTEND noninteractive ---> Using cache
 ---> 71aaeed475a5
.
.
.
Step 24/27 : RUN rm -fr workspace/artifacts ---> Running in a5ef8785b32f
 ---> 593b92ba4329
Step 25/27 : RUN chmod a+x /usr/local/bin/* ---> Running in 00b172bb03f9
 ---> 80e84ccc0ac5
Step 26/27 : ENTRYPOINT [ "/tini", "--" ] ---> Running in 95be61a89095
 ---> 0c94c0e4cdc8
Step 27/27 : CMD handoff ${COMMAND:-run} -w workspace -a -v $(eval echo ${__VARS:-"dummy=1"}) -s ${HO_STAGE:-"test"} -a ---> Running in 7ed37e348260
 ---> b5bbffac014c
Successfully built b5bbffac014c
Successfully tagged xxxxxxxxv:0.1
```

Now let's run the code in the Docker container.

```shell
> handoff container run -p 04_install --envs __VARS='$(date -I -d "-7 day")'
```
```shell

[2020-12-28 22:06:58,810] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:06:59,418] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
Run xxxxxxxxv:0.1 (y/N)? [2020-12-28 22:07:01,003] [    INFO] - Found credentials in environment variables. - (credentials.py:1094)
[2020-12-28 22:07:01,384] [    INFO] - Found credentials in environment variables. - (credentials.py:1094)
[2020-12-28 22:07:01,851] [    INFO] - Found credentials in environment variables. - (credentials.py:1094)
[2020-12-28 22:07:02,319] [    INFO] - GET s3://xxxxxxxx/dev-exchange-rates-to-csv/files - (s3.py:66)
[2020-12-28 22:07:02,846] [    INFO] - GET s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last - (s3.py:66)
[2020-12-28 22:07:03,415] [    INFO] - Job started at 2020-12-28 22:07:03.415462 - (__init__.py:178)
[2020-12-28 22:07:03,415] [    INFO] - Running pipeline fetch_exchange_rates - (operators.py:193)
[2020-12-28 22:07:03,434] [    INFO] - Checking return code of pid 28 - (operators.py:262)
```

Note: Mac OS local run should also use the date command with -I option because
the command runs inside the container.

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

[2020-12-28 22:07:08,485] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:07:09,020] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
Repository xxxxxxxxv does not exist. Create (y/N)?[2020-12-28 22:07:09,410] [    INFO] - Creating repository xxxxxxxxv - (__init__.py:94)
Push xxxxxxxxv:0.1 to xxxxxxxxxxxx.dkr.ecr.us-east-1.amazonaws.com (y/N)? id: e36ccb76f941 status: Preparing
id: b5bfa90522bd status: Preparing
id: 5cdca8bd36d3 status: Preparing
id: 6c96d483f769 status: Preparing
id: 476b387d4f0a status: Preparing
id: 0cc9d5b47311 status: Preparing
id: b779c87a670a status: Preparing
.
.
.
id: 6734fdd29c24 [========================>                          ]  265.8MB/540.8MB
id: 6734fdd29c24 [===========================>                       ]    298MB/540.8MB
id: 6734fdd29c24 [==============================>                    ]  331.4MB/540.8MB
id: 6734fdd29c24 [=================================>                 ]  362.9MB/540.8MB
id: 6734fdd29c24 [====================================>              ]  394.8MB/540.8MB
id: 6734fdd29c24 [=======================================>           ]    429MB/540.8MB
id: 6734fdd29c24 [==========================================>        ]  461.4MB/540.8MB
id: 6734fdd29c24 [=============================================>     ]  493.5MB/540.8MB
id: 6734fdd29c24 [================================================>  ]  526.1MB/540.8MB
id: 6734fdd29c24 status: Pushed
```

Confirm that the Docker image has been uploaded to:

https://console.aws.amazon.com/ecr/repositories?region=us-east-1



Now that the Docker image is prepared, we will finally deploy the task on
AWS Fargate in the next tutorial.

