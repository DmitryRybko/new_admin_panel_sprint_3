#!/usr/bin/env bash

set -e
/opt/app/wait-for-it.sh "${DB_HOST}":"${DB_PORT}"  -- echo "Postgres is up"
python manage.py collectstatic --noinput
python manage.py compilemessages -l en -l ru
python manage.py migrate
uwsgi --strict --ini /opt/app/uwsgi/uwsgi.ini
