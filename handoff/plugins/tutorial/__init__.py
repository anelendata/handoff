import os, shutil
from handoff.core.utils import get_logger

LOGGER = get_logger(__name__)


def start(project_dir, workspace_dir, data, **kwargs):
    d, f = os.path.split(__file__)
    try:
        shutil.copytree(os.path.join(d, "../..",  "test_projects"),
                        os.path.join(os.getcwd(), "test_projects"))
    except FileExistsError:
        print("It looks like you already copied the test projects to ./test_projects")
    else:
        print("Copied the test projects to ./test_projects")
    print("Try running:")
    print("    handoff run local --project ./test_projects/01_word_count --workspace ./workspace")
    print("Then:")
    print("    cat ./workspace/artifacts/state")
    print("Then, continue on https://dev.handoff.cloud")
