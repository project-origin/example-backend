import marshmallow_dataclass as md

from originexample import logger
from originexample.db import inject_session
from originexample.http import Controller
from originexample.auth import UserQuery
from originexample.pipelines import start_handle_ggo_received_pipeline

from .models import OnGgoReceivedWebhookRequest


class OnGgoReceivedWebhook(Controller):
    """
    TODO
    """
    Request = md.class_schema(OnGgoReceivedWebhookRequest)

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
