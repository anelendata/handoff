import os, shutil, sys, tarfile
import yaml
from importlib import import_module as _import_module
from typing import Dict
from types import ModuleType

from handoff.core import admin
from handoff import utils
from handoff.utils import get_logger as _get_logger
from handoff.config import (BUCKET, RESOURCE_GROUP, TASK, CONTAINER_IMAGE,
                            IMAGE_VERSION, CLOUD_PROVIDER, CLOUD_PLATFORM,
                            STAGE, TASK_NAKED)
from handoff.config import get_state as _get_state


LOGGER = _get_logger(__name__)


PLATFORM_MODULE = None


def logout():
    global PLATFORM_MODULE
    PLATFORM_MODULE = None


def get_platform(
    provider_name: str = None,
    platform_name: str = None,
    stdout: bool = False,
    cloud_profile: str = None,
    vars: Dict = {},
    **kwargs) -> ModuleType:
    global PLATFORM_MODULE
    if PLATFORM_MODULE:
        return PLATFORM_MODULE

    state = _get_state()

    if not provider_name:
        provider_name = state.get(CLOUD_PROVIDER)
    if not platform_name:
        platform_name = state.get(CLOUD_PLATFORM)
    if not provider_name or not platform_name:
        raise Exception("You need to set provider_name and platform_name")

    PLATFORM_MODULE = _import_module("handoff.services.cloud."
                                     + provider_name)
    cred_keys = PLATFORM_MODULE.find_cred_keys(vars)
    response = PLATFORM_MODULE.login(cloud_profile, cred_keys=cred_keys)
    if not response:
        raise Exception(
            f"Login to {provider_name} failed. Credentials may not be set correctly.")

    return PLATFORM_MODULE


def login_test(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> None:
    platform = get_platform()
    account_id = platform.get_account_id()
    if not account_id:
        return {"status": "not connected", "account_id": account_id}
    return {"status": "success", "account_id": account_id}


def role_create(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> None:
    """`handoff cloud role create -p <project_directory> -v external_id=<id> grantee_account_id=<grantee_id>`
    Create the role with deployment privilege.
    """
    state = _get_state()
    platform = get_platform()
    account_id = platform.get_account_id()
    if not account_id:
        raise Exception("Login failed")
    # state.validate_env()
    if not vars.get("grantee_account_id"):
        LOGGER.warn("grantee_account_id was not set." +
                    "The grantee will be set for the same account. To set: ")
        LOGGER.warn("-v grantee_account_id=xxxx")
    if not vars.get("external_id"):
        raise ValueError("external_id must be set. Do as:\n    " +
                         "handoff cloud create_role -p <project-vir> " +
                         "-v external_id=yyyy")

    return platform.create_role(
        grantee_account_id=str(vars.get("grantee_account_id", account_id)),
        external_id=vars.get("external_id"),
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
    platform = get_platform()
    account_id = platform.get_account_id()
    if not account_id:
        raise Exception("Login failed")
    # state.validate_env()
    if not vars.get("grantee_account_id"):
        LOGGER.warn("grantee_account_id was not set." +
                    "The grantee will be set for the same account. To set: ")
        LOGGER.warn("-v grantee_account_id=xxxx")
    if not vars.get("external_id"):
        raise ValueError("external_id must be set. Do as:\n    " +
                         "handoff cloud create_role -p <project-vir> " +
                         "-v external_id=yyyy")

    return platform.update_role(
        grantee_account_id=str(vars.get("grantee_account_id", account_id)),
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
    platform = get_platform()
    account_id = platform.get_account_id()
    # state.validate_env()
    if not vars.get("grantee_account_id"):
        LOGGER.warn("grantee_account_id was not set." +
                    "The grantee will be set for the same account. To set: ")
        LOGGER.warn("-v grantee_account_id=xxxx")

    return platform.delete_role(
        grantee_account_id=str(vars.get("grantee_account_id", account_id))
    )


def role_status(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> None:
    """`handoff cloud role status -p <project_directory>` -s <stage>
    Check the status of role
    """
    state = _get_state()
    platform = get_platform()
    state.validate_env()
    return platform.get_role_status(
        grantee_account_id=str(vars.get("grantee_account_id", account_id))
    )


def bucket_create(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff cloud bucket create -p <project_directory>`
    Create remote storage bucket. Bucket is attached to the resource group.
    """
    state = _get_state()
    platform = get_platform()
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
    platform = get_platform()
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
    platform = get_platform()
    state.validate_env()
    return platform.delete_bucket()


def bucket_status(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> None:
    """`handoff cloud bucket status -p <project_directory>` -s <stage>
    Check the status of bucket
    """
    state = _get_state()
    platform = get_platform()
    state.validate_env()
    return platform.get_bucket_status(**vars)


def resources_create(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> None:
    """`handoff cloud resources create -p <project_directory>`
    Create resources necessary for task execution.
    The resources are shared among the tasks under the same resource group.

    Optionally:
    -v static_ip=True: [AWS] Create Elastic IP and NAT Gateway to obtain a static IP. This [costs more](https://aws.amazon.com/vpc/pricing/).

    AWS:
    - Please refer to the
      [CloudFormation template](https://github.com/anelenvars/handoff/blob/master/handoff/services/cloud/aws/cloudformation_templates/resources.yml) for the resources created with this command.
    """
    state = _get_state()
    platform = get_platform()
    state.validate_env()
    return platform.create_resources(**vars)


def resources_update(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> None:
    """`handoff cloud resources update -p <project_directory>`
    Update the resources

    The resources are shared among the tasks under the same resource group.
    """
    state = _get_state()
    platform = get_platform()
    state.validate_env()
    return platform.update_resources(**vars)


def resources_delete(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff cloud resources delete -p <project_directory>`
    Delete the resources

    The resources are shared among the tasks under the same resource group.
    """
    state = _get_state()
    platform = get_platform()
    state.validate_env()
    return platform.delete_resources()


def resources_status(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> None:
    """`handoff cloud resources status -p <project_directory>` -s <stage>
    Check the status of resources
    """
    state = _get_state()
    platform = get_platform()
    state.validate_env()
    return platform.get_resources_status(**vars)


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
    platform = get_platform()
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
    platform = get_platform()
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
    platform = get_platform()
    state.validate_env()
    return platform.delete_task()


def task_status(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> None:
    """`handoff cloud task status -p <project_directory>` -s <stage>
    Check the status of task
    """
    state = _get_state()
    platform = get_platform()
    state.validate_env()
    return platform.get_task_status(**vars)


def job_status(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> None:
    """`handoff cloud job status -p <project_directory> -v full=False running=True stopped=True resource_group_level=False`
    list task status

    AWS options:
    - full: When true, print the full description (default: false)
    - running: When true, include desired status = RUNNING (default: true)
    - stopped: When true, include desired status = STOPPED (default: true)
    - resource_group_level: When true, list all the tasks under the same resource groups (default: false)
    """
    state = _get_state()
    platform = get_platform()
    state.validate_env()
    return platform.list_jobs(**vars)


def job_stop(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> None:
    """`handoff cloud job stop -p <project_directory> -v id=<task_id> reason=<reason>`
    stop a running task
    Options:
    - reason
    """
    state = _get_state()
    platform = get_platform()
    state.validate_env()
    return platform.stop_job(**vars)


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
    platform = get_platform()
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
    return platform.run_job(env=target_envs, extras=extras_obj)


def container_build(
    project_dir: str,
    workspace_dir: str,
    envs: Dict = {},
    vars: Dict = {},
    extras: str = None,
    yes: bool = False,
    **kwargs) -> None:
    """`handoff cloud container build -v resource_group=<resource_group_name> task=<task_name> target_id=<target_id> -e vars='key1=val1 key2=val2...'`
    build and push container in the cloud
    """
    state = _get_state()
    platform = get_platform()
    config = admin._config_get_local(project_dir, workspace_dir)
    state.validate_env()

    # Make the image repository if it does not exist
    username, password, registry = platform.get_docker_registry_credentials()
    image_name = state.get(CONTAINER_IMAGE)
    try:
        platform.get_repository_images(image_name)
    except Exception:
        if not yes:
            sys.stdout.write("Repository %s does not exist. Create (y/N)?" %
                             image_name)
            response = input()
            if response.lower() not in ["y", "yes"]:
                return
        LOGGER.info("Creating repository " + image_name)
        platform.create_repository()

    tar_file_name = state[TASK_NAKED] + ".tar.gz"
    account_id = platform.get_account_id()
    version = platform.get_latest_container_image_version(state[CONTAINER_IMAGE])
    new_version = utils.increment_version(version)
    destination = f"{account_id}.dkr.ecr.{state['AWS_REGION']}.amazonaws.com/{state[CONTAINER_IMAGE]}:{new_version}"
    command = [
        "--context", f"s3://{state[BUCKET]}/{state[TASK_NAKED]}/bundles/{tar_file_name}",
        #"--context-sub-path", "./some_subdir",
        #"--dockerfile", "myDockerfile",
        "--destination", destination,
        "--force",
    ]

    extras_obj = None
    if extras:
        with open(extras, "r") as f:
            extras_obj = yaml.load(f)

    target_envs = {}
    target_envs.update(envs)
    target_envs[STAGE] = state[STAGE]
    target_envs["COMMAND"] = "container remote build"
    target_envs[TASK] = state[TASK_NAKED]

    return platform.run_job(
            task_name="handoff-container-builder",
            container_name="handoff-container-builder",
            env=target_envs,
            command=command,
            extras=extras_obj,
            )


def container_version(
    project_dir: str,
    workspace_dir: str,
    envs: Dict = {},
    vars: Dict = {},
    extras: str = None,
    yes: bool = False,
    **kwargs) -> None:
    state = _get_state()
    platform = get_platform()
    image_name = state.get(CONTAINER_IMAGE)
    try:
        version = platform.get_latest_container_image_version(state[CONTAINER_IMAGE])
    except Exception as e:
        return {"status": "error", "message": str(e)}

    return {"status": "success", "version": version}


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
    platform = get_platform()
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
        return {
                "status": "error",
                "message": "Schedules not found in project.yml. You can also set "
                           "'-v target_id=<ID> cron=<CRON>'",
              }

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
        r = platform.schedule_job(
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
    platform = get_platform()
    state.validate_env()
    if not vars.get("target_id"):
        return {
            "status": "error",
            "message": "Forgot to set '-v target_id=<ID>' ?",
        }
    target_id = str(vars["target_id"])
    try:
        response = platform.unschedule_job(target_id)
    except Exception as e:
        response = str(e)
    return response

def schedule_list(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> None:
    """`handoff cloud schedule list`
    List the scheduled tasks
    """
    state = _get_state()
    platform = get_platform()
    state.validate_env()
    schedules = platform.list_schedules(**vars)
    target_ids = []
    for s in schedules["schedules"]:
        target_ids.append(str(s["target_id"]))
        s["status"] = "scheduled"

    if vars.get("include_unpublished"):
        config = admin._config_get_local(project_dir, workspace_dir)
        local_schedules = config.get("schedules", [])
        for s in local_schedules:
            status = ""
            try:
                index = target_ids.index(str(s["target_id"]))
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
            if s.get("description"):
                s.pop("description")
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
    - filter: Filter log term
    """
    state = _get_state()
    platform = get_platform()
    state.validate_env()
    close = False
    if vars.get("file"):
        file_descriptor = open(vars.pop("file"), "a")
        close = True
    else:
        file_descriptor = sys.stdout

    if vars.get("role_arn"):
        vars.pop("role_arn")
    platform.write_logs(file_descriptor, **vars)

    if close:
        file_descriptor.close()
