import os, sys
import yaml
from importlib import import_module as _import_module
from typing import Dict
from types import ModuleType

from handoff.core import admin
from handoff.utils import get_logger as _get_logger
from handoff.config import (BUCKET, RESOURCE_GROUP, TASK, CONTAINER_IMAGE,
                            IMAGE_VERSION, CLOUD_PROVIDER, CLOUD_PLATFORM,
                            STAGE)
from handoff.config import get_state as _get_state

LOGGER = _get_logger(__name__)


PLATFORM_MODULE = None


def _get_platform(
    provider_name: str = None,
    platform_name: str = None,
    stdout: bool = False,
    cloud_profile: str = None,
    **kwargs) -> ModuleType:
    state = _get_state()
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
    vars: Dict = {},
    **kwargs) -> None:
    state = _get_state()
    state.validate_env([RESOURCE_GROUP])
    platform = _get_platform()
    role_arn = vars.get("role_arn")
    target_account_id = vars.get("target_account_id")
    external_id = vars.get("external_id")
    platform.assume_role(role_arn=role_arn,
                         target_account_id=target_account_id,
                         external_id=external_id)


def _get_platform_auth_env(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> Dict:
    platform = _get_platform()
    return platform.get_platform_auth_env(vars)


def role_create(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> None:
    """`handoff cloud role create -p <project_directory> -v external_id=<id> grantee_account_id=<grantee_id>`
    Create the role with deployment privilege.
    """
    state = _get_state()
    platform = _get_platform()
    account_id = platform.login()
    state.validate_env()
    if not vars.get("grantee_account_id"):
        LOGGER.warn("grantee_account_id was not set." +
                    "The grantee will be set for the same account. To set: ")
        LOGGER.warn("-v grantee_account_id=xxxx")
    if not vars.get("external_id"):
        raise ValueError("external_id must be set. Do as:\n    " +
                         "handoff cloud create_role -p <project-vir> " +
                         "-v external_id=yyyy")

    return platform.create_role(
        grantee_account_id=vars.get("grantee_account_id", account_id),
        external_id=vars.get("external_id")
    )


def role_update(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> None:
    """`handoff cloud role update -p <project_directory> -v external_id=<id> grantee_account_id=<grantee_id>`
    Update the role privilege information.
    """
    state = _get_state()
    platform = _get_platform()
    account_id = platform.login()
    state.validate_env()
    if not vars.get("grantee_account_id"):
        LOGGER.warn("grantee_account_id was not set." +
                    "The grantee will be set for the same account. To set: ")
        LOGGER.warn("-v grantee_account_id=xxxx")
    if not vars.get("external_id"):
        raise ValueError("external_id must be set. Do as:\n    " +
                         "handoff cloud create_role -p <project-vir> " +
                         "-v external_id=yyyy")

    return platform.update_role(
        grantee_account_id=vars.get("grantee_account_id", account_id),
        external_id=vars.get("external_id")
    )


def role_delete(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> None:
    """`handoff cloud role delete -p <project_directory> -v grantee_account_id=<grantee_id>`
    Delete the role.
    """
    state = _get_state()
    platform = _get_platform()
    account_id = platform.login()
    state.validate_env()
    if not vars.get("grantee_account_id"):
        LOGGER.warn("grantee_account_id was not set." +
                    "The grantee will be set for the same account. To set: ")
        LOGGER.warn("-v grantee_account_id=xxxx")
    if not vars.get("external_id"):
        raise ValueError("external_id must be set. Do as:\n    " +
                         "handoff cloud create_role -p <project-vir> " +
                         "-v external_id=yyyy")

    return platform.delete_role(
        grantee_account_id=vars.get("grantee_account_id", account_id),
        external_id=vars.get("external_id")
    )


def bucket_create(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff cloud bucket create -p <project_directory>`
    Create remote storage bucket. Bucket is attached to the resource group.
    """
    state = _get_state()
    platform = _get_platform()
    state.validate_env()
    return platform.create_bucket()


def bucket_update(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff cloud bucket update -p <project_directory>`
    Update remote storage bucket info
    """
    state = _get_state()
    platform = _get_platform()
    state.validate_env()
    return platform.update_bucket()


def bucket_delete(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff cloud bucket delete -p <project_directory>`
    Delete remote storage bucket.
    """
    state = _get_state()
    platform = _get_platform()
    state.validate_env()
    return platform.delete_bucket()


def resources_create(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff cloud resources create -p <project_directory>`
    Create resources necessary for task execution.
    The resources are shared among the tasks under the same resource group.

    AWS:
    - Please refer to the
      [CloudFormation template](https://github.com/anelenvars/handoff/blob/master/handoff/services/cloud/aws/cloudformation_templates/resources.yml) for the resources created with this command.
    """
    state = _get_state()
    platform = _get_platform()
    state.validate_env()
    return platform.create_resources()


def resources_update(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff cloud resources update -p <project_directory>`
    Update the resources

    The resources are shared among the tasks under the same resource group.
    """
    state = _get_state()
    platform = _get_platform()
    state.validate_env()
    return platform.update_resources()


def resources_delete(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff cloud resources delete -p <project_directory>`
    Delete the resources

    The resources are shared among the tasks under the same resource group.
    """
    state = _get_state()
    platform = _get_platform()
    state.validate_env()
    return platform.delete_resources()


def task_create(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> None:
    """`handoff cloud task create -p <project_directory>`
    Create the task
    Optionally,
    -v cpu=256, memory=512
    """
    state = _get_state()
    platform = _get_platform()
    state.validate_env([IMAGE_VERSION])
    return platform.create_task(**vars)


def task_update(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> None:
    """`handoff cloud task update -p <project_directory>`
    Update the task
    Optionally,
    -v cpu=256, memory=512
    """
    state = _get_state()
    platform = _get_platform()
    state.validate_env([IMAGE_VERSION])
    return platform.update_task(**vars)


def task_delete(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff cloud task delete -p <project_directory>`
    Delete the task
    """
    state = _get_state()
    platform = _get_platform()
    state.validate_env()
    return platform.delete_task()


def task_status(
    project_dir: str,
    workspace_dir: str,
    vars: str = None,
    **kwargs) -> None:
    """`handoff cloud task status -p <project_directory> -v full=False running=True stopped=True resource_group_level=False`
    list task status

    AWS options:
    - full: When true, print the full description (default: false)
    - running: When true, include desired status = RUNNING (default: true)
    - stopped: When true, include desired status = STOPPED (default: true)
    - resource_group_level: When true, list all the tasks under the same resource groups (default: false)
    """
    state = _get_state()
    platform = _get_platform()
    state.validate_env()
    return platform.list_tasks(**vars)


def task_stop(
    project_dir: str,
    workspace_dir: str,
    vars: str = None,
    **kwargs) -> None:
    """`handoff cloud task stop -p <project_directory> -v id=<task_id> reason=<reason>`
    stop a running task
    Options:
    - reason
    """
    state = _get_state()
    platform = _get_platform()
    state.validate_env()
    return platform.stop_task(**vars)


def run(
    project_dir: str,
    workspace_dir: str,
    envs: Dict = {},
    vars: Dict = {},
    extras: str = None,
    **kwargs) -> None:
    """`handoff cloud run -v resource_group=<resource_group_name> task=<task_name> target_id=<target_id> -e vars='key1=val1 key2=val2...'`
    Run a task once in the platform

    If the environment variable vars is specified via -e option, it will be
    used as:
    `handoff run -v $(eval echo $vars)`
    """
    state = _get_state()
    platform = _get_platform()
    config = admin._config_get_local(project_dir, workspace_dir)
    state.validate_env()

    extras_obj = None
    if extras:
        with open(extras, "r") as f:
            extras_obj = yaml.load(f)

    target_id = vars.get("target_id")
    target_envs = dict()
    if target_id:
        for s in config.get("schedules", []):
            if str(s["target_id"]) == target_id:
                for e in s.get("envs"):
                    target_envs[e["key"]] = e["value"]
                break
    target_envs.update(envs)
    target_envs[STAGE] = state[STAGE]
    return platform.run_task(env=target_envs, extras=extras_obj)


def schedule_create(
    project_dir: str,
    workspace_dir: str,
    envs: Dict = {},
    vars: Dict = {},
    extras: str = None,
    **kwargs) -> None:
    """`handoff cloud schedule create -v target_id=<target_id> cron="<cron_format>" -e vars='key1=val1 key2=val2...'`
    Schedule a task named <target_id> at the recurring scheduled specified
    as <cron_format>. An example of cron-format string is `10 01 * * ? *`
    for every day at 01:10 (1:10AM)

    If the environment variable vars is specified via -e option, it will be
    used as:
    `handoff run -v $(eval echo $vars)`
    """
    state = _get_state()
    platform = _get_platform()
    config = admin._config_get_local(project_dir, workspace_dir)
    state.validate_env()
    schedules = config.get("schedules")

    target_id = vars.get("target_id")
    cronexp = vars.get("cron")
    extras_obj = None
    if extras:
        with open(extras, "r") as f:
            extras_obj = yaml.load(f)
    if not schedules:
        schedules = [{"target_id": target_id, "cron": cronexp,
                      "extras_obj": extras_obj}]

    if not schedules and (not target_id or not cronexp):
        print("Schedules not found in project.yml. You can also set " +
              "'-v target_id=<ID> cron=<CRON>'")
        exit(1)

    envs[STAGE] = state[STAGE]

    responses = []
    for s in schedules:
        if target_id is not None and str(s["target_id"]) != str(target_id):
            continue
        if target_id is not None and cronexp:
            s["cron"] = cronexp

        e = dict()
        for e1 in s.get("envs", list()):
            e[e1["key"]] = e1["value"]
        # priority of the values schedule section < envs section < command line
        e.update(envs)
        r = platform.schedule_task(
            str(s["target_id"]), "cron(" + s["cron"] + ")",
            env=e,
            extras=s.get("extras_obj"))
        responses.append(r)
    return responses



def schedule_delete(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> None:
    """`handoff cloud schedule delete -v target_id=<target_id>`
    Unschedule a task named <target_id>
    """
    state = _get_state()
    platform = _get_platform()
    state.validate_env()
    if not vars.get("target_id"):
        print("Forgot to set '-v target_id=<ID>' ?")
        exit(1)
    target_id = str(vars["target_id"])
    try:
        response = platform.unschedule_task(target_id)
    except Exception as e:
        response = str(e)
    return response

def schedule_list(
    project_dir: str,
    workspace_dir: str,
    vars=None,
    **kwargs) -> None:
    """`handoff cloud schedule list`
    List the scheduled tasks
    """
    state = _get_state()
    platform = _get_platform()
    state.validate_env()
    schedules = platform.list_schedules(**vars)
    target_ids = []
    for s in schedules["schedules"]:
        target_ids.append(s["target_id"])
        s["status"] = "scheduled"

    if vars.get("include_unpublished"):
        config = admin._config_get_local(project_dir, workspace_dir)
        local_schedules = config.get("schedules", [])
        for s in local_schedules:
            status = ""
            try:

                index = target_ids.index(s["target_id"])
            except ValueError:
                index = len(target_ids)
                target_ids.append(s["target_id"])
                schedules["schedules"].append({})
                status = "draft"

            remote = {}
            remote.update(schedules["schedules"][index])
            if remote.get("status"):
                remote.pop("status")
            if remote.get("name"):
                remote.pop("name")
            if s != remote:
                schedules["schedules"][index] = s
                status = status or "edited"
                schedules["schedules"][index]["status"] = status

    return schedules


def logs(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> None:
    """`handoff cloud logs -v start_time=<start_time> end_time=<end_time> follow=<True/False>`
    Show logs
    Use --vars (-v) option to:
    - start_time: ISO 8086 formatted date time to indicate the start time
    - end_time
    - follow: If set, it waits for more logs until interrupted by ctrl-c
    """
    state = _get_state()
    platform = _get_platform()
    state.validate_env()
    close = False
    if vars.get("file"):
        file_descriptor = open(vars.pop("file"), "a")
        close = True
    else:
        file_descriptor = sys.stdout

    platform.write_logs(file_descriptor, **vars)

    if close:
        file_descriptor.close()

