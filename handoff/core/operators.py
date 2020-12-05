#!/usr/bin/python
import io, json, logging, subprocess, sys, os, re
import attr
from typing import Dict
from jinja2 import Template as _Template

LOGGER = logging.getLogger(__name__)

"""
In Docker container, it takes shell=True to run a subprocess without causing Permission error (13)
and to run with shell=True, we need to feed the entire cmd string with args without splitting.
(subprocess.Popen(shlex.split(command_str),...)
In the olden days, it was never recommended for a container to run multiple processes.
Now the guideline is "Each container should have only one concern." and
"Limiting each container to one process is a good rule of thumb, but it is not a hard and fast rule."
https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#decouple-applications
Also see
https://docs.python.org/3/library/subprocess.html#security-considerations
"""

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


def _run_commands(task: Dict, state: Dict, artifacts_dir="artifacts",
                  kill_downstream_on_fail=True) -> None:
    commands = task["commands"]
    name = task["name"]
    env = _get_env()
    stdout = ""
    stderr = ""
    killed = False
    for command_obj in commands:
        if not command_obj.get("active", True):
            continue
        params = _get_params(state)
        params["venv"] = command_obj.get("venv", None)
        command_str = _get_command_string(command_obj["command"],
                                          command_obj["args"],
                                          params)
        proc = subprocess.Popen([command_str], env=env, shell=True)
        LOGGER.info("Checking return code of pid %d" % proc.pid)
        exit_code = proc.wait()
        LOGGER.debug("Process %d (%s) exited with code %d" %
                     (proc.pid, command_obj["command"], exit_code))

        # This assumes the data is not big. Use stdout, stderr in the last process
        # only for logging purposes, not passing big data.
        # https://docs.python.org/3/library/subprocess.html#subprocess.Popen.communicate
        cur_stdout, cur_stderr = proc.communicate()
        if cur_stdout:
            stdout += cur_stdout
        if cur_stderr:
            stderr += cur_stderr

        if exit_code > 0:
            LOGGER.warning("Process %d (%s) exited with code %d" %
                           (proc.pid, command_obj["command"], exit_code))
            killed = True
            break

    if stdout:
        stdout = stdout.decode("utf-8").strip("\n").strip(" ")
    if stderr:
        stderr = stderr.decode("utf-8").strip("\n").strip(" ")

    if stdout:
        with open(os.path.join(artifacts_dir, name + "_stdout.log"), "w") as f:
            f.write(stdout)
    if stderr:
        with open(os.path.join(artifacts_dir, name + "_stderr.log"), "w") as f:
            f.write(stderr)

    if killed and kill_downstream_on_fail:
        raise Exception(
            f"Task {name} ended with exit code {exit_code}.")

    return stdout, stderr, exit_code


def _run_pipeline(task: Dict, state: Dict, artifacts_dir="artifacts",
                  kill_downstream_on_fail=True) -> None:
    pipeline = task["pipeline"]
    name = task["name"]
    last_proc = None
    env = _get_env()
    for command_obj in pipeline:
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
            LOGGER.info("Running foreach loop")
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
    for command_obj in pipeline:
        proc = command_obj.get("proc")
        if not proc:
            LOGGER.debug("No process found for %s" % command_obj)
            continue
        if killed:
            proc.terminate()
            continue

        if proc is not None and proc == last_proc:
            LOGGER.debug("Last process pid %d" % proc.pid)
            break

        LOGGER.info("Checking return code of pid %d" % proc.pid)
        exit_code = proc.wait()
        LOGGER.debug("Process %d (%s) exited with code %d" %
                     (proc.pid, command_obj["command"], exit_code))
        if exit_code > 0:
            LOGGER.warning("Process %d (%s) exited with code %d" %
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
        with open(os.path.join(artifacts_dir, name + "_stdout.log"), "w") as f:
            f.write(stdout)
    if stderr:
        with open(os.path.join(artifacts_dir, name + "_stderr.log"), "w") as f:
            f.write(stderr)

    if killed and kill_downstream_on_fail:
        raise Exception(
            f"Task {name} ended with exit code {exit_code}.")

    return stdout, stderr, exit_code


def _run_task(task: Dict, state: Dict, artifacts_dir="artifacts",
              kill_downstream_on_fail=True) -> None:
    """`handoff run -w <workspace_directory> -e resource_group=<resource_group_name> task=<task_name>`
    Run the task by the configurations and files stored in the remote parameter store and the file store.
    """
    task_name = task.get("name", "")

    entries = 0
    if "tasks" in task.keys():
        entries = entries + 1
    if "pipeline" in task.keys():
        entries = entries + 1
    if "commands" in task.keys():
        entries = entries + 1
    if entries != 1:
        raise Exception(
            "A task record can only have 1 of tasks, pipeline, commands entry")

    # subtask recursion
    if task.get("tasks"):
        if not task.get("active", True):
            return None, None, 0
        stdout = None
        stderr = None
        exit_code = 0

        for subtask in task["tasks"]:
            kill_downstream_on_fail = not subtask.get(
                "run_downstream_on_fail", False)
            stdout, stderr, exit_code = _run_task(
                subtask, state, artifacts_dir=artifacts_dir,
                kill_downstream_on_fail=kill_downstream_on_fail)
        return stdout, stderr, exit_code

    if state.get("_line"):
        task_name = task_name + "_" + str(state.get("_line"))

    LOGGER.info("Running task " + task_name)
    if task.get("pipeline"):
        stdout, stderr, exit_code = _run_pipeline(task, state, artifacts_dir,
                                                  kill_downstream_on_fail)
    elif task.get("commands"):
        stdout, stderr, exit_code = _run_commands(task, state, artifacts_dir,
                                                  kill_downstream_on_fail)
    else:
        raise Exception(
            "Neither pipline or commands record was found in this task")

    return stdout, stderr, exit_code


def foreach(foreach_obj, params):
    lines = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
    for line in lines:
        line = line.strip()
        params["_line"] = line

        for task in foreach_obj:
            if not task.get("active", True):
                continue
            kill_downstream_on_fail = not task.get(
                "run_downstream_on_fail", False)
            stdout, stderr, exit_code = _run_task(
                task, params, kill_downstream_on_fail=kill_downstream_on_fail)


if __name__ == "__main__":
    command = sys.argv[1]
    if command == "_foreach":
        foreach_obj = json.loads(sys.argv[2])
        params = json.loads(sys.argv[3])
        kill_downstream_on_fail = (sys.argv[4].strip().lower() == "true")
        foreach(foreach_obj, params)
    else:
        raise NotImplementedError(command)
