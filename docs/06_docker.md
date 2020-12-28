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

Build xxxxxxxxv:0.1 (y/N)? Step 1/27 : FROM ubuntu:18.04 ---> 2ca708c1c9cc
Step 2/27 : MAINTAINER Daigo Tanaka <daigo.tanaka@gmail.com> ---> Using cache
 ---> 22aac56eb931
Step 3/27 : ENV DEBIAN_FRONTEND noninteractive ---> Using cache
 ---> 71aaeed475a5
Step 4/27 : ENV LANGUAGE en_US.UTF-8 ---> Using cache
 ---> 69bb386693c5
Step 5/27 : ENV LANG en_US.UTF-8 ---> Using cache
 ---> 34ba01929880
Step 6/27 : ENV LC_ALL en_US.UTF-8 ---> Using cache
.
.
.
Step 24/27 : RUN rm -fr workspace/artifacts ---> Running in b7fc9c19c551
 ---> 5752a039c2ad
Step 25/27 : RUN chmod a+x /usr/local/bin/* ---> Running in c1ba2c0f286c
 ---> 5b0c684931c1
Step 26/27 : ENTRYPOINT [ "/tini", "--" ] ---> Running in a4db14151cc6
 ---> cbffe1cb9a39
Step 27/27 : CMD handoff ${COMMAND:-run} -w workspace -a -v $(eval echo ${__VARS:-"dummy=1"}) -s ${HO_STAGE:-"test"} -a ---> Running in f05617a9a273
 ---> d6ea7b42ff6a
Successfully built d6ea7b42ff6a
Successfully tagged xxxxxxxxv:0.1
```

Now let's run the code in the Docker container.

```shell
> handoff container run -p 04_install --envs __VARS='start_date=2020-12-21'
```
```shell

Run xxxxxxxxv:0.1 (y/N)? [2020-12-28 08:08:08,001] [    INFO] - GET s3://xxxxxxxx/dev-exchange-rates-to-csv/files - (s3.py:66)
[2020-12-28 08:08:08,525] [    INFO] - GET s3://xxxxxxxx/dev-exchange-rates-to-csv/artifacts/last - (s3.py:66)
Running run in workspace directory
Job started at 2020-12-28 08:08:09.039015
[2020-12-28 08:08:09,039] [    INFO] - Running pipeline fetch_exchange_rates - (operators.py:193)
[2020-12-28 08:08:09,058] [    INFO] - Checking return code of pid 28 - (operators.py:262)
[2020-12-28 08:08:09,741] [    INFO] - Checking return code of pid 29 - (operators.py:262)
[2020-12-28 08:08:09,749] [    INFO] - Checking return code of pid 31 - (operators.py:262)
Job ended at 2020-12-28 08:08:09.767180
Processed in 0:00:00.728165
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

Repository xxxxxxxxv does not exist. Create (y/N)?Push xxxxxxxxv:0.1 to xxxxxxxxxxxx.dkr.ecr.us-east-1.amazonaws.com (y/N)? id: 039bab61566e status: Preparing
id: xxxxxxxxxxxx status: Preparing
id: 35c5e5e7dba1 status: Preparing
id: af98175705a9 status: Preparing
id: 400bec3327f4 status: Preparing
id: f61f41e3c9ab status: Preparing
id: 6b1d9dbb36fb status: Preparing
id: 0046985a391c status: Preparing
id: xxxxxxxxxxxx status: Preparing
id: 0f2faf39efd9 status: Preparing
.
.
.
99.6MB/540.8MB
id: 6734fdd29c24 [==============================>                    ]  331.4MB/540.8MB
id: 6734fdd29c24 [=================================>                 ]  362.9MB/540.8MB
id: 6734fdd29c24 [====================================>              ]  395.3MB/540.8MB
id: 6734fdd29c24 [=======================================>           ]  429.5MB/540.8MB
id: 6734fdd29c24 [==========================================>        ]  459.8MB/540.8MB
id: 6734fdd29c24 [=============================================>     ]  492.9MB/540.8MB
id: 6734fdd29c24 [================================================>  ]  525.6MB/540.8MB
id: 6734fdd29c24 status: Pushed
```

Confirm that the Docker image has been uploaded to:

https://console.aws.amazon.com/ecr/repositories?region=us-east-1



Now that the Docker image is prepared, we will finally deploy the task on
AWS Fargate in the next tutorial.

