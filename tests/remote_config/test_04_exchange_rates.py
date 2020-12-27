import csv, datetime, json, logging, os, shutil, tempfile
import handoff
from handoff.config import (ARTIFACTS_DIR, FILES_DIR,
                            CLOUD_PROVIDER, CLOUD_PLATFORM,
                            CONTAINER_PROVIDER, BUCKET)

TEST_PROJECTS_DIR = "./handoff/test_projects"

LOGGER = logging.getLogger(__name__)


def test_04_exchange_rates():
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

    project_name = "04_install"
    orig_project_dir = os.path.join(TEST_PROJECTS_DIR, project_name)

    data = dict()
    with tempfile.TemporaryDirectory() as root_dir:
        project_dir = os.path.join(root_dir, "project")
        shutil.copytree(orig_project_dir, project_dir)
        base_currency = "JPY"
        start_date = (datetime.datetime.now() - datetime.timedelta(days=7)
                      ).isoformat()[:10]
        workspace_dir = os.path.join(root_dir, "workspace")
        kwargs = {
            "cloud_provider": "aws",
            "cloud_platform": "fargate",
            "container_provider": "docker",
            "stage": "prod"
        }

        handoff.do("config push", project_dir, workspace_dir, data=data,
                   push_artifacts=False, **kwargs)
        handoff.do("files push", project_dir, workspace_dir, data=data,
                   push_artifacts=False, **kwargs)

        handoff.do("workspace install", project_dir, workspace_dir, data=data,
                   push_artifacts=False, **kwargs)

        handoff.do("run", project_dir, workspace_dir, data=data,
                   push_artifacts=True,
                   vars={"start_date": start_date, "base_currency": base_currency}, **kwargs)

        handoff.do("files delete", project_dir, None, data=data,
                   push_artifacts=False, **kwargs)
        handoff.do("artifacts delete", project_dir, None, data=data,
                   push_artifacts=False, **kwargs)
        handoff.do("config delete", project_dir, None, data=data,
                   push_artifacts=False, **kwargs)
