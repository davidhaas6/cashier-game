import threading
import time
from collections import deque
from queue import Queue

from src.events import EventBus
from src.input_handler import read
from src.models import CustomerState, GameState, Item
from src.systems import CustomerSystem, SpawnSystem
from src.systems.checkout import CheckoutSystem


class GameManager:
    def __init__(self) -> None:
        # core
        self.events: EventBus = EventBus()
        self.state: GameState = GameState(
            customers=[],
            money=0,
            inventory=[
                Item("apple", 100),
                Item("bread", 250),
                Item("milk", 300),
                Item("eggs", 425),
                Item("coffee", 200),
            ],
            checkout_line=deque(),
        )

        # systems
        self.spawner: SpawnSystem = SpawnSystem(self.events, self.state, 4)
        self.customer_system: CustomerSystem = CustomerSystem(self.events, self.state)
        self.checkout_system: CheckoutSystem = CheckoutSystem(self.events, self.state)
        self.seconds_since_print: float = 0

        # io
        self.input_queue = Queue[str]()
        self.input_thread = threading.Thread(target=read,args=(self.input_queue, self.events), daemon=True)
        self.input_thread.start()

        self.init_event_system()

    def loop(self):
        TICK_RATE_HZ = 2

        last_time = time.perf_counter()
        while True:
            start = time.perf_counter()
            dt_seconds = start - last_time
            last_time = start

            player_input=None
            if not self.input_queue.empty():
                player_input = self.input_queue.get_nowait()

            # use .update for continuous responsibilities and events for discrete moments/reactions
            self.spawner.update(dt_seconds)
            self.customer_system.update(dt_seconds)
            self.checkout_system.update(dt_seconds, player_input)
            self.print_customers(dt_seconds, 2)

            duration_s = time.perf_counter() - start
            time.sleep(max(0, 1 / TICK_RATE_HZ - duration_s))

    def init_event_system(self):
        # self.events.subscribe(
        #     "checkout_started",
        #     lambda customer: print(f"{customer.name}'s checkout started."),
        # )
        self.events.subscribe(
            "sale_completed",
            lambda customer, total: print(f"Sale complete! {customer.name}-{customer.uuid[:3]} paid ${total / 100:.2f}"),
        )
        self.events.subscribe(
            "customer_left",
            lambda customer: print(f"{customer.name}-{customer.uuid[:3]} left."),
        )
        # self.events.subscribe(
        #     "customer_joined_checkout_line",
        #     lambda customer: print(f"{customer.name} joined the checkout line."),
        # )

    def print_customers(self, dt: float, period_s: int = 1):
        self.seconds_since_print += dt
        if self.seconds_since_print < period_s:
            return

        self.seconds_since_print = 0
        shopping_count = sum(
            customer.state == CustomerState.SHOPPING
            for customer in self.state.customers
        )
        customer_checkout = next(
            (
                customer for customer in self.state.customers
                if customer.state == CustomerState.CHECKING_OUT
            ),
            None,
        )

        print("\n--- Register ---")
        print(
            f"Cash: ${self.state.money / 100:.2f} | "
            f"Shopping: {shopping_count} | Waiting: {len(self.state.checkout_line)}"
        )

        if customer_checkout is None:
            if not self.state.customers:
                print("\nNo customers in the store. Waiting for arrivals.")
            else:
                print("\nNobody at the register. Waiting for the next customer.")
            return

        print(
            f"\nServing: {customer_checkout.name}-{customer_checkout.uuid[:3]}"
            f" ({customer_checkout.description})"
        )
        print(f"Patience: {customer_checkout.patience:.1f}s")
        print("\nBasket:")
        for item in customer_checkout.basket.items:
            print(f"  {item.name:<12} ${item.price / 100:.2f}")
        print("\nEnter total in dollars, then press Enter.")
