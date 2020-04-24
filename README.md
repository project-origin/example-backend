![alt text](doc/logo.png)

# Project Origin Example Application Backend

TODO Describe the project here


# Environment variables

Name | Description | Example
:--- | :--- | :--- |
`DEBUG` | Whether or not to enable debugging mode (off by default) | `0` or `1`
`DATABASE_URI` | Database connection string for SQLAlchemy | `postgresql://scott:tiger@localhost/mydatabase`
**URLs:** | |
`PROJECT_URL` | Public URL to this service without trailing slash | `https://examplebackend.projectorigin.dk`
`FRONTEND_URL` | Public URL the the frontend application | `https://projectorigin.dk`
`DATAHUB_SERVICE_URL` | Public URL to DataHubService without trailing slash | `https://datahub.projectorigin.dk`
`ACCOUNT_SERVICE_URL` | Public URL to AccountService without trailing slash | `https://account.projectorigin.dk`
`ACCOUNT_SERVICE_LOGIN_URL` | Public URL to AccountService login endpoint | `https://account.projectorigin.dk/auth/login`
**Authentication:** | |
`HYDRA_URL` | URL to Hydra without trailing slash | `https://auth.projectorigin.dk`
`HYDRA_INTROSPECT_URL` | URL to Hydra Introspect without trailing slash | `https://authintrospect.projectorigin.dk`
`HYDRA_CLIENT_ID` | Hydra client ID | `example_app`
`HYDRA_CLIENT_SECRET` | Hydra client secret | `some-secret`
**Redis:** | |
`REDIS_HOST` | Redis hostname/IP | `127.0.0.1`
`REDIS_PORT` | Redis port number | `6379`
`REDIS_USERNAME` | Redis username | `johndoe`
`REDIS_PASSWORD` | Redis username | `qwerty`
`REDIS_CACHE_DB` | Redis database for caching (unique for this service) | `0`
`REDIS_BROKER_DB` | Redis database for task brokering (unique for this service) | `1`
`REDIS_BACKEND_DB` | Redis database for task results (unique for this service) | `2`


# Building container images

Web API:

    sudo docker build -f Dockerfile.web -t example-backend-web:v1 .

Worker:

    sudo docker build -f Dockerfile.worker -t example-backend-worker:v1 .

Worker Beat:

    sudo docker build -f Dockerfile.beat -t example-backend-beat:v1 .


---
---
---


# Installing and running the project

The following sections describes how to install and run the project locally for development and debugging.

### Requirements

- Python 3.7
- Pip
- Pipenv

### First time installation

Make sure to upgrade your system packages for good measure:
   
    pip install --upgrade --user setuptools pip pipenv

Then install project dependencies:

    pipenv install
   
Then apply database migrations (while at the same time creating an empty SQLite database-file, if using SQLite):

    cd src/migrations
    pipenv run alembic upgrade head
    cd ../../

Then (optionally) seed the database with some data:

    pipenv run python src/seed.py

### Running locally (development)

This starts the local development server (NOT for production use):

    pipenv run python src/serve.py

### Running tests

Run unit- and integration tests:

    pipenv run pytest


# Project configuration

### Environment variables

TODO describe necessary environment variables

### Project settings

TODO describe src/origin/settings.py


# System design and implementation

### Dependencies

- SQLAlchemy
- marshmellow
- TODO


# Database (models and migrations)

TODO

## Workflow

TODO

## Make migrations

TODO

## Apply migrations

TODO


# Domain knowledge

TODO Alot to describe here...

## Terminology

TODO

## GGO calculation

- Stored = Issued + Inbound - Outbound - Expired
- Retired = Stored - Consumed


# Testing

Testing is done in a number of different ways, including:

- Pure unit-testing using mocked dependencies
- Unit-testing using a SQLite database, where assertions are made on the data stored in the database after the test
- Complex multi-component integration- and functional testing using both mocked dependencies and a SQLite database

*NOTE: Because of the use of SQLite in testing its necessary for the process executing
the tests to have write-access to the /var folder.*


# Glossary

TODO Describe commonly used terms
