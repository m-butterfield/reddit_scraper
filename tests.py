"""
Reddit scraper tests.

"""
import unittest

from datetime import datetime, timedelta

import db
import reddit_scraper


class BaseDBTestCase(unittest.TestCase):

    def setUp(self):
        db.create_tables()

    def tearDown(self):
        db.drop_tables()


class TestBackfill(BaseDBTestCase):

    def test_backfill_subreddit(self):
        backfill_to = datetime.utcnow() - timedelta(days=3)
        # reddit_scraper.scrape('blah', backfill_to=backfill_to)


class TestScrape(BaseDBTestCase):

    def test_scrape_no_backfill(self):
        self.assertRaises(ValueError, reddit_scraper.scrape, 'blah')
