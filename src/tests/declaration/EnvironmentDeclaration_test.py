import pytest
from unittest.mock import Mock, patch

from originexample.declaration import EnvironmentDeclaration
from originexample.services.energidataservice import ElectricityBalance


def test__EnvironmentDeclaration__emission_values_from_energy_balance():

    # Arrange
    eb = ElectricityBalance(
        biomass_mwh=209.50,
        fossil_gas_mwh=89.30,
        fossil_hard_coal_mwh=50.70,
        fossil_oil_mwh=10.20,
        hydro_power_mwh=1.10,
        other_renewable_mwh=2.70,
        solar_power_mwh=0.00,
        waste_mwh=82.60,
        onshore_wind_power_mwh=364.40,
        offshore_wind_power_mwh=685.00,
    )

    declaration = EnvironmentDeclaration(Mock(), Mock())

    # Act
    emission_values = declaration.emission_values_from_energy_balance(eb)

    # Assert
    # assert emission_values.carbon_dioxide == 110.1118
    assert emission_values.methane == 0.0518
