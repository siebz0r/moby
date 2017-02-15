#!/usr/bin/env python
# coding utf-8

from setuptools import setup


setup(
    author='Siebe Joris Jochems',
    author_email='siebz0r@gmail.com',
    description='Tool to automate running commands in docker.',
    entry_points={
        'console_scripts': ['moby=moby:main']
    },
    install_requires=[
        'docker',
        'pyyaml'
    ],
    keywords=['docker', 'moby'],
    name='moby',
    py_modules=['moby'],
    url='https://github.com/siebz0r/moby',
    version='0.0.3',
    zip_safe=True)
