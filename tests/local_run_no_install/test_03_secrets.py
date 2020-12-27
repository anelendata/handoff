import json, os, shutil, tempfile
import handoff
from handoff.config import ARTIFACTS_DIR

TEST_PROJECTS_DIR = "./handoff/test_projects"


def test_03_variables():
    project_name = "03_secrets"
    project_dir = os.path.join(TEST_PROJECTS_DIR, project_name)
    text_file = "README.md"
    data = dict()
    with tempfile.TemporaryDirectory() as root_dir:
        shutil.copyfile(text_file, os.path.join(root_dir, text_file))
        workspace_dir = os.path.join(root_dir, "workspace")
        handoff.do("run local", project_dir, workspace_dir, data,
                   cloud_provider="aws",
                   cloud_platform="fargate",
                   container_provider="docker",
                   stage="prod",
                   push_artifacts=False)
        with open(os.path.join(workspace_dir, ARTIFACTS_DIR,
                               "show_curl_command_stdout.log")) as f:
            s = f.readline()
            assert s.strip("\n").strip() == "curl -u my_user_name:isawsomeonewithastickynotewithapasswordonthelaptopscreenworkinginapubliccafeinpaloalto https://example.com"
