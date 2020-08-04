from importlib import import_module as _import_module
from handoff.utils import get_logger as _get_logger
from handoff import config
from handoff.config import CONTAINER_PROVIDER


CONTAINER_MODULE = None


def _get_platform(provider_name=None):
    state = config.get_state()
    if not provider_name:
        provider_name = state.get(CONTAINER_PROVIDER)
    global CONTAINER_MODULE
    if not CONTAINER_MODULE:
        if not provider_name:
            raise Exception("You need to set provider_name and platform_name")
        CONTAINER_MODULE = _import_module("handoff.services.container." +
                                          provider_name)
    return CONTAINER_MODULE


def build(project_dir, workspace_dir, data, **kwargs):
    _get_platform.build(project_dir, workspace_dir, data, **kwargs)


def run(project_dir, workspace_dir, data, **kwargs):
    _get_platform.run(project_dir, workspace_dir, data, **kwargs)


def push(project_dir, workspace_dir, data, **kwargs):
    _get_platform.push(project_dir, workspace_dir, data, **kwargs)


def get_latest_image_version(project_dir, workspace_dir, data, **kwargs):
    return _get_platform.get_latest_version(project_dir, workspace_dir,
                                            data, **kwargs)
