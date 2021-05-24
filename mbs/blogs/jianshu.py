#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: jianshu.py
# @Created: 2021-04-07 09:00:26
# @Modified: 2021-05-24 16:30:26

import os
import json
import asyncio
import requests

from typing import Union, List, Optional, Tuple

from requests import Response

from mbs.utils.structs import BaseStruct
from mbs.utils.structs.jianshu import Category, NewCategory, Created, Updated, Published, Deleted, Error, OVER_FLOW

from mbs.utils.settings import CONFIG_FILE_PATH
from mbs.utils.logger import child_logger

Categories = List[Category]

logger = child_logger(__name__)


def parse_response(struct: BaseStruct, resp: Response) -> BaseStruct:
    """解析响应

    Args:
        struct (BaseStruct): 响应对应的结构体
        resp (Response): 响应

    Returns:
        BaseStruct: 解析过的结构体
    """
    if resp.status_code == 200:
        return struct(resp.json())
    else:
        error = Error(resp.json())
        # TODO: 出错后，如果当前是在发布文章，则将当前文章进行标记，保存到数据库，
        # 之后再运行程序时，跳过之前被标记的发布出错的文章，以免草稿中出现太多重复文章
        if error.error[0]["code"] == OVER_FLOW:
            # TODO: 当天发布文章超过 2 篇，手动定时到明天发布。简书的定时发送是会员功能。
            pass
        logger.error(f"简书上传或更新文章失败：{error.error}，不再重试，跳过简书")


class Jianshu:
    """简书 api"""
    key = "jianshu"
    headers = {
        "Accept": 'application/json',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:87.0) Gecko/20100101 Firefox/87.0',
    }

    def __init__(self, cookies: Optional[dict] = None):
        if not cookies:
            self.__read_config_from_file()
        else:
            self.cookies = cookies
            self.__save_config_to_local_file()

    def __read_config_from_file(self):
        try:
            with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                self.cookies = json.loads(f.read())[self.key]["cookies"]
            return 0
        except FileNotFoundError:
            logger.error("config file is not found, you should input the cookies of jianshu to create config file.")
            return 1

    def __save_config_to_local_file(self):
        try:
            with open(CONFIG_FILE_PATH, "r+") as f:
                all_config = json.loads(f.read())
                all_config.update({self.key: {"cookies": self.cookies}})
                f.seek(0, 0)
                f.write(json.dumps(all_config))
                f.truncate()
        except FileNotFoundError:
            with open(CONFIG_FILE_PATH, "w") as f:
                f.write(json.dumps({self.key: {"cookies": self.cookies}}))

    def __get(self, url: str, headers: Optional[dict] = None) -> Response:
        if not headers:
            headers = self.headers
        return requests.get(url, headers=headers, cookies=self.cookies)

    def __post(self, url: str, data: Optional[dict] = None, headers: Optional[dict] = None) -> Response:
        if not headers:
            headers = self.headers
        if data:
            return requests.post(url, headers=headers, cookies=self.cookies, json=data)
        else:
            return requests.post(url, headers=headers, cookies=self.cookies)

    def __put(self, url: str, data: Optional[dict], headers: Optional[dict] = None) -> Response:
        if not headers:
            headers = self.headers

        return requests.put(url, headers=headers, cookies=self.cookies, json=data)

    def get_categories(self) -> Optional[Categories]:
        url = "https://www.jianshu.com/author/notebooks"
        resp = self.__get(url)
        if resp.status_code == 200:
            categories = []
            for i in resp.json():
                categories.append(Category({
                    "id": i["id"],
                    "name": i["name"],
                }))
            return categories
        logger.error("cookie 已过期：", resp.json())

    def __create_new_post(self, notebook_id: Union[str, int], title: str) -> Optional[dict]:
        url = "https://www.jianshu.com/author/notes"

        data = {
            "notebook_id": str(notebook_id),
            "title": title,
            "at_bottom": False,
        }
        logger.debug(f"正在向文集 [ {notebook_id} ] 中创建新文章：{title}")
        resp = self.__post(url, data)
        return parse_response(Created, resp)

    async def __put_post(self, postid: int, title: str, content: str, version: int = 1):
        url = "https://www.jianshu.com/author/notes/%d" % postid

        # 将 content 中所有的图片上传到简书，用简书反回的图片链接进行替换
        content = await self._replace_all_images(content)

        data = {"id": str(postid), "autosave_control": version, "title": title, "content": content}

        resp = self.__put(url, data)
        return parse_response(Updated, resp)

    def __put_new_post(self, postid: int, title: str, content: str):
        logger.debug(f"正在上传新文章的内容：{title}")
        return self.__put_post(postid, title, content)

    async def __publish_new_post(self, postid: int):
        url = f"https://www.jianshu.com/author/notes/{postid}/publicize"
        data = {}

        logger.info(f"正在发布文章 => {url}")
        resp = self.__post(url, data)
        logger.info(f"文章 {url} 已发布")
        return parse_response(Published, resp)

    def get_post(self, postid: Union[str, int]) -> str:
        url = f"https://www.jianshu.com/author/notes/{postid}/content"
        return self.__get(url).json()["content"]

    async def new_post(self, notebook_id: Union[str, int], title: str, content: str, db) -> Tuple[str, int]:
        created = self.__create_new_post(notebook_id, title)
        if not created:
            logger.error("上传失败")
            return self.key, None
        logger.debug(f"新文章《{title}》已创建")

        updated = await self.__put_new_post(created["id"], title, content)
        if not updated:
            logger.error("上传失败")
            return self.key, None
        logger.debug(f"已上传新文章的内容：{title}")

        published = await self.__publish_new_post(created["id"])
        if not published:
            return self.key, None

        logger.info(f"新文章《{title}》已上传到 {self}")

        db.update_new_post(title, jianshu_id=created.id)

        return self.key, created.id

    def delete_post(self, postid: Union[str, int]) -> Optional[dict]:
        url = f"https://www.jianshu.com/author/notes/{postid}/soft_destroy"

        resp = self.__post(url)
        return parse_response(Deleted, resp)

    async def update_post(self, postid: Union[str, int], content: str):
        # 奇葩简书不能更新太频繁，每次更新前休眠 2 秒
        await asyncio.sleep(2)

        title, version, notebook_id = await self._get_info_of_post(postid)
        logger.debug(f"原文章信息：id={postid}，title={title}，version={version}")
        logger.info("正在更新文章")
        put_result = await self.__put_post(postid, title, content, version + 1)
        if put_result["content_size_status"] != "fine":
            logger.error(f"文章更新失败：{put_result}")
            return
        logger.debug("更新的文章已保存到草稿箱，待发布")
        await self.__publish_new_post(postid)
        logger.info(f"{self}中已更新文章《{title}》")

    async def _get_info_of_post(self, postid: int) -> Tuple[str, int, int]:
        notebook_id = self.__select_category_for_post(postid)
        url = f"https://www.jianshu.com/author/notebooks/{notebook_id}/notes"
        logger.debug(f"正在访问 {url}")
        resp = self.__get(url)
        for note in resp.json():
            if note["id"] == postid:
                return note["title"], note["autosave_control"], notebook_id
        logger.error(f"没有找到 postid={postid} 的文章")

    def __select_category_for_post(self, postid: int):
        from mbs.utils.database import DataBase
        db = DataBase()
        sql = "SELECT c.jianshu_id FROM categories as c WHERE c.id = (SELECT p.category_id FROM posts p WHERE p.jianshu_id = %d)" % postid
        logger.debug(sql)
        row = db.execute(sql).fetchone()
        if not row:
            return 0
        return row[0]

    def new_category(self, category: str) -> int:
        url = "https://www.jianshu.com/author/notebooks"
        data = {"name": category}

        resp = self.__post(url, data)
        if resp.status_code == 200:
            result = NewCategory(resp.json())
            return result.id
        else:
            error = Error(resp.json())
            logger.error(f"简书添加新分类出错：{error.error}")

    def update_category(self, category_id: Union[str, int], category: str) -> bool:
        url = f"https://www.jianshu.com/author/notebooks/{category_id}"
        data = {"name": category}

        resp = self.__put(url, data)
        return resp.status_code == 204

    def delete_category(self, category_id: Union[str, int]) -> int:
        url = f"https://www.jianshu.com/author/notebooks/{category_id}/soft_destroy"
        return self.__post(url).status_code

    async def _replace_all_images(self, content: str) -> str:
        import re
        from mbs.utils.database import DataBase

        db = DataBase()

        imgs = re.findall(r"!\[.+?\]\((.+?)\)", content)

        imgs = list(set(imgs))

        amount = len(imgs)

        new_imgs = []
        tasks = []

        for i in range(amount):
            new_img = db.is_uploaded(imgs[i])
            if new_img:
                logger.info(f"外链图片 {imgs[i]} 已向简书上传过 => {new_img}")
                new_imgs.append((imgs[i], new_img))
            else:
                tasks.append(self.upload_image(imgs[i], db))

        if tasks:
            logger.info("正在向简书上传文档内未上传过的图片...")
            uploaded_imgs = await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("已上传所有图片")
            new_imgs.extend(uploaded_imgs)

        if new_imgs:
            new_imgs = set(new_imgs)
            for img in imgs:
                for new_img in new_imgs:
                    if new_img[0] == img:
                        content = content.replace(img,
                                                  new_img[1] + "?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240")
                        new_imgs.remove(new_img)
                        break

        return content

    def __get_token_and_key_of_local_image(self, filename: str) -> Tuple[str, str]:
        logger.debug("正在向简书请求上传图片的认证 token")
        url = f"https://www.jianshu.com/upload_images/token.json?filename={filename}"
        headers = self.headers.copy()
        headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        resp = self.__get(url, headers=headers)
        return resp.json()["token"], resp.json()["key"]

    async def upload_image(self, path_or_url: str, db) -> Tuple[str, str]:
        if path_or_url.startswith("http"):
            logger.info(f"正在上传远程图片 {path_or_url}")
            url = "https://www.jianshu.com/upload_images/fetch"
            resp = self.__post(url, data={"url": path_or_url})
        else:
            if not os.path.exists(path_or_url):
                logger.error(f"没有找到文件 {path_or_url}")
                return

            logger.info(f"正在上传本地图片 {path_or_url}")

            filename = os.path.basename(path_or_url).replace(" ", "_")

            token, key = self.__get_token_and_key_of_local_image(filename)

            # 根据 token 和 key 上传图片
            url = "https://upload.qiniup.com/"
            params = {
                "token": (None, token),
                "key": (None, key),
                "file": (filename, open(path_or_url, "rb")),
                "x:protocol": "https"
            }
            resp = requests.post(url, files=params)
        try:
            if "url" in resp.json():
                logger.info("图片上传成功，本地或远程地址：%s，上传到简书后返回的地址：%s", path_or_url, resp.json()["url"])
                db.uploaded(path_or_url, resp.json()["url"])
                logger.info("已将上传的图片链接保存到数据库")
            return (path_or_url, resp.json()["url"])
        except KeyError:
            logger.error("上传图片时出错：%s", ", ".join([e["message"] for e in resp.json()["error"]]))

    def __str__(self):
        return "简书"
