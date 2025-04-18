#!/usr/bin/env python3

from setuptools import setup


setup(
    name="automations",
    version="0.1.0",
    description="Simulate an automation system",
    author="Franck Barbenoire",
    author_email="fbarbenoire@gmail.com",
    url="https://github.com/domotik-or/automations",
    packages=["automation"],
    package_dir={"automation": "src"},
    include_package_data=True,
    install_requires=[
        "aiohttp", "aiomqtt", "aiosmtplib", "asyncpg", "python-dotenv"
    ],
    entry_points={
        "console_scripts": ["automation=src.main:main", ]
    },
    python_requires='>=3.11',
    zip_safe=False,
    license="MIT"
)

# http://python-packaging.readthedocs.io/en/latest/command-line-scripts.html
