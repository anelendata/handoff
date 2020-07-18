# Execute in a Docker container

The repository refers to [fgops](https://github.com/anelendata/fgops) as a submodule
at `deploy/fargate`.
fgops are a set of Docker and CloudFormation commands to build and push the docker images to
ECR, create the ECS task definition, and schedule the events to be executed via Fargate.

fgops requires an environment file. See
[fg_env_example](https://github.com/anelendata/fgops/blob/master/fg_env_example)
as an example. This file will be referred as <fg_env_file> from here.

fgops are symlinked from `./bin` for convenience.

## Build the image

Dockerfile will try to install the project from `./project` directory. So copy
what you want to build:
```
cp -r test_projects/03_exchange_rates project
```

```
./bin/docker_task build <fg_env_file> 0.1
```

Note: "0.1" here is the image version name. You decide what to put there.

## Run

```
docker run --env-file <env_var_file> <IMAGE_NAME>
```

Like the way you defined when running locally, you need to define:
```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
STACK_NAME
S3_BUCKET
```

in <env_var_file> file to pass on to Docker contianer.

By default, Dockerfile is configured to execute
`handoff run -p ./project -w ./workspace` assuming that the remote
configurations are set.

Or you can specify the function to run together with the data via additional
environment variables in <env_var_file>:

```
COMMAND=show_commands
DATA={"start_at":"1990-01-01T00:00:00","end_at":"2030-01-01T00:00:00"}
```

...that would be picked up by Docker just as

```
CMD handoff ${COMMAND:-run} -w workspace -d ${DATA:-{}} -a
```

See [Dockerfile](https://github.com/anelendata/handoff/blob/master/Dockerfile) for details.

Next: [Fargate Deployment](fargate.md)
