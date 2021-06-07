import datetime, logging

import boto3

from . import credentials as cred
from . import cloudformation as cfn, sts


logger = logging.getLogger(__name__)


def get_client(cred_keys: dict = {}):
    return cred.get_client("ecs", cred_keys)


def describe_tasks(
        resource_group,
        region,
        running=True,
        stopped=True,
        extras=None,
        cred_keys: dict = {},
        ):
    client = get_client(cred_keys=cred_keys)
    account_id = sts.get_account_id(cred_keys=cred_keys)
    cluster = f"arn:aws:ecs:{region}:{account_id}:cluster/{resource_group}"
    task_arns = []
    if stopped:
        response = client.list_tasks(cluster=cluster, desiredStatus="STOPPED")
        task_arns = task_arns + response["taskArns"]
    if running:
        response = client.list_tasks(cluster=cluster, desiredStatus="RUNNING")
        task_arns = task_arns + response["taskArns"]
    tasks = [t for t in task_arns]
    if not tasks:
        return None
    response = client.describe_tasks(cluster=cluster, tasks=tasks)
    return response


def stop_task(resource_group, region, task_id, reason, extras=None,
        cred_keys: dict = {}):
    client = get_client(cred_keys=cred_keys)
    account_id = sts.get_account_id(cred_keys=cred_keys)
    cluster = f"arn:aws:ecs:{region}:{account_id}:cluster/{resource_group}"
    response = client.stop_task(cluster=cluster, task=task_id, reason=reason)
    return response


def run_fargate_task(
        account_id,
        task_stack,
        resource_group_stack,
        container_image,
        region,
        env=[], extras=None, cred_keys: dict = {}):
    """Run a fargate task
    extras overwrite the kwargs given to run_task boto3 command.
    See: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html#ECS.Client.run_task
    """
    env.append({"name": "TASK_TRIGGERED_AT",
                "value": datetime.datetime.utcnow().isoformat()})
    client = get_client(cred_keys=cred_keys)

    rg_resources = cfn.describe_stack_resources(
        resource_group_stack,
        cred_keys=cred_keys,
    )["StackResources"]

    task_resources = cfn.describe_stack_resources(
        task_stack,
        cred_keys=cred_keys,
    )["StackResources"]
    task_def_arn = None
    for r in task_resources:
        if r["ResourceType"] == "AWS::ECS::TaskDefinition":
            task_def_arn = r["PhysicalResourceId"]
            break

    rg_resources = cfn.describe_stack_resources(
        resource_group_stack,
        cred_keys=cred_keys,
    )["StackResources"]
    cluster_arn = None
    subnets = list()
    security_groups =list()
    for r in rg_resources:
        # PublicSubnetTwo is for <= v0.3.4
        if (r["ResourceType"] == "AWS::EC2::Subnet" and
                r["LogicalResourceId"] in ["PublicSubnetTwo", "Subnet2"]):
            subnets.append(r["PhysicalResourceId"])
        if r["ResourceType"] == "AWS::EC2::SecurityGroup":
            security_groups.append(r["PhysicalResourceId"])
        if r["ResourceType"] == "AWS::ECS::Cluster":
            cluster_arn = "arn:aws:ecs:{region}:{account_id}:cluster/{phys_rsrc_id}".format(
                **{"region": region,
                   "account_id": account_id,
                   "phys_rsrc_id": r["PhysicalResourceId"]})

    logger.debug("%s\n%s\n%s\n%s" %
                 (cluster_arn, task_def_arn, subnets, security_groups))

    kwargs = {
        "cluster": cluster_arn,
        "taskDefinition": task_def_arn,
        "count": 1,
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
                 "name": container_image,
                 "environment": env
                 }
            ]
        }
    }
    if extras:
        kwargs.update(extras)

    return client.run_task(**kwargs)
