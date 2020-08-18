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
