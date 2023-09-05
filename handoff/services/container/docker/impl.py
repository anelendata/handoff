import json, logging, os, shutil, sys, tempfile
from collections import defaultdict

from packaging import version

import docker
from docker import APIClient as docker_api_client

from handoff import utils
from handoff.config import ADMIN_ENVS, CONTAINER_IMAGE, get_state


logger = utils.get_logger(__name__)

DOCKERFILE = "Dockerfile"


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
        if (ver not in ignore and
                (max_version is None or
                 version.parse(max_version) < version.parse(ver))):
            max_version = ver
    return max_version


def copy_files(project_dir, build_dir, docker_file=None, files_dir=None):
    docker_file_dir, _ = os.path.split(__file__)
    if not docker_file:
        docker_file = os.path.join(docker_file_dir, DOCKERFILE)

    cwd, _ = os.path.split(__file__)
    logger.info("Current working directory: " + cwd)
    handoff_dir = os.path.join(cwd, "../../../../")
    logger.info("Looking for handoff source at " + handoff_dir)
    if os.path.isfile(os.path.join(handoff_dir, "setup.py")):
        logger.info("Found handoff. Copying to the build directory")
        ho_build_dir = os.path.join(build_dir, "handoff")
        os.mkdir(ho_build_dir)
        shutil.copytree(os.path.join(handoff_dir, "handoff"),
                        os.path.join(ho_build_dir, "handoff"))
        files = [
            "MANIFEST.in",
            "README.md",
            "requirements.txt",
            "setup.cfg",
            "setup.py",
        ]
        for fn in files:
            shutil.copyfile(os.path.join(handoff_dir, fn),
                            os.path.join(ho_build_dir, fn))
    else:
        logger.info("...not found")

    shutil.copytree(project_dir, os.path.join(build_dir, "project"),
                    symlinks=True)
    shutil.copytree(os.path.join(docker_file_dir, "script"),
                    os.path.join(build_dir, "script"))
    shutil.copyfile(docker_file, os.path.join(build_dir, DOCKERFILE))

    if files_dir:
        logger.info(f"Copying the directory {files_dir} to {build_dir}")
        path, dir_ = os.path.split(files_dir)
        shutil.copytree(files_dir, os.path.join(build_dir, dir_))
    return {"status": "success"}


def build(project_dir, new_version=None, docker_file=None, files_dir=None,
          nocache=False, yes=False, file_descriptor=sys.stdout, **kwargs):
    state = get_state()
    cli = docker_api_client()
    image_name = state[CONTAINER_IMAGE]
    if not image_name:
        raise Exception(f"You need to set {CONTAINER_IMAGE} environment variable.")

    if not new_version:
        latest_version = get_latest_version(image_name)
        new_version = utils.increment_version(latest_version)

    if not yes:
        sys.stdout.write("Build %s:%s (y/N)? " % (image_name, new_version))
        response = input()
        if response.lower() not in ["y", "yes"]:
            return{"status": "canceled"}

    logger.info("Building %s:%s" % (image_name, new_version))

    with tempfile.TemporaryDirectory() as build_dir:
        copy_files(project_dir, build_dir, docker_file, files_dir)
        for line in cli.build(path=build_dir,
                              tag=f"{image_name}:{new_version}",
                              nocache=nocache):
            for subline in line.decode("utf-8").split("\n"):
                try:
                    msg = json.loads(subline)
                except json.decoder.JSONDecodeError:
                    continue
                if msg.get("stream") and msg["stream"] != "\n":
                    file_descriptor.write(msg["stream"])
        return{"status": "success"}


def run(version=None, extra_env=dict(), yes=False, command=None, detach=False,
        interactive=False, file_descriptor=sys.stdout, **kwargs):
    state = get_state()
    env = {}
    for e in ADMIN_ENVS.keys():
        env[e] = state.get(e)

    env.update(extra_env)

    image_name = state[CONTAINER_IMAGE]
    if not version:
        version = get_latest_version(image_name)

    if not yes:
        sys.stdout.write("Run %s:%s (y/N)? " % (image_name, version))
        response = input()
        if response.lower() not in ["y", "yes"]:
            return

    if interactive:
        stdin_open = True
        tty = True
    else:
        stdin_open = False
        tty = False

    client = docker.from_env()

    try:
        # TODO: Streaming log is not working :(
        for line in client.containers.run(image_name + ":" + version,
                                          command=command, environment=env,
                                          stream=True, detach=detach,
                                          stdin_open=stdin_open, tty=tty):
            file_descriptor.write(line.decode("utf-8").replace("\\n", "\n"))
    except Exception as e:
        return {
            "status": "error",
            "message": (str(e))
        }


def push(username, password, registry, version=None, yes=False,
         file_descriptor=sys.stdout, **kwargs):
    state = get_state()
    image_name = state[CONTAINER_IMAGE]
    if not version:
        version = get_latest_version(image_name)

    if not version:
        raise Exception("Image %s not found" % image_name)

    if not yes:
        sys.stdout.write("Push %s:%s to %s (y/N)? " %
                         (image_name, version, registry))
        response = input()
        if response.lower() not in ["y", "yes"]:
            return {"status": "canceled"}

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
            file_descriptor.write("id: %s status: %s\n" % (block, status[block]))
        if msg.get("progressDetail"):
            total = msg["progressDetail"].get("total")
            current= msg["progressDetail"].get("current")
            progress_bar = msg.get("progress")
            if total and current and progress_bar:
                current_progress = int(100 * current / total)
                if current_progress - progress[block] > 5:
                    progress[block] = current_progress
                    file_descriptor.write("id: %s %s\n" % (block, progress_bar))
    return {"status": "success"}
