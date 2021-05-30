import json, logging, os

import boto3

from . import credentials as cred
from . import cloudformation as cfn, iam, sts


logger = logging.getLogger(__name__)


def get_client(cred_keys: dict = {}):
    return cred.get_client("events", cred_keys)


def schedule_task(task_stack, resource_group_stack, container_image,
                  region, target_id, cronexp, role_arn,
                  env=[], extras=None, cred_keys: dict = {}):
    """Schedule a task
    extras overwrite the kwargs given to put_targets boto3 command.
    See: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/events.html#EventBridge.Client.put_targets
    """
    client = get_client(cred_keys)

    rule_name = resource_group_stack + "-" + task_stack + "-" + target_id

    kwargs = {
        "Name": rule_name,
        "ScheduleExpression": cronexp
    }
    client.put_rule(**kwargs)

    task_resources = cfn.describe_stack_resources(task_stack)["StackResources"]
    task_def_arn = None
    for r in task_resources:
        if r["ResourceType"] == "AWS::ECS::TaskDefinition":
            task_def_arn = r["PhysicalResourceId"]
            break

    rg_resources = cfn.describe_stack_resources(
        resource_group_stack)["StackResources"]
    account_id = sts.get_account_id()
    cluster_arn = None
    subnets = list()
    security_groups = list()
    for r in rg_resources:
        if not cluster_arn and r["ResourceType"] == "AWS::ECS::Cluster":
            cluster_arn = "arn:aws:ecs:{region}:{account_id}:cluster/{phys_rsrc_id}".format(
                **{"region": region,
                   "account_id": account_id,
                   "phys_rsrc_id": r["PhysicalResourceId"]})
        # PublicSubnetTwo is <= v0.3.4
        if (r["ResourceType"] == "AWS::EC2::Subnet" and
                r["LogicalResourceId"] in ["PublicSubnetTwo", "Subnet2"]):
            subnets.append(r["PhysicalResourceId"])
        if r["ResourceType"] == "AWS::EC2::SecurityGroup":
            security_groups.append(r["PhysicalResourceId"])

    logger.debug("%s\n%s\n%s\n%s" %
                 (cluster_arn, task_def_arn, subnets, security_groups))

    input_json = json.dumps(
        {"containerOverrides": [{"name": container_image, "environment": env}]})

    kwargs = {
        "Rule": rule_name,
        "Targets": [
            {
                "Id": target_id,
                "Arn": cluster_arn,
                "RoleArn": role_arn,
                "EcsParameters": {
                    "TaskDefinitionArn": task_def_arn,
                    "TaskCount": 1,
                    "LaunchType": "FARGATE",
                    "NetworkConfiguration": {
                        "awsvpcConfiguration": {
                            "Subnets": subnets,
                            "SecurityGroups": security_groups,
                            "AssignPublicIp": "ENABLED"
                        }
                    }
                },
                "Input": input_json
            }
        ]
    }

    if extras:
        kwargs.update(extras)

    return client.put_targets(**kwargs)


def unschedule_task(task_stack, resource_group_stack, target_id, cred_keys: dict = {}):
    client = get_client(cred_keys)
    rule_name = resource_group_stack + "-" + task_stack + "-" + target_id
    kwargs = {
        "Rule": rule_name,
        "Ids": [target_id]
    }
    client.remove_targets(**kwargs)
    client.delete_rule(Name=rule_name)


def list_schedules(task_stack, resource_group_stack, cred_keys: dict = {}):
    client = get_client(cred_keys)
    rule_prefix = resource_group_stack + "-" + task_stack
    kwargs = {
        "NamePrefix": rule_prefix,
    }
    rules = client.list_rules(**kwargs)
    if not rules.get("Rules"):
        raise Exception("No rules found")

    response = list()
    for rule in rules.get("Rules"):
        targets = client.list_targets_by_rule(Rule=rule["Name"])
        record = {"rule": rule, "targets": targets.get("Targets")}
        response.append(record)
    return response
