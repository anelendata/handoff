# Virtual envs and configs

## Running a Python Program in a Virtual Environment

You can specify a virtual environments in case the command is a Python program.
In `project.yml`, you can also define virtual environment for Python program:
```
commands:
  - command: cat
    args: "./requirements.txt"
  - command: "./scripts/python/collector_stats.py"
    venv: "./venv/root"
```

Try runing:
```
./bin/mkparams > ./params.json
./bin/runlocal ./params.json
```

This time, you will get `.artifacts/collector_stats.json` that looks like:

```
{"rows_read": 15}
```

## Running Code with Configuration Files

The configuration files that may contain sensitive information go to
`.local` directory.

Such configuration files include singer.io tap and target's JSON config files,
and Google Cloud Platform key JSON file.

Note: Currently, only JSON files are supported for remote config store.

Example:

1. Install singer.io tap & target in separate virtual environments:
```
source ./venv/proc_01/bin/activate && pip install tap-exchangeratesapi && deactivate
source ./venv/proc_02/bin/activate && pip install target-csv && deactivate
```

2. Create a copy of config file for tap-exchangeratesapi:
```
echo '{ "base": "JPY", "start_date": "'`date --iso-8601`'" }' > .local/tap-config.json
```

Note: The config file of this example does not contain a sensitive information.


3. Update the project file.

.local/project.yml:
```
commands:
  - command: "tap-exchangeratesapi"
    args: "--config ./.env/config/tap-config.json"
    venv: "./venv/proc_01"
  - command: "./impl/collector_stats.py"
    venv: "./venv/root"
  - command: "target-csv"
    venv: "./venv/proc_02"
```

4. Generate parameter file and run:
```
./bin/mkparams > ./params.json
```

You will see the content of `tap-config.json` included in `params.json`:
```
cat params.json
```

Now let's run:
```
./bin/runlocal ./params.json
```

This should produce a file `exchange_rate-{timestamp}.csv` in the current directory.
It also leaves `.artifacts/state` and `.artifacts/collector_stats.json`.

Next: [Outputs](outputs)
