import json, os, shutil, tempfile
import handoff
from handoff.config import ARTIFACTS_DIR

TEST_PROJECTS_DIR = "./handoff/test_projects"


def test_02_variables():
    project_name = "02_commands_and_vars"
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
                               "show_content_stdout.log"), "r") as f:
            s = f.readline()
            assert s.strip("\n").strip() == "The Great Dictator"
