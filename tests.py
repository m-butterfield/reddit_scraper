"""
Reddit scraper tests.

"""
import hashlib
import mock
import unittest

from datetime import datetime, timedelta

from imgurpython import ImgurClient
from imgurpython.helpers.error import ImgurClientError

from praw.objects import Subreddit

import requests

from sqlalchemy.engine.reflection import Inspector

import reddit_scraper

from db import (
    create_tables,
    drop_tables,
    engine,
    Image,
    init_db,
    Post,
    session_manager,
)


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


def _imgur_error(imgur_id):
    raise ImgurClientError('blah')


def _requests_error():
    raise requests.HTTPError()


class TestDBInit(unittest.TestCase):

    def test_init_db(self):
        init_db()
        inspector = Inspector.from_engine(engine)
        self.assertEqual({'image', 'post'}, set(inspector.get_table_names()))
        drop_tables()


class BaseDBTestCase(unittest.TestCase):

    def setUp(self):
        create_tables()

    def tearDown(self):
        drop_tables()


class TestBackfill(BaseDBTestCase):

    @mock.patch.object(Subreddit, 'get_new')
    @mock.patch.object(ImgurClient, 'get_image')
    @mock.patch('reddit_scraper.requests.get')
    def test_backfill_subreddit(self, fake_get, fake_get_image, fake_get_new):
        fake_get.side_effect = _fake_get
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
            self.assertEqual(post.image.file_hash, FILE_HASH)
            self.assertEqual(post.image.file_name, FILE_HASH + '.jpg')


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

    @mock.patch.object(Subreddit, 'get_new')
    @mock.patch.object(ImgurClient, 'get_image')
    @mock.patch('reddit_scraper.requests.get')
    def test_scrape_image_exists(self, fake_get, fake_get_image, fake_get_new):
        fake_get.side_effect = _fake_get
        fake_get_new.side_effect = [[FakeSubmission(name='blerg')], []]
        fake_get_image.return_value = FakeImage()
        reddit_scraper.scrape(self.subreddit_name)
        with session_manager() as session:
            image = session.query(Image).one()
            self.assertEqual(image.file_hash, self.image_file_hash)

    @mock.patch.object(Subreddit, 'get_new')
    @mock.patch.object(ImgurClient, 'get_image')
    def test_scrape_unknown_image_source(self, fake_get_image, fake_get_new):
        fake_get_new.side_effect = [
            [FakeSubmission(name='blerg', url='http://blah.com/img.jpg')], []]
        reddit_scraper.scrape(self.subreddit_name)
        fake_get_image.assert_not_called()

    @mock.patch.object(Subreddit, 'get_new')
    @mock.patch.object(ImgurClient, 'get_image')
    @mock.patch('reddit_scraper._download_and_save_image')
    def test_scrape_imgur_error(self, fake_save, fake_get_image, fake_get_new):
        fake_get_new.side_effect = [[FakeSubmission(name='blerg')], []]
        fake_get_image.side_effect = _imgur_error
        reddit_scraper.scrape(self.subreddit_name)
        fake_save.assert_not_called()

    @mock.patch.object(Subreddit, 'get_new')
    @mock.patch.object(ImgurClient, 'get_image')
    @mock.patch.object(requests.Response, 'raise_for_status')
    @mock.patch('reddit_scraper._save_post')
    def test_scrape_http_error(self,
                               fake_save,
                               fake_raise,
                               fake_get_image,
                               fake_get_new):
        fake_get_new.side_effect = [[FakeSubmission(name='blerg')], []]
        fake_get_image.return_value = FakeImage()
        fake_raise.side_effect = _requests_error
        reddit_scraper.scrape(self.subreddit_name)
        fake_save.assert_not_called()
