# Variables and secrets

This is a new feature of v0.3.0.

## Files with variables

Handoff now supports templated files based on
[Jinja2](https://jinja.palletsprojects.com/).

To use it, simply put files with Jinja2 templates syntax in
project.yml or the file under `<project_dir>/files` directory.

Example 1 (project.yml):
```
- command: echo
  args: "Hello {{ username }}"
```

Example 2 (files/some_config.yml):
```
username: {{ username }}
password: {{ password }}
```

One simple way to pass the variables is from the command line via -d option:

```
handoff run local -p <project_dir> -d username=my_account password="secret pwd"
```

## Secrets

Instead of passing variables as command line arguments, you can use the
secure remote parameter store such as AWS Systems Manager Parameter Store.
To do so, create `.secrets` directory under the project directory and
create `secrets.yml` file there.

```
- key: key1
  value: value1
- key: key2
  # The value can also be loaded from a text file
  file: ./file_key.txt
- key: key3
  value: value3
  # The value is stored as a resource group level secret and can be
  # shared among the projects under the same group.
  level: "resource group"
- key: key4
  file: ../../shared/file_key.txt
  level: "resource group"
  # You can mark to skip pushing to remote. Useful for resource level keys
  push: False
```

When level is "resource group", the value is stored as a resource group level
secret and can be shared among the projects under the same group.

When you run `handoff run local -p <project_dir> -w <workspace_dir>`, the
secrets are loaded from the local file.

To push the secrets to the remote parameter store, do:

```
handoff secrets push -p <project_dir> (-d secrets_dir=<directory>)
```

If you specify `<directory>`, handoff looks for secrets.yml in the directory.

After pushing to remote, you can run `handoff run -p <project_dir> -w <workspace_dir>`
so it reads from the remote parameter store.

## Reserved variables

handoff reserve the variable names starting with "_" as the system variables.

List of reserved variables:

- `{{ _stage }}`: Stage (see the next section)
- `{{ _stage_ }}`: `{{ _stage }}` + "_"
- `{{ _stage- }}`: `{{ _stage }}` + "-"

## Switching stages (prod, dev, ...)

These corresponds to stage, given as the commmand line option
(--stage <stage>, -s <stage>). The default value is "dev".

For example, when stage is "dev",

- `{{ _stage }}` translates to "dev"
- `{{ _stage_ }}` translates to "dev_"
- `{{ _stage- }}` translates to "dev-"

When stage is "prod", all three variables above becomes "" (blank).

This is useful when you are writing out in a database and use prefix "dev_"
during the developer test.

