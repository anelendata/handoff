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
    for pipe in config["tasks"]:
        if not pipe.get("active", True):
            continue
        kill_downstream_on_fail = not pipe.get(
            "run_downstream_on_fail", False)

        stdout, stderr, exit_code = _run_task(
            pipe, state, ARTIFACTS_DIR,
            kill_downstream_on_fail=kill_downstream_on_fail)

        LOGGER.info("Pipeline %s exited with code %d" %
                    (pipe.get("name", ""), exit_code))
        if exit_code != 0:
            break


def run_local(config, **kwargs):
    """`handoff run local -p <project_directory> -w <workspace_directory>`
    Run the task locally.
    """
    return run(config, **kwargs)
