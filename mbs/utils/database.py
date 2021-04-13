#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: database.py
# @Created: 2021-04-07 09:00:26
# @Modified: 2021-04-13 17:01:18

import sys
import sqlite3

from typing import Optional, Tuple, List

from mbs.blogs import logger
from mbs.utils.settings import DATABASE_FILE_PATH


class DataBase:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_FILE_PATH)
        self.cursor = self.conn.cursor()

        self._create_database()

    def _create_database(self):
        # 分类表
        sql = """
        CREATE TABLE IF NOT EXISTS `categories` (
            id INTEGER PRIMARY KEY NOT NULL,
            category VARCHAR NOT NULL UNIQUE,
            jianshu_id INTEGER UNIQUE,
            cnblogs_id INTEGER UNIQUE
        );
        """
        self.execute(sql)

        # 已上传文件表
        sql = """
        CREATE TABLE IF NOT EXISTS `posts` (
            id INTEGER PRIMARY KEY NOT NULL,
            title VARCHAR NOT NULL UNIQUE,
            md5 VARCHAR NOT NULL UNIQUE,
            jianshu_id INTEGER NOT NULL UNIQUE,
            cnblogs_id INTEGER NOT NULL UNIQUE,
            category_id INTEGER NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );
        """
        self.execute(sql)

        self.commit()

    def get_categories(self) -> List[str]:
        """从数据库中获取全部分类"""
        sql = "SELECT category FROM categories"
        rows = self.execute(sql).fetchall()
        return [i[0] for i in rows]

    def select_category(self, category: str) -> Optional[Tuple[int, int, int]]:
        sql = "SELECT * FROM `categories` WHERE `category` = '%s';" % category
        row = self.execute(sql).fetchone()
        if row:
            return row[0], row[2], row[3]
        return None

    def insert_category(self,
                        category: str,
                        jianshu_id: Optional[str] = None,
                        cnblogs_id: Optional[str] = None):
        sql = "INSERT INTO `categories`(`category`, `jianshu_id`, `cnblogs_id`) VALUES (?, ?, ?);"
        try:
            self.execute(sql, category, jianshu_id, cnblogs_id)
            self.commit()
        except sqlite3.IntegrityError:
            logger.warning("重复的分类：%s" % category)
            self.rollback()

    def update_category(self,
                        category: str,
                        jianshu_id: Optional[str] = None,
                        cnblogs_id: Optional[str] = None):
        if jianshu_id and not cnblogs_id:
            sql = "UPDATE `categories` SET `jianshu_id` = {%s};" % jianshu_id
        elif cnblogs_id and not jianshu_id:
            sql = "UPDATE `categories` SET `cnblogs_id` = {%s};" % cnblogs_id
        else:
            raise ValueError("更新分类时简书id和博客园id只能存在且必须存在一个值")

        self.execute(sql)
        self.commit()

    def query_category_for_post(self, title: str) -> Tuple[str, int, int]:
        sql = "SELECT c.category, c.jianshu_id, c.cnblogs_id FROM categories c WHERE c.id = (SELECT p.category_id FROM posts p WHERE p.title = '%s')" % title
        row = self.execute(sql).fetchone()
        if not row:
            logger.error(f"没找到标题为《{title}》的记录")
            sys.exit(1)
        return row

    def category_exists(self, category: str):
        return bool(self.select_category(category))

    def select_post(self, title: str) -> Tuple[int, int, int]:
        sql = "SELECT id, jianshu_id, cnblogs_id FROM posts WHERE title = '%s'" % title
        row = self.execute(sql).fetchone()
        return row

    def update_post(self, title: str, md5: str):
        sql = "UPDATE posts SET md5 = '%s' WHERE title = '%s';" % (md5, title)
        self.execute(sql)

        self.commit()  # 不 commit 就无法完成更新

    def select_md5_of_all_posts(self) -> tuple:
        sql = "SELECT * FROM posts"
        rows = self.execute(sql).fetchall()
        return rows

    def insert_post(self, title: str, md5: str, jianshu_id: int,
                    cnblogs_id: int, category_id: int):
        sql = "INSERT INTO `posts` (title, md5, jianshu_id, cnblogs_id, category_id) VALUES (?, ?, ?, ?, ?);"
        self.execute(sql, title, md5, jianshu_id, cnblogs_id, category_id)
        self.commit()

    def execute(self, sql, *args):
        return self.cursor.execute(sql, args)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

    def __del__(self):
        self.close()


if __name__ == '__main__':
    db = DataBase()
    db._create_database()
