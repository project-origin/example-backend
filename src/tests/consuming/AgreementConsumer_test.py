import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from originexample.consuming.consumers import AgreementConsumer


@patch('originexample.consuming.consumers.get_transferred_amount')
@pytest.mark.parametrize(
    'ggo_amount, agreement_amount, transferred_amount, expected_amount', (
    (200,        100,              50,                 50),
    (200,        0,                50,                 0),
    (200,        200,              0,                  200),
    (200,        200,              50,                 150),
    (100,        200,              0,                  100),
    (100,        200,              100,                100),
    (100,        200,              150,                50),
    (100,        200,              200,                0),
    (0,          200,              100,                0),
))
def test__AgreementConsumer__get_desired_amount__should_return_correct_amount(
        get_transferred_amount_mock, ggo_amount, agreement_amount, transferred_amount, expected_amount):

    get_transferred_amount_mock.return_value = transferred_amount

    begin = datetime(2020, 1, 1, 0, 0, tzinfo=timezone.utc)
    agreement = Mock(public_id='PUBLIC_ID', calculated_amount=agreement_amount)
    ggo = Mock(begin=begin, amount=ggo_amount)
    uut = AgreementConsumer(agreement=agreement)

    # Act
    desired_amount = uut.get_desired_amount(ggo)

    # Assert
    assert desired_amount == expected_amount

    get_transferred_amount_mock.assert_called_once_with(token=agreement.user_from.access_token, reference='PUBLIC_ID', begin=begin)


def test__AgreementConsumer__consume__should_append_transfers():
    request = Mock()
    request.transfers = []
    request.retires = []

    uut = AgreementConsumer(agreement=Mock(
        public_id='Agreement Public ID',
        user_to=Mock(sub='user_to_sub'),
        calculated_amount=100,
    ))

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
