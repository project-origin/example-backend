import marshmallow_dataclass as md

from originexample import logger
from originexample.db import inject_session, atomic
from originexample.http import Controller
from originexample.auth import UserQuery
from originexample.webhooks import validate_hmac
from originexample.services import MeasurementType
from originexample.facilities import FacilityQuery, FacilityType, Facility
from originexample.services.datahub import (
    MeteringPointType as DataHubMeteringPointType,
)
from originexample.pipelines import (
    start_handle_ggo_received_pipeline,
    start_handle_measurement_published_pipeline,
    start_import_meteringpoints_pipeline,
)

from .models import (
    OnGgoReceivedWebhookRequest,
    OnMeasurementPublishedWebhookRequest,
    OnMeteringPointAvailableWebhookRequest,
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


class OnMeteringPointAvailableWebhook(Controller):
    """
    TODO
    """
    Request = md.class_schema(OnMeteringPointAvailableWebhookRequest)

    @validate_hmac
    @inject_session
    def handle_request(self, request, session):
        """
        :param OnMeteringPointAvailableWebhookRequest request:
        :param sqlalchemy.orm.Session session:
        :rtype: bool
        """
        user = UserQuery(session) \
            .has_sub(request.sub) \
            .one_or_none()

        # User exists?
        if user is None:
            logger.error(f'Can not import MeteringPoint (user not found in DB)', extra={
                'subject': request.sub,
                'gsrn': request.meteringpoint.gsrn,
            })
            return False

        # MeteringPoint already present in database?
        if self.facility_exists(request.meteringpoint.gsrn, session):
            logger.info(f'MeteringPoint {request.meteringpoint.gsrn} already exists in DB, skipping...', extra={
                'subject': request.sub,
                'gsrn': request.meteringpoint.gsrn,
            })
            return True

        # Insert new MeteringPoint in to DB
        facility = self.create_facility(user, request.meteringpoint)

        logger.info(f'Imported MeteringPoint with GSRN: {facility.gsrn}', extra={
            'subject': user.sub,
            'gsrn': facility.gsrn,
            'type': facility.facility_type,
            'facility_id': facility.id,
        })

        return True

    def facility_exists(self, gsrn, session):
        """
        :param str gsrn:
        :param sqlalchemy.orm.Session session:
        :rtype: bool
        """
        count = FacilityQuery(session) \
            .has_gsrn(gsrn) \
            .count()

        return count > 0

    @atomic
    def create_facility(self, user, imported_meteringpoint, session):
        """
        :param originexample.auth.User user:
        :param originexample.services.datahub.MeteringPoint imported_meteringpoint:
        :param sqlalchemy.orm.Session session:
        :rtype: Facility
        """
        facility = Facility(
            user=user,
            gsrn=imported_meteringpoint.gsrn,
            sector=imported_meteringpoint.sector,
            facility_type=self.get_type(imported_meteringpoint),
            technology_code=imported_meteringpoint.technology_code,
            fuel_code=imported_meteringpoint.fuel_code,
            street_code=imported_meteringpoint.street_code,
            street_name=imported_meteringpoint.street_name,
            building_number=imported_meteringpoint.building_number,
            city_name=imported_meteringpoint.city_name,
            postcode=imported_meteringpoint.postcode,
            municipality_code=imported_meteringpoint.municipality_code,
        )

        session.add(facility)
        session.flush()

        return facility

    def get_type(self, imported_meteringpoint):
        """
        :param originexample.services.datahub.MeteringPoint imported_meteringpoint:
        :rtype: FacilityType
        """
        if imported_meteringpoint.type is DataHubMeteringPointType.PRODUCTION:
            return FacilityType.PRODUCTION
        elif imported_meteringpoint.type is DataHubMeteringPointType.CONSUMPTION:
            return FacilityType.CONSUMPTION
        else:
            raise RuntimeError('Should NOT have happened!')


class OnMeteringPointsAvailableWebhook(Controller):
    """
    TODO remove this
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
