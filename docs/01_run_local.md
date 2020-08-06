## Running a task locally

In this section, we will learn how to run a task with handoff locally,
using project 01_word_count.



Each project directory contains:

```shell
> ls -l 01_word_count
```
```shell

 files
 project.yml
```


project.yml looks like:

```shell
> cat 01_word_count/project.yml
```

```shell
commands:
  - command: cat
    args: "./files/the_great_dictator_speech.txt"
  - command: wc
    args: "-w"
envs:
  - key: TITLE
    value: "The Great Dictator"
```


Here,

- `commands` lists the commands and arguments.
- `envs` lists the environment varaibles.


The example from 01_word_count runs a command line equivalent of:

```shell
cat ./files/the_great_dictator_speech.txt | wc -w
```

Now let's run. Try entering this command below:

```shell
> handoff --project 01_word_count --workspace workspace run local
```
```shell

INFO - 2020-08-06 03:35:12,691 - handoff.config - Reading configurations from 01_word_count/project.yml
INFO - 2020-08-06 03:35:12,693 - handoff.config - Setting environment variables from config.
INFO - 2020-08-06 03:35:12,771 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
INFO - 2020-08-06 03:35:13,056 - handoff.config - You have the access to AWS resources.
WARNING - 2020-08-06 03:35:13,123 - handoff.config - Environment variable HO_BUCKET is not set. Remote file read/write will fail.
INFO - 2020-08-06 03:35:13,123 - handoff.config - Writing configuration files in the workspace configuration directory workspace/config
INFO - 2020-08-06 03:35:13,123 - handoff.config - Copying files from the local project directory 01_word_count
INFO - 2020-08-06 03:35:13,124 - handoff.config - Running run local in workspace directory
INFO - 2020-08-06 03:35:13,124 - handoff.config - Job started at 2020-08-06 03:35:13.124542
INFO - 2020-08-06 03:35:13,130 - handoff.config - Job ended at 2020-08-06 03:35:13.130391
```


If you see the output that looks like:

```shell

 INFO - 2020-08-03 04:51:01,971 - handoff.config - Reading configurations from 01_word_count/project.yml
 ...
 INFO - 2020-08-03 04:51:02,690 - handoff.config - Processed in 0:00:00.005756

```


Then great! You just ran the first local test. It created a workspace
directory that looks like:

```shell
> ls -l workspace
```
```shell

 artifacts
 config
 files
```

And the word count is stored at workspace/artifacts/state. Here is the content:

```shell
> cat  workspace/artifacts/state
```

```shell
644
```


By the way, the example text is from the awesome speech by Charlie Chaplin's
in the movie the Great Dictator.

Here is a link to the famous speech scene.
Check out on YouTube: https://www.youtube.com/watch?v=J7GY1Xg6X20



And here is the first few paragraphs of the text:

```shell

I’m sorry, but I don’t want to be an emperor. That’s not my business. I don’t want to rule or conquer anyone. I should like to help everyone - if possible - Jew, Gentile - black man - white. We all want to help one another. Human beings are like that. We want to live by each other’s happiness - not by each other’s misery. We don’t want to hate and despise one another. In this world there is room for everyone. And the good earth is rich and can provide for everyone. The way of life can be free and beautiful, but we have lost the way.

Greed has poisoned men’s souls, has barricaded the world with hate, has goose-stepped us into misery and bloodshed. We have developed speed, but we have shut ourselves in. Machinery that gives abundance has left us in want. Our knowledge has made us cynical. Our cleverness, hard and unkind. We think too much and feel too little. More than machinery we need humanity. More than cleverness we need kindness and gentleness. Without these qualities, life will be violent and all will be lost….

```


Now to the second example. This time project.yml looks like:

```shell
> cat 02_collect_stats/project.yml
```

```shell
commands:
  - command: cat
    args: ./files/the_great_dictator_speech.txt
  - command: python files/stats_collector.py
  - command: wc
    args: -w
```


...which is shell equivalent to

```shell
cat ./files/the_great_dictator_speech.txt | python ./files/stats_collector.py | wc -w
```

The script for the second command stats_collector.py can be found in
02_collect_stats/files directory and it is a Python script that looks like:


```shell
> cat 02_collect_stats/files/stats_collector.py
```

```python
#!/usr/bin/python
import io, json, logging, sys, os

LOGGER = logging.getLogger()

def collect_stats(outfile):
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


if __name__ == "__main__":
    collect_stats("artifacts/collect_stats.json")
```

The script reads from stdin and counts the lines while passing the raw input to stdout.
The raw text is then processed by the third command (wc -w) and it conts the number of words.



Now let's run. Try entering this command below:

```shell
> handoff --project 02_collect_stats --workspace workspace run local
```
```shell

INFO - 2020-08-06 03:35:13,401 - handoff.config - Reading configurations from 02_collect_stats/project.yml
INFO - 2020-08-06 03:35:13,402 - handoff.config - Setting environment variables from config.
INFO - 2020-08-06 03:35:13,481 - botocore.credentials - Found credentials in shared credentials file: ~/.aws/credentials
INFO - 2020-08-06 03:35:13,765 - handoff.config - You have the access to AWS resources.
WARNING - 2020-08-06 03:35:13,830 - handoff.config - Environment variable HO_BUCKET is not set. Remote file read/write will fail.
INFO - 2020-08-06 03:35:13,830 - handoff.config - Writing configuration files in the workspace configuration directory workspace/config
INFO - 2020-08-06 03:35:13,830 - handoff.config - Copying files from the local project directory 02_collect_stats
INFO - 2020-08-06 03:35:13,831 - handoff.config - Running run local in workspace directory
INFO - 2020-08-06 03:35:13,831 - handoff.config - Job started at 2020-08-06 03:35:13.831683
INFO - 2020-08-06 03:35:13,881 - handoff.config - Job ended at 2020-08-06 03:35:13.881507
INFO - 2020-08-06 03:35:13,881 - handoff.config - Processed in 0:00:00.049824
```

Let's check out the contents of the second command:


```shell
> cat workspace/artifacts/collect_stats.json
```

```shell
{"rows_read": 15}
```


In the next section, we will try pullin the currency exchange rate data.
You will also learn how to create Python virtual enviroments for each command
and pip-install commands.
