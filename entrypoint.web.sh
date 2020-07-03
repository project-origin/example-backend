#!/bin/sh
cd /app/migrations && pipenv run migrate || exit
cd /app && exec pipenv run gunicorn -b 0.0.0.0:8081 originexample:app --workers $WORKERS --worker-class gevent --worker-connections $WORKER_CONNECTIONS
