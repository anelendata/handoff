import os, sys
import yaml
from importlib import import_module as _import_module
from typing import Dict
from types import ModuleType

from handoff.core import admin
from handoff.utils import get_logger as _get_logger
from handoff.config import (BUCKET, RESOURCE_GROUP, TASK, CONTAINER_IMAGE,
                            IMAGE_VERSION, CLOUD_PROVIDER, CLOUD_PLATFORM,
                            STAGE, get_state)

LOGGER = _get_logger(__name__)


PLATFORM_MODULE = None


def _get_platform(
    provider_name: str = None,
    platform_name: str = None,
    stdout: bool = False,
    cloud_profile: str = None,
    **kwargs) -> ModuleType:
    state = get_state()
    if not provider_name:
        provider_name = state.get(CLOUD_PROVIDER)
    if not platform_name:
        platform_name = state.get(CLOUD_PLATFORM)
    global PLATFORM_MODULE
    if not PLATFORM_MODULE:
        if not provider_name or not platform_name:
            raise Exception("You need to set provider_name and platform_name")
        # TODO: use platform_name
        PLATFORM_MODULE = _import_module("handoff.services.cloud."
                                         + provider_name)
        response = PLATFORM_MODULE.login(cloud_profile)
        if stdout:
            sys.stdout.write(response)
    return PLATFORM_MODULE


def _assume_role(
    project_dir: str,
    workspace_dir: str,
    data: Dict = {},
    **kwargs) -> None:
    state = get_state()
    state.validate_env([RESOURCE_GROUP])
    platform = _get_platform()
    role_arn = data.get("role_arn")
    target_account_id = data.get("target_account_id")
    external_id = data.get("external_id")
    platform.assume_role(role_arn=role_arn,
                         target_account_id=target_account_id,
                         external_id=external_id)


def _get_platform_auth_env(
    project_dir: str,
    workspace_dir: str,
    data: Dict = {},
    **kwargs) -> Dict:
    platform = _get_platform()
    return platform.get_platform_auth_env(data)


def role_create(
    project_dir: str,
    workspace_dir: str,
    data: Dict = {},
    **kwargs) -> None:
    """`handoff cloud role create -p <project_directory> -d external_id=<id> grantee_account_id=<grantee_id>`
    Create the role with deployment privilege.
    """
    state = get_state()
    platform = _get_platform()
    account_id = platform.login()
    state.validate_env()
    if not data.get("grantee_account_id"):
        LOGGER.warn("grantee_account_id was not set." +
                    "The grantee will be set for the same account. To set: ")
        LOGGER.warn("-d grantee_account_id=xxxx")
    if not data.get("external_id"):
        raise ValueError("external_id must be set. Do as:\n    " +
                         "handoff cloud create_role -p <project-dir> " +
                         "-d external_id=yyyy")

    platform.create_role(
        grantee_account_id=data.get("grantee_account_id", account_id),
        external_id=data.get("external_id")
    )


def role_update(
    project_dir: str,
    workspace_dir: str,
    data: Dict = {},
    **kwargs) -> None:
    """`handoff cloud role update -p <project_directory> -d external_id=<id> grantee_account_id=<grantee_id>`
    Update the role privilege information.
    """
    state = get_state()
    platform = _get_platform()
    account_id = platform.login()
    state.validate_env()
    if not data.get("grantee_account_id"):
        LOGGER.warn("grantee_account_id was not set." +
                    "The grantee will be set for the same account. To set: ")
        LOGGER.warn("-d grantee_account_id=xxxx")
    if not data.get("external_id"):
        raise ValueError("external_id must be set. Do as:\n    " +
                         "handoff cloud create_role -p <project-dir> " +
                         "-d external_id=yyyy")

    platform.update_role(
        grantee_account_id=data.get("grantee_account_id", account_id),
        external_id=data.get("external_id")
    )


def role_delete(
    project_dir: str,
    workspace_dir: str,
    data: Dict = {},
    **kwargs) -> None:
    """`handoff cloud role delete -p <project_directory> -d grantee_account_id=<grantee_id>`
    Delete the role.
    """
    state = get_state()
    platform = _get_platform()
    account_id = platform.login()
    state.validate_env()
    if not data.get("grantee_account_id"):
        LOGGER.warn("grantee_account_id was not set." +
                    "The grantee will be set for the same account. To set: ")
        LOGGER.warn("-d grantee_account_id=xxxx")
    if not data.get("external_id"):
        raise ValueError("external_id must be set. Do as:\n    " +
                         "handoff cloud create_role -p <project-dir> " +
                         "-d external_id=yyyy")

    platform.delete_role(
        grantee_account_id=data.get("grantee_account_id", account_id),
        external_id=data.get("external_id")
    )


def bucket_create(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff cloud bucket create -p <project_directory>`
    Create remote storage bucket. Bucket is attached to the resource group.
    """
    state = get_state()
    platform = _get_platform()
    state.validate_env()
    platform.create_bucket()


def bucket_update(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff cloud bucket update -p <project_directory>`
    Update remote storage bucket info
    """
    state = get_state()
    platform = _get_platform()
    state.validate_env()
    platform.update_bucket()


def bucket_delete(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff cloud bucket delete -p <project_directory>`
    Delete remote storage bucket.
    """
    state = get_state()
    platform = _get_platform()
    state.validate_env()
    platform.delete_bucket()


def resources_create(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff cloud resources create -p <project_directory>`
    Create resources necessary for task execution.
    The resources are shared among the tasks under the same resource group.

    AWS:
    - Please refer to the
      [CloudFormation template](https://github.com/anelendata/handoff/blob/master/handoff/services/cloud/aws/cloudformation_templates/resources.yml) for the resources created with this command.
    """
    state = get_state()
    platform = _get_platform()
    state.validate_env()
    platform.create_resources()


def resources_update(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff cloud resources update -p <project_directory>`
    Update the resources

    The resources are shared among the tasks under the same resource group.
    """
    state = get_state()
    platform = _get_platform()
    state.validate_env()
    platform.update_resources()


def resources_delete(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff cloud resources delete -p <project_directory>`
    Delete the resources

    The resources are shared among the tasks under the same resource group.
    """
    state = get_state()
    platform = _get_platform()
    state.validate_env()
    platform.delete_resources()


def task_create(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff cloud task create -p <project_directory>`
    Create the task
    """
    state = get_state()
    platform = _get_platform()
    state.validate_env([IMAGE_VERSION])
    platform.create_task()


def task_update(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff cloud task update -p <project_directory>`
    Update the task
    """
    state = get_state()
    platform = _get_platform()
    state.validate_env([IMAGE_VERSION])
    platform.update_task()


def task_delete(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff cloud task delete -p <project_directory>`
    Delete the task
    """
    state = get_state()
    platform = _get_platform()
    state.validate_env()
    platform.delete_task()


def run(
    project_dir: str,
    workspace_dir: str,
    envs: Dict = {},
    extras: str = None,
    **kwargs) -> None:
    """`handoff cloud run -d resource_group=<resource_group_name> task=<task_name> -e DATA='key1=val1 key2=val2...'`
    Run a task once in the platform

    If the environment variable DATA is specified via -e option, it will be
    used as:
    `handoff run -d $(eval echo $DATA)`
    """
    state = get_state()
    platform = _get_platform()
    state.validate_env()

    extras_obj = None
    if extras:
        with open(extras, "r") as f:
            extras_obj = yaml.load(f)

    envs[STAGE] = state[STAGE]
    platform.run_task(env=envs, extras=extras_obj)


def schedule(
    project_dir: str,
    workspace_dir: str,
    envs: Dict = {},
    data: Dict = {},
    extras: str = None,
    **kwargs) -> None:
    """`handoff cloud schedule -d target_id=<target_id> cron="<cron_format>" -e DATA='key1=val1 key2=val2...'`
    Schedule a task named <target_id> at the recurring scheduled specified
    as <cron_format>. An example of cron-format string is "10 01 * * ? *"
    for every day at 01:10 (1:10AM)

    If the environment variable DATA is specified via -e option, it will be
    used as:
    `handoff run -d $(eval echo $DATA)`
    """
    state = get_state()
    platform = _get_platform()
    config = admin._config_get_local(project_dir, workspace_dir)
    state.validate_env()
    schedules = config.get("schedules")
    if not schedules:
        if not data.get("target_id") or not data.get("cron"):
            raise Exception("Forgot to set '-d target_id=<ID> cron=<CRON>' ?")
        target_id = str(data["target_id"])
        cronexp = "cron(" + data["cron"] + ")"
        extras_obj = None
        if extras:
            with open(extras, "r") as f:
                extras_obj = yaml.load(f)
        schedules = [{"target_id": target_id, "cron": cronexp,
                      "extras_obj": extras_obj}]
    envs[STAGE] = state[STAGE]

    for s in schedules:
        e = dict()
        e.update(envs)
        for e1 in s.get("envs", list()):
            e[e1["key"]] = e1["value"]
        platform.schedule_task(
            s["target_id"], "cron(" + s["cron"] + ")",
            env=e,
            extras=s.get("extras_obj"))


def unschedule(
    project_dir: str,
    workspace_dir: str,
    data: Dict = {},
    **kwargs) -> None:
    """`handoff cloud unschedule -d target_id=<target_id>`
    Unschedule a task named <target_id>
    """
    state = get_state()
    platform = _get_platform()
    state.validate_env()
    target_id = str(data["target_id"])
    platform.unschedule_task(target_id)


def schedule_list(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff cloud schedule list`
    List the scheduled tasks
    """
    state = get_state()
    platform = _get_platform()
    state.validate_env()
    platform.list_schedules()


def logs(
    project_dir: str,
    workspace_dir: str,
    data: Dict = {},
    **kwargs) -> None:
    """`handoff cloud logs -d start_time=<start_time> end_time=<end_time> follow=<True/False>`
    Show logs
    Use --data (-d) option to:
    - start_time: ISO 8086 formatted date time to indicate the start time
    - end_time
    - follow: If set, it waits for more logs until interrupted by ctrl-c
    """
    state = get_state()
    platform = _get_platform()
    state.validate_env()
    last_update = platform.print_logs(**data)

    print(last_update)
