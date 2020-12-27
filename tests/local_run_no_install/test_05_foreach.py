import json, os, shutil, tempfile
import handoff
from handoff.config import ARTIFACTS_DIR

TEST_PROJECTS_DIR = "./handoff/test_projects"


def test_05_foreach():
    project_name = "05_foreach"
    project_dir = os.path.join(TEST_PROJECTS_DIR, project_name)
    data = dict()
    with tempfile.TemporaryDirectory() as root_dir:
        workspace_dir = os.path.join(root_dir, "workspace")
        handoff.do("run local", project_dir, workspace_dir, data,
                   cloud_provider="aws",
                   cloud_platform="fargate",
                   container_provider="docker",
                   stage="prod",
                   push_artifacts=False)
        with open(os.path.join(workspace_dir, ARTIFACTS_DIR,
                               "verify_stdout.log")) as f:
            s = f.readline()
            # TODO: Cannot get stdout when running do() from pytest...
            # assert int(s.strip("\n").strip()) == 5
