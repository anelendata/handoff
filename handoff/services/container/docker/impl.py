import json, logging, os, shutil, sys, tempfile
from collections import defaultdict

import docker
from docker import APIClient as docker_api_client

from handoff import utils
from handoff.config import ADMIN_ENVS, DOCKER_IMAGE, get_state


logger = utils.get_logger(__name__)

DOCKERFILE = "Dockerfile"


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


def get_latest_version(image_name, ignore=["latest"]):
    client = docker.from_env()
    images = client.images.list(name=image_name)
    if not images:
        return None

    tags = list()
    for image in images:
        tags = tags + image.tags
    tags.sort(reverse=True)
    version = "".join(tags[0].split(":")[1:])
    return version


def build(project_dir, new_version=None, docker_file=None, nocache=False):
    state = get_state()
    cli = docker_api_client()
    image_name = state[DOCKER_IMAGE]
    if not image_name:
        raise Exception("You need to set DOCKER_IMAGE environment variable.")

    if not docker_file:
        docker_file_dir, _ = os.path.split(__file__)
        docker_file = os.path.join(docker_file_dir, DOCKERFILE)

    if not new_version:
        latest_version = get_latest_version(image_name)
        if latest_version:
            new_version = _increment_version(latest_version)
        else:
            new_version = "0.1"

    sys.stdout.write("Build %s:%s (y/N)? " % (image_name, new_version))
    response = input()
    if response.lower() not in ["y", "yes"]:
        return
    logger.info("Building %s:%s" % (image_name, new_version))

    with tempfile.TemporaryDirectory() as build_dir:
        cwd, _ = os.path.split(__file__)
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


def run(version=None, extra_env=dict()):
    state = get_state()
    env = {}
    for e in ADMIN_ENVS.keys():
        env[e] = state.get(e)

    env.update(extra_env)

    image_name = state[DOCKER_IMAGE]
    if not version:
        version = get_latest_version(image_name)

    sys.stdout.write("Run %s:%s (y/N)? " % (image_name, version))
    response = input()
    if response.lower() not in ["y", "yes"]:
        return

    client = docker.from_env()
    for line in client.containers.run(image_name + ":" + version,
                                      environment=env,
                                      stream=True, detach=False):
        print(line.decode("utf-8"))


def push(username, password, registry, version=None):
    state = get_state()
    image_name = state[DOCKER_IMAGE]
    if not version:
        version = get_latest_version(image_name)

    if not version:
        raise Exception("Image %s not found" % image_name)

    sys.stdout.write("Push %s:%s to %s (y/N)? " %
                     (image_name, version, registry))
    response = input()
    if response.lower() not in ["y", "yes"]:
        return

    client = docker.from_env()

    image = client.images.list(name=image_name + ":" + version)[0]
    image.tag(registry + "/" + image_name, version)

    client.login(username, password, registry=registry, reauth=True)

    status = defaultdict(lambda: "")
    progress = defaultdict(lambda: 1)
    for line in client.images.push(registry + "/" + image_name,
                                   version, stream=True):
        try:
            msg = json.loads(line.decode("utf-8"))
        except Exception:
            continue
        total = 0
        current = 0
        block = msg.get("id")
        if block and status[block] != msg.get("status"):
            status[block] = msg.get("status")
            logger.info("id: %s status: %s" % (block, status[block]))
        if msg.get("progressDetail"):
            total = msg["progressDetail"].get("total")
            current= msg["progressDetail"].get("current")
            progress_bar = msg.get("progress")
            if total and current and progress_bar:
                current_progress = int(100 * current / total)
                if current_progress - progress[block] > 5:
                    progress[block] = current_progress
                    logger.info("id: %s %s" % (block, progress_bar))
