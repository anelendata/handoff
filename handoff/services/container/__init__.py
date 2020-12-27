from importlib import import_module as _import_module
from handoff.utils import get_logger as _get_logger
from handoff import config
from handoff.config import CONTAINER_PROVIDER


CONTAINER_MODULE = None


def _get_platform(provider_name: str = None) -> str:
    state = config.get_state()
    if not provider_name:
        provider_name = state.get(CONTAINER_PROVIDER)
    global CONTAINER_MODULE
    if not CONTAINER_MODULE:
        if not provider_name:
            raise Exception(
                "You need to set container provider name (e.g. docker)")
        CONTAINER_MODULE = _import_module("handoff.services.container." +
                                          provider_name)
    return CONTAINER_MODULE


def _get_latest_image_version(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> str:
    return _get_platform().get_latest_image_version(
        project_dir, workspace_dir, **kwargs)


def build(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff container build -p <project_directory> -v docker_file=<docker_file> files_dir=<addtnl_files_dir>`
    Build the container image
    Optionally, use docker_file to specify own Dockerfile
    """
    return _get_platform().build(project_dir, workspace_dir, **kwargs)


def run(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff container run -p <project_directory> -e resource_group=<resource_group_name> task=<task_name> __VARS='key1=val1 key2=val2...'`
    Run the container

    If the environment variable __VARS is specified via -e option, it will be
    used as:
    `handoff run -d $(eval echo $__VARS)`
    """
    return _get_platform().run(project_dir, workspace_dir, **kwargs)


def push(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff container push -p <project_directory>`
    Push the container image to remote repository
    """
    return _get_platform().push(project_dir, workspace_dir, **kwargs)
