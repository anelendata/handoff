import logging
import boto3
from . import credentials as cred

logger = logging.getLogger(__name__)


def get_client(cred_keys: dict = {}):
    return cred.get_client("sts", cred_keys)


def get_default_region(cred_keys: dict = {}):
    client = cred.get_session(cred_keys)
    return client.region_name


def get_account_id(cred_keys: dict = {}):
    client = get_client(cred_keys)
    account_id = client.get_caller_identity()["Account"]
    return account_id


def assume_role(
        role_arn: str,
        session_name: str = "tmp",
        external_id: str = None,
        cred_keys: dict = {}):
    client = get_client(cred_keys)
    kwargs = {
        "RoleArn": role_arn,
        "RoleSessionName": session_name,
    }
    if external_id:
        kwargs["ExternalId"] = external_id
    return client.assume_role(**kwargs)
