import csv, datetime, json, logging, os, shutil, tempfile
import handoff
from handoff.config import (ARTIFACTS_DIR, FILES_DIR, BUCKET, IMAGE_VERSION)

TEST_PROJECTS_DIR = "./handoff/test_projects"

LOGGER = logging.getLogger(__name__)


def test_04_install():
    project_name = "04_install"
    orig_project_dir = os.path.join(TEST_PROJECTS_DIR, project_name)
    data = dict()
    with tempfile.TemporaryDirectory() as root_dir:
        project_dir = os.path.join(root_dir, "project")
        shutil.copytree(orig_project_dir, project_dir)
        start_date = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat()[:10]
        base_currency = "JPY"

        workspace_dir = os.path.join(root_dir, "workspace")

        # make up a bucket name for the test
        os.environ[BUCKET] = "test"
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
                   push_artifacts=False,
                   vars={"start_date": start_date, "base_currency": base_currency})

        files = os.listdir(os.path.join(workspace_dir, ARTIFACTS_DIR))
        rate_file = None
        for fn in files:
            if fn[:len("exchange_rate-")] == "exchange_rate-":
                rate_file = fn
                break
        with open(os.path.join(workspace_dir, ARTIFACTS_DIR, rate_file), "r") as f:
            rows = csv.DictReader(f)
            for row in rows:
                bc = row[base_currency]
                assert(float(bc) == 1.0)

        with open(os.path.join(workspace_dir, ARTIFACTS_DIR, "collect_stats.json"), "r") as f:
            stats = json.load(f)
            assert(stats.get("rows_read") is not None)
