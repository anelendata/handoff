import json, logging, os

import boto3

from . import credentials as cred
from handoff import utils


LOGGER = utils.get_logger()


def get_client(cred_keys: dict = {}):
    return cred.get_client("stepfunctions", cred_keys)


def create_state_machine(
        name,
        cluster_arn,
        task_def_arn,
        subnets,
        security_groups,
        role_arn,
        overrides,
        log_group_arn=None,
        timeout=3600 * 4,
        retry_interval=1800,
        max_retries=4,
        backoff_rate=1,
        cred_keys: dict = {},
        **kwargs):
    client = get_client(cred_keys)
    definition = {
        "Version": "1.0",
        "Comment": "Run ECS/Fargate tasks",
        "TimeoutSeconds": timeout,
        "StartAt": "RunTask",
        "States": {
            "RunTask": {
                "Type": "Task",
                "Resource": "arn:aws:states:::ecs:runTask.sync",
                "Parameters": {
                    "LaunchType": "FARGATE",
                    "Cluster": cluster_arn,
                    "TaskDefinition": task_def_arn,
                    "NetworkConfiguration": {
                        "AwsvpcConfiguration": {
                            "Subnets": subnets,
                            "SecurityGroups": security_groups,
                            "AssignPublicIp": "ENABLED"
                        }
                    },
                    "Overrides": overrides,
                },
                "Retry": [
                    {
                        "ErrorEquals": [
                            "States.TaskFailed"
                        ],
                        "IntervalSeconds": retry_interval,
                        "MaxAttempts": max_retries,
                        "BackoffRate": backoff_rate,
                    }
                ],
                "End": True
            }
        }
    }
    sfn_kwargs = {}
    if log_group_arn:
        sfn_kwargs["loggingConfiguration"] = {
            "level": "ALL",
            "includeExecutionData": False,
            "destinations": [
                {
                    "cloudWatchLogsLogGroup": {
                        "logGroupArn": log_group_arn,
                    }
                },
            ]
        }

    response = client.create_state_machine(
        name=name,
        definition=json.dumps(definition),
        roleArn=role_arn,
        **sfn_kwargs,
    )
    sm_arn = response["stateMachineArn"]
    return sm_arn


def delete_state_machine(
        arn,
        cred_keys: dict = {}):
    client = get_client(cred_keys)
    response = client.delete_state_machine(stateMachineArn=arn)
