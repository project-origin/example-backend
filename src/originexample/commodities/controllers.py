import marshmallow_dataclass as md

from originexample.http import Controller
from originexample.db import inject_session
from originexample.facilities import FacilityQuery
from originexample.common import DataSet, DateTimeRange
from originexample.auth import User, requires_login, inject_user
from originexample.services import SummaryResolution

from originexample.services.datahub import (
    DataHubService,
    GetMeasurementSummaryRequest,
    MeasurementFilters,
)

from originexample.services.account import (
    AccountService,
    GgoFilters,
    GgoCategory,
    SummaryGrouping,
    summarize_technologies,
    GetGgoSummaryRequest,
)

from .models import (
    MeasurementType,
    GgoTechnology,
    GgoDistribution,
    GgoDistributionBundle,
    GetGgoDistributionsRequest,
    GetGgoDistributionsResponse,
    GetMeasurementsRequest,
    GetMeasurementsResponse,
)


class GetGgoDistributions(Controller):
    """
    TODO
    """
    Request = md.class_schema(GetGgoDistributionsRequest)
    Response = md.class_schema(GetGgoDistributionsResponse)

    service = AccountService()

    @requires_login
    def handle_request(self, request, user):
        """
        :param GetGgoDistributionsRequest request:
        :param User user:
        :rtype: GetGgoDistributionsResponse
        """
        # gsrn = self.get_gsrn_numbers(user, request.filters)
        #
        # if not gsrn:
        #     return GetMeasurementsResponse(success=True)
        #
        # distributions = self.collector.get_ggo_distribution_bundle(
        #     token=token,
        #     gsrn=gsrn,
        #     date_from=request.date.begin,
        #     date_to=request.date.end,
        # )

        bundle = GgoDistributionBundle(
            issued=self.get_issued(request, user.access_token),
            stored=self.get_stored(request, user.access_token),
            retired=self.get_retired(request, user.access_token),
            expired=self.get_expired(request, user.access_token),
        )

        return GetGgoDistributionsResponse(
            success=True,
            distributions=bundle,
        )

    # @inject_session
    # def get_gsrn_numbers(self, user, filters, session):
    #     """
    #     :param User user:
    #     :param FacilityFilters filters:
    #     :param Session session:
    #     :rtype: list[str]
    #     """
    #     query = FacilityQuery(session) \
    #         .belongs_to(user)
    #
    #     if filters is not None:
    #         query = query.apply_filters(filters)
    #
    #     return query.get_distinct_gsrn()

    def get_issued(self, request, token):
        """
        :param GetGgoDistributionsRequest request:
        :param str token:
        :rtype: GgoDistribution
        """
        return self.get_ggo_distributions(request, token, GgoCategory.ISSUED)

    def get_stored(self, request, token):
        """
        :param GetGgoDistributionsRequest request:
        :param str token:
        :rtype: GgoDistribution
        """
        return self.get_ggo_distributions(request, token, GgoCategory.STORED)

    def get_retired(self, request, token):
        """
        :param GetGgoDistributionsRequest request:
        :param str token:
        :rtype: GgoDistribution
        """
        return self.get_ggo_distributions(request, token, GgoCategory.RETIRED)

    def get_expired(self, request, token):
        """
        :param GetGgoDistributionsRequest request:
        :param str token:
        :rtype: GgoDistribution
        """
        return self.get_ggo_distributions(request, token, GgoCategory.EXPIRED)

    def get_ggo_distributions(self, request, token, category):
        """
        :param GetGgoDistributionsRequest request:
        :param str token:
        :param GgoCategory category:
        :rtype: GgoDistribution
        """
        grouping = [
            SummaryGrouping.TECHNOLOGY_CODE,
            SummaryGrouping.FUEL_CODE,
        ]

        begin_range = DateTimeRange.from_date_range(request.date_range)

        response = self.service.get_ggo_summary(token, GetGgoSummaryRequest(
            category=category,
            resolution=SummaryResolution.ALL,
            grouping=grouping,
            fill=False,
            filters=GgoFilters(begin_range=begin_range),
        ))

        distribution = GgoDistribution()

        summarized = summarize_technologies(response.groups, grouping)

        for technology, summary_group in summarized:
            distribution.technologies.append(GgoTechnology(
                technology=technology,
                amount=sum(summary_group.values),
            ))

        return distribution


class GetMeasurements(Controller):
    """
    TODO
    """
    Request = md.class_schema(GetMeasurementsRequest)
    Response = md.class_schema(GetMeasurementsResponse)

    account = AccountService()
    datahub = DataHubService()

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
        resolution = self.get_resolution(begin_range.delta)

        if request.measurement_type == MeasurementType.PRODUCTION:
            category = GgoCategory.ISSUED
            summary_filters = GgoFilters(begin_range=begin_range, issue_gsrn=gsrn)
        elif request.measurement_type == MeasurementType.CONSUMPTION:
            category = GgoCategory.RETIRED
            summary_filters = GgoFilters(begin_range=begin_range, retire_gsrn=gsrn)
        else:
            raise RuntimeError('Should NOT have happened!')

        ggos, labels = self.get_ggo_summary(
            user.access_token, resolution, category, summary_filters)

        measurements = self.get_measurements(
            user.access_token, request.measurement_type, resolution, begin_range, gsrn)

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

    def get_resolution(self, delta):
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

        response = self.datahub.get_measurement_summary(token, request)
        label = measurement_type.value.capitalize()

        if response.groups:
            return DataSet(label=label, values=response.groups[0].values)
        else:
            return DataSet(label=label)

    def get_ggo_summary(self, token, resolution, category, filters):
        """
        :param str token:
        :param SummaryResolution resolution:
        :param GgoCategory category:
        :param GgoFilters filters:
        :rtype: (list[DataSet], list[str])
        """
        grouping = [
            SummaryGrouping.TECHNOLOGY_CODE,
            SummaryGrouping.FUEL_CODE,
        ]

        request = GetGgoSummaryRequest(
            category=category,
            filters=filters,
            resolution=resolution,
            grouping=grouping,
            fill=True,
        )

        response = self.account.get_ggo_summary(token, request)
        summarized = summarize_technologies(response.groups, grouping)
        datasets = []

        for technology, summary_group in summarized:
            datasets.append(DataSet(
                label=technology,
                values=summary_group.values,
            ))

        return datasets, response.labels
