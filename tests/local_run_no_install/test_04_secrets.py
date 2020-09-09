import json, os, shutil, tempfile
import handoff
from handoff.config import FILES_DIR, get_state

TEST_PROJECTS_DIR = "./handoff/test_projects"


def test_04_secrets():
    project_name = "04_secrets"
    project_dir = os.path.join(TEST_PROJECTS_DIR, project_name)
    text_file = "README.md"
    data = dict()
    with tempfile.TemporaryDirectory() as root_dir:
        workspaces_dir = os.path.join(root_dir, "workspaces")
        os.mkdir(workspaces_dir)
        shutil.copyfile(text_file, os.path.join(root_dir, text_file))
        workspace_dir = os.path.join(workspaces_dir, project_name)

        # tap-config.json will be parsed from templates
        tap_config_file = os.path.join(workspace_dir, FILES_DIR,
                                       "tap-config.json")
        assert os.path.isfile(tap_config_file) is False

        handoff.do("workspace", "init", project_dir, workspace_dir, data,
                   push_artifacts=False)
        handoff.do("files", "get_local", project_dir, workspace_dir, data,
                   push_artifacts=False)
        state = get_state()

        # date is registered as an env variable
        assert state["date"] == "2020-09-01"

        # base_currency is on-memory only
        assert state["base_currency"] == "USD"
        assert state.get_env("base_currency") is None

        assert os.path.isfile(tap_config_file) is True
        with open(tap_config_file) as f:
            tap_config = json.load(f)
            assert(tap_config.get("base") == "USD")
