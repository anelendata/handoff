import datetime, json, logging, os, shlex, sys, venv
import subprocess
from typing import Dict

from jinja2 import Template as _Template

from handoff import utils
from handoff.config import get_state, ARTIFACTS_DIR
from handoff.core.operators import _run_task


LOGGER = utils.get_logger(__name__)


def run(config: Dict, **kwargs) -> None:
    """`handoff run -w <workspace_directory> -e resource_group=<resource_group_name> task=<task_name>`
    Run the task by the configurations and files stored in the remote parameter store and the file store.
    """
    state = get_state()
    kill_downstream_on_fail = config.get("kill_downstream_on_fail", True)
    kill_loop_on_fail = config.get("kill_loop_on_fail", True)
    exit_code = 0
    for task in config["tasks"]:
        if not task.get("active", True):
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
        LOGGER.info("Task %s exited with code %d" %
                    (task.get("name", ""), exit_code))
        if exit_code > 0:
            if kill_downstream_on_fail:
                LOGGER.warning("Not running the rest of the tasks.")
                break
    return exit_code


def run_local(config, **kwargs):
    """`handoff run local -p <project_directory> -w <workspace_directory>`
    Run the task locally.
    """
    return run(config, **kwargs)
