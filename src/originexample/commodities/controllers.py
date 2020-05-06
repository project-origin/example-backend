from functools import partial

import marshmallow_dataclass as md

from originexample.http import Controller
from originexample.db import inject_session
from originexample.facilities import FacilityQuery
from originexample.common import DataSet, DateTimeRange
from originexample.auth import User, requires_login
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
    GetTransferSummaryRequest,
    TransferFilters,
    TransferDirection,
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

    def get_issued(self, token, begin_range):
        """
        :param str token:
        :param DateTimeRange begin_range:
        :rtype: GgoDistribution
        """
        return self.get_and_summarize_distributions(partial(
            self.get_ggo_summary,
            token,
            begin_range,
            GgoCategory.ISSUED,
        ))

    def get_stored(self, token, begin_range):
        """
        :param str token:
        :param DateTimeRange begin_range:
        :rtype: GgoDistribution
        """
        return self.get_and_summarize_distributions(partial(
            self.get_ggo_summary,
            token,
            begin_range,
            GgoCategory.STORED,
        ))

    def get_retired(self, token, begin_range):
        """
        :param str token:
        :param DateTimeRange begin_range:
        :rtype: GgoDistribution
        """
        return self.get_and_summarize_distributions(partial(
            self.get_ggo_summary,
            token,
            begin_range,
            GgoCategory.RETIRED,
        ))

    def get_expired(self, token, begin_range):
        """
        :param str token:
        :param DateTimeRange begin_range:
        :rtype: GgoDistribution
        """
        return self.get_and_summarize_distributions(partial(
            self.get_ggo_summary,
            token,
            begin_range,
            GgoCategory.EXPIRED,
        ))

    def get_inbound(self, token, begin_range):
        """
        :param str token:
        :param DateTimeRange begin_range:
        :rtype: GgoDistribution
        """
        return self.get_and_summarize_distributions(partial(
            self.get_transfer_summary,
            token,
            begin_range,
            TransferDirection.INBOUND,
        ))

    def get_outbound(self, token, begin_range):
        """
        :param str token:
        :param DateTimeRange begin_range:
        :rtype: GgoDistribution
        """
        return self.get_and_summarize_distributions(partial(
            self.get_transfer_summary,
            token,
            begin_range,
            TransferDirection.OUTBOUND,
        ))

    def get_and_summarize_distributions(self, get_summary_groups):
        """
        :param function get_summary_groups: A function which returns a
            list of SummaryGroup objects
        :rtype: GgoDistribution
        """
        summarized = summarize_technologies(get_summary_groups(), [
            SummaryGrouping.TECHNOLOGY_CODE,
            SummaryGrouping.FUEL_CODE,
        ])

        distribution = GgoDistribution()

        for technology, summary_group in summarized:
            distribution.technologies.append(GgoTechnology(
                technology=technology,
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
        response = self.service.get_ggo_summary(token, GetGgoSummaryRequest(
            resolution=SummaryResolution.ALL,
            fill=False,
            filters=GgoFilters(
                category=category,
                begin_range=begin_range,
            ),
            grouping=[
                SummaryGrouping.TECHNOLOGY_CODE,
                SummaryGrouping.FUEL_CODE,
            ],
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
        response = self.service.get_transfer_summary(token, GetTransferSummaryRequest(
            direction=direction,
            resolution=SummaryResolution.ALL,
            fill=False,
            filters=TransferFilters(begin_range=begin_range),
            grouping=[
                SummaryGrouping.TECHNOLOGY_CODE,
                SummaryGrouping.FUEL_CODE,
            ],
        ))

        return response.groups


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
            ggo_filters = GgoFilters(
                begin_range=begin_range,
                category=GgoCategory.ISSUED,
                issue_gsrn=gsrn,
            )
        elif request.measurement_type == MeasurementType.CONSUMPTION:
            ggo_filters = GgoFilters(
                begin_range=begin_range,
                category=GgoCategory.RETIRED,
                retire_gsrn=gsrn,
            )
        else:
            raise RuntimeError('Should NOT have happened!')

        ggos, labels = self.get_ggo_summary(
            user.access_token, resolution, ggo_filters)

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

    def get_ggo_summary(self, token, resolution, filters):
        """
        :param str token:
        :param SummaryResolution resolution:
        :param GgoFilters filters:
        :rtype: (list[DataSet], list[str])
        """
        grouping = [
            SummaryGrouping.TECHNOLOGY_CODE,
            SummaryGrouping.FUEL_CODE,
        ]

        request = GetGgoSummaryRequest(
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
