# Advanced topics

## Specifying relative time as run-time variable

You can use [GNU date command](https://www.gnu.org/software/coreutils/manual/html_node/Examples-of-date.html).

Example:

```
tasks:
- name: show dates
  description: 
  - command: echo
    args: "yesterday / today: {{ yesterday }} / {{ tooday }}"
```

For local runs, run handoff with date command passing via --vars (-v) option:

```
handoff run local -p project_dir -v yesterday=$(date -Iseconds -d "00:00 yesterday") today=$(date -Iseconds -d "00:00 today")
```

You can delay the evaluation of date command in container run and cloud run
commands by passing `__VARS` environment variable via `-e` option:

```
handoff container run -p project_dir -e __VARS='today=$(date -I) tomorrow=$(date -I -d "1 day")'
handoff cloud run -p project_dir -e __VARS='today=$(date -I) tomorrow=$(date -I -d "1 day")'
```

Make sure to **use single quotes** when defining `__VARS` variable so it won't be
evaluated when container/cloud run command runs. You want the command string to be passed
'as is' and then evaluated when the **container** executes the `handoff run` command.

`__VARS` is a sepecial environment variable inside the container as defined in
Dockerfile, the container evaluates `__VARS` and pass to handoff via -v option:

```
handoff run -w workspace_dir -v $(eval echo $__VARS)
```

In this way, the date command defined in `__VARS` is finally evaluated inside
the container.

For convenience, you can define the environment variable in schedule:

```
schedules:
- cron: '0 1 * * ? *'
  envs:
  - key: '__VARS'
    value: 'yesterday=$(date -Iseconds -d "00:00 yesterday") today=$(date -Iseconds -d "00:00 today")'
  target_id: '1'
```

Note:

- `handoff run local` may not be able to handle this correctly if
  your local machine does not implement GNU date (e.g. OSX).
  By default, `handoff container run` and `handoff cloud run` should be able
  to handle correctly as the Docker image is based on Ubuntu.

## Installing a Python package from a Github repository

You can put `https://github.com/<account>/<repository>/archive/<commit-hash>.tar.gz#egg=<command-name>`
format like this project of executing a pair of singer.io processes,
[tap-rest-api](https://github.com/anelendata/tap-rest-api) and
[target_gcs](https://github.com/anelendata/target_gcs):
```
commands:
  - command: tap-rest-api
    args: "file/rest_api_spec.json --config files/tap_config.json --schema_dir file/schema --catalog file/catalog/default.json --state artifacts/state --start_datetime '{start_at}' --end_datetime '{end_at}'"
    venv: proc_01
    installs:
      - "pip install tap-rest-api"
  - command: target_gcs
    args: "--config files/target_config.json"
    venv: proc_02
    installs:
      - "pip install install --no-cache-dir https://github.com/anelendata/target_gcs/archive/17e70bced723fe202425a61199e6e1180b6fada7.tar.gz#egg=target_gcs"
envs:
  - key: "GOOGLE_APPLICATION_CREDENTIALS"
    value: "files/google_client_secret.json"
```

## Custom Dockerfile

One may need to deploy a Docker image with special root installations
(e.g. JDBC driver). This is beyond the capability of workspace install command.

```
container:
  docker_file: ./my_Dockerfile
  files_dir: ./my_files
```

In the above example, handoff will use `./my_Dockerfile` instead of the
default Dockerfile. It also copies `./my_files` directory to the temporary
directory where handoff start a docker command.

To get started, it is recommended to copy the
[default Dockerfile](https://github.com/anelendata/handoff/blob/master/handoff/services/container/docker/Dockerfile)
and modify it.

Then in your version of Dockerfile, you should be able to add install extra
software or copy the files like:

```
RUN apt-get update -yqq && apt-get install -yqq jq
COPY ./my_files/hello.txt /app/
```

## Monitorig the process with Grafana

<img src="https://github.com/anelendata/handoff/raw/master/assets/grafana.png"/>

When deployed to the cloud service, handoff creates logging resources.
The logs are easily parsed and visualized with the dashboarding tools like
[Grafana](https://grafana.com/).

Here are some resources to get started.

### Grafana for AWS CloudWatch logs

handoff's default cloud provider is AWS. In this case, CloudWatch logs can
be visualized with Grafana.

- [Download and instll Grafana](https://grafana.com/grafana/download)
- [Setting up Grafana for AWS CloudWatch](https://grafana.com/docs/grafana/latest/features/datasources/cloudwatch/)

Tips:

- When setting AWS CloudWatch data source on Grafana dashboard, make sure there
  is a .aws/credentials file accessible by the user running Grafana. When running
  on Ubuntu and authenticating AWS with a crendential file, you may need to keep
  a copy at `/usr/share/grafana/.aws/credentials`.
- handoff creates a log group per task with the following naming convention: `<resource-name>-<task-name>`
- When adding a query on Grafana Panel, set Query Mode to "CloudWatch Logs" and enter an
  [Insigh query](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html).
  For example, here is a query to extract Singer's metrics:

```
fields @timestamp, @message
| filter @message like /METRIC/
| parse "* *: {\"type\": \"*\", \"metric\": \"*\", \"value\": *, *}" as log_level, log_type, singer_type, singer_metric, singer_value, rest
| filter singer_type = "counter"
| stats max(singer_value) as rows_loaded by bin(4h)
```

- You can also count the errors and send an alert. Our suggestion for a beginner
  is to create [a free PagerDuty account](https://www.pagerduty.com/) and create
  a new service from `https://<your-domain>.pagerduty.com/service-directory`.
  Select AWS CloudWatch as Integration Type and obtain the integration key to
  use it on [Grafana alert setup](https://grafana.com/docs/grafana/latest/alerting/alerts-overview/).
- Here is an example query for filtering errors from the logs and count:

```
fields @timestamp, @log, @message
| filter @message like /(CRITICAL|Error|error)/
| count() as errors by bin(1h)
```

## Alarming on task completion gaps

The default task template's `ErrorLogMetricFilter` is intentionally narrow: it
matches specific application-level failure phrases (`ended with exit code 1`,
`CRITICAL`, a Python traceback, etc.) so that unrelated log noise doesn't trip
false alarms. The tradeoff is that it can only catch failures the task's own
process got far enough to *log*. It cannot see:

- task-startup failures before any application log line is emitted (e.g. the
  container image can't be pulled, or the task can't be scheduled)
- OOM or signal-based exits that never reach a matching log line
- a task that hangs and never exits at all

For a scheduled task, ECS Fargate execution is wrapped in an AWS Step
Functions state machine (one per scheduled `target_id`), and Step Functions
already emits `AWS/States` `ExecutionsFailed` and `ExecutionsTimedOut`
metrics, dimensioned by `StateMachineArn`, that reflect the outcome of the
*whole* execution regardless of whether the task process itself ever started
or logged anything. These cover all three gaps above, and since they only
fire once an execution has truly finished failing or timed out, a task whose
container pull is retried and eventually succeeds within the same execution
will not trip the alarm — you won't get paged for something that already
self-healed.

To use them, find the state machine ARN for a scheduled task with:

```
handoff cloud schedule list -p <project_dir> -s <stage> -v full=True
```

Look for `targets[0].Arn` in the output — that's the `StateMachineArn`.

The repo ships a ready-to-deploy, opt-in alarm stack at
[`handoff/services/cloud/aws/cloudformation_templates/alarm.yml`](https://github.com/anelendata/handoff/blob/master/handoff/services/cloud/aws/cloudformation_templates/alarm.yml)
(also included in the installed package under the same relative path). It
creates an SNS topic with an email subscription plus the two alarms. Deploy
it per task with the plain AWS CLI, since it's independent of handoff's own
`cloud resources`/`cloud task` stacks:

```
aws cloudformation create-stack \
  --stack-name <resource-group>-<task-name>-completion-alarm \
  --template-body file://alarm.yml \
  --parameters \
      ParameterKey=ResourceGroup,ParameterValue=<resource-group> \
      ParameterKey=TaskName,ParameterValue=<task-name> \
      ParameterKey=StateMachineArn,ParameterValue=<state-machine-arn-from-above> \
      ParameterKey=AlarmEmail,ParameterValue=<your-email>
```

If you also want to catch a task that starts but *stalls* mid-run with no
`global_timeout` set (so `ExecutionsTimedOut` never fires), you can build a
secondary alarm on the existing `<stack>-started` / `<stack>-ended` metric
filters using CloudWatch metric math (`started_sum - ended_sum`, evaluated
over a period comfortably longer than the task's expected runtime). Keep in
mind this only complements the alarm above — since `<stack>-started` is only
incremented once the task process is already running, it cannot see any of
the three startup-time gaps this section opened with.
