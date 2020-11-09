import json, os, shutil, tempfile
import handoff
from handoff.config import ARTIFACTS_DIR

TEST_PROJECTS_DIR = "./handoff/test_projects"


def test_02_collect_stats():
    project_name = "02_collect_stats"
    project_dir = os.path.join(TEST_PROJECTS_DIR, project_name)
    text_file = "README.md"
    data = dict()
    with tempfile.TemporaryDirectory() as root_dir:
        workspaces_dir = os.path.join(root_dir, "workspaces")
        os.mkdir(workspaces_dir)
        shutil.copyfile(text_file, os.path.join(root_dir, text_file))
        workspace_dir = os.path.join(workspaces_dir, project_name)
        handoff.do("workspace install", project_dir, workspace_dir, data,
                   cloud_provider="aws",
                   cloud_platform="fargate",
                   container_provider="docker",
                   stage="prod",
                   push_artifacts=False)
        handoff.do("run local", project_dir, workspace_dir, data,
                   cloud_provider="aws",
                   cloud_platform="fargate",
                   container_provider="docker",
                   stage="prod",
                   push_artifacts=False)
        with open(os.path.join(workspace_dir, ARTIFACTS_DIR, "collect_stats.json")) as f:
            stats = json.load(f)
            assert(stats.get("rows_read") is not None)
