import requests
import marshmallow_dataclass as md

from originexample import logger
from originexample.settings import (
    PROJECT_URL,
    DATAHUB_SERVICE_URL,
    TOKEN_HEADER,
    DEBUG,
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
)


class DataHubService(object):
    """
    An interface to the Project Origin DataHub Service API.
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
        url = '%s%s' % (DATAHUB_SERVICE_URL, path)
        verify_ssl = not DEBUG

        if request and request_schema:
            body = request_schema().dump(request)
        else:
            body = None

        try:
            response = requests.post(
                url=url,
                json=body,
                headers={TOKEN_HEADER: f'Bearer {token}'},
                verify=verify_ssl,
            )
        except:
            logger.exception(f'Invoking DataHubService resulted in an exception', extra={
                'url': url,
                'verify_ssl': verify_ssl,
                'request_body': str(body),
            })
            raise

        if response.status_code != 200:
            logger.error(f'Invoking DataHubService resulted in a status != 200', extra={
                'url': url,
                'verify_ssl': verify_ssl,
                'request_body': str(body),
                'response_code': response.status_code,
                'response_content': str(response.content),
            })
            raise Exception('Request to DataHub failed: %s' % str(response.content))

        response_json = response.json()

        return response_schema().load(response_json)

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

    def webhook_on_meteringpoints_available_subscribe(self, token):
        """
        :param str token:
        :rtype: WebhookSubscribeResponse
        """
        url = f'{PROJECT_URL}/webhook/on-meteringpoints-available'

        return self.invoke(
            token=token,
            path='/webhook/on-meteringpoints-available/subscribe',
            request=WebhookSubscribeRequest(url=url),
            request_schema=md.class_schema(WebhookSubscribeRequest),
            response_schema=md.class_schema(WebhookSubscribeResponse),
        )
