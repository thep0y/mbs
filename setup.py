#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: setup.py (c) 2021
# @Created:  2021-04-13 13:35:37
# @Modified: 2021-04-13 17:26:49

import codecs
import mbs

from setuptools import setup, find_packages

with codecs.open("README.md", "r", "utf-8") as fd:
    setup(
        name="mbs-cn",
        version=mbs.__version__,
        description='''
        博客管理器，可以管理多个博客的文章
        ''',
        long_description_content_type="text/markdown",
        long_description=fd.read(),
        author="thepoy",
        author_email="thepoy@163.com",
        url="https://github.com/thep0y/mbs",
        license="MIT",
        keywords="blog 博客 博客园 简书",
        packages=find_packages(),
        entry_points={
            'console_scripts': [
                'mbs = mbs:run_main',
            ],
        },
        install_requires=[
            "requests",
        ],
    )
