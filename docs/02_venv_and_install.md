## Virtual environment and install

In this section, we will retrieve currency exchange rates and write out to CSV
file.

We will install singer.io (https://singer.io), a data collection framework,
in Python vitual environment.



We will use 04_install project. project.yml looks like:

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

(The deploy section in the file is irrelevant and unnecessary for now.
We will use it in the later exercise.)



The project runs a pipeline that is a shell equivalent to

    tap-exchangeratesapi | python files/stats_collector.py | target-csv



Before we can run this, we need to install tap-exchangeratesapi and target-csv.
The instructions for the install are listed in install section of project.yml.

Notice `venv` entries for each command. handoff can create Python virtual
enviroment for each command to avoid conflicting dependencies among the
commands.

To install everything, run this command:

```shell
> handoff workspace install -p 04_install -w workspace_04
```
```shell

Requirement already satisfied: wheel in ./tap/lib/python3.6/site-packages (0.36.2)
Collecting tap-exchangeratesapi
  Using cached tap_exchangeratesapi-0.1.1-cp36-none-any.whl
Collecting backoff==1.3.2
  Using cached backoff-1.3.2-cp36-none-any.whl
Collecting requests==2.21.0
  Using cached requests-2.21.0-py2.py3-none-any.whl (57 kB)
Collecting singer-python==5.3.3
  Using cached singer_python-5.3.3-cp36-none-any.whl
Collecting jsonschema==2.6.0
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

Now, if you look at tap-config.json,

```shell
> cat 04_install/files/tap-config.json
```

```shell
{ "base": "{{ base_currency }}", "start_date": "{{ start_date }}" }

```
You will notice {{ start_date }} variable but it is not defined in
project.yml. That is because I did not hardcode this value. If I did, you would
have to fetch a lot of data. Instead, let's set it when you run handoff run command.

Try this to get the last 7 days of the data:

```shell
> handoff run local -p 04_install -w workspace_04 -v start_date=$(date -I -d "-7 day")
```
```shell

Running run local in workspace_04 directory
Job started at 2020-12-28 08:03:32.153881
[2020-12-28 08:03:32,153] [    INFO] - Running pipeline fetch_exchange_rates - (operators.py:193)
[2020-12-28 08:03:32,170] [    INFO] - Checking return code of pid 21980 - (operators.py:262)
[2020-12-28 08:03:33,481] [    INFO] - Checking return code of pid 21981 - (operators.py:262)
[2020-12-28 08:03:33,488] [    INFO] - Checking return code of pid 21983 - (operators.py:262)
Job ended at 2020-12-28 08:03:33.506941
Processed in 0:00:01.353060
```



This process should have created a CSV file in artifacts directory:

```shell

exchange_rate-20201228T080332.csv
```


We learned how to install Python command in a virtual environment and run
in this section. The exchange rate application is a realistic use of fetching
the data from an API and store the data to the destination store.
In the next section, we will learn a little more advanced flow logic
such as foreach and fork.

