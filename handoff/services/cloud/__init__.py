import os, sys
from importlib import import_module as _import_module
from handoff.core import admin
from handoff.utils import get_logger as _get_logger
from handoff import config
from handoff.config import (BUCKET, RESOURCE_GROUP, TASK, DOCKER_IMAGE,
                            IMAGE_VERSION, CLOUD_PROVIDER, CLOUD_PLATFORM)

LOGGER = _get_logger(__name__)


PLATFORM_MODULE = None


def _get_platform(provider_name=None, platform_name=None,
                  stdout=False, cloud_profile=None, **kwargs):
    state = config.get_state()
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


def _assume_role(project_dir, workspace_dir, data, **kwargs):
    state = config.get_state()
    admin.config_get_local(project_dir, workspace_dir, data, **kwargs)
    state.validate_env([RESOURCE_GROUP])
    platform = _get_platform()
    role_arn = data.get("role_arn")
    target_account_id = data.get("target_account_id")
    external_id = data.get("external_id")
    platform.assume_role(role_arn=role_arn,
                         target_account_id=target_account_id,
                         external_id=external_id)


def _get_platform_auth_env(project_dir, workspace_dir, data, **kwargs):
    platform = _get_platform()
    return platform.get_platform_auth_env(data)


def create_role(project_dir, workspace_dir, data, **kwargs):
    state = config.get_state()
    admin.config_get_local(project_dir, workspace_dir, data, **kwargs)
    platform = _get_platform()
    account_id = platform.login()
    state.validate_env()
    if not data.get("external_id"):
        raise ValueError("external_id must be set. Do as:\n    " +
                         "handoff provider create_role -p <project-dir> " +
                         "-d '{\"external_id\": \"yyyy\"}'")
    if not data.get("grantee_account_id"):
        LOGGER.warn("grantee_account_id was not set." +
                    "The grantee will be set for the same account. To set: ")
        LOGGER.warn("-d '{\"grantee_account_id\": \"xxxx\"}'")

    platform.create_role(
        grantee_account_id=data.get("grantee_account_id", account_id),
        external_id=data.get("external_id")
    )


def update_role(project_dir, workspace_dir, data, **kwargs):
    state = config.get_state()
    admin.config_get_local(project_dir, workspace_dir, data, **kwargs)
    platform = _get_platform()
    account_id = platform.login()
    state.validate_env()
    if not data.get("external_id"):
        raise ValueError("external_id must be set. Do as:\n    " +
                         "handoff provider create_role -p <project-dir> " +
                         "-d '{\"external_id\": \"yyyy\"}'")
    if not data.get("grantee_account_id"):
        LOGGER.warn("grantee_account_id was not set." +
                    "The grantee will be set for the same account. To set: ")
        LOGGER.warn("-d '{\"grantee_account_id\": \"xxxx\"}'")

    platform.update_role(
        grantee_account_id=data.get("grantee_account_id", account_id),
        external_id=data.get("external_id")
    )


def delete_role(project_dir, workspace_dir, data, **kwargs):
    state = config.get_state()
    admin.config_get_local(project_dir, workspace_dir, data, **kwargs)
    platform = _get_platform()
    state.validate_env()
    platform.delete_role()


def create_bucket(project_dir, workspace_dir, data, **kwargs):
    state = config.get_state()
    admin.config_get_local(project_dir, workspace_dir, data, **kwargs)
    platform = _get_platform()
    state.validate_env()
    platform.create_bucket()


def update_bucket(project_dir, workspace_dir, data, **kwargs):
    state = config.get_state()
    admin.config_get_local(project_dir, workspace_dir, data, **kwargs)
    platform = _get_platform()
    state.validate_env()
    platform.update_bucket()


def delete_bucket(project_dir, workspace_dir, data, **kwargs):
    state = config.get_state()
    admin.config_get_local(project_dir, workspace_dir, data, **kwargs)
    platform = _get_platform()
    state.validate_env()
    platform.delete_bucket()


def create_resources(project_dir, workspace_dir, data, **kwargs):
    state = config.get_state()
    admin.config_get_local(project_dir, workspace_dir, data, **kwargs)
    platform = _get_platform()
    state.validate_env()
    platform.create_resources()


def update_resources(project_dir, workspace_dir, data, **kwargs):
    state = config.get_state()
    admin.config_get_local(project_dir, workspace_dir, data, **kwargs)
    platform = _get_platform()
    state.validate_env()
    platform.update_resources()


def delete_resources(project_dir, workspace_dir, data, **kwargs):
    state = config.get_state()
    admin.config_get_local(project_dir, workspace_dir, data, **kwargs)
    platform = _get_platform()
    state.validate_env()
    platform.delete_resources()


def create_task(project_dir, workspace_dir, data, **kwargs):
    state = config.get_state()
    admin.config_get_local(project_dir, workspace_dir, data, **kwargs)
    platform = _get_platform()
    state.validate_env([IMAGE_VERSION])
    platform.create_task()


def update_task(project_dir, workspace_dir, data, **kwargs):
    state = config.get_state()
    admin.config_get_local(project_dir, workspace_dir, data, **kwargs)
    platform = _get_platform()
    state.validate_env([IMAGE_VERSION])
    platform.update_task()


def delete_task(project_dir, workspace_dir, data, **kwargs):
    state = config.get_state()
    admin.config_get_local(project_dir, workspace_dir, data, **kwargs)
    platform = _get_platform()
    state.validate_env()
    platform.delete_task()


def run(project_dir, workspace_dir, data, **kwargs):
    """Run a task once in the platform
    """
    state = config.get_state()
    admin.config_get_local(project_dir, workspace_dir, data, **kwargs)
    platform = _get_platform()
    state.validate_env()
    platform.run_task(env=data)


def schedule(project_dir, workspace_dir, data, **kwargs):
    """Schedule a task
    Must have --data option
    -d '{"target_id": <target_id>, "cron": <cron_format>}'

    An example of cron-format string is "10 01 * * ? *"
    """
    state = config.get_state()
    admin.config_get_local(project_dir, workspace_dir, data, **kwargs)
    platform = _get_platform()
    state.validate_env()
    target_id = str(data["target_id"])
    cronexp = "cron(" + data["cron"] + ")"
    platform.schedule_task(target_id, cronexp)


def unschedule(project_dir, workspace_dir, data, **kwargs):
    """Unschedule a task
    Must have --data option:
    -d '{"target_id": <target_id>}'
    """
    state = config.get_state()
    admin.config_get_local(project_dir, workspace_dir, data, **kwargs)
    platform = _get_platform()
    state.validate_env()
    target_id = str(data["target_id"])
    platform.unschedule_task(target_id)
