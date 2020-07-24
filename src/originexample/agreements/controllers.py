import csv
import marshmallow_dataclass as md
from io import StringIO
from datetime import datetime, timedelta
from functools import partial
from flask import make_response

from originexample import logger
from originexample.auth import User, UserQuery, requires_login
from originexample.db import inject_session, atomic
from originexample.http import Controller
from originexample.facilities import Facility, FacilityQuery
from originexample.common import DateTimeRange, DataSet
from originexample.pipelines import start_consume_back_in_time_pipeline
from originexample.services.account import (
    AccountService,
    SummaryResolution,
    SummaryGrouping,
    TransferFilters,
    TransferDirection,
    GetTransferSummaryRequest,
)

from .queries import AgreementQuery
from .models import (
    TradeAgreement,
    MappedTradeAgreement,
    AgreementDirection,
    AgreementState,
    GetAgreementListResponse,
    GetAgreementSummaryRequest,
    GetAgreementSummaryResponse,
    SubmitAgreementProposalRequest,
    SubmitAgreementProposalResponse,
    RespondToProposalRequest,
    RespondToProposalResponse,
    CountPendingProposalsResponse,
    WithdrawProposalRequest,
    WithdrawProposalResponse,
    GetAgreementDetailsRequest,
    GetAgreementDetailsResponse,
    CancelAgreementRequest,
    SetTransferPriorityRequest,
)


account = AccountService()


# -- Helpers -----------------------------------------------------------------


def get_resolution(delta):
    """
    TODO write me

    :param timedelta delta:
    :rtype: SummaryResolution
    """
    if delta.days >= (365 * 3):
        return SummaryResolution.YEAR
    elif delta.days >= 60:
        return SummaryResolution.MONTH
    elif delta.days >= 3:
        return SummaryResolution.DAY
    else:
        return SummaryResolution.HOUR


def update_transfer_priorities(user, session):
    """
    TODO write me

    :param User user:
    :param sqlalchemy.orm.Session session:
    """
    session.execute("""
        update agreements_agreement
        set transfer_priority = s.row_number - 1
        from (
            select a.id, row_number() over (
                partition by a.user_from_id
                order by a.transfer_priority asc
            )
          from agreements_agreement as a
          where a.state = 'ACCEPTED'
          order by a.transfer_priority asc
        ) as s
        where agreements_agreement.id = s.id
        and agreements_agreement.user_from_id = :user_from_id
    """, {'user_from_id': user.id})


# -- Controllers -------------------------------------------------------------


class AbstractAgreementController(Controller):
    def map_agreement_for(self, user, agreement):
        """
        :param TradeAgreement agreement:
        :param User user:
        :rtype: MappedTradeAgreement
        """
        if agreement.is_inbound_to(user):
            return self.map_inbound_agreement(agreement)
        elif agreement.is_outbound_from(user):
            return self.map_outbound_agreement(agreement)
        else:
            raise RuntimeError('This should NOT have happened!')

    def map_inbound_agreement(self, agreement):
        """
        :param TradeAgreement agreement:
        :rtype: MappedTradeAgreement
        """
        return MappedTradeAgreement(
            direction=AgreementDirection.INBOUND,
            state=agreement.state,
            public_id=agreement.public_id,
            counterpart_id=agreement.user_from.sub,
            counterpart=agreement.user_from.name,
            date_from=agreement.date_from,
            date_to=agreement.date_to,
            amount=agreement.amount,
            unit=agreement.unit,
            technology=agreement.technology,
            reference=agreement.reference,
            limit_to_consumption=agreement.limit_to_consumption,
        )

    def map_outbound_agreement(self, agreement):
        """
        :param TradeAgreement agreement:
        :rtype: MappedTradeAgreement
        """
        return MappedTradeAgreement(
            direction=AgreementDirection.OUTBOUND,
            state=agreement.state,
            public_id=agreement.public_id,
            counterpart_id=agreement.user_to.sub,
            counterpart=agreement.user_to.name,
            date_from=agreement.date_from,
            date_to=agreement.date_to,
            amount=agreement.amount,
            unit=agreement.unit,
            technology=agreement.technology,
            reference=agreement.reference,
            facilities=list(agreement.facilities),
            limit_to_consumption=agreement.limit_to_consumption,
        )


class GetAgreementList(AbstractAgreementController):
    """
    TODO
    """
    Response = md.class_schema(GetAgreementListResponse)

    @requires_login
    @inject_session
    def handle_request(self, user, session):
        """
        :param User user:
        :param Session session:
        :rtype: GetAgreementListResponse
        """

        # Invitations currently awaiting response by this user
        pending = AgreementQuery(session) \
            .is_proposed_to(user) \
            .is_pending() \
            .order_by(TradeAgreement.created.asc()) \
            .all()

        # Invitations sent by this user awaiting response by another user
        sent = AgreementQuery(session) \
            .is_proposed_by(user) \
            .is_pending() \
            .order_by(TradeAgreement.created.asc()) \
            .all()

        # Inbound agreements currently active
        inbound = AgreementQuery(session) \
            .is_inbound_to(user) \
            .is_accepted() \
            .order_by(TradeAgreement.created.asc()) \
            .all()

        # Outbound agreements currently active
        outbound = AgreementQuery(session) \
            .is_outbound_from(user) \
            .is_accepted() \
            .order_by(TradeAgreement.transfer_priority.asc()) \
            .all()

        # Formerly accepted agreements which has now been cancelled
        cancelled = AgreementQuery(session) \
            .belongs_to(user) \
            .is_cancelled() \
            .is_cancelled_recently() \
            .order_by(TradeAgreement.cancelled.desc()) \
            .all()

        # Formerly proposed agreements which has now been declined
        declined = AgreementQuery(session) \
            .belongs_to(user) \
            .is_declined() \
            .is_declined_recently() \
            .order_by(TradeAgreement.declined.desc()) \
            .all()

        map_agreement = partial(self.map_agreement_for, user)

        return GetAgreementListResponse(
            success=True,
            pending=list(map(map_agreement, pending)),
            sent=list(map(map_agreement, sent)),
            inbound=list(map(map_agreement, inbound)),
            outbound=list(map(map_agreement, outbound)),
            cancelled=list(map(map_agreement, cancelled)),
            declined=list(map(map_agreement, declined)),
        )


class GetAgreementDetails(AbstractAgreementController):
    """
    TODO
    """
    Request = md.class_schema(GetAgreementDetailsRequest)
    Response = md.class_schema(GetAgreementDetailsResponse)

    @requires_login
    @inject_session
    def handle_request(self, request, user, session):
        """
        :param GetAgreementDetailsRequest request:
        :param User user:
        :param Session session:
        :rtype: GetAgreementDetailsResponse
        """
        agreement = AgreementQuery(session) \
            .has_public_id(request.public_id) \
            .belongs_to(user) \
            .one_or_none()

        if agreement:
            agreement = self.map_agreement_for(user, agreement)

        return GetAgreementDetailsResponse(
            success=agreement is not None,
            agreement=agreement,
        )


class GetAgreementSummary(AbstractAgreementController):
    """
    TODO
    """
    Request = md.class_schema(GetAgreementSummaryRequest)
    Response = md.class_schema(GetAgreementSummaryResponse)

    @requires_login
    @inject_session
    def handle_request(self, request, user, session):
        """
        :param GetAgreementSummaryRequest request:
        :param User user:
        :param Session session:
        :rtype: GetAgreementListResponse
        """
        agreement = None

        if request.date_range:
            resolution = get_resolution(request.date_range.delta)
        else:
            resolution = SummaryResolution.MONTH

        if request.public_id:
            agreement = AgreementQuery(session) \
                .has_public_id(request.public_id) \
                .belongs_to(user) \
                .one_or_none()

        if request.direction is AgreementDirection.INBOUND:
            direction = TransferDirection.INBOUND
        elif request.direction is AgreementDirection.OUTBOUND:
            direction = TransferDirection.OUTBOUND
        else:
            direction = None

        ggos, labels = self.get_agreement_summary(
            request=request,
            token=user.access_token,
            resolution=resolution,
            utc_offset=request.utc_offset,
            direction=direction,
            reference=agreement.public_id if agreement else None,
        )

        return GetAgreementSummaryResponse(
            success=True,
            labels=labels,
            ggos=ggos,
        )

    def get_agreement_summary(self, request, token, resolution, utc_offset,
                              direction=None, reference=None):
        """
        :param GetMeasurementsRequest request:
        :param str token:
        :param SummaryResolution resolution:
        :param int utc_offset:
        :param TransferDirection direction:
        :param str reference:
        :rtype: (list[DataSet], list[str])
        """
        if request.date_range:
            begin_range = DateTimeRange.from_date_range(request.date_range)
            fill = True
        else:
            begin_range = None
            fill = False

        response = account.get_transfer_summary(token, GetTransferSummaryRequest(
            direction=direction,
            resolution=resolution,
            utc_offset=utc_offset,
            fill=fill,
            grouping=[SummaryGrouping.TECHNOLOGY],
            filters=TransferFilters(
                reference=[reference] if reference else None,
                begin_range=begin_range,
            ),
        ))

        datasets = [DataSet(g.group[0], g.values) for g in response.groups]

        return datasets, response.labels


class CancelAgreement(Controller):
    """
    TODO
    """
    Request = md.class_schema(CancelAgreementRequest)

    @requires_login
    @inject_session
    def handle_request(self, request, user, session):
        """
        :param CancelAgreementRequest request:
        :param User user:
        :param Session session:
        :rtype: bool
        """
        agreement = AgreementQuery(session) \
            .has_public_id(request.public_id) \
            .belongs_to(user) \
            .one_or_none()

        if agreement:
            # Agreement must be cancelled and its transaction committed to
            # the database before updating transfer priorities, hence both
            # are executed in a transaction for themselves sequentially
            self.cancel_agreement(agreement.public_id, user)
            self.update_transfer_priorities(agreement.user_from)
            return True
        else:
            return False

    @atomic
    def cancel_agreement(self, public_id, user, session):
        """
        TODO
        """
        AgreementQuery(session) \
            .has_public_id(public_id) \
            .belongs_to(user) \
            .one() \
            .cancel()

    @atomic
    def update_transfer_priorities(self, *args, **kwargs):
        """
        TODO
        """
        update_transfer_priorities(*args, **kwargs)


class SetTransferPriority(Controller):
    """
    TODO
    """
    Request = md.class_schema(SetTransferPriorityRequest)

    @requires_login
    def handle_request(self, request, user):
        """
        :param SetTransferPriorityRequest request:
        :param User user:
        :rtype: bool
        """
        self.update_transfer_priorities(
            request.public_ids_prioritized, user)

        self.complete_priorities(user)

        return True

    @atomic
    def update_transfer_priorities(self, public_ids_prioritized, user, session):
        """
        :param list[str public_ids_prioritized:
        :param User user:
        :param Session session:
        :rtype: bool
        """
        agreements = AgreementQuery(session) \
            .is_outbound_from(user) \
            .is_accepted()

        # Initially remove priority for all agreements
        agreements.update({TradeAgreement.transfer_priority: None})

        # Set priorities in the order they were provided
        for i, public_id in enumerate(public_ids_prioritized):
            agreements \
                .has_public_id(public_id) \
                .update({TradeAgreement.transfer_priority: i})

        return True

    @atomic
    def complete_priorities(self, *args, **kwargs):
        """
        TODO
        """
        update_transfer_priorities(*args, **kwargs)


# -- Proposals ---------------------------------------------------------------


class SubmitAgreementProposal(Controller):
    """
    TODO
    """
    Request = md.class_schema(SubmitAgreementProposalRequest)
    Response = md.class_schema(SubmitAgreementProposalResponse)

    @requires_login
    @atomic
    def handle_request(self, request, user, session):
        """
        :param SubmitAgreementProposalRequest request:
        :param User user:
        :param Session session:
        :rtype: SubmitAgreementProposalResponse
        """
        counterpart = UserQuery(session) \
            .has_public_id(request.counterpart_id) \
            .exclude(user) \
            .one_or_none()

        if not counterpart:
            return SubmitAgreementProposalResponse(success=False)

        if request.direction == AgreementDirection.INBOUND:
            user_from = counterpart
            user_to = user
            facilities = []
        elif request.direction == AgreementDirection.OUTBOUND:
            user_from = user
            user_to = counterpart
            facilities = self.get_facilities(user, request.facility_ids, session)
        else:
            raise RuntimeError('This should NOT have happened!')

        agreement = self.create_pending_agreement(
            request=request,
            user=user,
            user_from=user_from,
            user_to=user_to,
            facilities=facilities,
        )

        session.add(agreement)
        session.flush()

        logger.info(f'User submitted TradeAgreement proposal', extra={
            'subject': user.sub,
            'target': counterpart.sub,
            'agreement_id': agreement.id,
        })

        return SubmitAgreementProposalResponse(success=True)

    def create_pending_agreement(self, request, user, user_from, user_to, facilities):
        """
        :param SubmitAgreementProposalRequest request:
        :param User user:
        :param User user_from:
        :param User user_to:
        :param collections.abc.Iterable[Facility] facilities:
        :rtype: TradeAgreement
        """
        agreement = TradeAgreement(
            user_proposed=user,
            user_from=user_from,
            user_to=user_to,
            state=AgreementState.PENDING,
            date_from=request.date.begin,
            date_to=request.date.end,
            reference=request.reference,
            amount=request.amount,
            unit=request.unit,
            technology=request.technology,
            limit_to_consumption=request.limit_to_consumption,
        )

        if facilities:
            agreement.facilities.extend(facilities)

        return agreement

    def get_facilities(self, user, facility_public_ids, session):
        """
        :param User user:
        :param list[str] facility_public_ids:
        :param Session session:
        """
        return FacilityQuery(session) \
            .belongs_to(user) \
            .has_any_public_id(facility_public_ids) \
            .all()


class RespondToProposal(Controller):
    """
    TODO
    """
    Request = md.class_schema(RespondToProposalRequest)
    Response = md.class_schema(RespondToProposalResponse)

    @requires_login
    @atomic
    def handle_request(self, request, user, session):
        """
        :param RespondToProposalRequest request:
        :param User user:
        :param Session session:
        :rtype: RespondToProposalResponse
        """
        agreement = AgreementQuery(session) \
            .has_public_id(request.public_id) \
            .is_awaiting_response_by(user) \
            .one_or_none()

        if not agreement:
            return RespondToProposalResponse(success=False)

        if request.accept:
            self.accept_proposal(request, agreement, user, session)
            logger.info(f'User accepted to TradeAgreement proposal', extra={
                'subject': user.sub,
                'agreement_id': agreement.id,
            })

            start_consume_back_in_time_pipeline(
                user=agreement.user_from,
                begin_from=datetime.fromordinal(agreement.date_from.toordinal()) - timedelta(days=2),
                begin_to=datetime.fromordinal(agreement.date_to.toordinal()) + timedelta(days=2),
            )
        else:
            agreement.decline_proposal()
            logger.info(f'User declined to TradeAgreement proposal', extra={
                'subject': user.sub,
                'agreement_id': agreement.id,
            })

        return RespondToProposalResponse(success=True)

    def accept_proposal(self, request, agreement, user, session):
        """
        :param RespondToProposalRequest request:
        :param TradeAgreement agreement:
        :param User user:
        :param Session session:
        """
        agreement.state = AgreementState.ACCEPTED
        agreement.transfer_priority = self.get_next_priority(
            agreement.user_from, session)

        if request.technology and self.can_set_technology(agreement, user):
            agreement.technology = request.technology

        if request.facility_ids and self.can_set_facilities(agreement, user):
            agreement.facilities.extend(self.get_facilities(
                user=user,
                facility_public_ids=request.facility_ids,
                session=session,
            ))

    def can_set_technology(self, agreement, user):
        """
        :param User user:
        :param TradeAgreement agreement:
        :rtype: bool
        """
        return not agreement.technology and agreement.is_outbound_from(user)

    def can_set_facilities(self, agreement, user):
        """
        :param User user:
        :param TradeAgreement agreement:
        :rtype: bool
        """
        return agreement.is_outbound_from(user)

    def get_facilities(self, user, facility_public_ids, session):
        """
        :param User user:
        :param list[str] facility_public_ids:
        :param Session session:
        """
        return FacilityQuery(session) \
            .belongs_to(user) \
            .has_any_public_id(facility_public_ids) \
            .all()

    def get_next_priority(self, user, session):
        """
        :param User user:
        :param Session session:
        :rtype: int
        """
        current_max_priority = AgreementQuery(session) \
            .is_outbound_from(user) \
            .get_peiority_max()

        if current_max_priority is not None:
            return current_max_priority + 1
        else:
            return 0


class WithdrawProposal(Controller):
    """
    TODO
    """
    Request = md.class_schema(WithdrawProposalRequest)
    Response = md.class_schema(WithdrawProposalResponse)

    @requires_login
    @atomic
    def handle_request(self, request, user, session):
        """
        :param WithdrawProposalRequest request:
        :param User user:
        :param Session session:
        :rtype: WithdrawProposalResponse
        """
        agreement = AgreementQuery(session) \
            .has_public_id(request.public_id) \
            .is_proposed_by(user) \
            .is_pending() \
            .one_or_none()

        if not agreement:
            return RespondToProposalResponse(success=False)

        agreement.state = AgreementState.WITHDRAWN

        return WithdrawProposalResponse(success=True)


class CountPendingProposals(Controller):
    """
    TODO
    """
    Response = md.class_schema(CountPendingProposalsResponse)

    @requires_login
    @inject_session
    def handle_request(self, user, session):
        """
        :param User user:
        :param Session session:
        :rtype: RespondToProposalResponse
        """
        count = AgreementQuery(session) \
            .is_awaiting_response_by(user) \
            .count()

        return CountPendingProposalsResponse(
            success=True,
            count=count,
        )


# -- CSV EXPORTING -----------------------------------------------------------


class ExportGgoSummaryCSV(Controller):
    """
    Exports a CSV document with the following columns:

    Type | Technology Code | Fuel Code | Technology | Begin | Amount

    Where "Type" is either ISSUED or RETIRED.
    """
    Request = md.class_schema(GetAgreementSummaryRequest)

    @requires_login
    def handle_request(self, request, user):
        """
        :param GetAgreementSummaryRequest request:
        :param User user:
        :rtype: flask.Response
        """
        begin_range = DateTimeRange.from_date_range(request.date_range)
        resolution = get_resolution(begin_range.delta)

        if request.public_id:
            reference = [request.public_id]
        else:
            reference = None

        inbound, inbound_labels = self.get_transfer_summary(
            token=user.access_token,
            resolution=resolution,
            direction=TransferDirection.INBOUND,
            filters=TransferFilters(
                begin_range=begin_range,
                reference=reference,
            )
        )

        outbound, outbound_labels = self.get_transfer_summary(
            token=user.access_token,
            resolution=resolution,
            direction=TransferDirection.OUTBOUND,
            filters=TransferFilters(
                begin_range=begin_range,
                reference=reference,
            )
        )

        # -- Write CSV -------------------------------------------------------

        csv_file = StringIO()
        csv_writer = csv.writer(
            csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        # Headers
        csv_writer.writerow([
            'Type',
            'TechnologyCode',
            'FuelCode',
            'Technology',
            'Begin',
            'Amount',
        ])

        # Issued GGOs
        for summary_group in inbound:
            technology, technology_code, fuel_code = summary_group.group

            for label, amount in zip(inbound_labels, summary_group.values):
                csv_writer.writerow([
                    'INBOUND',
                    technology_code,
                    fuel_code,
                    technology,
                    label,
                    amount,
                ])

        # Retired GGOs
        for summary_group in outbound:
            technology, technology_code, fuel_code = summary_group.group

            for label, amount in zip(outbound_labels, summary_group.values):
                csv_writer.writerow([
                    'OUTBOUND',
                    technology_code,
                    fuel_code,
                    technology,
                    label,
                    amount,
                ])

        # -- HTTP response ---------------------------------------------------

        response = make_response(csv_file.getvalue())
        response.headers["Content-Disposition"] = 'attachment; filename=transfer-ggo-summary.csv'
        response.headers["Content-type"] = 'text/csv'

        return response

    @inject_session
    def get_facilities(self, user, filters, session):
        """
        :param User user:
        :param FacilityFilters filters:
        :param Session session:
        :rtype: list[Facility]
        """
        query = FacilityQuery(session) \
            .belongs_to(user)

        if filters is not None:
            query = query.apply_filters(filters)

        return query.all()

    def get_transfer_summary(self, token, resolution, direction, filters):
        """
        :param str token:
        :param SummaryResolution resolution:
        :param TransferDirection direction:
        :param TransferFilters filters:
        :rtype: list[SummaryGroup]
        """
        request = GetTransferSummaryRequest(
            resolution=resolution,
            fill=True,
            filters=filters,
            direction=direction,
            grouping=[
                SummaryGrouping.TECHNOLOGY,
                SummaryGrouping.TECHNOLOGY_CODE,
                SummaryGrouping.FUEL_CODE,
            ],
        )

        response = account.get_transfer_summary(token, request)

        return response.groups, response.labels
