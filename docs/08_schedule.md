## Scheduling a task on Fargate

In this section, we will learn how to schedule a task so it runs automatically.


To schedule a task, use schedule command with parameters target_id and
cron in [CRON format](https://en.wikipedia.org/wiki/Cron).

At the bottom of project.yml of 04_install project, there is a schedule section
which defines both:


```shell
> cat 04_install/project.yml
```

```shell
version: 0.3
description: Fetch foreign exchange rates

installs:
- venv: tap
  command: pip install tap-exchangeratesapi
- venv: target
  command: pip install target-csv

vars:
- key: base_currency
  value: USD

tasks:
- name: fetch_exchange_rates
  description: Fetch exchange rates
  pipeline:
  - command: tap-exchangeratesapi
    args: --config files/tap-config.json
    venv: tap
  - command: python
    args: files/stats_collector.py
    venv: tap
  - command: target-csv
    args: --config files/target-config.json
    venv: target

deploy:
  cloud_provider: aws
  cloud_platform: fargate
  resource_group: handoff-etl
  container_image: xxxxxxxxv
  task: exchange-rates-to-csv

schedules:
- target_id: 1
  cron: "0 0 * * ? *"
  envs:
  - key: __VARS
    value: 'start_date=$(date -I -d "-7 day")'

```


Also note that __VARS is defined in the section instead of giving at the command line.

With the schedule section presnt, you can simply schedule the task by running:

```shell
handoff cloud schedule create -p 04_install
```

Alternatively, we can pass those values to handoff with `--vars` (`-v` for short) option:


```shell
> handoff cloud schedule create -p 04_install -v target_id=1 cron='24 22 * * ? *' --envs __VARS='start_date=2020-12-21'
```
```shell

[2020-12-28 22:19:19,499] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:19:20,476] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:19:20,862] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:19:21,243] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
Check the status at https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/dev-handoff-etl-resources/scheduledTasks
- FailedEntries: []
  FailedEntryCount: 0
  ResponseMetadata:
    HTTPHeaders:
      content-length: '41'
```


At the end of the log, you should see a line like:

```shell

    Check the progress at Check the status at https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/...

```


Grab the entire link and open in a browser (you need to login in to AWS) to see
it's scheduled.



We confirmed that the task run in the same way as local execution.
Now let's go to the next module to learn how to schedule the task
so it runs periodically.

