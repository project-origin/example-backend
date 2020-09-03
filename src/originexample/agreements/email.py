import sendgrid
from sendgrid.helpers.mail import (
    Email, Content, Mail, To, Attachment, FileContent,
    FileName, FileType, Disposition,
)

from originexample.settings import (
    EMAIL_FROM_ADDRESS,
    EMAIL_FROM_NAME,
    SENDGRID_API_KEY,
    PROJECT_URL,
)


INVITATION_RECEIVED_SUBJECT = 'You have received a transfer proposal'
INVITATION_RECEIVED_TEMPLATE = """
"""


INVITATION_ACCEPTED_TEMPLATE = """
"""


INVITATION_DECLINED_TEMPLATE = """
"""


def _send_email(user, subject, body):
    """
    :param originexample.auth.User user:
    :param str body:
    :rtype: bool
    """
    from_email = Email(EMAIL_FROM_ADDRESS, EMAIL_FROM_NAME)
    to_email = To(user.email, user.name)
    content = Content('text/plain', body)
    mail = Mail(from_email, to_email, subject, content)

    client = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    response = client.client.mail.send.post(request_body=mail.get())

    return response.status_code in (200, 201, 202)


def send_invitation_received_email(user, agreement):
    """
    :param originexample.auth.User user:
    :param originexample.agreements.TradeAgreement agreement:
    :rtype: bool
    """
    body = INVITATION_RECEIVED_TEMPLATE % {
        'sub': user.sub,
        'name': user.name,
        'company': user.company,
        'link': PROJECT_URL,
        'message': request.message,
    }

    return _send_email(user, INVITATION_RECEIVED_SUBJECT, body)


def send_invitation_accepted_email():
    pass


def send_invitation_declined_email():
    pass
