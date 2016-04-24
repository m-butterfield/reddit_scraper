import os


DB_URI = 'postgresql://localhost/reddit_scraper'

REDDIT_USER_AGENT = 'Reddit Scraper Script'

IMAGES_FOLDER_NAME = 'scraped_images'
IMAGES_FOLDER_PATH = os.path.join(os.getcwd(), IMAGES_FOLDER_NAME)

IMGUR_CLIENT_ID = os.getenv('IMGUR_CLIENT_ID')
IMGUR_CLIENT_SECRET = os.getenv('IMGUR_CLIENT_SECRET')
