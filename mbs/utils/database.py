#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: database.py
# @Created: 2021-04-07 09:00:26
# @Modified: 2021-05-24 20:40:58

import sqlite3

from typing import Optional, Tuple, List

from mbs.utils.settings import DATABASE_FILE_PATH
from mbs.utils.logger import child_logger

logger = child_logger(__name__)


class DataBase:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_FILE_PATH)
        self.cursor = self.conn.cursor()

        self._create_database()

    def _create_database(self):
        # 分类表
        sql = """
        CREATE TABLE IF NOT EXISTS `categories` (
            id INTEGER PRIMARY key NOT NULL,
            category VARCHAR NOT NULL UNIQUE,
            jianshu_id INTEGER UNIQUE,
            cnblogs_id INTEGER UNIQUE,
            segment_fault_id INTEGER UNIQUE
        );
        """
        self.execute(sql)

        # 已上传文件表
        sql = """
        CREATE TABLE IF NOT EXISTS `posts` (
            id INTEGER PRIMARY key NOT NULL,
            title VARCHAR NOT NULL UNIQUE,
            md5 VARCHAR NOT NULL UNIQUE,
            jianshu_id INTEGER UNIQUE,
            cnblogs_id INTEGER UNIQUE,
            segment_fault_id INTEGER UNIQUE,
            category_id INTEGER NOT NULL,
            FOREIGN key (category_id) REFERENCES categories(id)
        );
        """
        self.execute(sql)

        # 已上传图片
        sql = """
        CREATE TABLE IF NOT EXISTS `uploaded_images` (
            id INTEGER PRIMARY key NOT NULL,
            raw_url VARCHAR NOT NULL UNIQUE,
            jianshu_url VARCHAR NOT NULL UNIQUE
        );
        """
        self.execute(sql)

        self.commit()

    def get_categories(self) -> List[str]:
        """从数据库中获取全部分类"""
        sql = "SELECT category FROM categories"
        rows = self.execute(sql).fetchall()
        return [i[0] for i in rows]

    def select_category(self, category: str) -> Optional[Tuple[int, int, int, int]]:
        sql = "SELECT * FROM `categories` WHERE `category` = '%s';" % category
        row = self.execute(sql).fetchone()
        if row:
            return row[0], row[2], row[3], row[4]
        return None

    def insert_category(self,
                        category: str,
                        jianshu_id: Optional[str] = None,
                        cnblogs_id: Optional[str] = None,
                        sf_id: Optional[str] = None):
        if not (jianshu_id or cnblogs_id or sf_id):
            raise NotImplementedError("简书、博客园和思否的分类 id， 必须至少传入其中一个")

        sql = "INSERT INTO `categories`(`category`, "

        values = f"VALUES ('{category}', "

        if jianshu_id:
            sql += "`jianshu_id`, "
            values += f"{jianshu_id}, "

        if cnblogs_id:
            sql += "`cnblogs_id`, "
            values += f"{cnblogs_id}, "

        if sf_id:
            sql += "`segment_fault_id`, "
            values += f"{sf_id}, "

        values = values[:-2] + ");"

        sql = sql[:-2] + ") " + values

        try:
            self.execute(sql)
            self.commit()
        except sqlite3.IntegrityError:
            logger.warning("重复的分类：%s" % category)
            self.rollback()

    def update_category(self,
                        category: str,
                        jianshu_id: Optional[str] = None,
                        cnblogs_id: Optional[str] = None,
                        sf_id: Optional[str] = None):
        if not (jianshu_id or cnblogs_id or sf_id):
            raise NotImplementedError("简书、博客园和思否的分类 id， 必须至少传入其中一个")

        sql = "UPDATE `categories` SET "

        if jianshu_id:
            sql += f"`jianshu_id` = {jianshu_id}, "

        if cnblogs_id:
            sql += f"`cnblogs_id` = {cnblogs_id}, "

        if sf_id:
            sql += f"`segment_fault_id` = {sf_id}, "

        sql = sql[:-2] + f" WHERE `category` = '{category}';"

        self.execute(sql)
        self.commit()

    def query_category_for_post(self, title: str) -> Tuple[str, int, int]:
        sql = "SELECT c.category, c.jianshu_id, c.cnblogs_id FROM categories c WHERE c.id = (SELECT p.category_id FROM posts p WHERE p.title = '%s')" % title
        row = self.execute(sql).fetchone()
        if not row:
            logger.fatal(f"没找到标题为《{title}》的记录")
        return row

    def category_exists(self, category: str):
        return bool(self.select_category(category))

    def select_post(self, title: str) -> Tuple[int, int, int, int]:
        sql = "SELECT id, jianshu_id, cnblogs_id, segment_fault_id FROM posts WHERE title = '%s'" % title
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

    def insert_post(
        self,
        title: str,
        md5: str,
        category_id: int,
        jianshu_id: Optional[int] = None,
        cnblogs_id: Optional[int] = None,
        sf_id: Optional[int] = None,
    ):
        # 不同博客对于分类的设计模式不同，有的博客只有一个分类（简书），有的博客只有标签（思否），
        # 所以分类 id 应该可以是一个数字，也可以是一个列表。
        # 但思否的文章会使用第一个标签作为默认分类，所以不将分类写成列表也是可以的。
        sql = "INSERT INTO `posts` (title, md5, jianshu_id, cnblogs_id, segment_fault_id, category_id) VALUES (?, ?, ?, ?, ?, ?);"
        self.execute(sql, title, md5, jianshu_id, cnblogs_id, sf_id, category_id)
        self.commit()

    def update_new_post(
        self,
        title: str,
        jianshu_id: Optional[int] = None,
        cnblogs_id: Optional[int] = None,
        sf_id: Optional[int] = None,
    ):
        if not (jianshu_id or cnblogs_id or sf_id):
            logger.fatal("至少传入一个 id")

        sql = "UPDATE `posts` SET "

        if jianshu_id:
            sql += f"`jianshu_id` = {jianshu_id}, "

        if cnblogs_id:
            sql += f"`cnblogs_id` = {cnblogs_id}, "

        if sf_id:
            sql += f"`segment_fault_id` = {sf_id}, "

        sql = sql[:-2] + f" WHERE `title` = '{title}';"

        self.execute(sql)
        self.commit()

    def uploaded(self, raw_url: str, jianshu_url: str):
        """将上传成功的图片原链接和新链接保存起来

        Args:
            raw_url (str): 原链接 / 外链
            jianshu_url (str): 简书图床中的链接
        """
        sql = "INSERT INTO `uploaded_images` VALUES (NULL, ?, ?)"
        self.execute(sql, raw_url, jianshu_url)
        self.commit()

    def is_uploaded(self, raw_url: str) -> Optional[str]:
        """图片是否上传过
        如果能在数据库中找到对应的链接，说明图片上传过，不需要再上传，直接返回之前上传的图床的链接。

        Args:
            raw_url (str): 外链

        Returns:
            Optional[str]: 简书链接或 None
        """
        sql = "SELECT `jianshu_url` FROM `uploaded_images` WHERE `raw_url` = '%s'" % raw_url
        row = self.execute(sql).fetchone()
        if not row:
            return None
        return row[0]

    def execute(self, sql: str, *args):
        if args:
            spilts = sql.split("?")
            if len(spilts) != len(args) + 1:
                logger.warning(f"传入的参数数量与 sql 语句所需的参数数量不一致，sql: {sql}, params: {args}")
            else:
                s = spilts[0]
                for i in range(len(args)):
                    t = type(args[i])
                    if t == int or t == float:
                        s += str(t)
                    elif t == str:
                        s += f"'{args[i]}'"
                    elif args[i] is None:
                        s += "NULL"
                    else:
                        raise RuntimeError(f"unkown type: {t}")
                    s += spilts[i + 1]
                logger.debug(s)
        else:
            logger.debug(sql)
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
