#!/usr/bin/python
import io, json, logging, subprocess, sys, os, re
import attr
from typing import Dict
from jinja2 import Template as _Template

LOGGER = logging.getLogger(__name__)


def _get_python_info(module=__file__):
    python_exec = sys.executable
    lib_dir = os.path.dirname(os.path.realpath(attr.__file__))
    work_dir = os.getcwd()
    code_dir = os.path.dirname(os.path.realpath(module))
    python_info = {"python": python_exec,
                   "python_lib_dir": lib_dir,
                   "work_dir": work_dir,
                   "code_dir": code_dir
                   }

    return python_info


def _get_params(args=None):
    """
    Pack up the python path, work directory, and current directory into a dict
    """
    params = _get_python_info(__name__)
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


def _foreach_process(foreach_obj, params, env=None, stdin=None):
    foreach_obj_str = re.escape(json.dumps(foreach_obj).replace("\n", ""))
    params_str = re.escape(json.dumps(dict(params)))

    file_dir, _ = os.path.split(__file__)
    foreach_script = os.path.join(file_dir, "operators.py")

    args = " ".join([foreach_script, "_foreach", foreach_obj_str, params_str])
    command_str = _get_command_string("python3", "", params)
    command_str = command_str + " " + args
    return subprocess.Popen([command_str], stdin=stdin, stdout=subprocess.PIPE,
                            env=env, shell=True)


def _run_pipeline(pipe:str, state:Dict, artifacts_dir="artifacts") -> None:
    """`handoff run -w <workspace_directory> -e resource_group=<resource_group_name> task=<task_name>`
    Run the task by the configurations and files stored in the remote parameter store and the file store.
    """
    pipe_name = pipe["name"]
    LOGGER.info("Running pipeline: " + pipe_name)

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
    commands = pipe["commands"]
    last_proc = None
    for command_obj in commands:
        if not command_obj.get("active", True):
            continue

        stdin = None
        if last_proc:
            stdin = last_proc.stdout
        params = _get_params(state)
        params["venv"] = command_obj.get("venv", None)

        if command_obj["command"] == "_foreach":
            command_obj["proc"] = _foreach_process(command_obj, params, env,
                                                   stdin)
            last_proc = command_obj["proc"]
            continue

        command_str = _get_command_string(command_obj["command"],
                                          command_obj["args"],
                                          params)
        command_obj["proc"] = subprocess.Popen(
            [command_str], stdin=stdin, stdout=subprocess.PIPE, env=env,
            shell=True)
        last_proc = command_obj["proc"]

    kill = False
    for command_obj in commands:
        proc = command_obj.get("proc")
        if not proc:
            LOGGER.debug("No process found for %s" % command_obj)
            continue
        if kill:
            proc.terminate()
            continue

        if proc is not None and proc == last_proc:
            LOGGER.debug("Last process pid %s" % proc.pid)
            break

        LOGGER.info("Checking return code of pid %d" % proc.pid)
        return_code = proc.wait()
        if return_code > 0:
            LOGGER.error("Process %d (%s) exited with code %d" %
                         (proc.pid, command_obj["command"], return_code))
            kill = True

    # This assumes the data is not big. Use stdout, stderr in the last process
    # only for logging purposes, not passing big data.
    # https://docs.python.org/3/library/subprocess.html#subprocess.Popen.communicate
    stdout, stderr = last_proc.communicate()

    if stdout:
        stdout = stdout.decode("utf-8").strip("\n").strip(" ")
    if stderr:
        stderr = stderr.decode("utf-8").strip("\n").strip(" ")

    if stdout:
        with open(os.path.join(artifacts_dir, pipe_name + "_stdout.log"), "w") as f:
            f.write(stdout)
    if stderr:
        with open(os.path.join(artifacts_dir, pipe_name + "_stderr.log"), "w") as f:
            f.write(stderr)

    return stdout, stderr


def foreach(foreach_obj, params):
    lines = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
    for line in lines:
        params["_stdin"] = line

        for pipe in foreach_obj["pipelines"]:
            if not pipe.get("active", True):
                continue
            _run_pipeline(pipe, params)


if __name__ == "__main__":
    command = sys.argv[1]
    foreach_obj = json.loads(sys.argv[2])
    params = json.loads(sys.argv[3])
    if command == "_foreach":
        foreach(foreach_obj, params)
    else:
        raise NotImplementedError(command)
