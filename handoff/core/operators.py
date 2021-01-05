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


def _foreach(foreach_obj, params, stdin,
             kill_downstream_on_fail=True):
    if isinstance(stdin, int) and stdin == subprocess.PIPE:
        raise Exception("You cannot nest control flow operators. Dump in a file.")

    for line in stdin:
        line = line.decode("utf-8").strip()
        params["_line"] = line
        safe_name = re.sub(r"[^a-zA-Z0-9-_.]+", "_", line)
        params["_line_safe"] = safe_name

        for task in foreach_obj:
            if not task.get("active", True):
                continue
            kill_downstream_on_fail = not task.get(
                "run_downstream_on_fail", False)
            cur_task = {}
            cur_task.update(task)
            cur_task["name"] = cur_task["name"] + "_" + safe_name
            _ = _run_task(cur_task, params,
                          kill_downstream_on_fail=kill_downstream_on_fail)


def _fork(fork_obj, state, stdin=None, artifacts_dir="artifacts",
          kill_downstream_on_fail=True):
    tasks = []
    for task in fork_obj:
        if not task.get("pipeline"):
            raise Exception("fork's children must be pipelines")
        if not task.get("active", True):
            LOGGER.debug(f'Skipping {task["name"]}')
            continue
        tasks.append(_run_pipeline(task, state, artifacts_dir,
                                   kill_downstream_on_fail,
                                   stdin=subprocess.PIPE))
    first_procs = []
    for task in tasks:
        pipeline = task["pipeline"]
        for cmd_obj in pipeline:
            proc = cmd_obj.get("proc")
            if not proc:
                continue
            first_procs.append(proc)
            break

    for line in stdin:
        # feed the new line to the first process in procs
        for proc in first_procs:
            proc.stdin.write(line)

    for proc in first_procs:
        proc.stdin.close()

    for task in tasks:
        _wait_for_pipeline(task, state, artifacts_dir=artifacts_dir,
                           kill_downstream_on_fail=kill_downstream_on_fail)
    return None


def _run_commands(task: Dict, state: Dict,
                  artifacts_dir: str = "artifacts",
                  kill_downstream_on_fail=True) -> None:
    commands = task["commands"]
    name = task.get("name", "")
    LOGGER.info("Running commands " + name)
    if state.get("_line"):
        name = name + "_" + state.get("_line")
    env = _get_env()
    stdout = ""
    stderr = ""
    killed = False

    if task.get("stdout", True):
        stdout_fn = os.path.join(artifacts_dir, name + "_stdout.log")
    else:
        stdout_fn = os.devnull
    if task.get("stderr", True):
        stderr_fn = os.path.join(artifacts_dir, name + "_stderr.log")
    else:
        stderr_fn = os.devnull

    with open(stdout_fn, "w") as stdout, open(stderr_fn, "w") as stderr:
        for command_obj in commands:
            if not command_obj.get("active", True):
                continue
            params = _get_params(state)
            params["venv"] = command_obj.get("venv", None)
            command_str = _get_command_string(command_obj["command"],
                                              command_obj.get("args", ""),
                                              params)
            proc = subprocess.Popen([command_str], stdout=stdout, stderr=stderr,
                                    env=env, shell=True)
            LOGGER.debug("Checking return code of pid %d" % proc.pid)
            exit_code = proc.wait()
            LOGGER.debug("Process %d (%s) exited with code %d" %
                         (proc.pid, command_obj["command"], exit_code))

            if exit_code > 0:
                LOGGER.warning("Process %d (%s) exited with code %d" %
                               (proc.pid, command_obj["command"], exit_code))
                killed = True
                break

    if killed and kill_downstream_on_fail:
        raise Exception(
            f"Task {name} ended with exit code {exit_code}.")

    return exit_code


def _run_pipeline(task: Dict, state: Dict,
                  artifacts_dir: str = "artifacts",
                  kill_downstream_on_fail=True,
                  stdin=None) -> None:
    pipeline = task["pipeline"]
    name = task.get("name", "")
    LOGGER.info("Running pipeline " + name)
    last_proc = None
    env = _get_env()
    for command_obj in pipeline:
        if not command_obj.get("active", True):
            continue

        if last_proc:
            stdin = last_proc.stdout
        params = _get_params(state)
        params["venv"] = command_obj.get("venv", None)

        if command_obj.get("foreach"):
            if stdin is None:
                raise Exception("foreach requires stdin")
            LOGGER.info("Running foreach loop")
            command_obj["proc"] = _foreach(command_obj["foreach"], params, stdin,
                                           kill_downstream_on_fail)
            break

        if command_obj.get("fork"):
            if stdin is None:
                raise Exception("fork requires stdin")
            LOGGER.info("Forking the downstream...")
            # TODO: It hangs if the parent process errors...
            command_obj["proc"] = _fork(command_obj["fork"], params, stdin,
                                        artifacts_dir,
                                        kill_downstream_on_fail)
            break

        command_str = _get_command_string(command_obj["command"],
                                          command_obj.get("args", ""),
                                          params)

        command_obj["proc"] = subprocess.Popen(
            [command_str], stdin=stdin, stdout=subprocess.PIPE, env=env,
            shell=True)
        last_proc = command_obj["proc"]

    if task.get("stdout", True):
        stdin = last_proc.stdout
        stdout_fn = os.path.join(artifacts_dir, name + "_stdout.log")
        with open(stdout_fn, "w") as stdout:
            subprocess.Popen(["cat"], stdin=stdin, stdout=stdout, shell=True)

    return task


def _wait_for_pipeline(task: Dict, state: Dict,
                       artifacts_dir: str = "artifacts",
                       kill_downstream_on_fail: str = True):
    killed = False
    exit_code = 0
    last_proc = None
    name = task.get("name", "")
    if state.get("_line"):
        name = name + "_" + state.get("_line")
    pipeline = task["pipeline"]
    for command_obj in pipeline:
        proc = command_obj.get("proc")
        if not proc:
            LOGGER.debug("No process found for %s" % command_obj)
            continue
        if killed:  # Upstream in the pipeline exited with non-zero status
            LOGGER.warning("Terminating Process (%d) (%s)" %
                           (proc.pid, command_obj["command"]))
            proc.terminate()
            continue

        LOGGER.info("Checking return code of pid %d" % proc.pid)
        exit_code = proc.wait()
        last_proc = proc
        LOGGER.debug("Process %d (%s) exited with code %d" %
                     (proc.pid, str(command_obj.get("command")), exit_code))
        if exit_code > 0:
            LOGGER.warning("Process %d (%s) exited with code %d" %
                           (proc.pid, command_obj["command"], exit_code))
            killed = True

    if last_proc and last_proc.stdin and last_proc.stdin.closed:
        return exit_code

    if last_proc:
        last_proc.wait()

    if killed and kill_downstream_on_fail:
        raise Exception(
            f"Task {name} ended with exit code {exit_code}.")

    return exit_code


def _run_task(task: Dict, state: Dict, artifacts_dir="artifacts",
              kill_downstream_on_fail=True, stdin=None) -> None:
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
        exit_code = 0

        for subtask in task["tasks"]:
            kill_downstream_on_fail = not subtask.get(
                "run_downstream_on_fail", False)
            exit_code = _run_task(
                subtask, state, artifacts_dir=artifacts_dir,
                kill_downstream_on_fail=kill_downstream_on_fail, stdin=stdin)
        return exit_code

    if state.get("_line"):
        task_name = task_name + "_" + str(state.get("_line"))

    if task.get("pipeline"):
        task_w_process = _run_pipeline(task, state, artifacts_dir,
                                       kill_downstream_on_fail,
                                       stdin=stdin)
        exit_code = _wait_for_pipeline(task_w_process, state, artifacts_dir,
                                       kill_downstream_on_fail)
    elif task.get("commands"):
        exit_code = _run_commands(task, state, artifacts_dir,
                                  kill_downstream_on_fail)
    else:
        raise Exception(
            "Neither pipline or commands record was found in this task")

    return exit_code
