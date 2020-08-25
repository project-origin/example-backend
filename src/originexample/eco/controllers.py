import csv
import marshmallow_dataclass as md
from flask import send_file, make_response
from io import BytesIO, StringIO

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
        gsrn_numbers = self.get_gsrn_numbers(user, request.filters)

        if gsrn_numbers:
            return account_service.get_eco_declaration(
                token=user.access_token,
                request=self.build_account_service_request(request, user, gsrn_numbers),
            )
        else:
            return GetEcoDeclarationResponse(
                success=True,
                individual=acc.EcoDeclaration.empty(),
                general=acc.EcoDeclaration.empty(),
            )

    def build_account_service_request(self, request, user, gsrn_numbers=None):
        """
        :param GetEcoDeclarationRequest request:
        :param User user:
        :param list[str] gsrn_numbers:
        :rtype: acc.GetEcoDeclarationRequest
        """
        if gsrn_numbers is None:
            gsrn_numbers = self.get_gsrn_numbers(user, request.filters)

        return acc.GetEcoDeclarationRequest(
            gsrn=gsrn_numbers,
            resolution=request.resolution,
            begin_range=DateTimeRange.from_date_range(request.date_range),
            utc_offset=request.utc_offset,
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


class ExportEcoDeclarationPDF(GetEcoDeclaration):
    """
    TODO
    """
    Request = md.class_schema(GetEcoDeclarationRequest)
    Response = None

    @requires_login
    def handle_request(self, request, user):
        """
        :param GetEcoDeclarationRequest request:
        :param User user:
        :rtype: flask.Response
        """
        pdf_file_data = account_service.export_eco_declaration_pdf(
            token=user.access_token,
            request=self.build_account_service_request(request, user),
        )

        f = BytesIO()
        f.write(pdf_file_data)
        f.seek(0)

        return send_file(f, attachment_filename='EnvironmentDeclaration.pdf')


class ExportEcoDeclarationEmissionsCSV(GetEcoDeclaration):
    """
    TODO
    """
    Request = md.class_schema(GetEcoDeclarationRequest)
    Response = None

    @requires_login
    def handle_request(self, request, user):
        """
        :param GetEcoDeclarationRequest request:
        :param User user:
        :rtype: flask.Response
        """
        base_response = account_service.get_eco_declaration(
            token=user.access_token,
            request=self.build_account_service_request(request, user),
        )

        emission_keys = list(base_response.individual.total_emissions.keys())
        fieldnames = ['begin', 'consumption'] + emission_keys

        f = StringIO()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for begin, emissions in base_response.individual.emissions.items():
            emissions.update({
                'begin': begin.isoformat(),
                'consumption': base_response.individual.consumed_amount[begin],
            })
            writer.writerow(emissions)

        response = make_response(f.getvalue())
        response.headers['Content-type'] = 'text/csv'
        response.headers['Content-Disposition'] = \
            'attachment; filename=EnvironmentDeclaration-emissions.csv'

        return response


class ExportEcoDeclarationTechnologiesCSV(GetEcoDeclaration):
    """
    TODO
    """
    Request = md.class_schema(GetEcoDeclarationRequest)
    Response = None

    @requires_login
    def handle_request(self, request, user):
        """
        :param GetEcoDeclarationRequest request:
        :param User user:
        :rtype: flask.Response
        """
        base_response = account_service.get_eco_declaration(
            token=user.access_token,
            request=self.build_account_service_request(request, user),
        )

        technologies_keys = list(base_response.individual.total_technologies.keys())
        fieldnames = ['begin'] + technologies_keys

        f = StringIO()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for begin, technologies in base_response.individual.technologies.items():
            technologies.update({'begin': begin.isoformat()})
            writer.writerow(technologies)

        response = make_response(f.getvalue())
        response.headers['Content-type'] = 'text/csv'
        response.headers['Content-Disposition'] = \
            'attachment; filename=EnvironmentDeclaration-technologies.csv'

        return response
