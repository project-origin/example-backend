import sendgrid
import marshmallow_dataclass as md
from sendgrid.helpers.mail import Email, Content, Mail, To

from originexample.http import Controller
from originexample.auth import User, requires_login
from originexample.settings import (
    EMAIL_TO_ADDRESS,
    EMAIL_PREFIX,
    SENDGRID_API_KEY,
)

from .models import (
    SubmitSupportEnquiryRequest,
    SubmitSupportEnquiryResponse,
)


SUPPORT_ENQUIRY_EMAIL_TEMPLATE = """Support enquiry sent from ElOverblik.dk:
------------------------------------------------------------------------------
Sender: %(name)s <%(email)s>
Phone: %(phone)s
User ID: %(sub)s
------------------------------------------------------------------------------

%(message)s"""


class SubmitSupportEnquiry(Controller):
    """
    TODO
    """
    Request = md.class_schema(SubmitSupportEnquiryRequest)
    Response = md.class_schema(SubmitSupportEnquiryResponse)

    @requires_login
    def handle_request(self, request, user):
        """
        :param SubmitSupportEnquiryRequest request:
        :param User user:
        :rtype: bool
        """
        body = SUPPORT_ENQUIRY_EMAIL_TEMPLATE % {
            'sub': user.sub,
            'email': request.email,
            'name': user.name,
            'phone': request.phone,
            'message': request.message,
        }

        from_email = Email(request.email, user.name)
        to_email = To(EMAIL_TO_ADDRESS)
        subject = f'{EMAIL_PREFIX}{request.subject}'
        content = Content('text/plain', body)
        mail = Mail(from_email, to_email, subject, content)

        client = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
        response = client.client.mail.send.post(request_body=mail.get())

        return response.status_code in (200, 201, 202)
