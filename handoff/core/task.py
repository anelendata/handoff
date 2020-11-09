import datetime, json, logging, os, shlex, sys, venv
import subprocess
from typing import Dict

from jinja2 import Template as _Template

from handoff import utils
from handoff.config import get_state


LOGGER = utils.get_logger(__name__)

ARTIFACTS_DIR = ".artifacts"


def _get_params(args=None):
    """
    Pack up the python path, work directory, and current directory into a dict
    """
    params = utils.get_python_info(__name__)
    if args:
        params.update(args)
    return params


def _get_env():
    """
    Make sure proper PYTHONPATH is in the environmenta variable
    and returns the dict copy.
    """
    env = os.environ.copy()
    # env["PYTHONPATH"] = ":".join(sys.path)
    return env


def _get_command_string(command, argstring, params):
    """
    Construct a shell command string from a template, inserting virtual env
    and parameters.

    Available params:
    - python
    - code_dir
    - work_dir
    """
    if argstring is None:
        argstring = ""
    command = "%s %s" % (command,  argstring)

    template = _Template(command)
    command = template.render(**params)

    if params.get("venv"):
        command = '/bin/bash -c "source {code_dir}/{venv}/bin/activate && '.format(**params) + command + '"'

    return command


def _get_commands(params, data):
    commands = list()
    for command in params["commands"]:
        if not command.get("active", True):
            continue
        params = _get_params(data)
        params["venv"] = command.get("venv", None)
        command_str = _get_command_string(command["command"],
                                          command.get("args", None), params)
        commands.append(command_str)
    return commands


def _get_time_window(data):
    iso_str = data.get("iso_format", True)
    start_offset = datetime.timedelta(days=data.get("start_offset_days", -1))
    end_offset = datetime.timedelta(days=data.get("duration_days", 1))

    start_at, end_at = utils.get_time_window(
        data,
        start_offset=start_offset,
        end_offset=end_offset,
        iso_str=iso_str)
    return start_at, end_at


def run(
    config:Dict,
    **kwargs) -> None:
    """`handoff run -w <workspace_directory> -e resource_group=<resource_group_name> task=<task_name>`
    Run the task by the configurations and files stored in the remote parameter store and the file store.
    """
    state = get_state()
    commands = _get_commands(config, state)

    env = _get_env()

    # In Docker container, it takes shell=True to run a subprocess without causing Permission error (13)
    # and to run with shell=True, we need to feed the entire cmd string with args without splitting.
    # (subprocess.Popen(shlex.split(command_str),...)
    # In the olden days, it was never recommended for a container to run multiple processes.
    # Now the guideline is "Each container should have only one concern." and
    # "Limiting each container to one process is a good rule of thumb, but it is not a hard and fast rule."
    # https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#decouple-applications
    procs = list()
    procs.append(subprocess.Popen([commands[0]], stdout=subprocess.PIPE,
                                  env=env, shell=True))

    for i in range(1, len(commands)):
        try:
            procs.append(subprocess.Popen([commands[i]],
                                          stdin=procs[i - 1].stdout,
                                          stdout=subprocess.PIPE,
                                          env=env, shell=True))
        except subprocess.CalledProcessError as e:
            LOGGER.error("Error:" + str(e))
            raise

    for i in range(0, len(commands) - 1):
        return_code = procs[i].wait()
        if return_code > 0:
            print(return_code)
            for j in range(i, len(commands) - 1):
                procs[j].terminate()
            raise Exception("Process %d (%s) exited with code %d" %
                            (i, commands[i], return_code))

    stdout, stderr = procs[-1].communicate()

    if stdout:
        stdout = stdout.decode("utf-8").strip("\n").strip(" ")
    if stderr:
        stderr = stderr.decode("utf-8").strip("\n").strip(" ")

    LOGGER.debug("STDOUT of the last process:\n%s\n    " % stdout)
    LOGGER.debug("STDERR of the last process:\n%s\n    " % stderr)

    return stdout



def run_local(config, **kwargs):
    """`handoff run local -p <project_directory> -w <workspace_directory>`
    Run the task locally.
    """
    return run(config, **kwargs)


def show_commands(config, data={}, **kwargs):
    """`handoff show commands -p <project_directory>`
    Show the shell commands that drives the task.
    """
    start_at, end_at = _get_time_window(data)
    data.update({"start_at": start_at, "end_at": end_at})
    commands = _get_commands(config, data)
    for command in commands:
        print(command)
