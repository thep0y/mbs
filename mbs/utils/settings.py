#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: settings.py
# @Created: 2021-04-07 09:00:26
# @Modified: 2021-04-13 17:11:15

import sys
import os

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    CONFIG_FOLDER = os.path.join(os.environ['APPDATA'], "mbs")
else:
    CONFIG_FOLDER = os.path.join(os.environ["HOME"], ".config", "mbs")

if not os.path.exists(CONFIG_FOLDER):
    os.mkdir(CONFIG_FOLDER, 0o755)

CONFIG_FILE_PATH = os.path.join(CONFIG_FOLDER, "config.json")
DATABASE_FILE_PATH = os.path.join(CONFIG_FOLDER, "blogs.db")
