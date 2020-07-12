# Outputs

## State file

For each run, `.artifacts/state` is generated. This is a copy of stderr output
from the last command in the pipeline:
```
{"start_date": "2020-07-12"}
```

A state file is a convenient way of passing information from one run to another
especially in serverless environment such as AWS Fargate. More about this later.

## Environment files

The last example also creates a file `.env/config/tap-config.json`:
```
.env
└── config
    └── tap-config.json
```

This is extracted from params.json then written out during the run.

The `.env` directory is reserved for a run time file generation. The files
can be fetched from a remote folder. This will be explained later.

Next: [Remote config & files](remote_config)
