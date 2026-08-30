from collections import deque
import time

from src.events import EventBus
from src.models import CustomerState, GameState, Item
from src.systems import CustomerSystem, SpawnSystem


class GameManager:
    def __init__(self) -> None:
        self.events: EventBus = EventBus()
        self.state: GameState = GameState(customers=[], money=0, inventory=[
            Item("apple", 100),
            Item("bread", 250),
            Item("milk", 300),
            Item("eggs", 425),
            Item("coffee", 200),
        ], checkout_line=deque())
        self.spawner: SpawnSystem = SpawnSystem(self.events, self.state, 4)
        self.customer_system: CustomerSystem = CustomerSystem(self.events, self.state)
        self.seconds_since_print: float = 0
        self.init_event_system()

    def loop(self):
        TICK_RATE_HZ = 2

        last_time = time.perf_counter()
        while True:
            start = time.perf_counter()

            dt_seconds = start - last_time
            last_time = start

            # use .update for continuous responsibilities and events for discrete moments/reactions
            self.spawner.update(dt_seconds)
            self.customer_system.update(dt_seconds)
            self.advance_state(dt_seconds)

            if len(self.state.checkout_line) > 0:
                self.checkout()

            duration_s = time.perf_counter() - start
            time.sleep(max(0, 1 / TICK_RATE_HZ - duration_s))


    def init_event_system(self):
        self.events.subscribe("checkout_started", lambda customer: print(f"{customer.name}'s checkout started."))
        self.events.subscribe("sale_completed", lambda customer, total: print(f"{customer.name} paid ${total/100:.2f}"))
        self.events.subscribe("customer_patience_expired", lambda customer: print(f"{customer.name} left."))
        self.events.subscribe("customer_joined_checkout_line", lambda customer: print(f"{customer.name} joined the checkout line."))

    def print_customers(self, dt: float, period_s: int=1):
        self.seconds_since_print += dt

        if self.seconds_since_print >= period_s:
            line_positions = {
                customer_id: position
                for position, customer_id in enumerate(self.state.checkout_line, start=1)
            }

            print("\n--- Store status ---")
            print(" | ".join((
                f"Cash: ${self.state.money / 100:.2f}",
                f"Customers: {len(self.state.customers)}",
                f"Checkout line: {len(self.state.checkout_line)}",
            )))

            if not self.state.customers:
                print("No customers in the store.")

            for customer in self.state.customers:
                state = customer.state.name.replace("_", " ").title()
                basket_total = sum(item.price for item in customer.basket.items)
                details = (
                    f"next item: {max(0, customer.seconds_until_next_item):.1f}s"
                    if customer.state == CustomerState.SHOPPING
                    else f"line position: {line_positions.get(customer.uuid, '-')}"
                )

                print(" | ".join((
                    f"{customer.uuid[:3]}",
                    f"{customer.name:<6}",
                    f"{state:<15}",
                    f"patience: {customer.patience:>5.1f}s",
                    f"basket: {len(customer.basket.items)}/{customer.target_item_count} (${basket_total / 100:.2f})",
                    details,
                )))

            self.seconds_since_print = 0

    def checkout(self):
        """
        todo: Catch-up spawns lose the entire blocked checkout duration and may leave immediately.
        """
        if  len(self.state.checkout_line) == 0:
            return

        customer_id = self.state.checkout_line.popleft()
        customer = next(c for c in self.state.customers if c.uuid == customer_id)
        customer.state = CustomerState.CHECKING_OUT
        self.events.emit("checkout_started", customer=customer) # emit after state update

        player_total = -999
        total = sum(item.price for item in customer.basket.items)

        print("=*"*20 + "=")
        print(f'Cash: {self.state.money/100:.2f}\n')
        print(f'{customer.name} - {customer.description}')
        print('='*20)

        while True:  # emulate do-while
            # todo: in future, need to handle if customer patience runs out during checkout
            print(f'\nPatience: {customer.patience:.1f}')
            print("Basket:")
            for item in customer.basket.items:
                print(f"\t{item.name}\t${item.price / 100:.2f}")
            try:
                player_total = float(input("\nTotal: $"))
                player_total = round(player_total*100, 0)
                if player_total == total:
                    self.state.money += total
                    self.events.emit("sale_completed", customer=customer, total=total)
                    break
                else:
                    self.events.emit("incorrect_total", customer=customer)
            except ValueError as _:
                self.events.emit("incorrect_total", customer=customer)

            if customer.patience <= 0:
                self.events.emit("customer_patience_expired", customer=customer)
                break
        self.state.customers.remove(customer)



    def advance_state(self, dt: float):
        self.print_customers(dt)

if __name__ == "__main__":
    GameManager().loop()
