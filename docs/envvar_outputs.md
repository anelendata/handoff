# Environment varaible

If you want to pass environment variables to the subprocesses, you can do so
by defining them in `project.yml`. Here is a singer.io example to fetch
the exchange rates then write out to BigQuery. Access to BigQuery requires
a credential file, and the environment variable `GOOGLE_APPLICATION_CREDENTIALS`
must indicate the path to the file:

```
commands:
  - command: "tap-exchangeratesapi"
    args: "--config config/tap-config.json"
    venv: "proc_01"
    installs:
      - "pip install tap-exchangeratesapi"
  - command: "python files/stats_collector.py"
    venv: "proc_01"
  - command: "target-bigquery"
    args: "--config config/target-config.json"
    venv: "proc_02"
  installs:
    - "pip install target-bigquery"
envs:
  - key: "GOOGLE_APPLICATION_CREDENTIALS"                                       
    value: "config/google_client_secret.json"
```

The above example should be accompanied by the following files stored in
`<project_dir>/config` directory:

- tap-config.json
- target-config.json
- google_client_secret.json

# Outputs

## State file

For each run, `<workspace_dir>/artifacts/state` is generated. This is a copy of
stderr output from the last command in the pipeline:
```
{"start_date": "2020-07-12"}
```

A state file is a convenient way of passing information from one run to another
especially in serverless environment such as AWS Fargate. More about this later.

## Environment files

The current exchange rate example in [the last section](./venv_config)
also creates a file `<workspace_dir>/config/tap-config.json`:
```
workspace
└── config
    └── tap-config.json
```

This is extracted from the project config then written out during the run.

The files can be fetched from a remote folder. This will be explained later.

Next: [fgops & IAM role creation](role)
