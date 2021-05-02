import datetime, json, logging, multiprocessing, os, re, tempfile

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

import handoff
from handoff.config import (
    init_state,
    get_state,
    CLOUD_PROVIDER,
    CLOUD_PLATFORM,
    CONTAINER_PROVIDER,
)

CODE_DIR, _ = os.path.split(__file__)
FRONTEND_DIR = os.path.join(CODE_DIR, "../../frontend")

router = APIRouter()
logger = logging.getLogger(__name__)

# handoff specific logic
log_proc = None
stats_proc = None

PROJECT_ROOT = os.getcwd()


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def run_handoff_command(project_dir, command, stage, vars):
    kwargs = dict()
    with tempfile.TemporaryDirectory() as root_dir:
        workspace_dir = os.path.join(root_dir, "workspace")
        ret = handoff.do(command, project_dir, workspace_dir,
                         stage=stage, vars=vars, **kwargs)
    response = json.dumps(ret, default=json_serial)

    return json.loads(response)


def handoff_do(project, command, stage, vars={}, do_async=False):
    project_dir = os.path.join(PROJECT_ROOT, project)
    if not project or not os.path.isdir(project_dir):
        return "Invalid project", 404

    if not do_async:
        return run_handoff_command(project_dir, command, stage, vars)

    proc = multiprocessing.Process(
        target=run_handoff_command,
        args=(project_dir, command, vars))
    proc.start()
    return proc


@router.get("/api/repositories")
def read_repositories():
    repositories = next(os.walk("."))[1]
    repositories.sort()
    return repositories


@router.get("/api/{repository}/projects")
def read_projects(repository):
    path = f"./{repository}/projects"
    dirs = next(os.walk(path))[1]
    projects = [d for d in dirs if os.path.isfile(os.path.join(path, d, "project.yml"))]
    projects.sort()
    return projects


def _get_cur_dir(tree, path):
    if not path:
        return tree
    cur_dir = tree
    for dir_ in path.split("/"):
        next_dir = None
        for i in cur_dir["items"]:
            if i["name"] == dir_:
                next_dir = i
                break
        if not next_dir:
            raise Exception(f"{dir_} not found")
        cur_dir = next_dir

    return cur_dir


def _get_directory_structure(rootdir):
    """
    Creates a nested dictionary that represents the folder structure of rootdir
    """
    rootdir = rootdir.rstrip(os.sep)
    project_files = [{
        "name": os.path.split(rootdir)[-1],
        "isDirectory": True,
        "items": [],
        }]
    cur_path = rootdir
    for path, dirs, files in os.walk(rootdir):
        cur_dir = _get_cur_dir(project_files[0], path[len(rootdir):].strip("/"))
        for d in dirs:
            new_dir = {
                    "name": d,
                    "isDirectory": True,
                    "items": [],
                    }
            cur_dir["items"].append(new_dir)
        for f in files:
            size = os.path.getsize(os.path.join(path, f))
            new_file = {
                    "name": f,
                    "isDirectory": False,
                    "size": size,
                    }
            cur_dir["items"].append(new_file)
    return project_files


@router.get("/api/{repository}/{project}/files")
def read_projects(repository, project):
    path = f"./{repository}/projects/{project}"
    return _get_directory_structure(path)


@router.get("/api/{repository}/{project}/files/{path:path}")
def read_projects(repository, project, path):

    path = f"./{repository}/projects/{path}"
    with open(path, "r") as f:
        text = f.read()
    return text


@router.get("/api/{repository}/{project}/{stage}/schedules")
def read_schedules(repository, project, stage):
    response = handoff_do(
        os.path.join(repository, "projects", project),
        "cloud schedule list",
        stage=stage,
    )
    return response


@router.get("/api/{repository}/{project}/{stage}/status")
def status(repository, project, stage):
    response = handoff_do(
        os.path.join(repository, "projects", project),
        "cloud task status",
        stage=stage,
        )
    return response


@router.post("/api/{repository}/{project}/{stage}/run")
def run(repository, project, stage, target_id=None):
    response = handoff_do(
        os.path.join(repository, "projects", project),
        "cloud run",
        stage=stage,
        vars={
            "target_id": target_id,
            },
        )
    return response


@router.get("/api/{repository}/{project}/{stage}/log", response_class=PlainTextResponse)
def log(repository, project, stage, start_time=None, end_time=None):
    file_name = f"./{project}.log"
    if os.path.isfile(file_name):
        os.remove(file_name)
    start_time = datetime.datetime.fromtimestamp(float(start_time)).isoformat()
    if end_time:
        end_time = datetime.datetime.fromtimestamp(float(end_time)).isoformat()
    handoff_do(
        os.path.join(repository, "projects", project),
        "cloud logs",
        stage=stage,
        vars={
            "start_time": start_time,
            "end_time": end_time,
            "file": file_name,
            "follow": False,
            },
        # async=True,
    )

    with open(file_name) as f:
        log = f.read()

    return log


@router.get("/api/{repository}/{project}/{stage}/stats")
def stats(repository, project, stage, start_time=None, end_time=None):
    file_name = f"./{repository}/{project}_stats.json"
    if os.path.isfile(file_name):
        os.remove(file_name)
    start_time = datetime.datetime.fromtimestamp(
        float(start_time)).isoformat()
    if end_time:
        end_time = datetime.datetime.fromtimestamp(float(end_time)).isoformat()

    handoff_do(
        os.path.join(repository, "projects", project),
        "cloud logs",
        stage=stage,
        vars={
            "start_time": start_time,
            "end_time": end_time,
            "file": file_name,
            "filter_pattern": "count",
            "format_": "json",
            "follow": False,
            },
        # async=True,
    )

    ret = []
    with open(file_name) as f:
        text = f.read()
        for line in text.split("\n"):
            try:
                r = json.loads(line)
            except Exception as e:
                r = {"error": str(e), "str": line}
            ret.append(r)

    return ret


@router.get("/", response_class=HTMLResponse)
def project():
    with open(FRONTEND_DIR + "/index.html", "r") as f:
        body = f.read()
    return HTMLResponse(body)
