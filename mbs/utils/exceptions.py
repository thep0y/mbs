#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: exceptions.py
# @Created: 2021-04-07 09:00:26
# @Modified: 2021-04-13 16:24:51


class ConfigFileNotFoundError(FileNotFoundError):
    pass


class ConfigNotFoundError(KeyError):
    pass
