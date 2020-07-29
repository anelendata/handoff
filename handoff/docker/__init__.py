import json, os, shutil, sys, tempfile
import docker
from docker import APIClient as docker_api_client
from handoff.impl import utils

logger = utils.get_logger(__name__)
DOCKERFILE = "Dockerfile"


def build(project_dir, tag=None, docker_file=None, nocache=False):
    client = docker.from_env()
    cli = docker_api_client()
    image_name = os.environ["IMAGE_NAME"]
    if not image_name:
        raise Exception("You need to set IMAGE_NAME environment variable.")

    if not docker_file:
        docker_file_dir, _ = os.path.split(__file__)
        docker_file = os.path.join(docker_file_dir, DOCKERFILE)

    images = client.images.list(name=image_name)
    if not images:
        tag = "0.1"

    if not tag:
        tags = images[0].tags
        current_tag = None
        latest_version = None
        max_digit = 0
        for t in tags:
            current_tag = t.split(":")[-1]
            if current_tag == "latest":
                continue
            version = current_tag.split(".")
            try:
                digit = int(version[-1])
            except ValueError:
                digit = 0
            if digit > max_digit:
                max_digit = digit
                latest_version = version
        if latest_version is None:
            tag = "0.1"
        else:
            latest_version[-1] = str(max_digit + 1)
            tag = ".".join(latest_version)

    sys.stdout.write("Build %s:%s (y/N)? " % (image_name, tag))
    response = input()
    if response.lower() not in ["y", "yes"]:
        return
    logger.info("Building %s:%s" % (image_name, tag))

    with tempfile.TemporaryDirectory() as build_dir:
        cwd = os.getcwd()
        pos = cwd.find("handoff")
        if pos >= 0:
            handoff_dir = os.path.join(cwd[:pos], "handoff")
            shutil.copytree(handoff_dir, os.path.join(build_dir, "handoff"))

        shutil.copytree(project_dir, os.path.join(build_dir, "project"), symlinks=True)
        shutil.copytree(os.path.join(docker_file_dir, "script"), os.path.join(build_dir, "script"))
        shutil.copyfile(docker_file, os.path.join(build_dir, DOCKERFILE))

        for line in cli.build(path=build_dir, tag=image_name + ":" + tag, nocache=nocache):
            msg = json.loads(line.decode("utf-8"))
            if msg.get("stream") and msg["stream"] != "\n":
                logger.info(msg["stream"])
