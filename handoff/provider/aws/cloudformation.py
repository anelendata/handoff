import logging
import boto3
from botocore.exceptions import ClientError
# from botocore.errorfactory import RepositoryNotFoundException
from . import credentials as cred

logger = logging.getLogger(__name__)

CFN_CLIENT = None


def get_client():
    global CFN_CLIENT
    if CFN_CLIENT:
        return CFN_CLIENT
    aws_access_key_id, aws_secret_access_key, aws_session_token, aws_region = cred.get_credentials()
    logger.debug(aws_access_key_id[0:-5] + "***** " + aws_secret_access_key[0:-5] + "***** " + aws_region)
    boto_session = boto3.session.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name=aws_region)
    CFN_CLIENT = boto_session.client("cloudformation")
    return CFN_CLIENT


def create_stack(stack_name, template_file, parameters={},
                 capabilities=["CAPABILITY_NAMED_IAM"]):
    """
    Parameters are a list of dict objects that has these four keys,
    latter two keys are optional:
      - ParameterKey (string)
      - ParameterValue (string)
      - UsePreviousValue (True|False)
      - ResolvedValue (string)

    See:
    - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudformation.html#CloudFormation.Client.create_stack
    """
    with open(template_file, "r") as f:
        template = f.read()
    client = get_client()
    response = client.create_stack(
        StackName=stack_name,
        TemplateBody=template,
        Capabilities=capabilities,
        Parameters=parameters)
    logger.info(response)


def update_stack(stack_name, template_file, parameters={},
                 capabilities=["CAPABILITY_NAMED_IAM"]):
    """
    Parameters are a list of dict objects that has these four keys,
    latter two keys are optional:
      - ParameterKey (string)
      - ParameterValue (string)
      - UsePreviousValue (True|False)
      - ResolvedValue (string)

    See:
    - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudformation.html#CloudFormation.Client.update_stack
    """
    with open(template_file, "r") as f:
        template = f.read()
    client = get_client()
    response = client.create_stack(
        StackName=stack_name,
        TemplateBody=template,
        Capabilities=capabilities,
        Parameters=parameters)
    logger.info(response)


def delete_stack(stack_name):
    """
    See:
    - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudformation.html#CloudFormation.Client.delete_stack
    """
    client = get_client()
    response = client.delete_stack(StackName=stack_name)
    logger.info(response)
