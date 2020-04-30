"""
TODO
"""
import marshmallow_dataclass as md
from datetime import datetime
from celery import group

from originexample import logger
from originexample.db import inject_session
from originexample.tasks import celery_app
from originexample.auth import User, UserQuery
from originexample.consuming import GgoConsumerProvider
from originexample.services.account import (
    AccountService,
    Ggo,
    GetGgoListRequest,
    GgoFilters,
    GgoCategory,
    DateTimeRange,
)

from .handle_ggo_received import handle_ggo_received


provider = GgoConsumerProvider()
service = AccountService()

ggo_schema = md.class_schema(Ggo)()


def start_consume_back_in_time_pipeline(user, begin_from, begin_to):
    """
    :param User user:
    :param datetime begin_from:
    :param datetime begin_to:
    """
    consume_back_in_time \
        .s(
            subject=user.sub,
            begin_from=begin_from.isoformat(),
            begin_to=begin_to.isoformat(),
        ) \
        .apply_async()


@celery_app.task(
    name='consume_back_in_time.consume_back_in_time',
)
@logger.wrap_task(
    pipeline='consume_back_in_time',
    task='consume_back_in_time',
)
@inject_session
def consume_back_in_time(subject, begin_from, begin_to, session):
    """
    TODO UNIQUE PER (ACCOUNT, BEGIN)

    :param str subject:
    :param str begin_from:
    :param str begin_to:
    :param Session session:
    """
    user = UserQuery(session) \
        .has_sub(subject) \
        .one()

    filters = GgoFilters(
        category=GgoCategory.STORED,
        begin_range=DateTimeRange(
            begin=datetime.fromisoformat(begin_from),
            end=datetime.fromisoformat(begin_to),
        )
    )

    tasks = []
    offset = 0
    limit = 100

    while 1:
        response = service.get_ggo_list(user.access_token, GetGgoListRequest(
            offset=offset,
            limit=limit,
            filters=filters,
        ))

        for ggo in response.results:
            tasks.append(handle_ggo_received.s(
                subject=user.sub,
                ggo_json=ggo_schema.dump(ggo),
            ))

        offset += limit

        if offset >= response.total:
            break

    if tasks:
        group(*tasks).apply_async()
