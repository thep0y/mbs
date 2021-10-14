#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: __init__.py
# @Created: 2021-04-07 09:00:26
# @Modified: 2021-07-05 08:10:49

from abc import ABCMeta, abstractstaticmethod
from typing import List, Optional, Tuple, Any


class Database(metaclass=ABCMeta):
    @abstractstaticmethod
    def _create_database(self):
        """创建表"""
        pass

    @abstractstaticmethod
    def get_categories(self) -> List[str]:
        """获取全部分类"""
        pass

    @abstractstaticmethod
    def select_category(self, category: str) -> Optional[Tuple[int, int, int, int]]:
        pass

    @abstractstaticmethod
    def select_category_by_title(self, title: str, jianshu=0, cnblogs=0, sf=0) -> Optional[str]:
        pass

    @abstractstaticmethod
    def insert_category(
        self,
        category: str,
        jianshu_id: Optional[int] = None,
        cnblogs_id: Optional[int] = None,
        sf_id: Optional[str] = None,
    ):
        pass

    @abstractstaticmethod
    def update_category(
        self,
        category: str,
        jianshu_id: Optional[str] = None,
        cnblogs_id: Optional[str] = None,
        sf_id: Optional[str] = None,
    ):
        pass

    @abstractstaticmethod
    def query_category_for_post(self, title: str) -> Tuple[str, int, int]:
        pass

    @abstractstaticmethod
    def category_exists(self, category: str):
        pass

    @abstractstaticmethod
    def select_post(self, title: str) -> Tuple[int, int, int, int]:
        pass

    @abstractstaticmethod
    def update_post(self, title: str, md5: str):
        pass

    @abstractstaticmethod
    def select_all_not_uploaded_posts(self):
        pass

    @abstractstaticmethod
    def select_md5_of_all_posts(self) -> List[Any]:
        pass

    @abstractstaticmethod
    def insert_post(
        self,
        title: str,
        md5: str,
        category_id: int,
        file_path: Optional[str] = None,
        jianshu_id: Optional[int] = None,
        cnblogs_id: Optional[int] = None,
        sf_id: Optional[int] = None,
    ):
        pass

    @abstractstaticmethod
    def update_new_post(
        self,
        title: str,
        jianshu_id: Optional[int] = None,
        cnblogs_id: Optional[int] = None,
        sf_id: Optional[int] = None,
    ):
        pass

    @abstractstaticmethod
    def uploaded(self, raw_url: str, jianshu_url: str):
        pass

    @abstractstaticmethod
    def is_uploaded(self, raw_url: str) -> Optional[str]:
        pass

    @abstractstaticmethod
    def execute(self, sql: str, *args):
        pass

    @abstractstaticmethod
    def commit(self):
        pass

    @abstractstaticmethod
    def rollback(self):
        pass

    @abstractstaticmethod
    def close(self):
        pass
