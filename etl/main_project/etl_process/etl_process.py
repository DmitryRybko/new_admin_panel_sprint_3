import backoff
import psycopg2
import requests
import json
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from elasticsearch.exceptions import ConnectionError
from es_schema import es_schema
from datetime import datetime
from settings import dsn_settings, load_size, ES_HOST, ES_PORT, starting_time


def backoff_hdlr(details):
    """"
    Функция, которая принимает от @backoff словарь details с информацией о статусе процесса backoff.
    """
    print("Backing off {wait:0.1f} seconds after {tries} tries calling function {target}".format(**details))


@backoff.on_exception(backoff.expo, psycopg2.OperationalError, max_time=60, max_tries=8, on_backoff=backoff_hdlr)
def extract_from_pg(dsn: dict, chunk_size: int):
    """
    Функция осуществляет соединение с PostgresDB, считывает данные пачками, инициирует их трансформацию в формат для
    Elasticsearch и инициирует загрузку каждой пачки в Elasticsearch. Время последней успешной загрузки в Elasticsearch
    сохраняется во внешнем файле (status_file.txt). При следующем запуске функция выгружает пачки записей со временем
    модификации позже ранее сохраненного. В случае потери связи с Postgres декоратор backoff перехватывает
    ошибку соединения и пытается соединиться вновь (увеличивая время экcпоненциально). При восстановлении соединения
    загрузка продолжается.

    :param dsn: словарь с настройками соединения с PostgresDB
    :param chunk_size: размер пачки для выгрузки данных из Postgres
    :return:
    """
    with psycopg2.connect(**dsn) as conn, conn.cursor() as cursor:
        current_table = "film_work"
        cursor.execute(f'SELECT COUNT(*) FROM {current_table}')
        records_qty = cursor.fetchone()[0]
        chunks_qty = -(-records_qty//chunk_size)

        with open("state_file.txt", 'r') as state_file:
            status_time = str(state_file.readline())

        cursor.execute('''
                    SELECT
                       fw.id,
                       fw.title,
                       fw.description,
                       fw.rating,
                       COALESCE (
                           json_agg(
                               DISTINCT jsonb_build_object(
                                   'person_role', pfw.role,
                                   'id', p.id,
                                   'name', p.full_name
                               )
                           ) FILTER (WHERE p.id is not null),
                           '[]'
                       ) as persons,
                       array_agg(DISTINCT g.name) as genres
                    FROM content.film_work fw
                    LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
                    LEFT JOIN content.person p ON p.id = pfw.person_id
                    LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
                    LEFT JOIN content.genre g ON g.id = gfw.genre_id
                    WHERE fw.modified > (%s)
                    GROUP BY fw.id
                    ORDER BY fw.modified
                    ''', (status_time,))

        for chunk_no in range(chunks_qty):
            current_chunk = cursor.fetchmany(chunk_size)
            data_for_es = transform_data(current_chunk)
            load_data_to_es(data_for_es)

    with open("state_file.txt", 'w') as state_file:
        current_time = str(datetime.now())
        state_file.write(current_time)


def transform_data(chunk: dict):
    """
    Функция трансформирует данные, полученные из Postgres, в соответствии с описанием индекса для
    Elasticsearch (es_schema.py).
    :param chunk:
    :param index_name:
    :return:
    """
    records = chunk
    for record in records:
        persons_dict = process_persons(record[4])
        doc = {
            "_index": index_name,
            "_id": record[0],
            "_source": {
                "id": record[0],
                "title": record[1],
                "description": record[2],
                "imdb_rating": record[3],
                "actors": persons_dict["actors"],
                "director": str(persons_dict.get("directors")),
                "writers": persons_dict["writers"],
                "genre": record[5],
            }
        }
        yield doc


def process_persons(persons_data):
    """
    Функция трансформирует данные по persons в соответствии с описанием индекса для Elasticsearch (es_schema.py).
    """
    persons_dict = {}
    roles = ["actor", "director", "writer"]
    for role in roles:
        role_dict = [{"id": item["id"], "name": item["name"]} for item in persons_data if item["person_role"] == role]
        persons_dict[f'{role}s'] = role_dict
    return persons_dict


@backoff.on_exception(backoff.expo, requests.exceptions.ConnectionError, max_time=60, max_tries=8,
                      on_backoff=backoff_hdlr)
def create_es_index(data_scheme):
    """
    Функция загружает описание индекса из файла es_schema.py и на ее основе создает индекс в Elasticsearch.
    В случае потери связи с Elasticsearch декоратор backoff перехватывает ошибку соединения и пытается соединиться вновь
    (увеличивая время экcпоненциально). При восстановлении соединения создание индекса продолжается. Если индекс уже
    существует, то новый не сохдается и не перезаписывается. Также, функция создает файл state_file и записывает в него
    стартовое время по умолчанию, которое должно быть меньше, чем время модификации любой записи в Postgres. Если
    файл существует, то он остается как есть.
    :param data_scheme:
    :return:
    """

    url = f'http://{ES_HOST}:{ES_PORT}/movies'
    payload = json.dumps(data_scheme)
    headers = {'Content-Type': 'application/json'}
    requests.put(url, headers=headers, data=payload)

    try:
        with open("state_file.txt", 'x') as state_file:
            state_file.write(starting_time)
    except FileExistsError:
        pass


@backoff.on_exception(backoff.expo, ConnectionError, max_time=60, max_tries=8, on_backoff=backoff_hdlr)
def load_data_to_es(doc):
    """
    Функция осуществляет соединение с Elasticsearch, загружает документы из пачки в Elasticsearch. В случае потери
    связи с Elasticsearch декоратор backoff перехватывает ошибку соединения и пытается соединиться вновь
    (увеличивая время экcпоненциально). При восстановлении соединения загрузка продолжается.
    :param doc: генератор документов для загрузки в Elasticsearch
    :return:
    """
    es_client = Elasticsearch(f"http://{ES_HOST}:{ES_PORT}")
    helpers.bulk(es_client, doc)


if __name__ == '__main__':

    index_name = "movies"
    create_es_index(es_schema)
    movies_data = extract_from_pg(dsn_settings, load_size)


