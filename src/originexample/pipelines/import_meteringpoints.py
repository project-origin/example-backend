"""
TODO write this
"""
from originexample import logger
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


def start_import_meteringpoints(user):
    """
    :param User user:
    """
    import_meteringpoints_and_insert_to_db \
        .s(subject=user.sub) \
        .apply_async()


@celery_app.task(name='import_meteringpoints.import_meteringpoints_and_insert_to_db')
@logger.wrap_task(
    title='Importing meteringpoints from DataHub',
    pipeline='import_meteringpoints',
    task='import_meteringpoints_and_insert_to_db',
)
@atomic
def import_meteringpoints_and_insert_to_db(subject, session):
    """
    :param str subject:
    :param Session session:
    """
    user = UserQuery(session) \
        .has_sub(subject) \
        .one()

    response = service.get_meteringpoints(user.access_token)

    for meteringpoint in response.meteringpoints:
        count = FacilityQuery(session) \
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

            logger.info(f'Imported meteringpoint with GSRN: {meteringpoint.gsrn}', extra={
                'gsrn': meteringpoint.gsrn,
                'subject': user.sub,
                'pipeline': 'import_meteringpoints',
                'task': 'import_meteringpoints_and_insert_to_db',
            })
        else:
            logger.info(f'Skipping meteringpoint with GSRN: {meteringpoint.gsrn} (already exists in DB)', extra={
                'gsrn': meteringpoint.gsrn,
                'subject': user.sub,
                'pipeline': 'import_meteringpoints',
                'task': 'import_meteringpoints_and_insert_to_db',
            })
