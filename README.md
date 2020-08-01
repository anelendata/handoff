[![Build Status](https://travis-ci.com/anelendata/handoff.svg?branch=master)](https://travis-ci.com/anelendata/handoff)
[![Documentation Status](https://readthedocs.org/projects/handoffcloud/badge/?version=latest)](https://dev.handoff.cloud/en/latest/?badge=latest)

# handoff.cloud

Deploy configurable unix pipeline jobs serverlessly.

<img style="width: 320px; text-align: center;" src="./assets/handoff_logo.png"/>

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
