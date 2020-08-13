import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import ARRAY
from marshmallow import validate, EXCLUDE
from sqlalchemy.orm import relationship
from uuid import uuid4
from enum import Enum
from typing import List
from dataclasses import dataclass, field

from originexample.db import ModelBase
from originexample.facilities.models import MappedFacility
from originexample.auth import User, user_public_id_exists
from originexample.common import Unit, DateRange, DataSet


class AgreementDirection(Enum):
    INBOUND = 'inbound'
    OUTBOUND = 'outbound'


class AgreementState(Enum):
    PENDING = 'PENDING'
    ACCEPTED = 'ACCEPTED'
    DECLINED = 'DECLINED'
    CANCELLED = 'CANCELLED'
    WITHDRAWN = 'WITHDRAWN'


class TradeAgreement(ModelBase):
    """
    TODO
    """
    __tablename__ = 'agreements_agreement'
    __table_args__ = (
        sa.UniqueConstraint('public_id'),
        sa.CheckConstraint(
            "(amount_percent IS NULL) OR (amount_percent >= 1 AND amount_percent <= 100)",
            name="amount_percent_is_NULL_or_between_1_and_100",
        ),
        sa.CheckConstraint(
            "(limit_to_consumption = 'f' and amount is not null and unit is not null) or (limit_to_consumption = 't')",
            name="limit_to_consumption_OR_amount_and_unit",
        ),
    )

    # Meta
    id = sa.Column(sa.Integer(), primary_key=True, autoincrement=True, index=True)
    public_id = sa.Column(sa.String(), index=True, nullable=False)
    created = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    declined = sa.Column(sa.DateTime(timezone=True))
    cancelled = sa.Column(sa.DateTime(timezone=True))

    # Involved parties (users)
    user_proposed_id = sa.Column(sa.Integer(), sa.ForeignKey('auth_user.id'), index=True, nullable=False)
    user_proposed = relationship('User', foreign_keys=[user_proposed_id], lazy='joined')
    user_from_id = sa.Column(sa.Integer(), sa.ForeignKey('auth_user.id'), index=True, nullable=False)
    user_from = relationship('User', foreign_keys=[user_from_id], lazy='joined')
    user_to_id = sa.Column(sa.Integer(), sa.ForeignKey('auth_user.id'), index=True, nullable=False)
    user_to = relationship('User', foreign_keys=[user_to_id], lazy='joined')

    # Outbound facilities
    facility_ids = sa.Column(ARRAY(sa.Integer()))

    # Agreement details
    state = sa.Column(sa.Enum(AgreementState), index=True, nullable=False)
    date_from = sa.Column(sa.Date(), nullable=False)
    date_to = sa.Column(sa.Date(), nullable=False)
    technologies = sa.Column(ARRAY(sa.String()), index=True)
    reference = sa.Column(sa.String())

    # Max. amount to transfer (per begin)
    amount = sa.Column(sa.Integer())
    unit = sa.Column(sa.Enum(Unit))

    # Transfer percentage (though never exceed max. amount - "amount" above)
    amount_percent = sa.Column(sa.Integer())

    # Limit transferred amount to recipient's consumption?
    limit_to_consumption = sa.Column(sa.Boolean())

    # Lowest number = highest priority
    # Is set when user accepts the agreement, otherwise None
    transfer_priority = sa.Column(sa.Integer())

    # Senders proposal note to recipient
    proposal_note = sa.Column(sa.String())

    @property
    def transfer_reference(self):
        """
        :rtype: str
        """
        return self.public_id

    @property
    def calculated_amount(self):
        """
        :rtype: int
        """
        return self.amount * self.unit.value

    def is_proposed_by(self, user):
        """
        :param User user:
        :rtype: bool
        """
        return user.id == self.user_proposed_id

    def is_inbound_to(self, user):
        """
        :param User user:
        :rtype: bool
        """
        return user.id == self.user_to_id

    def is_outbound_from(self, user):
        """
        :param User user:
        :rtype: bool
        """
        return user.id == self.user_from_id

    def is_pending(self):
        """
        :rtype: bool
        """
        return self.state == AgreementState.PENDING

    def decline_proposal(self):
        self.state = AgreementState.DECLINED
        self.declined = func.now()

    def cancel(self):
        self.state = AgreementState.CANCELLED
        self.cancelled = func.now()
        self.transfer_priority = None

# ----------------------------------------------------------------------------


@sa.event.listens_for(TradeAgreement, 'before_insert')
def on_before_creating_task(mapper, connect, agreement):
    if not agreement.public_id:
        agreement.public_id = str(uuid4())


# ----------------------------------------------------------------------------


@dataclass
class MappedTradeAgreement:
    state: AgreementState = field(metadata=dict(by_value=True))
    direction: AgreementDirection = field(metadata=dict(by_value=True))
    counterpart_id: str = field(metadata=dict(data_key='counterpartId'))
    counterpart: str
    public_id: str = field(metadata=dict(data_key='id'))
    date_from: str = field(metadata=dict(data_key='dateFrom'))
    date_to: str = field(metadata=dict(data_key='dateTo'))
    amount: int
    amount_percent: int = field(metadata=dict(data_key='amountPercent'))
    unit: Unit
    technologies: List[str]
    reference: str
    limit_to_consumption: bool = field(metadata=dict(data_key='limitToConsumption'))
    proposal_note: str = field(metadata=dict(data_key='proposalNote', allow_none=True))

    # Only for the outbound-user of an agreement
    facilities: List[MappedFacility] = field(default_factory=list)


# -- GetAgreementList request and response -----------------------------------


@dataclass
class GetAgreementListResponse:
    success: bool
    pending: List[MappedTradeAgreement] = field(default_factory=list)
    sent: List[MappedTradeAgreement] = field(default_factory=list)
    inbound: List[MappedTradeAgreement] = field(default_factory=list)
    outbound: List[MappedTradeAgreement] = field(default_factory=list)
    cancelled: List[MappedTradeAgreement] = field(default_factory=list)
    declined: List[MappedTradeAgreement] = field(default_factory=list)


# -- GetAgreementSummary request and response --------------------------------


@dataclass
class GetAgreementDetailsRequest:
    public_id: str = field(default=None, metadata=dict(data_key='id'))


@dataclass
class GetAgreementDetailsResponse:
    success: bool
    agreement: MappedTradeAgreement = field(default=None)


# -- GetAgreementSummary request and response --------------------------------


@dataclass
class GetAgreementSummaryRequest:
    utc_offset: int = field(metadata=dict(required=False, missing=0, data_key='utcOffset'))
    date_range: DateRange = field(default=None, metadata=dict(data_key='dateRange'))
    public_id: str = field(default=None, metadata=dict(data_key='id'))
    direction: AgreementDirection = field(default=None, metadata=dict(by_value=True))


@dataclass
class GetAgreementSummaryResponse:
    success: bool
    labels: List[str]
    ggos: List[DataSet]


# -- CancelAgreement request and response ------------------------------------


@dataclass
class CancelAgreementRequest:
    public_id: str = field(metadata=dict(data_key='id'))


# -- SetTransferPriority request and response ------------------------------------


@dataclass
class SetTransferPriorityRequest:
    public_ids_prioritized: List[str] = field(default_factory=list, metadata=dict(data_key='idsPrioritized', missing=[]))


# -- SetFacilities request and response ------------------------------------


@dataclass
class SetFacilitiesRequest:
    public_id: str = field(metadata=dict(data_key='id'))
    facility_public_ids: List[str] = field(default_factory=list, metadata=dict(data_key='facilityIds', missing=[]))


# -- SubmitAgreementProposal request and response ----------------------------


@dataclass
class SubmitAgreementProposalRequest:
    direction: AgreementDirection = field(metadata=dict(by_value=True))
    reference: str = field(metadata=dict(validate=validate.Length(min=1)))
    counterpart_id: str = field(metadata=dict(data_key='counterpartId', validate=(validate.Length(min=1), user_public_id_exists)))
    amount: int
    unit: Unit
    amount_percent: int = field(metadata=dict(allow_none=True, data_key='amountPercent', validate=validate.Range(min=1, max=100)))
    date: DateRange
    limit_to_consumption: bool = field(metadata=dict(data_key='limitToConsumption'))
    proposal_note: str = field(metadata=dict(data_key='proposalNote', allow_none=True))
    technologies: List[str] = field(default_factory=None)
    facility_ids: List[str] = field(default_factory=list, metadata=dict(data_key='facilityIds'))

    class Meta:
        unknown = EXCLUDE


@dataclass
class SubmitAgreementProposalResponse:
    success: bool


# -- RespondToProposal request and response ----------------------------------


@dataclass
class RespondToProposalRequest:
    public_id: str = field(metadata=dict(data_key='id'))
    accept: bool
    technologies: List[str] = field(default_factory=None)
    facility_ids: List[str] = field(default_factory=list, metadata=dict(data_key='facilityIds'))
    amount_percent: int = field(default_factory=list, metadata=dict(allow_none=True, data_key='amountPercent'))


# -- WithdrawProposal request and response -----------------------------------


@dataclass
class WithdrawProposalRequest:
    public_id: str = field(metadata=dict(data_key='id'))


# -- CountPendingProposals request and response ------------------------------


@dataclass
class CountPendingProposalsResponse:
    success: bool
    count: int
