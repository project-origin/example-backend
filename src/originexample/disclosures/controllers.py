import marshmallow_dataclass as md

from originexample.db import atomic, inject_session
from originexample.tools import slugify
from originexample.http import Controller
from originexample.auth import User, requires_login
from originexample.facilities import FacilityQuery

from .models import (
    Disclosure,
    CreateDisclosureRequest,
    CreateDisclosureResponse,
    GetPublicDisclosureRequest,
    GetPublicDisclosureResponse,
)


class CreateDisclosure(Controller):
    """
    TODO
    """
    Request = md.class_schema(CreateDisclosureRequest)
    Response = md.class_schema(CreateDisclosureResponse)

    @requires_login
    @atomic
    def handle_request(self, request, user, session):
        """
        :param CreateDisclosureRequest request:
        :param User user:
        :param Session session:
        :rtype: CreateDisclosureResponse
        """
        facilities = FacilityQuery(session) \
            .belongs_to(user) \
            .apply_filters(request.filters) \
            .all()

        disclosure = Disclosure(
            slug=slugify(user.name, request.name),
            user=user,
            facilities=facilities,
            date_from=request.date_from,
            date_to=request.date_to,
            name=request.name,
            description=request.description,
        )

        session.add(disclosure)

        return CreateDisclosureResponse(
            success=True,
            url=disclosure.get_public_url(),
        )


class GetPublicDisclosure(Controller):
    """
    TODO
    """
    Request = md.class_schema(GetPublicDisclosureRequest)
    Response = md.class_schema(GetPublicDisclosureResponse)

    @inject_session
    def handle_request(self, request, session):
        """
        :param GetPublicDisclosureRequest request:
        :param Session session:
        :rtype: GetPublicDisclosureResponse
        """
        disclosure = session.query(Disclosure) \
            .filter(Disclosure.slug == request.slug) \
            .one_or_none()

        return CreateDisclosureResponse(
            success=True,
            url=disclosure.get_public_url(),
        )
