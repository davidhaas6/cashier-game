import unittest
from collections import deque
from unittest.mock import patch

from src.command_dispatcher import CommandDispatcher
from src.events import EventBus
from src.models import Basket, Customer, CustomerState, GameState, Item, PickupItem
from src.systems.checkout import CheckoutSystem
from src.systems.customer import CustomerSystem


def make_customer(customer_id, *, patience=100, items=None,
                  state=CustomerState.WAITING_IN_LINE,
                  target_item_count=1, pickup_period=3):
    return Customer(
        uuid=customer_id, name="Sam", description="patient", patience=patience,
        state=state, basket=Basket([] if items is None else list(items)),
        target_item_count=target_item_count, item_pickup_period=pickup_period,
        seconds_until_next_item=pickup_period,
    )


class CheckoutBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.active = make_customer(
            "active", items=[Item("apple", 100), Item("bread", 250)],
        )
        self.next_customer = make_customer("next", items=[Item("milk", 300)])
        self.state = GameState(
            customers=[self.active, self.next_customer],
            checkout_line=deque(["active", "next"]), money=700, inventory=[],
        )
        self.events = EventBus()
        self.customers = CustomerSystem(self.events, self.state, CommandDispatcher())
        self.checkout = CheckoutSystem(self.events, self.state)

    def test_correct_payment_awards_money_once_and_frees_register(self):
        self.checkout.update(0, player_input=None)
        self.checkout.update(0, player_input="3.50")

        self.assertEqual(self.state.money, 1050)
        self.assertNotIn(self.active, self.state.customers)
        self.assertNotIn(self.active.uuid, self.state.checkout_line)

        self.checkout.update(0, player_input=None)
        self.assertEqual(self.checkout.current_customer_id, self.next_customer.uuid)
        self.assertEqual(self.next_customer.state, CustomerState.CHECKING_OUT)
        self.checkout.update(0, player_input=None)
        self.assertEqual(self.state.money, 1050)

    def test_incorrect_input_reduces_patience_and_allows_recovery(self):
        for player_input in ("9.99", "not a number"):
            with self.subTest(player_input=player_input):
                # Each input case gets independent state and real event wiring.
                customer = make_customer("payer", items=[Item("bread", 250)])
                state = GameState([customer], deque([customer.uuid]), 700, [])
                events = EventBus()
                CustomerSystem(events, state, CommandDispatcher())
                checkout = CheckoutSystem(events, state)
                checkout.update(0, player_input=None)
                patience_before = customer.patience

                with patch("builtins.print"):
                    checkout.update(0, player_input=player_input)

                self.assertEqual(state.money, 700)
                self.assertGreater(customer.patience, 0)
                self.assertLess(customer.patience, patience_before)
                self.assertIn(customer, state.customers)
                self.assertEqual(checkout.current_customer_id, customer.uuid)

                checkout.update(0, player_input="2.50")
                self.assertEqual(state.money, 950)
                self.assertNotIn(customer, state.customers)

    def test_no_input_preserves_active_transaction_without_penalty(self):
        self.checkout.update(0, player_input=None)
        patience_before = self.active.patience

        self.checkout.update(0, player_input=None)

        self.assertEqual(self.state.money, 700)
        self.assertEqual(self.active.patience, patience_before)
        self.assertIn(self.active, self.state.customers)
        self.assertEqual(self.checkout.current_customer_id, self.active.uuid)

    def test_active_customer_expires_at_zero_patience_without_payment(self):
        self.checkout.update(0, player_input=None)
        # Keep the queued customer alive while the active customer's timer expires.
        self.next_customer.patience = self.active.patience + 100

        self.customers.update(self.active.patience - 0.5)
        self.assertIn(self.active, self.state.customers)
        self.assertEqual(self.checkout.current_customer_id, self.active.uuid)
        self.assertEqual(self.state.money, 700)

        self.customers.update(0.5)

        self.assertNotIn(self.active, self.state.customers)
        self.assertNotIn(self.active.uuid, self.state.checkout_line)
        self.assertEqual(self.state.money, 700)
        self.checkout.update(0, player_input=None)
        self.assertEqual(self.checkout.current_customer_id, self.next_customer.uuid)
        self.assertEqual(self.next_customer.state, CustomerState.CHECKING_OUT)

    def test_incorrect_total_can_expire_customer_and_free_register(self):
        self.checkout.update(0, player_input=None)
        # This is the one test tied to the current 0.5-second penalty boundary.
        self.active.patience = 0.5

        with patch("builtins.print"):
            self.checkout.update(0, player_input="0")

        self.assertNotIn(self.active, self.state.customers)
        self.assertNotIn(self.active.uuid, self.state.checkout_line)
        self.assertEqual(self.state.money, 700)
        self.checkout.update(0, player_input=None)
        self.assertEqual(self.checkout.current_customer_id, self.next_customer.uuid)
        self.assertEqual(self.next_customer.state, CustomerState.CHECKING_OUT)

    def test_waiting_departure_preserves_active_sale_and_queue_order(self):
        impatient = make_customer("impatient", patience=1)
        last = make_customer("last")
        self.state.customers.extend([impatient, last])
        self.state.checkout_line = deque(["active", "impatient", "next", "last"])
        self.checkout.update(0, player_input=None)

        self.customers.update(0.5)
        self.assertIn(impatient, self.state.customers)
        self.assertEqual(list(self.state.checkout_line), ["impatient", "next", "last"])

        self.customers.update(0.5)

        self.assertNotIn(impatient, self.state.customers)
        self.assertEqual(list(self.state.checkout_line), ["next", "last"])
        self.assertIn(self.active, self.state.customers)
        self.assertEqual(self.checkout.current_customer_id, self.active.uuid)
        self.assertEqual(self.state.money, 700)

        self.checkout.update(0, player_input="3.50")
        self.assertEqual(self.state.money, 1050)
        self.assertNotIn(self.active, self.state.customers)
        self.checkout.update(0, player_input=None)
        self.assertEqual(self.checkout.current_customer_id, self.next_customer.uuid)
        self.assertEqual(self.next_customer.state, CustomerState.CHECKING_OUT)
        self.assertEqual(list(self.state.checkout_line), ["last"])


class ShoppingBehaviorTests(unittest.TestCase):
    def test_pickup_timing_completes_basket_and_queues_customer_once(self):
        item = Item("apple", 100)
        customer = make_customer(
            "shopper", state=CustomerState.SHOPPING,
            target_item_count=4, pickup_period=2,
        )
        state = GameState([customer], deque(), 0, [item])
        dispatcher = CommandDispatcher()
        customers = CustomerSystem(EventBus(), state, dispatcher)
        dispatcher.register(PickupItem, customers.try_pickup_item)

        customers.update(1)
        self.assertEqual(customer.basket.items, [])
        self.assertEqual(list(state.checkout_line), [])

        customers.update(1)
        self.assertEqual(customer.basket.items, [item])
        self.assertEqual(list(state.checkout_line), [])

        customers.update(1.5)
        self.assertEqual(customer.basket.items, [item])
        self.assertEqual(list(state.checkout_line), [])

        customers.update(0.5)
        self.assertEqual(customer.basket.items, [item, item])
        self.assertEqual(list(state.checkout_line), [])

        # Enough elapsed time for multiple pickups, including beyond the target.
        customers.update(10)
        self.assertEqual(customer.basket.items, [item, item, item, item])
        self.assertEqual(customer.state, CustomerState.WAITING_IN_LINE)
        self.assertEqual(list(state.checkout_line), [customer.uuid])

        customers.update(2)
        self.assertEqual(customer.basket.items, [item, item, item, item])
        self.assertEqual(list(state.checkout_line), [customer.uuid])


if __name__ == "__main__":
    unittest.main()
