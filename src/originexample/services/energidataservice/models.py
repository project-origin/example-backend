from typing import List
from datetime import datetime
from dataclasses import dataclass, field
from marshmallow import EXCLUDE


MWh = 10 ** 6


@dataclass
class ElectricityBalance:
    biomass_mwh: float = field(default=0, metadata=dict(data_key='Biomass', allow_none=True))
    onshore_wind_power_mwh: float = field(default=0, metadata=dict(data_key='OnshoreWindPower', allow_none=True))
    offshore_wind_power_mwh: float = field(default=0, metadata=dict(data_key='OffshoreWindPower', allow_none=True))
    hydro_power_mwh: float = field(default=0, metadata=dict(data_key='HydroPower', allow_none=True))
    waste_mwh: float = field(default=0, metadata=dict(data_key='Waste', allow_none=True))
    solar_power_mwh: float = field(default=0, metadata=dict(data_key='SolarPower', allow_none=True))
    fossil_gas_mwh: float = field(default=0, metadata=dict(data_key='FossilGas', allow_none=True))
    fossil_hard_coal_mwh: float = field(default=0, metadata=dict(data_key='FossilHardCoal', allow_none=True))
    fossil_oil_mwh: float = field(default=0, metadata=dict(data_key='FossilOil', allow_none=True))
    other_renewable_mwh: float = field(default=0, metadata=dict(data_key='OtherRenewable', allow_none=True))
    total_load_mwh: float = field(default=0, metadata=dict(data_key='TotalLoad', allow_none=True))

    hour_utc: datetime = field(default=None, metadata=dict(data_key='HourUTC'))
    hour_dk: datetime = field(default=None, metadata=dict(data_key='HourDK'))
    price_area: str = field(default=None, metadata=dict(data_key='PriceArea'))

    class Meta:
        unknown = EXCLUDE

    @property
    def biomass(self):
        """
        :rtype: float
        :returns: Watt per hour
        """
        return self.biomass_mwh * MWh if self.biomass_mwh else 0

    @property
    def coal(self):
        """
        :rtype: float
        :returns: Watt per hour
        """
        return self.fossil_hard_coal_mwh * MWh if self.fossil_hard_coal_mwh else 0

    @property
    def hydro(self):
        """
        :rtype: float
        :returns: Watt per hour
        """
        return self.hydro_power_mwh * MWh if self.hydro_power_mwh else 0

    @property
    def naturalgas(self):
        """
        :rtype: float
        :returns: Watt per hour
        """
        return self.fossil_gas_mwh * MWh if self.fossil_gas_mwh else 0

    @property
    def oil(self):
        """
        :rtype: float
        :returns: Watt per hour
        """
        return self.fossil_oil_mwh * MWh if self.fossil_oil_mwh else 0

    @property
    def solar(self):
        """
        :rtype: float
        :returns: Watt per hour
        """
        return self.solar_power_mwh * MWh if self.solar_power_mwh else 0

    @property
    def waste(self):
        """
        :rtype: float
        :returns: Watt per hour
        """
        return self.waste_mwh * MWh if self.waste_mwh else 0

    @property
    def wind_onshore(self):
        """
        :rtype: float
        :returns: Watt per hour
        """
        return self.onshore_wind_power_mwh * MWh if self.onshore_wind_power_mwh else 0

    @property
    def wind_offshore(self):
        """
        :rtype: float
        :returns: Watt per hour
        """
        return self.offshore_wind_power_mwh * MWh if self.offshore_wind_power_mwh else 0

    @property
    def wind(self):
        """
        :rtype: float
        :returns: Watt per hour
        """
        return self.wind_onshore + self.wind_offshore

    @property
    def other_renewable(self):
        """
        :rtype: float
        :returns: Watt per hour
        """
        return self.other_renewable_mwh * MWh if self.other_renewable_mwh else 0

    @property
    def total(self):
        """
        :rtype: float
        """
        return sum([
            self.biomass,
            self.coal,
            self.hydro,
            self.naturalgas,
            self.oil,
            self.solar,
            self.waste,
            self.wind,
            self.other_renewable,
        ])


@dataclass
class GetElectricityBalanceResult:
    records: List[ElectricityBalance]

    class Meta:
        unknown = EXCLUDE


@dataclass
class GetElectricityBalanceResponse:
    success: bool
    result: GetElectricityBalanceResult

    class Meta:
        unknown = EXCLUDE
