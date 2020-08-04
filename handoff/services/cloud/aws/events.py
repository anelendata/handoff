import logging, os

import boto3

from . import credentials as cred
from . import cloudformation as cfn, iam, sts


logger = logging.getLogger(__name__)


def get_client():
    return cred.get_client("events")


def schedule_task(task_stack, resource_group_stack, region,
                  target_id, cronexp, role_arn,
                  workers=1):
    client = get_client()

    rule_name = resource_group_stack + "-" + task_stack + "-" + target_id

    kwargs = {
        "Name": rule_name,
        "ScheduleExpression": cronexp
    }
    client.put_rule(**kwargs)

    task_resources = cfn.describe_stack_resources(task_stack)["StackResources"]
    account_id = sts.get_account_id()
    cluster_arn = None
    task_def_arn = None
    for r in task_resources:
        if not cluster_arn and r["ResourceType"] == "AWS::ECS::Cluster":
            cluster_arn = "arn:aws:ecs:{region}:{account_id}:cluster/{phys_rsrc_id}".format(
                **{"region": region,
                   "account_id": account_id,
                   "phys_rsrc_id": r["PhysicalResourceId"]})

        if not task_def_arn and r["ResourceType"] == "AWS::ECS::TaskDefinition":
            task_def_arn = r["PhysicalResourceId"]

    rg_resources = cfn.describe_stack_resources(resource_group_stack)["StackResources"]
    subnets = list()
    security_groups =list()
    for r in rg_resources:
        if r["ResourceType"]  == "AWS::EC2::Subnet":
            subnets.append(r["PhysicalResourceId"])
        if r["ResourceType"] == "AWS::EC2::SecurityGroup":
            security_groups.append(r["PhysicalResourceId"])

    logger.debug("%s\n%s\n%s\n%s" % (cluster_arn, task_def_arn, subnets, security_groups))

    kwargs = {
        "Rule": rule_name,
        "Targets": [
            {
                "Id": target_id,
                "Arn": cluster_arn,
                "RoleArn": role_arn,
                "EcsParameters": {
                    "TaskDefinitionArn": task_def_arn,
                    "TaskCount": workers,
                    "LaunchType": "FARGATE",
                    "NetworkConfiguration": {
                        "awsvpcConfiguration": {
                            "Subnets": subnets,
                            "SecurityGroups": security_groups,
                            "AssignPublicIp": "ENABLED"
                        }
                    }
                }
            }
        ]
    }
    return client.put_targets(**kwargs)


def unschedule_task(task_stack, resource_group_stack, target_id):
    client = get_client()
    rule_name = resource_group_stack + "-" + task_stack + "-" + target_id
    kwargs = {
        "Rule": rule_name,
        "Ids": [target_id]
    }
    client.remove_targets(**kwargs)
    client.delete_rule(Name=rule_name)
