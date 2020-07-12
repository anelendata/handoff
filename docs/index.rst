.. handoff.cloud documentation master file, created by
   sphinx-quickstart on Sun Jul 12 04:03:07 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to handoff.cloud's documentation!
=========================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Construct and deploy a configurable unix pipeline process serverlessly*.

What is it?
===========

This is a template repository to build handoff.cloud process:
A framework for executing tasks unix-pipeline process serverlessly.

handoff is originally designed to deploy a single-line ETL process like
[singer.io](https://singer.io) on AWS Fargate, and it was redesigned to
run any commands and program.

In handoff.cloud framework, the configurations are stored and retrieved
from a secure parameter store such as AWS Systems Manager Parameter Store.
This avoids storing sensitive information or configurations that changes
frequently on the Docker image.

Supporting files for commands can also be fetched from a cloud storage such
as AWS S3. The artifacts, the files produced by each command can also
be stored in the cloud storage.

This repository also contains AWS Cloudformation templates and deployment
scripts to support the workflow from local development to the production
deployment.

Clone this repository and follow the easy steps to learn how to use
handoff.cloud in the next few sections.

Next: :doc:`./quick_start`

Indices and tables
==================

* :doc:`./quick_start`
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
