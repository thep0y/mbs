#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: manager.py
# @Created:  2021-04-13 14:57:51
# @Modified: 2021-10-14 11:17:39

import sys
import time
import asyncio

from typing import Union, List

from mbs.blogs.cnblogs import create_post, CnblogsMetaWeblog
from mbs.blogs.jianshu import Jianshu
from mbs.blogs.segmentfault import SegmentFault
from mbs.utils.common import read_post_from_file, parse_cookies, remove_yaml_header, get_md5_of_file
from mbs.utils.database.sqlite import DataBase
from mbs.utils.exceptions import ConfigFileNotFoundError, CookiesExpiredError, ConfigFileIsNull
from mbs.utils.logger import child_logger
from mbs.utils.settings import YES_CODE, NO_CODE, UPDATED_CODE

logger = child_logger(__name__)


def input_auth_info_of_cnblogs() -> CnblogsMetaWeblog:
    blog_name = input("请输入博客园的博客名：")
    username = input("请输入博客园用户名：")
    password = input("请输入博客园密码：")
    return CnblogsMetaWeblog(blog_name=blog_name, username=username, password=password)


class AllBlogsManager:
    """博客管理器"""

    def __init__(self):
        try:
            self.jianshu = Jianshu()
        except (ConfigFileNotFoundError, ConfigFileIsNull, FileNotFoundError):
            print("没有找到配置文件，需要输入认证信息来生成配置文件")
            cookies = input("请输入已登录的简书 cookies：")
            self.jianshu = Jianshu(parse_cookies(cookies))

            self.cnblogs = input_auth_info_of_cnblogs()

            # TODO: token 好像就是 cookie 中的  PHPSESSIONID
            cookies = input("请输入思否的 cookies:")
            token = input("请输入思否的 token:")
            self.sf = SegmentFault({"cookie": cookies, "token": token})
        else:
            self.cnblogs = CnblogsMetaWeblog()
            self.sf = SegmentFault()

        self.db = DataBase()

        try:
            self.sync_categories()
        except CookiesExpiredError:
            cookies = input("简书 cookies 过期，请重新在浏览器中登录简书，并将请求头中的新的 Cookies 填写到下面：\n")
            self.jianshu = Jianshu(parse_cookies(cookies))

    def get_categories(self):
        pass

    def new_category(self, category_name: str):
        # 简书能创建重名的分类，所以需要先在数据库中做本地判断
        if self.db.category_exists(category_name):
            logger.fatal("分类名 %s 已经存在了，不可重复创建相同分类名" % category_name)
            sys.exit(1)
        jianshu_category_id = self.jianshu.new_category(category_name)
        cnblogs_category_id = self.cnblogs.new_category(category_name)

        assert type(cnblogs_category_id) == int

        self.db.insert_category(category_name, jianshu_category_id, cnblogs_category_id)  # type: ignore
        logger.info(f"已创建新的分类：{category_name}")

    def update_category(self, category_id: Union[str, int], category_name: str):
        pass

    def delete_category(self, ategory_name: str):
        # 博客园没有提供删除分类的 api
        # self.jianshu.delete_category()
        pass

    async def new_post(self, category: str, title: str, content: str, md5: str, file_path: str):
        post_record = self.db.select_post(title)
        if post_record:
            logger.warning(f"之前上传过此文章，文章的记录已存在 {post_record}")
            _, jianshu_id, cnblogs_id, segment_fault_id = post_record
            if jianshu_id and cnblogs_id and segment_fault_id:
                logger.fatal("所有博客中均有此文章，不能再上传，可以更新此文章")

        ids = self.db.select_category(category)
        if not ids:
            logger.fatal("没有此分类：%s" % category)
            sys.exit(1)

        logger.info("正在上传 “%s” ..." % title)

        # 提取 tags 需要在删除 yaml 头之前
        sf_tags_str = self.sf.parse_tags_from_yaml_header(content)
        logger.debug(f"文章标签：{sf_tags_str}")
        if sf_tags_str:
            if len(sf_tags_str) > 5:
                logger.fatal("思否的标签个数不能超过 5 个")
        else:
            sf_tags_str = [category]

        # 删除开头的 yaml 内容
        content = remove_yaml_header(content)
        logger.debug("已删除文章的 yaml 头")

        tasks = []

        if post_record:
            if not jianshu_id:  # type: ignore
                tasks.append(asyncio.create_task(self.jianshu.new_post(ids[1], title, content, self.db)))
            if not cnblogs_id:  # type: ignore
                post = create_post(title, content, category)
                tasks.append(asyncio.create_task(self.cnblogs.new_post(post, self.db)))
            if not segment_fault_id:  # type: ignore
                sf_tags = await self.sf.search_tags(sf_tags_str, self.db)
                tasks.append(asyncio.create_task(self.sf.new_post(title, content, sf_tags, self.db)))
        else:
            self.db.insert_post(title, md5, ids[0], file_path=file_path)

            jianshu_task = asyncio.create_task(self.jianshu.new_post(ids[1], title, content, self.db))

            post = create_post(title, content, category)
            cnblogs_task = asyncio.create_task(self.cnblogs.new_post(post, self.db))

            sf_tags = await self.sf.search_tags(sf_tags_str, self.db)
            sf_task = asyncio.create_task(self.sf.new_post(title, content, sf_tags, self.db))

            tasks = [jianshu_task, cnblogs_task, sf_task]

        await asyncio.gather(*tasks)

        logger.info(
            "已上传 “%s.md” 到所有博客 - [%s, %s, %s] 的 “%s” 分类中" % (title, self.jianshu, self.cnblogs, self.sf, category)
        )

    async def update_post(self, title: str, content: str, md5: str):
        # TODO: 更新时应记录每个网站的更新结果，如果某个网站更新失败，可在下次再次更新该网站的文章
        post_id, jianshu_id, cnblogs_id, sf_id = self.db.select_post(title)

        logger.info(f"正在更新《{title}》...")

        # TODO: 简书更新有问题
        jianshu_task = asyncio.create_task(self.jianshu.update_post(jianshu_id, content, self.db))

        category = self.db.query_category_for_post(title)[0]
        post = create_post(title, content, category)
        cnblogs_task = asyncio.create_task(self.cnblogs.edit_post(cnblogs_id, post))

        if sf_id:
            sf_task = asyncio.create_task(self.sf.update_post(sf_id, content, self.db, title=title))
            tasks = [jianshu_task, cnblogs_task, sf_task]
        else:
            tasks = [jianshu_task, cnblogs_task]

        await asyncio.gather(*tasks)

        self.db.update_post(title, md5)

        logger.info(f"《{title}》更新完成")

    async def update_all_posts(self) -> List[str]:
        from mbs.utils.common import remove_yaml_header

        # TODO: 思否发表文章不能太快
        logger.info("正在上传之前上传失败的文章...")
        not_uploaded_posts = self.find_all_not_uploaded_posts()

        count = 0
        for p in not_uploaded_posts:
            if count > 0:
                time.sleep(60)
                logger.warning("思否创建文章限制在 1篇 / 分，休息 60 秒")

            title, jianshu, cnblogs, sf, file_path = p
            category = self.db.select_category_by_title(title, jianshu=jianshu, cnblogs=cnblogs, sf=sf)
            if not category:
                logger.fatal("没有找到分类：%s" % title)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            # 不上传曾经上传失败的文章到个人网站中

            await self.new_post(category, title, content, "", file_path)  # type: ignore
            count += 1

        logger.info("之前上传失败的文章已全部上传")

        # 给个人博客更新用的文件集合
        change_files = []

        update_tasks = []

        rows = self.db.select_md5_of_all_posts()
        for row in rows:
            id_, title, md5, jianshu_id, cnblogs_id, category_id, sf_id, file_path, _, _ = row
            current_md5 = get_md5_of_file(file_path)
            if current_md5 != md5:
                change_files.append(file_path)
                content = read_post_from_file(file_path)[1]
                content = remove_yaml_header(content)
                update_tasks.append(asyncio.create_task(self.update_post(title, content, current_md5)))

        await asyncio.gather(*update_tasks)

        return change_files

    def delete_post(self, title: str):
        post = self.db.select_post(title)
        if not post:
            logger.error("文章不存在：%s" % title)
            sys.exit(1)
        category_id, jianshu_id, cnblogs_id, segment_fault_id = post
        self.jianshu.delete_post(jianshu_id)
        self.cnblogs.delet_post(cnblogs_id)
        logger.info("标题为《%s》的文章已删除" % title)

    def sync_categories(self):
        # TODO: 改为异步或多线程
        while True:
            jcs = self.jianshu.get_categories()
            ccs = self.cnblogs.get_categories()

            if not jcs or not ccs:
                logger.error("获取分类列表失败")
                break

            jcs_set = {i["name"] for i in jcs}
            ccs_set = {i["name"] for i in ccs}

            if jcs_set - ccs_set:
                for c in jcs_set - ccs_set:
                    self.cnblogs.new_category(c)
                logger.info(f"已向博客园添加缺失的分类：{jcs_set - ccs_set}")
            elif ccs_set - jcs_set:
                for c in ccs_set - jcs_set:
                    self.jianshu.new_category(c)
                logger.info(f"已向简书添加缺失的分类：{ccs_set - jcs_set}")
            else:
                logger.info("已同步所有分类")
                break

        if jcs and ccs:
            jcs = {i["name"]: i["id"] for i in jcs}
            ccs = {i["name"]: i["id"] for i in ccs}
            for k, v in jcs.items():
                if self.db.select_category(k):
                    self.db.update_category(k, v, ccs[k])
                else:
                    self.db.insert_category(k, v, ccs[k])

    def find_all_not_uploaded_posts(self):
        records = self.db.select_all_not_uploaded_posts()
        not_uploaded_posts = []
        for r in records:
            title, jianshu_id, cnblogs_id, segment_fault_id, file_path = r
            not_uploaded_posts.append(
                (
                    title,
                    YES_CODE if jianshu_id else NO_CODE,
                    YES_CODE if cnblogs_id else NO_CODE,
                    YES_CODE if segment_fault_id else NO_CODE,
                    file_path,
                )
            )
        return not_uploaded_posts

    def find_all_changed_markdown_files(self):
        change_files = []
        for row in self.db.select_md5_of_all_posts():
            id_, title, md5, _, _, _, _, file_path, _, _ = row
            current_md5 = get_md5_of_file(file_path)
            if current_md5 != md5:
                change_files.append((title, UPDATED_CODE, UPDATED_CODE, UPDATED_CODE, file_path))
        if not change_files:
            return None

        return change_files
