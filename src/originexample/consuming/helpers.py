from originexample.services.datahub import (
    DataHubService,
    GetMeasurementRequest,
)
from originexample.services.account import (
    GgoCategory,
    AccountService,
    TransferFilters,
    TransferDirection,
    GetTransferredAmountRequest,
    GetTotalAmountRequest,
    GgoFilters,
    GetGgoListRequest)


account_service = AccountService()
datahub_service = DataHubService()


def get_consumption(token, gsrn, begin):
    """
    :param str token:
    :param str gsrn:
    :param datetime.datetime begin:
    :rtype: Measurement
    """
    request = GetMeasurementRequest(gsrn=gsrn, begin=begin)
    response = datahub_service.get_consumption(token, request)
    return response.measurement


def get_stored_amount(token, begin):
    """
    :param str token:
    :param datetime.datetime begin:
    :rtype: int
    """
    request = GetTotalAmountRequest(
        filters=GgoFilters(
            begin=begin,
            category=GgoCategory.STORED,
        )
    )
    response = account_service.get_total_amount(token, request)
    return response.amount


def get_retired_amount(token, gsrn, measurement):
    """
    :param str token:
    :param str gsrn:
    :param Measurement measurement:
    :rtype: int
    """
    request = GetTotalAmountRequest(
        filters=GgoFilters(
            retire_gsrn=[gsrn],
            retire_address=[measurement.address],
            category=GgoCategory.RETIRED,
        )
    )
    response = account_service.get_total_amount(token, request)
    return response.amount


def get_transferred_amount(token, reference, begin):
    """
    :param str token:
    :param str reference:
    :param datetime.datetime begin:
    :rtype: int
    """
    request = GetTransferredAmountRequest(
        direction=TransferDirection.OUTBOUND,
        filters=TransferFilters(
            reference=[reference],
            begin=begin,
        )
    )
    response = account_service.get_transferred_amount(token, request)
    return response.amount


def ggo_is_available(token, ggo):
    """
    Check whether a GGO is available for transferring/retiring.

    :param str token:
    :param Ggo ggo:
    :rtype: bool
    """
    request = GetGgoListRequest(
        filters=GgoFilters(
            address=[ggo.address],
            category=GgoCategory.STORED,
        )
    )
    response = account_service.get_ggo_list(token, request)
    return len(response.results) > 0
