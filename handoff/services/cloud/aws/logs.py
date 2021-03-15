import datetime, json, logging, os

import boto3

from . import credentials as cred


logger = logging.getLogger(__name__)


def get_client():
    return cred.get_client("logs")


def filter_log_events(
    log_group_name,
    start_time=None,
    end_time=None,
    next_token=None,
    filter_pattern=None,
    extras=None,
):
    if not filter_pattern:
        filter_pattern = " "

    client = get_client()
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

    if extras:
        kwargs.update(extras)

    response = client.filter_log_events(**kwargs)
    return response
