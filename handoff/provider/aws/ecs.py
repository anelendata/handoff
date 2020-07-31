import datetime, json, logging, os

import boto3

from . import credentials as cred
from . import cloudformation as cfn, sts

ECS_CLIENT = None


logger = logging.getLogger(__name__)


def get_client():
    global ECS_CLIENT
    if ECS_CLIENT:
        return ECS_CLIENT
    aws_access_key_id, aws_secret_access_key, aws_session_token, aws_region = cred.get_credentials()
    logger.debug(aws_access_key_id[0:-5] + "***** " + aws_secret_access_key[0:-5] + "***** " + aws_region)
    boto_session = boto3.session.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name=aws_region)
    ECS_CLIENT = boto_session.client("ecs")
    return ECS_CLIENT


def run_fargate_task(task_stack, resource_group_stack, docker_image, region,
                     env=[], workers=1):
    env.append({"name": "TASK_TRIGGERED_AT", "value": datetime.datetime.utcnow().isoformat()})
    client = get_client()
    task_resources = cfn.describe_stack_resources(task_stack)["StackResources"]
    account_id = sts.get_account_id()
    cluster = None
    task_def = None
    for r in task_resources:
        if not cluster and r["ResourceType"] == "AWS::ECS::Cluster":
            cluster = "arn:aws:ecs:{region}:{account_id}:cluster/{phys_rsrc_id}".format(
                **{"region": region,
                   "account_id": account_id,
                   "phys_rsrc_id": r["PhysicalResourceId"]})

        if r["ResourceType"] == "AWS::ECS::TaskDefinition":
            task_def = r["PhysicalResourceId"]

    rg_resources = cfn.describe_stack_resources(resource_group_stack)["StackResources"]
    subnets = list()
    security_groups =list()
    for r in rg_resources:
        if r["ResourceType"]  == "AWS::EC2::Subnet":
            subnets.append(r["PhysicalResourceId"])
        if r["ResourceType"] == "AWS::EC2::SecurityGroup":
            security_groups.append(r["PhysicalResourceId"])

    logger.debug("%s\n%s\n%s\n%s" % (cluster, task_def, subnets, security_groups))

    kwargs = {
        "cluster": cluster,
        "taskDefinition": task_def,
        "count": workers,
        "launchType": "FARGATE",
        "networkConfiguration": {
            "awsvpcConfiguration": {
                "subnets": subnets,
                "securityGroups": security_groups,
                "assignPublicIp": "ENABLED"
            }
        },
        "overrides": {
            "containerOverrides": [
                {
                 "name": docker_image,
                 "environment": env
                 }
            ]
        }
    }
    return client.run_task(**kwargs)
