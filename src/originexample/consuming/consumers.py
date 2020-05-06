from itertools import takewhile

from originexample import logger
from originexample.auth import User
from originexample.agreements import TradeAgreement, AgreementQuery
from originexample.facilities import Facility, FacilityQuery
from originexample.services.datahub import DataHubService, GetMeasurementRequest
from originexample.services.account import (
    AccountService,
    TransferFilters,
    TransferDirection,
    TransferRequest,
    RetireFilters,
    RetireRequest,
    ComposeGgoRequest,
    GetTransferredAmountRequest,
    GetRetiredAmountRequest,
    Ggo,
)


account = AccountService()
datahub = DataHubService()


class GgoConsumerController(object):
    """
    TODO
    """
    def get_consumers(self, user, ggo, session):
        """
        :param User user:
        :param Ggo ggo:
        :param Session session:
        :rtype: collections.abc.Iterable[GgoConsumer]
        """
        facilities = FacilityQuery(session) \
            .belongs_to(user) \
            .is_retire_receiver() \
            .is_eligible_to_retire(ggo) \
            .order_by(Facility.retiring_priority.asc())

        yield from map(self.build_retire_consumer, facilities)

        agreements = AgreementQuery(session) \
            .is_outbound_from(user) \
            .is_elibigle_to_trade(ggo) \
            .is_active()

        yield from map(self.build_agreement_consumer, agreements)

    def build_retire_consumer(self, facility):
        """
        :param Facility facility:
        :rtype: GgoConsumer
        """
        return RetiringConsumer(facility)

    def build_agreement_consumer(self, agreement):
        """
        :param TradeAgreement agreement:
        :rtype: GgoConsumer
        """
        return AgreementConsumer(agreement)

    def consume_ggo(self, user, ggo, session):
        """
        :param User user:
        :param Ggo ggo:
        :param Session session:
        """
        request = ComposeGgoRequest(address=ggo.address)
        consumers = list(self.get_consumers(user, ggo, session))
        remaining_amount = ggo.amount

        for consumer in takewhile(lambda _: remaining_amount > 0, consumers):
            desired_amount = consumer.get_desired_amount(ggo)
            assigned_amount = min(remaining_amount, desired_amount)
            remaining_amount -= assigned_amount

            if assigned_amount:
                consumer.consume(request, ggo, assigned_amount)

        if remaining_amount < ggo.amount:
            logger.info('Composing a new GGO split', extra={
                'subject': user.sub,
                'address': ggo.address,
                'begin': str(ggo.begin),
            })

            account.compose(user.access_token, request)


class GgoConsumer(object):
    """
    TODO
    """
    def get_desired_amount(self, ggo):
        """
        :param Ggo ggo:
        :rtype: int
        """
        raise NotImplementedError

    def consume(self, request, ggo, amount):
        """
        :param ComposeGgoRequest request:
        :param Ggo ggo:
        :param int amount:
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
        self.gsrn = facility.gsrn
        self.token = facility.user.access_token

    def __str__(self):
        return 'RetiringConsumer<%s>' % self.gsrn

    def get_desired_amount(self, ggo):
        """
        :rtype: int
        """
        measurement = self.get_measurement(self.gsrn, ggo.begin)
        if measurement:
            retired_amount = self.get_retired_amount(measurement)
            remaining_amount = measurement.amount - retired_amount
            desired_amount = min(remaining_amount, ggo.amount)
            return max(0, desired_amount)
        else:
            return 0

    def consume(self, request, ggo, amount):
        """
        :param ComposeGgoRequest request:
        :param Ggo ggo:
        :param int amount:
        """
        request.retires.append(RetireRequest(
            amount=amount,
            gsrn=self.gsrn,
        ))

    def get_measurement(self, gsrn, begin):
        """
        :param str gsrn:
        :param datetime.datetime begin:
        :rtype: Measurement
        """
        request = GetMeasurementRequest(gsrn=gsrn, begin=begin)
        response = datahub.get_consumption(self.token, request)
        return response.measurement

    def get_retired_amount(self, measurement):
        """
        :param Measurement measurement:
        :rtype: int
        """
        filters = RetireFilters(
            address=[measurement.address],
            retire_gsrn=[self.gsrn],
        )
        request = GetRetiredAmountRequest(filters=filters)
        response = account.get_retired_amount(self.token, request)

        return response.amount


class AgreementConsumer(GgoConsumer):
    """
    TODO
    """
    def __init__(self, agreement):
        """
        :param TradeAgreement agreement:
        """
        self.amount = agreement.calculated_amount
        self.reference = agreement.public_id
        self.receiver_sub = agreement.user_to.sub
        self.token = agreement.user_from.access_token

    def __str__(self):
        return 'AgreementConsumer<%s>' % self.reference

    def get_desired_amount(self, ggo):
        """
        :param Ggo ggo:
        :rtype: int
        """
        transferred_amount = self.get_transferred_amount(ggo.begin)
        desired_amount = min(self.amount - transferred_amount, ggo.amount)
        return max(0, desired_amount)

    def consume(self, request, ggo, amount):
        """
        :param ComposeGgoRequest request:
        :param Ggo ggo:
        :param int amount:
        """
        request.transfers.append(TransferRequest(
            amount=amount,
            reference=self.reference,
            sub=self.receiver_sub,
        ))

    def get_transferred_amount(self, begin):
        """
        :param datetime.datetime begin:
        :rtype: int
        """
        request = GetTransferredAmountRequest(
            direction=TransferDirection.OUTBOUND,
            filters=TransferFilters(
                reference=[self.reference],
                begin=begin,
            )
        )

        response = account.get_transferred_amount(self.token, request)

        return response.amount
