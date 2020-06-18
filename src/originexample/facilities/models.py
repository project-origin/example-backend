from enum import Enum

import marshmallow
import sqlalchemy as sa
from uuid import uuid4
from typing import List
from marshmallow_dataclass import NewType
from sqlalchemy.orm import relationship
from dataclasses import dataclass, field

from originexample.db import ModelBase
from originexample.technology import Technology
from originexample.settings import UNKNOWN_TECHNOLOGY_LABEL


class FacilityType:  # TODO Enum
    PRODUCTION = 'production'
    CONSUMPTION = 'consumption'


class FacilityOrder(Enum):
    NAME = 'name'
    RETIRE_PRIORITY = 'retirePriority'


class Facility(ModelBase):
    """
    Represents one used in the system who is able to authenticate.

    facility_type: production or consumption.
    technology_type: solar, wind, oil, etc.
    technology_code: T010000, T030100, etc.
    source_code: F01010300, F01010500, etc.

    technology_code and source_code is None where facility_type is 'consumption'.
    technology_type is None where technology_code and source_code is None.
    """
    __tablename__ = 'facilities_facility'
    __table_args__ = (
        sa.UniqueConstraint('gsrn'),
        sa.UniqueConstraint('user_id', 'retiring_priority'),
    )

    # Meta
    id = sa.Column(sa.Integer(), primary_key=True, autoincrement=True, index=True)
    public_id = sa.Column(sa.String(), index=True)
    created = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())

    # Relationships
    user_id = sa.Column(sa.Integer(), sa.ForeignKey('auth_user.id'), index=True, nullable=False)
    user = relationship('User', foreign_keys=[user_id])
    tags = relationship('FacilityTag', back_populates='facility', lazy='joined', cascade='all, delete-orphan')

    # Facility data
    gsrn = sa.Column(sa.String(), index=True)
    facility_type = sa.Column(sa.String(), nullable=False)  # TODO rename to "type" to match MeteringPoint?
    technology_code = sa.Column(sa.String())
    fuel_code = sa.Column(sa.String())
    sector = sa.Column(sa.String(), nullable=False)
    name = sa.Column(sa.String(), nullable=False)

    technology = relationship(
        'Technology',
        lazy='joined',
        foreign_keys=[technology_code, fuel_code],
        primaryjoin=sa.and_(
            technology_code == Technology.technology_code,
            fuel_code == Technology.fuel_code,
        ),
     )

    # Address
    street_code = sa.Column(sa.String())
    street_name = sa.Column(sa.String())
    building_number = sa.Column(sa.String())
    city_name = sa.Column(sa.String())
    postcode = sa.Column(sa.String())
    municipality_code = sa.Column(sa.String())

    # Lowest number = highest priority
    retiring_priority = sa.Column(sa.Integer())

    def __str__(self):
        return self.gsrn

    def __repr__(self):
        return 'Facility<%s>' % self

    @property
    def address(self):
        return '%s %s' % (self.street_name, self.building_number)


class FacilityTag(ModelBase):
    """
    TODO
    """
    __tablename__ = 'facilities_tag'
    __table_args__ = (
        sa.UniqueConstraint('facility_id', 'tag'),
    )

    id = sa.Column(sa.Integer(), primary_key=True, autoincrement=True, index=True)
    facility_id = sa.Column(sa.Integer(), sa.ForeignKey('facilities_facility.id'), index=True, nullable=False)
    facility = relationship('Facility', foreign_keys=[facility_id], back_populates='tags')
    tag = sa.Column(sa.String(), index=True, nullable=False)


# ----------------------------------------------------------------------------


@sa.event.listens_for(Facility, 'before_insert')
def on_before_creating_task(mapper, connect, facility):
    if not facility.public_id:
        facility.public_id = str(uuid4())
    if not facility.name:
        facility.name = '%s, %s %s' % (
            facility.address,
            facility.postcode,
            facility.city_name,
        )


# -- Common ------------------------------------------------------------------


FacilityTechnology = NewType(
    name='FacilityTechnology',
    typ=str,
    field=marshmallow.fields.Function,
    serialize=lambda facility: (facility.technology.technology
                                if facility.technology
                                else UNKNOWN_TECHNOLOGY_LABEL),
)


FacilityTagList = NewType(
    name='FacilityTag',
    typ=str,
    field=marshmallow.fields.Function,
    serialize=lambda facility: [t.tag for t in facility.tags],
)


@dataclass
class MappedFacility:
    """
    Replicates the data structure of a Facility, but is compatible
    with marshmallow_dataclass obj-to-JSON
    """
    public_id: str = field(metadata=dict(data_key='id'))
    retiring_priority: int = field(metadata=dict(data_key='retiringPriority'))
    gsrn: str
    facility_type: str = field(metadata=dict(data_key='facilityType'))
    technology: FacilityTechnology
    technology_code: str = field(metadata=dict(data_key='technologyCode'))
    fuel_code: str = field(metadata=dict(data_key='fuelCode'))
    sector: str
    name: str
    description: str
    address: str
    city_name: str = field(metadata=dict(data_key='cityName'))
    postcode: str
    municipality_code: str = field(metadata=dict(data_key='municipalityCode'))
    tags: FacilityTagList = field(default_factory=list)


@dataclass
class FacilityFilters:
    facility_type: str = field(default=None, metadata=dict(data_key='facilityType'))  # TODO OneOf
    gsrn: List[str] = field(default_factory=list)
    sectors: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    technology: str = field(default=None)
    text: str = field(default=None)


# -- GetFacilityList request and response ------------------------------------


@dataclass
class GetFacilityListRequest:
    filters: FacilityFilters = None
    order_by: FacilityOrder = field(default=None, metadata=dict(data_key='orderBy', by_value=True))


@dataclass
class GetFacilityListResponse:
    success: bool
    facilities: List[MappedFacility] = field(default_factory=list)


# -- GetFilteringOptions request and response --------------------------------


@dataclass
class GetFilteringOptionsRequest:
    filters: FacilityFilters = None


@dataclass
class GetFilteringOptionsResponse:
    success: bool
    sectors: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)


# -- EditFacilityDetails request and response --------------------------------


@dataclass
class EditFacilityDetailsRequest:
    id: str
    name: str
    tags: List[str] = field(default_factory=list)


@dataclass
class EditFacilityDetailsResponse:
    success: bool


# -- GetFacilityList request and response ------------------------------------


@dataclass
class SetRetiringPriorityRequest:
    public_ids_prioritized: List[str] = field(default_factory=list, metadata=dict(data_key='idsPrioritized', missing=[]))


@dataclass
class SetRetiringPriorityResponse:
    success: bool
