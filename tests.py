"""
Reddit scraper tests

"""
import unittest

from db import create_tables, drop_tables


class BaseDBTestCase(unittest.TestCase):

    def setUp(self):
        create_tables()

    def tearDown(self):
        drop_tables()


class TestAPI(BaseDBTestCase):

    def test_api(self):
        pass
