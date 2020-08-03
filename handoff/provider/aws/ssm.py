import json, logging, os

import boto3

from . import credentials as cred


logger = logging.getLogger(__name__)


def get_client():
    return cred.get_client("ssm")


def get_parameter(project, name):
    client = get_client()
    param = client.get_parameter(Name=project + "_" + name, WithDecryption=True)
    value = param["Parameter"]["Value"]
    return value


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
    return response


def delete_parameter(project, key):
    client = get_client()
    kwargs = {"Name": project + "_" + key}
    response = client.delete_parameter(**kwargs)
    return response
