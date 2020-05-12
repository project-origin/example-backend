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
    max_retries=5,
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

        # request = ComposeGgoRequest(address=ggo.address)
        # consumers = list(provider.get_consumers(receiving_user, ggo, session))
        # remaining_amount = ggo.amount
        #
        # for consumer in takewhile(lambda _: remaining_amount > 0, consumers):
        #     desired_amount = consumer.get_desired_amount(ggo)
        #     assigned_amount = min(remaining_amount, desired_amount)
        #     remaining_amount -= assigned_amount
        #
        #     if assigned_amount:
        #         consumer.consume(request, ggo, assigned_amount)
        #
        # if remaining_amount < ggo.amount:
        #     logger.info('Composing a new GGO split', extra={
        #         'subject': subject,
        #         'address': ggo.address,
        #         'begin': str(ggo.begin),
        #     })
        #     service.compose(receiving_user.access_token, request)
