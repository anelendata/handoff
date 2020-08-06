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
    args: "--config config/tap-config.json"
    venv: "proc_01"
    installs:
      - "pip install tap-exchangeratesapi"
  - command: "python files/stats_collector.py"
    venv: "proc_01"
  - command: "target-csv"
    args: "--config config/target-config.json"
    venv: "proc_02"
    installs:
      - "pip install target-csv"
deploy:
  provider: "aws"
  platform: "fargate"
  envs:
    resource_group: "handoff-test"
    docker_image: "singer_exchange_rates_to_csv"
    task: "test-03-exchange-rates"
```


...which is shell equivalent to

    tap-exchangeratesapi | python files/stats_collector.py | target-csv



Before we can run this, we need to install tap-exchangeratesapi and target-csv.
The instructions for the install are listed in install section of project.yml.

Notice `venv` entries for each command. handoff can create Python virtual
enviroment for each command to avoid conflicting dependencies among the
commands.

To install everything, run this command:

```shell
> handoff -p 03_exchange_rates -w workspace_03 workspace install
```
```shell

INFO - 2020-08-06 03:35:14,158 - handoff.config - Reading configurations from 03_exchange_rates/project.yml
INFO - 2020-08-06 03:35:14,240 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
INFO - 2020-08-06 03:35:14,524 - handoff.config - You have the access to AWS resources.
INFO - 2020-08-06 03:35:14,524 - handoff.config - Platform: aws
INFO - 2020-08-06 03:35:19,456 - handoff.config - Running /bin/bash -c "source proc_01/bin/activate && pip install wheel && pip install tap-exchangeratesapi"
Requirement already satisfied: wheel in ./proc_01/lib/python3.6/site-packages (0.34.2)
Processing /home/ubuntu/.cache/pip/wheels/1f/73/f9/xxxxxxxx0dba8423841c1404f319bb/tap_exchangeratesapi-0.1.1-cp36-none-any.whl
Processing /home/ubuntu/.cache/pip/wheels/6e/07/1b/xxxxxxxx6d9ce55c05f67a69127e25/singer_python-5.3.3-cp36-none-any.whl
Processing /home/ubuntu/.cache/pip/wheels/fc/d8/34/xxxxxxxx027b62dfcf922fdf8e396d/backoff-1.3.2-cp36-none-any.whl
Collecting requests==2.21.0
.
.
.
Collecting python-dateutil
  Using cached python_dateutil-2.8.1-py2.py3-none-any.whl (227 kB)
Collecting pytzdata
  Using cached pytzdata-2020.1-py2.py3-none-any.whl (489 kB)
Collecting pytz
  Using cached pytz-2020.1-py2.py3-none-any.whl (510 kB)
Collecting six>=1.5
  Using cached six-1.15.0-py2.py3-none-any.whl (10 kB)
Installing collected packages: jsonschema, simplejson, pytz, tzlocal, six, python-dateutil, pytzdata, pendulum, singer-python, target-csv
Successfully installed jsonschema-2.6.0 pendulum-1.2.0 python-dateutil-2.8.1 pytz-2020.1 pytzdata-2020.1 simplejson-3.11.1 singer-python-2.1.4 six-1.15.0 target-csv-0.3.0 tzlocal-2.1
```

Now let's run the task. Try entering this command below:

```shell
> handoff -p 03_exchange_rates -w workspace_03 run local
```
```shell

INFO - 2020-08-06 03:35:29,258 - handoff.config - Reading configurations from 03_exchange_rates/project.yml
INFO - 2020-08-06 03:35:29,339 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
INFO - 2020-08-06 03:35:29,626 - handoff.config - You have the access to AWS resources.
INFO - 2020-08-06 03:35:29,626 - handoff.config - Platform: aws
INFO - 2020-08-06 03:35:29,626 - handoff.config - Setting environment variables from config.
INFO - 2020-08-06 03:35:29,693 - handoff.config - Environment variable HO_BUCKET was set autoamtically as xxxxxxxxxxxx-handoff-test
INFO - 2020-08-06 03:35:29,693 - handoff.config - Writing configuration files in the workspace configuration directory workspace_03/config
INFO - 2020-08-06 03:35:29,694 - handoff.config - Copying files from the local project directory 03_exchange_rates
INFO - 2020-08-06 03:35:29,695 - handoff.config - Running run local in workspace_03 directory
INFO - 2020-08-06 03:35:29,695 - handoff.config - Job started at 2020-08-06 03:35:29.695732
.
.
.
INFO - 2020-08-06 03:35:33,964 - handoff.config - Job ended at 2020-08-06 03:35:33.964206
INFO - 2020-08-06 03:35:33,964 - handoff.config - Processed in 0:00:04.268474
```

This process should have created a CSV file in artifacts directory:

```shell

exchange_rate-20200806T033530.csv
```

...which looks like:

```shell

CAD,HKD,ISK,PHP,DKK,HUF,CZK,GBP,RON,SEK,IDR,INR,BRL,RUB,HRK,JPY,THB,CHF,EUR,MYR,BGN,TRY,CNY,NOK,NZD,ZAR,USD,MXN,SGD,AUD,ILS,KRW,PLN,date
0.0127290837,0.0725398406,1.3197211155,0.4630976096,0.0618218792,2.9357569721,0.2215388446,0.007434429,0.0401958831,0.0863047809,135.1005146082,0.7041915671,0.050374336,0.6657569721,0.0625373506,1.0,0.29312749,0.0088188911,0.0083001328,0.0399311089,0.0162333997,0.0642571381,0.0655312085,0.0889467131,0.0142670983,0.158440405,0.0093592297,0.2132744024,0.0130336985,0.0134852258,0.032375498,11.244189907,0.0371372842,2020-07-10T00:00:00Z
0.0126573311,0.072330313,1.313014827,0.4612685338,0.061324547,2.9145799012,0.2195057661,0.007408402,0.0399036244,0.085529654,134.613509061,0.7019439868,0.049830313,0.6601894563,0.0620593081,1.0,0.2929324547,0.0088014827,0.0082372323,0.0397907743,0.0161103789,0.0641054366,0.0653286656,0.0878500824,0.0141894563,0.1562817133,0.0093319605,0.209931631,0.0129678748,0.013383855,0.0321466227,11.2139209226,0.0368682043,2020-07-13T00:00:00Z
```


Now that we know how to run locally, we will gradually thinking about how to deploy this in the cloud *severlessly*.
We will learn how to save and fetch the configurations to the remote storage.
Before doing that, we will cover how to set up AWS account and profile in the next section.

