"""
TODO write this
"""
import logging
import marshmallow_dataclass as md
from itertools import takewhile

from originexample.db import inject_session
from originexample.tasks import celery_app, lock
from originexample.auth import User, UserQuery
from originexample.consuming import GgoConsumerProvider
from originexample.services.account import AccountService, Ggo, ComposeGgoRequest


provider = GgoConsumerProvider()
service = AccountService()

ggo_schema = md.class_schema(Ggo)()


def start_handle_ggo_received_pipeline(ggo, user):
    """
    :param Ggo ggo:
    :param User user:
    """
    handle_ggo_received \
        .s(ggo_schema.dump(ggo), user.id) \
        .apply_async()


@celery_app.task(bind=True, name='handle_ggo_received')
@inject_session
def handle_ggo_received(task, ggo_json, user_id, session):
    """
    TODO UNIQUE PER (ACCOUNT, BEGIN)

    :param celery.Task task:
    :param JSON ggo_json:
    :param int user_id:
    :param Session session:
    """
    # logging.info('--- handle_ggo_received, ggo.address = %s' % ggo_json['address'])

    ggo = ggo_schema.load(ggo_json)

    receiving_user = UserQuery(session) \
        .has_id(user_id) \
        .one()

    lock_key = '%s-%s' % (receiving_user.sub, ggo.begin)

    # This lock is in place to avoid timing issues when executing multiple
    # tasks for the same account at the same Ggo.begin, which can cause
    # the transferred or retired amount to exceed the allowed amount
    with lock(lock_key) as acquired:
        if not acquired:
            raise task.retry()

        request = ComposeGgoRequest(address=ggo.address)
        consumers = list(provider.get_consumers(receiving_user, ggo, session))
        remaining_amount = ggo.amount

        for consumer in takewhile(lambda _: remaining_amount > 0, consumers):

            desired_amount = consumer.get_desired_amount(ggo)
            assigned_amount = min(remaining_amount, desired_amount)
            remaining_amount -= assigned_amount

            logging.error(f'------------ consumer={consumer}, desired_amount={desired_amount}, assigned_amount={assigned_amount}, remaining_amount={remaining_amount}')

            if assigned_amount:
                logging.error('------------ Consume %d' % assigned_amount)
                consumer.consume(request, ggo, assigned_amount)

        if remaining_amount < ggo.amount:
            logging.error('------------ receiving_user.id = %d, receiving_user.access_token=%s' % (
                receiving_user.id, receiving_user.access_token
            ))
            service.compose(receiving_user.access_token, request)
