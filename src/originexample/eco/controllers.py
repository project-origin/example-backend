import marshmallow_dataclass as md

from originexample.http import Controller
from originexample.db import inject_session
from originexample.facilities import FacilityQuery, FacilityFilters
from originexample.auth import User, requires_login
from originexample.services import account as acc
from originexample.common import DateTimeRange

from .models import (
    GetEcoDeclarationRequest,
    GetEcoDeclarationResponse,
)

account_service = acc.AccountService()


def get_resolution(delta):
    """
    :param timedelta delta:
    :rtype: acc.EcoDeclarationResolution
    """
    if delta.days >= (365 * 3):
        return acc.EcoDeclarationResolution.year
    elif delta.days >= 60:
        return acc.EcoDeclarationResolution.month
    elif delta.days >= 3:
        return acc.EcoDeclarationResolution.day
    else:
        return acc.EcoDeclarationResolution.hour


class GetEcoDeclaration(Controller):
    """
    TODO
    """
    Request = md.class_schema(GetEcoDeclarationRequest)
    Response = md.class_schema(GetEcoDeclarationResponse)

    @requires_login
    def handle_request(self, request, user):
        """
        :param GetEcoDeclarationRequest request:
        :param User user:
        :rtype: GetEcoDeclarationResponse
        """
        account_service_request = acc.GetEcoDeclarationRequest(
            gsrn=self.get_gsrn_numbers(user, request.filters),
            resolution=get_resolution(request.date_range.delta),
            begin_range=DateTimeRange.from_date_range(request.date_range),
        )

        return account_service.get_eco_declaration(
            token=user.access_token,
            request=account_service_request,
        )

    @inject_session
    def get_gsrn_numbers(self, user, filters, session):
        """
        :param User user:
        :param FacilityFilters filters:
        :param Session session:
        :rtype: list[str]
        """
        query = FacilityQuery(session) \
            .belongs_to(user) \
            .is_consumer()

        if filters is not None:
            query = query.apply_filters(filters)

        return query.get_distinct_gsrn()
