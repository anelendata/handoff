import os
from handoff.provider.aws import s3, ssm
from handoff.impl import utils

LOGGER = utils.get_logger(__name__)


def get_parameter(key):
    return ssm.get_parameter(os.environ.get("STACK_NAME"), key)


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
    ssm.put_parameter(os.environ.get("STACK_NAME"), key, value, tier=tier)


def download_dir(remote_dir, local_dir):
    remote_dir = os.path.join(os.environ.get("STACK_NAME"), remote_dir)
    s3.download_dir(remote_dir, local_dir, os.environ.get("BUCKET_NAME"))


def upload_dir(src_dir_name, dest_prefix):
    dest_prefix = os.path.join(os.environ.get("STACK_NAME"), dest_prefix)
    s3.upload_dir(src_dir_name, dest_prefix, os.environ.get("BUCKET_NAME"))


def delete_dir(remote_dir):
    remote_dir = os.path.join(os.environ.get("STACK_NAME"), remote_dir)
    s3.delete_recurse(remote_dir, os.environ.get("BUCKET_NAME"))


def copy_dir_to_another_bucket(src_dir, dest_dir):
    src_prefix = os.path.join(os.environ.get("STACK_NAME"), src_dir)
    dest_prefix = os.path.join(os.environ.get("STACK_NAME"), dest_dir)
    s3.copy_dir_to_another_bucket(os.environ.get("BUCKET_NAME"), src_prefix,
                                  os.environ.get("BUCKET_NAME"), dest_prefix)
