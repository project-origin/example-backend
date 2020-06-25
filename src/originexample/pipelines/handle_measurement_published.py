"""
TODO write this
"""
import marshmallow_dataclass as md
from datetime import datetime
from celery import group
from sqlalchemy import orm

from originexample import logger
from originexample.agreements import AgreementQuery
from originexample.db import inject_session
from originexample.services.datahub import Measurement
from originexample.tasks import celery_app
from originexample.auth import User, UserQuery
from originexample.services.account import (
    Ggo,
    GgoFilters,
    GgoCategory,
    GetGgoListRequest,
    AccountService,
    AccountServiceError,
)

from .handle_ggo_received import start_handle_ggo_received_pipeline


# Settings
RETRY_DELAY = 10
MAX_RETRIES = (24 * 60 * 60) / RETRY_DELAY
LOCK_TIMEOUT = 2 * 60


account_service = AccountService()

measurement_schema = md.class_schema(Measurement)()


def start_handle_measurement_published_pipeline(measurement, user):
    """
    :param Measurement measurement:
    :param User user:
    """
    handle_measurement_published \
        .s(
            subject=user.sub,
            measurement_json=measurement_schema.dump(measurement),
        ) \
        .apply_async()


@celery_app.task(
    bind=True,
    name='handle_measurement_published.handle_measurement_published',
    default_retry_delay=RETRY_DELAY,
    max_retries=MAX_RETRIES,
)
@logger.wrap_task(
    title='Handling Measurement published',
    pipeline='handle_measurement_published',
    task='handle_measurement_published',
)
@inject_session
def handle_measurement_published(task, subject, measurement_json, session):
    """
    :param celery.Task task:
    :param str subject:
    :param JSON measurement_json:
    :param Session session:
    """
    __log_extra = {
        'subject': subject,
        'measurement_json': str(measurement_json),
        'pipeline': 'handle_measurement_published',
        'task': 'handle_measurement_published',
    }

    measurement = measurement_schema.load(measurement_json)
    subjects = set()

    # Get User from database
    try:
        user = UserQuery(session) \
            .has_sub(subject) \
            .one()
    except orm.exc.NoResultFound:
        raise
    except Exception as e:
        logger.exception('Failed to load User from database, retrying...', extra=__log_extra)
        raise task.retry(exc=e)

    # Triggers handle_ggo_received for each GGO the user has stored (to retire)
    subjects.add(subject)

    # Get inbound agreements from database
    try:
        agreements = AgreementQuery(session) \
            .is_inbound_to(user) \
            .is_limited_to_consumption() \
            .is_operating_at(measurement.begin) \
            .is_active() \
            .all()
    except Exception as e:
        logger.exception('Failed to load Agreements from database, retrying...', extra=__log_extra)
        raise task.retry(exc=e)

    # Triggers handle_ggo_received for each GGO the outbound user
    # has stored (to transfer)
    for agreement in agreements:
        subjects.add(agreement.user_from.sub)

    # Start
    tasks = [
        trigger_handle_ggo_received_pipeline.si(
            subject=sub,
            begin=measurement.begin.isoformat(),
        )
        for sub in subjects
    ]

    group(*tasks).apply_async()


@celery_app.task(
    bind=True,
    name='handle_measurement_published.trigger_handle_ggo_received',
    default_retry_delay=RETRY_DELAY,
    max_retries=MAX_RETRIES,
)
@logger.wrap_task(
    title='Triggering pipeline handle_ggo_received for TradeAgreement',
    pipeline='handle_measurement_published',
    task='trigger_handle_ggo_received',
)
@inject_session
def trigger_handle_ggo_received_pipeline(task, subject, begin, session):
    """
    :param celery.Task task:
    :param str subject:
    :param str begin:
    :param Session session:
    """
    __log_extra = {
        'subject': subject,
        'begin': begin,
        'pipeline': 'handle_measurement_published',
        'task': 'handle_measurement_published',
    }

    begin_dt = datetime.fromisoformat(begin)

    # Get User from database
    try:
        user = UserQuery(session) \
            .has_sub(subject) \
            .one()
    except orm.exc.NoResultFound:
        raise
    except Exception as e:
        logger.exception('Failed to load User from database, retrying...', extra=__log_extra)
        raise task.retry(exc=e)

    # Get stored GGOs from AccountService
    try:
        stored_ggos = get_stored_ggos(user.access_token, begin_dt)
    except AccountServiceError as e:
        if e.status_code == 400:
            raise
        else:
            logger.exception('Failed to get GGO list, retrying...', extra=__log_extra)
            raise task.retry(exc=e)
    except Exception as e:
        logger.exception('Failed to get GGO list, retrying...', extra=__log_extra)
        raise task.retry(exc=e)

    # Trigger handle_ggo_received pipeline for each stored GGO
    for ggo in stored_ggos:
        start_handle_ggo_received_pipeline(ggo, user)


# -- Helper functions --------------------------------------------------------


def get_stored_ggos(token, begin):
    """
    :param str token:
    :param datetime.datetime begin:
    :rtype: list[Ggo]
    """
    request = GetGgoListRequest(filters=GgoFilters(
        begin=begin,
        category=GgoCategory.STORED,
    ))
    response = account_service.get_ggo_list(token, request)
    return response.results
