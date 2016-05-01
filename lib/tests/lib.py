"""
Common code for tests

"""
import unittest

from ..db import create_tables, drop_tables


class BaseDBTestCase(unittest):

    def setUp(self):
        create_tables()

    def tearDown(self):
        drop_tables()
