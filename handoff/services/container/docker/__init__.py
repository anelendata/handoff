import os, sys
from typing import Dict

from handoff import config, utils
from handoff.services import cloud
from handoff.config import CONTAINER_IMAGE
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
    # Do this to set CONTAINER_IMAGE
    _ = admin._config_get_local(project_dir, workspace_dir, **kwargs)


def build(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> None:
    """Build Docker image
    If you want to feed a custom Dockerfile, use --vars (-v) option:
      --vars docker_file="/path_to/Dockerfile"
    If you have extra files to copy to the image's workspace directory,
    use --vars option. Every file under the directory will be copied:
      --vars files_dir="/path_to/extra_files_dir"
    """
    _envs(project_dir, workspace_dir, vars=vars, **kwargs)
    state = config.get_state()
    state.validate_env([CONTAINER_IMAGE])
    files_dir = vars.get("files_dir")
    docker_file = vars.get("docker_file")
    new_version = vars.get("version")
    if docker_file:
        LOGGER.info("Using Dockerfile at: " + docker_file)
    impl.build(project_dir, docker_file=docker_file, files_dir=files_dir,
               new_version=new_version, **kwargs)


def run(
    project_dir: str,
    workspace_dir: str,
    envs: Dict = {},
    vars: Dict = {},
    **kwargs) -> None:
    _envs(project_dir, workspace_dir, envs=envs, **kwargs)
    state = config.get_state()
    state.validate_env([CONTAINER_IMAGE])

    env = cloud._get_platform_auth_env(project_dir, workspace_dir,
                                       envs=envs, **kwargs)
    env.update(envs)
    kwargs.update(vars)
    try:
        impl.run(extra_env=env, **kwargs)
    except Exception as e:
        LOGGER.critical(str(e).replace("\\n", "\n"))
        raise


def push(
    project_dir: str,
    workspace_dir: str,
    yes=False,
    **kwargs) -> None:
    _envs(project_dir, workspace_dir, **kwargs)
    state = config.get_state()
    state.validate_env([CONTAINER_IMAGE])

    platform = cloud._get_platform()
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

    impl.push(username, password, registry, yes=yes, **kwargs)


def get_latest_image_version(
     project_dir: str,
    workspace_dir: str,
    **kwargs) -> str:
    state = config.get_state()
    state.validate_env([CONTAINER_IMAGE])
    image_name = state.get(CONTAINER_IMAGE)
    return impl.get_latest_version(image_name)
