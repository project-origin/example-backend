import csv
import marshmallow_dataclass as md
from io import StringIO
from functools import partial
from flask import make_response

from originexample.http import Controller
from originexample.db import inject_session
from originexample.facilities import FacilityQuery, Facility, FacilityFilters, get_technology
from originexample.common import DataSet, DateTimeRange
from originexample.auth import User, requires_login
from originexample.services import SummaryResolution
from originexample.services.datahub import (
    DataHubService,
    GetMeasurementSummaryRequest,
    MeasurementFilters,
    SummaryGroup,
)
from originexample.services import account as acc
# from originexample.services.account import (
#     AccountService,
#     GgoFilters,
#     GgoCategory,
#     SummaryGrouping,
#     summarize_technologies,
#     GetGgoSummaryRequest,
#     GetTransferSummaryRequest,
#     TransferFilters,
#     TransferDirection,
#     GetGgoListRequest,
#     Ggo,
# )

from .models import (
    MeasurementType,
    GgoTechnology,
    GgoDistribution,
    GgoDistributionBundle,
    GetGgoDistributionsRequest,
    GetGgoDistributionsResponse,
    GetMeasurementsRequest,
    GetMeasurementsResponse,
    GetGgoSummaryRequest, GetGgoSummaryResponse)


account_service = acc.AccountService()
datahub_service = DataHubService()


def get_resolution(delta):
    """
    :param timedelta delta:
    :rtype: SummaryResolution
    """
    if delta.days >= (365 * 3):
        return SummaryResolution.YEAR
    elif delta.days >= 60:
        return SummaryResolution.MONTH
    elif delta.days >= 3:
        return SummaryResolution.DAY
    else:
        return SummaryResolution.HOUR


class GetGgoDistributions(Controller):
    """
    TODO
    """
    Request = md.class_schema(GetGgoDistributionsRequest)
    Response = md.class_schema(GetGgoDistributionsResponse)

    @requires_login
    def handle_request(self, request, user):
        """
        :param GetGgoDistributionsRequest request:
        :param User user:
        :rtype: GetGgoDistributionsResponse
        """
        begin_range = DateTimeRange.from_date_range(request.date_range)

        bundle = GgoDistributionBundle(
            issued=self.get_issued(user.access_token, begin_range),
            stored=self.get_stored(user.access_token, begin_range),
            retired=self.get_retired(user.access_token, begin_range),
            expired=self.get_expired(user.access_token, begin_range),
            inbound=self.get_inbound(user.access_token, begin_range),
            outbound=self.get_outbound(user.access_token, begin_range),
        )

        return GetGgoDistributionsResponse(
            success=True,
            distributions=bundle,
        )

    def get_issued(self, token, begin_range):
        """
        :param str token:
        :param DateTimeRange begin_range:
        :rtype: GgoDistribution
        """
        return self.get_distributions(partial(
            self.get_ggo_summary,
            token,
            begin_range,
            acc.GgoCategory.ISSUED,
        ))

    def get_stored(self, token, begin_range):
        """
        :param str token:
        :param DateTimeRange begin_range:
        :rtype: GgoDistribution
        """
        return self.get_distributions(partial(
            self.get_ggo_summary,
            token,
            begin_range,
            acc.GgoCategory.STORED,
        ))

    def get_retired(self, token, begin_range):
        """
        :param str token:
        :param DateTimeRange begin_range:
        :rtype: GgoDistribution
        """
        return self.get_distributions(partial(
            self.get_ggo_summary,
            token,
            begin_range,
            acc.GgoCategory.RETIRED,
        ))

    def get_expired(self, token, begin_range):
        """
        :param str token:
        :param DateTimeRange begin_range:
        :rtype: GgoDistribution
        """
        return self.get_distributions(partial(
            self.get_ggo_summary,
            token,
            begin_range,
            acc.GgoCategory.EXPIRED,
        ))

    def get_inbound(self, token, begin_range):
        """
        :param str token:
        :param DateTimeRange begin_range:
        :rtype: GgoDistribution
        """
        return self.get_distributions(partial(
            self.get_transfer_summary,
            token,
            begin_range,
            acc.TransferDirection.INBOUND,
        ))

    def get_outbound(self, token, begin_range):
        """
        :param str token:
        :param DateTimeRange begin_range:
        :rtype: GgoDistribution
        """
        return self.get_distributions(partial(
            self.get_transfer_summary,
            token,
            begin_range,
            acc.TransferDirection.OUTBOUND,
        ))

    def get_distributions(self, get_summary_groups):
        """
        :param function get_summary_groups: A function which returns a
            list of SummaryGroup objects
        :rtype: GgoDistribution
        """
        distribution = GgoDistribution()

        for summary_group in get_summary_groups():
            distribution.technologies.append(GgoTechnology(
                technology=summary_group.group[0],
                amount=sum(summary_group.values),
            ))

        return distribution

    def get_ggo_summary(self, token, begin_range, category):
        """
        Get either Issued, Stored, Retired and Expired from GgoSummary.

        :param str token:
        :param DateTimeRange begin_range:
        :param GgoCategory category:
        :rtype: List[SummaryGroup]
        """
        response = account_service.get_ggo_summary(token, acc.GetGgoSummaryRequest(
            resolution=SummaryResolution.ALL,
            fill=False,
            grouping=[acc.SummaryGrouping.TECHNOLOGY],
            filters=acc.GgoFilters(
                category=category,
                begin_range=begin_range,
            ),
        ))

        return response.groups

    def get_transfer_summary(self, token, begin_range, direction):
        """
        Get either Inbound and Outbound from TransferSummary.

        :param str token:
        :param DateTimeRange begin_range:
        :param TransferDirection direction:
        :rtype: List[SummaryGroup]
        """
        response = account_service.get_transfer_summary(token, acc.GetTransferSummaryRequest(
            direction=direction,
            resolution=SummaryResolution.ALL,
            fill=False,
            grouping=[acc.SummaryGrouping.TECHNOLOGY],
            filters=acc.TransferFilters(begin_range=begin_range),
        ))

        return response.groups


class GetGgoSummary(Controller):
    """
    TODO
    """
    Request = md.class_schema(GetGgoSummaryRequest)
    Response = md.class_schema(GetGgoSummaryResponse)

    def __init__(self, category=None):
        """
        :param GgoCategory category:
        """
        self.category = category

    @requires_login
    def handle_request(self, request, user):
        """
        :param GetGgoSummaryRequest request:
        :param User user:
        :rtype: GetGgoSummaryResponse
        """
        begin_range = DateTimeRange.from_date_range(request.date_range)
        resolution = get_resolution(begin_range.delta)

        ggo_filters = acc.GgoFilters(
            begin_range=begin_range,
            category=request.category,
        )

        ggos, labels = self.get_ggo_summary(
            user.access_token, resolution, ggo_filters)

        return GetGgoSummaryResponse(
            success=True,
            labels=labels,
            ggos=ggos,
        )

    def get_ggo_summary(self, token, resolution, filters):
        """
        :param str token:
        :param SummaryResolution resolution:
        :param GgoFilters filters:
        :rtype: (list[DataSet], list[str])
        """
        request = acc.GetGgoSummaryRequest(
            filters=filters,
            resolution=resolution,
            grouping=[acc.SummaryGrouping.TECHNOLOGY],
            fill=True,
        )

        response = account_service.get_ggo_summary(token, request)
        datasets = [DataSet(g.group[0], g.values) for g in response.groups]

        return datasets, response.labels


class GetMeasurements(Controller):
    """
    TODO
    """
    Request = md.class_schema(GetMeasurementsRequest)
    Response = md.class_schema(GetMeasurementsResponse)

    @requires_login
    def handle_request(self, request, user):
        """
        :param GetMeasurementsRequest request:
        :param User user:
        :rtype: GetMeasurementsResponse
        """
        gsrn = self.get_gsrn_numbers(user, request.filters)

        if not gsrn:
            return GetMeasurementsResponse(success=True)

        begin_range = DateTimeRange.from_date_range(request.date_range)
        resolution = get_resolution(begin_range.delta)

        if request.measurement_type == MeasurementType.PRODUCTION:
            ggo_filters = acc.GgoFilters(
                begin_range=begin_range,
                category=acc.GgoCategory.ISSUED,
                issue_gsrn=gsrn,
            )
        elif request.measurement_type == MeasurementType.CONSUMPTION:
            ggo_filters = acc.GgoFilters(
                begin_range=begin_range,
                category=acc.GgoCategory.RETIRED,
                retire_gsrn=gsrn,
            )
        else:
            raise RuntimeError('Should NOT have happened!')

        ggos, labels = self.get_ggo_summary(
            user.access_token, resolution, ggo_filters)

        measurements = self.get_measurements(
            user.access_token, request.measurement_type,
            resolution, begin_range, gsrn)

        return GetMeasurementsResponse(
            success=True,
            labels=labels,
            ggos=ggos,
            measurements=measurements,
        )

    @inject_session
    def get_gsrn_numbers(self, user, filters, session):
        """
        :param User user:
        :param FacilityFilters filters:
        :param Session session:
        :rtype: list[str]
        """
        query = FacilityQuery(session) \
            .belongs_to(user)

        if filters is not None:
            query = query.apply_filters(filters)

        return query.get_distinct_gsrn()

    def get_measurements(self, token, measurement_type, resolution, begin_range, gsrn):
        """
        :param str token:
        :param MeasurementType measurement_type:
        :param SummaryResolution resolution:
        :param DateTimeRange begin_range:
        :param list[str] gsrn:
        :rtype: DataSet
        """
        request = GetMeasurementSummaryRequest(
            resolution=resolution,
            fill=True,
            filters=MeasurementFilters(
                begin_range=begin_range,
                type=measurement_type,
                gsrn=gsrn,
            ),
        )

        response = datahub_service.get_measurement_summary(token, request)
        label = measurement_type.value.capitalize()

        if response.groups:
            return DataSet(label=label, values=response.groups[0].values)
        else:
            return DataSet(label=label)

    def get_ggo_summary(self, token, resolution, filters):
        """
        :param str token:
        :param SummaryResolution resolution:
        :param GgoFilters filters:
        :rtype: (list[DataSet], list[str])
        """
        request = acc.GetGgoSummaryRequest(
            filters=filters,
            resolution=resolution,
            grouping=[acc.SummaryGrouping.TECHNOLOGY],
            fill=True,
        )

        response = account_service.get_ggo_summary(token, request)
        datasets = [DataSet(g.group[0], g.values) for g in response.groups]

        return datasets, response.labels


# -- CSV EXPORTING -----------------------------------------------------------


class ExportGgoSummaryCSV(Controller):
    """
    Exports a CSV document with the following columns:

    Type | Technology Code | Fuel Code | Technology | Begin | Amount

    Where "Type" is either ISSUED or RETIRED.
    """
    Request = md.class_schema(GetMeasurementsRequest)

    @requires_login
    def handle_request(self, request, user):
        """
        :param GetMeasurementsRequest request:
        :param User user:
        :rtype: flask.Response
        """
        facilities = self.get_facilities(user, request.filters)
        gsrn = [f.gsrn for f in facilities]

        if not gsrn:
            return False

        begin_range = DateTimeRange.from_date_range(request.date_range)
        resolution = get_resolution(begin_range.delta)

        issued, issued_labels = self.get_ggo_summary(
            token=user.access_token,
            resolution=resolution,
            filters=acc.GgoFilters(
                begin_range=begin_range,
                category=acc.GgoCategory.ISSUED,
                issue_gsrn=gsrn,
            ),
        )

        retired, retired_labels = self.get_ggo_summary(
            token=user.access_token,
            resolution=resolution,
            filters=acc.GgoFilters(
                begin_range=begin_range,
                category=acc.GgoCategory.RETIRED,
                retire_gsrn=gsrn,
            ),
        )

        # -- Write CSV -------------------------------------------------------

        csv_file = StringIO()
        csv_writer = csv.writer(
            csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        # Headers
        csv_writer.writerow([
            'Type',
            'TechnologyCode',
            'FuelCode',
            'Technology',
            'Begin',
            'Amount',
        ])

        # Issued GGOs
        for summary_group in issued:
            technology_code, fuel_code = summary_group.group

            for label, amount in zip(issued_labels, summary_group.values):
                csv_writer.writerow([
                    'ISSUED',
                    technology_code,
                    fuel_code,
                    get_technology(technology_code, fuel_code),
                    label,
                    amount,
                ])

        # Retired GGOs
        for summary_group in retired:
            technology_code, fuel_code = summary_group.group

            for label, amount in zip(retired_labels, summary_group.values):
                csv_writer.writerow([
                    'RETIRED',
                    technology_code,
                    fuel_code,
                    get_technology(technology_code, fuel_code),
                    label,
                    amount,
                ])

        # -- HTTP response ---------------------------------------------------

        response = make_response(csv_file.getvalue())
        response.headers["Content-Disposition"] = 'attachment; filename=ggo-summary.csv'
        response.headers["Content-type"] = 'text/csv'

        return response

    @inject_session
    def get_facilities(self, user, filters, session):
        """
        :param User user:
        :param FacilityFilters filters:
        :param Session session:
        :rtype: list[Facility]
        """
        query = FacilityQuery(session) \
            .belongs_to(user)

        if filters is not None:
            query = query.apply_filters(filters)

        return query.all()

    def get_ggo_summary(self, token, resolution, filters):
        """
        :param str token:
        :param SummaryResolution resolution:
        :param GgoFilters filters:
        :rtype: list[SummaryGroup]
        """
        request = acc.GetGgoSummaryRequest(
            resolution=resolution,
            fill=True,
            filters=filters,
            grouping=[
                acc.SummaryGrouping.TECHNOLOGY_CODE,
                acc.SummaryGrouping.FUEL_CODE,
            ],
        )

        response = account_service.get_ggo_summary(token, request)

        return response.groups, response.labels


class ExportGgoListCSV(Controller):
    """
    Exports a CSV document with the following columns:

    Address | Type | Technology Code | Fuel Code | Technology | Begin | Amount | GSRN | Sector

    Where:
    - "Address" is the GGO's address on the ledger
    - "Type" is either ISSUED or RETIRED
    """
    Request = md.class_schema(GetMeasurementsRequest)

    @requires_login
    def handle_request(self, request, user):
        """
        :param GetMeasurementsRequest request:
        :param User user:
        :rtype: flask.Response
        """
        facilities = self.get_facilities(user, request.filters)
        gsrn = [f.gsrn for f in facilities]

        if not gsrn:
            return False

        begin_range = DateTimeRange.from_date_range(request.date_range)

        issued = self.get_ggos(user.access_token, acc.GgoFilters(
            begin_range=begin_range,
            category=acc.GgoCategory.ISSUED,
            issue_gsrn=gsrn,
        ))

        retired = self.get_ggos(user.access_token, acc.GgoFilters(
            begin_range=begin_range,
            category=acc.GgoCategory.RETIRED,
            retire_gsrn=gsrn,
        ))

        # -- Write CSV -------------------------------------------------------

        csv_file = StringIO()
        csv_writer = csv.writer(
            csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        # Headers
        csv_writer.writerow([
            'Address',
            'Type',
            'TechnologyCode',
            'FuelCode',
            'Technology',
            'Begin',
            'Amount',
            'Sector',
        ])

        # Issued GGOs
        for ggo in issued:
            csv_writer.writerow([
                ggo.address,
                'ISSUED',
                ggo.technology_code,
                ggo.fuel_code,
                get_technology(ggo.technology_code, ggo.fuel_code),
                ggo.begin,
                ggo.amount,
                ggo.sector,
            ])

        # Retired GGOs
        for ggo in retired:
            csv_writer.writerow([
                ggo.address,
                'RETIRED',
                ggo.technology_code,
                ggo.fuel_code,
                get_technology(ggo.technology_code, ggo.fuel_code),
                ggo.begin,
                ggo.amount,
                ggo.sector,
            ])

        # -- HTTP response ---------------------------------------------------

        response = make_response(csv_file.getvalue())
        response.headers["Content-Disposition"] = 'attachment; filename=ggo-list.csv'
        response.headers["Content-type"] = 'text/csv'

        return response

    @inject_session
    def get_facilities(self, user, filters, session):
        """
        :param User user:
        :param FacilityFilters filters:
        :param Session session:
        :rtype: list[Facility]
        """
        query = FacilityQuery(session) \
            .belongs_to(user)

        if filters is not None:
            query = query.apply_filters(filters)

        return query.all()

    def get_ggos(self, token, filters):
        """
        :param str token:
        :param GgoFilters filters:
        :rtype: collections.abc.Iterable[Ggo]
        """
        offset = 0
        limit = 100

        while 1:
            response = account_service.get_ggo_list(token, acc.GetGgoListRequest(
                offset=offset,
                limit=limit,
                filters=filters,
            ))

            yield from response.results

            offset += limit

            if offset >= response.total:
                break


class ExportMeasurementsCSV(Controller):
    """
    Exports a CSV document with the following columns:

    GSRN | Facility name | Facility type | Begin | End | Amount

    Where "Facility Type" is either PRODUCTION or CONSUMPTION.
    """
    Request = md.class_schema(GetMeasurementsRequest)

    @requires_login
    def handle_request(self, request, user):
        """
        :param GetMeasurementsRequest request:
        :param User user:
        :rtype: flask.Response
        """
        facilities = self.get_facilities(user, request.filters)
        facilities_mapped = {f.gsrn: f for f in facilities}
        gsrn = [f.gsrn for f in facilities]

        if not gsrn:
            return False

        begin_range = DateTimeRange.from_date_range(request.date_range)
        resolution = get_resolution(begin_range.delta)

        measurements, labels = self.get_measurements(
            user.access_token, resolution, begin_range, gsrn)

        # -- Write CSV -------------------------------------------------------

        csv_file = StringIO()
        csv_writer = csv.writer(
            csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        # Headers
        csv_writer.writerow([
            'GSRN',
            'FacilityName',
            'FacilityType',
            'Begin',
            'Amount',
        ])

        # Measurements
        for summary_group in measurements:
            gsrn = summary_group.group[0]
            facility = facilities_mapped[gsrn]

            for label, amount in zip(labels, summary_group.values):
                csv_writer.writerow([
                    gsrn,
                    facility.name,
                    facility.facility_type,
                    label,
                    amount,
                ])

        # -- HTTP response ---------------------------------------------------

        response = make_response(csv_file.getvalue())
        response.headers["Content-Disposition"] = 'attachment; filename=measurements.csv'
        response.headers["Content-type"] = 'text/csv'

        return response

    @inject_session
    def get_facilities(self, user, filters, session):
        """
        :param User user:
        :param FacilityFilters filters:
        :param Session session:
        :rtype: list[Facility]
        """
        query = FacilityQuery(session) \
            .belongs_to(user)

        if filters is not None:
            query = query.apply_filters(filters)

        return query.all()

    def get_measurements(self, token, resolution, begin_range, gsrn):
        """
        :param str token:
        :param SummaryResolution resolution:
        :param DateTimeRange begin_range:
        :param list[str] gsrn:
        :rtype: list[SummaryGroup]
        """
        request = GetMeasurementSummaryRequest(
            resolution=resolution,
            fill=True,
            grouping=['gsrn'],
            filters=MeasurementFilters(
                begin_range=begin_range,
                gsrn=gsrn,
            ),
        )

        response = datahub_service.get_measurement_summary(token, request)

        return response.groups, response.labels
