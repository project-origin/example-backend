import pytest
from unittest.mock import Mock, patch

from originexample.consuming.consumers import AgreementConsumer


@patch('originexample.consuming.consumers.account')
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
))
def test__AgreementConsumer__get_desired_amount__should_return_correct_amount(
        account, ggo_amount, agreement_amount, transferred_amount, expected_amount):

    agreement = Mock(calculated_amount=agreement_amount)
    uut = AgreementConsumer(agreement=agreement)
    account.get_transferred_amount.return_value = Mock(amount=transferred_amount)

    # Act
    desired_amount = uut.get_desired_amount(Mock(amount=ggo_amount))

    # Assert
    assert desired_amount == expected_amount


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
    assert request.transfers[0].sub == 'user_to_sub'
