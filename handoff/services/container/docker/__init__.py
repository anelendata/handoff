import os, sys
from typing import Dict

from handoff import config, utils
from handoff.services import cloud
from handoff.config import DOCKER_IMAGE
from handoff.core import admin
from . import impl


LOGGER = utils.get_logger(__name__)


def _envs(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    platform = cloud._get_platform()
    if not platform.login():
        raise Exception("Please set platform credentials")
    # Do this to set DOCKER_IMAGE
    _ = admin._config_get_local(project_dir, workspace_dir, **kwargs)


def build(
    project_dir: str,
    workspace_dir: str,
    data: Dict = {},
    **kwargs) -> None:
    """Build Docker image
    If you want to feed a custom Dockerfile, use --data option:
      --data docker_file="/path_to/Dockerfile"
    If you have extra files to copy to the image's workspace directory,
    use --data option. Every file under the directory will be copied:
      --data files_dir="/path_to/extra_files_dir"
    """
    _envs(project_dir, workspace_dir, data=data, **kwargs)
    state = config.get_state()
    state.validate_env([DOCKER_IMAGE])
    files_dir = data.get("files_dir")
    docker_file = data.get("docker_file")
    new_version = data.get("version")
    if docker_file:
        LOGGER.info("Using Dockerfile at: " + docker_file)
    impl.build(project_dir, docker_file=docker_file, files_dir=files_dir,
               new_version=new_version)


def run(
    project_dir: str,
    workspace_dir: str,
    envs: Dict = {},
    **kwargs) -> None:
    _envs(project_dir, workspace_dir, envs=envs, **kwargs)
    state = config.get_state()
    state.validate_env([DOCKER_IMAGE])

    env = cloud._get_platform_auth_env(project_dir, workspace_dir,
                                       envs=envs, **kwargs)
    env.update(envs)
    try:
        impl.run(extra_env=env)
    except Exception as e:
        LOGGER.critical(str(e).replace("\\n", "\n"))
        raise


def push(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    _envs(project_dir, workspace_dir, **kwargs)
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


def get_latest_image_version(
     project_dir: str,
    workspace_dir: str,
    **kwargs) -> str:
    state = config.get_state()
    state.validate_env([DOCKER_IMAGE])
    image_name = state.get(DOCKER_IMAGE)
    return impl.get_latest_version(image_name)
