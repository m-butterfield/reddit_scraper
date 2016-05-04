"""
Reddit scraper tests.

"""
import hashlib
import mock
import unittest

from datetime import datetime, timedelta

from imgurpython import ImgurClient

from praw.objects import Subreddit

import reddit_scraper
import settings

from db import create_tables, drop_tables, Image, Post, session_manager


FILE_CONTENT = 'stuff'
FILE_HASH = hashlib.sha1(FILE_CONTENT).hexdigest()
FAKE_IMGUR_URL = 'http://imgur.com/123abc.jpg'


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
        return [FILE_CONTENT]

    def json(self):
        return {}

    def raise_for_status(self):
        pass


def _fake_get(*args, **kwargs):
    return FakeResponse()


def _make_get_new_func(first_batch, second_batch):
    """
    Create a function to replace PRAW Subreddit's get_new().  Assumes the first
    time the function is called, the 'params' argument will not be passed,
    therefore only returning the first batch of submissions, then when 'params'
    is passed, the second batch will be returned.

    :type first_batch: list
    :type second_batch: list

    :rtype: function

    """
    def func(limit, params=None):
        if params is None:
            return first_batch
        return second_batch
    return func


class BaseDBTestCase(unittest.TestCase):

    def setUp(self):
        create_tables()

    def tearDown(self):
        drop_tables()


class TestBackfill(BaseDBTestCase):

    @mock.patch.object(Subreddit, 'get_new')
    @mock.patch.object(ImgurClient, 'get_image')
    @mock.patch('reddit_scraper.requests.get', side_effect=_fake_get)
    def test_backfill_subreddit(self, fake_get, fake_get_image, fake_get_new):
        backfill_to = datetime.now()
        submission = FakeSubmission(
            backfill_to + timedelta(seconds=1), 'new submission')

        fake_get_new.side_effect = _make_get_new_func(
            [submission], [FakeSubmission(backfill_to - timedelta(seconds=1))])

        fake_get_image.return_value = FakeImage()

        reddit_scraper.scrape('blah', backfill_to=backfill_to)

        with session_manager() as session:
            post = session.query(Post).one()
            self.assertEqual(post.name, submission.name)


class TestScrape(BaseDBTestCase):

    def setUp(self):
        super(TestScrape, self).setUp()
        self.subreddit_name = 'blah'
        with session_manager() as session:
            image = Image(file_hash=FILE_HASH,
                          file_ext='.jpg',
                          content_type='image/jpeg',
                          width=100,
                          height=150,
                          size=1024)
            session.add(image)
            session.add(Post(name='blah',
                             image_file_hash=image.file_hash,
                             submitted=datetime.now(),
                             subreddit_name=self.subreddit_name))

    @mock.patch('reddit_scraper.requests.get', side_effect=_fake_get)
    def test_scrape_no_backfill(self, _fake_get):
        self.assertRaises(reddit_scraper.NoBackfillError,
                          reddit_scraper.scrape,
                          self.subreddit_name + '_derp')

    @mock.patch.object(Subreddit, 'get_new')
    @mock.patch('reddit_scraper.requests.get', side_effect=_fake_get)
    @mock.patch('reddit_scraper._handle_submission')
    def test_scrape_up_to_date(self, fake_handle, fake_get, fake_get_new):
        reddit_scraper.scrape('blah')
        fake_handle.assert_not_called()
