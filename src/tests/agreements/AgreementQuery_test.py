import pytz
import pytest
from itertools import product
from unittest.mock import Mock
from datetime import datetime, timezone, date

from originexample.common import Unit
from originexample.auth import User
from originexample.agreements.queries import AgreementQuery
from originexample.agreements.models import TradeAgreement, AgreementState


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
    users = (
        # (user_proposed, user_from, user_to)
        (user1, user1, user2),
        (user2, user1, user2),
        (user1, user1, user3),
        (user3, user1, user3),

        (user2, user2, user1),
        (user1, user2, user1),
        (user2, user2, user3),
        (user3, user2, user3),

        (user3, user3, user1),
        (user1, user3, user1),
        (user3, user3, user2),
        (user2, user3, user2),
    )

    technologies = (None, 'Wind', 'Marine')
    states = (
        AgreementState.PENDING,
        AgreementState.ACCEPTED,
        AgreementState.DECLINED,
        AgreementState.CANCELLED,
        AgreementState.WITHDRAWN,
    )

    dates = (
        # (date_from, date_to)
        (date(2020, 1, 1), date(2020, 1, 31)),
        (date(2020, 1, 1), date(2020, 2, 29)),
        (date(2020, 2, 1), date(2020, 3, 31)),
    )

    # Combinations
    combinations = product(users, technologies, states, dates)

    # Seed Agreements
    for i, ((user_propose, user_from, user_to), tech, state, (date_from, date_to)) in enumerate(combinations, start=1):
        session.add(TradeAgreement(
            id=i,
            public_id=str(i),
            user_proposed_id=user_propose.id,
            user_proposed=user_propose,
            user_from_id=user_from.id,
            user_from=user_from,
            user_to_id=user_to.id,
            user_to=user_to,
            state=state,
            date_from=date_from,
            date_to=date_to,
            amount=100,
            unit=Unit.Wh,
            technology=tech,
            reference='some-reference',
        ))

        if i % 250 == 0:
            session.flush()

    session.commit()

    yield session


# -- TEST CASES --------------------------------------------------------------


@pytest.mark.parametrize('public_id', ('1', '2'))
def test__AgreementQuery__has_public_id__TradeAgreement_exists__returns_correct_agreement(
        seeded_session, public_id):

    query = AgreementQuery(seeded_session) \
        .has_public_id(public_id)

    assert query.count() == 1
    assert query.one().public_id == public_id


@pytest.mark.parametrize('public_id', ('-1', '0', 'asd'))
def test__AgreementQuery__has_public_id__TradeAgreement_does_not_exist__returs_nothing(
        seeded_session, public_id):

    query = AgreementQuery(seeded_session) \
        .has_public_id(public_id)

    assert query.count() == 0
    assert query.one_or_none() is None


@pytest.mark.parametrize('user', (user1, user2, user3))
def test__AgreementQuery__belongs_to__TradeAgreement_exists__returns_correct_agreements(
        seeded_session, user):

    query = AgreementQuery(seeded_session) \
        .belongs_to(user)

    assert query.count() > 0
    assert all(user.id in (ag.user_from_id, ag.user_to_id) for ag in query.all())


def test__AgreementQuery__belongs_to__TradeAgreement_does_not_exist__returs_nothing(seeded_session):

    query = AgreementQuery(seeded_session) \
        .belongs_to(user4)

    assert query.count() == 0


@pytest.mark.parametrize('user', (user1, user2, user3))
def test__AgreementQuery__is_proposed_by__TradeAgreement_exists__returns_correct_agreements(
        seeded_session, user):

    query = AgreementQuery(seeded_session) \
        .is_proposed_by(user)

    assert query.count() > 0
    assert all(ag.user_proposed_id == user.id for ag in query.all())


def test__AgreementQuery__is_proposed_by__TradeAgreement_does_not_exist__returs_nothing(seeded_session):

    query = AgreementQuery(seeded_session) \
        .is_proposed_by(user4)

    assert query.count() == 0


@pytest.mark.parametrize('user', (user1, user2, user3))
def test__AgreementQuery__is_proposed_to__TradeAgreement_exists__returns_correct_agreements(
        seeded_session, user):

    query = AgreementQuery(seeded_session) \
        .is_proposed_to(user)

    assert query.count() > 0
    assert all(ag.user_proposed_id != user.id for ag in query.all())
    assert all(user.id in (ag.user_from_id, ag.user_to_id) for ag in query.all())


def test__AgreementQuery__is_proposed_to__TradeAgreement_does_not_exist__returs_nothing(seeded_session):

    query = AgreementQuery(seeded_session) \
        .is_proposed_to(user4)

    assert query.count() == 0


@pytest.mark.parametrize('user', (user1, user2, user3))
def test__AgreementQuery__is_awaiting_response_by__TradeAgreement_exists__returns_correct_agreements(
        seeded_session, user):

    query = AgreementQuery(seeded_session) \
        .is_awaiting_response_by(user)

    assert query.count() > 0
    assert all(ag.state is AgreementState.PENDING for ag in query.all())
    assert all(ag.user_proposed_id != user.id for ag in query.all())
    assert all(user.id in (ag.user_from_id, ag.user_to_id) for ag in query.all())


def test__AgreementQuery__is_awaiting_response_by__TradeAgreement_does_not_exist__returs_nothing(seeded_session):

    query = AgreementQuery(seeded_session) \
        .is_awaiting_response_by(user4)

    assert query.count() == 0


@pytest.mark.parametrize('user', (user1, user2, user3))
def test__AgreementQuery__is_inbound_to__TradeAgreement_exists__returns_correct_agreements(
        seeded_session, user):

    query = AgreementQuery(seeded_session) \
        .is_inbound_to(user)

    assert query.count() > 0
    assert all(ag.user_to_id == user.id for ag in query.all())


def test__AgreementQuery__is_inbound_to__TradeAgreement_does_not_exist__returs_nothing(seeded_session):

    query = AgreementQuery(seeded_session) \
        .is_inbound_to(user4)

    assert query.count() == 0


@pytest.mark.parametrize('user', (user1, user2, user3))
def test__AgreementQuery__is_outbound_from__TradeAgreement_exists__returns_correct_agreements(
        seeded_session, user):

    query = AgreementQuery(seeded_session) \
        .is_outbound_from(user)

    assert query.count() > 0
    assert all(ag.user_from_id == user.id for ag in query.all())


def test__AgreementQuery__is_outbound_from__TradeAgreement_does_not_exist__returs_nothing(seeded_session):

    query = AgreementQuery(seeded_session) \
        .is_outbound_from(user4)

    assert query.count() == 0


def test__AgreementQuery__is_pending__returns_correct_agreements(seeded_session):
    query = AgreementQuery(seeded_session) \
        .is_pending()

    assert query.count() > 0
    assert all(ag.state is AgreementState.PENDING for ag in query.all())


def test__AgreementQuery__is_accepted__returns_correct_agreements(seeded_session):
    query = AgreementQuery(seeded_session) \
        .is_accepted()

    assert query.count() > 0
    assert all(ag.state is AgreementState.ACCEPTED for ag in query.all())


def test__AgreementQuery__is_active__returns_correct_agreements(seeded_session):
    query = AgreementQuery(seeded_session) \
        .is_active()

    assert query.count() > 0
    assert all(ag.state is AgreementState.ACCEPTED for ag in query.all())


# -- is_elibigle_to_trade() --------------------------------------------------


@pytest.mark.parametrize('ggo_technology, ggo_begin', (
    ('Wind', datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)),
    ('Wind', datetime(2020, 1, 31, 23, 0, 0, tzinfo=timezone.utc)),
    ('Wind', datetime(2020, 2, 1, 0, 0, 0, tzinfo=timezone.utc)),
    ('Wind', datetime(2020, 2, 29, 23, 0, 0, tzinfo=timezone.utc)),
    ('Wind', datetime(2020, 3, 1, 0, 0, 0, tzinfo=timezone.utc)),
    ('Wind', datetime(2020, 3, 31, 21, 0, 0, tzinfo=timezone.utc)),
))
def test__AgreementQuery__is_elibigle_to_trade__TradeAgreement_exists__returns_correct_agreements(
        seeded_session, ggo_technology, ggo_begin):

    # Arrange
    ggo = Mock(begin=ggo_begin, technology=ggo_technology)

    # Act
    query = AgreementQuery(seeded_session) \
        .is_elibigle_to_trade(ggo)

    # Assert
    assert query.count() > 0
    assert all(ag.date_from <= ggo_begin.astimezone(pytz.timezone('Europe/Copenhagen')).date() <= ag.date_to for ag in query.all())
    assert all(ag.technology in (None, ggo_technology) for ag in query.all())


@pytest.mark.parametrize('ggo_begin', (
    datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
    datetime(2020, 1, 31, 23, 0, 0, tzinfo=timezone.utc),
    datetime(2020, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
    datetime(2020, 2, 29, 23, 0, 0, tzinfo=timezone.utc),
    datetime(2020, 3, 1, 0, 0, 0, tzinfo=timezone.utc),
    datetime(2020, 3, 31, 21, 0, 0, tzinfo=timezone.utc),
))
def test__AgreementQuery__is_elibigle_to_trade__technology_does_not_exists__returns_only_agreements_without_technology(
        seeded_session, ggo_begin):

    # Arrange
    ggo = Mock(begin=ggo_begin, technology='nonexisting-technology')

    # Act
    query = AgreementQuery(seeded_session) \
        .is_elibigle_to_trade(ggo)

    # Assert
    assert query.count() > 0
    assert all(ag.technology is None for ag in query.all())


@pytest.mark.parametrize('ggo_begin', (
    datetime(2019, 12, 31, 21, 0, 0, tzinfo=timezone.utc),
    datetime(2020, 4, 1, 0, 0, 0, tzinfo=timezone.utc),
))
def test__AgreementQuery__is_elibigle_to_trade__ggo_date_is_outside_agreements__returns_nothing(
        seeded_session, ggo_begin):

    # Arrange
    ggo = Mock(begin=ggo_begin, technology='Wind')

    # Act
    query = AgreementQuery(seeded_session) \
        .is_elibigle_to_trade(ggo)

    # Assert
    assert query.count() == 0
