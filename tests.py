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

    def __init__(self, created_utc=None, name='', url=FAKE_IMGUR_URL):
        if created_utc is None:
            created_utc = datetime.utcnow()
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
        fake_get_new.side_effect = [
            [submission], [FakeSubmission(backfill_to - timedelta(seconds=1))]]
        fake_get_image.return_value = FakeImage()

        reddit_scraper.scrape('blah', backfill_to=backfill_to)

        with session_manager() as session:
            post = session.query(Post).one()
            self.assertEqual(post.name, submission.name)


class TestScrape(BaseDBTestCase):

    def setUp(self):
        super(TestScrape, self).setUp()
        self.subreddit_name = 'blah'
        self.image_file_hash = FILE_HASH
        self.post_name = 'post'
        with session_manager() as session:
            session.add(Image(file_hash=self.image_file_hash,
                              file_ext='.jpg',
                              content_type='image/jpeg',
                              width=100,
                              height=150,
                              size=1024))
            session.add(Post(name=self.post_name,
                             image_file_hash=self.image_file_hash,
                             submitted=datetime.now(),
                             subreddit_name=self.subreddit_name))

    def test_scrape_no_backfill(self):
        self.assertRaises(reddit_scraper.NoBackfillError,
                          reddit_scraper.scrape,
                          self.subreddit_name + '_derp')

    @mock.patch.object(Subreddit, 'get_new')
    @mock.patch('reddit_scraper._handle_submission')
    def test_scrape_up_to_date(self, fake_handle, fake_get_new):
        reddit_scraper.scrape(self.subreddit_name)
        fake_handle.assert_not_called()

    @mock.patch.object(Subreddit, 'get_new')
    def test_scrape_post_exists(self, fake_get_new):
        fake_get_new.side_effect = [[FakeSubmission(name=self.post_name)], []]
        reddit_scraper.scrape(self.subreddit_name)
