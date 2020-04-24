"""
TODO write this
"""
import logging

from originexample.db import atomic
from originexample.tasks import celery_app
from originexample.auth import UserQuery
from originexample.services.datahub import DataHubService, MeteringPointType
from originexample.facilities import (
    Facility,
    FacilityType,
    FacilityQuery,
    get_technology,
)


service = DataHubService()


def start_import_meteringpoints(user_id):
    """
    :param int user_id:
    """
    fetch_meteringpoints_and_insert_to_db.s(user_id).apply_async()


@celery_app.task(name='import_meteringpoints.fetch_meteringpoints_and_insert_to_db')
@atomic
def fetch_meteringpoints_and_insert_to_db(user_id, session):
    """
    :param int user_id:
    :param Session session:
    """
    logging.info('--- fetch_meteringpoints_and_insert_to_db, user_id=%d' % user_id)

    user = UserQuery(session) \
        .has_id(user_id) \
        .one()

    response = service.get_meteringpoints(user.access_token)

    for meteringpoint in response.meteringpoints:
        count = FacilityQuery(session) \
            .belongs_to(user) \
            .has_gsrn(meteringpoint.gsrn) \
            .count()

        if count == 0:
            if meteringpoint.type is MeteringPointType.PRODUCTION:
                facility_type = FacilityType.PRODUCTION
            elif meteringpoint.type is MeteringPointType.CONSUMPTION:
                facility_type = FacilityType.CONSUMPTION
            else:
                raise RuntimeError('Should NOT have happened!')

            if meteringpoint.technology_code and meteringpoint.fuel_code:
                technology = get_technology(
                    meteringpoint.technology_code,
                    meteringpoint.fuel_code)
            else:
                technology = None

            session.add(Facility(
                user=user,
                gsrn=meteringpoint.gsrn,
                sector=meteringpoint.sector,
                facility_type=facility_type,
                technology=technology,
                technology_code=meteringpoint.technology_code,
                fuel_code=meteringpoint.fuel_code,
                street_code=meteringpoint.street_code,
                street_name=meteringpoint.street_name,
                building_number=meteringpoint.building_number,
                city_name=meteringpoint.city_name,
                postcode=meteringpoint.postcode,
                municipality_code=meteringpoint.municipality_code,
            ))
