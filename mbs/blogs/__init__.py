#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: __init__.py
# @Created: 2021-04-07 09:00:26
# @Modified: 2021-04-13 17:10:57

import os
import logging

from typing import Union

from mbs.utils.settings import CONFIG_FOLDER

PostID = Union[str, int]

debug = int(os.getenv("MBS_DEBUG")) if os.getenv("MBS_DEBUG") else 0


def _console_handler(logger, fmt):
    # 输出到终端
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)


logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 输出到文件
file_handler = logging.FileHandler(
    filename=os.path.join(CONFIG_FOLDER, "mbs.log"),
    mode="w",
    encoding="utf-8",
)
file_handler.setLevel(logging.NOTSET)

# 设置格式
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
fmt = logging.Formatter(LOG_FORMAT)
file_handler.setFormatter(fmt)

# 整合到 logger 里
logger.addHandler(file_handler)

if debug:
    _console_handler(logger, fmt)
