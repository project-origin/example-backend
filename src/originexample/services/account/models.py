import isodate
from enum import Enum
from typing import List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field

from marshmallow import fields
from marshmallow_dataclass import NewType

from originexample.common import DateTimeRange, DateRange

from ..shared_models import SummaryResolution, SummaryGroup


# -- Common ------------------------------------------------------------------


@dataclass
class Ggo:
    address: str
    sector: str
    begin: datetime
    end: datetime
    amount: int
    technology: str = field(metadata=dict(allow_none=True))
    technology_code: str = field(metadata=dict(data_key='technologyCode'))
    fuel_code: str = field(metadata=dict(data_key='fuelCode'))
    emissions: Dict[str, float] = field(default=None, metadata=dict(required=False, missing=None))


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

    address: List[str] = field(default_factory=list)
    sector: List[str] = field(default_factory=list)
    technology_code: List[str] = field(default_factory=list, metadata=dict(data_key='technologyCode'))
    fuel_code: List[str] = field(default_factory=list, metadata=dict(data_key='fuelCode'))

    category: GgoCategory = field(default=None, metadata=dict(by_value=True))
    issue_gsrn: List[str] = field(default_factory=list, metadata=dict(data_key='issueGsrn'))
    retire_gsrn: List[str] = field(default_factory=list, metadata=dict(data_key='retireGsrn'))
    retire_address: List[str] = field(default_factory=list, metadata=dict(data_key='retireAddress'))


@dataclass
class TransferFilters(GgoFilters):
    """
    TODO
    """
    reference: List[str] = field(default_factory=list)

    # TODO add recipient user account?


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
    account: str


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


# -- Forecast ----------------------------------------------------------------


ForecastDuration = NewType(
    name='ForecastDuration',
    typ=int,
    field=fields.Function,
    deserialize=lambda s: isodate.parse_duration(s),
    serialize=lambda f: isodate.duration_isoformat(f.resolution),
)


ForecastBeginList = NewType(
    name='ForecastBeginList',
    typ=List[datetime],
    field=fields.Function,
    serialize=lambda f: [begin.isoformat() for begin in f.get_begins()],
)


ForecastEndList = NewType(
    name='ForecastEndList',
    typ=List[datetime],
    field=fields.Function,
    serialize=lambda f: [end.isoformat() for end in f.get_ends()],
)


@dataclass
class Forecast:
    """
    TODO
    """
    id: str
    sender: str
    recipient: str
    created: datetime
    begin: datetime
    end: datetime
    sector: str
    reference: str
    forecast: List[int]
    resolution: ForecastDuration
    begins: ForecastBeginList = field(default_factory=list)
    ends: ForecastEndList = field(default_factory=list)

    def get_begins(self):
        """
        :rtype: list[datetime]
        """
        return [
            self.begin + (self.resolution * i)
            for i in range(len(self.forecast))
        ]

    def get_ends(self):
        """
        :rtype: list[datetime]
        """
        return [begin + self.resolution for begin in self.get_begins()]


# -- FindSuppliers request and response --------------------------------------


@dataclass
class FindSuppliersRequest:
    date_range: DateRange = field(metadata=dict(data_key='dateRange'))
    min_amount: int = field(metadata=dict(data_key='minAmount'))
    min_coverage: float = field(metadata=dict(data_key='minCoverage'))


@dataclass
class FindSuppliersResponse:
    success: bool
    suppliers: List[str]


# -- GetGgoList request and response -----------------------------------------


@dataclass
class GetGgoListRequest:
    filters: GgoFilters
    offset: int = field(default=0)
    limit: int = field(default=None)
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
    utc_offset: int = field(default=0, metadata=dict(data_key='utcOffset'))


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
    utc_offset: int = field(default=0, metadata=dict(data_key='utcOffset'))


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


# -- GetTotalAmount request and response -------------------------------------


@dataclass
class GetTotalAmountRequest:
    filters: GgoFilters


@dataclass
class GetTotalAmountResponse:
    success: bool
    amount: int


# -- GetEcoDeclaration request and response -------------------------------------


class EcoDeclarationResolution(Enum):
    all = 'all'
    year = 'year'
    month = 'month'
    day = 'day'
    hour = 'hour'


@dataclass
class EcoDeclaration:
    emissions: Dict[datetime, Dict[str, float]] = field(metadata=dict(data_key='emissions'))
    emissions_per_wh: Dict[datetime, Dict[str, float]] = field(metadata=dict(data_key='emissionsPerWh'))
    consumed_amount: Dict[datetime, float] = field(metadata=dict(data_key='consumedAmount'))
    retired_amount: Dict[datetime, float] = field(metadata=dict(data_key='retiredAmount'))
    technologies: Dict[datetime, Dict[str, float]]
    total_emissions: Dict[str, float] = field(metadata=dict(data_key='totalEmissions'))
    total_emissions_per_wh: Dict[str, Any] = field(metadata=dict(data_key='totalEmissionsPerWh'))
    total_consumed_amount: int = field(metadata=dict(data_key='totalConsumedAmount'))
    total_retired_amount: int = field(metadata=dict(data_key='totalRetiredAmount'))
    total_technologies: Dict[str, int] = field(metadata=dict(data_key='totalTechnologies'))

    @classmethod
    def empty(cls):
        return cls(
            emissions={},
            emissions_per_wh={},
            consumed_amount={},
            retired_amount={},
            technologies={},
            total_emissions={},
            total_emissions_per_wh={},
            total_consumed_amount=0,
            total_retired_amount=0,
            total_technologies={},
        )


@dataclass
class GetEcoDeclarationRequest:
    gsrn: List[str]
    resolution: EcoDeclarationResolution
    begin_range: DateTimeRange = field(metadata=dict(data_key='beginRange'))
    utc_offset: int = field(metadata=dict(data_key='utcOffset'))


@dataclass
class GetEcoDeclarationResponse:
    success: bool
    general: EcoDeclaration
    individual: EcoDeclaration


# -- GetForecast request and response ----------------------------------------


@dataclass
class GetForecastRequest:
    id: str
    reference: str = field(default=None)
    at_time: datetime = field(default=None, metadata=dict(data_key='atTime'))


@dataclass
class GetForecastResponse:
    success: bool
    forecast: Forecast


# -- GetForecastList request and response ------------------------------------


@dataclass
class GetForecastListRequest:
    offset: int = field(default=0)
    limit: int = field(default=None)
    reference: str = field(default=None)
    at_time: datetime = field(default=None, metadata=dict(data_key='atTime'))


@dataclass
class GetForecastListResponse:
    success: bool
    total: int
    forecasts: List[Forecast]


# -- GetForecastSeries request and response ----------------------------------


@dataclass
class GetForecastSeriesResponse:
    success: bool
    sent: List[str]
    received: List[str]


# -- SubmitForecast request and response -------------------------------------


@dataclass
class SubmitForecastRequest:
    account: str
    reference: str
    sector: str
    begin: datetime
    resolution: str
    forecast: List[int]


@dataclass
class SubmitForecastResponse:
    success: bool
    id: str


# -- Webhooks request and response -------------------------------------------


@dataclass
class WebhookSubscribeRequest:
    url: str
    secret: str


@dataclass
class WebhookSubscribeResponse:
    success: bool
