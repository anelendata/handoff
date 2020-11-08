# How to write project.yml

The project directory needs to have project.yml.
Here are the hints of defining your own project.yml

```
# commands are required
commands:
  - command: "tap-exchangeratesapi"
    args: "--config files/tap-config.json"
    # List of commands in sequence for non-superuser installing
    installs:
      - "pip install tap-exchangeratesapi"
    # venv is required for Python program only
    venv: "proc_01"
  - command: "python files/stats_collector.py"
    venv: "proc_01"
  - command: "target-csv"
    args: "--config files/target-config.json"
    venv: "proc_02"
    installs:
      - "pip install target-csv"

# deploy is required for using `handoff run`, config/files/secrets push/delete,
#   container, cloud
deploy:
  # For now, aws/fargate is the only supported provider/platform
  cloud_provider: "aws"
  cloud_platform: "fargate"
  resource_group: "handoff-test"
  container_image: "singer_exchange_rates_to_csv"
  task: "test-03-exchange-rates"
```
