import marshmallow_dataclass as md

from originexample.db import atomic, inject_session
from originexample.http import Controller, BadRequest
from originexample.auth import User, requires_login
from originexample.facilities import FacilityQuery, FacilityFilters
from originexample.services import datahub as dh
from originexample.services.account import summarize_technologies
from originexample.common import DataSet

from .models import (
    DisclosureDataSeries,
    GetDisclosurePreviewRequest,
    GetDisclosurePreviewResponse,
    CreateDisclosureRequest,
    CreateDisclosureResponse,
    GetDisclosureRequest,
    GetDisclosureResponse,
    GetDisclosureListResponse, DeleteDisclosureRequest)


datahub = dh.DataHubService()


class GetDisclosure(Controller):
    """
    TODO
    """
    Request = md.class_schema(GetDisclosureRequest)
    Response = md.class_schema(GetDisclosureResponse)

    @inject_session
    def handle_request(self, request, session):
        """
        :param GetDisclosureRequest request:
        :param Session session:
        :rtype: GetDisclosureResponse
        """
        datahub_request = dh.GetDisclosureRequest(id=request.id)
        datahub_response = datahub.get_disclosure(datahub_request)

        response = GetDisclosureResponse(
            success=datahub_response.success,
            labels=datahub_response.labels,
            data=[],
        )

        for datahub_dataseries in datahub_response.data:
            dataseries = DisclosureDataSeries(
                gsrn=datahub_dataseries.gsrn,
                address=datahub_dataseries.address,
                measurements=datahub_dataseries.measurements,
                ggos=[],
            )

            ggos_summarized = summarize_technologies(
                datahub_dataseries.ggos, ['technologyCode', 'fuelCode'])

            for technology, summary_group in ggos_summarized:
                dataseries.ggos.append(DataSet(
                    label=technology,
                    values=summary_group.values,
                ))

            response.data.append(dataseries)

        return response


class GetDisclosurePreview(Controller):
    """
    TODO
    """
    Request = md.class_schema(GetDisclosurePreviewRequest)
    Response = md.class_schema(GetDisclosurePreviewResponse)

    @requires_login
    @atomic
    def handle_request(self, request, user, session):
        """
        :param GetDisclosurePreviewRequest request:
        :param User user:
        :param Session session:
        :rtype: GetDisclosurePreviewResponse
        """
        return GetDisclosurePreviewResponse(
            success=True,
            date_range=request.date_range,
            facilities=self.get_facilities(user, request.filters),
        )

    @inject_session
    def get_facilities(self, user, filters, session):
        """
        :param User user:
        :param FacilityFilters filters:
        :param Session session:
        :rtype: list[Facility]
        """
        query = FacilityQuery(session) \
            .belongs_to(user) \
            .is_consumer()

        if filters is not None:
            query = query.apply_filters(filters)

        return query.all()


class GetDisclosureList(Controller):
    """
    TODO
    """
    Response = md.class_schema(GetDisclosureListResponse)

    @requires_login
    def handle_request(self, user):
        """
        :param User user:
        :rtype: GetDisclosureListResponse
        """
        datahub_response = datahub.get_disclosure_list(user.access_token)

        return GetDisclosureListResponse(
            success=True,
            disclosures=datahub_response.disclosures,
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
            .is_consumer() \
            .has_any_gsrn(request.gsrn) \
            .all()

        if not facilities:
            raise BadRequest('No [consuming] facilities selected')

        request = dh.CreateDisclosureRequest(
            name=request.name,
            description=request.description,
            gsrn=request.gsrn,
            begin=request.date_range.begin,
            end=request.date_range.end,
            publicize_meteringpoints=request.publicize_meteringpoints,
            publicize_gsrn=request.publicize_gsrn,
            publicize_physical_address=request.publicize_physical_address,
        )

        response = datahub.create_disclosure(user.access_token, request)

        return CreateDisclosureResponse(
            success=True,
            id=response.id,
        )


class DeleteDisclosure(Controller):
    """
    TODO
    """
    Request = md.class_schema(DeleteDisclosureRequest)

    @requires_login
    @inject_session
    def handle_request(self, request, user, session):
        """
        :param DeleteDisclosureRequest request:
        :param User user:
        :param Session session:
        :rtype: bool
        """
        datahub_request = dh.DeleteDisclosureRequest(id=request.id)
        datahub_response = datahub.delete_disclosure(
            user.access_token, datahub_request)

        return datahub_response.success
