## History

### 0.3.0 (2020-12-28)

A major release with improved interface and new features.

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

### 0.2.0b4 (2020-08-18)

- Workaround for failing setuptools installation script source.

### 0.2.0b3 (2020-08-10)

- Fix the issue of not downloading artifacts from remote storage.
    - Fix artifacts archive/get/push/delete commands
    - Fix files get/push/delete commands
- Add USGS Earthquake events data example

### 0.2.0b2 (2020-08-06)

- Fix the issue of inconsistent state file among OS (trailing spaces)

### 0.2.0b1 (2020-08-05)

- Mac OS: fix a bug in parsing Docker build JSON log
- Mac OS: fix sed -u issue
- Fix typos in tutorial

### 0.2.0b0 (2020-08-05)

- Beta
- Covers entire workflow from the local test to Fargate deployment
- Clean extensible code-design (services and plugins)
- Unit, integration, and installation tests
- Interactive tutorial
- Near-stable CLI version

### 0.1.2-alpha (2020-07-17)

- Alpha
- fix docker files to remove project dir
- fix the issue of env var not passed to subprocesses

### 0.1.1-alpha (2020-07-16)

Just added a long description to setup.py for the pypi release.

### 0.1.0-alpha (2020-07-16)

Pilot. The first package build.
