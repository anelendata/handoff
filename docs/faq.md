# FAQs

## Q. How do I configure project.yml so it installs an Python command from git?

You can put `https://github.com/<account>/<repository>/archive/<commit-hash>.tar.gz#egg=<command-name>`
format like this project of executing a pair of singer.io processes,
[tap_rest_api](https://github.com/anelendata/tap_rest_api) and
[target_gcs](https://github.com/anelendata/target_gcs):
```
commands:
  - command: tap_rest_api
    args: ".env/rest_api_spec.json --config .env/config/tap_config.json --schema_dir .env/schema --catalog .env/catalog/default.json --state .artifacts/state    --start_datetime '{start_at}' --end_datetime '{end_at}'"
    venv: "./venv/proc_01"
    installs:
      - "pip install --no-cache-dir https://github.com/anelendata/tap_rest_api/archive/1b46f383b62c8dc9ce1205c5cf67c7ebc3107349.tar.gz#egg=tap_rest_api"
  - command: target_gcs
    args: "--config .env/config/target_config.json"
    venv: "./venv/proc_02"
    installs:
      - "pip install install --no-cache-dir https://github.com/anelendata/target_gcs/archive/17e70bced723fe202425a61199e6e1180b6fada7.tar.gz#egg=target_gcs"
envs:
  - key: "GOOGLE_APPLICATION_CREDENTIALS"
    value: ".env/config/google_client_secret.json"
```
