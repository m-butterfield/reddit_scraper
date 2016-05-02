"""
Reddit scraper tests.

"""
import mock
import unittest

from datetime import datetime, timedelta

from imgurpython import ImgurClient

from praw.objects import Subreddit

import reddit_scraper

from db import create_tables, drop_tables, Post, session_manager


FAKE_IMGUR_URL = 'http://imgur.com/123abc.jpg'


class BaseDBTestCase(unittest.TestCase):

    def setUp(self):
        create_tables()

    def tearDown(self):
        drop_tables()


class FakeImage(object):

    type = 'image/jpeg'
    width = 100
    height = 200
    size = 1024

    def __init__(self, link=FAKE_IMGUR_URL):
        self.link = link


class FakeSubmission(object):

    def __init__(self, created_utc, name='', url=FAKE_IMGUR_URL):
        self.created_utc = int(created_utc.strftime('%s'))
        self.name = name
        self.url = url


class FakeResponse(object):

    headers = {}

    def __init__(self, status_code=200):
        self.status_code = status_code

    def iter_content(self, size):
        return ['stuff']

    def json(self):
        return {}

    def raise_for_status(self):
        pass


def _fake_get(*args, **kwargs):
    return FakeResponse()


class TestBackfill(BaseDBTestCase):

    @mock.patch.object(Subreddit, 'get_new')
    @mock.patch.object(ImgurClient, 'get_image')
    def test_backfill_subreddit(self, fake_get_image, fake_get_new):
        backfill_to = datetime.now()

        new_submission = FakeSubmission(
            backfill_to + timedelta(seconds=1), 'new submission')
        old_submission = FakeSubmission(backfill_to - timedelta(seconds=1))
        fake_submissions = [new_submission, old_submission]
        fake_get_new.return_value = fake_submissions

        fake_get_image.return_value = FakeImage()

        with mock.patch('reddit_scraper.requests.get', side_effect=_fake_get):
            reddit_scraper.scrape('blah', backfill_to=backfill_to)

        with session_manager() as session:
            post = session.query(Post).one()
            self.assertEqual(post.name, new_submission.name)


class TestScrape(BaseDBTestCase):

    def test_scrape_no_backfill(self):
        self.assertRaises(
            reddit_scraper.NoBackfillError, reddit_scraper.scrape, 'blah')
