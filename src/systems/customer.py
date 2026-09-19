import random

from src.events import EventBus
from src.models import Customer, CustomerState, GameState


class CustomerSystem:
    def __init__(self, events: EventBus, state: GameState) -> None:
        self.sec_since_spawn: float = 0
        self.event_bus: EventBus = events
        self.state: GameState = state

        self._init_susbscriptions()

    def update(self, dt: float):
        to_remove: list[Customer] = []
        for customer in self.state.customers:
            if customer.state == CustomerState.SHOPPING:
                self._update_shopping_customer(customer, dt)
            elif customer.state == CustomerState.WAITING_IN_LINE:
                self._update_waiting_customer(customer, dt)
            elif customer.state == CustomerState.CHECKING_OUT:
                self._update_checking_out_customer(customer, dt)
            if customer.patience <= 0:
                to_remove.append(customer)

        for customer in to_remove:
            self._expire_customer(customer)

    def _remove_customer(self, customer: Customer) -> None:
        self.state.customers.remove(customer)
        if customer.uuid in self.state.checkout_line:
            self.state.checkout_line.remove(customer.uuid)
        self.event_bus.emit("customer_left", customer=customer)

    def _expire_customer(self, customer: Customer) -> None:
        self._remove_customer(customer)
        self.event_bus.emit("customer_patience_expired", customer=customer)

    def _handle_sale_completed(self, customer: Customer, total: int) -> None:
        self._remove_customer(customer)

    def _handle_incorrect_total(self, customer: Customer) -> None:
        customer.patience -= 0.5
        print(f"Register total rejected. {customer.name} is losing patience.")
        if customer.patience <= 0:
            self._expire_customer(customer)

    def _update_shopping_customer(self, customer: Customer, dt: float) -> None:
        customer.seconds_until_next_item -= dt

        while customer.seconds_until_next_item <= 0:
            if len(customer.basket.items) >= customer.target_item_count:
                self._send_customer_to_checkout_line(customer)
                break

            item = random.choice(self.state.inventory)
            customer.basket.items.append(item)
            self.event_bus.emit("customer_added_item", customer=customer, item=item)
            customer.seconds_until_next_item += customer.item_pickup_period

            if len(customer.basket.items) >= customer.target_item_count:
                self._send_customer_to_checkout_line(customer)
                break

    def _update_waiting_customer(self, customer: Customer, dt: float) -> None:
        customer.patience -= dt

    def _update_checking_out_customer(self, customer: Customer, dt: float) -> None:
        customer.patience -= dt

    def _send_customer_to_checkout_line(self, customer: Customer) -> None:
        customer.state = CustomerState.WAITING_IN_LINE
        self.state.checkout_line.append(customer.uuid)
        self.event_bus.emit("customer_joined_checkout_line", customer=customer)

    def _init_susbscriptions(self):
        self.event_bus.subscribe("incorrect_total", self._handle_incorrect_total)
        self.event_bus.subscribe("sale_completed", self._handle_sale_completed)
        self.event_bus.subscribe("checkout_started", handle_start_checkout)


def handle_start_checkout(customer: Customer):
    customer.patience += 5
