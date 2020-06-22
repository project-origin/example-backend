import marshmallow_dataclass as md

from originexample.db import inject_session
from originexample.http import Controller
from originexample.auth import UserQuery
from originexample.webhooks import validate_hmac
from originexample.services import MeasurementType
from originexample.pipelines import (
    start_handle_ggo_received_pipeline,
    start_handle_measurement_published_pipeline,
    start_import_meteringpoints_pipeline,
)

from .models import (
    OnGgoReceivedWebhookRequest,
    OnMeasurementPublishedWebhookRequest,
    OnMeteringPointsAvailableWebhookRequest,
)


class OnGgoReceivedWebhook(Controller):
    """
    TODO
    """
    Request = md.class_schema(OnGgoReceivedWebhookRequest)

    @validate_hmac
    @inject_session
    def handle_request(self, request, session):
        """
        :param OnGgoReceivedWebhookRequest request:
        :param Session session:
        :rtype: bool
        """
        user = UserQuery(session) \
            .has_sub(request.sub) \
            .one_or_none()

        if user:
            start_handle_ggo_received_pipeline(request.ggo, user)
            return True
        else:
            return False


class OnMeasurementPublishedWebhook(Controller):
    """
    TODO
    """
    Request = md.class_schema(OnMeasurementPublishedWebhookRequest)

    @validate_hmac
    @inject_session
    def handle_request(self, request, session):
        """
        :param OnMeasurementPublishedWebhookRequest request:
        :param Session session:
        :rtype: bool
        """
        if request.measurement.type is MeasurementType.CONSUMPTION:
            user = UserQuery(session) \
                .has_sub(request.sub) \
                .one_or_none()

            if user:
                start_handle_measurement_published_pipeline(
                    request.measurement, user)

        return True


class OnMeteringPointsAvailableWebhook(Controller):
    """
    TODO
    """
    Request = md.class_schema(OnMeteringPointsAvailableWebhookRequest)

    @validate_hmac
    @inject_session
    def handle_request(self, request, session):
        """
        :param OnMeteringPointsAvailableWebhookRequest request:
        :param Session session:
        :rtype: bool
        """
        user = UserQuery(session) \
            .has_sub(request.sub) \
            .one_or_none()

        if user:
            start_import_meteringpoints_pipeline(user.sub)
            return True
        else:
            return False
