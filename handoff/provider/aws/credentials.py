import json, logging, os
import requests

logger = logging.getLogger(__name__)


def get_credentials():
    """
    AWS credentials are either retrieved from credentials local endpoint
    or defined as environment variables
    """
    aws_region = os.environ.get("AWS_REGION", None)
    rel_uri = os.environ.get("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI")
    if rel_uri:
        # See https://docs.aws.amazon.com/AmazonECS/latest/userguide/task-iam-roles.html
        response = requests.get("http://169.254.170.2" + rel_uri)
        cred = json.loads(response.content)
        logger.debug("Role ARN: " + cred["RoleArn"])
        return cred["AccessKeyId"], cred["SecretAccessKey"], cred["Token"], aws_region

    logger.info("Reading keys from environment variables.")
    aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID", None)
    aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY", None)
    aws_session_token = os.environ.get("AWS_SESSION_TOKEN", None)

    return (aws_access_key_id,
            aws_secret_access_key,
            aws_session_token,
            aws_region)
