import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from originexample.consuming.consumers import RetiringConsumer


@patch('originexample.consuming.consumers.get_consumption')
@patch('originexample.consuming.consumers.get_retired_amount')
@pytest.mark.parametrize(
    'ggo_amount, measured_amount, retired_amount, expected_amount', (
    (200,        100,             50,             50),
    (200,        0,               50,             0),
    (200,        None,            50,             0),
    (200,        200,             0,              200),
    (200,        200,             50,             150),
    (100,        200,             0,              100),
    (100,        200,             100,            100),
    (100,        200,             150,            50),
    (100,        200,             200,            0),
    (0,          200,             100,            0),
))
def test__RetiringConsumer__get_desired_amount__should_return_correct_amount(
        get_retired_amount_mock, get_consumption_mock,
        ggo_amount, measured_amount, retired_amount, expected_amount):

    get_retired_amount_mock.return_value = retired_amount

    if measured_amount is None:
        measurement = None
        get_consumption_mock.return_value = None
    else:
        measurement = Mock(amount=measured_amount)
        get_consumption_mock.return_value = measurement

    begin = datetime(2020, 1, 1, 0, 0, tzinfo=timezone.utc)
    facility = Mock(gsrn='GSRN1')
    uut = RetiringConsumer(facility)
    ggo = Mock(begin=begin, amount=ggo_amount)

    # Act
    desired_amount = uut.get_desired_amount(ggo)

    # Assert
    assert desired_amount == expected_amount

    get_consumption_mock.assert_called_once_with(token=facility.user.access_token, gsrn='GSRN1', begin=begin)

    if measured_amount is None:
        get_retired_amount_mock.assert_not_called()
    else:
        get_retired_amount_mock.assert_called_once_with(token=facility.user.access_token, gsrn='GSRN1', measurement=measurement)


def test__RetiringConsumer__consume__should_append_retires():
    request = Mock()
    request.transfers = []
    request.retires = []

    uut = RetiringConsumer(facility=Mock(
        gsrn='Facility GSRN',
        user=Mock(),
    ))

    # Act
    uut.consume(
        request=request,
        ggo=Mock(),
        amount=100,
    )

    # Assert
    assert len(request.transfers) == 0
    assert len(request.retires) == 1
    assert request.retires[0].amount == 100
    assert request.retires[0].gsrn == 'Facility GSRN'
