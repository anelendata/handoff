import os, sys
from handoff import provider
from handoff.config import DOCKER_IMAGE
from handoff.core import utils
from handoff.core.utils import env_check as _env_check
from . import impl


LOGGER = utils.get_logger(__name__)


def build(project_dir, workspace_dir, data, **kwargs):
    if not project_dir:
        raise Exception("Project directory is not set")
    _env_check([DOCKER_IMAGE])
    impl.build(project_dir)


def run(project_dir, workspace_dir, data, **kwargs):
    platform = provider._get_platform()
    _env_check()
    if not os.environ.get("AWS_ACCESS_KEY_ID"):
        platform.assume_role()
    impl.run()


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
