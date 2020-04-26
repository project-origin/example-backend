from functools import partial
import marshmallow_dataclass as md

from originexample.auth import User, UserQuery, requires_login
from originexample.db import inject_session, atomic
from originexample.http import Controller
from originexample.facilities import Facility, FacilityQuery
from originexample.common import DateTimeRange, DataSet
from originexample.services.account import (
    AccountService,
    SummaryResolution,
    SummaryGrouping,
    TransferFilters,
    TransferDirection,
    GetTransferSummaryRequest,
    summarize_technologies,
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
)


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
            public_id=agreement.public_id,
            counterpart=agreement.user_from.name,
            date_from=agreement.date_from,
            date_to=agreement.date_to,
            amount=agreement.amount,
            unit=agreement.unit,
            technology=agreement.technology,
            reference=agreement.reference,
        )

    def map_outbound_agreement(self, agreement):
        """
        :param TradeAgreement agreement:
        :rtype: MappedTradeAgreement
        """
        return MappedTradeAgreement(
            direction=AgreementDirection.OUTBOUND,
            public_id=agreement.public_id,
            counterpart=agreement.user_to.name,
            date_from=agreement.date_from,
            date_to=agreement.date_to,
            amount=agreement.amount,
            unit=agreement.unit,
            technology=agreement.technology,
            reference=agreement.reference,
            facilities=list(agreement.facilities),
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
            .all()

        # Invitations sent by this user awaiting response by another user
        sent = AgreementQuery(session) \
            .is_proposed_by(user) \
            .is_pending() \
            .all()

        # Inbound agreements currently active
        inbound = AgreementQuery(session) \
            .is_inbound_to(user) \
            .is_accepted() \
            .all()

        # Outbound agreements currently active
        outbound = AgreementQuery(session) \
            .is_outbound_from(user) \
            .is_accepted() \
            .all()

        map_agreement = partial(self.map_agreement_for, user)

        return GetAgreementListResponse(
            success=True,
            pending=list(map(map_agreement, pending)),
            sent=list(map(map_agreement, sent)),
            inbound=list(map(map_agreement, inbound)),
            outbound=list(map(map_agreement, outbound)),
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

    service = AccountService()

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
            resolution = self.get_resolution(request.date_range.delta)
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
            direction=direction,
            reference=agreement.public_id if agreement else None,
        )

        return GetAgreementSummaryResponse(
            success=True,
            labels=labels,
            ggos=ggos,
        )

    def get_resolution(self, delta):
        """
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

    def get_agreement_summary(self, request, token, resolution, direction=None, reference=None):
        """
        :param GetMeasurementsRequest request:
        :param str token:
        :param SummaryResolution resolution:
        :param TransferDirection direction:
        :param str reference:
        :rtype: (list[DataSet], list[str])
        """
        grouping = [
            SummaryGrouping.TECHNOLOGY_CODE,
            SummaryGrouping.FUEL_CODE,
        ]

        if request.date_range:
            begin_range = DateTimeRange.from_date_range(request.date_range)
            fill = True
        else:
            begin_range = None
            fill = False

        response = self.service.get_transfer_summary(token, GetTransferSummaryRequest(
            direction=direction,
            resolution=resolution,
            grouping=grouping,
            fill=fill,
            filters=TransferFilters(
                reference=[reference] if reference else None,
                begin_range=begin_range,
            ),
        ))

        datasets = []

        summarized = summarize_technologies(response.groups, grouping)

        for technology, summary_group in summarized:
            datasets.append(DataSet(
                label=technology,
                values=summary_group.values,
            ))

        return datasets, response.labels


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

        session.add(self.create_pending_agreement(
            request=request,
            user=user,
            user_from=user_from,
            user_to=user_to,
            facilities=facilities,
        ))

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
        else:
            self.decline_proposal(agreement)

        return RespondToProposalResponse(success=True)

    def decline_proposal(self, agreement):
        """
        :param TradeAgreement agreement:
        """
        agreement.state = AgreementState.DECLINED

    def accept_proposal(self, request, agreement, user, session):
        """
        :param RespondToProposalRequest request:
        :param TradeAgreement agreement:
        :param User user:
        :param Session session:
        """
        agreement.state = AgreementState.ACCEPTED

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
