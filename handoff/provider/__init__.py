import os, sys
from importlib import import_module as _import_module
from handoff.core.utils import get_logger as _get_logger
from handoff.core.utils import env_check as _env_check
from handoff.config import (BUCKET, RESOURCE_GROUP, TASK, DOCKER_IMAGE,
                            IMAGE_VERSION)

LOGGER = _get_logger(__name__)


PLATFORM = None


def _get_platform(provider_name=None, platform_name=None, stdout=False,
                  profile=None, **kwargs):
    global PLATFORM
    if not PLATFORM:
        if not provider_name or not platform_name:
            raise Exception("You need to set provider_name and platform_name")
        PLATFORM = _import_module("handoff.provider." + provider_name)
        response = PLATFORM.login(profile)
        if stdout:
            sys.stdout.write(response)
    return PLATFORM


def get_platform_auth_env(project_dir, workspace_dir, data, **kwargs):
    platform = _get_platform()
    return platform.get_platform_auth_env(data)


def assume_role(project_dir, workspace_dir, data, **kwargs):
    _env_check([RESOURCE_GROUP])
    platform = _get_platform()
    role_arn = data.get("role_arn")
    target_account_id = data.get("target_account_id")
    external_id = data.get("external_id")
    platform.assume_role(role_arn=role_arn,
                         target_account_id=target_account_id,
                         external_id=external_id)


def create_role(project_dir, workspace_dir, data, **kwargs):
    platform = _get_platform()
    _env_check()
    platform.create_role(
        grantee_account_id=data.get("grantee_account_id"),
        external_id=data.get("external_id")
    )


def update_role(project_dir, workspace_dir, data, **kwargs):
    platform = _get_platform()
    _env_check()
    platform.update_role(
        grantee_account_id=data.get("grantee_account_id"),
        external_id=data.get("external_id")
    )


def delete_role(project_dir, workspace_dir, data, **kwargs):
    platform = _get_platform()
    _env_check()
    platform.delete_role()


def create_bucket(project_dir, workspace_dir, data, **kwargs):
    platform = _get_platform()
    _env_check()
    platform.create_bucket()


def update_bucket(project_dir, workspace_dir, data, **kwargs):
    platform = _get_platform()
    _env_check()
    platform.update_bucket()


def delete_bucket(project_dir, workspace_dir, data, **kwargs):
    platform = _get_platform()
    _env_check()
    platform.delete_bucket()


def create_resources(project_dir, workspace_dir, data, **kwargs):
    platform = _get_platform()
    _env_check()
    platform.create_resources()


def update_resources(project_dir, workspace_dir, data, **kwargs):
    platform = _get_platform()
    _env_check()
    platform.update_resources()


def delete_resources(project_dir, workspace_dir, data, **kwargs):
    platform = _get_platform()
    _env_check()
    platform.delete_resources()


def create_task(project_dir, workspace_dir, data, **kwargs):
    platform = _get_platform()
    _env_check()
    platform.create_task()


def update_task(project_dir, workspace_dir, data, **kwargs):
    platform = _get_platform()
    _env_check()
    platform.update_task()


def delete_task(project_dir, workspace_dir, data, **kwargs):
    platform = _get_platform()
    _env_check()
    platform.delete_task()


def run(project_dir, workspace_dir, data, **kwargs):
    platform = _get_platform()
    _env_check()
    platform.run_task()


def schedule(project_dir, workspace_dir, data, **kwargs):
    platform = _get_platform()
    _env_check()
    target_id = str(data["target_id"])
    cronexp = "cron(" + data["cron"] + ")"
    platform.schedule_task(target_id, cronexp)


def unschedule(project_dir, workspace_dir, data, **kwargs):
    platform = _get_platform()
    _env_check()
    target_id = str(data["target_id"])
    platform.unschedule_task(target_id)
