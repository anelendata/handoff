## Virtual environment and install

In this section, we will retrieve currency exchange rates and write out to CSV
file.

We will install singer.io (https://singer.io), a data collection framework,
in Python vitual environment.



We will use 03_exchange_rates project. project.yml looks like:

```shell
> cat 03_exchange_rates/project.yml
```

```shell
commands:
  - command: "tap-exchangeratesapi"
    args: "--config files/tap-config.json"
    venv: "proc_01"
    installs:
      - "pip install tap-exchangeratesapi"
  - command: "python files/stats_collector.py"
    venv: "proc_01"
  - command: "target-csv"
    args: "--config files/target-config.json"
    venv: "proc_02"
    installs:
      - "pip install target-csv"
deploy:
  cloud_provider: "aws"
  cloud_platform: "fargate"
  resource_group: "handoff-test"
  container_image: "singer_exchange_rates_to_csv"
  task: "test-exchange-rates"
```


(The deploy section in the file is irrelevant and unnecessary for now.
We will use it in the later exercise.)


...which is shell equivalent to

    tap-exchangeratesapi | python files/stats_collector.py | target-csv



Before we can run this, we need to install tap-exchangeratesapi and target-csv.
The instructions for the install are listed in install section of project.yml.

Notice `venv` entries for each command. handoff can create Python virtual
enviroment for each command to avoid conflicting dependencies among the
commands.

To install everything, run this command:

```shell
> handoff workspace install -p 03_exchange_rates -w workspace_03
```
```shell

[2020-11-09 01:46:11,331] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:144)
[2020-11-09 01:46:11,460] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 01:46:11,740] [    INFO] - You have the access to AWS resources. - (__init__.py:69)
[2020-11-09 01:46:11,740] [    INFO] - Platform: aws - (admin.py:164)
[2020-11-09 01:46:11,740] [    INFO] - Setting environment variables from config. - (admin.py:92)
[2020-11-09 01:46:11,806] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxt - (admin.py:115)
[2020-11-09 01:46:11,806] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:144)
[2020-11-09 01:46:11,809] [    INFO] - Platform: aws - (admin.py:164)
[2020-11-09 01:46:15,810] [    INFO] - Running /bin/bash -c "source proc_01/bin/activate && pip install wheel" - (admin.py:30)
Requirement already satisfied: wheel in ./proc_01/lib/python3.6/site-packages (0.35.1)
.
.
.
Collecting tzlocal
  Using cached tzlocal-2.1-py2.py3-none-any.whl (16 kB)
Collecting python-dateutil
  Using cached python_dateutil-2.8.1-py2.py3-none-any.whl (227 kB)
Collecting pytz
  Using cached pytz-2020.4-py2.py3-none-any.whl (509 kB)
Collecting six>=1.5
  Using cached six-1.15.0-py2.py3-none-any.whl (10 kB)
Installing collected packages: simplejson, pytzdata, pytz, tzlocal, six, python-dateutil, pendulum, singer-python, jsonschema, target-csv
Successfully installed jsonschema-2.6.0 pendulum-1.2.0 python-dateutil-2.8.1 pytz-2020.4 pytzdata-2020.1 simplejson-3.11.1 singer-python-2.1.4 six-1.15.0 target-csv-0.3.0 tzlocal-2.1
```

Now let's run the task. Try entering this command below:

```shell
> handoff run local -p 03_exchange_rates -w workspace_03
```
```shell

[2020-11-09 01:46:24,654] [    INFO] - Reading configurations from 03_exchange_rates/project.yml - (admin.py:144)
[2020-11-09 01:46:24,779] [    INFO] - Found credentials in shared credentials file: ~/.aws/credentials - (credentials.py:1182)
[2020-11-09 01:46:25,054] [    INFO] - You have the access to AWS resources. - (__init__.py:69)
[2020-11-09 01:46:25,055] [    INFO] - Platform: aws - (admin.py:164)
[2020-11-09 01:46:25,055] [    INFO] - Setting environment variables from config. - (admin.py:92)
[2020-11-09 01:46:25,118] [    INFO] - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxt - (admin.py:115)
[2020-11-09 01:46:25,119] [ WARNING] - 03_exchange_rates/.secrets/secrets.yml does not exsist - (admin.py:206)
[2020-11-09 01:46:25,119] [    INFO] - Copying files from the local project directory 03_exchange_rates - (admin.py:504)
[2020-11-09 01:46:25,125] [    INFO] - Running run local in workspace_03 directory - (__init__.py:174)
[2020-11-09 01:46:25,125] [    INFO] - Job started at 2020-11-09 01:46:25.125485 - (__init__.py:176)
.
.
.
[2020-11-09 01:46:27,914] [    INFO] - Job ended at 2020-11-09 01:46:27.914722 - (__init__.py:182)
[2020-11-09 01:46:27,915] [    INFO] - Processed in 0:00:02.789237 - (__init__.py:184)
```

This process should have created a CSV file in artifacts directory:

```shell

exchange_rate-20201109T014625.csv
```

...which looks like:

```shell

CAD,HKD,ISK,PHP,DKK,HUF,CZK,GBP,RON,SEK,IDR,INR,BRL,RUB,HRK,JPY,THB,CHF,EUR,MYR,BGN,TRY,CNY,NOK,NZD,ZAR,USD,MXN,SGD,AUD,ILS,KRW,PLN,date
0.0122912071,0.0731957138,1.2960920265,0.4583280807,0.0586463914,2.7893161046,0.2066341002,0.0070103215,0.038132682,0.0816301607,137.6068389537,0.6886897258,0.0513126379,0.6945115033,0.059344469,1.0,0.2934919634,0.0085605106,0.0078789789,0.0391238575,0.0154097069,0.0694894422,0.0644019855,0.0822392058,0.0139670659,0.1571533249,0.009444532,0.2050724866,0.0128222502,0.0127970375,0.0316601009,11.1890954932,0.0346084147,2020-09-01T00:00:00Z
0.012297619,0.0729563492,1.3055555556,0.4576587302,0.0590571429,2.8473809524,0.209031746,0.0070507937,0.0384309524,0.081797619,138.8019047619,0.6890674603,0.0509563492,0.6989484127,0.0597896825,1.0,0.2944047619,0.0085706349,0.0079365079,0.0390285714,0.0155222222,0.0695142857,0.0642666667,0.0825873016,0.0139214286,0.1580587302,0.0094134921,0.2056746032,0.0128198413,0.012834127,0.0316674603,11.1751587302,0.035068254,2020-09-02T00:00:00Z
```


Now that we know how to run locally, we will gradually thinking about how to deploy this in the cloud *severlessly*.
We will learn how to save and fetch the configurations to the remote storage.
Before doing that, we will cover how to set up AWS account and profile in the next section.

