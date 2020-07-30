# Remote configurations and files

We continue to use
[the currency exchange rate example](venv_config) from the previous
sections, so if you have not done so, please do it before trying the following
example.

We also assume the following environment variables are exported by assuming
the IAM role from [the previous section](role).

## Pushing config to SSM Parameter Store

First push the project configurations at AWS SSM Parameter Store:

```
handoff config push -p test_projects/03_exchange_rates
```

You can check the currently stored values by print command:

```
handoff config print -p test_projects/03_exchange_rates
```

It should return a string like this:
```
{"commands": [{"command": "tap-exchangeratesapi", "args": "--config config/tap-config.json", "venv": "proc_01", "installs": ["pip install tap-exchangeratesapi"]}, {"command": "files/stats_collector.py", "venv": "proc_01"}, {"command": "target-csv", "venv": "proc_02", "installs": ["pip install target-csv"]}], "files": [{"name": "tap-config.json", "value": "{ \"base\": \"JPY\", \"start_date\": \"2020-07-09\" }\n"}]}
```

The string is "compiled" from profile.yml and the JSON configuration files under
`<profile_dir>/config` directory.

Note: The maximum size of a value in Parameter Store is 4KB with Standard
tier. You can bump it up to 8KB with Advanced tier with `--allow-advanced-tier` option:

```
handoff config print -p test_projects/03_exchange_rates --allow-advanced-tier
```

## Pushing files to S3

In the project directory may contain `files` subdirectory and store the
files needed at run-time. The files should be first pushed to the remote
store (AWS S3) by running:

```
handoff files push -p test_projects/03_exchange_rates
```

You see handoff fetching the files into `workspace/files` by runnig:
```
handoff files get -p test_projects/03_exchange_rates
```

You do not need to run the above command explicitly as handoff automatically
downlods them into the workspace as described in the next section.

## Run

Let's clean up the local workspace before running with the remotely stored
configs:
```
rm -fr test_workspaces/03_exchange_rates/*
```

First we need to create the virtual environments and install the commands:
```
handoff workspace install -w test_workspaces/03_exchange_rates
```

Then run:
```
handoff run -w test_workspaces/03_exchange_rates -a
```

Notice that we dropped `-p` option in the last two commands. The project
configurations are fetched from remote this time.

After the run, you find the output from the exchange rate tap example from
the previous example.

In the above run command, we added `-a` option. This is short for `--push-artifacts`.
With this option, the files under `<workspace_dir>/artifacts` will be push to
the remote storage after the run. You can download the artifacts from the
remote storage by runing:
```
handoff artifacts get -w <workspace_dir>
```

You can also push the contents of `<workspace_dir>/artifacts` manually:
```
handoff artifacts push -w <workspace_dir>
```

In the remote storage, the copy of artifacts from the last run is found at
`<bucket_name>/<stack_name>/last`. The historical files are archived in
`<bucket_name>/<stack_name>/runs`.

### Other useful commands

`default` is a function defined in `impl.py`. Any function defined in `impl.py` can be invoked

in the same manner.

```
source ./venv/root/bin/activate && python code show_commands && deactivate
```

This shows the commands in the pipeline.

Next: [Building and running Docker image](docker)
