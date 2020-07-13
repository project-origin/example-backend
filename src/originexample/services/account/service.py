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
    GetGgoListRequest,
    GetGgoListResponse,
    GetGgoSummaryRequest,
    GetGgoSummaryResponse,
    ComposeGgoRequest,
    ComposeGgoResponse,
    GetTransferSummaryRequest,
    GetTransferSummaryResponse,
    GetTransferredAmountRequest,
    GetTransferredAmountResponse,
    GetTotalAmountRequest,
    GetTotalAmountResponse,
    GetEcoDeclarationRequest,
    GetEcoDeclarationResponse,
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
    def invoke(self, token, path, request, request_schema, response_schema):
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
        except marshmallow.ValidationError as e:
            raise AccountServiceError(
                f'Failed to validate response JSON: {url}\n\n{response.content}\n\n{str(e)}',
                status_code=response.status_code,
                response_body=str(response.content),
            )

        return response_model

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

    def get_eco_declaration(self, token, request):
        """
        :param str token:
        :param GetEcoDeclarationRequest request:
        :rtype: GetEcoDeclarationResponse
        """
        return self.invoke(
            token=token,
            path='/eco-declaration',
            request=request,
            request_schema=md.class_schema(GetEcoDeclarationRequest),
            response_schema=md.class_schema(GetEcoDeclarationResponse),
        )

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
