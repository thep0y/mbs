#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: jianshu.py
# @Created: 2021-04-07 09:00:26
# @Modified: 2021-04-13 17:04:05

import sys
import json

import requests

from typing import Union, List, Optional, Tuple

from requests import Response

from mbs.blogs import logger
from mbs.utils.structs import BaseStruct
from mbs.utils.structs.jianshu import Category, NewCategory, Created, Updated, Published, Deleted, Error, OVER_FLOW
from mbs.utils.exceptions import ConfigFileNotFoundError
from mbs.utils.settings import CONFIG_FILE_PATH

Categories = List[Category]


def parse_response(struct: BaseStruct, resp: Response) -> BaseStruct:
    if resp.status_code == 200:
        return struct(resp.json())
    else:
        error = Error(resp.json())
        # TODO: 出错后，如果当前是在发布文章，则将当前文章进行标记，保存到数据库，
        # 之后再运行程序时，跳过之前被标记的发布出错的文章，以免草稿中出现太多重复文章
        if error.error[0]["code"] == OVER_FLOW:
            # TODO: 当天发布文章超过 2 篇，手动定时到明天发布。简书的定时发送是会员功能。
            pass
        logger.fatal(error.error)
        sys.exit(1)


class Jianshu:
    """简书 api"""
    headers = {
        "Accept":
        'application/json',
        'User-Agent':
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:87.0) Gecko/20100101 Firefox/87.0',
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
                self.cookies = json.loads(f.read())["jianshu"]["cookies"]
        except FileNotFoundError:
            raise ConfigFileNotFoundError(
                "config file is not found, you should input the cookies of jianshu to create config file."
            )

    def __save_config_to_local_file(self):
        try:
            with open(CONFIG_FILE_PATH, "r+") as f:
                all_config = json.loads(f.read())
                all_config.update({"jianshu": {"cookies": self.cookies}})
                f.seek(0, 0)
                f.write(json.dumps(all_config))
                f.truncate()
        except FileNotFoundError:
            with open(CONFIG_FILE_PATH, "w") as f:
                f.write(json.dumps({"jianshu": {"cookies": self.cookies}}))

    def __get(self, url: str):
        return requests.get(url, headers=self.headers, cookies=self.cookies)

    def __post(self,
               url: str,
               data: Optional[dict] = None,
               headers: Optional[dict] = None):
        if not headers:
            headers = self.headers
        if data:
            return requests.post(url,
                                 headers=headers,
                                 cookies=self.cookies,
                                 json=data)
        else:
            return requests.post(url, headers=headers, cookies=self.cookies)

    def __put(self,
              url: str,
              data: Optional[dict],
              headers: Optional[dict] = None):
        if not headers:
            headers = self.headers

        return requests.put(url,
                            headers=headers,
                            cookies=self.cookies,
                            json=data)

    def get_categories(self) -> Optional[Categories]:
        url = "https://www.jianshu.com/author/notebooks"
        resp = self.__get(url)
        if resp.status_code == 200:
            categories = []
            for i in resp.json():
                categories.append(
                    Category({
                        "id": i["id"],
                        "name": i["name"],
                    }))
            return categories
        return None

    def __create_new_post(self, notebook_id: Union[str, int],
                          title: str) -> Optional[dict]:
        url = "https://www.jianshu.com/author/notes"

        data = {
            "notebook_id": str(notebook_id),
            "title": title,
            "at_bottom": False,
        }
        resp = self.__post(url, data)
        return parse_response(Created, resp)

    def __put_post(self,
                   postid: int,
                   title: str,
                   content: str,
                   version: int = 1):
        url = "https://www.jianshu.com/author/notes/%d" % postid
        data = {
            "id": str(postid),
            "autosave_control": version,
            "title": title,
            "content": content
        }

        resp = self.__put(url, data)
        return parse_response(Updated, resp)

    def __put_new_post(self, postid: int, title: str, content: str):
        return self.__put_post(postid, title, content)

    def __publish_new_post(self, postid: int):
        url = f"https://www.jianshu.com/author/notes/{postid}/publicize"
        data = {}

        resp = self.__post(url, data)
        return parse_response(Published, resp)

    def get_post(self, postid: Union[str, int]) -> str:
        url = f"https://www.jianshu.com/author/notes/{postid}/content"
        return self.__get(url).json()["content"]

    def new_post(self, notebook_id: Union[str, int], title: str,
                 content: str) -> str:
        created = self.__create_new_post(notebook_id, title)

        self.__put_new_post(created["id"], title, content)

        self.__publish_new_post(created["id"])

        return str(created.id)

    def delete_post(self, postid: Union[str, int]) -> Optional[dict]:
        url = f"https://www.jianshu.com/author/notes/{postid}/soft_destroy"

        resp = self.__post(url)
        return parse_response(Deleted, resp)

    def update_post(self, postid: Union[str, int], content: str):
        title, version, notebook_id = self._get_info_of_post(postid)
        put_result = self.__put_post(postid, title, content, version + 1)
        if put_result["content_size_status"] != "fine":
            logger.error(f"文章更新失败：{put_result}")
            sys.exit(1)

        self.__publish_new_post(postid)

    def _get_info_of_post(self, postid: int) -> Tuple[str, int, int]:
        notebook_id = self.__select_category_for_post(postid)
        url = f"https://www.jianshu.com/author/notebooks/{notebook_id}/notes"
        resp = self.__get(url)
        for note in resp.json():
            if note["id"] == postid:
                return note["title"], note["autosave_control"], notebook_id
        logger.error(f"没有找到 postid={postid} 的文章")
        sys.exit(1)

    def __select_category_for_post(self, postid: int):
        from utils.database import DataBase
        db = DataBase()
        sql = "SELECT c.jianshu_id FROM categories as c WHERE c.id = (SELECT p.category_id FROM posts p WHERE p.jianshu_id = %d)" % postid
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
            logger.fatal(f"简书添加新分类出错：{error.error}")
            sys.exit(1)

    def update_category(self, category_id: Union[str, int],
                        category: str) -> bool:
        url = f"https://www.jianshu.com/author/notebooks/{category_id}"
        data = {"name": category}

        resp = self.__put(url, data)
        return resp.status_code == 204

    def delete_category(self, category_id: Union[str, int]) -> int:
        url = f"https://www.jianshu.com/author/notebooks/{category_id}/soft_destroy"
        return self.__post(url).status_code

    def __str__(self):
        return "简书"
