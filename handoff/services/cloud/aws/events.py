import json, logging, os

import boto3

from . import credentials as cred
from . import cloudformation as cfn, iam, sts, stepfunctions as stepfns

from handoff import utils


LOGGER = utils.get_logger()


def get_client(cred_keys: dict = {}):
    return cred.get_client("events", cred_keys)


def schedule_job(
        account_id,
        task_stack,
        resource_group_stack,
        container_image,
        region,
        target_id,
        cronexp,
        role_arn,
        env=[],
        state_machine=True,
        state_machine_timeout=3600 * 4,
        extras=None,
        cred_keys: dict = {},
        **kwargs):
    """Schedule a task
    extras overwrite the kwargs given to put_targets boto3 command.
    See: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/events.html#EventBridge.Client.put_targets
    """
    client = get_client(cred_keys)

    rule_name = task_stack + "-" + target_id

    rule_kwargs = {
        "Name": rule_name,
        "ScheduleExpression": cronexp
    }
    client.put_rule(**rule_kwargs)

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
    security_groups = list()
    for r in rg_resources:
        if not cluster_arn and r["ResourceType"] == "AWS::ECS::Cluster":
            phys_rsrc_id= r["PhysicalResourceId"]
            cluster_arn = f"arn:aws:ecs:{region}:{account_id}:cluster/{phys_rsrc_id}"
        # PublicSubnetTwo is <= v0.3.4
        elif (r["ResourceType"] == "AWS::EC2::Subnet" and
                r["LogicalResourceId"] in ["PublicSubnetTwo", "Subnet2"]):
            subnets.append(r["PhysicalResourceId"])
        elif r["ResourceType"] == "AWS::EC2::SecurityGroup":
            security_groups.append(r["PhysicalResourceId"])

    task_resources = cfn.describe_stack_resources(
            task_stack,
            cred_keys=cred_keys,
        )["StackResources"]
    log_group_arn = None
    for r in task_resources:
        if r["ResourceType"] == "AWS::Logs::LogGroup":
            phys_rsrc_id = r["PhysicalResourceId"]
            log_group_arn = f"arn:aws:logs:{region}:{account_id}:log-group:{phys_rsrc_id}:*"

    LOGGER.debug(f"{cluster_arn}\n{task_def_arn}\n{subnets}\n{security_groups}\n{log_group_arn}")

    overrides = {
        "ContainerOverrides": [{
            "Name": container_image,
            "Environment": env,
        }]
    }

    if state_machine:
        sm_arn = stepfns.create_state_machine(
            rule_name,
            cluster_arn,
            task_def_arn,
            subnets,
            security_groups,
            role_arn,
            overrides=overrides,
            log_group_arn=log_group_arn,
            timeout=state_machine_timeout,
            cred_keys=cred_keys,
            **kwargs,
        )
        target = {
            "Id": target_id,
            "Arn": sm_arn,
            "RoleArn": role_arn,
            "Input": json.dumps(overrides),
        }
    else:
        target = {
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
            "Input": json.dumps(overrides)
        }

    rule_kwargs = {
        "Rule": rule_name,
        "Targets": [target]
    }

    if extras:
        rule_kwargs.update(extras)

    return client.put_targets(**rule_kwargs)


def unschedule_job(
        task_stack,
        target_id,
        cred_keys: dict = {}):
    client = get_client(cred_keys)
    rule_name = task_stack + "-" + target_id
    targets = client.list_targets_by_rule(Rule=rule_name)
    target_ids = []
    for target in targets["Targets"]:
        target_ids.append(target["Id"])
        if "stateMachine" in target["Arn"]:
            LOGGER.debug(f"Removing stepfunction {target['Arn']}")
            stepfns.delete_state_machine(
                target["Arn"],
                cred_keys=cred_keys,
            )

    kwargs = {
        "Rule": rule_name,
        "Ids": target_ids
    }
    client.remove_targets(**kwargs)
    client.delete_rule(Name=rule_name)


def list_schedules(
        task_stack,
        cred_keys: dict = {},
        ):
    client = get_client(cred_keys)
    rule_prefix = task_stack
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
