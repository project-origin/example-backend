import sqlalchemy as sa

from originexample.auth import User
from originexample.services.account import Ggo
from originexample.facilities import get_technology

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

    def has_public_id(self, public_id):
        """
        :param str public_id:
        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.q.filter(
            TradeAgreement.public_id == public_id
        ))

    def belongs_to(self, user):
        """
        :param User user:
        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.q.filter(
            sa.or_(
                TradeAgreement.user_from_id == user.id,
                TradeAgreement.user_to_id == user.id
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
                TradeAgreement.user_to_id == user.id
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
                TradeAgreement.user_to_id == user.id
            ),
        ))

    def is_inbound_to(self, user):
        """
        :param User user:
        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.q.filter(
            TradeAgreement.user_to_id == user.id
        ))

    def is_outbound_from(self, user):
        """
        :param User user:
        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.q.filter(
            TradeAgreement.user_from_id == user.id
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

    def is_declined(self):
        """
        TODO unittest this

        :rtype: AgreementQuery
        """
        return AgreementQuery(self.session, self.q.filter(
            TradeAgreement.state == AgreementState.DECLINED,
        ))

    def is_active(self):
        """
        TODO Filter on dates?

        :rtype: AgreementQuery
        """
        return self.is_accepted()

    def is_elibigle_to_trade(self, ggo):
        """
        :param Ggo ggo:

        :rtype: AgreementQuery
        """
        technology = get_technology(ggo.technology_code, ggo.fuel_code)

        return AgreementQuery(self.session, self.q.filter(
            TradeAgreement.date_from <= ggo.begin.date(),
            TradeAgreement.date_to >= ggo.begin.date(),
            (TradeAgreement.technology == None) | (TradeAgreement.technology == technology),
        ))
