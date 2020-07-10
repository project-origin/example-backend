from dataclasses import dataclass, field

from originexample.common import DateTimeRange
from originexample.facilities import FacilityFilters
from originexample.services.account import (
    EcoDeclarationResolution,
    GetEcoDeclarationResponse,
)


@dataclass
class GetEcoDeclarationRequest:
    filters: FacilityFilters
    resolution: EcoDeclarationResolution
    begin_range: DateTimeRange = field(metadata=dict(data_key='beginRange'))
