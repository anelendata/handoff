from pathlib import Path


EXPECTED_ERROR_FILTER_PATTERN = (
    '?"ended with exit code 1" ?"exited with code 1" ?"CRITICAL" '
    '?"Traceback (most recent call last)"'
)

TASK_TEMPLATE_PATHS = [
    Path("handoff/services/cloud/aws/cloudformation_templates/task.yml"),
    Path("handoff/services/cloud/aws/kaniko_config/task.yml"),
]


def test_error_metric_filter_pattern_is_tightened():
    for path in TASK_TEMPLATE_PATHS:
        template = path.read_text()

        assert f"FilterPattern: '{EXPECTED_ERROR_FILTER_PATTERN}'" in template
        assert "?ERROR ?Error ?error ?CRITICAL ?Exception" not in template


def test_task_templates_do_not_contain_account_specific_arns():
    for path in TASK_TEMPLATE_PATHS:
        template = path.read_text()

        assert "arn:aws:iam::" not in template
