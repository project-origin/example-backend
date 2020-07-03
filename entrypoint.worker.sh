#!/bin/sh
cd /app/migrations && pipenv run migrate || exit
cd /app && exec pipenv run celery worker -A originexample.pipelines -O fair -l info --pool=gevent --concurrency=$CONCURRENCY
