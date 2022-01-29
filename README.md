[![Build Status](https://travis-ci.com/anelendata/handoff.svg?branch=master)](https://travis-ci.com/anelendata/handoff)
[![Documentation Status](https://readthedocs.org/projects/handoffcloud/badge/?version=latest)](https://dev.handoff.cloud/en/latest/?badge=latest)

# handoff core

👉 For a fully managed service, checkout [handoff.cloud website](https://handoff.cloud)

<img src="https://github.com/anelendata/handoff/raw/master/assets/this_is_handoff.png"/>

## What is it?

handoff ([repository](https://github.com/anelendata/handoff))
is a single command that let you quickly orchestrate the data pipeline on
a serverless platform such as AWS Fargate.

Deploying on a serverless platform saves you from the need for managing servers
and paying for idling virtual machines. The serverless configuration could be
very complicated, so handoff takes care of it under the hood so you can focus on
the pipeline logic.

Features and benefits:

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

## Get started easily

Check out [the super quick example](https://dev.handoff.cloud/en/latest/quick_example.html)
and [tutorial](https://dev.handoff.cloud/en/latest/tutorial.html).

## Open Source handoff Recipes!

We will upload more and more [recipes](https://github.com/anelendata/handoff_recipe) that you can use and learn from!

# About this project

This project is developed by
ANELEN and friends. Please check out the ANELEN's
[open innovation philosophy and other projects](https://anelen.co/open-source.html)

![ANELEN](https://avatars.githubusercontent.com/u/13533307?s=400&u=a0d24a7330d55ce6db695c5572faf8f490c63898&v=4)
---

Copyright &copy; 2020~ Anelen Co., LLC
