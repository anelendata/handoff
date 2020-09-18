import json, logging, os, shutil, sys, tempfile
from collections import defaultdict

from packaging import version

import docker
from docker import APIClient as docker_api_client

from handoff import utils
from handoff.config import ADMIN_ENVS, DOCKER_IMAGE, get_state


logger = utils.get_logger(__name__)

DOCKERFILE = "Dockerfile"


def _increment_version(ver, delimiter="."):
    digits = ver.split(delimiter)
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
    max_version = None
    for image in images:
        tags = tags + image.tags
    for tag in tags:
        ver = "".join(tag.split(":")[1:])
        if (max_version is None or
                version.parse(max_version) < version.parse(ver)):
            max_version = ver
    return max_version


def build(project_dir, new_version=None, docker_file=None, files_dir=None,
          nocache=False):
    state = get_state()
    cli = docker_api_client()
    image_name = state[DOCKER_IMAGE]
    if not image_name:
        raise Exception("You need to set DOCKER_IMAGE environment variable.")

    docker_file_dir, _ = os.path.split(__file__)
    if not docker_file:
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
        logger.info("Current working directory: " + cwd)
        handoff_dir = os.path.join(cwd, "../../../../")
        logger.info("Looking for handoff source at " + handoff_dir)
        if os.path.isfile(os.path.join(handoff_dir, "setup.py")):
            logger.info("Found handoff. Copying to the build directory")
            shutil.copytree(handoff_dir, os.path.join(build_dir, "handoff"))
        else:
            logger.info("...not found")

        shutil.copytree(project_dir, os.path.join(build_dir, "project"),
                        symlinks=True)
        shutil.copytree(os.path.join(docker_file_dir, "script"),
                        os.path.join(build_dir, "script"))
        shutil.copyfile(docker_file, os.path.join(build_dir, DOCKERFILE))

        if files_dir:
            logger.info(("Copying the directory %s to Docker image build " +
                         "temporary directory") % files_dir)
            path, dir_ = os.path.split(files_dir)
            shutil.copytree(files_dir, os.path.join(build_dir, dir_))

        for line in cli.build(path=build_dir,
                              tag=image_name + ":" + new_version,
                              nocache=nocache):
            for subline in line.decode("utf-8").split("\n"):
                try:
                    msg = json.loads(subline)
                except json.decoder.JSONDecodeError:
                    continue
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
        except json.decoder.JSONDecodeError:
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
