import json, logging, os

import boto3

from . import credentials as cred


logger = logging.getLogger(__name__)


def get_client(cred_keys: dict = {}):
    return cred.get_client("ssm", cred_keys)


def get_parameter(key, cred_keys: dict = {}):
    client = get_client(cred_keys)
    param = client.get_parameter(Name=key, WithDecryption=True)
    value = param["Parameter"]["Value"]
    return value


def get_parameters_by_path(path, cred_keys: dict = {}):
    client = get_client(cred_keys)
    response = client.get_parameters_by_path(
        Path=path,
        Recursive=False,
        WithDecryption=True)
    params = {}
    for item in response["Parameters"]:
        params[item["Name"]] = item["Value"]
    return params


def put_parameter(key, value,
                  description="",
                  type_="SecureString",
                  key_id=None,
                  overwrite=True,
                  allowed_pattern=None,
                  tags=None,
                  tier="Standard",
                  policies=None,
                  cred_keys: dict = {},
                  ):
    """
    For parameters, see
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.put_parameter
    """
    client = get_client(cred_keys)

    kwargs = {"Name": key,
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


def delete_parameter(key, cred_keys: dict = {}):
    client = get_client(cred_keys)
    kwargs = {"Name": key}
    response = client.delete_parameter(**kwargs)
    return response
