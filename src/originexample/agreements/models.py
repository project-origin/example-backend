import sqlalchemy as sa
from marshmallow import validate
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


agreements_facility_association = sa.Table(
    'agreements_facility_association', ModelBase.metadata,

    sa.Column('agreement_id', sa.Integer(), sa.ForeignKey('agreements_agreement.id'), index=True),
    sa.Column('facility_id', sa.Integer(), sa.ForeignKey('facilities_facility.id'), index=True),

    sa.UniqueConstraint('agreement_id', 'facility_id'),
)


class TradeAgreement(ModelBase):
    """
    TODO
    """
    __tablename__ = 'agreements_agreement'
    __table_args__ = (
        sa.UniqueConstraint('public_id'),
        #sa.CheckConstraint('date_from <= date_to', name='date_from <= date_to'),
        #sa.CheckConstraint('user_from_id != user_to_id', name='user_from_id != user_to_id'),
        #sa.CheckConstraint('user_proposed_id = user_from_id OR user_proposed_id = user_to_id',
        #                   name='user_proposed_id = user_from_id OR user_proposed_id = user_to_id'),
    )

    # Meta
    id = sa.Column(sa.Integer(), primary_key=True, autoincrement=True, index=True)
    public_id = sa.Column(sa.String(), index=True, nullable=False)
    created = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())

    # Involved parties (users)
    user_proposed_id = sa.Column(sa.Integer(), sa.ForeignKey('auth_user.id'), index=True, nullable=False)
    user_proposed = relationship('User', foreign_keys=[user_proposed_id], lazy='joined')
    user_from_id = sa.Column(sa.Integer(), sa.ForeignKey('auth_user.id'), index=True, nullable=False)
    user_from = relationship('User', foreign_keys=[user_from_id], lazy='joined')
    user_to_id = sa.Column(sa.Integer(), sa.ForeignKey('auth_user.id'), index=True, nullable=False)
    user_to = relationship('User', foreign_keys=[user_to_id], lazy='joined')

    # Outbound facilities
    facilities = relationship('Facility', secondary=agreements_facility_association, uselist=True)

    # Agreement details
    state = sa.Column(sa.Enum(AgreementState), index=True, nullable=False)
    date_from = sa.Column(sa.Date(), nullable=False)
    date_to = sa.Column(sa.Date(), nullable=False)
    amount = sa.Column(sa.Integer(), nullable=False)
    unit = sa.Column(sa.Enum(Unit), nullable=False)
    technology = sa.Column(sa.String())
    reference = sa.Column(sa.String())

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


# ----------------------------------------------------------------------------


@sa.event.listens_for(TradeAgreement, 'before_insert')
def on_before_creating_task(mapper, connect, agreement):
    if not agreement.public_id:
        agreement.public_id = str(uuid4())


# ----------------------------------------------------------------------------


@dataclass
class MappedTradeAgreement:
    direction: AgreementDirection = field(metadata=dict(by_value=True))
    counterpart: str
    public_id: str = field(metadata=dict(data_key='id'))
    date_from: str = field(metadata=dict(data_key='dateFrom'))
    date_to: str = field(metadata=dict(data_key='dateTo'))
    amount: int
    unit: Unit
    technology: str
    reference: str

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
    date_range: DateRange = field(default=None, metadata=dict(data_key='dateRange'))
    public_id: str = field(default=None, metadata=dict(data_key='id'))
    direction: AgreementDirection = field(default=None, metadata=dict(by_value=True))


@dataclass
class GetAgreementSummaryResponse:
    success: bool
    labels: List[str]
    ggos: List[DataSet]


# -- SubmitAgreementProposal request and response ----------------------------


@dataclass
class SubmitAgreementProposalRequest:
    direction: AgreementDirection = field(metadata=dict(by_value=True))
    reference: str = field(metadata=dict(validate=validate.Length(min=1)))
    counterpart_id: str = field(metadata=dict(data_key='counterpartId', validate=(validate.Length(min=1), user_public_id_exists)))
    amount: int
    unit: Unit
    date: DateRange
    technology: str = field(default=None)
    facility_ids: List[str] = field(default_factory=list, metadata=dict(data_key='facilityIds'))


@dataclass
class SubmitAgreementProposalResponse:
    success: bool


# -- RespondToProposal request and response ----------------------------------


@dataclass
class RespondToProposalRequest:
    public_id: str = field(metadata=dict(data_key='id'))
    accept: bool
    technology: str = field(default=None)
    facility_ids: List[str] = field(default_factory=list, metadata=dict(data_key='facilityIds'))


@dataclass
class RespondToProposalResponse:
    success: bool


# -- WithdrawProposal request and response -----------------------------------


@dataclass
class WithdrawProposalRequest:
    public_id: str = field(metadata=dict(data_key='id'))


@dataclass
class WithdrawProposalResponse:
    success: bool


# -- CountPendingProposals request and response ------------------------------


@dataclass
class CountPendingProposalsResponse:
    success: bool
    count: int
