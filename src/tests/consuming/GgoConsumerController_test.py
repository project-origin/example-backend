from unittest.mock import Mock, patch, ANY

from originexample.consuming.consumers import GgoConsumerController


@patch('originexample.consuming.consumers.account')
def test__GgoConsumerController__consume_ggo__consume_nothing__should_not_invoke_AccountService(account):

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
    account.compose.assert_not_called()


@patch('originexample.consuming.consumers.account')
def test__GgoConsumerController__consume_ggo__consume_more_than_available__should_only_consume_available_amount(account):

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
    account.compose.assert_called_once()
