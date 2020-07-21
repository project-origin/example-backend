from typing import List
from dataclasses import dataclass, field

from originexample.common import DateRange, DataSet
from originexample.services import MeasurementType
from originexample.services.account import GgoCategory
from originexample.facilities import FacilityFilters


# -- Common ------------------------------------------------------------------


@dataclass
class GgoTechnology:
    technology: str
    amount: int
    unit: str = 'Wh'


@dataclass
class GgoDistribution:
    technologies: List[GgoTechnology] = field(default_factory=list)

    @property
    def total(self):
        return sum(t.amount for t in self.technologies)

    @property
    def unit(self):
        return 'Wh'


@dataclass
class GgoDistributionBundle:
    issued: GgoDistribution = field(default_factory=GgoDistribution)
    stored: GgoDistribution = field(default_factory=GgoDistribution)
    retired: GgoDistribution = field(default_factory=GgoDistribution)
    expired: GgoDistribution = field(default_factory=GgoDistribution)
    inbound: GgoDistribution = field(default_factory=GgoDistribution)
    outbound: GgoDistribution = field(default_factory=GgoDistribution)


# -- GetGgoDistributions request and response --------------------------------


@dataclass
class GetGgoDistributionsRequest:
    utc_offset: int = field(metadata=dict(required=False, missing=0, data_key='utcOffset'))
    date_range: DateRange = field(metadata=dict(data_key='dateRange'))


@dataclass
class GetGgoDistributionsResponse:
    success: bool
    distributions: GgoDistributionBundle


# -- GetGgoSummary request and response --------------------------------------


@dataclass
class GetGgoSummaryRequest:
    utc_offset: int = field(metadata=dict(required=False, missing=0, data_key='utcOffset'))
    category: GgoCategory = field(metadata=dict(by_value=True))
    date_range: DateRange = field(metadata=dict(data_key='dateRange'))


@dataclass
class GetGgoSummaryResponse:
    success: bool
    labels: List[str] = field(default_factory=list)
    ggos: List[DataSet] = field(default_factory=list)


# -- GetMeasurements request and response ------------------------------------


@dataclass
class GetMeasurementsRequest:
    utc_offset: int = field(metadata=dict(required=False, missing=0, data_key='utcOffset'))
    date_range: DateRange = field(metadata=dict(data_key='dateRange'))
    filters: FacilityFilters = field(default=None)
    measurement_type: MeasurementType = field(default=None, metadata=dict(data_key='measurementType', by_value=True))


@dataclass
class GetMeasurementsResponse:
    success: bool
    measurements: DataSet = None
