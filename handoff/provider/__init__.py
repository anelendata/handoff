import os
from importlib import import_module as _import_module
from handoff.core.utils import get_logger as _get_logger
from handoff.core.utils import env_check as _env_check
from handoff.config import (BUCKET, RESOURCE_GROUP, TASK, DOCKER_IMAGE,
                            IMAGE_VERSION)

platform = None
LOGGER = _get_logger(__name__)


def _log_stack_info(response):
    params = {"stack_id": response["StackId"], "region": os.environ["AWS_REGION"]}
    LOGGER.info(("Check the progress at https://console.aws.amazon.com/" +
                 "cloudformation/home?region={region}#/stacks/stackinfo" +
                 "?viewNested=true&hideStacks=false" +
                 "&stackId={stack_id}").format(**params))


def _log_stack_filter(stack_name):
    params = {"stack_name": stack_name, "region": os.environ["AWS_REGION"]}
    LOGGER.info(("Check the progress at https://console.aws.amazon.com/" +
                 "cloudformation/home?region={region}#/stacks/stackinfo" +
                 "?filteringText={stack_name}").format(**params))


def _log_task_run_filter(task_name, response):
    task_arn = response["tasks"][0]["taskArn"]
    task_id = task_arn[task_arn.find("task/") + len("task/"):]
    params = {"task":task_name,
              "region": os.environ["AWS_REGION"],
              "task_id": task_id}
    LOGGER.info(("Check the task at https://us-east-1.console.aws.amazon.com/ecs/home?region=" +
                 "{region}#/clusters/{task}/tasks/{task_id}").format(**params))


def _get_platform(provider):
    global platform
    if platform:
        return platform
    platform = _import_module("handoff.provider." + provider)
    return platform


def create_bucket(project_dir, workspace_dir, data, **kwargs):
    _env_check()
    global platform
    response = platform.create_bucket()
    LOGGER.info(response)
    _log_stack_info(response)


def update_bucket(project_dir, workspace_dir, data, **kwargs):
    _env_check()
    response = platform.update_bucket()
    LOGGER.info(response)
    _log_stack_info(response)


def delete_bucket(project_dir, workspace_dir, data, **kwargs):
    _env_check()
    response = platform.delete_bucket()
    LOGGER.info(response)
    _log_stack_filter(os.environ[BUCKET])


def create_resources(project_dir, workspace_dir, data, **kwargs):
    _env_check()
    global platform
    response = platform.create_resources()
    LOGGER.info(response)
    _log_stack_info(response)


def update_resources(project_dir, workspace_dir, data, **kwargs):
    _env_check()
    response = platform.update_resources()
    LOGGER.info(response)
    _log_stack_info(response)


def delete_resources(project_dir, workspace_dir, data, **kwargs):
    _env_check()
    response = platform.delete_resources()
    LOGGER.info(response)
    _log_stack_filter(os.environ[RESOURCE_GROUP])


def create_task(project_dir, workspace_dir, data, **kwargs):
    _env_check()
    global platform
    response = platform.create_task()
    LOGGER.info(response)
    _log_stack_info(response)


def update_task(project_dir, workspace_dir, data, **kwargs):
    _env_check()
    response = platform.update_task()
    LOGGER.info(response)
    _log_stack_info(response)


def delete_task(project_dir, workspace_dir, data, **kwargs):
    _env_check()
    response = platform.delete_task()
    LOGGER.info(response)
    _log_stack_filter(os.environ[TASK])


def run(project_dir, workspace_dir, data, **kwargs):
    _env_check()
    response = platform.run_task()
    LOGGER.info(response)
    _log_task_run_filter(os.environ[RESOURCE_GROUP] + "-" + os.environ[TASK],
                         response)
