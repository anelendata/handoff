import json, logging, os
import boto3
import requests

logger = logging.getLogger(__name__)

CLIENTS = dict()


def _get_credentials(cred: dict = {}):
    """
    In AWS instance, AWS credentials are either retrieved from credentials local endpoint
    """
    rel_uri = os.environ.get("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI")

    if not cred and rel_uri:
        # See https://docs.aws.amazon.com/AmazonECS/latest/userguide/task-iam-roles.html
        response = requests.get("http://169.254.170.2" + rel_uri)
        task_cred = json.loads(response.content)
        logger.debug("Role ARN: " + task_cred["RoleArn"])
        logger.debug("Set AWS credentials from " +
                     "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI")
        # Standardize the key names
        cred["aws_access_key_id"] = task_cred["AccessKeyId"]
        cred["aws_secret_access_key"] = task_cred["SecretAccessKey"]
        cred["aws_session_token"] = task_cred["Token"]
        # cred["aws_role_arn"] = task_cred["RoleArn"]

    if not cred.get("region_name") and cred.get("aws_region"):
        cred["region_name"] = cred["aws_region"]

    return cred


def _get_boto3_session_kwargs(params):
    kwargs = {}
    valid_boto3_session_keys = [
        "aws_access_key_id",
        "aws_secret_access_key",
        "aws_session_token",
        "region_name",
        "botocore_session",
        "profile_name",
    ]
    for key in params.keys():
        if key in valid_boto3_session_keys:
            kwargs[key] = params[key]
    return kwargs


def get_client(service, cred_keys: dict = {}):
    global CLIENTS
    # Disabling cache as it is doing strange bug
    # if CLIENTS.get(service):
    #   return CLIENTS[service]
    cred_keys = _get_credentials(cred_keys)
    kwargs = _get_boto3_session_kwargs(cred_keys)
    session = boto3.session.Session(**kwargs)
    CLIENTS[service] = session.client(service)
    return CLIENTS[service]
