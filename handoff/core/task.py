import datetime
import json
import logging
import os
import psutil
import shlex
import signal
import subprocess
import sys
import venv
from typing import Dict

from jinja2 import Template as _Template
from handoff import utils
from handoff.config import get_state, ARTIFACTS_DIR
from handoff.core.operators import _run_task


LOGGER = utils.get_logger(__name__)


def shutdown(signal_id, from_):
    LOGGER.warning(f"Received SIGTERM. Gracefully shutting down.")
    parent_pid = os.getpid()
    try:
        parent = psutil.Process(parent_pid)
    except psutil.NoSuchProcess:
        LOGGER.info("No child processes running.")
        return
    children = parent.children(recursive=True)
    for proc in children:
        proc.send_signal(signal.SIGTERM)
        LOGGER.info(f"SIGINT sent to a child pid {proc.pid}")

    for proc in children:
        try:
            proc.communicate(timeout=30)
        except TimeoutExpired:
            LOGGER.warning(f"Process {str(proc.pid)} not responding to SIGINT. Killing...")
            proc.kill()


SELECT_TASKS_VAR = "_tasks"


def _selected_tasks(config: Dict, vars: Dict):
    """Return the task names given by --tasks or -v _tasks=a,b, or None to run
    every active task. Named tasks run in project.yml order even if they are
    inactive, so a step can stay inactive by default and run only when named.
    Unknown names are an error before any task runs.
    """
    value = vars.get(SELECT_TASKS_VAR)
    if value is None or value == "":
        return None
    names = [n.strip() for n in str(value).split(",") if n.strip()]
    if not names:
        raise ValueError(f"{SELECT_TASKS_VAR} is set but names no task")
    known = [t.get("name") for t in config.get("tasks") or []]
    unknown = [n for n in names if n not in known]
    if unknown:
        raise ValueError(f"Unknown task(s) in {SELECT_TASKS_VAR}: {', '.join(unknown)}. " +
                         f"Tasks in project.yml: {', '.join(str(k) for k in known)}")
    LOGGER.info(f"Running only the selected tasks: {', '.join(n for n in known if n in names)}")
    return set(names)


def run(config: Dict, **kwargs) -> None:
    """`handoff run -w <workspace_directory> -e resource_group=<resource_group_name> task=<task_name>`
    Run the task by the configurations and files stored in the remote parameter store and the file store.
    """
    state = get_state()
    kill_downstream_on_fail = config.get("kill_downstream_on_fail", True)
    kill_loop_on_fail = config.get("kill_loop_on_fail", True)
    exit_code = 0
    signal.signal(signal.SIGTERM, shutdown)
    selected = _selected_tasks(config, kwargs.get("vars") or {})
    for task in config["tasks"]:
        if selected is None:
            if not task.get("active", True):
                continue
        elif task.get("name") not in selected:
            LOGGER.info(f"Task {task.get('name', '')} skipped: not in {SELECT_TASKS_VAR}")
            continue
        kill_ds_on_fail = task.get(
            "kill_downstream_on_fail",
            kill_downstream_on_fail,
        )
        kill_lp_on_fail = task.get(
            "kill_loop_on_fail",
            kill_loop_on_fail,
        )
        try:
            exit_code = _run_task(
                task,
                state,
                ARTIFACTS_DIR,
                kill_downstream_on_fail=kill_ds_on_fail,
                kill_loop_on_fail=kill_lp_on_fail,
            )
        except Exception as e:
            LOGGER.error(str(e))
            exit_code = 1
        LOGGER.info(f"Task {task.get('name', '')} exited with code {str(exit_code)}")
        if exit_code > 0:
            if kill_ds_on_fail:
                LOGGER.warning("Not running the rest of the tasks.")
                break
    return exit_code


def run_local(config, **kwargs):
    """`handoff run local -p <project_directory> -w <workspace_directory>`
    Run the task locally.
    """
    return run(config, **kwargs)
