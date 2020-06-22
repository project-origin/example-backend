"""
conftest.py according to pytest docs:
https://docs.pytest.org/en/2.7.3/plugins.html?highlight=re#conftest-py-plugins
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

from originexample.db import ModelBase


@pytest.fixture(scope='module')
def session():
    with PostgresContainer('postgres:9.6') as psql:
        engine = create_engine(psql.get_connection_url())
        ModelBase.metadata.create_all(engine)
        Session = sessionmaker(bind=engine, expire_on_commit=False)

        session = Session()
        yield session
        session.close()
