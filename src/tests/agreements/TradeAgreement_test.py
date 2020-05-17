import pytest
from datetime import datetime

from originexample.auth import User
from originexample.common import Unit
from originexample.agreements import TradeAgreement, AgreementState


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


# -- TEST CASES --------------------------------------------------------------


@pytest.mark.parametrize('amount, unit, calculated_amount', (
        (0,     Unit.Wh,    0),
        (1,     Unit.Wh,    1),
        (100,   Unit.Wh,    10**2),
        (0,     Unit.KWh,   0),
        (1,     Unit.KWh,   10**3),
        (100,   Unit.KWh,   10**5),
        (0,     Unit.MWh,   0),
        (1,     Unit.MWh,   10**6),
        (100,   Unit.MWh,   10**8),
        (0,     Unit.GWh,   0),
        (1,     Unit.GWh,   10**9),
        (100,   Unit.GWh,   10**11),
))
def test__TradeAgreement__calculated_amount__returns_correct_amount(amount, unit, calculated_amount):

    # Arrange
    agreement = TradeAgreement(amount=amount, unit=unit)

    # Assert
    assert agreement.calculated_amount == calculated_amount


@pytest.mark.parametrize('user_propose, user_from, user_to', (
        (user1, user1, user2),
        (user1, user2, user1),
        (user2, user1, user2),
        (user2, user2, user1),
))
def test__TradeAgreement__is_proposed_by__returns_correct_value(user_propose, user_from, user_to):

    # Arrange
    agreement = TradeAgreement(
        user_proposed_id=user_propose.id,
        user_proposed=user_propose,
        user_from_id=user_from.id,
        user_from=user_from,
        user_to_id=user_to.id,
        user_to=user_to,
    )

    # Assert
    assert agreement.is_proposed_by(user_propose) is True


@pytest.mark.parametrize('user_from, user_to', (
        (user1, user2),
        (user2, user1),
))
def test__TradeAgreement__is_inbound_to__returns_correct_value(user_from, user_to):

    # Arrange
    agreement = TradeAgreement(
        user_from_id=user_from.id,
        user_from=user_from,
        user_to_id=user_to.id,
        user_to=user_to,
    )

    # Assert
    assert agreement.is_inbound_to(user_to) is True
    assert agreement.is_inbound_to(user_from) is False


@pytest.mark.parametrize('user_from, user_to', (
        (user1, user2),
        (user2, user1),
))
def test__TradeAgreement__is_outbound_from__returns_correct_value(user_from, user_to):

    # Arrange
    agreement = TradeAgreement(
        user_from_id=user_from.id,
        user_from=user_from,
        user_to_id=user_to.id,
        user_to=user_to,
    )

    # Assert
    assert agreement.is_outbound_from(user_from) is True
    assert agreement.is_outbound_from(user_to) is False


@pytest.mark.parametrize('state, expected_is_pending', (
        (AgreementState.PENDING, True),
        (AgreementState.ACCEPTED, False),
        (AgreementState.DECLINED, False),
        (AgreementState.CANCELLED, False),
        (AgreementState.WITHDRAWN, False),
))
def test__TradeAgreement__is_outbound_from__returns_correct_value(state, expected_is_pending):

    # Arrange
    agreement = TradeAgreement(state=state)

    # Assert
    assert agreement.is_pending() == expected_is_pending

