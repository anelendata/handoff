import os, tarfile
from importlib import import_module as _import_module
from typing import Dict

import yaml

from handoff.utils import get_logger as _get_logger
from handoff.config import get_state, BUNDLES_DIR, CONTAINER_PROVIDER, TASK_NAKED
from handoff.services import cloud


CONTAINER_MODULE = None


def _get_platform(provider_name: str = None) -> str:
    state = get_state()
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


def _tar_filter(file_):
    if ".secret" in file_.name:
        return None
    return file_


def bundle(
    project_dir: str,
    workspace_dir: str,
    vars: Dict = {},
    **kwargs) -> None:
    build_dir = vars.get("build_dir")
    tarball_dir = vars.get("tarball_dir")
    if not build_dir or not tarball_dir:
        raise Exception("build_dir and tarball_dir must be given")

    platform = cloud.get_platform()
    state = get_state()
    state.validate_env()

    res = _get_platform().bundle(project_dir, workspace_dir, vars, **kwargs)
    if res["status"] != "success":
        raise Exception("Bundle creation failed.")

    platform.delete_dir(BUNDLES_DIR)

    current_dir = os.getcwd()
    tar_file_name = state[TASK_NAKED] + ".tar.gz"
    with tarfile.open(os.path.join(tarball_dir, tar_file_name), "w:gz") as tar:
        os.chdir(build_dir)
        tar.add(
            ".",
            arcname=".",
            recursive=True,
            filter=_tar_filter,
        )
    os.chdir(current_dir)
    remote_tarball_path = f"{BUNDLES_DIR}/{tar_file_name}"
    res = platform.upload_file(
            os.path.join(tarball_dir, tar_file_name),
            remote_tarball_path,
    )


def build(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff container build -p <project_directory> -v docker_file=<docker_file> files_dir=<addtnl_files_dir>`
    Build the container image
    Optionally, use docker_file to specify own Dockerfile
    """
    return _get_platform().build(project_dir, workspace_dir, **kwargs)


def push(
    project_dir: str,
    workspace_dir: str,
    **kwargs) -> None:
    """`handoff container push -p <project_directory>`
    Push the container image to remote repository
    """
    return _get_platform().push(project_dir, workspace_dir, **kwargs)


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
