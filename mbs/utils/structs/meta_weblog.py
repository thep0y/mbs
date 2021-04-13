#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: meta_weblog.py
# @Created: 2021-04-07 09:00:26
# @Modified: 2021-04-08 11:14:07

from mbs.utils.structs import BaseStruct


class BlogInfo(BaseStruct):
    fields = ["blogid", "url", "blogName", "username", "password"]


class Post(BaseStruct):
    fields = [
        "dateCreated", "description", "title", "categories", "enclosure",
        "link", "permalink", "postid", "source", "userid", "mt_allow_comments",
        "mt_allow_pings", "mt_convert_breaks", "mt_text_more", "mt_excerpt",
        "mt_keywords", "wp_slug"
    ]


class CategoryInfo(BaseStruct):
    fields = ["description", "htmlUrl", "rssUrl", "title", "categoryid"]


class FileData(BaseStruct):
    fields = ["bits", "name", "type"]


class UrlData(BaseStruct):
    fields = ["url"]


class WpCategory(BaseStruct):
    fields = ["name", "slug", "parent_id", "description"]


class Enclosure(BaseStruct):
    fields = ["length", "type", "url"]


class Source(BaseStruct):
    fields = ["name", "url"]
