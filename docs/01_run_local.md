## Running a task locally

In this section, we will learn how to run a task with handoff locally,
using project 01_word_count.



### project.yml

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
version: 0.3
description: A simple pipeline to count words from a text file

tasks:
- name: word_count
  description: This task will be executed as 'cat <file_path> | wc -w'
  pipeline:
  - command: cat
    args: files/the_great_dictator_speech.txt
  - command: wc
    args: -w

```


Here,

- `tasks` is a list defining each task
- Under the `tasks`, there is a `pipeline`
- `pipeline` lists commands and their arguments


The example from 01_word_count runs a command line equivalent of:

```shell
cat files/the_great_dictator_speech.txt | wc -w
```

cat writes out the content of the file to the stdin, and it is picked up by
wc command through Unix pipeline and it counts the number of words.

Now let's run. Try entering this command below:

```shell
> handoff run local --project 01_word_count --workspace workspace
```
```shell

Running run local in workspace directory
Job started at 2020-12-28 08:03:14.818033
[2020-12-28 08:03:14,818] [    INFO] - Running pipeline word_count - (operators.py:193)
[2020-12-28 08:03:14,825] [    INFO] - Checking return code of pid 21847 - (operators.py:262)
[2020-12-28 08:03:14,826] [    INFO] - Checking return code of pid 21848 - (operators.py:262)
Job ended at 2020-12-28 08:03:14.827343
Processed in 0:00:00.009310
```


If you see the output that looks like:

```shell

 Running run local in workspace directory
 Job started at 2020-12-27 22:53:51.190660
 [2020-12-27 22:53:51,190] [ INFO] - Running pipeline word_count - (operators.py:193)
 [2020-12-27 22:53:51,198] [ INFO] - Checking return code of pid 6472 - (operators.py:262)
 [2020-12-27 22:53:51,199] [ INFO] - Checking return code of pid 6473 - (operators.py:262)
 Job ended at 2020-12-27 22:53:51.200250
 Processed in 0:00:00.009590

```


Then great! You just ran handoff task locally.
    
For now, let's not worry about the warnings in the log such as:

```shell

 [WARNING] - 01_word_count/.secrets/secrets.yml does not exsist
```

This is for using handoff's template feature with secret variables.


```shell

 [WARNING] - Environment variable HO_BUCKET is not set. Remote file read/write will fail.
```

This is for running the task with remotely stored configurations and files.
I will explain in the later section.



### Output in workspace directory

The previous run created a workspace directory that looks like:

```shell
> ls -l workspace
```
```shell

 artifacts
 files
```

And the word count is stored at workspace/artifacts/word_count_stdout.log. Here is the content:

```shell
> cat workspace/artifacts/word_count_stdout.log
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


### Variables

Now to the second example. This time project.yml looks like:

```shell
> cat 02_commands_and_vars/project.yml
```

```shell
version: 0.3
descriptoin: Commands and variables example

tasks:
- name: word_count
  description: This task will be executed as 'cat <file_path> | wc -w'
  active: False  # This will skip word_count task
  pipeline:
  - command: cat
    args: ./files/the_great_dictator_speech.txt
  - command: wc
    args: -w
  - nulldev:
    description: "nulldev at the end prevents task from writing out to artifacts/<task_name>_stdout.log"
    active: False  # You can set active at command level

- name: show_content
  description: This executes after word_count task completes. Use commands executes non-pipeline manner 'echo $TITLE && head -n 1 <file_path>'
  stdout: True
  commands:
  - command: echo
    args: $TITLE
  - command: head
    args: -n 1 {{ file_path }}

# These are set as in-memory variables in the task execution
vars:
  - key: file_path
    value: "files/the_great_dictator_speech.txt"  # Relative path to workspace directory

# These are set as environment variables in the task execution
envs:
  - key: TITLE
    value: "The Great Dictator"

```


There are a couple of new sections.
The key-value pairs in vars section are defined as in-memory variables
during the task execution. Those in envs section are defined as envrionment
variables.



### Commands vs. pipeline

In this file, there are two tasks: word_count and show_content.
The first task is the same as the previous example, but it is deactivated.

The second one has commands instead of pipeline. Instead of running the
commands as a pipeline, it runs them as independent commands just like:

```shell
echo $TITLE && head -n {{ file_path }}
```


As indicated by &&, the second command only runs if the first runs successfully,
exiting with code 0.

{{ file_path }} will be replaced by the corresponding variable defined in vars.



Now let's run. Try entering this command below. Notice that I'm using
shorthands for options:

```shell
> handoff run local -p 02_commands_and_vars -w workspace
```
```shell

Running run local in workspace directory
Job started at 2020-12-28 08:03:15.740124
[2020-12-28 08:03:15,740] [    INFO] - Running commands show_content - (operators.py:141)
Job ended at 2020-12-28 08:03:15.746955
Processed in 0:00:00.006831
```

Let's check out the contents of the second command:


```shell
> cat workspace/artifacts/show_content_stdout.log
```

```shell
The Great Dictator
I’m sorry, but I don’t want to be an emperor. That’s not my business. I don’t want to rule or conquer anyone. I should like to help everyone - if possible - Jew, Gentile - black man - white. We all want to help one another. Human beings are like that. We want to live by each other’s happiness - not by each other’s misery. We don’t want to hate and despise one another. In this world there is room for everyone. And the good earth is rich and can provide for everyone. The way of life can be free and beautiful, but we have lost the way.

```


### Secrets

We intend the files under project directory to be check in in a code
repository such as git. So we don't want to store sensitive information such
as password.

We can define them in a separate file. In the third example project, we have
.secrets/secrets/yml under the project directory. It looks like:

```shell
> cat 03_secrets/.secrets/secrets.yml
```

```shell
- key: username
  value: my_user_name
- key: password
  value: xxxxxxxxxxxxxxxxxxxxxxxxto

  # You can also refer external text file. This is handy for stuff like RSA key file:
- key: google_client_secret
  file: ./google_client_secret.json
  # You can share the secrets among the projects within the same resource group
  level: resource group

```


Let's see how we can use secrets in the project. project.yml looks like this:

```shell
> cat 03_secrets/project.yml
```

```shell
version: 0.3
descriptoin: Secrets and template example

tasks:
- name: show_curl_command
  description: Show curl command with username and password but not actually sending
  commands:
  - command: echo
    args: "curl -u {{ username }}:{{ password }} {{ url }}"

vars:
  - key: url
    value: "https://example.com"

envs:
- key: GOOGLE_APPLICATION_CREDENTIALS
  value: files/google_client_secret.json

```

You can see {{ username }} and {{ password }} in the curl command. This project
does not run curl command, but write out the command in the stdout.log file.

Now let's run.

```shell
> handoff run local -p 03_secrets -w workspace -y
```
```shell

Running run local in workspace directory
Job started at 2020-12-28 08:03:16.654891
[2020-12-28 08:03:16,654] [    INFO] - Running commands show_curl_command - (operators.py:141)
Job ended at 2020-12-28 08:03:16.658682
Processed in 0:00:00.003791
```

show_curl_command_stdout.log shows the curl command with the actual username
and password:

```shell
> cat workspace/artifacts/show_curl_command_stdout.log
```

```shell
curl -u my_user_name:xxxxxxxxxxxxxxxxxxxxxxxxto https://example.com

```


There is one more thing about this project. In files folder, you see
google_client_secret.json. This is a hypothetical RSA file for Google
Cloud Platform's
[service account](https://cloud.google.com/iam/docs/service-accounts#service_account_keys)

The original file under the project directory  does not contain the value:

```shell
> cat 03_secrets/files/google_client_secret.json
```

```shell
{{ google_client_secret }}

```


During the run, google_client_secret.json is copied to workspace/files. When that happens,
{{ google_client_secret }} is replaced with the actual values:

```shell
> cat workspace/files/google_client_secret.json
```

```shell
{
  "type": "service_account",
  "project_id": "my_project_id",
  "private_key_id": "1234567890abcdefg",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIE1234567890abcdefg\n1234567890abcdefg\n1234567890abcdefg\n1234567890abcdefg\n1234567890abcdefg\n1234567890abcdefg\n1234567890abcdefg\n1234567890abcdefg\n1234567890abcdefg\n1234567890abcdefg\n1234567890abcdefg\n1234567890abcdefg\n-----END PRIVATE KEY-----\n",
  "client_email": "service_account@my_project_id.iam.gserviceaccount.com",
  "client_id": "12345",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/bigquery-api-access%40my_project_id.iam.gserviceaccount.com"
}

```


**Important:**

The content of workspace directory is created at run-time, and you should not
submit them in the code repository because sensitive information may be
inserted.

For an obvious reason, you should not commit .secrets directory to a code
repository. The content of secrets.yml will be uploaded to a secure remote
storage when the task run in the cloud platform such as AWS Fargate. More
about this later.

We recommand adding "workspace" and ".secrets"to .gitigonore file.



In the next section, we will try pulling the currency exchange rate data.
You will also learn how to create Python virtual enviroments for each command
and install programs.

