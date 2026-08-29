from src.models import Customer, CustomerState, GameState
from src.events import EventBus

class CustomerSystem:
    def __init__(self, events: EventBus, state: GameState) -> None:
        self.sec_since_spawn: float = 0
        self.event_bus: EventBus = events
        self.state: GameState = state

        self._init_susbscriptions()

    def update(self, dt: float):
        to_remove: list[Customer] = []
        for customer in self.state.customers:

            if customer.state == CustomerState.WAITING_IN_LINE:
                customer.patience -= dt

            if customer.patience < 0:
                to_remove.append(customer)

        for customer in to_remove:
            self.event_bus.emit("customer_patience_expired", customer=customer)
            self.state.customers.remove(customer)

    def _init_susbscriptions(self):
        self.event_bus.subscribe("incorrect_total", handle_incorrect_total)

def handle_incorrect_total(customer: Customer):
    customer.patience -= 0.5
    print(f"Register total rejected. {customer.name} is losing patience.")
