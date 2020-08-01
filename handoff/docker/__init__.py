import os, sys
from handoff import provider
from handoff.config import DOCKER_IMAGE
from handoff.core import admin, utils
from handoff.core.utils import env_check as _env_check
from . import impl


LOGGER = utils.get_logger(__name__)


def _envs(project_dir, workspace_dir, data, **kwargs):
    _ = admin.config_get_local(project_dir, workspace_dir, data, **kwargs)
    platform = provider._get_platform()
    if not platform.login():
        raise Exception("Please set platform credentials")
    # Do this again to set DOCKER_IMAGE
    _ = admin.config_get_local(project_dir, workspace_dir, data, **kwargs)


def build(project_dir, workspace_dir, data, **kwargs):
    _envs(project_dir, workspace_dir, data, **kwargs)
    _env_check([DOCKER_IMAGE])
    impl.build(project_dir)


def run(project_dir, workspace_dir, data, **kwargs):
    _envs(project_dir, workspace_dir, data, **kwargs)
    _env_check([DOCKER_IMAGE])

    env = provider.get_platform_auth_env(project_dir, workspace_dir,
                                         data, **kwargs)
    env.update(data)
    try:
        impl.run(extra_env=env)
    except Exception as e:
        LOGGER.critical(str(e).replace("\\n", "\n"))
        raise


def push(project_dir, workspace_dir, data, **kwargs):
    platform = provider._get_platform()
    _env_check()
    username, password, registry = platform.get_docker_registry_credentials()
    image_name = os.environ.get(DOCKER_IMAGE)
    try:
        platform.get_repository_images(image_name)
    except Exception:
        sys.stdout.write("Repository %s does not exist. Create? (y/N)" %
                         image_name)
        response = input()
        if response.lower() not in ["y", "yes"]:
            return
        LOGGER.info("Creating repository " + image_name)
        platform.create_repository()

    impl.push(username, password, registry)


def get_latest_version(project_dir, workspace_dir, data, **kwargs):
    _env_check([DOCKER_IMAGE])
    image_name = os.environ.get(DOCKER_IMAGE)
    return impl.get_latest_version(image_name)
