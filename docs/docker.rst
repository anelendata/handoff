Building and running Docker
===========================

Dockerfile will try to install the project from `./project` directory. So copy
what you want to build from handoff repository root:

.. code-block:: shell

    cp -r ./test_projects/03_exchange_rates ./project

Then use fgops commands to build and test-running the image.

.. mdinclude:: ../deploy/fargate/docker.md

Run behavior
~~~~~~~~~~~~

By default, Dockerfile is configured to execute
`handoff run -p ./project -w ./workspace` assuming that the remote
configurations are set.

Or you can specify the function to run together with the data via additional
environment variables in <env_var_file>:

.. code-block:: shell

    COMMAND=show_commands
    DATA={"start_at":"1990-01-01T00:00:00","end_at":"2030-01-01T00:00:00"}

...that would be picked up by Docker just as

.. code-block:: shell

    CMD handoff ${COMMAND:-run} -w workspace -d ${DATA:-{}} -a

See Dockerfile_ for details.

.. _Dockerfile: https://github.com/anelendata/handoff/blob/master/Dockerfile
