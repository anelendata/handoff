# Quick Start

## Install

Prerequisites:

- Python 3.6 or later

You can check your Python version by running:
```
python --version
```

Note: You may have `python` command linked to Python 2.x and `python3` to 3.x.
If that is the case use `python3` command when you create the virtual
environment (venv) in the installtion commands below.

Install:
```
python -m venv ./venv
source venv/bin/activate
pip install handoff
```

The rest of the instruction uses the test project definitions in the repository.
Clone [repo](https://github.com/anelendata/handoff) & initialize the submodules:
```
git clone https://github.com/anelendata/handoff.git
git submodule init
git submodule update
```

Note: Instead of installing from Python Package Index with `pip` command, you can
also install handoff from the repository. This is good for the people who
wants to try the unreleased version or wants to improve the project:
```
python3 -m venv ./venv
source venv/bin/activate
python setup.py install
```

## A Super Quick Example

There is a `project.yml` file in `test_projects/01_word_count` directory at
the root of the repository ([here](https://github.com/anelendata/handoff/blob/master/test_projects/01_word_count/project.yml)).
The project file defines the commands to be executed as a pipeline, for example:
```
commands:
  - command: cat
    args: "../../README.md"
  - command: wc
    args: "-l"
```

This project file defines a shell-script equivalent of
`cat ../../README.md | wc -l`.

Try runing:
```
handoff run_local -p test_projects/01_word_count -w test_workspaces/01_word_count
```

You get console outputs like this:
```
INFO - 2020-07-16 22:04:34,004 - handoff: Running run_local in workspace directory
INFO - 2020-07-16 22:04:34,004 - handoff: Job started at 2020-07-16 22:04:34.004465
INFO - 2020-07-16 22:04:34,010 - handoff: Job ended at 2020-07-16 22:04:34.010021
INFO - 2020-07-16 22:04:34,010 - handoff: Processed in 0:00:00.005556
```

It creates `test_workspaces/01_word_count/artifacts/state` whose content:
```
42
```
is the equivalent of running:
```
cat ./README.md | wc -l
```
from the repository's root directory.

Next: [Try fetching currency exchange rates](venv_config)
