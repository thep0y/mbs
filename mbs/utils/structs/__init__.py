#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: __init__.py
# @Created: 2021-04-07 09:00:26
# @Modified: 2021-04-08 11:13:31

from typing import Optional, Union


class BaseStruct(dict):
    fields: Optional[Union[tuple, set, list]] = None

    def __new__(cls, *args, **kwargs):
        if not (isinstance(cls.fields, tuple) or isinstance(cls.fields, set)
                or isinstance(cls.fields, list)):
            raise AttributeError(
                "`fields` is must be instance of tuple, set, or list")
        if not set(args[0].keys()).issubset(set(cls.fields)):
            raise OverflowError(
                f"the keys of the dict object not in `fields`: {set(args[0].keys())-set(cls.fields)}"
            )
        return super().__new__(cls, *args, **kwargs)

    def __getattr__(self, item: str):
        if item not in self.fields:
            raise KeyError("the key `%s` not exists" % item)
        return self[item]

    def __setattr__(self, key, value):
        raise NotImplementedError('read only')

    def __setitem__(self, k, v):
        raise NotImplementedError('read only')
