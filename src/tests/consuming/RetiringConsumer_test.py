import pytest
from unittest.mock import Mock, patch

from originexample.consuming.consumers import RetiringConsumer


@patch('originexample.consuming.consumers.account')
@patch('originexample.consuming.consumers.datahub')
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
))
def test__RetiringConsumer__get_desired_amount__should_return_correct_amount(
        datahub, account, ggo_amount, measured_amount, retired_amount, expected_amount):

    uut = RetiringConsumer(facility=Mock())
    account.get_retired_amount.return_value = Mock(amount=retired_amount)
    if measured_amount is None:
        datahub.get_consumption.return_value = Mock(measurement=None)
    else:
        datahub.get_consumption.return_value = Mock(measurement=Mock(amount=measured_amount))

    # Act
    desired_amount = uut.get_desired_amount(Mock(amount=ggo_amount))

    # Assert
    assert desired_amount == expected_amount


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
