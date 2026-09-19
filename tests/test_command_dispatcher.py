import unittest
from unittest.mock import Mock

from src.command_dispatcher import CommandDispatcher
from src.models import Command, PickupItem


class OtherCommand(Command):
    pass


class CommandDispatcherTests(unittest.TestCase):
    def test_dispatch_calls_matching_handler_and_returns_its_result(self):
        for result in (True, False):
            with self.subTest(result=result):
                dispatcher = CommandDispatcher()
                handler = Mock(return_value=result)
                other_handler = Mock(return_value=True)
                dispatcher.register(PickupItem, handler)
                dispatcher.register(OtherCommand, other_handler)
                command = PickupItem(customer_id="customer", item_id="apple")

                self.assertIs(dispatcher.dispatch(command), result)

                handler.assert_called_once_with(command)
                self.assertIs(handler.call_args.args[0], command)
                other_handler.assert_not_called()

    def test_duplicate_registration_rejects_replacement_and_keeps_original(self):
        dispatcher = CommandDispatcher()
        original = Mock(return_value=True)
        replacement = Mock(return_value=False)
        dispatcher.register(PickupItem, original)

        with self.assertRaises(ValueError):
            dispatcher.register(PickupItem, replacement)

        command = PickupItem(customer_id="customer", item_id="apple")
        self.assertIs(dispatcher.dispatch(command), True)
        original.assert_called_once_with(command)
        replacement.assert_not_called()

    def test_unregistered_command_raises_without_calling_other_handler(self):
        dispatcher = CommandDispatcher()
        handler = Mock(return_value=True)
        dispatcher.register(PickupItem, handler)

        with self.assertRaises(KeyError):
            dispatcher.dispatch(OtherCommand())

        handler.assert_not_called()


if __name__ == "__main__":
    unittest.main()
