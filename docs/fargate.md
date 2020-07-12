# Fargate Deployment

## Creating VPN and S3 bucket

If you have not done so, created a shared VPN and S3 bucket.
This command creates VPN (named from `PARENT_STACK_NAME`) and S3 bucket
(named from `S3_BUCKET`) shared across multiple stacks:

```
./bin/cf_create_vpn <fg_env_file>
```

## Pushing the image and create the ECS task

Note: Please see fgops instructions for the details.

Push the image to the ECR:

```
./bin/docker_task <fg_env_file> push 0.1 
```

Create the cluster and the task via Cloudformation:

```
./bin/cf_create_stack <fg_env_file> 0.1
```

Check the creation on [Cloudformation](https://console.aws.amazon.com/cloudformation/home)

## Additional permissions

Farget TaskRole will be created under the name: <STACK_NAME>-TaskRole-XXXXXXXXXXXXX
Additional AWS Policy may be attached to the TaskRole depends on the ECS Task.

## Run a one-off task

```
./bin/ecs_run_task <fg_env_file> [<remote_env_var_file>]
```

You can pass extra environmental variables via <remote_env_var_file>.
You need to and SHOULD NOT include AWS keys and secrets in <remote_env_var_file>.

## Scheduling via Fargate

```
./bin/events_schedule_create <fg_env_file> <target_id> '0 0 * * ? *'
```

The above cron example runs the task at midnight daily.

Check the execution at AWS Console:

https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters

...and Cloudwatch logs:

https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logs:

## How to update the stack

1. Make code change and test locally.
2. Build docker image with ./bin/docker_task build
3. Test docker execution locally.
4. Push docker image with ./bin/docker_task push
5. Update stack:

```
./bin/cf_update_stack <fg_env_file> 0.1
```

6. Unschedule the Fargate task:

```
./bin/events_schedule_remove <fg_env_file> <target_id>
```

7. Reschedule the task:

```
./bin/events_schedule_create <fg_env_file> <target_id> '0 0 * * ? *'
```
