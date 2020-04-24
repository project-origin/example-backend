from enum import Enum
from typing import List
from itertools import zip_longest
from dataclasses import dataclass, field
from marshmallow_dataclass import NewType


class MeasurementType(Enum):
    PRODUCTION = 'production'
    CONSUMPTION = 'consumption'


class SummaryResolution(Enum):
    """
    TODO
    """
    ALL = 'all'
    YEAR = 'year'
    MONTH = 'month'
    DAY = 'day'
    HOUR = 'hour'


SummaryGroupValue = NewType('SummaryGroupValue', int, allow_none=True)


@dataclass
class SummaryGroup:
    """
    TODO
    """
    group: List[str] = field(default_factory=list)
    values: List[SummaryGroupValue] = field(default_factory=list)

    def __add__(self, other):
        """
        :param SummaryGroup other:
        :rtype: SummaryGroup
        """
        if not isinstance(other, SummaryGroup):
            return NotImplemented

        values = []

        for v1, v2 in zip_longest(self.values, other.values, fillvalue=None):
            if v1 is not None and v2 is not None:
                values.append(v1 + v2)
            elif v1 is not None:
                values.append(v1)
            elif v2 is not None:
                values.append(v2)
            else:
                values.append(None)

        return SummaryGroup(self.group, values)

    def __radd__(self, other):
        """
        :param SummaryGroup other:
        :rtype: SummaryGroup
        """
        return self + other
