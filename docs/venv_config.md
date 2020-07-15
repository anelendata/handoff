# Virtual envs and configs

## Running a Python Program in a Virtual Environment

You can specify a virtual environments in case the command is a Python program.
In `project.yml`, you can also define virtual environment for Python program:
```
commands:
  - command: cat
    args: "./README.md"
  - command: "./scripts/python/collector_stats.py"
    venv: "./venv/root"
```

`collector_stats.py` is a simple Python program that pass on from stdin to
stdout while counting the number of rows. It is already in handoff repo, you
don't need to make the file. The function looks like this:
```
def collector_stats(outfile):
    """
    Read from stdin and count the lines. Output to a file after done.
    """
    lines = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
    output = {"rows_read": 0}
    for line in lines:
        try:
            o = json.loads(line)
            print(json.dumps(o))
            if o["type"].lower() == "record":
                output["rows_read"] += 1
        except json.decoder.JSONDecodeError:
            print(line)
            output["rows_read"] += 1
    with open(outfile, "w") as f:
        json.dump(output, f)
        f.write("\n")
```

Try runing:
```
./bin/mkvenvs
./bin/mkparams > ./.env/params.json
./bin/runlocal ./.env/params.json
```

This time, you will get `.artifacts/collector_stats.json` that looks like:
```
{"rows_read": 42}
```

Also notice that we chained 3 commands instead 2. This time, we got
`.artifacts/state` that contains the output of `wc` command:
```
     84     213    1715
```

Note: The example above is useful for the singer.io users who wants to insert
a transform process between tap and target.

## How to use config files: Fetching exchange rates with singer.io

The configuration files that may contain sensitive information go to
`.local` directory.

Such configuration files include singer.io tap and target's JSON config files,
and Google Cloud Platform key JSON file.

Note: Currently, only JSON files are supported for remote config store.

Example:

1. Update the project file.

.local/project.yml:
```
commands:
  - command: "tap-exchangeratesapi"
    args: "--config ./.env/config/tap-config.json"
    venv: "./venv/proc_01"
    installs:
      - "pip install tap-exchangeratesapi"
  - command: "./scripts/python/collector_stats.py"
    venv: "./venv/root"
  - command: "target-csv"
    venv: "./venv/proc_02"
    installs:
      - "pip install target-csv"
```

2. Make environments defined in the project and install commands

```
./bin/mkvenvs
```

3. Create a copy of config file for tap-exchangeratesapi:

In Debian/Ubuntu:
```
echo '{ "base": "JPY", "start_date": "'`date -d "$date -7 days" +'%Y-%m-%d'`'" }' \
  > .local/tap-config.json
```

In MacOS:
```
echo '{ "base": "JPY", "start_date": "'`date -v -7d  +'%Y-%m-%d'`'" }' \
  > .local/tap-config.json
```

`.local/tap-config.json` should looks something like:
```
{ "base": "JPY", "start_date": "2020-07-06" }
```


4. Generate parameter file and run:
```
./bin/mkparams > .env/params.json
```

You will see the content of `tap-config.json` included in `params.json`:
```
cat .env/params.json
```

Now let's run:
```
./bin/runlocal .env/params.json
```

This should output something like:
```
INFO - 2020-07-12 08:52:13,240 - impl.runner: Running run data:{}
INFO - 2020-07-12 08:52:13,240 - impl.runner: Running run
INFO - 2020-07-12 08:52:13,241 - impl.runner: Reading parameters from file: .env/params.json
INFO - 2020-07-12 08:52:13,241 - impl.runner: Job started at 2020-07-12 15:52:13.241577
INFO Replicating exchange rate data from 2020-07-10 using base JPY
INFO Sending version information to singer.io. To disable sending anonymous usage data, set the config parameter "disable_collection" to true
INFO Replicating exchange rate data from 2020-07-11 using base JPY
INFO Replicating exchange rate data from 2020-07-12 using base JPY
INFO Tap exiting normally
INFO - 2020-07-12 08:52:13,950 - impl.runner: Job ended at 2020-07-12 15:52:13.950879
INFO - 2020-07-12 08:52:13,951 - impl.runner: Processed in 0:00:00.709302
```

and produce a file `exchange_rate-{timestamp}.csv` in the current directory that looks like:
```
CAD,HKD,ISK,PHP,DKK,HUF,CZK,GBP,RON,SEK,IDR,INR,BRL,RUB,HRK,JPY,THB,CHF,EUR,MYR,BGN,TRY,CNY,NOK,NZD,ZAR,USD,MXN,SGD,AUD,ILS,KRW,PLN,date
0.0127290837,0.0725398406,1.3197211155,0.4630976096,0.0618218792,2.9357569721,0.2215388446,0.007434429,0.0401958831,0.0863047809,135.1005146082,0.7041915671,0.050374336,0.6657569721,0.0625373506,1.0,0.29312749,0.0088188911,0.0083001328,0.0399311089,0.0162333997,0.0642571381,0.0655312085,0.0889467131,0.0142670983,0.158440405,0.0093592297,0.2132744024,0.0130336985,0.0134852258,0.032375498,11.244189907,0.0371372842,2020-07-10T00:00:00Z
```

It also leaves `.artifacts/state` and `.artifacts/collector_stats.json`.

Next: [Outputs](outputs)
