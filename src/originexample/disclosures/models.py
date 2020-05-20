from dataclasses import dataclass, field
from datetime import date
from typing import List

from originexample.common import DateRange, DataSet
from originexample.facilities import MappedFacility, FacilityFilters
from originexample.services.datahub import Disclosure, SummaryResolution


# -- GetDisclosure request and response --------------------------------------


@dataclass
class DisclosureDataSeries:
    gsrn: str = field(default=None)
    address: str = field(default=None)
    measurements: List[int] = field(default_factory=list)
    ggos: List[DataSet] = field(default_factory=list)


@dataclass
class GetDisclosureRequest:
    id: str
    date_range: DateRange = field(default=None, metadata=dict(data_key='dateRange'))


@dataclass
class GetDisclosureResponse:
    success: bool
    description: str
    begin: date
    end: date
    labels: List[str]
    data: List[DisclosureDataSeries]


# -- GetDisclosurePreview request and response -------------------------------


@dataclass
class GetDisclosurePreviewRequest:
    filters: FacilityFilters
    date_range: DateRange = field(metadata=dict(data_key='dateRange'))


@dataclass
class GetDisclosurePreviewResponse:
    success: bool
    date_range: DateRange = field(metadata=dict(data_key='dateRange'))
    facilities: List[MappedFacility]


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
    max_resolution: SummaryResolution = field(metadata=dict(by_value=True, data_key='maxResolution'))
    date_range: DateRange = field(metadata=dict(data_key='dateRange'))
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
