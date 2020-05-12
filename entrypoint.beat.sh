#!/bin/sh
cd /app/migrations && pipenv run migrate || exit
cd /app && pipenv run celery beat -A originexample.pipelines -l info
