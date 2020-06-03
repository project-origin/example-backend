from dataclasses import fields
from datetime import datetime
from itertools import count
from functools import lru_cache

from originexample.auth import User
from originexample.common import DateTimeRange
from originexample.services.account import AccountService, Ggo
from originexample.services.energidataservice import (
    ElectricityBalance,
    EnergyDataService,
)
from originexample.services.datahub import (
    DataHubService,
    Measurement,
    MeasurementType,
    MeasurementFilters,
    GetMeasurementListRequest,
    DateRange,
)

from .models import EmissionValues
from .emission import (
    biomass,
    coal,
    hydro,
    naturalgas,
    oil,
    other_renewable,
    solar,
    waste,
    wind,
    nuclear,
)


datahub = DataHubService()
account_service = AccountService()
energy_data_service = EnergyDataService()


class EnvironmentDeclaration(object):

    def __init__(self, user, date_range):
        """
        :param User user:
        :param DateRange date_range:
        """
        self.access_token = user.access_token
        self.date_range = date_range

    @property
    def actual_begins(self):
        """
        :rtype: list[datetime]
        """
        return [m.begin for m in self.measurements]

    @property
    def begin(self):
        """
        :rtype: datetime
        """
        return self.date_range.begin
        return min(self.actual_begins)

    @property
    def end(self):
        """
        :rtype: datetime
        """
        return self.date_range.end
        return max(self.actual_begins)

    @property
    def general(self):
        """
        :rtype: EmissionValues
        """
        return sum(self.electricity_balances) / len(self.electricity_balances)

    @property
    def individual(self):
        """
        :rtype: EmissionValues
        """

    @property
    @lru_cache()
    def measurements(self):
        """
        Returns a list of all Consumed measurements in the period.

        :rtype: list[Measurement]
        """
        measurements = []

        for offset in count(0, 250):
            request = GetMeasurementListRequest(
                offset=offset,
                limit=250,
                filters=MeasurementFilters(
                    begin_range=DateTimeRange.from_date_range(self.date_range),
                    type=MeasurementType.CONSUMPTION,
                ),
            )

            response = datahub.get_measurement_list(
                token=self.access_token,
                request=request,
            )

            measurements.extend(response.measurements)

            if offset >= response.total:
                break

        return measurements

    @property
    @lru_cache()
    def electricity_balances(self):
        """
        Imports the general electricity balance from EnergyDataService for
        the duration of the user's consumption measurements (begin-end).
        Each item contains the amount of energy used in Denmark for a period
        of time, grouped by the type of technology (solar, wind, etc.)

        Returns a list of emission values, one for each period.

        :rtype: list[EmissionValues]
        """
        response = energy_data_service.get_electricity_balance(
            self.begin, self.end)

        return list(map(
            self.emission_values_from_energy_balance,
            response.result.records,
        ))

    def emission_values_from_energy_balance(self, eb):
        """
        :param ElectricityBalance eb:
        :rtype: EmissionValues
        """
        mappers = (
            ('biomass', biomass),
            ('coal', coal),
            ('hydro', hydro),
            ('naturalgas', naturalgas),
            ('oil', oil),
            ('solar', solar),
            ('waste', waste),
            ('wind', wind),
            ('other_renewable', other_renewable),
        )

        init_kwargs = {}

        for f in fields(EmissionValues):
            sum_of_emissions = sum(
                getattr(eb, attr) * getattr(mapper, f.name)
                for attr, mapper in mappers
            )

            if eb.total > 0:
                init_kwargs[f.name] = sum_of_emissions / eb.total

        return EmissionValues(**init_kwargs)
