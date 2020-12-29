[![Build Status](https://travis-ci.com/anelendata/handoff.svg?branch=master)](https://travis-ci.com/anelendata/handoff)
[![Documentation Status](https://readthedocs.org/projects/handoffcloud/badge/?version=latest)](https://dev.handoff.cloud/en/latest/?badge=latest)

# handoff.cloud

<img src="https://github.com/anelendata/handoff/raw/master/assets/this_is_handoff.png"/>

## What is it?

handoff ([repository](https://github.com/anelendata/handoff))
is a framework for developing and deploying data pipelines serverlessly.
executing unix-pipeline processes serverlessly.

handoff removes the complicated cloud configurations. You can easily take care
of the essential settings and save time and money with a single command:

1. Container orchestration (AWS Elastic Continer Service)
2. Extended serverless task execution (AWS Fargate, vs. AWS Lambda's 15min limit) 
3. CRON Scheduling (AWS EventBridge)
4. Configuration and secret management (AWS Systems Manager Parameter Store)
5. Simple switch between production and devlopment stages
6. Docker image management (AWS Elastic Container Registry)
7. Artifacts management (AWS Simple Cloud Storage)
8. Log management (AWS CloudWatch)
9. Shared resource management (Virtual Private Cloud, Security Group)
10. No need to pay and maintain a dedicated virtual instances!

Note: With the unified handoff command, we are planning to support multi-cloud
deployment experience (Azure and Google Cloud Platform).

## How it works

handoff was originally designed to deploy a single-line ETL process like
[singer.io](https://singer.io) on AWS Fargate, and it was extended to
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

## Get started easily

Check out [the super quick example](https://dev.handoff.cloud/en/latest/quick_example.html)

## Open Source handoff Recipes!

We will upload more and more [recipes](https://github.com/anelendata/handoff_recipe) that you can use and learn from!
