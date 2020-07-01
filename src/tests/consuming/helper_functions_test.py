import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from originexample.services.account import (
    GgoCategory,
    TransferDirection,
)
from originexample.consuming import (
    get_consumption,
    get_stored_amount,
    get_retired_amount,
    get_transferred_amount,
    ggo_is_available,
)


@patch('originexample.consuming.helpers.datahub_service')
def test__get_consumption__invokes_datahub_service_correctly(datahub_service_mock):

    # Arrange
    token = 'TOKEN'
    gsrn = 'GSRN'
    begin = datetime(2020, 1, 1, 0, 0, tzinfo=timezone.utc)
    measurement = Mock()

    datahub_service_mock.get_consumption.return_value = Mock(measurement=measurement)

    # Act
    returned_measurement = get_consumption(token, gsrn, begin)

    # Assert
    assert returned_measurement is measurement
    assert datahub_service_mock.get_consumption.called_once()
    assert datahub_service_mock.get_consumption.call_args[0][0] == token
    assert datahub_service_mock.get_consumption.call_args[0][1].gsrn == gsrn
    assert datahub_service_mock.get_consumption.call_args[0][1].begin == begin


@patch('originexample.consuming.helpers.account_service')
def test__get_stored_amount__invokes_account_service_correctly(account_service_mock):

    # Arrange
    token = 'TOKEN'
    begin = datetime(2020, 1, 1, 0, 0, tzinfo=timezone.utc)
    amount = 123

    account_service_mock.get_total_amount.return_value = Mock(amount=amount)

    # Act
    returned_amount = get_stored_amount(token, begin)

    # Assert
    assert returned_amount == amount
    assert account_service_mock.get_total_amount.called_once()
    assert account_service_mock.get_total_amount.call_args[0][0] == token
    assert account_service_mock.get_total_amount.call_args[0][1].filters.begin == begin
    assert account_service_mock.get_total_amount.call_args[0][1].filters.category is GgoCategory.STORED


@patch('originexample.consuming.helpers.account_service')
def test__get_retired_amount__invokes_account_service_correctly(account_service_mock):

    # Arrange
    token = 'TOKEN'
    gsrn = 'GSRN'
    measurement = Mock(address='ADDRESS')
    amount = 123

    account_service_mock.get_total_amount.return_value = Mock(amount=amount)

    # Act
    returned_amount = get_retired_amount(token, gsrn, measurement)

    # Assert
    assert returned_amount == amount
    assert account_service_mock.get_total_amount.called_once()
    assert account_service_mock.get_total_amount.call_args[0][0] == token
    assert account_service_mock.get_total_amount.call_args[0][1].filters.retire_gsrn == [gsrn]
    assert account_service_mock.get_total_amount.call_args[0][1].filters.retire_address == ['ADDRESS']
    assert account_service_mock.get_total_amount.call_args[0][1].filters.category is GgoCategory.RETIRED


@patch('originexample.consuming.helpers.account_service')
def test__get_transferred_amount__invokes_account_service_correctly(account_service_mock):

    # Arrange
    token = 'TOKEN'
    reference = 'REFERENCE'
    begin = datetime(2020, 1, 1, 0, 0, tzinfo=timezone.utc)
    amount = 123

    account_service_mock.get_transferred_amount.return_value = Mock(amount=amount)

    # Act
    returned_amount = get_transferred_amount(token, reference, begin)

    # Assert
    assert returned_amount == amount
    assert account_service_mock.get_transferred_amount.called_once()
    assert account_service_mock.get_transferred_amount.call_args[0][0] == token
    assert account_service_mock.get_transferred_amount.call_args[0][1].direction is TransferDirection.OUTBOUND
    assert account_service_mock.get_transferred_amount.call_args[0][1].filters.reference == [reference]
    assert account_service_mock.get_transferred_amount.call_args[0][1].filters.begin == begin


# -- ggo_is_available() ------------------------------------------------------


@patch('originexample.consuming.helpers.account_service')
def test__ggo_is_available__invokes_account_service_correctly(account_service_mock):

    # Arrange
    ggo = Mock(address='ADDRESS')

    account_service_mock.get_ggo_list.return_value = Mock(results=[])

    # Act
    ggo_is_available('TOKEN', ggo)

    # Assert
    assert account_service_mock.get_ggo_list.called_once()
    assert account_service_mock.get_ggo_list.call_args[0][0] == 'TOKEN'
    assert account_service_mock.get_ggo_list.call_args[0][1].filters.address == ['ADDRESS']
    assert account_service_mock.get_ggo_list.call_args[0][1].filters.category is GgoCategory.STORED


@patch('originexample.consuming.helpers.account_service')
def test__ggo_is_available__account_service_return_empty_list__should_return_false(account_service_mock):

    # Arrange
    account_service_mock.get_ggo_list.return_value = Mock(results=[])

    # Act
    result = ggo_is_available('TOKEN', Mock())

    # Assert
    assert result is False


@patch('originexample.consuming.helpers.account_service')
@pytest.mark.parametrize('returned_ggos', (
    [Mock()],
    [Mock(), Mock()],
))
def test__ggo_is_available__account_service_return_empty_list__should_return_false(account_service_mock, returned_ggos):

    # Arrange
    account_service_mock.get_ggo_list.return_value = Mock(results=returned_ggos)

    # Act
    result = ggo_is_available('TOKEN', Mock())

    # Assert
    assert result is True
