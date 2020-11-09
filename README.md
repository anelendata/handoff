[![Build Status](https://travis-ci.com/anelendata/handoff.svg?branch=master)](https://travis-ci.com/anelendata/handoff)
[![Documentation Status](https://readthedocs.org/projects/handoffcloud/badge/?version=latest)](https://dev.handoff.cloud/en/latest/?badge=latest)

# handoff.cloud

Deploy configurable unix pipeline jobs serverlessly.

**NEW:**
- Version 0.3.0 has been released!
  See [HISTORY.md](https://github.com/anelendata/handoff/blob/v0.3/HISTORY.md)

<img src="https://github.com/anelendata/handoff/raw/master/assets/handoff_landscape_transparent.png"/>

## What is it?

handoff ([repository](https://github.com/anelendata/handoff))
is a framework for executing unix-pipeline processes serverlessly.
It separates the code and run-time configurations, making the deployment
faster, more flexible, and more secure.

handoff helps the teams who want to:
- Automate the ETL/ELT process ([earthquake data ELT example](https://articles.anelen.co/elt-google-cloud-storage-bigquery/))
- Massively web-crawl and collect data ([market & education data example](https://articles.anelen.co/kinoko_webcrawler/))
- Relieve the pain of managing Apache Airflow Worker nodes.

...and more!

handoff is an open-source (APLv2) project sponsored by [ANELEN](https://anelen.co).

## Top 10 Features

handoff simplifies the cloud orchestration.
Developers can enjoy a seamless experience from local devlopment to cloud deployment.

1. Fully managed container orchestration (AWS Elastic Continer Service)
2. Extended (> 15min) serverless task execution (AWS Fargate)
3. CRON Scheduling (AWS EventBridge)
4. Configuration and secret management (AWS Systems Manager Parameter Store)
5. Simple switch between production and devlopment stages
6. Docker image management (AWS Elastic Container Registry)
7. Artifacts management (AWS Simple Cloud Storage)
8. Log management (AWS CloudWatch)
9. Shared resource management (Virtual Private Cloud, Security Group)
10. No need to pay and maintain a dedicated virtual machine!

Note: With a unified handoff command, we are planning to support multi-cloud
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
