#!/bin/sh
cd /app/migrations && pipenv run migrate || exit
cd /app && pipenv run gunicorn -b 0.0.0.0:8085 originexample:app --workers $WORKERS --worker-class gevent --worker-connections $WORKER_CONNECTIONS
