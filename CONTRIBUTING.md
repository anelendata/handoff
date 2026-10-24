# Contributing

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

You can contribute in many ways:

## Types of Contributions

### Report Bugs

Report bugs at https://github.com/anelendata/handoff

If you are reporting a bug, please include:

- Your operating system name and version.
- Any details about your local setup that might be helpful in troubleshooting.
- Detailed steps to reproduce the bug.

### Fix Bugs

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

### Implement Features

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

### Write Documentation

handoff.cloud could always use more documentation, whether as part of the
official dev.handoff.cloud docs, in docstrings, or even on the web in blog posts,
articles, and such.

### Submit Feedback

The best way to send feedback is to file an issue at https://github.com/anelendata/handoff/issues.

If you are proposing a feature:

- Explain in detail how it would work.
- Keep the scope as narrow as possible, to make it easier to implement.
- Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

## Submit a pull request through the GitHub website.

### Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.md.

3. The pull request should pass the `tests` GitHub Actions workflow, which runs
   `pytest tests/unit` on Python 3.9, 3.10 and 3.11.

## Deploying

A reminder for the maintainers on how to deploy.
Bump the version in both `pyproject.toml` and `handoff/config.py`, add an entry
in HISTORY.md, and commit. Then push a matching version tag:

$ git tag vX.Y.Z
$ git push origin vX.Y.Z

The `release` GitHub Actions workflow builds and install-tests the package, then
publishes it to PyPI via Trusted Publishing (the `pypi` environment). It fails
before publishing if the tag does not match both versions.
