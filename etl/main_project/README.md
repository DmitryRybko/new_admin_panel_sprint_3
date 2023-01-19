**Проект MOVIES_ADMIN**

В директории main_project размещена наиболее актуальная версия проекта movies_admin (по результатам спринтов 1, 2),
скрипт ETL(Extract-Transform-Load) процесса (спринт 3), который выгружает данные пачками напрямую из PostgresDB, трансформирует в
соответствии с описанием индекса Elasticsearch (es_schema.py), и загружает в Elasticsearch. При потере связи с 
PostgresDB и/или Elasticsearch выполняет backoff, а после восстановления соединения продолжает работу. 
По результатам спринта 4 добавлен ETL по жанрам, подняты сервисы FastAPI и redis.  

Для того, чтобы весь сервис поднимался, необходимо разместить в одну папку директории из двух репозиториев:
этот и Async_API_sprint_1.

Проект movies_admin - это приложение на Django (по стандарту WSGI).
Приложение хранит и предоставляет информацию о фильмах из своей базы данных.

Приложение функционально включает: 
 - панель администратора, где можно создавать, считывать, удалять, обновлять информацию по фильмам.
 - API, который позволяет получать информацию о всех фильмах в базе данных, либо по конкретному фильму.

Используемая база данных - PostgresDB.  
HTTP-сервер и обратный прокси-сервер - Nginx.

**Запуск проекта с помощью Docker Compose.**

1. Настроить переменные окружения в файле .env (пример - см. файл env.example).
2. В терминале из директории main_project выполнить команду "docker-compose up -d --build".
3. Команда создаст образы и запустит приложение с восемью Docker-контейнерами:
- Django (на порту 8000 внутри Docker приложения, закрыт для доступа извне)
- Postgres (на порту 5432 внутри Docker приложения, закрыт для доступа извне)
- Nginx (на порту 80:80)
- Elasticsearch (на порту 9200:9200 )
- ETL (без портов)
- Kibana (5601:5601) - для удобства работы с данными Elasticsearch.
- redis (6379:6379)
- FastAPI (8001:8001)

4. После запуска контейнера ETL (main_project_etl_1) начинается цикличный процесс переноса данных из 
Postgres в Elasticsearch. Чтобы перезагрузить все данные в Elasticsearch, нужно удалить файл status_file.txt.

Для удобного управления контейнерами можно установить Docker Desktop

После запуска будут доступны следующие сервисы:

(1) Административная панель: http://localhost/admin/

(2) API:

 - информация по всем фильмам (http://localhost/api/v1/movies/) в постраничной разбивке

 - информация по одному фильму (http://localhost/api/v1/movies/{id}/), где id - uuid фильма, 
например: http://localhost/api/v1/movies/00af52ec-9345-4d66-adbe-50eb917f463a/

Описание API находится в файле openapi.yaml.
Файл Postman для тестирования API - в файле movies API.postman_collection.json (порты линков заменены с 8000 на 80)

(3) Elasticsearch:

- описание индекса film_work: http://localhost:9200/film_work/
- информация по всем фильмам: http://localhost:9200/film_work/_search?pretty=true&size=50- описание индекса movies: http://localhost:9200/film_work/
- описание индекса generes: http://localhost:9200/genres/
- информация по всем жанрам: http://localhost:9200/genres/_search?pretty=true&size=50

Файл Postman для тестирования Elasticsearch - 
https://code.s3.yandex.net/middle-python/learning-materials/ETLTests-2.json

(4) Kibana:

- состояние индекса: http://localhost:5601/app/kibana#/management/elasticsearch/index_management/indices?_g=()
