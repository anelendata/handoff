Remote configurations
=====================

Why use cloud storages?
~~~~~~~~~~~~~~~~~~~~~~~

handoff not only lets you run the task locally with `hanoff run_local` command,
but also let you deploy the task in cloud platform (currently supports AWS
Fargate). In production, you do not want to store sensitive information in
Docker images. You may also want to avoid building new image just because
the password or other configurations slightly changes.

So, we store sensitive information in AWS SSM Parameter Store with SecureString
format. And also store other data files that may change frequently to S3. In
the future, we want to support non-AWS storages and deployment options.

We can first store the configurations and files in cloud, and still test
the task locally with the remotely stored configs and files. Then we can
deploy the task to Fargate.

But first, we need to set up the AWS permissions (Policy and Role). This
section explain how best this is achieved.

fgops
-----

Remote configurations and deployment are supported by
`fgops <https://github.com/anelendata/fgops>`_.
fgops can be found at
`./deploy/fargate <https://github.com/anelendata/handoff/tree/master/deploy>`_
in handoff repository. fgops commands are also symlinked from the `bin` directory from handoff
repository's root.

Note: The future plan is to implement a `handoff` subcommand to build Docker
image, run Docker locally, and deloy the task to Fargate.

Creating IAM Role
=================

handoff separates the code (Docker image) and configurations.
We use
`AWS Systems Manager Parameter Store <https://console.aws.amazon.com/systems-manager/parameters>`_
to store the parameter file derived from `project.yml` and other files
under `config` is stoed as a `SecureString`.
Less-sensitive files, prepared in `<project_dir>/files` are copied to AWS S3.

To start accessing the remote resources, we first need to set up the AWS
account. 

Change directory to :code:`./deploy/fargate` to follow these instructions.

.. mdinclude:: ../deploy/fargate/configuration.md

.. mdinclude:: ../deploy/fargate/role.md

Next: :doc:`remote_config`
