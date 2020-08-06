..  _essential_commands:

Essential Commands at a Glance
==============================

Use this page as a cheat-sheet after finishing the guided-tour (tutorial).

Next: :doc:`guided_tour`

Here is the essential commands in order of the workflow from the local testing
to Fargate deployment:

.. code-block:: shell

    handoff -p <project_dir> -w <workspace_dir> workspace install
    handoff -p <project_dir> -w <workspace_dir> run local
    handoff -p <project_dir> config push
    handoff -p <project_dir> cloud create_bucket
    handoff -p <project_dir> files push
    handoff -p <project_dir> -w <workspace_dir> run remote_config
    handoff -p <project_dir> container build
    handoff -p <project_dir> container run
    handoff -p <project_dir> container push
    handoff -p <project_dir> cloud create_resources
    handoff -p <project_dir> cloud create_task
    handoff -p <project_dir> cloud schedule

Here are the commands to take down:

.. code-block:: shell

    handoff -p <project_dir> cloud unschedule
    handoff -p <project_dir> cloud delete_task
    handoff -p <project_dir> cloud delete_resources
    handoff -p <project_dir> files delete
    handoff -p <project_dir> config delete
    handoff -p <project_dir> cloud delete_bucket

And here are the commands to remove the additional resources:

.. code-block:: shell

    aws s3 rm --recursive s3://<aws-account-id>-<resource-name>/<task-name>/
    aws s3 rb s3://<bucket_name>/<task-name>/
    aws ecr delete-repository --repository-name <docker-image-name>

Here are the commands to create and delete a role (e.g. AWS Role):

.. code-block:: shell

    handoff -p <project_dir> cloud create_role
    handoff -p <project_dir> cloud delete_role

handoff shows help document at the root level or subcommand-level:

.. code-block:: shell

    handoff --help
    handoff <command> --help  # Admin or Run command such as 'run local'
    handoff cloud [<command>] --help
    handoff container [<command>] --help
    handoff <plugin_name> [<command>] --help
