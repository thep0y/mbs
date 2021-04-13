#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: cnblogs.py
# @Created: 2021-04-07 09:00:26
# @Modified: 2021-04-13 17:03:06

import os
import sys
import json
import mimetypes
import xmlrpc.client as xml
from xmlrpc.client import Fault
from datetime import datetime

from typing import Optional, List, Union, Any

from mbs.blogs import logger
from mbs.utils.structs.meta_weblog import BlogInfo, Post, Enclosure, Source, FileData, WpCategory
from mbs.utils.exceptions import ConfigFileNotFoundError, ConfigNotFoundError
from mbs.utils.settings import CONFIG_FILE_PATH


def remove_none(data: dict):
    """去除值为 None 的元素

    Args:
        data (dict): 要去除 None 的字典
    """
    for k, v in data.copy().items():
        if not v:
            del data[k]


def create_post(title: str,
                description: str,
                category: str,
                enclosure: Optional[Enclosure] = None,
                link: Optional[str] = None,
                permalink: Optional[str] = None,
                postid: Optional[Union[str, int]] = None,
                source: Optional[Source] = None,
                userid: Optional[str] = None,
                mt_allow_comments: Optional[Any] = None,
                mt_allow_pings: Optional[Any] = None,
                mt_convert_breaks: Optional[Any] = None,
                mt_text_more: Optional[str] = None,
                mt_excerpt: Optional[str] = None,
                mt_keywords: Optional[str] = None,
                wp_slug: Optional[str] = None) -> Post:
    """创建 post 结构体/字典

    Args:
        title (str): 文章标题
        description (str): 文章内容
        category (Optional[List[str]], optional): 随笔分类
        enclosure (Optional[Enclosure], optional): 不知道什么东西
        link (Optional[str], optional): 不知道什么东西
        permalink (Optional[str], optional): 不知道什么东西
        postid (Optional[Union[str, int]], optional): 不知道什么东西
        source (Optional[Source], optional): 不知道什么东西
        userid (Optional[str], optional): 不知道什么东西
        mt_allow_comments (Optional[Any], optional): 不知道什么东西
        mt_allow_pings (Optional[Any], optional): 不知道什么东西
        mt_convert_breaks (Optional[Any], optional): 不知道什么东西
        mt_text_more (Optional[str], optional): 不知道什么东西
        mt_excerpt (Optional[str], optional): 不知道什么东西
        mt_keywords (Optional[str], optional): 不知道什么东西
        wp_slug (Optional[str], optional): 不知道什么东西

    Returns:
        Post: 文章结构体
    """

    categories = ['[Markdown]', f"[随笔分类]{category}"]
    post = {
        "dateCreated": datetime.now(),
        "description": description,
        "title": title,
        "categories": categories,
        "enclosure": enclosure,
        "link": link,
        "permalink": permalink,
        "postid": postid,
        "source": source,
        "userid": userid,
        "mt_allow_comments": mt_allow_comments,
        "mt_allow_pings": mt_allow_pings,
        "mt_convert_breaks": mt_convert_breaks,
        "mt_text_more": mt_text_more,
        "mt_excerpt": mt_excerpt,
        "mt_keywords": mt_keywords,
        "wp_slug": wp_slug,
    }

    remove_none(post)

    return Post(post)


class CnblogsMetaWeblog:
    """博客园 api"""
    def __init__(self,
                 blog_name: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None):
        """初始化函数

        Args:
            blog_name (Optional[str], optional): 博客名
            username (Optional[str], optional): 用户名
            password (Optional[str], optional): 密码
        """

        if not self._config_file_exists() and (not blog_name or not username
                                               or not password):
            raise ConfigFileNotFoundError(
                "config file not exists, you should input blogName, username, and password"
            )

        config = self._read_config()

        if not config:
            if not blog_name or not username or not password:
                raise ConfigNotFoundError(
                    "config file is empty, you should input blogName, username, and password"
                )
            else:
                self._server = xml.ServerProxy(
                    "https://rpc.cnblogs.com/metaweblog/%s" % blog_name)
                self._blogger = self._server.blogger
                self.config = BlogInfo({
                    "blogName": blog_name,
                    "username": username,
                    "password": password,
                })
                self._save_blog_config()
        else:
            self._server = xml.ServerProxy(
                "https://rpc.cnblogs.com/metaweblog/%s" % config["blogName"])
            self._blogger = self._server.blogger
            try:
                config = BlogInfo(config)
                self.config: BlogInfo = config
            except OverflowError as e:
                logger.fatal(e)
                sys.exit(1)

        self._meta_weblog = self._server.metaWeblog
        self._wp = self._server.wp

    def _get_users_blogs(self) -> Optional[dict]:
        """获取用户博客信息

        Returns:
            Optional[dict]: 博客信息
        """
        try:
            blog_info = self._blogger.getUsersBlogs(self.config.blogName,
                                                    self.config.username,
                                                    self.config.password)
        except Fault as e:
            logger.fatal(e)
            sys.exit(1)

        if len(blog_info):
            return blog_info[0]
        else:
            return None

    def _read_config(self):
        """在本地配置文件中读取配置

        Returns:
            Optional[dict]: 返回配置或 None
        """
        try:
            with open(CONFIG_FILE_PATH, "r") as f:
                return json.loads(f.read()).get("cnblogs", None)
        except FileNotFoundError:
            return None

    def _save_blog_config(self):
        """保存博客配置到本地文件"""
        config = self._get_users_blogs()
        if config:
            if self._blog_info_is_valid(config):
                self.config.update(config)
                try:
                    with open(CONFIG_FILE_PATH, "r+") as f:
                        all_config = json.loads(f.read())
                        all_config.update({"cnblogs": self.config})
                        f.seek(0, 0)
                        f.write(json.dumps(all_config))
                        f.truncate()
                except FileNotFoundError:
                    with open(CONFIG_FILE_PATH, "w") as f:
                        f.write(json.dumps({"cnblogs": self.config}))
                logger.info("save blog info to file: %s" % CONFIG_FILE_PATH)
                return
            else:
                logger.error("auth failed, response: ", config)
                sys.exit(1)
        logger.fatal("empty response")
        sys.exit(1)

    def _config_file_exists(self) -> bool:
        """配置文件是否存在

        Returns:
            bool: 是或否
        """
        return os.path.exists(CONFIG_FILE_PATH)

    def _blog_info_is_valid(self, config: dict) -> bool:
        """博客信息是否有效

        Args:
            config (dict): 配置信息

        Returns:
            bool: 是或否
        """
        return list(config.keys()) == ['blogid', 'url', 'blogName']

    def delet_post(self, postid: Union[str, int], recoverable: bool = False):
        """删除文章

        Args:
            postid (Union[str, int]): 文章 id
            recoverable (bool, optional): 是否放进回收站

        Returns:
            bool: 删除结果
        """
        if isinstance(postid, int):
            postid = str(postid)
        return self._blogger.deletePost(self.config.blogName, postid,
                                        self.config.username,
                                        self.config.password, recoverable)

    def edit_post(self,
                  postid: Union[str, int],
                  post: Post,
                  publish: bool = True):
        """编辑文章

        Args:
            postid (Union[str, int]): 文章 id
            post (Post): 编辑后的文章内容
            publish (bool, optional): 是否公开发布

        Returns:
            bool: 是否编辑成功
        """
        if isinstance(postid, int):
            postid = str(postid)
        return self._meta_weblog.editPost(postid, self.config.username,
                                          self.config.password, dict(post),
                                          publish)

    def get_categories(self) -> List[dict]:
        """获取全部分类

        Returns:
            list: 所有分类的详细信息
        """
        resp_categories = self._meta_weblog.getCategories(
            self.config.blogid, self.config.username, self.config.password)
        categories = []
        for category in resp_categories:
            if category["title"].startswith("[随笔分类]"):
                categories.append({
                    "id":
                    category["categoryid"],
                    "name":
                    category["title"].replace("[随笔分类]", ""),
                })
        return categories

    def get_post(self, postid: Union[str, int]):
        """获取文章

        Args:
            postid (Union[str, int]): 文章 id

        Returns:
            Post: 文章结构体
        """
        if isinstance(postid, int):
            postid = str(postid)
        return self._meta_weblog.getPost(postid, self.config.username,
                                         self.config.password)

    def get_recent_posts(self, count: int):
        """获取指定数量的最近发布的文章

        Args:
            count (int): 数量

        Returns:
            List[Post]: 文章列表
        """
        return self._meta_weblog.getRecentPosts(self.config.blogid,
                                                self.config.username,
                                                self.config.password, count)

    def new_media_object(self, file_path: str):
        """上传媒体文件，其实只能上传图片

        Args:
            file_path (str): 图片路径

        Returns:
            dict: 成功上传的图片的链接
        """
        with open(file_path, "rb") as fb:
            fd = {
                "bits": fb.read(),
                "name": os.path.basename(file_path),
                "type": mimetypes.guess_type(file_path)[0],
            }
        file_data = FileData(fd)
        try:
            return self._meta_weblog.newMediaObject(self.config.blogid,
                                                    self.config.username,
                                                    self.config.password,
                                                    dict(file_data))
        except Fault as e:
            logger.fatal(e)
            sys.exit(1)

    def new_post(self, post: Post) -> str:
        """发布新文章

        Args:
            post (Post): 新文章结构体

        Returns:
            str: 文章 id
        """
        return self._meta_weblog.newPost(self.config.blogid,
                                         self.config.username,
                                         self.config.password, dict(post),
                                         True)

    def new_category(self,
                     name: str,
                     parent_id: int = -4,
                     slug: Optional[str] = None,
                     description: Optional[str] = None):
        """新建分类

        Args:
            name (str): 分类名
            parent_id (int): 父分类 id
            slug (Optional[str], optional): 不知道什么东西
            description (Optional[str], optional): 分类描述

        Returns:
            bool: 是否成功创建
        """
        wp = {
            "name": name,
            "parent_id": parent_id,
            "slug": slug,
            "description": description,
        }
        remove_none(wp)
        wp = WpCategory(wp)
        return self._wp.newCategory(self.config.blogid, self.config.username,
                                    self.config.password, dict(wp))

    def __str__(self):
        return "博客园"
