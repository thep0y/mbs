#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: __init__.py
# @Created: 2021-04-07 09:00:26
# @Modified: 2021-05-23 13:22:09

import json

import requests

from typing import Union, Optional, Dict

from requests import Response

from mbs.utils.settings import CONFIG_FILE_PATH
from mbs.utils.exceptions import ConfigFileNotFoundError
from mbs.utils.logger import child_logger

PostID = Union[str, int]

logger = child_logger(__name__)


class BaseBlog:
    key: Optional[str] = None
    headers = {
        "Accept": 'application/json',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:87.0) Gecko/20100101 Firefox/87.0',
    }


class LoginedBaseBlog(BaseBlog):
    key: Optional[str] = None

    def __init__(self, auth_dict: dict = None):
        if not self.key:
            raise NotImplementedError("key must be a `str`, not `None`")

        if not auth_dict:
            self.__read_config_from_file()
        else:
            self.headers.update(auth_dict)
            self.__save_config_to_local_file(auth_dict)

    def __read_config_from_file(self):
        try:
            with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                auth_dict = json.loads(f.read())[self.key]
                self.headers.update(auth_dict)
        except FileNotFoundError:
            raise ConfigFileNotFoundError(
                f"config file is not found, you should input the cookies of {self.key} to create config file.")
        except KeyError:
            logger.error(f"there is no {self.key}'s cookies in config file, you should input it first.")
            auth_dict = self._input_auth_info()
            self.__save_config_to_local_file(auth_dict)
            self.headers.update(auth_dict)

    def _input_auth_info(self) -> Dict[str, str]:
        # cookies = input("Cookies: \n")
        # self.__save_config_to_local_file(cookies)
        # self.headers.update({"cookie": cookies})
        raise Exception("需要实现这个抽象方法 >> def _input_auth_info(self) -> Dict[str, str]:")

    def __save_config_to_local_file(self, auth_dict: dict):
        try:
            with open(CONFIG_FILE_PATH, "r+") as f:
                all_config = json.loads(f.read())
                all_config.update({self.key: auth_dict})
                f.seek(0, 0)
                f.write(json.dumps(all_config))
                f.truncate()
        except FileNotFoundError:
            with open(CONFIG_FILE_PATH, "w") as f:
                f.write(json.dumps({self.key: auth_dict}))

    def _get(self, url: str, headers: Optional[dict] = None) -> Response:
        if not headers:
            headers = self.headers
        return requests.get(url, headers=headers)

    def _post(self, url: str, data: Optional[dict] = None, headers: Optional[dict] = None) -> Response:
        if not headers:
            headers = self.headers
        if data:
            return requests.post(url, headers=headers, json=data)
        else:
            return requests.post(
                url,
                headers=headers,
            )

    def _put(self, url: str, data: Optional[dict], headers: Optional[dict] = None) -> Response:
        if not headers:
            headers = self.headers

        return requests.put(url, headers=headers, json=data)

    def get_post(self, postid: Union[str, int]) -> str:
        pass

    def new_post(self, title: str, content: str, *args) -> str:
        pass

    def update_post(self, postid: Union[str, int], content: str, title: Optional[str] = None):
        pass

    def delete_post(self, postid: Union[str, int]) -> Optional[dict]:
        pass
