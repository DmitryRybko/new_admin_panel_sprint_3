FROM python:3.10
RUN apt update
RUN apt install gettext -y
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.5.0/wait /wait
WORKDIR /opt/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV UWSGI_PROCESSES 1
ENV UWSGI_THREADS 16
ENV UWSGI_HARAKIRI 240
ENV DJANGO_SETTINGS_MODULE 'config.settings'

COPY requirements.txt requirements.txt
COPY uwsgi/uwsgi.ini uwsgi.ini
COPY config/wsgi.py config/wsgi.py
COPY wait-for-it.sh wait-for-it.sh
COPY entrypoint.sh entrypoint.sh

RUN  mkdir -p /opt/app/static/ \
     && mkdir -p /opt/app/media/ \
     && pip install --upgrade pip \
     && pip install -r requirements.txt \
     && chmod +x wait-for-it.sh \
     && chmod +x entrypoint.sh

COPY . .

EXPOSE 8000

ENTRYPOINT ["bash", "/opt/app/entrypoint.sh"]
