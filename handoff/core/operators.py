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


def _foreach_process(foreach_obj, params, env=None, stdin=None,
                     kill_downstream_on_fail=True):
    foreach_obj_str = re.escape(json.dumps(foreach_obj).replace("\n", ""))
    params_str = re.escape(json.dumps(dict(params)))

    file_dir, _ = os.path.split(__file__)
    foreach_script = os.path.join(file_dir, "operators.py")

    args = " ".join([foreach_script, "_foreach", foreach_obj_str, params_str,
                     str(kill_downstream_on_fail)])
    command_str = _get_command_string("python3", "", params)
    command_str = command_str + " " + args
    return subprocess.Popen([command_str], stdin=stdin, stdout=subprocess.PIPE,
                            env=env, shell=True)


def _run_pipeline(pipe:Dict, state:Dict, artifacts_dir="artifacts",
                  kill_downstream_on_fail=True) -> None:
    """`handoff run -w <workspace_directory> -e resource_group=<resource_group_name> task=<task_name>`
    Run the task by the configurations and files stored in the remote parameter store and the file store.
    """
    pipe_name = pipe["name"]

    if pipe.get("group"):
        if not pipe.get("active", True):
            return None, None, 0

        LOGGER.info("Running group: " + pipe_name)
        stdout = None
        stderr = None
        exit_code = 0

        for child_pipe in pipe["group"]:
            stdout, stderr, exit_code = _run_pipeline(
                child_pipe, state, artifacts_dir=artifacts_dir,
                kill_downstream_on_fail=kill_downstream_on_fail)
        return stdout, stderr, exit_code

    if state.get("_stdin"):
        pipe_name = pipe_name + "_" + state.get("_stdin")
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
    commands = pipe["pipeline"]
    last_proc = None
    for command_obj in commands:
        if not command_obj.get("active", True):
            continue

        stdin = None
        if last_proc:
            stdin = last_proc.stdout
        params = _get_params(state)
        params["venv"] = command_obj.get("venv", None)

        if command_obj.get("foreach"):
            if stdin is None:
                raise Exception("foreach requires stdin")
            command_obj["proc"] = _foreach_process(
                command_obj["foreach"], params, env, stdin,
                kill_downstream_on_fail)
            last_proc = command_obj["proc"]
            continue

        command_str = _get_command_string(command_obj["command"],
                                          command_obj["args"],
                                          params)

        command_obj["proc"] = subprocess.Popen(
            [command_str], stdin=stdin, stdout=subprocess.PIPE, env=env,
            shell=True)
        last_proc = command_obj["proc"]

    killed = False
    exit_code = 0
    for command_obj in commands:
        proc = command_obj.get("proc")
        if not proc:
            LOGGER.debug("No process found for %s" % command_obj)
            continue
        if killed:
            proc.terminate()
            continue

        if proc is not None and proc == last_proc:
            LOGGER.debug("Last process pid %s" % proc.pid)
            break

        LOGGER.info("Checking return code of pid %d" % proc.pid)
        exit_code = proc.wait()
        LOGGER.debug("Process %d (%s) exited with code %d" %
                     (proc.pid, command_obj["command"], exit_code))
        if exit_code > 0:
            LOGGER.error("Process %d (%s) exited with code %d" %
                         (proc.pid, command_obj["command"], exit_code))
            killed = True

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

    if killed and kill_downstream_on_fail:
        raise Exception(
            f"Pipeline {pipe_name} ended with exit code {exit_code}.")
    return stdout, stderr, exit_code


def foreach(foreach_obj, params, kill_downstream_on_fail):
    lines = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
    for line in lines:
        line = line.strip()
        params["_stdin"] = line

        for pipe in foreach_obj:
            if not pipe.get("active", True):
                continue
            stdout, stderr, return_code = _run_pipeline(
                pipe, params, kill_downstream_on_fail=kill_downstream_on_fail)


if __name__ == "__main__":
    command = sys.argv[1]
    if command == "_foreach":
        foreach_obj = json.loads(sys.argv[2])
        params = json.loads(sys.argv[3])
        kill_downstream_on_fail = (sys.argv[4].strip().lower() == "true")
        foreach(foreach_obj, params, kill_downstream_on_fail)
    else:
        raise NotImplementedError(command)
