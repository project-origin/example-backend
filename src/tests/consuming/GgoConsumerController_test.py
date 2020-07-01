from itertools import product

import pytest
from unittest.mock import Mock, patch, ANY
from datetime import datetime, timezone, date

from originexample.common import Unit
from originexample.auth import User
from originexample.services.account import Ggo
from originexample.facilities import Facility, FacilityType
from originexample.consuming import GgoConsumerController, RetiringConsumer
from originexample.agreements import (
    AgreementQuery,
    TradeAgreement,
    AgreementState,
)


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


ggo1 = Ggo(
    address='1',
    sector='DK1',
    begin=datetime(2020, 1, 1, 0, 0, tzinfo=timezone.utc),
    end=datetime(2020, 1, 1, 1, 0, tzinfo=timezone.utc),
    amount=100,
    technology='Wind',
    technology_code='T010101',
    fuel_code='F02020202',
)

ggo2 = Ggo(
    address='1',
    sector='DK2',
    begin=datetime(2020, 1, 1, 0, 0, tzinfo=timezone.utc),
    end=datetime(2020, 1, 1, 1, 0, tzinfo=timezone.utc),
    amount=100,
    technology='Solar',
    technology_code='T020202',
    fuel_code='F02020202',
)


@pytest.fixture(scope='module')
def seeded_session(session):
    """
    Returns a Session object with Ggo + User data seeded for testing
    """
    session.add(user1)
    session.add(user2)
    session.add(user3)
    session.add(user4)
    session.flush()

    types = (FacilityType.PRODUCTION, FacilityType.CONSUMPTION)
    sectors = ('DK1', 'DK2')
    retiring = (True, False)
    combis = list(product(types, sectors, retiring))

    for i, user in enumerate((user1, user2, user3)):
        for j, (type, sector, retire) in enumerate(combis, start=1):
            session.add(Facility(
                user=user,
                gsrn=f'GSRN{i*len(combis)+j}',
                facility_type=type,
                sector=sector,
                name='',
                retiring_priority=(i*len(combis)+j) if retire else None,
            ))

            # session.add(Facility(
            #     user=user,
            #     gsrn=f'GSRN{i*5+2}',
            #     facility_type=FacilityType.CONSUMPTION,
            #     sector='DK1',
            #     name='',
            #     retiring_priority=None,
            # ))
            #
            # session.add(Facility(
            #     user=user,
            #     gsrn=f'GSRN{i*5+3}',
            #     facility_type=FacilityType.PRODUCTION,
            #     sector='DK2',
            #     name='',
            #     retiring_priority=0,
            # ))
            #
            # session.add(Facility(
            #     user=user,
            #     gsrn=f'GSRN{i*5+4}',
            #     facility_type=FacilityType.CONSUMPTION,
            #     sector='DK2',
            #     name='',
            #     retiring_priority=1,
            # ))
            #
            # session.add(Facility(
            #     user=user,
            #     gsrn=f'GSRN{i*5+5}',
            #     facility_type=FacilityType.CONSUMPTION,
            #     sector='DK2',
            #     name='',
            #     retiring_priority=2,
            # ))

    session.commit()
    yield session


# -- TEST CASES --------------------------------------------------------------


@pytest.mark.parametrize('user, ggo', (
        (user1, ggo1),
        (user1, ggo2),
        (user2, ggo1),
        (user2, ggo2),
))
def test__AgreementConsumer__get_retire_consumers__should_return_RetiringConsumer_with_correct_facilities(user, ggo, seeded_session):
    uut = GgoConsumerController()

    # Act
    consumers = list(uut.get_retire_consumers(user, ggo, seeded_session))

    # Assert
    assert len(consumers) == 1
    assert all(isinstance(c, RetiringConsumer) for c in consumers)

    facility = consumers[0].facility

    assert facility.sector == ggo.sector
    assert facility.retiring_priority is not None
    assert facility.user_id == user.id


@patch('originexample.consuming.consumers.account_service')
def test__GgoConsumerController__consume_ggo__consume_nothing__should_not_invoke_AccountService(account_service_mock):

    uut = GgoConsumerController()
    uut.get_consumers = Mock()
    uut.get_consumers.return_value = []

    # Act
    uut.consume_ggo(
        ggo=Mock(amount=100),
        user=Mock(),
        session=Mock(),
    )

    # Assert on AccountService.compose()
    account_service_mock.compose.assert_not_called()


@patch('originexample.consuming.consumers.account_service')
def test__GgoConsumerController__consume_ggo__consume_more_than_available__should_only_consume_available_amount(account_service_mock):

    def __mock_consumer(amount):
        mock = Mock()
        mock.get_desired_amount.return_value = amount
        return mock

    consumer1 = __mock_consumer(50)
    consumer2 = __mock_consumer(40)
    consumer3 = __mock_consumer(30)
    consumer4 = __mock_consumer(20)

    ggo = Mock(amount=100)

    uut = GgoConsumerController()
    uut.get_consumers = Mock()
    uut.get_consumers.return_value = (
        consumer1,
        consumer2,
        consumer3,
    )

    # Act
    uut.consume_ggo(ggo=ggo, user=Mock(), session=Mock())

    # Assert on consumers.consume()
    consumer1.consume.assert_called_once_with(ANY, ggo, 50)
    consumer2.consume.assert_called_once_with(ANY, ggo, 40)
    consumer3.consume.assert_called_once_with(ANY, ggo, 10)
    consumer4.consume.assert_not_called()

    # Assert on AccountService.compose()
    account_service_mock.compose.assert_called_once()
