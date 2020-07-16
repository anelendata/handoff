#!/usr/bin/env python
from setuptools import setup

setup(
    name="handoff",
    version="0.1.0",
    description="Deploy configurable unix pipeline jobs serverlessly.",
    author="Daigo Tanaka, Anelen Co., LLC",
    url="http://dev.handoff.cloud",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: Apache Software License",

        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",

        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    install_requires=[
        "attr==0.3.1",
        "boto3==1.10.0",
        "botocore==1.13.0",
        "python-dateutil==2.8.0",
        "pyyaml==5.3.1",
        "requests==2.23.0",
        "s3transfer==0.2.1",
        "setuptools>=40.3.0",
    ],
    entry_points="""
    [console_scripts]
    handoff=handoff:main
    """,
    packages=["handoff", "handoff.aws_utils", "handoff.impl"],
    package_data = {
        # Use MANIFEST.ini
    },
    include_package_data=False
)
