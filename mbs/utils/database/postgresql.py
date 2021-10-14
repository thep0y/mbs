#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: thepoy
# @Email: thepoy@163.com
# @File Name: postgresql.py
# @Created: 2021-04-07 09:00:26
# @Modified: 2021-07-05 09:41:56

import psycopg2

from psycopg2.extensions import connection, cursor
from mbs.utils.database import Database


class PostgreSQL(Database):
    def __init__(self, dsn: str) -> None:
        self.conn: connection = psycopg2.connect(dsn)
        self.cursor: cursor = self.conn.cursor()

    def _create_database(self):
        pass
