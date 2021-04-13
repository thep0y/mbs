#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: jianshu.py
# @Created: 2021-04-07 09:00:26
# @Modified: 2021-04-09 12:17:15

from mbs.utils.structs import BaseStruct


class Category(BaseStruct):
    """分类信息，简书专用"""
    fields = ["id", "name"]


class NewCategory(BaseStruct):
    """分类信息，简书专用"""
    fields = ["id", "name", "seq"]


class Created(BaseStruct):
    fields = [
        'id', 'title', 'slug', 'shared', 'notebook_id', 'seq_in_nb',
        'note_type', 'autosave_control', 'content_updated_at',
        'last_compiled_at'
    ]


class Updated(BaseStruct):
    fields = [
        'id', 'content_updated_at', 'content_size_status', 'last_compiled_at'
    ]


class Published(BaseStruct):
    fields = ["last_compiled_at"]


class Deleted(BaseStruct):
    fields = ['id', 'title', 'deleted_at']


class Error(BaseStruct):
    fields = ["error"]


# error code
OVER_FLOW = 2016
