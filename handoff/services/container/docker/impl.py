import json, logging, os, shutil, sys, tempfile
from collections import defaultdict
from fnmatch import fnmatch

from packaging import version

import docker
from docker import APIClient as docker_api_client

from handoff import utils
from handoff.config import (ADMIN_ENVS, ARTIFACTS_DIR, BUNDLE_IGNORE_PATTERNS,
                            CONTAINER_IMAGE, FILES_DIR, get_state)


logger = utils.get_logger(__name__)

DOCKERFILE = "Dockerfile"


def _is_workspace_dir(path):
    # workspace_init creates both; a project directory has files/ (templates)
    # but no artifacts/.
    return (os.path.isdir(os.path.join(path, ARTIFACTS_DIR)) and
            os.path.isdir(os.path.join(path, FILES_DIR)))


def _project_ignore(workspace_dir=None):
    """Return a shutil.copytree ignore function that keeps secrets
    (BUNDLE_IGNORE_PATTERNS) and local handoff workspaces out of the build
    context. A workspace holds files rendered with real secret values (files/,
    config, artifacts) and venvs.
    """
    workspace_dir = os.path.realpath(workspace_dir) if workspace_dir else None

    def ignore(src, names):
        ignored = set()
        for name in names:
            path = os.path.join(src, name)
            if any(fnmatch(name, p) for p in BUNDLE_IGNORE_PATTERNS):
                ignored.add(name)
            elif (os.path.isdir(path) and not os.path.islink(path) and
                  (os.path.realpath(path) == workspace_dir or
                   _is_workspace_dir(path))):
                logger.warning(f"Excluding {path} from the bundle: it is a " +
                               "handoff workspace and may contain rendered " +
                               "secrets.")
                ignored.add(name)
        return ignored
    return ignore


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


def copy_files(project_dir, build_dir, docker_file=None, files_dir=None,
               workspace_dir=None):
    if _is_workspace_dir(project_dir):
        raise Exception(f"The project directory {project_dir} is also a " +
                        "handoff workspace, so it may contain rendered " +
                        "secrets. Use a separate workspace directory.")

    docker_file_dir, _ = os.path.split(__file__)
    if not docker_file:
        docker_file = os.path.join(docker_file_dir, DOCKERFILE)

    cwd, _ = os.path.split(__file__)
    logger.info("Current working directory: " + cwd)
    handoff_dir = os.path.join(cwd, "../../../../")
    logger.info("Looking for handoff source at " + handoff_dir)
    if os.path.isfile(os.path.join(handoff_dir, "setup.py")):
        logger.info(f"Found handoff. Copying to the build directory {build_dir}")
        ho_build_dir = os.path.join(build_dir, "handoff")
        os.mkdir(ho_build_dir)
        shutil.copytree(os.path.join(handoff_dir, "handoff"),
                        os.path.join(ho_build_dir, "handoff"),
                        ignore=_project_ignore())
        files = [
            "MANIFEST.in",
            "README.md",
            "pyproject.toml",
            "setup.cfg",
            "setup.py",
        ]
        for fn in files:
            shutil.copyfile(os.path.join(handoff_dir, fn),
                            os.path.join(ho_build_dir, fn))
    else:
        logger.info("...not found")

    shutil.copytree(project_dir, os.path.join(build_dir, "project"),
                    symlinks=True, ignore=_project_ignore(workspace_dir))
    shutil.copytree(os.path.join(docker_file_dir, "script"),
                    os.path.join(build_dir, "script"))
    shutil.copyfile(docker_file, os.path.join(build_dir, DOCKERFILE))

    if files_dir:
        logger.info(f"Copying the directory {files_dir} to {build_dir}")
        path, dir_ = os.path.split(files_dir)
        shutil.copytree(files_dir, os.path.join(build_dir, dir_))
    return {"status": "success"}


def build(project_dir, new_version=None, docker_file=None, files_dir=None,
          nocache=False, yes=False, file_descriptor=sys.stdout,
          workspace_dir=None, **kwargs):
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
        copy_files(project_dir, build_dir, docker_file, files_dir,
                   workspace_dir=workspace_dir)
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


def run(version=None, extra_env=dict(), yes=False, command=None, detach=True,
        interactive=False, file_descriptor=sys.stdout, ports=None, platform=None, **kwargs):
    state = get_state()
    env = {}
    for e in ADMIN_ENVS.keys():
        env[e] = state.get(e)

    if ports:
        logger.info(f"Port bindings (container:host): {ports}")
        ports = json.loads(ports)
    if platform:
        logger.info(f"Platform specified: {platform}")

    env.update(extra_env)
    logger.debug(env)
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
        container = client.containers.run(image_name + ":" + version,
                              command=command, environment=env,
                              platform=platform, ports=ports, detach=detach, remove=True)
        output = container.attach(stdout=True, stream=True, logs=True)
        for line in output:
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
    else:
        version = str(version)

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
    for msg in client.images.push(registry + "/" + image_name,
                                   version, stream=True, decode=True):
        if msg.get("error"):
            error_msg = msg["error"]
            error_msg += f"\nHint: If this is an auth error, try:\naws ecr get-login-password --region <region> | docker login --username AWS --password-stdin {registry}\nfrom the console."
            logger.error(error_msg)
            break

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
