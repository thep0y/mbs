#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: site.py
# @Created: 2021-05-13 16:40:03
# @Modified: 2021-05-24 16:28:49

import json
import os
import time
import re
import uuid
import paramiko

from typing import Optional, List

from mbs.utils.settings import CONFIG_FILE_PATH
from mbs.utils.logger import child_logger

logger = child_logger(__name__)


class Site:
    key = "site"

    def __init__(
        self,
        addr: Optional[str] = None,
        user: Optional[str] = None,
        passwd: Optional[str] = None,
        target_folder: Optional[str] = None,
    ):
        if not addr or not user or not passwd or not target_folder:
            self.__read_config_from_file()
        else:
            self.addr = addr
            self.user = user
            self.passwd = passwd
            self.target_folder = target_folder
            self.__save_config_to_local_file()

        self.connect_remote()

    def connect_remote(self):
        logger.debug(f"创建与 [ {self.addr} ] 的传输通道...")
        self.transport = paramiko.Transport((self.addr, 22))
        logger.debug(f"进行用户 [ {self.user} ] 认证，建立远程连接...")
        self.transport.connect(username=self.user, password=self.passwd)
        logger.debug("认证成功，远程连接已创建，创建 sftp 连接...")
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)

    def __read_config_from_file(self):
        try:
            with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                content = f.read()
                auth_info = json.loads(content)
                self.user = auth_info[self.key]["user"]
                self.passwd = auth_info[self.key]["passwd"]
                self.addr = auth_info[self.key]["addr"]
                self.target_folder = auth_info[self.key]["target_folder"]
        except FileNotFoundError:
            logger.error(
                "config file is not found, you should input host, user, password and target folder to create config file."
            )
            self.__input_auth_info()
        except KeyError:
            logger.error("there is not site auth info in config file, you should input them first.")
            self.__input_auth_info()

    def __input_auth_info(self):
        self.addr = input("Host: ")
        self.user = input("User: ")
        self.passwd = input("Password: ")
        self.target_folder = input("Target Folder: ")
        self.__save_config_to_local_file()

    def __save_config_to_local_file(self):
        try:
            with open(CONFIG_FILE_PATH, "r+") as f:
                all_config = json.loads(f.read())
                all_config.update({
                    self.key: {
                        "user": self.user,
                        "passwd": self.passwd,
                        "addr": self.addr,
                        "target_folder": self.target_folder,
                    }
                })
                f.seek(0, 0)
                f.write(json.dumps(all_config))
                f.truncate()
        except FileNotFoundError:
            with open(CONFIG_FILE_PATH, "w") as f:
                f.write(
                    json.dumps({
                        self.key: {
                            "user": self.user,
                            "passwd": self.passwd,
                            "addr": self.addr,
                            "target_folder": self.target_folder,
                        }
                    }))

    def new_post(self, path: str):
        logger.info("即将上传或更新 [ %s ]" % path)

        mds = self.get_all_markdown_files()

        basename = os.path.basename(path)
        remote_file_name = basename.replace(" ", "-")

        for md in mds:
            # 更新
            if md[11:] == remote_file_name:
                logger.info(f"服务器中已有文件 {md}，从服务器文件取获取 key")
                remote_file_name = md
                f = self.sftp.open(os.path.join(self.target_folder, remote_file_name))
                lines = f.readlines()
                # 更新文章时从远程文件中取 key，key 可能在第四行或第五行
                key_line = lines[3]
                logger.debug("第四行 -- " + key_line)
                if not key_line.startswith("key: "):
                    key_line = lines[4]
                    logger.debug("第五行 -- " + key_line)

                # 如果第三、四行都没有，报错
                if not key_line.startswith("key: "):
                    logger.fatal("第四、五行中没有找到 key")

                u = key_line.replace("key: ", "").replace("\n", "")

                if not re.match("[a-z0-9]{32}", u):
                    u = uuid.uuid4().hex
                    logger.info(f"旧 key 无效，已创建新 key: {u}")

                logger.debug(f"获取到的 key：{u}")
                break

        # 远程有此文件是更新，无此文件是创建，执行创建逻辑
        if not re.match(r"20\d{2}-\d{2}-\d{2}-.+?.md", remote_file_name):
            logger.info(f"正在向服务器中新建文件 {remote_file_name}")
            # Python 无法获取文件真正的创建时间
            t = os.path.getctime(path)

            date = time.strftime("%Y-%m-%d", time.localtime(t))
            remote_file_name = f"{date}-{remote_file_name}"
            logger.info(f"服务器中新建的文件名 {remote_file_name}")

            # 创建文章时，创建新的 key
            u = uuid.uuid4().hex

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            content = re.sub(r"^key: ?$", f"key: {u}", content, flags=re.MULTILINE)
            with open(f"/tmp/{remote_file_name}", "w", encoding="utf-8") as nf:
                nf.write(content)

        self.upload(f"/tmp/{remote_file_name}")
        logger.info("完成上传或更新 => %s" % path)

    def get_all_markdown_files(self) -> List[str]:
        logger.debug("开始获取 md 文件列表...")
        return self.sftp.listdir(self.target_folder)

    def upload(self, path: str):
        logger.info(f"正在向服务器中上传文件：{path}")
        self.sftp.put(path, os.path.join(self.target_folder, os.path.basename(path)))

    def __str__(self):
        return "个人网站"

    def __del__(self):
        self.transport.close()
