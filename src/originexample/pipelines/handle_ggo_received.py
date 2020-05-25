"""
TODO write this
"""
import marshmallow_dataclass as md

from originexample import logger
from originexample.db import inject_session
from originexample.tasks import celery_app, lock
from originexample.auth import User, UserQuery
from originexample.consuming import GgoConsumerController
from originexample.services.account import Ggo


controller = GgoConsumerController()

ggo_schema = md.class_schema(Ggo)()


def start_handle_ggo_received_pipeline(ggo, user):
    """
    :param Ggo ggo:
    :param User user:
    """
    handle_ggo_received \
        .s(subject=user.sub, ggo_json=ggo_schema.dump(ggo)) \
        .apply_async()


@celery_app.task(
    bind=True,
    name='handle_ggo_received',
    autoretry_for=(Exception,),
    retry_backoff=2,
    max_retries=11,
)
@logger.wrap_task(
    title='Handling GGO received',
    pipeline='handle_ggo_received',
    task='handle_ggo_received',
)
@inject_session
def handle_ggo_received(task, subject, ggo_json, session):
    """
    TODO UNIQUE PER (ACCOUNT, BEGIN)

    :param celery.Task task:
    :param str subject:
    :param JSON ggo_json:
    :param Session session:
    """
    ggo = ggo_schema.load(ggo_json)

    user = UserQuery(session) \
        .has_sub(subject) \
        .one()

    lock_key = '%s-%s' % (subject, ggo.begin.strftime('%Y-%m-%d-%H-%M'))

    # This lock is in place to avoid timing issues when executing multiple
    # tasks for the same account at the same Ggo.begin, which can cause
    # the transferred or retired amount to exceed the allowed amount
    with lock(lock_key) as acquired:
        if not acquired:
            raise task.retry()

        controller.consume_ggo(user, ggo, session)
