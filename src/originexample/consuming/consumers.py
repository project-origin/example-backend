from itertools import takewhile

from originexample import logger
from originexample.auth import User
from originexample.agreements import TradeAgreement, AgreementQuery
from originexample.facilities import Facility, FacilityQuery
from originexample.consuming.helpers import (
    get_consumption,
    get_retired_amount,
    get_transferred_amount,
    get_stored_amount,
)
from originexample.services.account import (
    Ggo,
    AccountService,
    TransferRequest,
    RetireRequest,
    ComposeGgoRequest,
)


account_service = AccountService()


class GgoConsumerController(object):
    """
    TODO
    """

    def get_consumers(self, user, ggo, session):
        """
        :param User user:
        :param Ggo ggo:
        :param sqlalchemy.orm.Session session:
        :rtype: collections.abc.Iterable[GgoConsumer]
        """
        yield from self.get_retire_consumers(user, ggo, session)
        yield from self.get_agreement_consumers(user, ggo, session)

    def get_retire_consumers(self, user, ggo, session):
        """
        TODO test this

        :param User user:
        :param Ggo ggo:
        :param sqlalchemy.orm.Session session:
        :rtype: collections.abc.Iterable[RetiringConsumer]
        """
        facilities = FacilityQuery(session) \
            .belongs_to(user) \
            .is_retire_receiver() \
            .is_eligible_to_retire(ggo) \
            .order_by(Facility.retiring_priority.asc()) \
            .all()

        for facility in facilities:
            yield RetiringConsumer(facility)

    def get_agreement_consumers(self, user, ggo, session):
        """
        TODO test this

        :param User user:
        :param Ggo ggo:
        :param sqlalchemy.orm.Session session:
        :rtype: collections.abc.Iterable[AgreementConsumer]
        """
        agreements = AgreementQuery(session) \
            .is_outbound_from(user) \
            .is_elibigle_to_trade(ggo) \
            .is_operating_at(ggo.begin) \
            .is_active() \
            .order_by(TradeAgreement.transfer_priority.asc()) \
            .all()

        # TODO test query ordering (transfer_priority)

        for agreement in agreements:
            if agreement.limit_to_consumption:
                yield AgreementLimitedToConsumptionConsumer(agreement, session)
            else:
                yield AgreementConsumer(agreement)

    def consume_ggo(self, user, ggo, session):
        """
        :param User user:
        :param Ggo ggo:
        :param Session session:
        """
        request = ComposeGgoRequest(address=ggo.address)
        consumers = self.get_consumers(user, ggo, session)
        remaining_amount = ggo.amount

        for consumer in takewhile(lambda _: remaining_amount > 0, consumers):
            already_transferred = ggo.amount - remaining_amount

            desired_amount = consumer.get_desired_amount(
                ggo, already_transferred)

            assigned_amount = min(remaining_amount, desired_amount)
            remaining_amount -= assigned_amount

            if assigned_amount > 0:
                consumer.consume(request, ggo, assigned_amount)

        if remaining_amount < ggo.amount:
            logger.info('Composing a new GGO split', extra={
                'subject': user.sub,
                'address': ggo.address,
                'begin': str(ggo.begin),
            })

            account_service.compose(user.access_token, request)


class GgoConsumer(object):
    """
    TODO
    """
    def consume(self, request, ggo, amount):
        """
        :param ComposeGgoRequest request:
        :param Ggo ggo:
        :param int amount:
        """
        raise NotImplementedError

    def get_desired_amount(self, ggo, already_transferred):
        """
        :param Ggo ggo:
        :param int already_transferred:
        :rtype: int
        """
        raise NotImplementedError


class RetiringConsumer(GgoConsumer):
    """
    TODO
    """
    def __init__(self, facility):
        """
        :param Facility facility:
        """
        self.facility = facility

    def __str__(self):
        return 'RetiringConsumer<%s>' % self.facility.gsrn

    def consume(self, request, ggo, amount):
        """
        :param ComposeGgoRequest request:
        :param Ggo ggo:
        :param int amount:
        """
        request.retires.append(RetireRequest(
            amount=amount,
            gsrn=self.facility.gsrn,
        ))

    def get_desired_amount(self, ggo, already_transferred):
        """
        :param Ggo ggo:
        :param int already_transferred:
        :rtype: int
        """
        measurement = get_consumption(
            token=self.facility.user.access_token,
            gsrn=self.facility.gsrn,
            begin=ggo.begin,
        )

        if measurement is None:
            return 0

        retired_amount = get_retired_amount(
            token=self.facility.user.access_token,
            gsrn=self.facility.gsrn,
            measurement=measurement,
        )

        desired_amount = measurement.amount - retired_amount

        return max(0, min(ggo.amount, desired_amount))


class AgreementConsumer(GgoConsumer):
    """
    TODO
    """
    def __init__(self, agreement):
        """
        :param TradeAgreement agreement:
        """
        self.agreement = agreement
        self.reference = agreement.public_id

    def __str__(self):
        return 'AgreementConsumer<%s>' % self.reference

    def consume(self, request, ggo, amount):
        """
        :param ComposeGgoRequest request:
        :param Ggo ggo:
        :param int amount:
        """
        request.transfers.append(TransferRequest(
            amount=amount,
            reference=self.reference,
            account=self.agreement.user_to.sub,
        ))

    def get_desired_amount(self, ggo, already_transferred):
        """
        :param Ggo ggo:
        :param int already_transferred:
        :rtype: int
        """
        transferred_amount = get_transferred_amount(
            token=self.agreement.user_from.access_token,
            reference=self.reference,
            begin=ggo.begin,
        )

        desired_amount = self.agreement.calculated_amount - transferred_amount

        return max(0, min(ggo.amount, desired_amount))


class AgreementLimitedToConsumptionConsumer(AgreementConsumer):
    """
    TODO
    """
    def __init__(self, agreement, session):
        """
        :param TradeAgreement agreement:
        :param sqlalchemy.orm.Session session:
        """
        super(AgreementLimitedToConsumptionConsumer, self).__init__(agreement)
        self.session = session

    def __str__(self):
        return 'AgreementLimitedToConsumptionConsumer<%s>' % self.reference

    def get_desired_amount(self, ggo, already_transferred):
        """
        :param Ggo ggo:
        :param int already_transferred:
        :rtype: int
        """
        remaining_amount = super(AgreementLimitedToConsumptionConsumer, self) \
            .get_desired_amount(ggo, already_transferred)

        if remaining_amount <= 0:
            return 0

        desired_amount = 0

        # TODO takewhile desired_amount < min(ggo.amount, remaining_amount)
        for facility in self.get_facilities(ggo):
            desired_amount += self.get_desired_amount_for_facility(
                facility=facility,
                begin=ggo.begin,
            )

        desired_amount -= already_transferred
        desired_amount -= get_stored_amount(
            token=self.agreement.user_to.access_token,
            begin=ggo.begin,
        )

        return max(0, min(ggo.amount, remaining_amount, desired_amount))

    def get_desired_amount_for_facility(self, facility, begin):
        """
        :param Facility facility:
        :param datetime.datetime begin:
        :rtype: int
        """
        measurement = get_consumption(
            token=facility.user.access_token,
            gsrn=facility.gsrn,
            begin=begin,
        )

        if measurement is None:
            return 0

        retired_amount = get_retired_amount(
            token=facility.user.access_token,
            gsrn=facility.gsrn,
            measurement=measurement,
        )

        remaining_amount = measurement.amount - retired_amount

        return max(0, remaining_amount)

    def get_facilities(self, ggo):
        """
        :param Ggo ggo:
        :rtype: list[Facility]
        """
        return FacilityQuery(self.session) \
            .belongs_to(self.agreement.user_to) \
            .is_retire_receiver() \
            .is_eligible_to_retire(ggo) \
            .all()
