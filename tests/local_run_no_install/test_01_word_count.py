import os, shutil, tempfile
import handoff
from handoff.config import ARTIFACTS_DIR

TEST_PROJECTS_DIR = "./test_projects"


def test_01_word_count():
    project_name = "01_word_count"
    project_dir = os.path.join(TEST_PROJECTS_DIR, project_name)
    text_file = "README.md"
    data = dict()
    with tempfile.TemporaryDirectory() as root_dir:
        workspaces_dir = os.path.join(root_dir, "workspaces")
        os.mkdir(workspaces_dir)
        shutil.copyfile(text_file, os.path.join(root_dir, text_file))
        workspace_dir = os.path.join(workspaces_dir, project_name)
        handoff.do("run", "local", data, project_dir, workspace_dir, push_artifacts=False)
        with open(os.path.join(workspace_dir, ARTIFACTS_DIR, "state")) as f:
            state = f.read()
            assert(int(state) > 40)
