import pytest
from unittest.mock import Mock
from datetime import datetime
from itertools import product

from originexample.auth import User
from originexample.facilities import FacilityType, Facility, FacilityQuery


user1 = User(
    id=1,
    sub='28a7240c-088e-4659-bd66-d76afb8c762f',
    name='User 1',
    company='Company 1',
    email='user1@email.com',
    phone='11111111',
    access_token='access_token',
    refresh_token='access_token',
    token_expire=datetime(2030, 1, 1, 0, 0, 0),
)

user2 = User(
    id=2,
    sub='972cfd2e-cbd3-42e6-8e0e-c0c5c502f25f',
    name='User 2',
    company='Company 2',
    email='user2@email.com',
    phone='22222222',
    access_token='access_token',
    refresh_token='access_token',
    token_expire=datetime(2030, 1, 1, 0, 0, 0),
)

user3 = User(
    id=3,
    sub='7169e62d-e349-4af2-9587-6027a4e86cf9',
    name='User 3',
    company='Company 3',
    email='user3@email.com',
    phone='33333333',
    access_token='access_token',
    refresh_token='access_token',
    token_expire=datetime(2030, 1, 1, 0, 0, 0),
)

user4 = User(
    id=4,
    sub='7eca644f-b6df-42e5-b6ae-03cb490678c9',
    name='User 4',
    company='Company 4',
    email='user4@email.com',
    phone='44444444',
    access_token='access_token',
    refresh_token='access_token',
    token_expire=datetime(2030, 1, 1, 0, 0, 0),
)



@pytest.fixture(scope='module')
def seeded_session(session):
    """
    Returns a Session object with Ggo + User data seeded for testing
    """
    # Dependencies
    session.add(user1)
    session.add(user2)
    session.add(user3)
    session.add(user4)

    # Input for combinations
    users = (user1, user2, user3)
    sectors = ('DK1', 'DK2')
    types = (FacilityType.PRODUCTION, FacilityType.CONSUMPTION)
    should_retire = (True, False)

    # Combinations
    combinations = product(users, sectors, types, should_retire)

    for i, (usr, sector, typ, ret) in enumerate(combinations, start=1):
        if ret:
            retiring_priority = session \
                .query(Facility) \
                .filter_by(user_id=usr.id) \
                .count()
        else:
            retiring_priority = None

        session.add(Facility(
            id=i,
            public_id=str(i),
            user_id=usr.id,
            user=usr,
            gsrn=f'GSRN{i}',
            facility_type=typ,
            technology_code='technology_code',
            fuel_code='fuel_code',
            sector=sector,
            name=f'Facility {i}',
            street_code='',
            street_name='',
            building_number='',
            city_name='',
            postcode='',
            municipality_code='',
            retiring_priority=retiring_priority,
        ))

        if i % 250 == 0:
            session.flush()

    session.commit()

    yield session


# -- TEST CASES --------------------------------------------------------------


@pytest.mark.parametrize('public_id', ('1', '2'))
def test__FacilityQuery__has_public_id__Facility_exists__returns_correct_facility(
        seeded_session, public_id):

    query = FacilityQuery(seeded_session) \
        .has_public_id(public_id)

    assert query.count() == 1
    assert query.one().public_id == public_id


@pytest.mark.parametrize('public_id', ('-1', '0', 'asd'))
def test__FacilityQuery__has_public_id__Facility_does_not_exist__returs_nothing(
        seeded_session, public_id):

    query = FacilityQuery(seeded_session) \
        .has_public_id(public_id)

    assert query.count() == 0
    assert query.one_or_none() is None


@pytest.mark.parametrize('public_ids', (
        ['1'],
        ['1', '2'],
))
def test__FacilityQuery__has_any_public_id__all_ids_exists__returns_correct_facility(
        seeded_session, public_ids):

    query = FacilityQuery(seeded_session) \
        .has_any_public_id(public_ids)

    assert query.count() == len(public_ids)
    assert all(f.public_id in public_ids for f in query.all())


@pytest.mark.parametrize('public_ids', (
        ['1', 'asd'],
        ['1', '2', 'asd'],
))
def test__FacilityQuery__has_any_public_id__some_ids_exists__returns_correct_facility(
        seeded_session, public_ids):

    query = FacilityQuery(seeded_session) \
        .has_any_public_id(public_ids)

    assert query.count() > 0
    assert all(f.public_id in public_ids for f in query.all())


@pytest.mark.parametrize('public_ids', (
        ['asd'],
        ['asd', 'foobar'],
))
def test__FacilityQuery__has_any_public_id__no_ids_exists__returns_nothing(
        seeded_session, public_ids):

    query = FacilityQuery(seeded_session) \
        .has_any_public_id(public_ids)

    assert query.count() == 0


@pytest.mark.parametrize('gsrn', ('GSRN1', 'GSRN2'))
def test__FacilityQuery__has_gsrn__Facility_exists__returns_correct_facility(
        seeded_session, gsrn):

    query = FacilityQuery(seeded_session) \
        .has_gsrn(gsrn)

    assert query.count() == 1
    assert query.one().gsrn == gsrn


@pytest.mark.parametrize('gsrn', ('-1', '0', 'asd'))
def test__FacilityQuery__has_gsrn__Facility_does_not_exist__returs_nothing(
        seeded_session, gsrn):

    query = FacilityQuery(seeded_session) \
        .has_gsrn(gsrn)

    assert query.count() == 0
    assert query.one_or_none() is None


@pytest.mark.parametrize('gsrn', (
        ['GSRN1'],
        ['GSRN1', 'GSRN2'],
))
def test__FacilityQuery__has_any_gsrn__all_ids_exists__returns_correct_facility(
        seeded_session, gsrn):

    query = FacilityQuery(seeded_session) \
        .has_any_gsrn(gsrn)

    assert query.count() == len(gsrn)
    assert all(f.gsrn in gsrn for f in query.all())


@pytest.mark.parametrize('gsrn', (
        ['GSRN1', 'asd'],
        ['GSRN1', 'GSRN2', 'asd'],
))
def test__FacilityQuery__has_any_gsrn__some_ids_exists__returns_correct_facility(
        seeded_session, gsrn):

    query = FacilityQuery(seeded_session) \
        .has_any_gsrn(gsrn)

    assert query.count() > 0
    assert all(f.gsrn in gsrn for f in query.all())


@pytest.mark.parametrize('gsrn', (
        ['asd'],
        ['asd', 'foobar'],
))
def test__FacilityQuery__has_any_gsrn__no_ids_exists__returns_nothing(
        seeded_session, gsrn):

    query = FacilityQuery(seeded_session) \
        .has_any_gsrn(gsrn)

    assert query.count() == 0


@pytest.mark.parametrize('user', (user1, user2, user3))
def test__FacilityQuery__belongs_to__Facility_exists__returns_correct_facility(
        seeded_session, user):

    query = FacilityQuery(seeded_session) \
        .belongs_to(user)

    assert query.count() > 0
    assert all(f.user_id == user.id for f in query.all())


def test__FacilityQuery__belongs_to__Facility_does_not_exists__returns_nothing(seeded_session):

    query = FacilityQuery(seeded_session) \
        .belongs_to(user4)

    assert query.count() == 0


@pytest.mark.parametrize('facility_type', (FacilityType.PRODUCTION, FacilityType.CONSUMPTION))
def test__FacilityQuery__is_type__returns_correct_facilities(
        seeded_session, facility_type):

    query = FacilityQuery(seeded_session) \
        .is_type(facility_type)

    assert query.count() > 0
    assert all(f.facility_type == facility_type for f in query.all())


def test__FacilityQuery__is_producer__returns_correct_facilities(seeded_session):

    query = FacilityQuery(seeded_session) \
        .is_producer()

    assert query.count() > 0
    assert all(f.facility_type == FacilityType.PRODUCTION for f in query.all())


def test__FacilityQuery__is_consumer__returns_correct_facilities(seeded_session):

    query = FacilityQuery(seeded_session) \
        .is_consumer()

    assert query.count() > 0
    assert all(f.facility_type == FacilityType.CONSUMPTION for f in query.all())


def test__FacilityQuery__is_retire_receiver__returns_correct_facilities(seeded_session):

    query = FacilityQuery(seeded_session) \
        .is_retire_receiver()

    assert query.count() > 0
    assert all(f.retiring_priority is not None for f in query.all())


@pytest.mark.parametrize('ggo_sector', ('DK1', 'DK2'))
def test__FacilityQuery__is_eligible_to_retire__sector_exists__returns_correct_facilities(
        seeded_session, ggo_sector):

    ggo = Mock(sector=ggo_sector)

    query = FacilityQuery(seeded_session) \
        .is_eligible_to_retire(ggo)

    assert query.count() > 0
    assert all(f.sector == ggo_sector for f in query.all())
    assert all(f.facility_type == FacilityType.CONSUMPTION for f in query.all())


@pytest.mark.parametrize('ggo_sector', ('DK1', 'DK2'))
def test__FacilityQuery__is_eligible_to_retire__sector_does_not_exists__returns_nothing(
        seeded_session, ggo_sector):

    ggo = Mock(sector='NO-FACILITIES-HAS-THIS-SECTOR')

    query = FacilityQuery(seeded_session) \
        .is_eligible_to_retire(ggo)

    assert query.count() == 0


def test__FacilityQuery__get_distinct_sectors__facilities_exists__returns_list_of_correct_sectors(seeded_session):

    distinct_sectors = FacilityQuery(seeded_session) \
        .get_distinct_sectors()

    assert sorted(distinct_sectors) == ['DK1', 'DK2']


def test__FacilityQuery__get_distinct_sectors__facilities_does_notexists__returns_empty_list(seeded_session):

    distinct_sectors = FacilityQuery(seeded_session) \
        .has_gsrn('NO-FACILITY-HAS-THIS-GSRN') \
        .get_distinct_sectors()

    assert sorted(distinct_sectors) == []
