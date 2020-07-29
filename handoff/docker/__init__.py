import json, os, shutil, sys, tempfile
import docker
from docker import APIClient as docker_api_client
from handoff.impl import utils

logger = utils.get_logger(__name__)
DOCKERFILE = "Dockerfile"


def _get_latest_version(image_name, ignore=["latest"]):
    client = docker.from_env()
    images = client.images.list(name=image_name)
    if not images:
        return None

    tags = list()
    for image in images:
        current_image_name = image.tags[0].split(":")[0]
        if current_image_name == image_name:
            tags = image.tags
            tags.sort(reverse=True)
            break
    if not tags:
        return None

    version = "".join(tags[0].split(":")[1:])
    return version


def _increment_version(version, delimiter="."):
    digits = version.split(delimiter)
    for i in range(len(digits) - 1, 0, -1):
        try:
            digit = int(digits[i])
        except ValueError:
            continue
        digits[i] = str(digit + 1)
        break

    new_version = ".".join(digits)
    return new_version


def build(project_dir, new_version=None, docker_file=None, nocache=False):
    cli = docker_api_client()
    image_name = os.environ["IMAGE_NAME"]
    if not image_name:
        raise Exception("You need to set IMAGE_NAME environment variable.")

    if not docker_file:
        docker_file_dir, _ = os.path.split(__file__)
        docker_file = os.path.join(docker_file_dir, DOCKERFILE)

    if not new_version:
        latest_version = _get_latest_version(image_name)
        new_version = _increment_version(latest_version)

    sys.stdout.write("Build %s:%s (y/N)? " % (image_name, new_version))
    response = input()
    if response.lower() not in ["y", "yes"]:
        return
    logger.info("Building %s:%s" % (image_name, new_version))

    with tempfile.TemporaryDirectory() as build_dir:
        cwd = os.getcwd()
        pos = cwd.find("handoff")
        if pos >= 0:
            handoff_dir = os.path.join(cwd[:pos], "handoff")
            shutil.copytree(handoff_dir, os.path.join(build_dir, "handoff"))

        shutil.copytree(project_dir, os.path.join(build_dir, "project"),
                        symlinks=True)
        shutil.copytree(os.path.join(docker_file_dir, "script"),
                        os.path.join(build_dir, "script"))
        shutil.copyfile(docker_file, os.path.join(build_dir, DOCKERFILE))

        for line in cli.build(path=build_dir,
                              tag=image_name + ":" + new_version,
                              nocache=nocache):
            msg = json.loads(line.decode("utf-8"))
            if msg.get("stream") and msg["stream"] != "\n":
                logger.info(msg["stream"])


def run(project_dir, version=None, extra_env=dict()):
    env = {"STACK_NAME": os.environ.get("STACK_NAME"),
           "IMAGE_NAME": os.environ.get("IMAGE_NAME"),
           "BUCKET_NAME": os.environ.get("BUCKET_NAME"),
           "AWS_ACCESS_KEY_ID": os.environ.get("AWS_ACCESS_KEY_ID"),
           "AWS_SECRET_ACCESS_KEY": os.environ.get("AWS_SECRET_ACCESS_KEY"),
           "AWS_SESSION_TOKEN": os.environ.get("AWS_SESSION_TOKEN"),
           "AWS_REGION": os.environ.get("AWS_REGION")
           }
    env.update(extra_env)

    image_name = os.environ["IMAGE_NAME"]
    if not version:
        version = _get_latest_version(image_name)

    sys.stdout.write("Run %s:%s (y/N)? " % (image_name, version))
    response = input()
    if response.lower() not in ["y", "yes"]:
        return

    client = docker.from_env()
    for line in client.containers.run(image_name + ":" + version,
                                      environment=env,
                                      stream=True, detach=False):
        logger.info(line.decode("utf-8"))
