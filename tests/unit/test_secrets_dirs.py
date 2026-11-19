import logging
import os

import pytest
import yaml

from handoff.core import admin


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def _secrets(path, entries):
    _write(path, yaml.safe_dump(entries))


def _project(root, project_yml, rel="projects/acme/billing/invoices"):
    project_dir = os.path.join(root, rel)
    _write(os.path.join(project_dir, "project.yml"), project_yml)
    return project_dir


@pytest.fixture
def stage(monkeypatch):
    state = {"_stage_": ""}
    monkeypatch.setattr(admin, "get_state", lambda: state)
    return state


@pytest.fixture
def root(tmp_path):
    root = str(tmp_path)
    _secrets(os.path.join(root, "projects", ".secrets", "secrets.yml"), [
        {"key": "google_client_secret", "file": "google.json", "level": "resource group"},
        {"key": "api_key", "value": "from-top"},
    ])
    _write(os.path.join(root, "projects", ".secrets", "google.json"), '{"fake": 1}')
    _secrets(os.path.join(root, "projects", "acme", "billing", ".secrets", "secrets.yml"), [
        {"key": "api_key", "value": "billing-key"},
        {"key": "subdomain", "value": "billing-sub"},
        {"key": "password", "value": "billing-pw"},
    ])
    _secrets(os.path.join(root, "projects", "acme", "billing", ".secrets", "dev_secrets.yml"), [
        {"key": "api_key", "value": "billing-dev-key"},
        {"key": "subdomain", "value": "billing-dev-sub"},
    ])
    return root


SHARED = "secrets_dirs:\n- projects/.secrets\n- projects/acme/billing/.secrets\n"


def test_without_secrets_dirs_reads_only_the_projects_own_file(root, stage):
    project_dir = _project(root, "description: x\n")
    _secrets(os.path.join(project_dir, ".secrets", "secrets.yml"), [{"key": "api_key", "value": "own"}])
    got = admin._secrets_get_local(project_dir, None)
    assert list(got) == ["api_key"]
    assert admin.SECRETS == {"api_key": "own"}


def test_without_secrets_dirs_and_no_file_returns_none(root, stage, caplog):
    project_dir = _project(root, "description: x\n")
    with caplog.at_level(logging.WARNING):
        assert admin._secrets_get_local(project_dir, None) is None
    assert "does not exsist" in caplog.text


def test_shared_folders_in_order_then_the_projects_own(root, stage):
    project_dir = _project(root, SHARED)
    _secrets(os.path.join(project_dir, ".secrets", "secrets.yml"), [{"key": "password", "value": "own-pw"}])
    got = admin._secrets_get_local(project_dir, None)
    assert admin.SECRETS == {"google_client_secret": '{"fake": 1}', "api_key": "billing-key",
                             "subdomain": "billing-sub", "password": "own-pw"}
    assert got["google_client_secret"]["level"] == "resource group"


def test_folders_are_found_from_any_depth(root, stage):
    project_dir = _project(root, SHARED, rel="projects/acme/billing/deep/er/invoices")
    admin._secrets_get_local(project_dir, None)
    assert admin.SECRETS["subdomain"] == "billing-sub"


def test_dev_stage_reads_dev_secrets_and_skips_folders_without_one(root, stage):
    stage["_stage_"] = "dev_"
    project_dir = _project(root, SHARED)
    admin._secrets_get_local(project_dir, None)
    # projects/.secrets has no dev_secrets.yml, so only the billing dev file is read.
    assert admin.SECRETS == {"api_key": "billing-dev-key", "subdomain": "billing-dev-sub"}


def test_secrets_list_picks_keys_from_shared_folders_only(root, stage):
    project_dir = _project(root, SHARED + "secrets:\n"
                                         "- key: google_client_secret\n  level: resource group\n"
                                         "- key: api_key\n- key: subdomain\n")
    _secrets(os.path.join(project_dir, ".secrets", "secrets.yml"), [{"key": "extra", "value": "own"}])
    got = admin._secrets_get_local(project_dir, None)
    # password is in the billing file but not listed; the project's own keys are always taken.
    assert sorted(got) == ["api_key", "extra", "google_client_secret", "subdomain"]
    assert "password" not in admin.SECRETS


def test_listed_task_key_missing_everywhere_is_an_error(root, stage):
    project_dir = _project(root, SHARED + "secrets:\n- key: api_key\n- key: username\n  level: task\n")
    with pytest.raises(Exception, match=r"username"):
        admin._secrets_get_local(project_dir, None)


def test_listed_resource_group_key_missing_is_a_warning(root, stage, caplog):
    project_dir = _project(root, SHARED + "secrets:\n- key: api_key\n- key: slack_token\n  level: resource group\n")
    with caplog.at_level(logging.WARNING):
        got = admin._secrets_get_local(project_dir, None)
    assert list(got) == ["api_key"]
    assert "Unregistered resource group level secret: slack_token" in caplog.text


def test_secrets_dir_var_replaces_only_the_projects_own_folder(root, stage, tmp_path):
    project_dir = _project(root, SHARED)
    other = str(tmp_path / "elsewhere")
    _secrets(os.path.join(other, "secrets.yml"), [{"key": "api_key", "value": "var-dir"}])
    admin._secrets_get_local(project_dir, None, vars={"secrets_dir": other})
    assert admin.SECRETS["api_key"] == "var-dir"
    assert admin.SECRETS["subdomain"] == "billing-sub"


def test_no_stage_file_in_any_folder_returns_none(root, stage, caplog):
    stage["_stage_"] = "prod_"
    project_dir = _project(root, SHARED)
    with caplog.at_level(logging.WARNING):
        assert admin._secrets_get_local(project_dir, None) is None
    assert "No prod_secrets.yml" in caplog.text


@pytest.mark.parametrize("entries,match", [
    ("secrets_dirs:\n- ../outside\n", "without '..'"),
    ("secrets_dirs:\n- /etc\n", "without '..'"),
    ("secrets_dirs:\n- projects/nowhere/.secrets\n", "not found"),
    ("secrets_dirs: projects/.secrets\n", "must be a list"),
    ("secrets_dirs:\n- {a: 1}\n", "must be a path"),
    ("secrets_dirs:\n- projects/.secrets/secrets.yml\n", "not found"),
    (SHARED + "secrets:\n- api_key\n", "entries with a key"),
])
def test_bad_secrets_dirs_fail(root, stage, entries, match):
    project_dir = _project(root, entries)
    with pytest.raises(Exception, match=match):
        admin._secrets_get_local(project_dir, None)


def test_secrets_push_pushes_the_merged_set_with_levels(root, stage, monkeypatch):
    project_dir = _project(root, SHARED + "secrets:\n"
                                         "- key: google_client_secret\n  level: resource group\n"
                                         "- key: api_key\n- key: subdomain\n")
    pushed = []

    class Platform:
        def get_parameter_key_full_path(self, key, resource_group_level=False):
            return ("/rg/" if resource_group_level else "/rg/task/") + key

        def push_parameter(self, key, value, resource_group_level=False, **kwargs):
            pushed.append((key, value, resource_group_level))

    class State(dict):
        def validate_env(self, keys):
            pass

    monkeypatch.setattr(admin, "get_state", lambda: State(_stage_=""))
    monkeypatch.setattr(admin.cloud, "get_platform", lambda *a, **k: Platform())
    assert admin.secrets_push(project_dir, None, yes=True)["status"] == "success"
    assert sorted(pushed) == [("api_key", "billing-key", False),
                              ("google_client_secret", '{"fake": 1}', True),
                              ("subdomain", "billing-sub", False)]
