from enum import Enum
from typing import List
from datetime import datetime
from dataclasses import dataclass, field

from originexample.common import DateTimeRange

from ..shared_models import SummaryResolution, SummaryGroup


# -- Common ------------------------------------------------------------------


@dataclass
class Ggo:
    address: str
    sector: str
    begin: datetime
    end: datetime
    amount: int
    technology: str
    technology_code: str = field(metadata=dict(data_key='technologyCode'))
    fuel_code: str = field(metadata=dict(data_key='fuelCode'))


class GgoCategory(Enum):
    """
    TODO
    """
    ISSUED = 'issued'
    STORED = 'stored'
    RETIRED = 'retired'
    EXPIRED = 'expired'


@dataclass
class GgoFilters:
    """
    TODO
    """
    begin: datetime = field(default=None)
    begin_range: DateTimeRange = field(default=None, metadata=dict(data_key='beginRange'))

    sector: List[str] = field(default_factory=list)
    technology_code: List[str] = field(default_factory=list, metadata=dict(data_key='technologyCode'))
    fuel_code: List[str] = field(default_factory=list, metadata=dict(data_key='fuelCode'))

    category: GgoCategory = field(default=None, metadata=dict(by_value=True))
    issue_gsrn: List[str] = field(default_factory=list, metadata=dict(data_key='issueGsrn'))
    retire_gsrn: List[str] = field(default_factory=list, metadata=dict(data_key='retireGsrn'))


@dataclass
class TransferFilters(GgoFilters):
    """
    TODO
    """
    reference: List[str] = field(default_factory=list)

    # TODO add recipient user account?


@dataclass
class RetireFilters(GgoFilters):
    """
    TODO
    """
    address: List[str] = field(default_factory=list)


class TransferDirection(Enum):
    """
    TODO
    """
    INBOUND = 'inbound'
    OUTBOUND = 'outbound'


@dataclass
class TransferRequest:
    """
    TODO
    """
    amount: int
    reference: str
    sub: str


@dataclass
class RetireRequest:
    """
    TODO
    """
    amount: int
    gsrn: str


class SummaryGrouping:
    BEGIN = 'begin'
    SECTOR = 'sector'
    TECHNOLOGY = 'technology'
    TECHNOLOGY_CODE = 'technologyCode'
    FUEL_CODE = 'fuelCode'


# -- GetGgoList request and response -----------------------------------------


@dataclass
class GetGgoListRequest:
    filters: GgoFilters
    offset: int
    limit: int
    order: List[str] = field(default_factory=list)


@dataclass
class GetGgoListResponse:
    success: bool
    total: int
    results: List[Ggo] = field(default_factory=list)


# -- GetGgoSummary request and response --------------------------------------


@dataclass
class GetGgoSummaryRequest:
    resolution: SummaryResolution = field(metadata=dict(by_value=True))
    filters: GgoFilters
    fill: bool
    grouping: List[str]


@dataclass
class GetGgoSummaryResponse:
    success: bool
    labels: List[str] = field(default_factory=list)
    groups: List[SummaryGroup] = field(default_factory=list)


# -- GetTransferSummary request and response ---------------------------------


@dataclass
class GetTransferSummaryRequest:
    resolution: SummaryResolution = field(metadata=dict(by_value=True))
    filters: TransferFilters
    fill: bool
    grouping: List[str] = field(default_factory=list)
    direction: TransferDirection = field(default=None, metadata=dict(by_value=True))


@dataclass
class GetTransferSummaryResponse(GetGgoSummaryResponse):
    pass


# -- ComposeGgo request and response -----------------------------------------


@dataclass
class ComposeGgoRequest:
    address: str
    transfers: List[TransferRequest] = field(default_factory=list)
    retires: List[RetireRequest] = field(default_factory=list)


@dataclass
class ComposeGgoResponse:
    success: bool
    message: str = field(default=None)


# -- GetTransferredAmount request and response -------------------------------


@dataclass
class GetTransferredAmountRequest:
    filters: TransferFilters
    direction: TransferDirection = field(default=None, metadata=dict(by_value=True))


@dataclass
class GetTransferredAmountResponse:
    success: bool
    amount: int


# -- GetRetiredAmount request and response -----------------------------------


@dataclass
class GetRetiredAmountRequest:
    filters: RetireFilters


@dataclass
class GetRetiredAmountResponse:
    success: bool
    amount: int


# -- Webhooks request and response -------------------------------------------


@dataclass
class WebhookSubscribeRequest:
    url: str
    secret: str


@dataclass
class WebhookSubscribeResponse:
    success: bool
