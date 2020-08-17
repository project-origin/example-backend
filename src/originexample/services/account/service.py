import json
import marshmallow
import requests
import marshmallow_dataclass as md

from originexample.settings import (
    PROJECT_URL,
    ACCOUNT_SERVICE_URL,
    TOKEN_HEADER,
    DEBUG,
    WEBHOOK_SECRET,
)

from .models import (
    FindSuppliersRequest,
    FindSuppliersResponse,
    GetGgoListRequest,
    GetGgoListResponse,
    GetGgoSummaryRequest,
    GetGgoSummaryResponse,
    GetTotalAmountRequest,
    GetTotalAmountResponse,
    ComposeGgoRequest,
    ComposeGgoResponse,
    GetTransferSummaryRequest,
    GetTransferSummaryResponse,
    GetTransferredAmountRequest,
    GetTransferredAmountResponse,
    GetForecastRequest,
    GetForecastResponse,
    GetForecastListRequest,
    GetForecastListResponse,
    GetForecastSeriesResponse,
    SubmitForecastRequest,
    SubmitForecastResponse,
    WebhookSubscribeRequest,
    WebhookSubscribeResponse,
)


class AccountServiceConnectionError(Exception):
    """
    Raised when invoking DataHubService results in a connection error
    """
    pass


class AccountServiceError(Exception):
    """
    Raised when invoking DataHubService results in a status code != 200
    """
    def __init__(self, message, status_code, response_body):
        super(AccountServiceError, self).__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class AccountService(object):
    """
    An interface to the Project Origin Account Service API.
    """
    def invoke(self, token, path, response_schema, request=None, request_schema=None):
        """
        :param str token:
        :param str path:
        :param obj request:
        :param Schema request_schema:
        :param Schema response_schema:
        :rtype obj:
        """
        url = '%s%s' % (ACCOUNT_SERVICE_URL, path)
        headers = {TOKEN_HEADER: f'Bearer {token}'}
        body = None

        if request and request_schema:
            body = request_schema().dump(request)

        try:
            response = requests.post(
                url=url,
                json=body,
                headers=headers,
                verify=not DEBUG,
            )
        except:
            raise AccountServiceConnectionError(
                'Failed to POST request to AccountService')

        if response.status_code != 200:
            raise AccountServiceError(
                (
                    f'Invoking AccountService resulted in status code {response.status_code}: '
                    f'{url}\n\n{response.content}'
                ),
                status_code=response.status_code,
                response_body=str(response.content),
            )

        try:
            response_json = response.json()
            response_model = response_schema().load(response_json)
        except json.decoder.JSONDecodeError:
            raise AccountServiceError(
                f'Failed to parse response JSON: {url}\n\n{response.content}',
                status_code=response.status_code,
                response_body=str(response.content),
            )
        except marshmallow.ValidationError:
            raise AccountServiceError(
                f'Failed to validate response JSON: {url}\n\n{response.content}',
                status_code=response.status_code,
                response_body=str(response.content),
            )

        return response_model

    # -- Users and accounts --------------------------------------------------

    def find_suppliers(self, token, request):
        """
        :param str token:
        :param FindSuppliersRequest request:
        :rtype: FindSuppliersResponse
        """
        return self.invoke(
            token=token,
            path='/accounts/find-suppliers',
            request=request,
            request_schema=md.class_schema(FindSuppliersRequest),
            response_schema=md.class_schema(FindSuppliersResponse),
        )

    # -- GGOs ----------------------------------------------------------------

    def get_ggo_list(self, token, request):
        """
        :param str token:
        :param GetGgoListRequest request:
        :rtype: GetGgoListResponse
        """
        return self.invoke(
            token=token,
            path='/ggo',
            request=request,
            request_schema=md.class_schema(GetGgoListRequest),
            response_schema=md.class_schema(GetGgoListResponse),
        )

    def get_ggo_summary(self, token, request):
        """
        :param str token:
        :param GetGgoSummaryRequest request:
        :rtype: GetGgoSummaryResponse
        """
        return self.invoke(
            token=token,
            path='/ggo/summary',
            request=request,
            request_schema=md.class_schema(GetGgoSummaryRequest),
            response_schema=md.class_schema(GetGgoSummaryResponse),
        )

    def compose(self, token, request):
        """
        :param str token:
        :param ComposeGgoRequest request:
        :rtype: ComposeGgoResponse
        """
        return self.invoke(
            token=token,
            path='/compose',
            request=request,
            request_schema=md.class_schema(ComposeGgoRequest),
            response_schema=md.class_schema(ComposeGgoResponse),
        )

    def get_transfer_summary(self, token, request):
        """
        :param str token:
        :param GetTransferSummaryRequest request:
        :rtype: GetTransferSummaryResponse
        """
        return self.invoke(
            token=token,
            path='/transfer/summary',
            request=request,
            request_schema=md.class_schema(GetTransferSummaryRequest),
            response_schema=md.class_schema(GetTransferSummaryResponse),
        )

    def get_transferred_amount(self, token, request):
        """
        :param str token:
        :param GetTransferredAmountRequest request:
        :rtype: GetTransferredAmountResponse
        """
        return self.invoke(
            token=token,
            path='/transfer/get-transferred-amount',
            request=request,
            request_schema=md.class_schema(GetTransferredAmountRequest),
            response_schema=md.class_schema(GetTransferredAmountResponse),
        )

    def get_total_amount(self, token, request):
        """
        :param str token:
        :param GetTotalAmountRequest request:
        :rtype: GetTotalAmountResponse
        """
        return self.invoke(
            token=token,
            path='/ggo/get-total-amount',
            request=request,
            request_schema=md.class_schema(GetTotalAmountRequest),
            response_schema=md.class_schema(GetTotalAmountResponse),
        )

    # -- Forecasts -----------------------------------------------------------

    def get_forecast(self, token, request):
        """
        :param str token:
        :param GetForecastRequest request:
        :rtype: GetForecastResponse
        """
        return self.invoke(
            token=token,
            path='/forecast',
            request=request,
            request_schema=md.class_schema(GetForecastRequest),
            response_schema=md.class_schema(GetForecastResponse),
        )

    def get_forecast_list(self, token, request):
        """
        :param str token:
        :param GetForecastListRequest request:
        :rtype: GetForecastListResponse
        """
        return self.invoke(
            token=token,
            path='/forecast/list',
            request=request,
            request_schema=md.class_schema(GetForecastListRequest),
            response_schema=md.class_schema(GetForecastListResponse),
        )

    def get_forecast_series(self, token):
        """
        :param str token:
        :rtype: GetForecastSeriesResponse
        """
        return self.invoke(
            token=token,
            path='/forecast/series',
            response_schema=md.class_schema(GetForecastSeriesResponse),
        )

    def submit_forecast(self, token, request):
        """
        :param str token:
        :param SubmitForecastRequest request:
        :rtype: SubmitForecastResponse
        """
        return self.invoke(
            token=token,
            path='/forecast/submit',
            request=request,
            request_schema=md.class_schema(SubmitForecastRequest),
            response_schema=md.class_schema(SubmitForecastResponse),
        )

    # -- Webhooks ------------------------------------------------------------

    def webhook_on_ggo_received_subscribe(self, token):
        """
        :param str token:
        :rtype: WebhookSubscribeResponse
        """
        callback_url = f'{PROJECT_URL}/webhook/on-ggo-received'

        return self.invoke(
            token=token,
            path='/webhook/on-ggo-received/subscribe',
            request=WebhookSubscribeRequest(url=callback_url, secret=WEBHOOK_SECRET),
            request_schema=md.class_schema(WebhookSubscribeRequest),
            response_schema=md.class_schema(WebhookSubscribeResponse),
        )
