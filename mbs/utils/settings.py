#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: settings.py
# @Created: 2021-04-07 09:00:26
# @Modified: 2021-06-05 20:46:40

import sys
import os

from colort import display_style as ds

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    CONFIG_FOLDER = os.path.join(os.environ["APPDATA"], "mbs")
else:
    CONFIG_FOLDER = os.path.join(os.environ["HOME"], ".config", "mbs")

if not os.path.exists(CONFIG_FOLDER):
    os.mkdir(CONFIG_FOLDER, 0o755)

CONFIG_FILE_PATH = os.path.join(CONFIG_FOLDER, "config.json")
LOG_FILE_PATH = os.path.join(CONFIG_FOLDER, "mbs.log")
DATABASE_FILE_PATH = os.path.join(CONFIG_FOLDER, "blogs.db")

STATUS = [
    ds.format_with_one_style("N", ds.foreground_color.red),
    ds.format_with_one_style("Y", ds.foreground_color.green),
    ds.format_with_one_style("U", ds.foreground_color.orange),
]

NO_CODE = 0
YES_CODE = 1
UPDATED_CODE = 2
