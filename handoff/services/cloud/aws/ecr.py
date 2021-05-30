import logging
import boto3
from botocore.exceptions import ClientError
# from botocore.errorfactory import RepositoryNotFoundException
from . import credentials as cred

logger = logging.getLogger(__name__)


def get_client(cred_keys: dict = {}):
    return cred.get_client("ecr", cred_keys)


def get_token(registry_id, cred_keys: dict = {}):
    client = get_client(cred_keys)
    token = client.get_authorization_token(registryIds=[registry_id])
    return token


def get_docker_registry_credentials(registry_id):
    token = get_token(registry_id)
    username = "AWS"
    password = token["authorizationData"][0]["authorizationToken"]
    registry = token["authorizationData"][0]["proxyEndpoint"][len("https://"):]

    from base64 import b64decode
    username, password = b64decode(token["authorizationData"][0]['authorizationToken']).decode().split(':')
    registry = token["authorizationData"][0]['proxyEndpoint'][len("https://"):]

    return username, password, registry


def list_images(image_name, cred_keys: dict = {}):
    client = get_client(cred_keys)
    response = client.list_images(repositoryName=image_name)
    ecr_images = response["imageIds"]
    while response.get("next_token"):
        response = client.list_images(repositoryName=image_name,
                                      next_token=response["next_token"])
        ecr_images = ecr_images + response["imageIds"]

    return ecr_images


def create_repository(repository_name, is_mutable, cred_keys: dict = {}):
    if is_mutable:
        mutability = "MUTABLE"
    else:
        mutability = "IMMUTABLE"

    client = get_client(cred_keys)
    response = client.create_repository(repositoryName=repository_name,
                                        imageTagMutability=mutability)
    return response
