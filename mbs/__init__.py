#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: __init__.py
# @Created: 2021-04-07 09:00:26
# @Modified: 2021-10-13 09:39:36

import json
import sys
import asyncio
import argparse
from typing import Any, Dict

from colort import display_style as ds

from mbs.utils.common import read_post_from_file, get_md5_of_file
from mbs.manager import AllBlogsManager
from mbs.utils.logger import logger, child_logger
from mbs.utils.settings import CONFIG_FILE_PATH, STATUS

main_logger = child_logger(__name__)

__version__ = "0.0.7"


def _merge_scan_result(not_uploaded_posts, changed_files):
    files = []

    if changed_files:
        for f in changed_files:
            exists = False
            for p in not_uploaded_posts:
                if f[0] == p[0]:
                    file = (f[0], f[1] * p[1], f[2] * p[2], f[3] * p[3], f[4])
                    not_uploaded_posts.remove(p)
                    files.append(file)
                    exists = True
                    break
            if not exists:
                files.append(f)

    files.extend(not_uploaded_posts)
    return files


def _build_parser():
    parser = argparse.ArgumentParser(description="博客管理器", prog="mbs", add_help=False)

    parser.add_argument("-h", "--help", action="help", help="显示当前帮助信息，然后退出")
    parser.add_argument("-v", "--version", action="version", help="显示 mbs 版本号，然后退出", version=__version__)
    parser.add_argument("-cs", "--categories", help="显示所有分类", action="store_true")
    parser.add_argument(
        "-n", "--new-post", nargs=2, metavar=("CATEGORY", "MARKDOWN_FILE_PATH"), help="要上传的 markdown 文件的分类和路径"
    )
    parser.add_argument("-d", "--delete", metavar="TITLE", help="要删除的文章标题", type=str)
    parser.add_argument("-sc", "--scan-updated-files", help="扫描所有需要更新的文档", action="store_true")
    parser.add_argument("-uo", "--update-one", metavar="PATH", help="更新一个文件", type=str)
    parser.add_argument("-ua", "--update-all", help="更新指定目录中的所有文件", action="store_true")
    parser.add_argument("--update-jianshu-cookies", help="更新简书 cookies", action="store_true")
    return parser


def print_updated_result(files):
    print()
    print(f"文章三种状态：{STATUS[1]} - 最新版，{STATUS[0]} - 未上传，{STATUS[2]} - 待更新")

    length = len(files)

    no_len = len(f"{length}/{length} ")
    if no_len < 6:
        no_len = 6

    def string_length(s):
        rl = 0
        for c in s:
            # 处理中文字符和全角符号的宽度
            if "\u4e00" <= c <= "\u9fff" or "\uff00" <= c <= "\uffef" or "\u3000" <= c <= "\u303f":
                rl += 1
        return len(s) + rl

    title_width = max([string_length(i[0]) for i in files])
    path_width = max([string_length(i[4]) for i in files])

    print(f'┌{"─" * 6}┬{"─"*title_width}┬{"─"*6}┬{"─"*8}┬{"─"*6}┬{"─"*(path_width)}┐')

    def format_title(title):
        return ds.format_with_multiple_styles(title, ds.foreground_color.blue, ds.mode.bold)

    title = format_title("标题")
    jianshu = format_title("简书")
    cnblogs = format_title("博客园")
    sf = format_title("思否")
    path = format_title("本地路径")

    title_space_length = title_width - 4
    title_left_space = int(title_space_length / 2) * " "
    title_right_space = (title_space_length - int(title_space_length / 2)) * " "

    path_space_length = path_width - 8
    path_left_space = int(path_space_length / 2) * " "
    path_right_space = (path_space_length - int(path_space_length / 2)) * " "

    print(
        f"│{' '*no_len}│{title_left_space}{title}{title_right_space}│ {jianshu} │ {cnblogs} │ {sf}"
        f" │{path_left_space}{path}{path_right_space}│"
    )
    print(f"├{'─'*(no_len)}┼{'─'*(title_width)}┼{'─'*6}┼{'─'*8}┼{'─'*6}┼{'─'*path_width}┤")

    for i in range(length):
        if i > 0:
            print(f"├{'─'*(no_len)}┼{'─'*(title_width)}┼{'─'*6}┼{'─'*8}┼{'─'*6}┼{'─'*path_width}┤")
        no = f"{i+1}/{length} "
        no = no + (no_len - len(no)) * " "

        item_title = ds.format_with_one_style(files[i][0], ds.foreground_color.cyan)
        item_title_space = (title_width - string_length(files[i][0])) * " "
        item_jianshu_status = STATUS[files[i][1]]
        item_cnblogs_status = STATUS[files[i][2]]
        item_sf_status = STATUS[files[i][3]]
        item_path_space = (path_width - string_length(files[i][4])) * " "

        print(
            f"│{no}│{item_title}{item_title_space}│  {item_jianshu_status}   │   {item_cnblogs_status}    │ "
            f" {item_sf_status}   │{files[i][4]}{item_path_space}│"
        )

    print(f'└{"─" * 6}┴{"─"*title_width}┴{"─"*6}┴{"─"*8}┴{"─"*6}┴{"─"*(path_width)}┘')


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    with logger:
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
                main_logger.error(f"输入的分类名 `{category}` 不存在，有效的所有分类：{categories}")
                return 1
            title, content = read_post_from_file(file_path)

            md5 = get_md5_of_file(file_path)

            asyncio.run(manager.new_post(category, title, content, md5, file_path))

            # site = Site()
            # site.new_post(file_path)

            return 0

        if args.delete:
            title = args.delete
            manager.delete_post(title)
            return 0

        if args.scan_updated_files:
            # 未上传的文章
            not_uploaded_posts = manager.find_all_not_uploaded_posts()
            if not not_uploaded_posts:
                main_logger.debug("没有上传失败的文章")

            # 待更新的文章
            changed_files = manager.find_all_changed_markdown_files()
            if not changed_files:
                main_logger.debug("没有已修改的文章")

            if not changed_files and not not_uploaded_posts:
                print(f'┌{"─"*24}┐')
                print(ds.format_with_one_style("│  所有文章都已是最新版  │", ds.foreground_color.green))
                print(f'└{"─"*24}┘')
                return 0

            files = _merge_scan_result(not_uploaded_posts, changed_files)

            print_updated_result(files)

            return 0

        if args.update_one:
            # TODO: 更新一篇文章，如果某网站没有上传，先上传此网站，再更新其他网站
            title, content = read_post_from_file(args.update_one)
            md5 = get_md5_of_file(args.update_one)
            asyncio.run(manager.update_post(title, content, md5))

            # site = Site()
            # site.new_post(args.update_one)

            return 0

        if args.update_all:
            changed_files = asyncio.run(manager.update_all_posts())

            # if changed_files:
            #     site = Site()
            #     for path in changed_files:
            #         site.new_post(path)

            return 0

        if args.update_jianshu_cookies:
            cookies = input("请输入 cookies:")

            cookies = {i.split("=")[0]: i.split("=")[1] for i in cookies.split("; ")}

            with open(CONFIG_FILE_PATH, "r+") as f:
                all_config: Dict[str, Any] = json.loads(f.read())
                all_config["jianshu"]["cookies"] = cookies
                f.seek(0, 0)
                f.write(json.dumps(all_config))
                f.truncate()

        return 1


def run_main():
    sys.exit(main())


if __name__ == "__main__":
    run_main()
