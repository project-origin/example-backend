from enum import Enum
from typing import List
from datetime import datetime, date
from dataclasses import dataclass, field

from marshmallow_dataclass import NewType

from originexample.common import DateTimeRange, DateRange

from ..shared_models import MeasurementType, SummaryResolution, SummaryGroup


# -- Common ------------------------------------------------------------------


@dataclass
class Technology:
    technology: str
    technology_code: str = field(metadata=dict(data_key='technologyCode'))
    fuel_code: str = field(metadata=dict(data_key='fuelCode'))


class MeteringPointType(Enum):
    PRODUCTION = 'production'
    CONSUMPTION = 'consumption'


@dataclass
class MeteringPoint:
    gsrn: str
    type: MeteringPointType = field(metadata=dict(by_value=True))
    sector: str
    technology_code: str = field(default=None, metadata=dict(data_key='technologyCode'))
    fuel_code: str = field(default=None, metadata=dict(data_key='fuelCode'))
    street_code: str = field(default=None, metadata=dict(data_key='streetCode'))
    street_name: str = field(default=None, metadata=dict(data_key='streetName'))
    building_number: str = field(default=None, metadata=dict(data_key='buildingNumber'))
    city_name: str = field(default=None, metadata=dict(data_key='cityName'))
    postcode: str = field(default=None, metadata=dict(data_key='postCode'))
    municipality_code: str = field(default=None, metadata=dict(data_key='municipalityCode'))


@dataclass
class Measurement:
    address: str
    gsrn: str
    begin: datetime
    end: datetime
    type: MeasurementType = field(metadata=dict(by_value=True))
    sector: str
    amount: int


@dataclass
class MeasurementFilters:
    """
    TODO
    """
    begin: datetime = field(default=None)
    begin_range: DateTimeRange = field(default=None, metadata=dict(data_key='beginRange'))
    sector: List[str] = field(default_factory=list)
    gsrn: List[str] = field(default_factory=list)
    type: MeasurementType = field(default=None, metadata=dict(by_value=True))


@dataclass
class Disclosure:
    id: str
    name: str
    description: str
    begin: date
    end: date
    publicize_meteringpoints: bool = field(metadata=dict(data_key='publicizeMeteringpoints'))
    publicize_gsrn: bool = field(metadata=dict(data_key='publicizeGsrn'))
    publicize_physical_address: bool = field(metadata=dict(data_key='publicizePhysicalAddress'))


# -- GetMeasurement request and response -------------------------------------


@dataclass
class GetMeasurementRequest:
    gsrn: str
    begin: datetime


@dataclass
class GetMeasurementResponse:
    success: bool
    measurement: Measurement = field(default=None)


# -- GetMeasurementList request and response ---------------------------------


@dataclass
class GetMeasurementListRequest:
    filters: MeasurementFilters
    offset: int
    limit: int


@dataclass
class GetMeasurementListResponse:
    success: bool
    total: int
    measurements: List[Measurement] = field(default_factory=list)


# -- GetBeginRange request and response --------------------------------------


@dataclass
class GetBeginRangeRequest:
    filters: MeasurementFilters = field(default=None)


@dataclass
class GetBeginRangeResponse:
    success: bool
    first: datetime
    last: datetime


# -- GetGgoSummary request and response --------------------------------------


@dataclass
class GetMeasurementSummaryRequest:
    resolution: SummaryResolution = field(metadata=dict(by_value=True))
    filters: MeasurementFilters
    fill: bool
    grouping: List[str] = field(default_factory=list)


@dataclass
class GetMeasurementSummaryResponse:
    success: bool
    labels: List[str] = field(default_factory=list)
    groups: List[SummaryGroup] = field(default_factory=list)


# -- GetMeteringPoints request and response ----------------------------------


@dataclass
class GetMeteringPointsResponse:
    success: bool
    meteringpoints: List[MeteringPoint] = field(default_factory=list)


# -- GetOnboadingUrl request and response ----------------------------------


@dataclass
class GetOnboadingUrlRequest:
    return_url: str = field(metadata=dict(data_key='returnUrl'))


@dataclass
class GetOnboadingUrlResponse:
    success: bool
    url: str


# -- GetDisclosure request and response --------------------------------------


MeasurementValue = NewType('MeasurementValue', int, allow_none=True)


@dataclass
class DisclosureState(Enum):
    PENDING = 'PENDING'
    PROCESSING = 'PROCESSING'
    AVAILABLE = 'AVAILABLE'


@dataclass
class DisclosureDataSeries:
    gsrn: str = field(default=None)
    address: str = field(default=None)
    measurements: List[MeasurementValue] = field(default_factory=list)
    ggos: List[SummaryGroup] = field(default_factory=list)


@dataclass
class GetDisclosureRequest:
    id: str
    resolution: SummaryResolution = field(default=None, metadata=dict(by_value=True))
    date_range: DateRange = field(default=None, metadata=dict(data_key='dateRange'))


@dataclass
class GetDisclosureResponse:
    success: bool
    labels: List[str]
    data: List[DisclosureDataSeries]
    message: str = field(default=None)
    state: DisclosureState = field(default=None, metadata=dict(by_value=True))


# -- GetDisclosureList request and response ----------------------------------


@dataclass
class GetDisclosureListResponse:
    success: bool
    disclosures: List[Disclosure]


# -- CreateDisclosure request and response -----------------------------------


@dataclass
class CreateDisclosureRequest:
    name: str
    description: str
    gsrn: List[str]
    begin: date
    end: date
    publicize_meteringpoints: bool = field(metadata=dict(data_key='publicizeMeteringpoints'))
    publicize_gsrn: bool = field(metadata=dict(data_key='publicizeGsrn'))
    publicize_physical_address: bool = field(metadata=dict(data_key='publicizePhysicalAddress'))


@dataclass
class CreateDisclosureResponse:
    success: bool
    id: str


# -- DeleteDisclosure request and response -----------------------------------


@dataclass
class DeleteDisclosureRequest:
    id: str


@dataclass
class DeleteDisclosureResponse:
    success: bool
    message: str = field(default=None)


# -- GetTechnologies request and response ------------------------------------


@dataclass
class GetTechnologiesResponse:
    success: bool
    technologies: List[Technology] = field(default_factory=list)


# -- Webhooks request and response -------------------------------------------


@dataclass
class WebhookSubscribeRequest:
    url: str
    secret: str


@dataclass
class WebhookSubscribeResponse:
    success: bool
