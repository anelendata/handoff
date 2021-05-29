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
        cred = json.loads(response.content)
        logger.debug("Role ARN: " + cred["RoleArn"])
        """
        os.environ["AWS_ACCESS_KEY_ID"] = cred["AccessKeyId"]
        os.environ["AWS_SECRET_ACCESS_KEY"] = cred["SecretAccessKey"]
        os.environ["AWS_SESSION_TOKEN"] = cred["Token"]
        """
        logger.debug("Set AWS credentials from " +
                     "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI")
        # Standardize the key names
        cred["aws_access_key_id"] = cred.pop("AccessKeyId")
        cred["aws_secret_access_key"] = cred.pop("SecretAccessKey")
        cred["aws_session_token"] = cred.pop("Token")
        cred["aws_role_arn"] = cred.pop("RoleArn")

    return cred


def get_session(aws_access_key_id=None, aws_secret_access_key=None,
                aws_session_token=None, aws_region=None):
    session = boto3.session.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
        region_name=aws_region)
    return session


def get_region(cred: dict = {}):
    cred = _get_credentials()
    session = boto3.session.Session(**cred)
    return session.region_name


def get_client(service, cred_keys: dict = {}):
    global CLIENTS
    # Disabling cache as it is doing strange bug
    # if CLIENTS.get(service):
    #   return CLIENTS[service]
    cred_keys = _get_credentials(cred_keys)

    session = boto3.session.Session(
            aws_access_key_id=cred_keys.get("aws_access_key_id"),
            aws_secret_access_key=cred_keys.get("aws_secret_access_key"),
            region_name=cred_keys.get("aws_region"),
            )
    CLIENTS[service] = session.client(service)

    return CLIENTS[service]
