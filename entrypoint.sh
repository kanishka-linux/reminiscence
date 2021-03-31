#!/bin/sh
while ! nc -w 1 -z ${DB_HOST} 5432; do sleep 0.1; done;
python manage.py migrate;
python manage.py createdefaultsu;
python manage.py collectstatic --no-input;
if [ ! -d '/usr/src/reminiscence/static/nltk_data' ]; then
    echo 'wait..downloading..nltk_data';
    python manage.py nltkdownload;
fi;
gunicorn --max-requests 1000 \
    --worker-class gthread \
    --workers 4 --thread 10 \
    --timeout 300 \
    --bind 0.0.0.0:8000 reminiscence.wsgi
