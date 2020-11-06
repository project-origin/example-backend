from marshmallow.exceptions import ValidationError

from originexample.db import inject_session

from .queries import UserQuery


@inject_session
def user_public_id_exists(public_id, session, *args, **kwargs):
    """
    Validates that a list of items are unique,
    ie. no value are present more than once.
    """
    user = UserQuery(session) \
        .is_active() \
        .has_public_id(public_id) \
        .one_or_none()

    if user is None:
        raise ValidationError('No user exists with ID: %s' % public_id)
