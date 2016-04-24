"""
Python API for reddit_scraper

"""
import hashlib
import os
import shutil

from datetime import datetime
from tempfile import NamedTemporaryFile
from urlparse import urlparse

import requests

from imgurpython import ImgurClient
from imgurpython.helpers.error import ImgurClientError

from praw import Reddit

from .db import db_session, init_db, Post, Image

import settings


PAGINATION_LIMIT = 5


initialize_database = init_db


def scrape(subreddit_name, backfill_to=None):
    """
    Scrape a subreddit.

    :type subreddit_name: str
    :type backfill_to: datetime.datetime

    """
    subreddit_name = subreddit_name.lower()
    imgur_client = ImgurClient(
        settings.IMGUR_CLIENT_ID, settings.IMGUR_CLIENT_SECRET)
    reddit = Reddit(user_agent=settings.REDDIT_USER_AGENT)
    subreddit = reddit.get_subreddit(subreddit_name)
    with db_session() as session:
        if backfill_to:
            _backfill(
                session, subreddit, subreddit_name, imgur_client, backfill_to)
        else:
            _scrape(session, subreddit, imgur_client)


def _backfill(session, subreddit, subreddit_name, imgur_client, backfill_to):
    print "Backfilling {} to {}".format(subreddit_name, backfill_to)
    submissions = [s for s in subreddit.get_new(limit=PAGINATION_LIMIT)]
    while submissions:
        for submission in submissions:
            created = datetime.fromtimestamp(submission.created_utc)
            if created < backfill_to:
                print "Backfill complete..."
                return
            _handle_submission(
                session, submission, imgur_client, subreddit_name, created)
        submissions = [s for s in subreddit.get_new(
            limit=PAGINATION_LIMIT, params={'after': submission.name})]


def _scrape(session, subreddit, imgur_client):
    for submission in subreddit.get_new(
            limit=PAGINATION_LIMIT, params={'before': 't3_4fp33k'}):
        print submission.name


def _handle_submission(session,
                       submission,
                       imgur_client,
                       subreddit_name,
                       created):
    if _get_post(session, submission.id) is not None:
        print "Post {} already saved...".format(submission.name)
        return

    uri = urlparse(submission.url)
    if 'imgur.com' not in uri.netloc:
        print "Submission not from imgur, skipping..."
        return

    image_id = os.path.basename(os.path.splitext(uri.path)[0])
    try:
        imgur_image = imgur_client.get_image(image_id)
    except ImgurClientError:
        print 'Could not get image from imgur, skipping...'
        return

    response = requests.get(imgur_image.link, stream=True)
    try:
        response.raise_for_status()
    except requests.HTTPError as ex:
        print "Could not download image: {}".format(ex)
        return

    print "Downloading image for post: {}".format(submission.id)
    with NamedTemporaryFile() as fp:
        for chunk in response.iter_content(1024):
            fp.write(chunk)
        fp.seek(0)
        file_hash = _get_file_hash(fp)
        image = _get_or_create_image(
            session, fp, imgur_image, file_hash, subreddit_name)
    print "Saving post {}".format(submission.id)
    session.add(Post(id=submission.id,
                image_file_hash=image.file_hash,
                submitted=created,
                subreddit_name=subreddit_name))
    session.commit()


def _get_post(session, submission_id):
    return session.query(Post).get(submission_id)


def _get_or_create_image(session, fp, imgur_image, file_hash, subreddit_name):
    existing_image = session.query(Image).get(file_hash)
    if existing_image:
        return existing_image
    file_ext = os.path.splitext(imgur_image.link)[1]
    file_name = file_hash + file_ext
    folder_path = os.path.join(settings.IMAGES_FOLDER_PATH, subreddit_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    shutil.copy(fp.name, os.path.join(folder_path, file_name))
    image = Image(file_hash=file_hash,
                  file_ext=file_ext,
                  content_type=imgur_image.type,
                  width=imgur_image.width,
                  height=imgur_image.height,
                  size=imgur_image.size)
    session.add(image)
    session.flush()
    return image


def _get_file_hash(fp):
    chunk_size = 1024
    data = fp.read(chunk_size)
    file_hash = hashlib.sha1()
    while data:
        file_hash.update(data)
        data = fp.read(chunk_size)
    fp.seek(0)
    return file_hash.hexdigest()
