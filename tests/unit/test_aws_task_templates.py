from pathlib import Path


TASK_TEMPLATES = [
    Path("handoff/services/cloud/aws/cloudformation_templates/task.yml"),
    Path("handoff/services/cloud/aws/kaniko_config/task.yml"),
]


def test_task_templates_do_not_embed_account_specific_arns():
    for template_path in TASK_TEMPLATES:
        template = template_path.read_text()

        assert "arn:aws:iam::" not in template
