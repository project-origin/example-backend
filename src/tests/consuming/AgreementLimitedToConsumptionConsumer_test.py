import pytest
from unittest.mock import Mock, patch
from datetime import timezone, datetime

from originexample.consuming.consumers import AgreementLimitedToConsumptionConsumer


@patch('originexample.consuming.consumers.get_consumption')
@patch('originexample.consuming.consumers.get_transferred_amount')
@patch('originexample.consuming.consumers.get_retired_amount')
@patch('originexample.consuming.consumers.get_stored_amount')
@pytest.mark.parametrize(
    'ggo_amount, agreement_amount, transferred_amount, retired_amount, stored_amount, measured_amount, expected_amount, already_transferred_amount', (
    (200,        100,              0,                  0,              0,             100,             100,             0),
    (200,        100,              50,                 0,              0,             100,             50,              0),
    (200,        100,              0,                  50,             0,             100,             50,              0),
    (200,        100,              0,                  0,              50,            100,             50,              0),
    (50,         100,              0,                  0,              0,             100,             50,              0),
    (200,        100,              0,                  0,              0,             50,              50,              0),
    (200,        100,              0,                  0,              0,             200,             100,             0),
    (100,        200,              0,                  0,              0,             200,             100,             0),
    (200,        100,              0,                  0,              0,             0,               0,               0),
    (200,        100,              0,                  0,              0,             None,            0,               0),
    (200,        100,              10,                 20,             20,            50,              10,              0),

    (200,        100,              0,                  0,              0,             100,             60,              40),
    (200,        100,              50,                 0,              0,             100,             50,              40),
    (200,        100,              0,                  50,             0,             100,             10,              40),
    (200,        100,              0,                  0,              50,            100,             10,              40),
    (50,         100,              0,                  0,              0,             100,             50,              40),
    (200,        100,              0,                  0,              0,             50,              10,              40),
    (200,        100,              0,                  0,              0,             200,             100,             40),
    (100,        200,              0,                  0,              0,             200,             100,             40),
    (200,        100,              0,                  0,              0,             0,               0,               40),
    (200,        100,              0,                  0,              0,             None,            0,               40),
    (200,        100,              10,                 20,             20,            50,              0,               40),
))
def test__AgreementLimitedToConsumptionConsumer__get_desired_amount__should_return_correct_amount(
        get_stored_amount_mock, get_retired_amount_mock, get_transferred_amount_mock, get_consumption_mock,
        ggo_amount, agreement_amount, transferred_amount, retired_amount, stored_amount,
        measured_amount, expected_amount, already_transferred_amount):

    begin = datetime(2020, 1, 1, 0, 0, tzinfo=timezone.utc)
    agreement = Mock(public_id='PUBLIC_ID', calculated_amount=agreement_amount, amount_percent=0)
    ggo = Mock(begin=begin, amount=ggo_amount)
    facility1 = Mock(gsrn='GSRN1')
    facility2 = Mock(gsrn='GSRN2')
    facilities = [facility1, facility2]

    get_transferred_amount_mock.return_value = transferred_amount
    get_retired_amount_mock.return_value = retired_amount / len(facilities)
    get_stored_amount_mock.return_value = stored_amount

    if measured_amount is None:
        measurement = None
        get_consumption_mock.return_value = None
    else:
        measurement = Mock(amount=(measured_amount / len(facilities)))
        get_consumption_mock.return_value = measurement

    uut = AgreementLimitedToConsumptionConsumer(agreement=agreement, session=Mock())
    uut.get_facilities = Mock(return_value=facilities)

    # Act
    desired_amount = uut.get_desired_amount(ggo, already_transferred_amount)

    # Assert
    assert desired_amount == expected_amount

    get_transferred_amount_mock.assert_called_once_with(token=agreement.user_from.access_token, reference='PUBLIC_ID', begin=begin)
    get_stored_amount_mock.assert_called_once_with(token=agreement.user_to.access_token, begin=begin)

    assert get_consumption_mock.call_count == 2
    get_consumption_mock.assert_any_call(token=facility1.user.access_token, gsrn='GSRN1', begin=begin)
    get_consumption_mock.assert_any_call(token=facility2.user.access_token, gsrn='GSRN2', begin=begin)

    if measured_amount is None:
        get_retired_amount_mock.assert_not_called()
    else:
        assert get_retired_amount_mock.call_count == 2
        get_retired_amount_mock.assert_any_call(token=facility1.user.access_token, gsrn='GSRN1', measurement=measurement)
        get_retired_amount_mock.assert_any_call(token=facility2.user.access_token, gsrn='GSRN2', measurement=measurement)


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
