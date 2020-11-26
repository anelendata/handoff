import datetime, json, logging, os, shlex, sys, venv
import subprocess
from typing import Dict

from jinja2 import Template as _Template

from handoff import utils
from handoff.config import get_state, ARTIFACTS_DIR


LOGGER = utils.get_logger(__name__)


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


def _get_commands_org(params, data):
    commands = list()
    for command in params["run"]:
        if not command.get("active", True):
            continue
        params = _get_params(data)
        params["venv"] = command.get("venv", None)
        command_str = _get_command_string(command["command"],
                                          command.get("args", None), params)
        commands.append(command_str)
    return commands


def _get_commands(piped_commands, data):
    commands = list()
    for command in piped_commands:
        if not command.get("active", True):
            continue
        params = _get_params(data)
        params["venv"] = command.get("venv", None)
        command_str = _get_command_string(command["command"],
                                          command.get("args", None), params)
        commands.append(command_str)
    return commands


def run_pipe(
    pipe:str,
    state:Dict
    ) -> None:
    """`handoff run -w <workspace_directory> -e resource_group=<resource_group_name> task=<task_name>`
    Run the task by the configurations and files stored in the remote parameter store and the file store.
    """
    pipe_name = pipe["name"]
    commands = _get_commands(pipe["commands"], state)

    env = _get_env()

    # In Docker container, it takes shell=True to run a subprocess without causing Permission error (13)
    # and to run with shell=True, we need to feed the entire cmd string with args without splitting.
    # (subprocess.Popen(shlex.split(command_str),...)
    # In the olden days, it was never recommended for a container to run multiple processes.
    # Now the guideline is "Each container should have only one concern." and
    # "Limiting each container to one process is a good rule of thumb, but it is not a hard and fast rule."
    # https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#decouple-applications
    # Also see
    # https://docs.python.org/3/library/subprocess.html#security-considerations
    procs = list()
    procs.append(subprocess.Popen([commands[0]], stdout=subprocess.PIPE,
                                  env=env, shell=True))

    for i in range(1, len(commands)):
        procs.append(subprocess.Popen([commands[i]],
                                      stdin=procs[i - 1].stdout,
                                      stdout=subprocess.PIPE,
                                      env=env, shell=True))

    for i in range(0, len(commands) - 1):
        return_code = procs[i].wait()
        if return_code > 0:
            LOGGER.error("Process %d (%s) exited with code %d" %
                         (i, commands[i], return_code))
            # Immediately kill the downstream processes
            for j in range(i, len(commands) - 1):
                procs[j].terminate()

    # This assumes the data is not big. Use stdout, stderr in the last process
    # only for logging purposes, not passing big data.
    # https://docs.python.org/3/library/subprocess.html#subprocess.Popen.communicate
    stdout, stderr = procs[-1].communicate()

    if stdout:
        stdout = stdout.decode("utf-8").strip("\n").strip(" ")
    if stderr:
        stderr = stderr.decode("utf-8").strip("\n").strip(" ")

    if stdout:
        with open(os.path.join(ARTIFACTS_DIR, pipe_name + "_stdout.log"), "w") as f:
            f.write(stdout)
    if stderr:
        with open(os.path.join(ARTIFACTS_DIR, pipe_name + "_stderr.log"), "w") as f:
            f.write(stderr)

    return stdout, stderr


def run(
    config:Dict,
    **kwargs) -> None:
    """`handoff run -w <workspace_directory> -e resource_group=<resource_group_name> task=<task_name>`
    Run the task by the configurations and files stored in the remote parameter store and the file store.
    """
    state = get_state()
    for pipe in config["pipelines"]:
        if not pipe.get("active", True):
            continue
        run_pipe(pipe, state)


def run_local(config, **kwargs):
    """`handoff run local -p <project_directory> -w <workspace_directory>`
    Run the task locally.
    """
    return run(config, **kwargs)


def show_commands(config, data={}, **kwargs):
    """`handoff show commands -p <project_directory>`
    Show the shell commands that drives the task.
    """
    commands = _get_commands(config, data)
    for command in commands:
        print(command)
