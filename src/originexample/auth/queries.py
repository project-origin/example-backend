from sqlalchemy import or_
from datetime import datetime, timezone

from .models import User
from ..settings import TOKEN_REFRESH_AT


class UserQuery(object):
    """
    TODO
    """
    def __init__(self, session, q=None):
        """
        :param Session session:
        :param UserQuery q:
        """
        self.session = session
        if q is None:
            self.q = session.query(User)
        else:
            self.q = q

    def __iter__(self):
        return iter(self.q)

    def __getattr__(self, name):
        return getattr(self.q, name)

    def exclude(self, user):
        """
        :param User user:
        :rtype: UserQuery
        """
        return UserQuery(self.session, self.q.filter(
            User.sub != user.sub,
        ))

    def is_active(self):
        """
        :rtype: UserQuery
        """
        return UserQuery(self.session, self.q.filter(
            User.disabled.is_(False),
        ))

    def has_id(self, id):
        """
        :param int id:
        :rtype: UserQuery
        """
        return UserQuery(self.session, self.q.filter(
            User.id == id,
        ))

    def has_sub(self, sub):
        """
        :param str sub:
        :rtype: UserQuery
        """
        return UserQuery(self.session, self.q.filter(
            User.sub == sub,
        ))

    def has_public_id(self, public_id):
        """
        :param str public_id:
        :rtype: UserQuery
        """
        return UserQuery(self.session, self.q.filter(
            User.sub == public_id,
        ))

    def starts_with(self, query):
        """
        :param str query:
        :rtype: UserQuery
        """
        return UserQuery(self.session, self.q.filter(
            or_(
                User.name.ilike('%s%%' % query),
                User.company.ilike('%s%%' % query),
            )
        ))

    def should_refresh_token(self):
        """
        :rtype: UserQuery
        """
        return UserQuery(self.session, self.q.filter(
            User.token_expire <= datetime.now(tz=timezone.utc) + TOKEN_REFRESH_AT,
        ))
