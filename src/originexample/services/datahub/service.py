import requests
import marshmallow_dataclass as md

from originexample import logger
from originexample.http import Unauthorized
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
    GetDisclosureRequest,
    GetDisclosureResponse,
    GetDisclosureListResponse,
    CreateDisclosureRequest,
    CreateDisclosureResponse,
    DeleteDisclosureRequest,
    DeleteDisclosureResponse,
)


class DataHubService(object):
    """
    An interface to the Project Origin DataHub Service API.
    """
    def invoke(self, path, response_schema, request=None, request_schema=None, token=None):
        """
        :param str path:
        :param obj request:
        :param Schema request_schema:
        :param Schema response_schema:
        :param str token:
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
                headers={TOKEN_HEADER: f'Bearer {token}'} if token else None,
                verify=verify_ssl,
            )
        except:
            logger.exception(f'Invoking DataHubService resulted in an exception', extra={
                'url': url,
                'verify_ssl': verify_ssl,
                'request_body': str(body),
            })
            raise

        if response.status_code == 401:
            raise Unauthorized
        elif response.status_code != 200:
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
        with logger.tracer.span('DataHubService.GetOnboardingUrl'):
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
        with logger.tracer.span('DataHubService.GetMeteringPoints'):
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
        with logger.tracer.span('DataHubService.GetProductionMeaurement'):
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
        with logger.tracer.span('DataHubService.GetConsumptionMeasurement'):
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
        with logger.tracer.span('DataHubService.GetMeasurementsBeginRange'):
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
        with logger.tracer.span('DataHubService.GetMeasurementsSummary'):
            return self.invoke(
                token=token,
                path='/measurements/summary',
                request=request,
                request_schema=md.class_schema(GetMeasurementSummaryRequest),
                response_schema=md.class_schema(GetMeasurementSummaryResponse),
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
        with logger.tracer.span('DataHubService.GetDisclosureUrl'):
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
        with logger.tracer.span('DataHubService.CreateDisclosure'):
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
        with logger.tracer.span('DataHubService.DeleteDisclosure'):
            return self.invoke(
                token=token,
                path='/disclosure/delete',
                request=request,
                request_schema=md.class_schema(DeleteDisclosureRequest),
                response_schema=md.class_schema(DeleteDisclosureResponse),
            )

    def webhook_on_meteringpoints_available_subscribe(self, token):
        """
        :param str token:
        :rtype: WebhookSubscribeResponse
        """
        url = f'{PROJECT_URL}/webhook/on-meteringpoints-available'

        with logger.tracer.span('DataHubService.SubscribeOnMeteringPointsAvailableWebhook'):
            return self.invoke(
                token=token,
                path='/webhook/on-meteringpoints-available/subscribe',
                request=WebhookSubscribeRequest(url=url),
                request_schema=md.class_schema(WebhookSubscribeRequest),
                response_schema=md.class_schema(WebhookSubscribeResponse),
            )
