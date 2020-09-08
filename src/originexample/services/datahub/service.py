import json

import marshmallow
import requests
import marshmallow_dataclass as md

from originexample import logger
from originexample.settings import (
    PROJECT_URL,
    DATAHUB_SERVICE_URL,
    TOKEN_HEADER,
    DEBUG,
    WEBHOOK_SECRET,
)

from .models import (
    GetMeasurementRequest,
    GetMeasurementResponse,
    GetBeginRangeRequest,
    GetBeginRangeResponse,
    GetMeasurementSummaryRequest,
    GetMeasurementSummaryResponse,
    GetMeteringPointsResponse,
    GetOnboadingUrlResponse,
    GetOnboadingUrlRequest,
    WebhookSubscribeRequest,
    WebhookSubscribeResponse,
    GetDisclosureRequest,
    GetDisclosureResponse,
    GetDisclosureListResponse,
    CreateDisclosureRequest,
    CreateDisclosureResponse,
    DeleteDisclosureRequest,
    DeleteDisclosureResponse,
    GetTechnologiesResponse,
    GetMeasurementListRequest,
    GetMeasurementListResponse,
)


class DataHubServiceConnectionError(Exception):
    """
    Raised when invoking DataHubService results in a connection error
    """
    pass


class DataHubServiceError(Exception):
    """
    Raised when invoking DataHubService results in a status code != 200
    """
    def __init__(self, message, status_code, response_body):
        super(DataHubServiceError, self).__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class DataHubService(object):
    """
    An interface to the Project Origin DataHub Service API.
    """
    def invoke(self, path, response_schema, token=None, request=None, request_schema=None):
        """
        :param str path:
        :param obj request:
        :param str token:
        :param Schema request_schema:
        :param Schema response_schema:
        :rtype obj:
        """
        url = '%s%s' % (DATAHUB_SERVICE_URL, path)
        headers = {}
        body = None

        if token:
            headers = {TOKEN_HEADER: f'Bearer {token}'}
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
            raise DataHubServiceConnectionError(
                'Failed to POST request to DataHubService')

        if response.status_code != 200:
            raise DataHubServiceError(
                (
                    f'Invoking DataHubService resulted in status code {response.status_code}: '
                    f'{url}\n\n{response.content}'
                ),
                status_code=response.status_code,
                response_body=str(response.content),
            )

        try:
            response_json = response.json()
            response_model = response_schema().load(response_json)
        except json.decoder.JSONDecodeError:
            raise DataHubServiceError(
                f'Failed to parse response JSON: {url}\n\n{response.content}',
                status_code=response.status_code,
                response_body=str(response.content),
            )
        except marshmallow.ValidationError as e:
            raise DataHubServiceError(
                f'Failed to validate response JSON: {url}\n\n{response.content}\n\n{str(e)}',
                status_code=response.status_code,
                response_body=str(response.content),
            )

        return response_model

    def get_onboarding_url(self, token, return_url):
        """
        :param str token:
        :param str return_url:
        :rtype: GetOnboadingUrlResponse
        """
        return self.invoke(
            token=token,
            path='/onboarding/get-url',
            request=GetOnboadingUrlRequest(return_url=return_url),
            request_schema=md.class_schema(GetOnboadingUrlRequest),
            response_schema=md.class_schema(GetOnboadingUrlResponse),
        )

    def get_meteringpoints(self, token):
        """
        :param str token:
        :rtype: GetMeteringPointsResponse
        """
        return self.invoke(
            token=token,
            path='/meteringpoints',
            response_schema=md.class_schema(GetMeteringPointsResponse),
        )

    def get_measurement_list(self, token, request):
        """
        :param str token:
        :param GetMeasurementListRequest request:
        :rtype: GetMeasurementListResponse
        """
        return self.invoke(
            token=token,
            path='/measurements',
            request=request,
            request_schema=md.class_schema(GetMeasurementListRequest),
            response_schema=md.class_schema(GetMeasurementListResponse),
        )

    def get_production(self, token, request):
        """
        :param str token:
        :param GetMeasurementRequest request:
        :rtype: GetMeasurementResponse
        """
        return self.invoke(
            token=token,
            path='/measurements/produced',
            request=request,
            request_schema=md.class_schema(GetMeasurementRequest),
            response_schema=md.class_schema(GetMeasurementResponse),
        )

    def get_consumption(self, token, request):
        """
        :param str token:
        :param GetMeasurementRequest request:
        :rtype: GetMeasurementResponse
        """
        return self.invoke(
            token=token,
            path='/measurements/consumed',
            request=request,
            request_schema=md.class_schema(GetMeasurementRequest),
            response_schema=md.class_schema(GetMeasurementResponse),
        )

    def get_measurement_begin_range(self, token, request):
        """
        :param str token:
        :param GetBeginRangeRequest request:
        :rtype: GetBeginRangeResponse
        """
        return self.invoke(
            token=token,
            path='/measurements/begin-range',
            request=request,
            request_schema=md.class_schema(GetBeginRangeRequest),
            response_schema=md.class_schema(GetBeginRangeResponse),
        )

    def get_measurement_summary(self, token, request):
        """
        :param str token:
        :param GetMeasurementSummaryRequest request:
        :rtype: GetMeasurementSummaryResponse
        """
        return self.invoke(
            token=token,
            path='/measurements/summary',
            request=request,
            request_schema=md.class_schema(GetMeasurementSummaryRequest),
            response_schema=md.class_schema(GetMeasurementSummaryResponse),
        )

    def get_technologies(self):
        """
        :rtype: GetTechnologiesResponse
        """
        return self.invoke(
            path='/technologies',
            response_schema=md.class_schema(GetTechnologiesResponse),
        )

    def get_disclosure(self, request):
        """
        :param GetDisclosureRequest request:
        :rtype: GetDisclosureResponse
        """
        with logger.tracer.span('DataHubService.GetDisclosure'):
            return self.invoke(
                path='/disclosure',
                request=request,
                request_schema=md.class_schema(GetDisclosureRequest),
                response_schema=md.class_schema(GetDisclosureResponse),
            )

    def get_disclosure_list(self, token):
        """
        :param str token:
        :rtype: GetDisclosureListResponse
        """
        return self.invoke(
            token=token,
            path='/disclosure/list',
            response_schema=md.class_schema(GetDisclosureListResponse),
        )

    def create_disclosure(self, token, request):
        """
        :param str token:
        :param CreateDisclosureRequest request:
        :rtype: CreateDisclosureResponse
        """
        return self.invoke(
            token=token,
            path='/disclosure/create',
            request=request,
            request_schema=md.class_schema(CreateDisclosureRequest),
            response_schema=md.class_schema(CreateDisclosureResponse),
        )

    def delete_disclosure(self, token, request):
        """
        :param str token:
        :param DeleteDisclosureRequest request:
        :rtype: DeleteDisclosureResponse
        """
        return self.invoke(
            token=token,
            path='/disclosure/delete',
            request=request,
            request_schema=md.class_schema(DeleteDisclosureRequest),
            response_schema=md.class_schema(DeleteDisclosureResponse),
        )

    def webhook_on_measurement_published_subscribe(self, token):
        """
        :param str token:
        :rtype: WebhookSubscribeResponse
        """
        callback_url = f'{PROJECT_URL}/webhook/on-measurement-published'

        return self.invoke(
            token=token,
            path='/webhook/on-measurement-published/subscribe',
            request=WebhookSubscribeRequest(url=callback_url, secret=WEBHOOK_SECRET),
            request_schema=md.class_schema(WebhookSubscribeRequest),
            response_schema=md.class_schema(WebhookSubscribeResponse),
        )

    def webhook_on_meteringpoint_available_subscribe(self, token):
        """
        :param str token:
        :rtype: WebhookSubscribeResponse
        """
        callback_url = f'{PROJECT_URL}/webhook/on-meteringpoint-available'

        return self.invoke(
            token=token,
            path='/webhook/on-meteringpoint-available/subscribe',
            request=WebhookSubscribeRequest(url=callback_url, secret=WEBHOOK_SECRET),
            request_schema=md.class_schema(WebhookSubscribeRequest),
            response_schema=md.class_schema(WebhookSubscribeResponse),
        )
