from pydantic import BaseSettings
from dotenv import load_dotenv

# load_dotenv здесь нужен несмотря на наличие pydantic, так как pydantic не умеет искать env в parent директориях
load_dotenv()


class Settings(BaseSettings):
    DB_NAME: str = "movies_database1"
    DB_USER: str = "some_user"
    DB_PASSWORD: str = "some_password"
    SECRET_KEY: str = "some_secret_key"
    DSN_OPTIONS = '-c search_path=content'
    DB_HOST: str = "localhost"
    DB_PORT: int = 54321

    ES_HOST: str = "localhost"
    ES_PORT: int = "9200"
    INDEX_NAME: str = "movies"

    STARTING_TIME: str = "2021-06-16 23:14:09.200 +0300"
    LOAD_SIZE: int = 50

    STATE_STORAGE_FILE: str = "state_file.txt"

    ETL_SLEEP_TIME: int = 20

    class Config:
        case_sensitive = False
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = Settings()
dsn_settings: dict = dict(dbname=settings.DB_NAME, user=settings.DB_USER, password=settings.DB_PASSWORD,
                          host=settings.DB_HOST, port=settings.DB_PORT, options=settings.DSN_OPTIONS)
