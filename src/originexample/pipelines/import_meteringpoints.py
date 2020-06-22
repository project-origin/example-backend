"""
Asynchronous tasks for importing MeteringPoints from DataHubService.

One entrypoint exists:

    start_import_meteringpoints_pipeline()

"""
from sqlalchemy import orm

from originexample import logger
from originexample.db import atomic, inject_session
from originexample.tasks import celery_app
from originexample.auth import UserQuery
from originexample.services.datahub import (
    DataHubService,
    MeteringPointType,
    DataHubServiceConnectionError,
    DataHubServiceError,
)
from originexample.facilities import (
    Facility,
    FacilityType,
    FacilityQuery,
)


# Settings
RETRY_DELAY = 10
MAX_RETRIES = (24 * 60 * 60) / RETRY_DELAY


# Services
datahub_service = DataHubService()


def start_import_meteringpoints_pipeline(subject):
    """
    :param str subject:
    """
    import_meteringpoints_and_insert_to_db \
        .s(subject=subject) \
        .apply_async()


@celery_app.task(
    bind=True,
    name='import_meteringpoints.import_meteringpoints_and_insert_to_db',
    default_retry_delay=RETRY_DELAY,
    max_retries=MAX_RETRIES,
)
@logger.wrap_task(
    title='Importing meteringpoints from DataHub',
    pipeline='import_meteringpoints',
    task='import_meteringpoints_and_insert_to_db',
)
@inject_session
def import_meteringpoints_and_insert_to_db(task, subject, session):
    """
    :param celery.Task task:
    :param str subject:
    :param Session session:
    """
    __log_extra = {
        'subject': subject,
        'pipeline': 'import_meteringpoints',
        'task': 'import_meteringpoints_and_insert_to_db',
    }

    # Get User from DB
    try:
        user = UserQuery(session) \
            .has_sub(subject) \
            .one()
    except orm.exc.NoResultFound:
        raise
    except Exception as e:
        logger.exception('Failed to load User from database, retrying...', extra=__log_extra)
        raise task.retry(exc=e)

    # Import MeteringPoints from DataHubService
    try:
        response = datahub_service.get_meteringpoints(user.access_token)
    except DataHubServiceConnectionError as e:
        logger.exception(f'Failed to establish connection to DataHubService, retrying...', extra=__log_extra)
        raise task.retry(exc=e)
    except DataHubServiceError as e:
        if e.status_code == 400:
            logger.exception('Got BAD REQUEST from DataHubService', extra=__log_extra)
            raise
        else:
            logger.exception('Failed to import MeteringPoints, retrying...', extra=__log_extra)
            raise task.retry(exc=e)

    # Save imported MeteringPoints to database
    try:
        facilities = save_imported_meteringpoints(user, response)
    except Exception as e:
        logger.exception('Failed to save imported Meteringpoints to database, retrying...', extra=__log_extra)
        raise task.retry(exc=e)

    # Logging
    logger.info(f'Imported {len(facilities)} new MeteringPoints from DataHubService', extra=__log_extra)

    for facility in facilities:
        logger.info(f'Imported meteringpoint with GSRN: {facility.gsrn}', extra={
            'gsrn': facility.gsrn,
            'subject': user.sub,
            'pipeline': 'import_meteringpoints',
            'task': 'import_meteringpoints_and_insert_to_db',
        })


# -- Helper functions --------------------------------------------------------


@atomic
def save_imported_meteringpoints(user, response, session):
    """
    :param originexample.auth.User user:
    :param originexample.services.datahub.GetMeteringPointsResponse response:
    :param sqlalchemy.orm.Session session:
    :rtype: list[Facility]
    """
    imported_facilities = []

    for meteringpoint in response.meteringpoints:
        count = FacilityQuery(session) \
            .has_gsrn(meteringpoint.gsrn) \
            .count()

        if count > 0:
            logger.info(f'Skipping meteringpoint with GSRN: {meteringpoint.gsrn} (already exists in DB)', extra={
                'gsrn': meteringpoint.gsrn,
                'subject': user.sub,
                'pipeline': 'import_meteringpoints',
                'task': 'import_meteringpoints_and_insert_to_db',
            })
            continue

        if meteringpoint.type is MeteringPointType.PRODUCTION:
            facility_type = FacilityType.PRODUCTION
        elif meteringpoint.type is MeteringPointType.CONSUMPTION:
            facility_type = FacilityType.CONSUMPTION
        else:
            raise RuntimeError('Should NOT have happened!')

        imported_facilities.append(Facility(
            user=user,
            gsrn=meteringpoint.gsrn,
            sector=meteringpoint.sector,
            facility_type=facility_type,
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

    session.add_all(imported_facilities)
    session.flush()

    return imported_facilities
