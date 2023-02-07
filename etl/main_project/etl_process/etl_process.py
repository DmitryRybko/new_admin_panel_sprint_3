import backoff
import psycopg2
import requests
import time
import json
import logging
from elasticsearch7 import Elasticsearch, helpers
from elasticsearch7.exceptions import ConnectionError
from es_schema import es_schema
from es_schema_genres import es_schema_genres
from es_schema_persons import es_schema_persons
from datetime import datetime
from settings import settings, dsn_settings
from state_processing import JsonFileStorage, State
from etl_sql import select_film_works, select_genres, select_persons


def backoff_hdlr(details: dict):
    """"
    Accepts a dictionary with info on backoff process status from @backoff.
    """
    logging.info("Backing off {wait:0.1f} seconds after {tries} tries calling function {target}".format(**details))


@backoff.on_exception(backoff.expo, psycopg2.OperationalError, max_time=60, max_tries=8, on_backoff=backoff_hdlr)
def extract_from_pg(dsn: dict, used_table: str):
    """
    Connects with PostgresDB, reads data by chunks and updates time of load of non-empty chunk in external status
    file (status_file.txt). Upon next run the function loads available chunk for records with modification time
    later that saved status time. In case of lost connection, @backoff intercepts conn err and attempts to
    reconnect (increasing time between attempts exponentially). Upon conn restore, the extract process continues.

    :param dsn: dictionary with setting for conn with PostgresDB
    :param used_table: basic Postgres table from which data is extracted
    :return: tuple with chunks of data from Postgres
    """

    current_table = used_table

    with psycopg2.connect(**dsn) as conn, conn.cursor() as cursor:

        if current_table == settings.INDEX_NAME:
            status_time = current_state.get_state("status_time_filmwork")
            cursor.execute(select_film_works, (status_time,))

            current_chunk = cursor.fetchall()
            current_status_time = current_chunk[-1][4]
            current_state.set_state("status_time_filmwork", str(current_status_time))
            if current_chunk == ():
                current_state.set_state("status_time_filmwork", str(datetime.now()))
                return None
            else:
                return current_chunk

        elif current_table == settings.INDEX_NAME_GENRE:

            cursor.execute(select_genres)

            current_chunk = cursor.fetchall()
            return current_chunk

        elif current_table == settings.INDEX_NAME_PERSONS:

            cursor.execute(select_persons)

            current_chunk = cursor.fetchall()
            return current_chunk


def transform_data(chunk: dict, table: str):
    """
    Transfroms data in accordance with Elasticsearch index description (es_schema.py).
    :param chunk: tuple with chunk of data from Postgres
    :param table: basic Postgres table from which data is extracted
    :return: generator which returns docs in Elasticsearch format
    """

    current_table = table

    if current_table == settings.INDEX_NAME:

        def process_persons(persons_data):
            """
            Transforms persons data in accordance with Elasticsearch index description (es_schema.py).
            """
            persons_dict = {}
            roles = ("actor", "director", "writer")
            for role in roles:
                role_dict = [{"id": item["id"], "name": item["name"]} for item in persons_data if
                             item["person_role"] == role]
                persons_dict[f'{role}s'] = role_dict
            return persons_dict

        for record in chunk:
            persons_dict = process_persons(record[5])
            doc = {
                "_index": current_table,
                "_id": record[0],
                "_source": {
                    "id": record[0],
                    "title": record[1],
                    "description": record[2],
                    "imdb_rating": record[3],
                    "actors": persons_dict["actors"],
                    "director": str(persons_dict.get("directors")),
                    "actors_names": "",
                    "writers_names": "",
                    "writers": persons_dict["writers"],
                    "genre": record[6],

                }
            }
            yield doc

    elif current_table == settings.INDEX_NAME_GENRE:

        for record in chunk:
            doc = {
                "_index": current_table,
                "_id": record[0],
                "_source": {
                    "id": record[0],
                    "name": record[1],
                    "description": record[2],
                }
            }
            yield doc

    elif current_table == settings.INDEX_NAME_PERSONS:

        for record in chunk:
            doc = {
                "_index": current_table,
                "_id": record[0],
                "_source": {
                    "id": record[0],
                    "full_name": record[1],
                    "roles": record[3],
                    "film_ids": record[4]
                }
            }
            yield doc

@backoff.on_exception(backoff.expo, requests.exceptions.ConnectionError, max_time=60, max_tries=8,
                      on_backoff=backoff_hdlr)
def create_es_index(data_scheme: dict):
    """
    Loads index description from es_schema.py and creates Elasticsearch index.
    In case of lost connection, @backoff intercepts conn err and attempts to reconnect
    (increasing time between attempts exponentially). Upon conn restore, the extract process continues.
    :param data_scheme: Elasticsearch index description
    :return: None
    """

    url = f'http://{settings.ES_HOST}:{settings.ES_PORT}/film_work'
    payload = json.dumps(data_scheme)
    headers = {'Content-Type': 'application/json'}
    requests.put(url, headers=headers, data=payload)


def create_es_index_genres(data_scheme: dict):
    """
    Loads index description from es_schema.py and creates Elasticsearch index.
    In case of lost connection, @backoff intercepts conn err and attempts to reconnect
    (increasing time between attempts exponentially). Upon conn restore, the extract process continues.
    :param data_scheme: Elasticsearch index description
    :return: None
    """

    url = f'http://{settings.ES_HOST}:{settings.ES_PORT}/genres'
    payload = json.dumps(data_scheme)
    headers = {'Content-Type': 'application/json'}
    requests.put(url, headers=headers, data=payload)

def create_es_index_persons(data_scheme: dict):
    """
    Loads index description from es_schema.py and creates Elasticsearch index.
    In case of lost connection, @backoff intercepts conn err and attempts to reconnect
    (increasing time between attempts exponentially). Upon conn restore, the extract process continues.
    :param data_scheme: Elasticsearch index description
    :return: None
    """

    url = f'http://{settings.ES_HOST}:{settings.ES_PORT}/persons'
    payload = json.dumps(data_scheme)
    headers = {'Content-Type': 'application/json'}
    requests.put(url, headers=headers, data=payload)


@backoff.on_exception(backoff.expo, ConnectionError, max_time=60, max_tries=8, on_backoff=backoff_hdlr)
def load_data_to_es(doc):
    """
    Cooonects with Elasticsearch, loads documents from a chunck to Elasticsearch.
    In case of lost connection, @backoff intercepts conn err and attempts to reconnect
    (increasing time between attempts exponentially). Upon conn restore, the extract process continues.
    :param doc: generator which returns docs in Elasticsearch format
    :return: None
    """
    es_client = Elasticsearch(f"http://{settings.ES_HOST}:{settings.ES_PORT}")
    helpers.bulk(es_client, doc)


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)
    state_storage = JsonFileStorage(settings.STATE_STORAGE_FILE)
    current_state = State(state_storage)

    if not current_state.get_state("status_time_filmwork"):
        current_state.set_state("status_time_filmwork", settings.STARTING_TIME)
    if not current_state.get_state("status_time_genres"):
        current_state.set_state("status_time_genres", settings.STARTING_TIME)
    if not current_state.get_state("status_time_persons"):
        current_state.set_state("status_time_persons", settings.STARTING_TIME)

    create_es_index(es_schema)
    create_es_index_genres(es_schema_genres)
    create_es_index_persons(es_schema_persons)
    tables = (settings.INDEX_NAME, settings.INDEX_NAME_GENRE, settings.INDEX_NAME_PERSONS)

    while True:
        for table in tables:

            records_data = extract_from_pg(dsn_settings, table)
            data_for_es = transform_data(records_data, table)
            load_data_to_es(data_for_es)

        time.sleep(settings.ETL_SLEEP_TIME)

