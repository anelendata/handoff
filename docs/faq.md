# FAQs

## Q. How do I specify relative time in the command?

You can use [GNU date command](https://www.gnu.org/software/coreutils/manual/html_node/Examples-of-date.html).

Example:

```
commands:
  - command: echo
    args: "UTC tomorrow to seconds in ISO8086: $(date -Iseconds -u -d '1 day') "
```

Note that `handoff run local` may not be able to handle this correctly if
your local machine does not implement GNU date (e.g. OSX).
By default, `handoff container run` and `handoff cloud run` should be able
to handle correctly as the Docker image is based on Ubuntu.

You can also use Template variables:

```
commands:
  - command: echo
    args: "today / tomorrow: {{ today }} / {{ tomorrow }}"
```

Then, run handoff with date command passing via -d option:

```
handoff run local -p project_dir -d today=$(date -I) tomorrow=$(date -I -d "1 day")
```

You can delay the evaluation of date command in container run and cloud run
commands by passing DATA environment variable via `-e` option:

```
handoff container run -p project_dir -e DATA='today=$(date -I) tomorrow=$(date -I -d "1 day")'
handoff cloud run -p project_dir -e DATA='today=$(date -I) tomorrow=$(date -I -d "1 day")'
```

Make sure to **use single quotes** when defining DATA variable so it won't be
evaluated when container/cloud run command runs. You want the command string to be passed
'as is' and then evaluated when the **container** executes the `handoff run` command.

DATA is a sepecial environment variable inside the container as defined in
Dockerfile, the container evaluates DATA and pass to handoff via -d option:

```
handoff run -w workspace_dir -d $(eval echo $DATA)
```

In this way, the date command defined in DATA is finally evaluated inside
the container.

## Q. How do I configure project.yml so it installs a Python command from a Github repository?

You can put `https://github.com/<account>/<repository>/archive/<commit-hash>.tar.gz#egg=<command-name>`
format like this project of executing a pair of singer.io processes,
[tap-rest-api](https://github.com/anelendata/tap-rest-api) and
[target_gcs](https://github.com/anelendata/target_gcs):
```
commands:
  - command: tap-rest-api
    args: "file/rest_api_spec.json --config files/tap_config.json --schema_dir file/schema --catalog file/catalog/default.json --state artifacts/state --start_datetime '{start_at}' --end_datetime '{end_at}'"
    venv: proc_01
    installs:
      - "pip install tap-rest-api"
  - command: target_gcs
    args: "--config files/target_config.json"
    venv: proc_02
    installs:
      - "pip install install --no-cache-dir https://github.com/anelendata/target_gcs/archive/17e70bced723fe202425a61199e6e1180b6fada7.tar.gz#egg=target_gcs"
envs:
  - key: "GOOGLE_APPLICATION_CREDENTIALS"
    value: "files/google_client_secret.json"
```

## Q. Can we use a customer Dockerfile?

Yes, you can.

One may need to deploy a Docker image with special root installations
(e.g. JDBC driver). This is beyond the capability of workspace install command.

```
container:
  docker_file: ./my_Dockerfile
  files_dir: ./my_files
```

In the above example, handoff will use `./my_Dockerfile` instead of the
default Dockerfile. It also copies `./my_files` directory to the temporary
directory where handoff start a docker command.

To get started, it is recommended to copy the
[default Dockerfile](https://github.com/anelendata/handoff/blob/master/handoff/services/container/docker/Dockerfile)
and modify it.

Then in your version of Dockerfile, you should be able to add install extra
software or copy the files like:

```
RUN apt-get update -yqq && apt-get install -yqq jq
COPY ./my_files/hello.txt /app/
```
