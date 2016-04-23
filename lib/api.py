"""
Python API for reddit_scraper

"""
from praw import Reddit

from .db import init_db

import settings


init_database = init_db


PAGINATION_LIMIT = 10


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
    pass


def _scrape(subreddit):
    for submission in subreddit.get_new(
            limit=PAGINATION_LIMIT, params={'after': 't3_4fp33k'}):
        print submission.name
