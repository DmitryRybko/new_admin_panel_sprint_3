import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.environ.get("DB_NAME")
USER = os.environ.get("DB_USER")
PASSWORD = os.environ.get("DB_PASSWORD")
HOST = os.environ.get("DB_HOST", 'localhost')
PORT = os.environ.get("DB_PORT", 54321)
DSN_OPTIONS = '-c search_path=content'

ES_HOST = os.environ.get("ES_HOST", 'localhost')
ES_PORT = os.environ.get("ES_PORT", 9200)

dsn_settings: dict = dict(dbname=DB_NAME, user=USER, password=PASSWORD, host=HOST, port=PORT, options=DSN_OPTIONS)
load_size = 50

starting_time = os.environ.get('STARTING_TIME', '2021-06-16 23:14:09.200 +0300')
