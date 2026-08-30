
import random
from uuid import uuid4

from src.events import EventBus
from src.models import Basket, Customer, CustomerState, GameState, Item


class SpawnSystem:
    def __init__(self, events: EventBus, state: GameState, spawn_period_s: int) -> None:
        self.sec_since_spawn: float = 0
        self.event_bus: EventBus = events
        self.period: int = spawn_period_s
        self.state: GameState = state

    def update(self, dt: float):
        self.sec_since_spawn += dt
        while self.sec_since_spawn > self.period:
            self.state.customers.append(create_random_customer())
            self.sec_since_spawn -= self.period


def create_random_customer() -> Customer:
    names = ["Alex", "Sam", "Jordan", "Taylor", "Riley"]
    descriptions = ["in a hurry", "patient", "confused", "chatty", "focused"]
    pickup_period = max(0.5,random.gauss(3,1))

    return Customer(
        uuid=uuid4().hex,
        basket=Basket(items=[]),
        name=random.choice(names),
        description=random.choice(descriptions),
        patience=max(1,random.gauss(20,4)),
        state=CustomerState.SHOPPING,
        target_item_count=random.randint(1,5),
        item_pickup_period=pickup_period,
        seconds_until_next_item=pickup_period
    )
