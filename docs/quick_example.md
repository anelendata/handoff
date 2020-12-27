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

## A Super Quick Example

Run this command to create a few example project under the current directory:

```
handoff quick_start make
```

You will find `project.yml` file in `projects/01_word_count` directory.

The project file defines the commands to be executed as a pipeline:

```
> cat projects/project.yml


tasks:
- name: word_count
  description: This task will be executed as 'cat <file_path> | wc -w'
  pipeline:
  - command: cat
    args: ./files/the_great_dictator_speech.txt
  - command: wc
    args: -w
```

This project file defines a shell-script equivalent of
`cat  ./files/the_great_dictator_speech.txt | wc -w`.

Try runing:
```
handoff -p projects/01_word_count -w workspace run local
```

You get console outputs like this:
```
INFO - 2020-07-16 22:04:34,004 - handoff: Running run_local in workspace directory
INFO - 2020-07-16 22:04:34,004 - handoff: Job started at 2020-07-16 22:04:34.004465
INFO - 2020-07-16 22:04:34,010 - handoff: Job ended at 2020-07-16 22:04:34.010021
INFO - 2020-07-16 22:04:34,010 - handoff: Processed in 0:00:00.005556
```

It will create `workspace/artifacts/state` whose content looks like:
```
644
```
...which is the equivalent of running:
```
cat  ./files/the_great_dictator_speech.txt | wc -w
```
It counted the word in the file.

## A Guided Tour

The project files you just created with `handoff quick_start make` has an
interactive command-line tutorial. Each section is very short (5~10 minutes
to complete.) To start the interactive tutorial, enter:

```
cd projects
./start
```

Otherwise, you can browse the same content from the next page:

Next: [A Guided Tour](./guided_tour)
