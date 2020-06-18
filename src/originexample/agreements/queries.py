import sqlalchemy as sa
from sqlalchemy import text

from originexample.auth import User
from originexample.services.account import Ggo

from .models import TradeAgreement, AgreementState


class AgreementQuery(object):
    """
    TODO
    """
    def __init__(self, session, q=None):
        """
        :param Session session:
        :param AgreementQuery q:
        """
        self.session = session
        if q is None:
            self.q = session.query(TradeAgreement)
        else:
            self.q = q

    def __iter__(self):
        return iter(self.q)

    def __getattr__(self, name):
        return getattr(self.q, name)

    def has_id(self, agreement_id):
        """
        TODO unittest this

        :param int agreement_id:
        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.q.filter(
            TradeAgreement.id == agreement_id,
        ))

    def has_public_id(self, public_id):
        """
        :param str public_id:
        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.q.filter(
            TradeAgreement.public_id == public_id,
        ))

    def belongs_to(self, user):
        """
        :param User user:
        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.q.filter(
            sa.or_(
                TradeAgreement.user_from_id == user.id,
                TradeAgreement.user_to_id == user.id,
            ),
        ))

    def is_proposed_by(self, user):
        """
        :param User user:
        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.q.filter(
            TradeAgreement.user_proposed_id == user.id,
        ))

    def is_proposed_to(self, user):
        """
        :param User user:
        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.q.filter(
            TradeAgreement.user_proposed_id != user.id,
            sa.or_(
                TradeAgreement.user_from_id == user.id,
                TradeAgreement.user_to_id == user.id,
            ),
        ))

    def is_awaiting_response_by(self, user):
        """
        :param User user:
        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.q.filter(
            TradeAgreement.state == AgreementState.PENDING,
            TradeAgreement.user_proposed_id != user.id,
            sa.or_(
                TradeAgreement.user_from_id == user.id,
                TradeAgreement.user_to_id == user.id,
            ),
        ))

    def is_inbound_to(self, user):
        """
        :param User user:
        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.q.filter(
            TradeAgreement.user_to_id == user.id,
        ))

    def is_outbound_from(self, user):
        """
        :param User user:
        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.q.filter(
            TradeAgreement.user_from_id == user.id,
        ))

    def is_pending(self):
        """
        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.q.filter(
            TradeAgreement.state == AgreementState.PENDING,
        ))

    def is_accepted(self):
        """
        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.q.filter(
            TradeAgreement.state == AgreementState.ACCEPTED,
        ))

    def is_cancelled(self):
        """
        TODO unittest this

        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.q.filter(
            TradeAgreement.state == AgreementState.CANCELLED,
        ))

    def is_cancelled_recently(self):
        """
        TODO unittest this

        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.q.filter(
            TradeAgreement.cancelled >= text("NOW() - INTERVAL '14 DAYS'"),
        ))

    def is_declined(self):
        """
        TODO unittest this

        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.q.filter(
            TradeAgreement.state == AgreementState.DECLINED,
        ))

    def is_declined_recently(self):
        """
        TODO unittest this

        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.q.filter(
            TradeAgreement.declined >= text("NOW() - INTERVAL '14 DAYS'"),
        ))

    def is_limited_to_consumption(self):
        """
        TODO unittest this

        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.q.filter(
            TradeAgreement.limit_to_consumption.is_(True),
        ))

    def is_active(self):
        """
        :rtype: AgreementQuery
        """
        return self.is_accepted()

    def is_operating_at(self, begin):
        """
        TODO unittest this

        :param datetime.datetime begin:
        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.q.filter(
            TradeAgreement.date_from <= begin.date(),
            TradeAgreement.date_to >= begin.date(),
        ))

    def is_elibigle_to_trade(self, ggo):
        """
        :param Ggo ggo:

        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.q.filter(
            TradeAgreement.date_from <= ggo.begin.date(),
            TradeAgreement.date_to >= ggo.begin.date(),
            sa.or_(
                TradeAgreement.technology.is_(None),
                TradeAgreement.technology == ggo.technology,
            ),
        ))
