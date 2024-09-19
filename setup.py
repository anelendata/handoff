#!/usr/bin/env python
from setuptools import setup

VERSION = "0.4.1"

with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name="handoff",
    version=VERSION,
    description="Deploy configurable unix pipeline jobs serverlessly.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Daigo Tanaka, Anelen Co., LLC",
    url="http://dev.handoff.cloud",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Apache Software License",

        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",

        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    install_requires=[
        "attrs>=17.4.0",
        "boto3>=1.10.0",
        "botocore>=1.13.0",
        "python-dateutil>=2.7.0",
        "docker==7.1.0",
        "lxml>=4.2.0",
        "Jinja2>=2.10.1",
        "jsonschema>=3.2.0",
        "packaging>=19.2",
        "psutil>=6.0.0",
        "pygit2==1.13.0",
        "PyGithub==1.59.1",
        "python-dateutil>=2.8.0",
        "pyyaml>=5.4",
        "requests>=2.19.0",
        "s3transfer>=0.2.0",
    ],
    entry_points="""
    [console_scripts]
    handoff=handoff:main
    """,
    packages=["handoff"],
    package_data={
        # Use MANIFEST.ini
    },
    include_package_data=True
)
