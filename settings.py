"""
Project settings

"""
import os


DB_URI = os.getenv("REDDIT_SCRAPER_DB_URI")

REDDIT_USER_AGENT = 'Reddit Scraper Script'

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

IMAGES_FOLDER_NAME = 'scraped_images'
IMAGES_FOLDER_PATH = os.path.join(PROJECT_ROOT, IMAGES_FOLDER_NAME)

IMGUR_CLIENT_ID = os.getenv('IMGUR_CLIENT_ID')
IMGUR_CLIENT_SECRET = os.getenv('IMGUR_CLIENT_SECRET')
