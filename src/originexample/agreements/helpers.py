from datetime import datetime, timedelta

from originexample.common import DateTimeRange, DataSet
from originexample.services.account import (
    AccountService,
    SummaryGrouping,
    TransferFilters,
    GetTransferSummaryRequest,
    summarize_technologies,
)


class TransferSummaryCollector(object):
    """
    TODO
    """

    GROUPING = [
        SummaryGrouping.TECHNOLOGY_CODE,
        SummaryGrouping.FUEL_CODE,
    ]

    service = AccountService()

    def get_measurements(self, token, reference, date_from, date_to, resolution):
        """
        :param str token:
        :param str reference:
        :param date date_from:
        :param date date_to:
        :param TransferResolution resolution:
        :rtype: (list[DataSet], list[str])
        """
        summary_groups, labels = self.fetch_summary_groups(
            token=token,
            reference=reference,
            date_from=date_from,
            date_to=date_to,
            resolution=resolution,
        )

        summarized = summarize_technologies(summary_groups, self.GROUPING)
        ggos = [DataSet(tech, sg.values) for tech, sg in summarized]

        return ggos, labels

    def fetch_summary_groups(self, token, reference, date_from, date_to, resolution):
        """
        :param str token:
        :param str reference:
        :param date date_from:
        :param date date_to:
        :param TransferResolution resolution:
        :rtype: (list[GgoSummaryGroup], list[str])
        """
        begin_from = datetime.combine(date_from, datetime.min.time())
        begin_to = datetime.combine(date_to, datetime.min.time()) + timedelta(days=1)

        if reference:
            ref = [reference]
        else:
            ref = []

        request = GetTransferSummaryRequest(
            fill=True,
            resolution=resolution,
            grouping=self.GROUPING,
            filters=TransferFilters(
                begin_range=DateTimeRange(begin_from, begin_to),
                reference=ref,
            ),
        )

        response = self.service.get_transfer_summary(token, request)

        if not response.success:
            raise RuntimeError('Request to Account Service failed')

        return response.groups, response.labels
