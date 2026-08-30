from src.models import Customer, CustomerState, GameState
from src.events import EventBus
import random

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
                customer.seconds_until_next_item -= dt

                while customer.seconds_until_next_item <= 0:
                    if len(customer.basket.items) >= customer.target_item_count:
                        customer.state = CustomerState.WAITING_IN_LINE
                        self.state.checkout_line.append(customer.uuid)
                        break

                    item = random.choice(self.state.inventory)
                    customer.basket.items.append(item)
                    self.event_bus.emit("customer_added_item", customer=customer, item=item)
                    customer.seconds_until_next_item += customer.item_pickup_period

                    if len(customer.basket.items) >= customer.target_item_count:
                        customer.state = CustomerState.WAITING_IN_LINE
                        self.state.checkout_line.append(customer.uuid)
                        break

            if customer.state == CustomerState.WAITING_IN_LINE:
                customer.patience -= dt

            if customer.patience < 0:
                to_remove.append(customer)

        for customer in to_remove:
            self.event_bus.emit("customer_patience_expired", customer=customer)
            self.state.customers.remove(customer)
            self.state.checkout_line.remove(customer.uuid)

    def _init_susbscriptions(self):
        self.event_bus.subscribe("incorrect_total", handle_incorrect_total)
        self.event_bus.subscribe("customer_added_item", lambda customer, item: print(f'{customer.name} added {item.name}'))

def handle_incorrect_total(customer: Customer):
    customer.patience -= 0.5
    print(f"Register total rejected. {customer.name} is losing patience.")
