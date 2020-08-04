import datetime, logging

import boto3

from . import credentials as cred
from . import cloudformation as cfn, sts


logger = logging.getLogger(__name__)


def get_client():
    return cred.get_client("ecs")


def run_fargate_task(task_stack, resource_group_stack, docker_image, region,
                     env=[], workers=1):
    env.append({"name": "TASK_TRIGGERED_AT", "value": datetime.datetime.utcnow().isoformat()})
    client = get_client()
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
        if r["ResourceType"] == "AWS::EC2::Subnet":
            subnets.append(r["PhysicalResourceId"])
        if r["ResourceType"] == "AWS::EC2::SecurityGroup":
            security_groups.append(r["PhysicalResourceId"])

    logger.debug("%s\n%s\n%s\n%s" % (cluster_arn, task_def_arn, subnets, security_groups))

    kwargs = {
        "cluster": cluster_arn,
        "taskDefinition": task_def_arn,
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
