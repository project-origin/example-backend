from dataclasses import dataclass, field

from originexample.common import DateRange
from originexample.facilities import FacilityFilters
from originexample.services.account import (
    EcoDeclarationResolution,
    GetEcoDeclarationResponse,
)


@dataclass
class GetEcoDeclarationRequest:
    filters: FacilityFilters
    resolution: EcoDeclarationResolution
    date_range: DateRange = field(metadata=dict(data_key='dateRange'))

    # Offset from UTC in hours
    utc_offset: int = field(metadata=dict(data_key='utcOffset'))
