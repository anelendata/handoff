# Managing secrets with template files

This is a new feature of v0.3.0.

## Templated files

Handoff now supports templated files based on
[Jinja2](https://jinja.palletsprojects.com/).

To use it, simply put files with Jinja2 templates syntax in
project.yml or `<project_dir>/files` directory.

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
handoff run local -p <project_dir> -d username=my_account password="secret pw"
```

## Secrets

Instead of passing variables as command line arguments, you can use the
secure remote parameter store such as AWS Systems Manager Parameter Store.
To do so, create `.secrets` directory under the project directory and
create `secrets.yml` file there.

```
<key_name>:
    value: <value>
    level: "task"  # "task" or "resource group", assumed to be task when absent.
```

When level is "resource group", the value is stored as a resource group level
secret and can be shared among the projects under the same group.
