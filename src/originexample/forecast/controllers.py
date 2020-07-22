import marshmallow_dataclass as md

from originexample.http import Controller
from originexample.auth import requires_login
from originexample.services import account as acc


account_service = acc.AccountService()


class GetForecast(Controller):
    """
    TODO
    """
    Request = md.class_schema(acc.GetForecastRequest)
    Response = md.class_schema(acc.GetForecastResponse)

    @requires_login
    def handle_request(self, request, user):
        """
        :param acc.GetForecastRequest request:
        :param originexample.auth.User user:
        :rtype: acc.GetForecastResponse
        """
        return account_service.get_forecast(user.access_token, request)


class GetForecastList(Controller):
    """
    TODO
    """
    Request = md.class_schema(acc.GetForecastListRequest)
    Response = md.class_schema(acc.GetForecastListResponse)

    @requires_login
    def handle_request(self, request, user):
        """
        :param acc.GetForecastListRequest request:
        :param originexample.auth.User user:
        :rtype: acc.GetForecastListResponse
        """
        return account_service.get_forecast_list(user.access_token, request)


class GetForecastSeries(Controller):
    """
    TODO
    """
    Response = md.class_schema(acc.GetForecastSeriesResponse)

    @requires_login
    def handle_request(self, user):
        """
        :param originexample.auth.User user:
        :rtype: acc.GetForecastSeriesResponse
        """
        return account_service.get_forecast_series(user.access_token)


class SubmitForecast(Controller):
    """
    TODO
    """
    Request = md.class_schema(acc.SubmitForecastRequest)
    Response = md.class_schema(acc.SubmitForecastResponse)

    @requires_login
    def handle_request(self, request, user):
        """
        :param acc.SubmitForecastRequest request:
        :param originexample.auth.User user:
        :rtype: acc.SubmitForecastResponse
        """
        return account_service.submit_forecast(user.access_token, request)
