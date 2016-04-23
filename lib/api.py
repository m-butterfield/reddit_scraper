"""
Python API for reddit_scraper

"""
from datetime import datetime

from praw import Reddit

from .db import init_db

import settings


init_database = init_db


PAGINATION_LIMIT = 5


def scrape(subreddit_name, backfill_to=None):
    """
    Scrape a subreddit.

    :type subreddit_name: str
    :type backfill_to: datetime.datetime

    """
    reddit = Reddit(user_agent=settings.USER_AGENT)
    subreddit = reddit.get_subreddit(subreddit_name)
    if backfill_to:
        _backfill(subreddit, backfill_to)
    else:
        _scrape(subreddit)


def _backfill(subreddit, backfill_to):
    submissions = [s for s in subreddit.get_new(limit=PAGINATION_LIMIT)]
    while submissions:
        for submission in submissions:
            created = datetime.fromtimestamp(submission.created_utc)
            print submission.name
            print created
            if created < backfill_to:
                return
        submissions = [s for s in subreddit.get_new(
            limit=PAGINATION_LIMIT, params={'after': submission.name})]


def _scrape(subreddit):
    for submission in subreddit.get_new(
            limit=PAGINATION_LIMIT, params={'before': 't3_4fp33k'}):
        print submission.name
