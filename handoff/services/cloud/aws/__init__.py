import datetime, json, logging, os, re, time
import yaml
import botocore
import dateutil

from handoff import utils
from handoff.config import (BUCKET, CONTAINER_IMAGE, IMAGE_DOMAIN,
                            IMAGE_VERSION, RESOURCE_GROUP, RESOURCE_GROUP_NAKED,
                            STAGE, TASK, TASK_NAKED, get_state)
from handoff.services.cloud.aws import (ecs, ecr, events, iam, logs, s3, ssm,
                                        sts, cloudformation)
from handoff.services.cloud.aws import credentials as cred


NAME = "aws"
TEMPLATE_DIR = "cloudformation_templates"
LOGGER = utils.get_logger()


boto3_logger = logging.getLogger("boto3")
boto3_logger.setLevel(LOGGER.level)
botocore_logger = logging.getLogger("botocore")
botocore_logger.setLevel(LOGGER.level)


def _get_cred_keys():
    state = get_state()
    cred_keys = {
        "aws_access_key_id": state["AWS_ACCESS_KEY_ID"],
        "aws_secret_access_key": state["AWS_SECRET_ACCESS_KEY"],
        "aws_session_token": state.get("AWS_SESSION_TOKEN"),
        "aws_region": state.get("AWS_REGION"),
    }
    return cred_keys


def _log_stack_info(response):
    state = get_state()
    params = {"stack_id": response["StackId"],
              "region": state["AWS_REGION"]}
    return (("Check the progress at https://console.aws.amazon.com/" +
           "cloudformation/home?region={region}#/stacks/stackinfo" +
           "?viewNested=true&hideStacks=false" +
           "&stackId={stack_id}").format(**params))


def _log_stack_filter(stack_name):
    state = get_state()
    params = {"stack_name": stack_name, "region": state["AWS_REGION"]}
    return (("Check the progress at https://console.aws.amazon.com/" +
           "cloudformation/home?region={region}#/stacks/stackinfo" +
           "?filteringText={stack_name}").format(**params))


def _log_task_run_filter(task_name, response):
    state = get_state()
    task_arn = response["tasks"][0]["taskArn"]
    task_name_id = task_arn[task_arn.find("task/") + len("task/"):]
    task_id = task_name_id[task_name_id.find("/") + 1:]
    params = {"task": task_name,
              "region": state["AWS_REGION"],
              "task_id": task_id}
    return (("Check the task at https://us-east-1.console.aws.amazon.com/ecs/home?region=" +
           "{region}#/clusters/{task}/tasks/{task_id}").format(**params))


def _assume_role(
        role_arn=None,
        target_account_id=None,
        external_id=None,
        cred_keys: dict = {},
        ):
    state = get_state()
    if not role_arn:
        account_id = sts.get_account_id(cred_keys=cred_keys)
        resource_group = state.get(RESOURCE_GROUP)
        role_name = ("FargateDeployRole-%s-%s" %
                     (resource_group, account_id))
        if not target_account_id:
            target_account_id = account_id
        role_arn = (f"arn:aws:iam::{target_account_id}:role/{role_name}")
    response = sts.assume_role(role_arn, external_id=external_id, cred_keys=cred_keys)

    state["AWS_ACCESS_KEY_ID"] = response["Credentials"]["AccessKeyId"]
    state["AWS_SECRET_ACCESS_KEY"] = response["Credentials"]["SecretAccessKey"]
    state["AWS_SESSION_TOKEN"] = response["Credentials"]["SessionToken"]

    return response


def set_log_level(log_level=logging.WARNING):
    logging.getLogger("boto").setLevel(log_level)


def find_cred_keys(vars_: dict):
    cred = {}
    valid_keys = [
        "aws_access_key_id",
        "aws_secret_access_key",
        "aws_region",
        "aws_session_token",
        "role_arn",
        "external_id",
    ]
    for key in vars_:
        if key in valid_keys:
            cred[key] = vars_[key]
    if not cred.get("role_arn") and cred.get("external_id"):
        cred.pop("external_id")
    return cred


def login(
        profile=None,
        cred_keys: dict = {},
        ):
    state = get_state()
    if cred_keys.get("role_arn"):
        try:
            _assume_role(
                    cred_keys["role_arn"],
                    external_id=cred_keys["external_id"],
                    cred_keys=cred_keys)
        except Exception as e:
            LOGGER.error(str(e))
            raise
        cred_keys["aws_access_key_id"] = state["AWS_ACCESS_KEY_ID"]
        cred_keys["aws_secret_access_key"] = state["AWS_SECRET_ACCESS_KEY"]
        cred_keys["aws_session_token"] = state["AWS_SESSION_TOKEN"]
    elif profile:
        state.set_env("AWS_PROFILE", profile)
        LOGGER.debug("AWS_PROFILE set to " + state.get("AWS_PROFILE"))

    try:
        account_id = sts.get_account_id(cred_keys)
        state["AWS_ACCOUNT_ID"] = account_id
        if cred_keys.get("aws_region"):
            state["AWS_REGION"] = cred_keys["aws_region"]
        else:
            default_region = sts.get_default_region(cred_keys)
            LOGGER.info(f"Default AWS Region is set to {default_region}")
            if default_region:
                state["AWS_REGION"] = default_region
        state["AWS_ACCESS_KEY_ID"] = cred_keys.get("aws_access_key_id")
        state["AWS_SECRET_ACCESS_KEY"] = cred_keys.get("aws_secret_access_key")
        state["AWS_SESSION_TOKEN"] = cred_keys.get("aws_session_token")
        return account_id
    except Exception as e:
        LOGGER.warning(str(e))
        return None


def get_account_id():
    state = get_state()
    return state["AWS_ACCOUNT_ID"]


def get_platform_auth_env():
    state = get_state()
    env = {"AWS_ACCESS_KEY_ID": state.get("AWS_ACCESS_KEY_ID"),
           "AWS_SECRET_ACCESS_KEY": state.get("AWS_SECRET_ACCESS_KEY"),
           "AWS_SESSION_TOKEN": state.get("AWS_SESSION_TOKEN"),
           "AWS_REGION": state.get("AWS_REGION")
           }
    return env


def get_parameter_key_full_path(key, resource_group_level=False):
    state = get_state()
    if resource_group_level:
        prefix_key = "/" + state.get(RESOURCE_GROUP) + "/" + key
    else:
        prefix_key = (
                "/" + state.get(RESOURCE_GROUP) + "/" + state.get(TASK_NAKED) +
                "/" + key)
    return prefix_key


def get_parameter(key, resource_group_level=False):
    prefix_key = get_parameter_key_full_path(key, resource_group_level)
    value = None
    try:
        value = ssm.get_parameter(prefix_key, cred_keys=_get_cred_keys())
    except Exception as e:
        LOGGER.error("Cannot get %s - %s" % (prefix_key, str(e)))
        LOGGER.error("See the parameters at https://console.aws.amazon.com/" +
                     "systems-manager/parameters/?region=" +
                     state.get("AWS_REGION") +
                     "&tab=Table#list_parameter_filters=Name:Contains:" +
                     prefix_key)
    # Parameter Store does not allow {{}}. Unescaping.
    if value:
        value = value.replace("\{\{", "{{").replace("\}\}", "}}")
    return value


def get_all_parameters():
    state = get_state()
    params = {}
    path = "/" + state.get(RESOURCE_GROUP)
    cred_keys = _get_cred_keys()
    raw_params = ssm.get_parameters_by_path(path, cred_keys=cred_keys)
    for p in raw_params:
        value = raw_params[p]
        # Parameter Store does not allow {{}}. Unescaping.
        value = value.replace("\{\{", "{{").replace("\}\}", "}}")
        key = p.split("/")[-1]
        params[key] = {"value": value, "path": p}

    path = path + "/" + state.get(TASK_NAKED)
    raw_params = ssm.get_parameters_by_path(path, cred_keys=cred_keys)
    for p in raw_params:
        value = raw_params[p]
        # Parameter Store does not allow {{}}. Unescaping.
        value = value.replace("\{\{", "{{").replace("\}\}", "}}")
        key = p.split("/")[-1]
        params[key] = {"value": value, "path": p}
    return params


def push_parameter(
        key,
        value,
        allow_advanced_tier=False,
        resource_group_level=False,
        **kwargs):
    state = get_state()
    state.validate_env([RESOURCE_GROUP, TASK, "AWS_REGION"])

    prefix_key = get_parameter_key_full_path(key, resource_group_level)

    if allow_advanced_tier:
        LOGGER.debug("Allowing AWS SSM Parameter Store to store with " +
                     "Advanced tier (max 8KB)")
    # Parameter Store does not allow {{}}. Escaping.
    value = value.replace("{{", "\{\{").replace("}}", "\}\}")
    tier = "Standard"
    if len(value) > 8192:
        raise Exception("Parameter string must be less than 8192kb!")
    if len(value) > 4096:
        if allow_advanced_tier:
            tier = "Advanced"
        else:
            raise Exception(("Parameter string is %s > 4096 byte. " +
                             "You must use -d allow_advanced_tier=true option.") % len(value))
    LOGGER.debug("Putting parameter %s to AWS SSM Parameter Store with %s tier" %
                 (prefix_key, tier))
    details = ssm.put_parameter(prefix_key, value, cred_keys=_get_cred_keys(), tier=tier)
    response = {
        "status": "success",
        "instructions": (
            "See the parameters at https://console.aws.amazon.com/"
            f"systems-manager/parameters/?region={state.get('AWS_REGION')}"
            f"&tab=Table#list_parameter_filters=Name:Contains:{prefix_key}"
        ),
        "details": details
    }
    return response


def delete_parameter(
        key,
        resource_group_level=False,
        **kwargs):
    prefix_key = get_parameter_key_full_path(key, resource_group_level)
    ssm.delete_parameter(prefix_key, cred_keys=_get_cred_keys())


def download_file(local_path, remote_path):
    state = get_state()
    bucket = state.get(BUCKET)
    remote_path = os.path.join(state.get(TASK_NAKED), remote_path)
    s3.download_file(bucket, local_path, remote_path, cred_keys=_get_cred_keys())


def upload_file(local_path, remote_path):
    state = get_state()
    bucket = state.get(BUCKET)
    remote_path = os.path.join(state.get(TASK_NAKED), remote_path)
    s3.upload_file(bucket, local_path, remote_path, cred_keys=_get_cred_keys())


def delete_file(remote_path):
    state = get_state()
    bucket = state.get(BUCKET)
    remote_path = os.path.join(state.get(TASK_NAKED), remote_path)
    s3.delete_file(bucket, remote_path, cred_keys=_get_cred_keys())


def download_dir(local_dir_path, remote_dir_path):
    state = get_state()
    bucket = state.get(BUCKET)
    remote_dir_path = os.path.join(state.get(TASK_NAKED), remote_dir_path)
    s3.download_dir(bucket, local_dir_path, remote_dir_path, cred_keys=_get_cred_keys())


def upload_dir(local_dir_path, remote_dir_path):
    state = get_state()
    state.validate_env([BUCKET, "AWS_REGION"])
    bucket = state.get(BUCKET)
    dest_prefix = os.path.join(state.get(TASK_NAKED), remote_dir_path)
    s3.upload_dir(bucket, local_dir_path, dest_prefix, cred_keys=_get_cred_keys())
    response = {
        "status": "success",
        "instructions": (
            "See the files at https://s3.console.aws.amazon.com/s3/"
            f"buckets/{bucket}/{dest_prefix}/"
        )
    }
    return response


def delete_dir(remote_dir_path):
    state = get_state()
    bucket = state.get(BUCKET)
    remote_dir = os.path.join(state.get(TASK_NAKED), remote_dir_path)
    s3.delete_recurse(bucket, remote_dir, cred_keys=_get_cred_keys())


def copy_dir_to_another_bucket(src_dir, dest_dir):
    state = get_state()
    bucket = state.get(BUCKET)
    src_prefix = os.path.join(state.get(TASK_NAKED), src_dir)
    dest_prefix = os.path.join(state.get(TASK_NAKED), dest_dir)
    s3.copy_dir_to_another_bucket(bucket, src_prefix,
                                  bucket, dest_prefix, cred_keys=_get_cred_keys())


def get_latest_container_image_version(image_name):
    return ecr.get_latest_version(
            image_name,
            cred_keys=_get_cred_keys(),
            )


def get_docker_registry_credentials(registry_id=None):
    if not registry_id:
        registry_id = get_account_id()
    return ecr.get_docker_registry_credentials(
            registry_id,
            cred_keys=_get_cred_keys(),
            )


def get_repository_images(image_name=None):
    state = get_state()
    if not image_name:
        image_name = state.get(CONTAINER_IMAGE)
    ecr_images = ecr.list_images(image_name, cred_keys=_get_cred_keys())
    if not ecr_images:
        return None
    images = [{"id": i["imageDigest"], "tag": i["imageTag"]} for i in ecr_images]
    return images


def create_repository(is_mutable=False):
    state = get_state()
    name = state.get(CONTAINER_IMAGE)
    ecr.create_repository(name, is_mutable, cred_keys=_get_cred_keys())


def create_role(
        grantee_account_id,
        external_id: str,
        template_file: str = None,
        update: bool = False):
    state = get_state()
    # resource_group = state.get(RESOURCE_GROUP)
    stack_name = "handoff-role-" + str(grantee_account_id)
    # stack_name = resource_group + "-role-" + str(grantee_account_id)
    if not template_file:
        aws_dir, _ = os.path.split(__file__)
        template_file = os.path.join(aws_dir, TEMPLATE_DIR, "role.yml")
    parameters = [
            # {"ParameterKey": "ResourceGroup", "ParameterValue": resource_group},
            {"ParameterKey": "GranteeAccountId", "ParameterValue": grantee_account_id},
            {"ParameterKey": "ExternalId", "ParameterValue": external_id},
    ]

    if not update:
        aws_response = cloudformation.create_stack(
                stack_name, template_file, parameters, cred_keys=_get_cred_keys())
    else:
        aws_response = cloudformation.update_stack(
                stack_name, template_file, parameters, cred_keys=_get_cred_keys())

    instructions = _log_stack_info(aws_response)

    account_id = get_account_id()
    role_name = f"handoff-FargateDeployRole-for-{grantee_account_id}"
    # role_name = f"{resource_group}-FargateDeployRole-for-{grantee_account_id}"
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"

    region = state.get("AWS_REGION")

    instructions = instructions + f"""\nAdd this info to ~/.aws/credentials (Linux & Mac)\n
%USERPROFILE%\\.aws\\credentials (Windows)

    [<new-profile-name>]
    source_profile = <aws_profile>
    role_arn = {role_arn}
    external_id = {external_id}
    region = {region}

And update the environment varialbe:
    export AWS_PROFILE=<new-profile-name> (Linux & Mac)
    setx AWS_PROFILE <new-profile-name> (Windows)

Learn more about AWS name profiles at
https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html
"""
    response = {
        "aws_response": aws_response,
        "account_id": account_id,
        "role_arn": role_arn,
        "external_id": external_id,
        "region": region,
        "instructions": instructions,
        }
    return response


def update_role(grantee_account_id, external_id, template_file=None):
    return create_role(grantee_account_id, external_id, template_file, update=True)


def delete_role(grantee_account_id, template_file=None):
    state = get_state()
    # resource_group = state.get(RESOURCE_GROUP)
    stack_name = "handoff-role-" + str(grantee_account_id)
    # stack_name = resource_group + "-role-" + str(grantee_account_id)
    response = cloudformation.delete_stack(stack_name, cred_keys=_get_cred_keys())
    instructions = _log_stack_filter(stack_name)
    response["instructions"] = instructions + "\nDon't forget to update ~/.aws/credentials and AWS_PROFILE"
    return response


def get_role_status(grantee_account_id):
    state = get_state()
    stack_name = "handoff-role-" + str(grantee_account_id)
    try:
        res = cloudformation.describe_stacks(stack_name, cred_keys=_get_cred_keys())
    except:
        status = {"status": "not created", "message": "role does not exist"}
    else:
        status = {
            "status": res["Stacks"][0]["StackStatus"],
            "details": res["Stacks"][0]
        }
    return status


def create_bucket(template_file=None, update=False):
    state = get_state()
    resource_group = state.get(RESOURCE_GROUP)
    bucket = state.get(BUCKET)
    stack_name = resource_group + "-bucket"
    if not template_file:
        aws_dir, _ = os.path.split(__file__)
        template_file = os.path.join(aws_dir, TEMPLATE_DIR, "s3.yml")
    parameters = [{"ParameterKey": "Bucket", "ParameterValue": bucket}]

    try:
        if not update:
            response = cloudformation.create_stack(stack_name, template_file, parameters, cred_keys=_get_cred_keys())
        else:
            response = cloudformation.update_stack(stack_name, template_file, parameters, cred_keys=_get_cred_keys())
    except botocore.exceptions.ClientError as e:
        # Bucket already exists
        LOGGER.error("Error creating/updating %s bucket: %s" %
                     (bucket, str(e)))
    else:
        response["instructions"] = _log_stack_info(response)
        return response


def update_bucket(template_file=None):
    create_bucket(template_file, update=True, cred_keys=_get_cred_keys())


def delete_bucket():
    state = get_state()
    LOGGER.warning("This will only delete the CloudFormation stack. " +
                   "The bucket %s will be retained." % state.get(BUCKET))
    resource_group = state.get(RESOURCE_GROUP)
    stack_name = resource_group + "-bucket"
    response = cloudformation.delete_stack(stack_name, cred_keys=_get_cred_keys())
    response["instructions"] = _log_stack_filter(state[BUCKET])
    return response


def get_bucket_status(**kwargs):
    state = get_state()
    resource_group = state.get(RESOURCE_GROUP)
    stack_name = resource_group + "-bucket"
    try:
        res = cloudformation.describe_stacks(stack_name, cred_keys=_get_cred_keys())
    except:
        status = {"status": "not created", "message": "bucket does not exist"}
    else:
        status = {
            "status": res["Stacks"][0]["StackStatus"],
            "details": res["Stacks"][0]
        }
    return status


def create_resources(template_file=None, update=False, static_ip=False,
        **kwargs):
    state = get_state()
    resource_group = state.get(RESOURCE_GROUP)
    stack_name = resource_group + "-resources"
    bucket = state.get(BUCKET)
    parameters = [
        {
            "ParameterKey": "ResourceGroup",
            "ParameterValue": resource_group,
        },
        {
            "ParameterKey": "Bucket",
            "ParameterValue": bucket,
        },
    ]
    if not template_file:
        aws_dir, _ = os.path.split(__file__)
        if static_ip:
            template_file = os.path.join(aws_dir, TEMPLATE_DIR, "resources_static_ip.yml")
        else:
            template_file = os.path.join(aws_dir, TEMPLATE_DIR, "resources.yml")

    if not update:
        response = cloudformation.create_stack(stack_name, template_file, parameters, cred_keys=_get_cred_keys())
    else:
        response = cloudformation.update_stack(stack_name, template_file, parameters, cred_keys=_get_cred_keys())

    response["instructions"] = _log_stack_info(response)
    return response


def update_resources(template_file=None, **kwargs):
    create_resources(template_file, update=True, **kwargs)


def delete_resources():
    state = get_state()
    resource_group = state.get(RESOURCE_GROUP)
    stack_name = resource_group + "-resources"
    response = cloudformation.delete_stack(stack_name, cred_keys=_get_cred_keys())
    response["instructions"] = _log_stack_filter(resource_group)
    return response


def get_resources_status(**kwargs):
    state = get_state()
    resource_group = state.get(RESOURCE_GROUP)
    stack_name = resource_group + "-resources"
    try:
        res = cloudformation.describe_stacks(stack_name, cred_keys=_get_cred_keys())
    except:
        status = {"status": "not created", "message": "resources do not exist"}
    else:
        status = {
            "status": res["Stacks"][0]["StackStatus"],
            "details": res["Stacks"][0]
        }
    return status


def create_task(template_file=None, update=False, memory=512,
                cpu=256, **kwargs):
    state = get_state()
    task_name = state.get(TASK)
    task_name_naked = state.get(TASK_NAKED)
    resource_group = state.get(RESOURCE_GROUP)
    resource_group_naked = state.get(RESOURCE_GROUP_NAKED)

    bucket = state.get(BUCKET)
    _, _, image_domain = get_docker_registry_credentials()
    container_image = state.get(CONTAINER_IMAGE)
    image_version = state.get(IMAGE_VERSION)

    parameters = [
        {
            "ParameterKey": "ResourceGroup",
            "ParameterValue": resource_group,
        },
        {
            "ParameterKey": "ResourceGroupNaked",
            "ParameterValue": resource_group_naked,
        },
        {
            "ParameterKey": "TaskName",
            "ParameterValue": task_name,
        },
        {
            "ParameterKey": "TaskNameNaked",
            "ParameterValue": task_name_naked,
        },
        {
            "ParameterKey": "Bucket",
            "ParameterValue": bucket,
            },
        {
            "ParameterKey": "ImageDomain",
            "ParameterValue": image_domain,
        },
        {
            "ParameterKey": "ImageName",
            "ParameterValue": container_image,
        },
        {
            "ParameterKey": "ImageVersion",
            "ParameterValue": image_version,
        },
        {
            "ParameterKey": "AllocatedCpu",
            "ParameterValue": str(cpu),
        },
        {
            "ParameterKey": "AllocatedMemory",
            "ParameterValue": str(memory),
        },
    ]

    if not template_file:
        aws_dir, _ = os.path.split(__file__)
        template_file = os.path.join(aws_dir, TEMPLATE_DIR, "task.yml")

    if not update:
        response = cloudformation.create_stack(
                resource_group + "-" + task_name_naked,
                template_file,
                parameters,
                cred_keys=_get_cred_keys(),
                )
    else:
        response = cloudformation.update_stack(
                resource_group + "-" + task_name_naked,
                template_file,
                parameters,
                cred_keys=_get_cred_keys(),
                )

    response["instructions"] = _log_stack_info(response)
    return response


def update_task(**kwargs):
    try:
        response = create_task(update=True, cred_keys=_get_cred_keys(), **kwargs)
    except botocore.exceptions.ClientError as e:
        LOGGER.error(e)
        return {
            "status": "error",
            "message": str(e),
            }
    response["message"] = ("Make sure to run `handoff cloud schedule` command" +
                           " to bump up the task version")
    return response


def delete_task():
    state = get_state()
    task_name = state.get(TASK)
    task_name_naked = state.get(TASK_NAKED)
    resource_group = state.get(RESOURCE_GROUP)
    response = cloudformation.delete_stack(
            resource_group + "-" + task_name_naked,
            cred_keys=_get_cred_keys(),
            )
    response["instructions"] = _log_stack_filter(resource_group + "-" + task_name_naked)
    return response


def get_task_status(**kwargs):
    state = get_state()
    resource_group = state.get(RESOURCE_GROUP)
    task_name = state.get(TASK_NAKED)
    stack_name = resource_group + "-" + task_name
    try:
        res = cloudformation.describe_stacks(stack_name, cred_keys=_get_cred_keys())
    except:
        status = {"status": "not created", "message": "task does not exist"}
    else:
        status = {
            "status": res["Stacks"][0]["StackStatus"],
            "details": res["Stacks"][0]
        }
    return status


def list_jobs(full=False, running=True, stopped=True,
               resource_group_level=False, **kwargs):
    state = get_state()
    stack_name = state.get(TASK_NAKED)
    resource_group = state.get(RESOURCE_GROUP)
    region = state.get("AWS_REGION")
    try:
        response = ecs.describe_tasks(
                resource_group + "-resources",
                region,
                running=running,
                stopped=stopped,
                cred_keys=_get_cred_keys(),
            )
    except Exception as e:
        response = {"status": "error", "message": str(e)}
        return response

    outputs = []
    digest = ["taskArn", "taskDefinitionArn", "lastStatus", "createdAt", "startedAt", "cpu", "memory"]
    if not response:
        return None
    for task in response["tasks"]:
        output = {}
        t = task["taskDefinitionArn"].split(":")[-2].split("/")[-1]
        if not resource_group_level and t != resource_group + "-" + stack_name:
            continue
        if not full:
            for item in digest:
                output[item] = task.get(item)
        else:
            output = task
        if output["lastStatus"] == "RUNNING":
            output["timeSinceStart"] = str(
                datetime.datetime.utcnow().replace(
                    tzinfo=datetime.timezone.utc) - task["startedAt"])
        elif output["lastStatus"] == "STOPPED":
            if task.get("executionStoppedAt") and task.get("startedAt"):
                output["duration"] = str(task["executionStoppedAt"] - task["startedAt"])
            elif task.get("startedAt"):
                output["duration"] = output["timeSinceStart"]
            else:
                output["duration"] = None

        outputs.append(output)
    return outputs


def stop_job(id=None, reason="Stopped by the user"):
    if not id:
        return({"success": False,
                "message": "You must provide task ID by -v id=<arn or task id>"})
    state = get_state()
    resource_group = state.get(RESOURCE_GROUP)
    region = state.get("AWS_REGION")
    response = ecs.stop_task(resource_group + "-resources", region, id, reason, cred_keys=_get_cred_keys())
    return response


def run_job(task_name=None, container_name=None, env={}, command=None, extras=None):
    state = get_state()
    account_id = state["AWS_ACCOUNT_ID"]
    if not task_name:
        task_name = state.get(TASK_NAKED)
    if not container_name:
        container_name = state.get(CONTAINER_IMAGE)
    region = state.get("AWS_REGION")
    resource_group = state.get(RESOURCE_GROUP)
    resource_group_stack = resource_group + "-resources"

    extra_env = []
    for key in env.keys():
        extra_env.append({"name": key, "value": env[key]})
    response = ecs.run_fargate_task(
            account_id,
            resource_group + "-" + task_name,
            resource_group_stack,
            container_name,
            region,
            extra_env,
            command=command,
            extras=extras,
            cred_keys=_get_cred_keys())
    response["instructions"] = _log_task_run_filter(
        state[RESOURCE_GROUP] + "-resources", response)
    return response


def schedule_job(target_id, cronexp, env=[], role_arn=None, state_machine=True,
        extras=None):
    state = get_state()
    account_id = state["AWS_ACCOUNT_ID"]
    task_stack = state.get(RESOURCE_GROUP) + "-" + state.get(TASK_NAKED)
    container_image = state.get(CONTAINER_IMAGE)
    region = state.get("AWS_REGION")
    resource_group_stack = state.get(RESOURCE_GROUP) + "-resources"

    role_name = "handoff-CloudWatchEventECSRole"

    if not role_arn:
        roles = iam.list_roles(cred_keys=_get_cred_keys())
        for r in roles:
            if r["RoleName"] == role_name:
                role_arn = r["Arn"]
                break
    if not role_arn:
        raise Exception("Role %s not found" % role_name)

    extra_env = []
    for key in env.keys():
        extra_env.append({"Name": key, "Value": env[key]})
    try:
        response = events.schedule_job(
                account_id,
                task_stack,
                resource_group_stack,
                container_image,
                region,
                target_id,
                cronexp,
                role_arn,
                env=extra_env,
                state_machine=state_machine,
                extras=extras,
                cred_keys=_get_cred_keys(),
                )
    except Exception as e:
        LOGGER.error("Scheduling task failed for %s target_id: %s cron: %s" %
                     (task_stack, target_id, cronexp))
        LOGGER.critical(str(e))
        return

    region= state.get("AWS_REGION")
    resource_group = state.get(RESOURCE_GROUP)
    response["instructions"] = (
        "Check the status at https://console.aws.amazon.com/ecs/"
        f"home?region={region}#/clusters/{resource_group}-resources"
        "/scheduledTasks\n"
        "For state machine enabled tasks, check the schedules at"
        f"https://console.aws.amazon.com/cloudwatch/home?region={region}#rules:")
    return response


def unschedule_job(target_id):
    state = get_state()
    task_stack = state.get(RESOURCE_GROUP) + "-" + state.get(TASK_NAKED)
    try:
        response = events.unschedule_job(
                task_stack,
                target_id,
                cred_keys=_get_cred_keys(),
        )
    except Exception as e:
        raise Exception(f"No schedules found: {str(e)}")

    region = state.get("AWS_REGION")
    resource_group = state.get(RESOURCE_GROUP)
    response["instructions"] = (
        "Check the status at https://console.aws.amazon.com/ecs/"
        f"home?region={region}#/clusters/{resource_group}-resources"
        "/scheduledTasks")
    return response


def list_schedules(full=False, **kwargs):
    state = get_state()
    task_stack = state.get(RESOURCE_GROUP) + "-" + state.get(TASK_NAKED)
    try:
        response = events.list_schedules(task_stack, cred_keys=_get_cred_keys())
    except Exception as e:
        LOGGER.error(e)
        response = []
    schedules = list()
    for r in response:
        record = {
            "name": r["rule"]["Name"],
            "cron": re.sub(r"cron\((.*)\)", "\\1",
                           r["rule"]["ScheduleExpression"])
        }
        if full:
            record.update(r)
        if not r["targets"]:
            LOGGER.warning("Rule %s has no target!" % record["name"])
            continue
        # One rule, one target
        record["target_id"] = str(r["targets"][0]["Id"])
        input_str = r["targets"][0].get("Input")
        if input_str:
            input_ = json.loads(input_str.replace("\\\\", ""))
            coverrides = input_.get("containerOverrides", input_.get("ContainerOverrides", None))
            LOGGER.debug(coverrides)
            if coverrides:
                envs = coverrides[0].get("environment", coverrides[0].get("Environment", None))
                if envs:
                    record["envs"] = [{
                        "key": e.get("name", e.get("Name", None)),
                        "value": e.get("value", e.get("Value", None)),
                        } for e in envs if e.get("name", e.get("Name", None)) != STAGE]
        schedules.append(record)
    yml_clean = re.sub(r"'([a-zA-Z_]*)':",
                       "\\1:",
                       yaml.dump({"schedules": schedules}, default_style="'"))
    return yaml.load(yml_clean, Loader=yaml.FullLoader)


def _find_json(string):
    pos = string.find("{")
    if pos > -1:
        json_str = string[pos:]
        try:
            obj = json.loads(json_str)
        except Exception:
            return None
        return obj
    return None


def _write_log(file_descriptor, event, format_):
    if format_ == "json":
        obj = _find_json(event["message"])
        if obj is not None:
            file_descriptor.write(
                json.dumps({"datetime": event["datetime"].isoformat(),
                            "message": obj}) + "\n")
    else:
        file_descriptor.write(format_.format(**event) + "\n")


def write_logs(
    file_descriptor,
    start_time=None,
    end_time=None,
    filter_pattern=None,
    format_=None,
    follow=False,
    wait=2.5,
    last_timestamp=None,
    **extras
):
    state = get_state()
    log_group_name = state.get(RESOURCE_GROUP) + "/" + state.get(TASK_NAKED)


    if start_time and type(start_time) is str:
        start_time = dateutil.parser.parse(start_time)
    if end_time and type(end_time) is str:
        end_time = dateutil.parser.parse(end_time)

    if not format_:
        format_ = "{datetime} - {message}"

    while True:
        try:
            response = logs.filter_log_events(log_group_name,
                                              start_time=start_time,
                                              end_time=end_time,
                                              filter_pattern=filter_pattern,
                                              extras=extras,
                                              cred_keys=_get_cred_keys())
        except Exception as e:
            LOGGER.error(e)
            response = {"status": "error", "message": str(e)}
            return response

        show = False
        for e in response.get("events", list()):
            e["datetime"] = datetime.datetime.fromtimestamp(e["timestamp"] / 1000)
            start_time = e["timestamp"]
            if show or last_timestamp is None or last_timestamp < e["timestamp"]:
                show = True
                wait = 2.5
                last_timestamp = e["timestamp"]
                _write_log(file_descriptor, e, format_=format_)

        next_token = response.get("nextToken")
        while next_token:
            response = logs.filter_log_events(log_group_name,
                                              next_token=next_token,
                                              filter_pattern=filter_pattern,
                                              extras=extras,
                                              cred_keys=_get_cred_keys())
            for e in response.get("events", list()):
                e["datetime"] = datetime.datetime.fromtimestamp(
                    e["timestamp"] / 1000)
                start_time = e["timestamp"]
                if show or last_timestamp < e["timestamp"]:
                    show = True
                    wait = 2.5
                    last_timestamp = e["timestamp"]
                    _write_log(file_descriptor, e, format_=format_)
            next_token = response.get("nextToken")

        if not follow:
            break

        time.sleep(wait)
        wait = min(wait * 2, 60)

    return start_time
