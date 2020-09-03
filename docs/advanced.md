# Advanced Topics

## Customizing Dockerfile

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
