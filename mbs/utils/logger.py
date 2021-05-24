#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: logger.py
# @Created: 2021-04-07 09:00:26
# @Modified: 2021-05-23 13:21:02

from colorful_logger import get_logger
from colorful_logger import child_logger as cl

from mbs.utils.settings import LOG_FILE_PATH

logger = get_logger(name="mbs", file_path=LOG_FILE_PATH)


def child_logger(name: str):
    return cl(name, logger)
