"""
TODO write this
"""
import marshmallow_dataclass as md
from sqlalchemy import orm

from originexample import logger
from originexample.db import inject_session
from originexample.tasks import celery_app, lock
from originexample.auth import User, UserQuery
from originexample.consuming import GgoConsumerController
from originexample.services.account import (
    Ggo,
    GgoFilters,
    GgoCategory,
    GetGgoListRequest,
    AccountService,
    AccountServiceError,
)

RETRY_DELAY = 10
MAX_RETRIES = (24 * 60 * 60) / RETRY_DELAY
LOCK_TIMEOUT = 2 * 60


controller = GgoConsumerController()
account_service = AccountService()

ggo_schema = md.class_schema(Ggo)()


def start_handle_ggo_received_pipeline(ggo, user):
    """
    :param Ggo ggo:
    :param User user:
    """
    handle_ggo_received \
        .s(
            subject=user.sub,
            ggo_json=ggo_schema.dump(ggo),
            address=ggo.address,
        ) \
        .apply_async()


@celery_app.task(
    bind=True,
    name='handle_ggo_received.handle_ggo_received',
    default_retry_delay=RETRY_DELAY,
    max_retries=MAX_RETRIES,
)
@logger.wrap_task(
    title='Handling GGO received',
    pipeline='handle_ggo_received',
    task='handle_ggo_received',
)
@inject_session
def handle_ggo_received(task, subject, address, ggo_json, session):
    """
    :param celery.Task task:
    :param str subject:
    :param str address:
    :param JSON ggo_json:
    :param Session session:
    """
    __log_extra = {
        'subject': subject,
        'address': address,
        'ggo': str(ggo_json),
        'pipeline': 'handle_ggo_received',
        'task': 'handle_ggo_received',
    }

    ggo = ggo_schema.load(ggo_json)

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

    lock_key = ggo.begin.strftime('%Y-%m-%d-%H-%M')

    # This lock is in place to avoid timing issues when executing multiple
    # tasks for the same account at the same time, which can cause
    # the transferred or retired amount to exceed the allowed amount
    with lock(lock_key, timeout=LOCK_TIMEOUT) as acquired:
        if not acquired:
            logger.debug('Could not acquire lock, retrying...', extra=__log_extra)
            raise task.retry()

        try:
            if not ggo_is_available(user.access_token, ggo):
                logger.info('GGO is unavailable, skipping', extra=__log_extra)
                return

            controller.consume_ggo(user, ggo, session)
        except AccountServiceError as e:
            if e.status_code == 400:
                raise
            else:
                logger.exception('Failed to consume GGO, retrying...', extra=__log_extra)
                raise task.retry(exc=e)
        except Exception as e:
            logger.exception('Failed to consume GGO, retrying...', extra=__log_extra)
            raise task.retry(exc=e)


# -- Helper functions --------------------------------------------------------


def ggo_is_available(token, ggo):
    """
    Check whether a GGO is available for transferring/retiring.

    :param str token:
    :param Ggo ggo:
    :rtype: bool
    """
    request = GetGgoListRequest(
        filters=GgoFilters(
            address=[ggo.address],
            category=GgoCategory.STORED,
        )
    )
    response = account_service.get_ggo_list(token, request)
    return len(response.results) > 0
