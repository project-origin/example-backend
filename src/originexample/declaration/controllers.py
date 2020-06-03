import marshmallow_dataclass as md

from originexample.http import Controller
from originexample.common import DateTimeRange
from originexample.auth import User, requires_login
from originexample.services import SummaryResolution
from originexample.services import account as acc
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

from .models import (
    EmissionValues,
    GetEcoDeclarationRequest,
    GetEcoDeclarationResponse,
)


datahub = DataHubService()
account_service = AccountService()
energy_service = EnergyDataService()


class GetEcoDeclaration(Controller):
    """
    TODO
    """
    Request = md.class_schema(GetEcoDeclarationRequest)
    Response = md.class_schema(GetEcoDeclarationResponse)

    @requires_login
    def handle_request(self, request, user):
        """
        :param GetEcoDeclarationRequest request:
        :param User user:
        :rtype: GetEcoDeclarationResponse
        """

        # Measurements mapped by their begin
        measurements = self.get_consmued_measurements(
            user, request.date_range)

        # GGOs mapped by begin
        ggos = {ggo.begin: ggo for ggo in
                self.get_retired_ggos(user, request.date_range)}

        # ElectricityBalances mapped by begin
        ebs = {eb.hour_utc: eb for eb in
               self.get_electricity_balance(request.date_range)}

        general = []
        individual = []

        for measurement in measurements:
            ggo = ggos.get(measurement.begin)
            eb = ebs.get(measurement.begin)

            general.append(
                EmissionValues.from_general_electricity_balance(eb))


        # return GetEcoDeclarationResponse(
        #     success=True,
        #     distributions=bundle,
        # )

    def get_consmued_measurements(self, user, date_range):
        """
        :param User user:
        :param DateRange date_range:
        :rtype: collections.abc.Iterable[Measurement]
        """
        offset = 0
        limit = 100

        filters = MeasurementFilters(
            begin_range=DateTimeRange.from_date_range(date_range),
            type=MeasurementType.CONSUMPTION,
        )

        while 1:
            response = datahub.get_measurement_list(
                token=user.access_token,
                request=GetMeasurementListRequest(
                    offset=offset,
                    limit=limit,
                    filters=filters,
                ),
            )

            yield from response.measurements

            offset += limit

            if offset >= response.total:
                break

    def get_retired_ggos(self, user, date_range):
        """
        :param User user:
        :param DateRange date_range:
        :rtype: collections.abc.Iterable[Ggo]
        """

        response = account_service.get_ggo_summary(
            token=user.access_token,
            request=acc.GetGgoSummaryRequest(
                resolution=SummaryResolution.ALL,
                fill=False,
                grouping=[acc.SummaryGrouping.TECHNOLOGY],
                filters=acc.GgoFilters(
                    category=category,
                    begin_range=begin_range,
                )
            ),
        )

        return response.groups

    def get_electricity_balance(self, date_range):
        """
        :param DateRange date_range:
        :rtype: collections.abc.Iterable[ElectricityBalance]
        """

    def get_general_declaration(self, electricity_balances):
        """
        :param list[ElectricityBalance] electricity_balances:
        """
