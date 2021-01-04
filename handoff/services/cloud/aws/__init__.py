import datetime, json, logging, os, re, time
import yaml
import botocore
import dateutil

from handoff import utils
from handoff.config import (BUCKET, CONTAINER_IMAGE, IMAGE_DOMAIN,
                            IMAGE_VERSION, RESOURCE_GROUP, STAGE, TASK,
                            get_state)
from handoff.services.cloud.aws import (ecs, ecr, events, iam, logs, s3, ssm,
                                        sts, cloudformation)
from handoff.services.cloud.aws import credentials as cred


logging.getLogger("boto").setLevel(logging.WARNING)

NAME = "aws"
TEMPLATE_DIR = "cloudformation_templates"
LOGGER = utils.get_logger()


boto3_logger = logging.getLogger("boto3")
boto3_logger.setLevel(LOGGER.level)
botocore_logger = logging.getLogger("botocore")
botocore_logger.setLevel(LOGGER.level)


def _log_stack_info(response):
    state = get_state()
    params = {"stack_id": response["StackId"],
              "region": state["AWS_REGION"]}
    print(("Check the progress at https://console.aws.amazon.com/" +
           "cloudformation/home?region={region}#/stacks/stackinfo" +
           "?viewNested=true&hideStacks=false" +
           "&stackId={stack_id}").format(**params))


def _log_stack_filter(stack_name):
    state = get_state()
    params = {"stack_name": stack_name, "region": state["AWS_REGION"]}
    print(("Check the progress at https://console.aws.amazon.com/" +
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
    print(("Check the task at https://us-east-1.console.aws.amazon.com/ecs/home?region=" +
           "{region}#/clusters/{task}/tasks/{task_id}").format(**params))


def login(profile=None):
    state = get_state()
    if profile:
        state.set_env("AWS_PROFILE", profile)
        LOGGER.debug("AWS_PROFILE set to " + state.get("AWS_PROFILE"))

    region = cred.get_region()
    if region:
        state.set_env("AWS_REGION", region)

    try:
        account_id = sts.get_account_id()
        LOGGER.debug("You have the access to AWS resources.")
        return account_id
    except Exception:
        return None


def get_platform_auth_env(data):
    state = get_state()
    if not state.get("AWS_ACCESS_KEY_ID"):
        try:
            role_arn = data.get("role_arn")
            target_account_id = data.get("target_account_id")
            external_id = data.get("external_id")
            assume_role(role_arn, target_account_id, external_id)
        except botocore.exceptions.ClientError:
            get_session()
    env = {"AWS_ACCESS_KEY_ID": state.get("AWS_ACCESS_KEY_ID"),
           "AWS_SECRET_ACCESS_KEY": state.get("AWS_SECRET_ACCESS_KEY"),
           "AWS_SESSION_TOKEN": state.get("AWS_SESSION_TOKEN"),
           "AWS_REGION": state.get("AWS_REGION")
           }
    return env


def get_session():
    state = get_state()
    session = cred.get_session()
    keys = session.get_credentials()
    state.set_env("AWS_ACCESS_KEY_ID",
                  keys.access_key,
                  trust=True)
    state.set_env("AWS_SECRET_ACCESS_KEY",
                  keys.secret_key,
                  trust=True)
    if keys.token:
        state.set_env("AWS_SESSION_TOKEN",
                      keys.token,
                      trust=True)


def assume_role(role_arn=None, target_account_id=None,  external_id=None):
    state = get_state()
    if not role_arn:
        account_id = sts.get_account_id()
        resource_group = state.get(RESOURCE_GROUP)
        role_name = ("FargateDeployRole-%s-%s" %
                     (resource_group, account_id))
        if not target_account_id:
            target_account_id = account_id
        params = {
            "role_name": role_name,
            "target_account_id": target_account_id
        }
        role_arn = ("arn:aws:iam::{target_account_id}:" +
                    "role/{role_name}").format(**params)
    response = sts.assume_role(role_arn, external_id=external_id)

    state.set_env("AWS_ACCESS_KEY_ID", response["Credentials"]["AccessKeyId"],
                  trust=True)
    state.set_env("AWS_SECRET_ACCESS_KEY",
                  response["Credentials"]["SecretAccessKey"], trust=True)
    state.set_env("AWS_SESSION_TOKEN", response["Credentials"]["SessionToken"],
                  trust=True)

    return response


def get_parameter(key, resource_group_level=False):
    state = get_state()
    if resource_group_level:
        prefix_key = "/" + state.get(RESOURCE_GROUP) + "/" + key
    else:
        prefix_key = ("/" + state.get(RESOURCE_GROUP) + "/" + state.get(TASK) +
                      "/" + key)

    value = None
    try:
        value = ssm.get_parameter(prefix_key)
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
    raw_params = ssm.get_parameters_by_path(path)
    for p in raw_params:
        value = raw_params[p]
        # Parameter Store does not allow {{}}. Unescaping.
        value = value.replace("\{\{", "{{").replace("\}\}", "}}")
        key = p.split("/")[-1]
        params[key] = {"value": value, "path": p}

    path = path + "/" + state.get(TASK)
    raw_params = ssm.get_parameters_by_path(path)
    for p in raw_params:
        value = raw_params[p]
        # Parameter Store does not allow {{}}. Unescaping.
        value = value.replace("\{\{", "{{").replace("\}\}", "}}")
        key = p.split("/")[-1]
        params[key] = {"value": value, "path": p}
    return params


def push_parameter(key, value, allow_advanced_tier=False,
                   resource_group_level=False, **kwargs):
    state = get_state()
    state.validate_env([RESOURCE_GROUP, TASK, "AWS_REGION"])

    if resource_group_level:
        prefix_key = "/" + state.get(RESOURCE_GROUP) + "/" + key
    else:
        prefix_key = ("/" + state.get(RESOURCE_GROUP) + "/" + state.get(TASK) +
                      "/" + key)

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
    ssm.put_parameter(prefix_key, value, tier=tier)
    print("See the parameters at https://console.aws.amazon.com/" +
          "systems-manager/parameters/?region=" +
          state.get("AWS_REGION") +
          "&tab=Table#list_parameter_filters=Name:Contains:" +
          prefix_key)


def delete_parameter(key, resource_group_level=False, **kwargs):
    state = get_state()

    if resource_group_level:
        prefix_key = "/" + state.get(RESOURCE_GROUP) + "/" + key
    else:
        prefix_key = ("/" + state.get(RESOURCE_GROUP) + "/" + state.get(TASK) +
                      "/" + key)

    ssm.delete_parameter(prefix_key)


def set_env_var_from_ssm(project, name):
    """
    Not used?
    """
    state = get_state()
    value = get_parameter(project, name)
    state.set_env(name, value, trust=True)


def download_file(local_path, remote_path):
    state = get_state()
    bucket = state.get(BUCKET)
    remote_path = os.path.join(state.get(TASK), remote_path)
    s3.download_file(bucket, local_path, remote_path)


def upload_file(local_path, remote_path):
    state = get_state()
    bucket = state.get(BUCKET)
    remote_path = os.path.join(state.get(TASK), remote_path)
    s3.upload_file(bucket, local_path, remote_path)


def delete_file(remote_path):
    state = get_state()
    bucket = state.get(BUCKET)
    remote_path = os.path.join(state.get(TASK), remote_path)
    s3.delete_file(bucket, remote_path)


def download_dir(local_dir_path, remote_dir_path):
    state = get_state()
    bucket = state.get(BUCKET)
    remote_dir_path = os.path.join(state.get(TASK), remote_dir_path)
    s3.download_dir(bucket, local_dir_path, remote_dir_path)


def upload_dir(local_dir_path, remote_dir_path):
    state = get_state()
    state.validate_env([BUCKET, "AWS_REGION"])
    bucket = state.get(BUCKET)
    dest_prefix = os.path.join(state.get(TASK), remote_dir_path)
    s3.upload_dir(bucket, local_dir_path, dest_prefix)
    print(("See the files at https://s3.console.aws.amazon.com/s3/" +
             "buckets/%s/%s/") % (bucket, dest_prefix))


def delete_dir(remote_dir_path):
    state = get_state()
    bucket = state.get(BUCKET)
    remote_dir = os.path.join(state.get(TASK), remote_dir_path)
    s3.delete_recurse(bucket, remote_dir)


def copy_dir_to_another_bucket(src_dir, dest_dir):
    state = get_state()
    bucket = state.get(BUCKET)
    src_prefix = os.path.join(state.get(TASK), src_dir)
    dest_prefix = os.path.join(state.get(TASK), dest_dir)
    s3.copy_dir_to_another_bucket(bucket, src_prefix,
                                  bucket, dest_prefix)


def get_account_id():
    return sts.get_account_id()


def get_docker_registry_credentials(registry_id=None):
    if not registry_id:
        registry_id = get_account_id()
    return ecr.get_docker_registry_credentials(registry_id)


def get_repository_images(image_name=None):
    state = get_state()
    if not image_name:
        image_name = state.get(CONTAINER_IMAGE)
    ecr_images = ecr.list_images(image_name)
    if not ecr_images:
        return None
    images = [{"id": i["imageDigest"], "tag": i["imageTag"]} for i in ecr_images]
    return images


def create_repository(is_mutable=False):
    state = get_state()
    name = state.get(CONTAINER_IMAGE)
    ecr.create_repository(name, is_mutable)


def create_role(grantee_account_id, external_id, template_file=None,
                update=False):
    state = get_state()
    resource_group = state.get(RESOURCE_GROUP)
    stack_name = resource_group + "-role-" + str(grantee_account_id)
    if not template_file:
        aws_dir, _ = os.path.split(__file__)
        template_file = os.path.join(aws_dir, TEMPLATE_DIR, "role.yml")
    parameters = [{"ParameterKey": "ResourceGroup",
                   "ParameterValue": resource_group},
                  {"ParameterKey": "GranteeAccountId",
                   "ParameterValue": grantee_account_id},
                  {"ParameterKey": "ExternalId",
                   "ParameterValue": external_id}
                  ]

    if not update:
        response = cloudformation.create_stack(stack_name, template_file,
                                               parameters)
    else:
        response = cloudformation.update_stack(stack_name, template_file,
                                               parameters)

    _log_stack_info(response)

    account_id = sts.get_account_id()
    role_name = ("FargateDeployRole-%s-%s" %
                 (resource_group, grantee_account_id))
    params = {
        "role_name": role_name,
        "account_id": account_id
    }
    role_arn = ("arn:aws:iam::{account_id}:" +
                "role/{role_name}").format(**params)
    print("""Add this info to ~/.aws/credentials (Linux & Mac)\n
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
""".format(**{"role_arn": role_arn, "external_id": external_id,
              "region": state.get("AWS_REGION")}))
    return response


def update_role(grantee_account_id, external_id, template_file=None):
    create_role(grantee_account_id, external_id, template_file, update=True)


def delete_role(grantee_account_id, template_file=None):
    state = get_state()
    resource_group = state.get(RESOURCE_GROUP)
    stack_name = resource_group + "-role-" + str(grantee_account_id)
    response = cloudformation.delete_stack(stack_name)
    _log_stack_filter(stack_name)
    print("Don't forget to update ~/.aws/credentials and AWS_PROFILE")
    return response


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
            response = cloudformation.create_stack(stack_name, template_file, parameters)
        else:
            response = cloudformation.update_stack(stack_name, template_file, parameters)
    except botocore.exceptions.ClientError as e:
        # Bucket already exists
        LOGGER.error("Error creating/updating %s bucket: %s" %
                     (bucket, str(e)))
    else:
        _log_stack_info(response)
        return response


def update_bucket(template_file=None):
    create_bucket(template_file, update=True)


def delete_bucket():
    state = get_state()
    LOGGER.warning("This will only delete the CloudFormation stack. " +
                   "The bucket %s will be retained." % state.get(BUCKET))
    resource_group = state.get(RESOURCE_GROUP)
    stack_name = resource_group + "-bucket"
    response = cloudformation.delete_stack(stack_name)
    _log_stack_filter(state[BUCKET])
    return response


def create_resources(template_file=None, update=False):
    state = get_state()
    resource_group = state.get(RESOURCE_GROUP)
    stack_name = resource_group + "-resources"
    if not template_file:
        aws_dir, _ = os.path.split(__file__)
        template_file = os.path.join(aws_dir, TEMPLATE_DIR, "resources.yml")

    if not update:
        response = cloudformation.create_stack(stack_name, template_file)
    else:
        response = cloudformation.update_stack(stack_name, template_file)

    _log_stack_info(response)
    return response


def update_resources(template_file=None):
    create_resources(template_file, update=True)


def delete_resources():
    state = get_state()
    resource_group = state.get(RESOURCE_GROUP)
    stack_name = resource_group + "-resources"
    response = cloudformation.delete_stack(stack_name)
    _log_stack_filter(resource_group)
    return response


def create_task(template_file=None, update=False, memory=512,
                cpu=256, **kwargs):
    state = get_state()
    stack_name = state.get(TASK)
    resource_group = state.get(RESOURCE_GROUP)
    bucket = state.get(BUCKET)
    _, _, image_domain = get_docker_registry_credentials()
    container_image = state.get(CONTAINER_IMAGE)
    image_version = state.get(IMAGE_VERSION)
    parameters = [
        {"ParameterKey": "ResourceGroup",
         "ParameterValue": resource_group},
        {"ParameterKey": "Bucket",
         "ParameterValue": bucket},
        {"ParameterKey": "ImageDomain",
         "ParameterValue": image_domain},
        {"ParameterKey": "ImageName",
         "ParameterValue": container_image},
        {"ParameterKey": "ImageVersion",
         "ParameterValue": image_version},
        {"ParameterKey": "AllocatedCpu",
         "ParameterValue": str(cpu)},
        {"ParameterKey": "AllocatedMemory",
         "ParameterValue": str(memory)}
    ]

    if not template_file:
        aws_dir, _ = os.path.split(__file__)
        template_file = os.path.join(aws_dir, TEMPLATE_DIR, "task.yml")

    if not update:
        response = cloudformation.create_stack(stack_name, template_file,
                                               parameters)
    else:
        response = cloudformation.update_stack(stack_name, template_file,
                                               parameters)

    _log_stack_info(response)
    return response


def update_task(**kwargs):
    try:
        response = create_task(update=True, **kwargs)
    except botocore.exceptions.ClientError as e:
        LOGGER.error(e)
        exit(1)
    print("Make sure to run `handoff cloud schedule` command to bump up " +
          "the task version")
    return response


def delete_task():
    state = get_state()
    stack_name = state.get(TASK)
    response = cloudformation.delete_stack(stack_name)
    _log_stack_filter(stack_name)
    return response


def list_tasks(full=False, resource_group_level=False):
    state = get_state()
    stack_name = state.get(TASK)
    resource_group = state.get(RESOURCE_GROUP)
    region = state.get("AWS_REGION")
    response = ecs.describe_tasks(resource_group + "-resources", region)
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
        outputs.append(output)
    return outputs


def run_task(env=[], extras=None):
    state = get_state()
    task_stack = state.get(TASK)
    container_image = state.get(CONTAINER_IMAGE)
    region = state.get("AWS_REGION")
    resource_group_stack = state.get(RESOURCE_GROUP) + "-resources"

    extra_env = []
    for key in env.keys():
        extra_env.append({"name": key, "value": env[key]})
    response = ecs.run_fargate_task(task_stack, resource_group_stack,
                                    container_image, region, extra_env,
                                    extras=extras)
    _log_task_run_filter(state[RESOURCE_GROUP] + "-resources", response)
    return response


def schedule_task(target_id, cronexp, env=[], role_arn=None, extras=None):
    state = get_state()
    task_stack = state.get(TASK)
    container_image = state.get(CONTAINER_IMAGE)
    region = state.get("AWS_REGION")
    resource_group_stack = state.get(RESOURCE_GROUP) + "-resources"

    role_name = (state.get(RESOURCE_GROUP) +
                 "-resources-CloudWatchEventECSRole")

    if not role_arn:
        roles = iam.list_roles()
        for r in roles:
            if r["RoleName"] == role_name:
                role_arn = r["Arn"]
                break
    if not role_arn:
        raise Exception("Role %s not found" % role_name)

    extra_env = []
    for key in env.keys():
        extra_env.append({"name": key, "value": env[key]})

    try:
        response = events.schedule_task(task_stack, resource_group_stack,
                                        container_image,
                                        region, target_id, cronexp, role_arn,
                                        env=extra_env, extras=extras)
    except Exception as e:
        LOGGER.error("Scheduling task failed for %s target_id: %s cron: %s" %
                     (task_stack, target_id, cronexp))
        LOGGER.critical(str(e))
        return

    params = {
        "region": state.get("AWS_REGION"),
        "resource_group": state.get(RESOURCE_GROUP),
        "task": state.get(TASK)
    }
    print(("Check the status at https://console.aws.amazon.com/ecs/" +
           "home?region={region}#/clusters/{resource_group}-resources" +
           "/scheduledTasks").format(**params))
    return response


def unschedule_task(target_id):
    state = get_state()
    task_stack = state.get(TASK)
    resource_group_stack = state.get(RESOURCE_GROUP) + "-resources"
    try:
        response = events.unschedule_task(task_stack, resource_group_stack,
                                          target_id)
    except Exception as e:
        raise Exception("No schedules found")
    params = {
        "region": state.get("AWS_REGION"),
        "resource_group": state.get(RESOURCE_GROUP),
        "task": state.get(TASK)
    }
    print(("Check the status at https://console.aws.amazon.com/ecs/" +
           "home?region={region}#/clusters/{resource_group}-resources" +
           "/scheduledTasks").format(**params))
    return response


def list_schedules():
    state = get_state()
    task_stack = state.get(TASK)
    resource_group_stack = state.get(RESOURCE_GROUP) + "-resources"
    response = events.list_schedules(task_stack, resource_group_stack)
    schedules = list()
    for r in response:
        record = {
            "name": r["rule"]["Name"],
            "cron": re.sub(r"cron\((.*)\)", "\\1",
                           r["rule"]["ScheduleExpression"])
        }
        if not r["targets"]:
            LOGGER.warning("Rule %s has no target!" % record["name"])
            continue
        # One rule, one target
        record["target_id"] = str(r["targets"][0]["Id"])
        input_str = r["targets"][0].get("Input")
        if input_str:
            input_ = json.loads(input_str.replace("\\\\", ""))
            record["envs"] = [{"key": e["name"], "value": e["value"]}
                              for e in input_["containerOverrides"][0]["environment"] if e["name"] != STAGE]
        schedules.append(record)
    yml_clean = re.sub(r"'([a-zA-Z_]*)':",
                       "\\1:",
                       yaml.dump({"schedules": schedules}, default_style="'"))
    return yaml.load(yml_clean, Loader=yaml.FullLoader)


def write_logs(file_descriptor, start_time=None, end_time=None, format_=None,
               follow=False, wait=2.5, last_timestamp=None, **extras):
    state = get_state()
    log_group_name = state.get(RESOURCE_GROUP) + "-" + state.get(TASK)

    if start_time and type(start_time) is str:
        start_time = dateutil.parser.parse(start_time)
    if end_time and type(end_time) is str:
        end_time = dateutil.parser.parse(end_time)

    if not format_:
        format_ = "{datetime} - {message}"

    while True:
        response = logs.filter_log_events(log_group_name,
                                          start_time=start_time,
                                          end_time=end_time,
                                          extras=extras)

        show = False
        for e in response.get("events", list()):
            e["datetime"] = datetime.datetime.fromtimestamp(e["timestamp"] / 1000)
            start_time = e["timestamp"]
            if show or last_timestamp is None or last_timestamp < e["timestamp"]:
                show = True
                wait = 2.5
                last_timestamp = e["timestamp"]
                file_descriptor.write(format_.format(**e) + "\n")

        next_token = response.get("nextToken")
        while next_token:
            response = logs.filter_log_events(log_group_name,
                                              next_token=next_token)
            for e in response.get("events", list()):
                e["datetime"] = datetime.datetime.fromtimestamp(
                    e["timestamp"] / 1000)
                start_time = e["timestamp"]
                if show or last_timestamp < e["timestamp"]:
                    show = True
                    wait = 2.5
                    last_timestamp = e["timestamp"]
                    file_descriptor.write(format_.format(**e) + "\n")
            next_token = response.get("nextToken")

        if not follow:
            break

        time.sleep(wait)
        wait = min(wait * 2, 60)

    return start_time
