import json, logging, os
import boto3
import requests

logger = logging.getLogger(__name__)

CLIENTS = dict()


def set_container_credentials():
    """
    AWS credentials are either retrieved from credentials local endpoint
    or defined as environment variables
    """
    rel_uri = os.environ.get("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI")
    if not rel_uri:
        return

    # See https://docs.aws.amazon.com/AmazonECS/latest/userguide/task-iam-roles.html
    response = requests.get("http://169.254.170.2" + rel_uri)
    cred = json.loads(response.content)
    logger.info("Role ARN: " + cred["RoleArn"])
    os.environ["AWS_ACCESS_KEY_ID"] = cred["AccessKeyId"]
    os.environ["AWS_SECRET_ACCESS_KEY"] = cred["SecretAccessKey"]
    os.environ["AWS_SESSION_TOKEN"] = cred["Token"]
    logger.info("Set AWS credentials from AWS_CONTAINER_CREDENTIALS_RELATIVE_URI")


def get_session(aws_access_key_id, aws_secret_access_key,
                aws_session_token, aws_region):
    session = boto3.session.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
        region_name=aws_region)
    return session


def get_region():
    set_container_credentials()
    session = boto3.session.Session()
    return session.region_name


def get_client(service):
    global CLIENTS
    if CLIENTS.get(service):
        return CLIENTS[service]

    set_container_credentials()
    session = boto3.session.Session(region_name=os.environ.get("AWS_REGION"))
    CLIENTS[service] = session.client(service)

    # boto_session = get_session(aws_access_key_id, aws_secret_access_key,
    #                            aws_session_token, aws_region)
    # CLIENTS[service] = boto_session.client(service)

    return CLIENTS[service]
