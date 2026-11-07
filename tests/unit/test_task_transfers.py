import os

import pytest

from handoff.core import task as T
from handoff.services import cloud


class FakePlatform:
    """In-memory bucket keyed like <task>/<key>, without the task prefix."""
    def __init__(self):
        self.objects = {}

    def upload_file(self, local_path, key):
        self.objects[key] = open(local_path).read()

    def upload_dir(self, local_dir, key):
        for root, _, files in os.walk(local_dir):
            for fn in files:
                full = os.path.join(root, fn)
                self.objects[os.path.join(key, full[len(local_dir) + 1:])] = open(full).read()

    def download_file(self, local_path, key):
        if key not in self.objects:
            raise Exception("404")
        open(local_path, "w").write(self.objects[key])

    def download_dir(self, local_dir, prefix):
        for k, v in self.objects.items():
            if k.startswith(prefix):
                dest = os.path.join(local_dir, k[len(prefix):])
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                open(dest, "w").write(v)


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fake = FakePlatform()
    monkeypatch.setattr(cloud, "get_platform", lambda *a, **k: fake)
    state = {"run_id": "r1"}
    monkeypatch.setattr(T, "get_state", lambda: state)
    return fake


def _writer(files):
    def run_task(task, *a, **k):
        for path, text in files.get(task["name"], {}).items():
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            open(path, "w").write(text)
        return 1 if task["name"] == "fails" else 0
    return run_task


CONFIG = {"tasks": [
    {"name": "compare", "upload": [{"path": "out/compare", "to": "runs/{{ run_id }}/compare"},
                                   {"path": "out/summary.json", "to": "runs/{{ run_id }}/summary.json"}]},
    {"name": "load", "active": False,
     "download": [{"from": "runs/{{ run_id }}/compare", "path": "in/compare"},
                  {"from": "runs/{{ run_id }}/summary.json", "path": "in/summary.json"}]},
]}


def test_upload_after_success_then_download_in_a_later_run(env, monkeypatch):
    monkeypatch.setattr(T, "_run_task", _writer({"compare": {"out/compare/a.tsv": "1", "out/compare/sub/b.tsv": "2", "out/summary.json": "{}"}}))
    assert T.run(CONFIG, vars={"_tasks": "compare"}, push_artifacts=True) == 0
    assert env.objects == {"runs/r1/compare/a.tsv": "1", "runs/r1/compare/sub/b.tsv": "2", "runs/r1/summary.json": "{}"}
    monkeypatch.setattr(T, "_run_task", _writer({}))
    assert T.run(CONFIG, vars={"_tasks": "load"}, push_artifacts=True) == 0
    assert open("in/compare/sub/b.tsv").read() == "2"
    assert open("in/summary.json").read() == "{}"


def test_no_upload_when_the_task_fails(env, monkeypatch):
    cfg = {"tasks": [{"name": "fails", "upload": [{"path": "out", "to": "runs/x"}]}]}
    monkeypatch.setattr(T, "_run_task", _writer({"fails": {"out/a": "partial"}}))
    assert T.run(cfg, vars={}, push_artifacts=True) == 1
    assert env.objects == {}


def test_missing_download_fails_the_task_before_it_runs(env, monkeypatch):
    ran = []
    monkeypatch.setattr(T, "_run_task", lambda task, *a, **k: ran.append(task["name"]) or 0)
    assert T.run(CONFIG, vars={"_tasks": "load"}, push_artifacts=True) == 1
    assert ran == []


def test_missing_upload_path_fails(env, monkeypatch):
    monkeypatch.setattr(T, "_run_task", _writer({}))
    assert T.run(CONFIG, vars={"_tasks": "compare"}, push_artifacts=True) == 1


@pytest.mark.parametrize("key", ["artifacts/last/x", "files/scripts", "../other_task/x", "/abs/key"])
def test_keys_under_handoff_prefixes_or_outside_are_refused(env, key):
    with pytest.raises(ValueError):
        T._transfer_key(key, "to", "t", {})


def test_local_run_without_push_artifacts_skips_transfers(env, monkeypatch):
    ran = []
    monkeypatch.setattr(T, "_run_task", lambda task, *a, **k: ran.append(task["name"]) or 0)
    assert T.run(CONFIG, vars={"_tasks": "load"}, push_artifacts=False) == 0
    assert ran == ["load"] and env.objects == {}
