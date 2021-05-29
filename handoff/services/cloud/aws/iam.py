import logging

import boto3

from . import credentials as cred


logger = logging.getLogger(__name__)


def get_client(cred_keys: dict = {}):
    return cred.get_client("iam", cred_keys)


def list_roles(path_prefix=None, cred_keys: dict = {}):
    client = get_client(cred_keys)
    kwargs = dict()
    if path_prefix:
        kwargs["PathPrefix"] = path_prefix
    response = client.list_roles(**kwargs)
    roles = response["Roles"]
    marker = None
    if response["IsTruncated"]:
        marker = response["Marker"]
    while marker:
        kwargs["Marker"] = marker
        marker = None
        response = client.list_roles(**kwargs)
        roles = roles + response["Roles"]
        if response["IsTruncated"]:
            marker = response["Marker"]
    return roles
