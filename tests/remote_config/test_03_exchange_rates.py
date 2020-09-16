import csv, datetime, json, logging, os, shutil, tempfile
import handoff
from handoff.config import (ARTIFACTS_DIR, CONFIG_DIR,
                            CLOUD_PROVIDER, CLOUD_PLATFORM,
                            CONTAINER_PROVIDER,
                            BUCKET)

TEST_PROJECTS_DIR = "./handoff/test_projects"

LOGGER = logging.getLogger(__name__)


def test_03_exchange_rates():
    os.environ[CLOUD_PROVIDER] = os.environ.get(CLOUD_PROVIDER, "aws")
    os.environ[CLOUD_PLATFORM] = os.environ.get(CLOUD_PLATFORM, "fargate")
    os.environ[CONTAINER_PROVIDER] = (
        os.environ.get(CONTAINER_PROVIDER, "docker"))

    if (not os.environ.get("AWS_PROFILE") and
            not os.environ.get("AWS_ACCESS_KEY_ID")):
        print("Please set environment variable AWS_PROFILE or " +
              "(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) to run this test.")
        assert False

    if os.environ.get(BUCKET):
        del os.environ[BUCKET]

    project_name = "03_exchange_rates"
    orig_project_dir = os.path.join(TEST_PROJECTS_DIR, project_name)

    data = dict()
    with tempfile.TemporaryDirectory() as root_dir:
        project_dir = os.path.join(root_dir, "project")
        shutil.copytree(orig_project_dir, project_dir)
        with open(os.path.join(project_dir, CONFIG_DIR, "tap-config.json"),
                  "w") as f:
            config = {"base": "JPY",
                      "start_date": (datetime.datetime.now() -
                                     datetime.timedelta(days=7)
                                     ).isoformat()[:10]}
            json.dump(config, f)

        workspace_dir = os.path.join(root_dir, "workspace")

        data["allow_advanced_tier"] = False
        handoff.do("config", "push", project_dir, workspace_dir, data,
                   push_artifacts=False)
        handoff.do("files", "push", project_dir, workspace_dir, data,
                   push_artifacts=False)

        handoff.do("workspace", "install", project_dir, workspace_dir, data,
                   push_artifacts=False)

        handoff.do("run", "", None, workspace_dir, data,
                   push_artifacts=True)

        handoff.do("files", "delete", project_dir, None, data,
                   push_artifacts=False)
        handoff.do("artifacts", "delete", project_dir, None, data,
                   push_artifacts=False)
        handoff.do("config", "delete", project_dir, None, data,
                   push_artifacts=False)

        files = os.listdir(os.path.join(workspace_dir, ARTIFACTS_DIR))
        rate_file = None
        for fn in files:
            if fn[:len("exchange_rate-")] == "exchange_rate-":
                rate_file = fn
                break
        assert rate_file is not None
        with open(os.path.join(workspace_dir, ARTIFACTS_DIR, rate_file),
                  "r") as f:
            rows = csv.DictReader(f)
            for row in rows:
                jpy = row["JPY"]
                assert(float(jpy) == 1.0)

        with open(os.path.join(workspace_dir, ARTIFACTS_DIR,
                               "collect_stats.json"), "r") as f:
            stats = json.load(f)
            assert(stats.get("rows_read") is not None)
