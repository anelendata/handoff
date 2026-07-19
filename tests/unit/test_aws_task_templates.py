from pathlib import Path

import yaml


EXPECTED_ERROR_FILTER_PATTERN = (
    '?"ended with exit code 1" ?"exited with code 1" ?"CRITICAL" '
    '?"Traceback (most recent call last)"'
)

TASK_TEMPLATE_PATHS = [
    Path("handoff/services/cloud/aws/cloudformation_templates/task.yml"),
    Path("handoff/services/cloud/aws/kaniko_config/task.yml"),
]


class CloudFormationLoader(yaml.SafeLoader):
    pass


def construct_cloudformation_value(loader, _tag_suffix, node):
    if isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    return loader.construct_scalar(node)


CloudFormationLoader.add_multi_constructor("!", construct_cloudformation_value)


def load_template(path):
    return yaml.load(path.read_text(), Loader=CloudFormationLoader)


def test_error_metric_filter_pattern_is_tightened():
    for path in TASK_TEMPLATE_PATHS:
        template_text = path.read_text()
        template = load_template(path)
        filter_pattern = template["Resources"]["ErrorLogMetricFilter"]["Properties"][
            "FilterPattern"
        ]

        assert filter_pattern == EXPECTED_ERROR_FILTER_PATTERN
        assert "?ERROR ?Error ?error ?CRITICAL ?Exception" not in template_text


def test_task_templates_do_not_contain_account_specific_arns():
    for path in TASK_TEMPLATE_PATHS:
        template = path.read_text()

        assert "arn:aws:iam::" not in template


def test_timeout_log_metric_filter_is_present():
    for path in TASK_TEMPLATE_PATHS:
        template = load_template(path)
        resources = template["Resources"]
        metric_filter = resources["TimeoutLogMetricFilter"]

        assert metric_filter["Type"] == "AWS::Logs::MetricFilter"
        assert metric_filter["Properties"]["FilterPattern"] == "?WARNING Timeout"

        transformation = metric_filter["Properties"]["MetricTransformations"][0]
        assert transformation["MetricName"] == "${AWS::StackName}-timeout"

        # Existing started/ended/error filters must be untouched by this change.
        assert resources["ErrorLogMetricFilter"]["Properties"]["FilterPattern"] == (
            EXPECTED_ERROR_FILTER_PATTERN
        )
        assert (
            resources["StartedLogMetricFilter"]["Properties"]["FilterPattern"]
            == "?Job started at"
        )
        assert (
            resources["EndedLogMetricFilter"]["Properties"]["FilterPattern"]
            == "?Job ended at"
        )
