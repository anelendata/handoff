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


def run_handoff_command(project_dir, command, vars):
    kwargs = dict()
    with tempfile.TemporaryDirectory() as root_dir:
        workspace_dir = os.path.join(root_dir, "workspace")
        ret = handoff.do(command, project_dir, workspace_dir,
                         vars=vars, **kwargs)
    response = json.dumps(ret, default=json_serial)

    return json.loads(response)


def handoff_do(project, command, vars={}, do_async=False):
    project_dir = os.path.join(PROJECT_ROOT, project)
    if not project or not os.path.isdir(project_dir):
        return "Invalid project", 404

    if not do_async:
        return run_handoff_command(project_dir, command, vars)

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


@router.get("/api/{repository}/{project}/schedules")
def read_schedules(repository, project):
    response = handoff_do(
        os.path.join(repository, "projects", project),
        "cloud schedule list")
    return response


@router.get("/api/{repository}/{project}/status")
def status(repository, project):
    response = handoff_do(
        os.path.join(repository, "projects", project),
        "cloud task status")
    return response


@router.post("/api/{repository}/{project}/run")
def run(repository, project, target_id=None):
    response = handoff_do(
        os.path.join(repository, "projects", project),
        "cloud run",
        vars={"target_id": target_id})
    return response


@router.get("/api/{repository}/{project}/log", response_class=PlainTextResponse)
def log(repository, project, start_time=None, end_time=None):
    file_name = f"./{project}.log"
    if os.path.isfile(file_name):
        os.remove(file_name)
    start_time = datetime.datetime.fromtimestamp(float(start_time)).isoformat()
    if end_time:
        end_time = datetime.datetime.fromtimestamp(float(end_time)).isoformat()
    handoff_do(
        os.path.join(repository, "projects", project),
        "cloud logs",
        vars={"start_time": start_time,
              "end_time": end_time,
              "file": file_name,
              "follow": False,
              },
        # async=True,
    )

    with open(file_name) as f:
        log = f.read()

    return log


@router.get("/api/{repository}/{project}/stats")
def stats(repository, project, start_time=None, end_time=None):
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
        vars={"start_time": start_time,
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
