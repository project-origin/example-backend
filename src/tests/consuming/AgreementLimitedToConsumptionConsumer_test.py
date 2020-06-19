import pytest
from unittest.mock import Mock, patch

from originexample.consuming.consumers import AgreementLimitedToConsumptionConsumer


@patch('originexample.consuming.consumers.account_service')
@patch('originexample.consuming.consumers.datahub_service')
@pytest.mark.parametrize(
    'ggo_amount, agreement_amount, transferred_amount, retired_amount, stored_amount, measured_amount, expected_amount', (
    (200,        100,              0,                  0,              0,             100,             100),
    (200,        100,              50,                 0,              0,             100,             50),
    (200,        100,              0,                  50,             0,             100,             50),
    (200,        100,              0,                  0,              50,            100,             50),

    (50,         100,              0,                  0,              0,             100,             50),
    (200,        100,              0,                  0,              0,             50,              50),
    (200,        100,              0,                  0,              0,             200,             100),
    (100,        200,              0,                  0,              0,             200,             100),
    (200,        100,              0,                  0,              0,             0,               0),
    (200,        100,              0,                  0,              0,             None,            0),

    (200,        100,              10,                 20,             20,            50,              30),
))
def test__AgreementLimitedToConsumptionConsumer__get_desired_amount__should_return_correct_amount(
        datahub_service_mock, account_service_mock,
        ggo_amount, agreement_amount, transferred_amount, retired_amount, stored_amount, measured_amount, expected_amount):

    agreement = Mock(calculated_amount=agreement_amount)
    facilities = [
        Mock(gsrn='GSRN1'),
        Mock(gsrn='GSRN2'),
    ]

    account_service_mock.get_transferred_amount.return_value = Mock(amount=transferred_amount)
    account_service_mock.get_retired_amount.return_value = Mock(amount=(retired_amount / len(facilities)))
    account_service_mock.get_total_amount.return_value = Mock(amount=stored_amount)
    if measured_amount is None:
        datahub_service_mock.get_consumption.return_value = Mock(measurement=None)
    else:
        datahub_service_mock.get_consumption.return_value = Mock(measurement=Mock(amount=(measured_amount / len(facilities))))

    uut = AgreementLimitedToConsumptionConsumer(agreement=agreement, session=Mock())
    uut.get_facilities = Mock(return_value=facilities)

    # Act
    desired_amount = uut.get_desired_amount(Mock(amount=ggo_amount))

    # Assert
    assert desired_amount == expected_amount


def test__AgreementLimitedToConsumptionConsumer__consume__should_append_transfers():
    request = Mock()
    request.transfers = []
    request.retires = []

    uut = AgreementLimitedToConsumptionConsumer(agreement=Mock(
        public_id='Agreement Public ID',
        user_to=Mock(sub='user_to_sub'),
        calculated_amount=100,
    ), session=Mock())

    # Act
    uut.consume(
        request=request,
        ggo=Mock(),
        amount=100,
    )

    # Assert
    assert len(request.transfers) == 1
    assert len(request.retires) == 0
    assert request.transfers[0].amount == 100
    assert request.transfers[0].reference == 'Agreement Public ID'
    assert request.transfers[0].account == 'user_to_sub'
