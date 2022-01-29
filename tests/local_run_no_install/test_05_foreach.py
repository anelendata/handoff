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
        retries = 5
        s = None
        while retries > 0:
            with open(os.path.join(workspace_dir, ARTIFACTS_DIR,
                                   "verify_result_stdout.log"), "r") as f:
                s = f.readline()
            if s and len(s) > 0:
                break
        assert int(s.strip("\n").strip()) == 5


def test_05a_foreach_no_kill_on_fail():
    project_name = "05a_foreach_except"
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
        retries = 5
        s = None
        while retries > 0:
            with open(os.path.join(workspace_dir, ARTIFACTS_DIR,
                                   "verify_result_stdout.log"), "r") as f:
                s = f.readline()
            if s and len(s) > 0:
                break
        # The output line sums to 4 with 1, 2, 3, 5 (skipping the fail on 4)
        assert int(s.strip("\n").strip()) == 4
