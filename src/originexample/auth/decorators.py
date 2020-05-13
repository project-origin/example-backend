from flask import request

from originexample.cache import redis
from originexample.db import inject_session
from originexample.http import Unauthorized
from originexample.settings import TOKEN_HEADER

from .models import User
from .queries import UserQuery


def inject_token(func):
    """
    Function decorator which injects a "token" named parameter
    if it doesn't already exists. The value is the authentication
    token provided by the client in a HTTP header.
    """
    def inject_user_wrapper(*args, **kwargs):
        kwargs['token'] = request.headers.get(TOKEN_HEADER)
        return func(*args, **kwargs)
    return inject_user_wrapper


def inject_user(func):
    """
    Function decorator which injects a "user" named parameter
    if it doesn't already exists. The value is a User object if
    possible, else None.

    Consumes the "token" parameter provided by previous @inject_token.
    """
    def inject_user_wrapper(*args, **kwargs):
        kwargs['user'] = _get_user()
        return func(*args, **kwargs)
    return inject_user_wrapper


def requires_login(func):
    """
    Function decorator which checks that a request contained
    a valid token, and that a user exists for that token.
    """
    @inject_user
    def requires_login_wrapper(*args, **kwargs):
        if not kwargs['user']:
            raise Unauthorized()
        return func(*args, **kwargs)
    return requires_login_wrapper


@inject_token
@inject_session
def _get_user(token, session):
    """
    :param str token:
    :param Session session:
    :rtype: User
    """
    if token:
        sub = redis.get(token)

        if sub:
            return UserQuery(session) \
                .has_sub(sub.decode()) \
                .one_or_none()
