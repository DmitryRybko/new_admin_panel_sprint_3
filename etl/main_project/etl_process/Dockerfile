FROM python:3.10
RUN apt update
RUN apt install cron -y
COPY . .
RUN pip install -r requirements.txt
RUN crontab crontab
RUN touch logfile.txt
CMD ["cron", "-f"]