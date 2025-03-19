#!/usr/bin/env python3

from setuptools import setup


setup(
    name="python3-automation",
    version="0.1.0",
    description="Simulate an automation system",
    author="Franck Barbenoire",
    author_email="fbarbenoire@gmail.com",
    url="https://github.com/franckinux/python3-automation",
    packages=["automation"],
    package_dir={"automation": "automation"},
    include_package_data=True,
    install_requires=[
        "aiomqtt", "aiosmtplib", "dotenv-python"
    ],
    entry_points={
        "console_scripts": ["automation=automation.main:main", ]
    },
    python_requires='>=3.11',
    zip_safe=False,
    license="MIT"
)

# http://python-packaging.readthedocs.io/en/latest/command-line-scripts.html
