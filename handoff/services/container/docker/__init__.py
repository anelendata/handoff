import os, sys
from handoff import config, utils
from handoff.services import cloud
from handoff.config import DOCKER_IMAGE
from handoff.core import admin
from . import impl


LOGGER = utils.get_logger(__name__)


def _envs(project_dir, workspace_dir, data, **kwargs):
    _ = admin.config_get_local(project_dir, workspace_dir, data, **kwargs)
    platform = cloud._get_platform()
    if not platform.login():
        raise Exception("Please set platform credentials")
    # Do this again to set DOCKER_IMAGE
    _ = admin.config_get_local(project_dir, workspace_dir, data, **kwargs)


def build(project_dir, workspace_dir, data, **kwargs):
    _envs(project_dir, workspace_dir, data, **kwargs)
    state = config.get_state()
    state.validate_env([DOCKER_IMAGE])
    config_vars = admin.config_get_local(
        project_dir, workspace_dir, data, **kwargs)
    files_dir = config_vars.get("container", {}).get("files_dir")
    docker_file = config_vars.get("container", {}).get("docker_file")
    if docker_file:
        LOGGER.info("Using Dockerfile at: " + docker_file)
    impl.build(project_dir, docker_file=docker_file, files_dir=files_dir)


def run(project_dir, workspace_dir, data, **kwargs):
    _envs(project_dir, workspace_dir, data, **kwargs)
    state = config.get_state()
    state.validate_env([DOCKER_IMAGE])

    env = cloud._get_platform_auth_env(project_dir, workspace_dir,
                                       data, **kwargs)
    env.update(data)
    try:
        impl.run(extra_env=env)
    except Exception as e:
        LOGGER.critical(str(e).replace("\\n", "\n"))
        raise


def push(project_dir, workspace_dir, data, **kwargs):
    _envs(project_dir, workspace_dir, data, **kwargs)
    state = config.get_state()
    state.validate_env([DOCKER_IMAGE])

    platform = cloud._get_platform()
    username, password, registry = platform.get_docker_registry_credentials()
    image_name = state.get(DOCKER_IMAGE)
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


def get_latest_image_version(project_dir, workspace_dir, data, **kwargs):
    state = config.get_state()
    state.validate_env([DOCKER_IMAGE])
    image_name = state.get(DOCKER_IMAGE)
    return impl.get_latest_version(image_name)
