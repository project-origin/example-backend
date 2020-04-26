from typing import List
from dataclasses import dataclass, field

from originexample.common import DateRange, DataSet
from originexample.services import MeasurementType
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
    date_range: DateRange = field(metadata=dict(data_key='dateRange'))


@dataclass
class GetGgoDistributionsResponse:
    success: bool
    distributions: GgoDistributionBundle


# -- GetMeasurements request and response ------------------------------------


@dataclass
class GetMeasurementsRequest:
    date_range: DateRange = field(metadata=dict(data_key='dateRange'))
    measurement_type: MeasurementType = field(metadata=dict(data_key='measurementType', by_value=True))
    filters: FacilityFilters = field(default=None)


@dataclass
class GetMeasurementsResponse:
    success: bool
    labels: List[str] = field(default_factory=list)
    measurements: DataSet = None
    ggos: List[DataSet] = field(default_factory=list)
