#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: segmentfault.py
# @Created: 2021-04-07 09:00:26
# @Modified: 2021-05-24 16:30:07

import asyncio

from typing import Union, Optional, Dict, List, Tuple

from mbs.blogs import LoginedBaseBlog
from mbs.utils.logger import child_logger

logger = child_logger(__name__)


class SegmentFault(LoginedBaseBlog):
    key = "segment_fault"

    def _input_auth_info(self) -> Dict[str, str]:
        cookie = input("输入思否 cookie：\n")
        token = input("输入思否 token：\n")
        return {
            "cookie": cookie,
            "token": token,
        }

    def get_post(self, postid: Union[str, int]) -> str:
        url = f"https://gateway.segmentfault.com/article?query=prepare&draft_id=&id={postid}&freshman=1"
        resp = self._get(url)

        if resp.status_code == 200:
            return resp.json()["article"]["original_text"]
        else:
            logger.error(f"状态码：{resp.status_code}，错误响应：{resp.text}")

    async def update_post(
        self,
        postid: Union[str, int],
        content: str,
        tags: List[int] = None,
        title: Optional[str] = None,
    ) -> bool:
        revisions = self._revisions(postid)
        logger.debug(f"最新版本：{revisions}")

        if not title:
            title = revisions["title"]

        if not tags:
            tags = [i["id"] for i in revisions["tags"]]
        else:
            tags = self.search_tags(tags)
            logger.debug(f"查询到的所有标签 id => {tags}")

        # TODO: 不管是创建还是更新都需要创建一个草稿，此步是否必要存疑
        draft_id = self._draft(postid, title, content, tags)

        url = f"https://gateway.segmentfault.com/article/{postid}"

        data = {
            "id": str(postid),
            "tags": tags,
            "title": title,
            "text": content,
            "draft_id": draft_id,
            "blog_id": 0,
            "type": 1,
            "url": "",
            "cover": None,
            "license": 1,
            "log": ""
        }

        logger.debug(f"即将更新文章 id={postid}")
        resp = self._put(url, data)

        if resp.status_code != 200:
            logger.error(f"状态码：{resp.status_code}，错误响应：{resp.text}")
            return False
        logger.info(f"{self}中已更新文章《{title}》")
        return bool(resp.json()["data"]["id"])

    def _revisions(self, postid: int) -> dict:
        url = f"https://gateway.segmentfault.com/revisions?object_id={postid}"
        logger.debug(f"生成版本查询链接 {url}，即将访问此链接")
        resp = self._get(url)

        if resp.status_code == 200:
            # 返回的是一个根据创建时间倒序排列的列表，第一个是最新版本
            return resp.json()[0]
        else:
            logger.error(f"状态码：{resp.status_code}，错误响应：{resp.text}")

    def _draft(self, postid, title, content, tags: List[int]) -> int:
        """生成草稿

        Args:
            postid (TYPE): Description
            title (TYPE): Description
            content (TYPE): Description
            tags (List[int]): Description

        Returns:
            int: Description
        """
        url = "https://gateway.segmentfault.com/draft"
        data = {"title": title, "tags": tags, "text": content, "object_id": postid, "type": "article", "cover": None}

        logger.debug("正在创建草稿")
        resp = self._post(url, data)
        if resp.status_code == 200 or resp.status_code == 201:
            logger.debug(f"已创建草稿，草稿 id = {resp.json()['id']}")
            return resp.json()["id"]
        else:
            logger.error(f"状态码：{resp.status_code}，错误响应：{resp.text}")

    async def search_tag(self, tag: str) -> int:
        url = f"https://gateway.segmentfault.com/tags?query=search&q={tag}"
        logger.debug(f"正在查询 tag [ {tag} ]")
        resp = self._get(url)
        if resp.status_code == 200:
            result = resp.json()["rows"]
            sf_id = result[0]["id"] if result else 0

            if sf_id:
                from mbs.utils.database import DataBase

                db = DataBase()
                if db.category_exists(tag):
                    logger.debug(f"数据库中已有此分类 {tag}，更新 `segment_fault_id` 字段为 [ {sf_id} ]")
                    db.update_category(tag, sf_id=sf_id)
                else:
                    logger.debug(f"在数据库中创建分类 {tag} => `segment_fault_id` =  {sf_id}")
                    db.insert_category(tag, sf_id=sf_id)

            return sf_id
        else:
            logger.error(f"状态码：{resp.status_code}，错误响应：{resp.text}")

    async def search_tags(self, tags: List[str]) -> List[int]:
        logger.debug(f"正在查询多个标签 {tags}")
        tasks = [asyncio.create_task(self.search_tag(tag)) for tag in tags]

        result = await asyncio.gather(*tasks)

        return [i for i in result if type(i) == int]

    async def new_post(self, title: str, content: str, tags: List[int], db) -> Tuple[str, int]:
        # TODO: 未测试是否必须创建先草稿
        draft_id = self._draft("", title, content, tags)

        url = "https://gateway.segmentfault.com/article"
        data = {
            "blog_id": "0",
            "cover": "",
            "draft_id": draft_id,
            "license": 1,
            "log": "",
            "tags": tags,
            "text": content,
            "title": title,
            "type": 1,
            "url": "",
        }

        logger.debug(f"正在上传新文章：{title}")
        resp = self._post(url, data)
        if resp.status_code == 201:

            logger.info(f"新文章《{title}》已上传到 {self}")

            id_ = resp.json()["data"]["id"]
            db.update_new_post(title, sf_id=id_)

            return self.key, id_
        else:
            resp.encoding = "utf-8"
            logger.error(f"状态码：{resp.status_code}，错误响应：{resp.text}")
            return self.key, None

    def parse_tags_from_yaml_header(self, content: str) -> List[str]:
        import re

        re_tags = re.search(r"tags: \[(.+?)\]", content).group(1)
        tags = [i for i in re_tags.split(", ")]
        logger.debug(f"正则表达式提取出来的标签为：{tags}")
        return tags

    def __str__(self):
        return "思否"
