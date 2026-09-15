import unittest
from collections import deque
from unittest.mock import patch

from src.events import EventBus
from src.models import Basket, CheckoutSystemState, Customer, CustomerState, GameState, Item
from src.systems.checkout import CheckoutSystem
from src.systems.customer import CustomerSystem


class CustomerDepartureTests(unittest.TestCase):
    def setUp(self):
        self.customer = Customer(
            uuid="active", name="Sam", description="patient", patience=10,
            state=CustomerState.WAITING_IN_LINE, basket=Basket([Item("apple", 100)]),
            target_item_count=1, item_pickup_period=3, seconds_until_next_item=3,
        )
        self.state = GameState([self.customer], deque(["active"]), 0, [])
        self.events = EventBus()
        self.customers = CustomerSystem(self.events, self.state)
        self.checkout = CheckoutSystem(self.events, self.state)
        self.departures = []
        self.events.subscribe("customer_left", lambda customer: self.departures.append(customer.uuid))

    def start_checkout(self):
        with patch("builtins.input", return_value="0"), patch("builtins.print"):
            self.checkout.update(0)
        self.assertEqual(self.checkout.current_customer_id, "active")

    def assert_departed(self):
        self.assertEqual(self.state.customers, [])
        self.assertEqual(list(self.state.checkout_line), [])
        self.assertEqual(self.departures, ["active"])
        self.assertIsNone(self.checkout.current_customer_id)
        self.assertEqual(self.checkout.checkout_state, CheckoutSystemState.WAITING_FOR_CUSTOMER)
        with patch("builtins.input", side_effect=AssertionError("Unexpected input")):
            self.checkout.update(0)

    def test_payment_removes_customer_and_resets_checkout(self):
        with patch("builtins.input", return_value="1"), patch("builtins.print"):
            self.checkout.update(0)
        self.assertEqual(self.state.money, 100)
        self.assert_departed()

    def test_active_customer_expires_from_elapsed_time(self):
        self.start_checkout()
        self.customers.update(self.customer.patience)
        self.assert_departed()

    def test_incorrect_total_can_expire_active_customer(self):
        self.start_checkout()
        self.customer.patience = 0.5
        with patch("builtins.input", return_value="0"), patch("builtins.print"):
            self.checkout.update(0)
        self.assert_departed()

    def test_waiting_customer_expiration_preserves_active_transaction(self):
        self.start_checkout()
        waiting = Customer(
            uuid="waiting", name="Alex", description="impatient", patience=0.5,
            state=CustomerState.WAITING_IN_LINE, basket=Basket([]),
            target_item_count=1, item_pickup_period=3, seconds_until_next_item=3,
        )
        self.state.customers.append(waiting)
        self.state.checkout_line.append(waiting.uuid)
        self.customers.update(0.5)
        self.assertEqual(self.state.customers, [self.customer])
        self.assertEqual(list(self.state.checkout_line), [])
        self.assertEqual(self.departures, ["waiting"])
        self.assertEqual(self.checkout.current_customer_id, "active")
        self.assertEqual(self.checkout.checkout_state, CheckoutSystemState.ENTERING_TOTAL)


if __name__ == "__main__":
    unittest.main()
