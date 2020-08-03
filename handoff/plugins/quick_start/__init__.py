import os, shutil
from handoff.core.utils import get_logger

LOGGER = get_logger(__name__)


def start(project_dir, workspace_dir, data, **kwargs):
    d, f = os.path.split(__file__)
    try:
        shutil.copytree(os.path.join(d, "../..",  "test_projects"),
                        os.path.join(os.getcwd(), "projects"))
    except FileExistsError:
        print("It looks like you already copied the test projects to ./projects")
    else:
        print("Copied the test projects to ./projects")
    print("Now just enter:")
    print("    ./projects/begin")
    print("to start the even-monkeys-can-follow tutorial.")
