import json, logging, os

import boto3
import requests

from . import credentials as cred

SSM_CLIENT = None


logger = logging.getLogger(__name__)


def get_client():
    global SSM_CLIENT
    if SSM_CLIENT:
        return SSM_CLIENT
    aws_access_key_id, aws_secret_access_key, aws_session_token, aws_region = cred.get_credentials()
    logger.debug(aws_access_key_id[0:-5] + "***** " + aws_secret_access_key[0:-5] + "***** " + aws_region)
    boto_session = boto3.session.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name=aws_region)
    SSM_CLIENT = boto_session.client("ssm")
    return SSM_CLIENT


def put_parameter(project, key, value,
                  description="",
                  type_="SecureString",
                  key_id=None,
                  overwrite=True,
                  allowed_pattern=None,
                  tags=None,
                  tier="Standard",
                  policies=None
                  ):
    """
    For parameters, see
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.put_parameter
    """
    client = get_client()

    kwargs = {"Name": project + "_" + key,
              "Value": value,
              "Type": type_,
              "Overwrite": overwrite,
              "Tier": tier}
    if description:
        kwargs["Description"] = description
    if key_id:
        kwargs["KeyId"] = key_id
    if allowed_pattern:
        kwargs["AllowedPattern"] = allowed_pattern
    if tags:
        kwargs["Tags"] = tags
    if policies:
        kwargs["Policies"] = policies

    response = client.put_parameter(**kwargs)


def get_parameter(project, name):
    client = get_client()
    param = client.get_parameter(Name=project + "_" + name, WithDecryption=True)
    value = param["Parameter"]["Value"]
    return value


def set_env_var_from_ssm(project, name):
    value = get_parameter(project, name)
    os.environ[name] = value
