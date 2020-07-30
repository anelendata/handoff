import os
from handoff.provider.aws import ecr, s3, ssm, sts  #, cloudformation
from handoff.impl import utils
from handoff.config import (BUCKET, DOCKER_IMAGE, IMAGE_DOMAIN,
                            IMAGE_VERSION, RESOURCE_GROUP, TASK)


LOGGER = utils.get_logger(__name__)
# TEMPLATE_DIR = "cloudformation_templates"


def get_parameter(key):
    return ssm.get_parameter(os.environ.get(RESOURCE_GROUP) + "-" +
                             os.environ.get(TASK), key)


def push_parameter(key, value, allow_advanced_tier=False):
    if allow_advanced_tier:
        LOGGER.info("Allowing AWS SSM Parameter Store to store with Advanced tier (max 8KB)")
    tier = "Standard"
    if len(value) > 8192:
        raise Exception("Parameter string must be less than 8192kb!")
    if len(value) > 4096:
        if allow_advanced_tier:
            tier = "Advanced"
        else:
            raise Exception("Parameter string is %s > 4096 byte and allow_advanced_tier=False" % len(value))
    LOGGER.info("Putting the config to AWS SSM Parameter Store with %s tier" % tier)
    ssm.put_parameter(os.environ.get(RESOURCE_GROUP) + "-" +
                      os.environ.get(TASK),
                      key, value, tier=tier)


def delete_parameter(key):
    ssm.delete_parameter(os.environ.get(RESOURCE_GROUP) + "-" +
                      os.environ.get(TASK),
                      key)


def download_dir(remote_dir, local_dir):
    remote_dir = os.path.join(os.environ.get(TASK), remote_dir)
    s3.download_dir(remote_dir, local_dir, os.environ.get(BUCKET))


def upload_dir(src_dir_name, dest_prefix):
    dest_prefix = os.path.join(os.environ.get(TASK), dest_prefix)
    s3.upload_dir(src_dir_name, dest_prefix, os.environ.get(BUCKET))


def delete_dir(remote_dir):
    remote_dir = os.path.join(os.environ.get(TASK), remote_dir)
    s3.delete_recurse(remote_dir, os.environ.get(BUCKET))


def copy_dir_to_another_bucket(src_dir, dest_dir):
    src_prefix = os.path.join(os.environ.get(TASK), src_dir)
    dest_prefix = os.path.join(os.environ.get(TASK), dest_dir)
    s3.copy_dir_to_another_bucket(os.environ.get(BUCKET), src_prefix,
                                  os.environ.get(BUCKET), dest_prefix)


def get_docker_registry_credentials(registry_id=None):
    if not registry_id:
        registry_id = sts.get_account_id()
    return ecr.get_docker_registry_credentials(registry_id)


def get_repository_images(image_name=None):
    if not image_name:
        image_name = os.environ.get(DOCKER_IMAGE)
    ecr_images = ecr.list_images(image_name)
    if not ecr_images:
        return None
    images = [{"id": i["imageDigest"], "tag": i["imageTag"]} for i in ecr_images]
    return images


def create_repository(is_mutable=False):
    name = os.environ.get(DOCKER_IMAGE)
    ecr.create_repository(name, is_mutable)
