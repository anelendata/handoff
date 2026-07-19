from pathlib import Path

from test_aws_task_templates import CloudFormationLoader, load_template


ALARM_TEMPLATE_PATH = Path(
    "handoff/services/cloud/aws/cloudformation_templates/alarm.yml")


def test_alarm_template_has_no_undefined_condition():
    template = load_template(ALARM_TEMPLATE_PATH)
    conditions = template.get("Conditions", {})

    for resource in template["Resources"].values():
        condition = resource.get("Condition")
        assert condition is None or condition in conditions, (
            f"Resource references undefined condition {condition!r}")


def test_alarm_template_execution_alarms_target_step_functions_metrics():
    template = load_template(ALARM_TEMPLATE_PATH)
    resources = template["Resources"]

    failed = resources["ExecutionsFailedAlarm"]["Properties"]
    timed_out = resources["ExecutionsTimeoutAlarm"]["Properties"]

    for alarm in (failed, timed_out):
        assert alarm["Namespace"] == "AWS/States"
        assert alarm["AlarmActions"] == ["AlarmSNSTopic"]

    assert failed["MetricName"] == "ExecutionsFailed"
    assert timed_out["MetricName"] == "ExecutionsTimedOut"


def test_alarm_template_arn_and_email_params_accept_realistic_values():
    template = load_template(ALARM_TEMPLATE_PATH)
    params = template["Parameters"]

    # These previously carried a copy-pasted MaxLength: 27 /
    # AllowedPattern: "[a-zA-Z][a-zA-Z0-9_-]*" that rejected any real ARN
    # or email address.
    for key in ("StateMachineArn", "AlarmEmail"):
        assert "AllowedPattern" not in params[key]
        assert "MaxLength" not in params[key]
