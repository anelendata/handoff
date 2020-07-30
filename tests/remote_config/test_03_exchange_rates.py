import csv, datetime, json, logging, os, shutil, tempfile
import handoff
from handoff.config import ARTIFACTS_DIR, CONFIG_DIR

TEST_PROJECTS_DIR = "./test_projects"

LOGGER = logging.getLogger(__name__)


def test_03_exchange_rates():
    envs = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"]
    not_set = list()
    for env in envs:
        if os.environ.get(env) is None:
            not_set.append(env)
    assert len(not_set) == 0, "Please set environment variables: %s" % str(not_set)

    project_name = "03_exchange_rates"
    orig_project_dir = os.path.join(TEST_PROJECTS_DIR, project_name)

    data = dict()
    with tempfile.TemporaryDirectory() as root_dir:
        project_dir = os.path.join(root_dir, "project")
        shutil.copytree(orig_project_dir, project_dir)
        with open(os.path.join(project_dir, CONFIG_DIR, "tap-config.json"), "w") as f:
            config = {"base": "JPY",
                      "start_date": (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat()[:10]}
            json.dump(config, f)

        workspace_dir = os.path.join(root_dir, "workspace")

        allow_advanced_tier = False
        handoff.do("push_config", data, project_dir, workspace_dir, push_artifacts=False,
                   **{"allow_advanced_tier": allow_advanced_tier})
        handoff.do("push_files", data, project_dir, workspace_dir, push_artifacts=False)

        handoff.do("install", data, project_dir, workspace_dir, push_artifacts=False)

        handoff.do("run", data, None, workspace_dir, push_artifacts=True)

        handoff.do("delete_files", data, None, workspace_dir, push_artifacts=False,
                   **{"allow_advanced_tier": allow_advanced_tier})
        handoff.do("delete_artifacts", data, None, workspace_dir, push_artifacts=False,
                   **{"allow_advanced_tier": allow_advanced_tier})
        handoff.do("delete_config", data, None, workspace_dir, push_artifacts=False,
                   **{"allow_advanced_tier": allow_advanced_tier})

        files = os.listdir(os.path.join(workspace_dir, ARTIFACTS_DIR))
        rate_file = None
        for fn in files:
            if fn[:len("exchange_rate-")] == "exchange_rate-":
                rate_file = fn
                break
        with open(os.path.join(workspace_dir, ARTIFACTS_DIR, rate_file), "r") as f:
            rows = csv.DictReader(f)
            for row in rows:
                jpy =  row["JPY"]
                assert(float(jpy)==1.0)

        with open(os.path.join(workspace_dir, ARTIFACTS_DIR, "collect_stats.json"), "r") as f:
            stats = json.load(f)
            assert(stats.get("rows_read") is not None)
