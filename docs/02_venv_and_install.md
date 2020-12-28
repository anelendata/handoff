## Virtual environment and install

Let's make a little more practical data pipeline application. In this section,
we will retrieve currency exchange rates and write out to CSV file.

We will install singer.io (https://singer.io), a data collection framework,
in Python vitual environment.



We will use 04_install project. Here is project.yml:

```shell
> cat 04_install/project.yml
```

```shell
version: 0.3
description: Fetch foreign exchange rates

installs:
- venv: tap
  command: pip install tap-exchangeratesapi
- venv: target
  command: pip install target-csv

vars:
- key: base_currency
  value: USD

tasks:
- name: fetch_exchange_rates
  description: Fetch exchange rates
  pipeline:
  - command: tap-exchangeratesapi
    args: --config files/tap-config.json
    venv: tap
  - command: python
    args: files/stats_collector.py
    venv: tap
  - command: target-csv
    args: --config files/target-config.json
    venv: target

deploy:
  cloud_provider: aws
  cloud_platform: fargate
  resource_group: handoff-etl
  container_image: xxxxxxxxv
  task: exchange-rates-to-csv

schedules:
- target_id: 1
  cron: "0 0 * * ? *"
  envs:
  - key: __VARS
    value: 'start_date=$(date -I -d "-7 day")'

```


What's new here is the installs section that lists the shell command to
install the necessary program for this project.

For each install, you can set venv key to set the name of the Python virtual
environment. This helps avoid the dependency conflicts among Python programs.

(The deploy and schedule sections in the file are irrelevant in this section.
We will use it later.)



The project runs a pipeline that is a shell equivalent to

    tap-exchangeratesapi | python files/stats_collector.py | target-csv



Before we can run this, we need to install a couple of Python packages:
tap-exchangeratesapi and target-csv. The `install` section contains the 
installation commands. Also notice `venv` entries for each command. handoff
can create Python virtual enviroment for each command to avoid conflicting
dependencies among the packages.

To install, run this command:

```shell
> handoff workspace install -p 04_install -w workspace_04
```
```shell

[2020-12-28 22:02:12,049] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
Requirement already satisfied: wheel in ./tap/lib/python3.6/site-packages (0.36.2)
Collecting tap-exchangeratesapi
  Using cached tap_exchangeratesapi-0.1.1-cp36-none-any.whl
Collecting backoff==1.3.2
  Using cached backoff-1.3.2-cp36-none-any.whl
Collecting requests==2.21.0
  Using cached requests-2.21.0-py2.py3-none-any.whl (57 kB)
Collecting singer-python==5.3.3
  Using cached singer_python-5.3.3-cp36-none-any.whl
.
.
.
  Using cached six-1.15.0-py2.py3-none-any.whl (10 kB)
Collecting pytzdata
  Using cached pytzdata-2020.1-py2.py3-none-any.whl (489 kB)
Collecting tzlocal
  Using cached tzlocal-2.1-py2.py3-none-any.whl (16 kB)
Collecting pytz
  Using cached pytz-2020.5-py2.py3-none-any.whl (510 kB)
Installing collected packages: six, pytz, tzlocal, pytzdata, python-dateutil, simplejson, pendulum, singer-python, jsonschema, target-csv
Successfully installed jsonschema-2.6.0 pendulum-1.2.0 python-dateutil-2.8.1 pytz-2020.5 pytzdata-2020.1 simplejson-3.11.1 singer-python-2.1.4 six-1.15.0 target-csv-0.3.0 tzlocal-2.1
sucess
```

Now, if you look at tap-config.json under files folder,

```shell
> cat 04_install/files/tap-config.json
```

```shell
{ "base": "{{ base_currency }}", "start_date": "{{ start_date }}" }

```

...you will notice {{ start_date }} variable but it is not defined in
project.yml. That is because I did not want to hardcode a particular date.
Instead, let's fill a value when we run handoff run command.

The following command, for example, sets the start_date as 7 days ago:

```shell
> handoff run local -p 04_install -w workspace_04 -v start_date=$(date -I -d "-7 day")
```
```shell

[2020-12-28 22:02:27,352] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-12-28 22:02:27,707] [    INFO] - Job started at 2020-12-28 22:02:27.707674 - (__init__.py:178)
[2020-12-28 22:02:27,707] [    INFO] - Running pipeline fetch_exchange_rates - (operators.py:193)
[2020-12-28 22:02:27,726] [    INFO] - Checking return code of pid 3033 - (operators.py:262)
[2020-12-28 22:02:28,313] [    INFO] - Checking return code of pid 3034 - (operators.py:262)
[2020-12-28 22:02:28,320] [    INFO] - Checking return code of pid 3036 - (operators.py:262)
[2020-12-28 22:02:28,338] [    INFO] - Pipeline fetch_exchange_rates exited with code 0 - (task.py:32)
[2020-12-28 22:02:28,338] [    INFO] - Job ended at 2020-12-28 22:02:28.338382 - (__init__.py:184)
[2020-12-28 22:02:28,338] [    INFO] - Processed in 0:00:00.630708 - (__init__.py:186)
```



This task should have created a CSV file in artifacts directory:

```shell

exchange_rate-20201228T220228.csv
```


We learned how to install Pythonn packages and in this section.
The exchange rate application is more practical use of handoff.
04_install project fetched the data from an API and store the data to the
destination (CSV file).

In the next section, we will learn a little more advanced flow logic
such as foreach and fork.

