"""
TODO write this
"""
from datetime import datetime, timezone
from celery import group

from originexample import logger
from originexample.db import inject_session, atomic
from originexample.auth import UserQuery, AuthBackend
from originexample.tasks import celery_app


backend = AuthBackend()


@celery_app.task(
    name='refresh_token.get_soon_to_expire_tokens',
    autoretry_for=(Exception,),
    retry_backoff=2,
    max_retries=5,
)
@logger.wrap_task(
    title='Getting soon-to-expire tokens',
    pipeline='refresh_token',
    task='get_soon_to_expire_tokens',
)
@inject_session
def get_soon_to_expire_tokens(session):
    """
    :param Session session:
    """
    users = UserQuery(session) \
        .should_refresh_token()

    tasks = [refresh_token.si(subject=user.sub) for user in users]

    group(*tasks).apply_async()


@celery_app.task(
    name='refresh_token.refresh_token_for_user',
    autoretry_for=(Exception,),
    retry_backoff=2,
    max_retries=5,
)
@logger.wrap_task(
    title='Refreshing user\'s refresh_token',
    pipeline='refresh_token',
    task='refresh_token',
)
@atomic
def refresh_token(subject, session):
    """
    :param str subject:
    :param Session session:
    """
    user = UserQuery(session) \
        .has_sub(subject) \
        .one()

    token = backend.refresh_token(user.refresh_token)

    user.access_token = token['access_token']
    user.refresh_token = token['refresh_token']
    user.token_expire = datetime \
        .fromtimestamp(token['expires_at']) \
        .replace(tzinfo=timezone.utc)
