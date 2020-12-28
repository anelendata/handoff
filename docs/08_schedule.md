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
.
.
.
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
> handoff cloud schedule create -p 04_install -v target_id=1 cron='25 08 * * ? *' --envs __VARS='start_date=2020-12-21'
```
```shell

Check the status at https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/dev-handoff-etl-resources/scheduledTasks
- FailedEntries: []
  FailedEntryCount: 0
  ResponseMetadata:
    HTTPHeaders:
      content-length: '41'
      content-type: application/x-amz-json-1.1
      date: Mon, 28 Dec 2020 08:20:35 GMT
      x-amzn-requestid: xxxxxxxxf19f154f
    HTTPStatusCode: 200
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

