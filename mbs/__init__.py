#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: __init__.py
# @Created: 2021-04-07 09:00:26
# @Modified: 2021-04-13 16:52:26

import sys

import argparse

from mbs.blogs import logger
from mbs.utils.common import read_post_from_file, get_md5_of_file
from mbs.manager import AllBlogsManager

__version__ = "0.0.1"


def _build_parser():
    parser = argparse.ArgumentParser(description='博客管理器',
                                     prog="mbs",
                                     add_help=False)

    parser.add_argument('-h', '--help', action='help', help='显示当前帮助信息，然后退出')
    parser.add_argument('-v',
                        '--version',
                        action='version',
                        help="显示 mbs 版本号，然后退出",
                        version=__version__)
    parser.add_argument("-cs",
                        "--categories",
                        help="显示所有分类",
                        action="store_true")
    parser.add_argument("-n",
                        "--new-post",
                        nargs=2,
                        metavar=("CATEGORY", "MARKDOWN_FILE_PATH"),
                        help="要上传的 markdown 文件的分类和路径")
    parser.add_argument("-d",
                        "--delete",
                        metavar="TITLE",
                        help="要删除的文章标题",
                        type=str)
    parser.add_argument("-sc",
                        "--scan-changed-files",
                        metavar="FOLDER",
                        help="扫描目标文件中所有有变化的文件",
                        type=str)
    parser.add_argument("-uo",
                        "--update-one",
                        metavar="PATH",
                        help="更新一个文件",
                        type=str)
    parser.add_argument("-ua",
                        "--update-all",
                        metavar="FOLDER",
                        help="更新指定目录中的所有文件",
                        type=str)
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    manager = AllBlogsManager()

    if args.categories:
        print("*" * 60)
        for i in manager.db.get_categories():
            print(i, end="\t")
        print()
        print("*" * 60)
        return 0

    if args.new_post:
        categories = manager.db.get_categories()
        category, file_path = args.new_post
        if category not in categories:
            logger.error(f"输入的分类名 `{category}` 不存在，有效的所有分类：{categories}")
            return 1
        title, content = read_post_from_file(file_path)
        md5 = get_md5_of_file(file_path)
        manager.new_post(category, title, content, md5)
        return 0

    if args.delete:
        title = args.delete
        manager.delete_post(title)
        return 0

    if args.scan_changed_files:
        manager.find_all_changed_markdown_files(args.scan_changed_files)
        return 0

    if args.update_one:
        title, content = read_post_from_file(args.update_one)
        md5 = get_md5_of_file(args.update_one)
        manager.update_post(title, content, md5)
        return 0

    if args.update_all:
        manager.update_all_posts(args.update_all)
        return 0


def run_main():
    sys.exit(main())


if __name__ == '__main__':
    run_main()
