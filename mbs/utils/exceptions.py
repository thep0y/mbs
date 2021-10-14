#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: exceptions.py
# @Created: 2021-04-07 09:00:26
# @Modified: 2021-06-20 08:33:45


class ConfigFileNotFoundError(Exception):
    pass


class ConfigFileIsNull(Exception):
    pass


class CookiesExpiredError(Exception):
    pass
