import sqlalchemy as sa
from sqlalchemy.orm import relationship
from dataclasses import dataclass, field
from datetime import date

from originexample.db import ModelBase
from originexample.settings import API_ROOT_URL
from originexample.tools import randomized_hash
from originexample.facilities import FacilityFilters


disclosures_facility_association = sa.Table(
    'disclosures_facility_association', ModelBase.metadata,

    sa.Column('disclosure_id', sa.Integer(), sa.ForeignKey('disclosures_disclosure.id'), index=True),
    sa.Column('facility_id', sa.Integer(), sa.ForeignKey('facilities_facility.id'), index=True),

    sa.UniqueConstraint('disclosure_id', 'facility_id'),
)


class Disclosure(ModelBase):
    """
    TODO
    """
    __tablename__ = 'disclosures_disclosure'
    __table_args__ = (
        sa.UniqueConstraint('slug'),
    )

    id = sa.Column(sa.Integer(), primary_key=True, autoincrement=True, index=True)
    public_id = sa.Column(sa.String(), index=True, default=randomized_hash)
    created = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    slug = sa.Column(sa.String(), unique=True, index=True, nullable=False)

    user_id = sa.Column(sa.Integer(), sa.ForeignKey('auth_user.id'), index=True, nullable=False)
    user = relationship('User', foreign_keys=[user_id])
    facilities = relationship('Facility', secondary=disclosures_facility_association)

    date_from = sa.Column(sa.Date(), nullable=False)
    date_to = sa.Column(sa.Date(), nullable=False)
    name = sa.Column(sa.String(), nullable=False)
    description = sa.Column(sa.String())

    def get_public_url(self):
        return '%s/disclosure/%s' % (API_ROOT_URL, self.slug)


# -- CreateDisclosure request and response -----------------------------------


@dataclass
class CreateDisclosureRequest:
    filters: FacilityFilters
    date_from: date = field(metadata=dict(data_key='dateFrom', required=True))
    date_to: date = field(metadata=dict(data_key='dateTo', required=True))
    name: str
    description: str


@dataclass
class CreateDisclosureResponse:
    success: bool
    url: str


# -- GetPublicDisclosure request and response --------------------------------


@dataclass
class GetPublicDisclosureRequest:
    slug: str


@dataclass
class GetPublicDisclosureResponse:
    success: bool
    url: str
