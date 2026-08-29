from src.models import Customer, GameState
from src.events import EventBus

class CustomerSystem:
    def __init__(self, events: EventBus, state: GameState) -> None:
        self.sec_since_spawn: float = 0
        self.event_bus: EventBus = events
        self.state: GameState = state

    def update(self, dt: float):
        to_remove: list[Customer] = []
        for customer in self.state.customers:
            customer.patience -= dt

            if customer.patience < 0:
                to_remove.append(customer)

        for customer in to_remove:
            self.event_bus.emit("customer_left", customer=customer)
            self.state.customers.remove(customer)
