import logging
import boto3
from botocore.exceptions import ClientError
# from botocore.errorfactory import RepositoryNotFoundException
from . import credentials as cred

logger = logging.getLogger(__name__)


def get_client():
    return cred.get_client("cloudformation")


def create_stack(stack_name, template_file, parameters=None,
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
    kwargs = {
        "StackName": stack_name,
        "TemplateBody": template,
        "Capabilities": capabilities
    }
    if parameters:
        kwargs["Parameters"] = parameters

    response = client.create_stack(**kwargs)
    return response


def update_stack(stack_name, template_file, parameters=None,
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

    kwargs = {
        "StackName": stack_name,
        "TemplateBody": template,
        "Capabilities": capabilities
    }
    if parameters:
        kwargs["Parameters"] = parameters

    response = client.update_stack(**kwargs)
    return response


def delete_stack(stack_name):
    """
    See:
    - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudformation.html#CloudFormation.Client.delete_stack
    """
    client = get_client()
    response = client.delete_stack(StackName=stack_name)
    return response


def describe_stack_resources(stack_name, query=None):
    client = get_client()
    return client.describe_stack_resources(StackName=stack_name)
