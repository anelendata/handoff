import datetime, json, logging, os

import boto3

from . import credentials as cred


logger = logging.getLogger(__name__)


def get_client(cred_keys: dict = {}):
    return cred.get_client("logs", cred_keys)


def get_log_group_arn(log_group_name, cred_keys: dict = {}):
    client = get_client(cred_keys)
    info = client.describe_log_groups(
            logGroupNamePrefix=log_group_name,
            limit=1,
            )
    return info["logGroups"][0]["arn"]


def filter_log_events(
    log_group_name,
    start_time=None,
    end_time=None,
    next_token=None,
    filter_pattern=None,
    extras=None,
    cred_keys: dict = {},
):
    if not filter_pattern:
        filter_pattern = " "

    client = get_client(cred_keys)
    kwargs = {
        "logGroupName": log_group_name,
        "filterPattern": filter_pattern,
    }
    if start_time:
        if type(start_time) is datetime.datetime:
            kwargs["startTime"] = int(start_time.timestamp() * 1000)
        elif type(start_time) is int:
            kwargs["startTime"] = start_time
        else:
            raise ValueError("Invalid startTime type")

    if end_time:
        if type(end_time) is datetime.datetime:
            kwargs["endTime"] = int(end_time.timestamp() * 1000)
        elif type(end_time) is int:
            kwargs["endTime"] = start_time
        else:
            raise ValueError("Invalid endTime type")

    if next_token:
        kwargs["nextToken"] = next_token

    valid_params = [
            "logGroupName",
            "logStreamNames",
            "logStreamNamePrefix",
            "startTime",
            "endTime",
            "filterPattern",
            "nextToken",
            "limit",
            "interleaved",
            ]
    if extras:
        for k in extras.keys():
            if k in valid_params:
                kwargs[k] = extras[k]

    response = client.filter_log_events(**kwargs)
    return response
