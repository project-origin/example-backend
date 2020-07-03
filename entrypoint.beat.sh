#!/bin/sh
cd /app/migrations && pipenv run migrate || exit
cd /app && exec pipenv run celery beat -A originexample.pipelines -l info
