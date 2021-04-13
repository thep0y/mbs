#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: manager.py (c) 2021
# @Created:  2021-04-13 14:57:51
# @Modified: 2021-04-13 17:10:46

import sys
import os

from typing import Union

from mbs.blogs import logger
from mbs.blogs.cnblogs import create_post, CnblogsMetaWeblog
from mbs.blogs.jianshu import Jianshu
from mbs.utils.common import find_all_files, read_post_from_file, parse_cookies
from mbs.utils.database import DataBase
from mbs.utils.exceptions import ConfigFileNotFoundError


def input_auth_info_of_cnblogs() -> CnblogsMetaWeblog:
    blog_name = input("请输入博客园的博客名：")
    username = input("请输入博客园用户名：")
    password = input("请输入博客园密码：")
    return CnblogsMetaWeblog(blog_name=blog_name,
                             username=username,
                             password=password)


class AllBlogsManager:
    """博客管理器"""
    try:
        jianshu = Jianshu()
    except ConfigFileNotFoundError:
        print("没有找到配置文件，需要输入认证信息来生成配置文件")
        cookies = input("请输入已登录的简书 cookies：")
        jianshu = Jianshu(parse_cookies(cookies))
        cnblogs = input_auth_info_of_cnblogs()
    else:
        cnblogs = CnblogsMetaWeblog()

    db = DataBase()

    def __init__(self):
        self.sync_categories()

    def get_categories(self):
        pass

    def new_category(self, category_name: str):
        # 简书能创建重名的分类，所以需要先在数据库中做本地判断
        if self.db.category_exists(category_name):
            logger.fatal("分类名 %s 已经存在了，不可重复创建相同分类名" % category_name)
            sys.exit(1)
        jianshu_category_id = self.jianshu.new_category(category_name)
        cnblogs_category_id = self.cnblogs.new_category(category_name)

        self.db.insert_category(category_name, jianshu_category_id,
                                cnblogs_category_id)
        logger.info(f"已创建新的分类：{category_name}")

    def update_category(self, category_id: Union[str, int],
                        category_name: str):
        pass

    def delete_category(self, ategory_name: str):
        # 博客园没有提供删除分类的 api
        # self.jianshu.delete_category()
        pass

    def new_post(self, category: str, title: str, content: str, md5: str):
        ids = self.db.select_category(category)
        if not ids:
            logger.fatal("没有此分类：%s" % category)
            sys.exit(1)

        logger.info("正在上传 “%s” ..." % title)

        jianshu_id = self.jianshu.new_post(ids[1], title, content)

        post = create_post(title, content, category)
        cnblogs_id = self.cnblogs.new_post(post)

        # 只向简书中添加文章
        # cnblogs_id = 14588389

        self.db.insert_post(title, md5, int(jianshu_id), int(cnblogs_id),
                            ids[0])
        logger.info("已上传 “%s.md” 到所有博客 - [%s, %s] 的 “%s” 分类中" %
                    (title, self.jianshu, self.cnblogs, category))

    def update_post(self, title: str, content: str, md5: str):
        post_id, jianshu_id, cnblogs_id = self.db.select_post(title)

        logger.info(f"正在更新《{title}》...")

        self.jianshu.update_post(jianshu_id, content)

        category = self.db.query_category_for_post(title)[0]
        post = create_post(title, content, category)
        self.cnblogs.edit_post(cnblogs_id, post)

        self.db.update_post(title, md5)

        logger.info(f"《{title}》更新完成")

    def update_all_posts(self, folder: str):
        current_files = find_all_files(folder)

        rows = self.db.select_md5_of_all_posts()
        for row in rows:
            id_, title, md5, jianshu_id, cnblogs_id, category_id = row
            try:
                if current_files[title + ".md"]["md5"] != md5:
                    file_path = os.path.join(
                        folder, current_files[title + ".md"]["category"],
                        title + ".md")
                    content = read_post_from_file(file_path)[1]
                    self.update_post(title, content,
                                     current_files[title + ".md"]["md5"])
            except KeyError:
                logger.error(f"博客中没有《{title}》，可能已被删除")

    def delete_post(self, title: str):
        post = self.db.select_post(title)
        if not post:
            logger.error("文章不存在：%s" % title)
            sys.exit(1)
        category_id, jianshu_id, cnblogs_id = post
        self.jianshu.delete_post(jianshu_id)
        self.cnblogs.delet_post(cnblogs_id)
        logger.info("标题为《%s》的文章已删除" % title)

    def sync_categories(self):
        # TODO: 改为异步或多线程
        while True:
            jcs = self.jianshu.get_categories()
            ccs = self.cnblogs.get_categories()

            jcs_set = {i["name"] for i in jcs}
            ccs_set = {i["name"] for i in ccs}

            if jcs_set - ccs_set:
                for c in (jcs_set - ccs_set):
                    self.cnblogs.new_category(c)
                logger.info(f"已向博客园添加缺失的分类：{jcs_set - ccs_set}")
            elif ccs_set - jcs_set:
                for c in (ccs_set - jcs_set):
                    self.jianshu.new_category(c)
                logger.info(f"已向简书添加缺失的分类：{ccs_set - jcs_set}")
            else:
                logger.info("已同步所有分类")
                break

        jcs = {i["name"]: i["id"] for i in jcs}
        ccs = {i["name"]: i["id"] for i in ccs}
        for k, v in jcs.items():
            self.db.insert_category(k, v, ccs[k])

    def find_all_changed_markdown_files(self, folder: str):
        current_files = find_all_files(folder)

        change_files = []
        for row in self.db.select_md5_of_all_posts():
            id_, title, md5, jianshu_id, cnblogs_id, category_id = row
            try:
                if current_files[title + ".md"]["md5"] != md5:
                    change_files.append(title)
            except KeyError:
                logger.error(f"博客中没有《{title}》，可能已被删除")
        if not change_files:
            print("所有文章都是最新状态")
            return None
        print("*" * 60)
        print("以下文章已被编辑过，需要更新：\n")
        for i in range(len(change_files)):
            print(f"{i+1}. {change_files[i]}")
        print("*" * 60)
        return change_files
