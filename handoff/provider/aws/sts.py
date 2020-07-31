import logging
import boto3
from . import credentials as cred

logger = logging.getLogger(__name__)


def get_client():
    return cred.get_client("sts")


def get_account_id():
    client = get_client()
    account_id = client.get_caller_identity()["Account"]
    return account_id


def assume_role(role_arn, session_name="tmp", external_id=None):
    client = get_client()
    kwargs = {
        "RoleArn": role_arn,
        "RoleSessionName": session_name,
    }
    if external_id:
        kwargs["ExternalId"] = external_id
    return client.assume_role(**kwargs)
