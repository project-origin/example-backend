import requests
import marshmallow_dataclass as md

from originexample.settings import (
    PROJECT_URL,
    ACCOUNT_SERVICE_URL,
    TOKEN_HEADER,
    DEBUG)

from .models import (
    # GetGgoListRequest,
    # GetGgoListResponse,
    GetGgoSummaryRequest,
    GetGgoSummaryResponse,
    ComposeGgoRequest,
    ComposeGgoResponse,
    GetTransferSummaryRequest,
    GetTransferSummaryResponse,
    GetTransferredAmountRequest,
    GetTransferredAmountResponse,
    GetRetiredAmountRequest,
    GetRetiredAmountResponse,
    WebhookSubscribeRequest,
    WebhookSubscribeResponse,
)


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
        body = request_schema().dump(request)

        response = requests.post(
            url='%s%s' % (ACCOUNT_SERVICE_URL, path),
            json=body,
            headers={TOKEN_HEADER: f'Bearer {token}'},
            verify=not DEBUG,
        )

        if response.status_code != 200:
            raise Exception('%s\n\n%s\n\n%s\n\n%s\n\n' % (str(response), path, body, response.content))

        response_json = response.json()

        return response_schema().load(response_json)

    # def get_ggo_list(self, token, request):
    #     """
    #     :param str token:
    #     :param GetGgoListRequest request:
    #     :rtype: GetGgoListResponse
    #     """
    #     return self.invoke(
    #         token=token,
    #         path='/ggo',
    #         request=request,
    #         request_schema=md.class_schema(GetGgoListRequest),
    #         response_schema=md.class_schema(GetGgoListResponse),
    #     )

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

    # def transfer(self, token, request):
    #     """
    #     :param str token:
    #     :param TransferGgoRequest request:
    #     :rtype: TransferGgoResponse
    #     """
    #     return self.invoke(
    #         token=token,
    #         path='/transfer',
    #         request=request,
    #         request_schema=md.class_schema(TransferGgoRequest),
    #         response_schema=md.class_schema(TransferGgoResponse),
    #     )

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

    def get_retired_amount(self, token, request):
        """
        :param str token:
        :param GetRetiredAmountRequest request:
        :rtype: GetRetiredAmountResponse
        """
        return self.invoke(
            token=token,
            path='/retire/get-retired-amount',
            request=request,
            request_schema=md.class_schema(GetRetiredAmountRequest),
            response_schema=md.class_schema(GetRetiredAmountResponse),
        )

    def webhook_on_ggo_received_subscribe(self, token):
        """
        :param str token:
        :rtype: WebhookSubscribeResponse
        """
        url = f'{PROJECT_URL}/webhook/on-ggo-received'

        return self.invoke(
            token=token,
            path='/webhook/on-ggo-received/subscribe',
            request=WebhookSubscribeRequest(url=url),
            request_schema=md.class_schema(WebhookSubscribeRequest),
            response_schema=md.class_schema(WebhookSubscribeResponse),
        )

    # def retire(self, request):
    #     """
    #     :param RetireGgoRequest request:
    #     :rtype: RetireGgoResponse
    #     """
    #     return self.invoke(
    #         path='/retire',
    #         request=request,
    #         request_schema=md.class_schema(RetireGgoRequest),
    #         response_schema=md.class_schema(RetireGgoResponse),
    #     )
    #
    # def transfer(self):
    #     """
    #     /transfer
    #     """
    #     pass
    #
    # def get_transactions(self):
    #     """
    #     /transfer/transactions
    #     """
    #     pass
    #
    # def get_transaction_summary(self):
    #     """
    #     /transfer/transactions/summary
    #     """
    #     pass
