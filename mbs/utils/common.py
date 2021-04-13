#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: common.py
# @Created: 2021-04-07 09:00:26
# @Modified: 2021-04-13 16:30:32

import sys
import os
if sys.platform == "darwin":
    import readline
import hashlib
from typing import Tuple, List


def parse_cookies(cookies: str) -> dict:
    return {i.split("=")[0]: i.split("=")[1] for i in cookies.split("; ")}


def read_post_from_file(file_path: str) -> Tuple[str, str]:
    """从文件中读取文章内容

    Args:
        file_path (str): 文件路径

    Returns:
        Tuple[str, str]: 文章标题和内容
    """
    title = os.path.basename(file_path).replace(".md", "")
    with open(file_path, "r", encoding="utf-8") as f:
        return title, f.read()


def _remove_hidden_folders_or_files(folder_path: str) -> List[str]:
    return [i for i in os.listdir(folder_path) if not i.startswith(".")]


def _get_all_markdown_files(folder_path: str) -> List[str]:
    files = _remove_hidden_folders_or_files(folder_path)
    return [i for i in files if i.endswith(".md")]


def get_md5_of_file(file_path, buf: int = 4096) -> str:
    md5 = hashlib.md5()
    with open(file_path, "rb") as fb:
        while True:
            data = fb.read(buf)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()


def scan_folder(folder_path: str) -> dict:
    """
        以子文件夹的文件名作为分类名，
        数据库中保存博客中存在的分类，如果本地分类多于数据库中的分类，则在博客中添加多出来的分类。
        所有文件名尽量不修改，如果修改文件名，将被视为新文件直接上传，而不更新。
        扫描时对比所有文件的 md5 与数据库中对应标题的已上传文件的 md5 是否相同，
        不相同则更新文章，相同则不进行任何操作。
        如果数据库中不存在对应标题的文章，直接上传。
    """
    folders = _remove_hidden_folders_or_files(folder_path)
    all_files = {}
    for folder in folders:
        item = []
        for file in _get_all_markdown_files(os.path.join(folder_path, folder)):
            item.append({
                "file_name":
                file,
                "md5":
                get_md5_of_file(os.path.join(folder_path, folder, file)),
            })
        all_files[folder] = item
    return all_files


def find_all_files(folder: str) -> dict:
    all_files = scan_folder(folder)
    current_files = {}
    for c, fs in all_files.items():
        for f in fs:
            current_files.update(
                {f["file_name"]: {
                     "md5": f["md5"],
                     "category": c
                 }})
    return current_files


def save_categories():
    pass


if __name__ == '__main__':
    # print(
    #     get_md5_of_file(
    #         "/Volumes/MAC专用/markdown/System/浅谈select、poll和epoll.md"))
    # print(get_md5_of_file("/Volumes/MAC专用/markdown/System/分布式系统的理论发展.md"))
    cookies = input("cookies: ")
    parse_cookies(cookies)
