import pytest

from handoff.core import task as T
from handoff.services import cloud


CONFIG = {"tasks": [
    {"name": "compare"},
    {"name": "fetch"},
    {"name": "load", "active": False},
    {"name": "verify"},
]}


def _run(monkeypatch, vars, config=CONFIG):
    ran = []
    monkeypatch.setattr(T, "_run_task", lambda task, *a, **k: ran.append(task["name"]) or 0)
    code = T.run(config, vars=vars)
    return code, ran


def test_no_selection_runs_every_active_task(monkeypatch):
    assert _run(monkeypatch, {}) == (0, ["compare", "fetch", "verify"])


def test_selection_runs_named_tasks_in_project_order(monkeypatch):
    assert _run(monkeypatch, {"_tasks": "verify,compare"}) == (0, ["compare", "verify"])


def test_named_inactive_task_runs(monkeypatch):
    assert _run(monkeypatch, {"_tasks": "load"}) == (0, ["load"])


def test_unknown_task_fails_before_anything_runs(monkeypatch):
    ran = []
    monkeypatch.setattr(T, "_run_task", lambda task, *a, **k: ran.append(task["name"]) or 0)
    with pytest.raises(ValueError, match="Unknown task"):
        T.run(CONFIG, vars={"_tasks": "compare,lod"})
    assert ran == []


def test_empty_selection_is_an_error():
    with pytest.raises(ValueError):
        T._selected_tasks(CONFIG, {"_tasks": " , "})


def test_failed_selected_task_stops_the_rest(monkeypatch):
    ran = []
    monkeypatch.setattr(T, "_run_task", lambda task, *a, **k: ran.append(task["name"]) or (1 if task["name"] == "compare" else 0))
    assert T.run(CONFIG, vars={"_tasks": "compare,verify"}) == 1
    assert ran == ["compare"]


def test_cloud_run_puts_selection_in_vars_env():
    assert cloud._add_selected_tasks({"HO_STAGE": "dev"}, {"_tasks": "load"}) == {"HO_STAGE": "dev", "__VARS": "_tasks=load"}
    envs = cloud._add_selected_tasks({"__VARS": "start_datetime=2026-01-01"}, {"_tasks": "compare,fetch"})
    assert envs["__VARS"] == "start_datetime=2026-01-01 _tasks=compare,fetch"
    assert cloud._add_selected_tasks({"a": "b"}, {}) == {"a": "b"}


def test_cloud_run_rejects_unsafe_or_duplicate_selection():
    with pytest.raises(ValueError):
        cloud._add_selected_tasks({}, {"_tasks": "load; rm -rf /"})
    with pytest.raises(ValueError):
        cloud._add_selected_tasks({"__VARS": "_tasks=compare"}, {"_tasks": "load"})


def test_cli_tasks_option_sets_the_var(monkeypatch):
    from handoff import main as M
    seen = {}
    monkeypatch.setattr(M, "do", lambda command, **kw: seen.update(kw) or None)
    monkeypatch.setattr(M, "check_announcements", lambda **kw: None)
    monkeypatch.setattr("sys.argv", ["handoff", "run", "local", "-p", "p", "-w", "w", "--tasks", "compare,load"])
    M.main()
    assert seen["vars"]["_tasks"] == "compare,load"
