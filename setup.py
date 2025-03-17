#!/usr/bin/env python3

from setuptools import setup, find_packages


setup(
	name="python3-automation",
	version="0.1.0",
	description="Simulate an automation system",
	author="Franck Barbenoire",
	author_email="fbarbenoire@gmail.com",
	url="https://github.com/franckinux/python3-automation",
	packages=find_packages(),
	include_package_data=True,
	zip_safe=False,
	license="MIT"
)

# http://python-packaging.readthedocs.io/en/latest/command-line-scripts.html
