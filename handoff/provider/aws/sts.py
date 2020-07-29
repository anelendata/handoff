import logging
import boto3
from . import credentials as cred

logger = logging.getLogger(__name__)
STS_CLIENT = None


def get_client():
    global STS_CLIENT
    if STS_CLIENT:
        return STS_CLIENT
    aws_access_key_id, aws_secret_access_key, aws_session_token, aws_region = cred.get_credentials()
    logger.debug(aws_access_key_id[0:-5] + "***** " + aws_secret_access_key[0:-5] + "***** " + aws_region)
    boto_session = boto3.session.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name=aws_region)
    STS_CLIENT = boto_session.client("sts")
    return STS_CLIENT


def get_account_id():
    client = get_client()
    account_id = client.get_caller_identity()["Account"]
    return account_id
