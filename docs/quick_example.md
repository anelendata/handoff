# Quick Start

## Install

Prerequisites:

- Python 3.6 or later

Clone [repo](https://github.com/anelendata/handoff) & initialize the submodules:
```
git clone https://github.com/anelendata/handoff.git
git submodule init
git submodule update
```

Create Python virtual environment and install the modules.
From the root directory of this repository, do:

```
./bin/mkvenvs
```

## A Super Quick Example

There is a `project.yml` file in `.local` directory at the root of this
repository. The project file defines the commands to be executed as a pipeline,
for example:
```
commands:
  - command: cat
    args: "./requirements.txt"
  - command: wc
    args: "-l"
```

This project file defines a shell-script equivalent of
`cat ./requirements.txt | wc -l`.

Try runing:
```
mkdir -p .env
./bin/mkparams > .env/params.json
./bin/runlocal .env/params.json
```

You get console outputs like this:
```
INFO - 2020-07-10 17:49:48,712 - impl.runner: Running run data:{}
INFO - 2020-07-10 17:49:48,712 - impl.runner: Running run
INFO - 2020-07-10 17:49:48,713 - impl.runner: Reading parameters from file: ./params.json
INFO - 2020-07-10 17:49:48,713 - impl.runner: Job started at 2020-07-10 17:49:48.713528
INFO - 2020-07-10 17:49:48,718 - impl.runner: Job ended at 2020-07-10 17:49:48.718836
INFO - 2020-07-10 17:49:48,719 - impl.runner: Processed in 0:00:00.005308
```

It creates `.artifacts/state` whose content is the equivalent to:

```
cat ./requirements.txt | wc -l
```

Next: [Using virtual environments](venv_config)

