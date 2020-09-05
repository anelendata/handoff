# How to write project.yml

The project directory needs to have project.yml.
Here are the hints of defining your own project.yml

```
# commands are required
commands:
  - command: "tap-exchangeratesapi"
    args: "--config config/tap-config.json"
    # List of commands in sequence for non-superuser installing
    installs:
      - "pip install tap-exchangeratesapi"
    # venv is required for Python program only
    venv: "proc_01"
  - command: "python files/stats_collector.py"
    venv: "proc_01"
  - command: "target-csv"
    args: "--config config/target-config.json"
    venv: "proc_02"
    installs:
      - "pip install target-csv"

# deploy is required for using run remote_config, config/files get/push,
#   container, cloud
deploy:
  # For now, aws/fargate is the only supported provider/platform
  provider: "aws"
  platform: "fargate"
  # The environment varaibles listed here are converte to upper case and given
  # "HO_" prefix
  envs:
    resource_group: "handoff-test"
    docker_image: "singer_exchange_rates_to_csv"
    task: "test-03-exchange-rates"
```
