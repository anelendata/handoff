import os, shutil
from handoff.utils import get_logger as _get_logger

LOGGER = _get_logger(__name__)


def make(project_dir, workspace_dir, data, **kwargs):
    """Copy the test projects to the test_projects under the current directory
    """
    d, f = os.path.split(__file__)
    try:
        shutil.copytree(os.path.join(d, "../..",  "test_projects"),
                        os.path.join(os.getcwd(), "projects"))
    except FileExistsError:
        print("It looks like you already copied the test projects to ./projects")
    else:
        print("Copied the test projects to ./projects")
    print("Now just do:")
    print("    ./projects/start")
    print("to start the even-monkeys-can-follow tutorial.")
