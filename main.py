import time

from src.events import EventBus
from src.models import Customer, CustomerState, GameState
from src.systems import CustomerSystem, SpawnSystem


class GameManager:
    def __init__(self) -> None:
        self.events: EventBus = EventBus()
        self.state: GameState = GameState(customers=[], money=0)
        self.spawner: SpawnSystem = SpawnSystem(self.events, self.state, 3)
        self.customer_system: CustomerSystem = CustomerSystem(self.events, self.state)
        self.seconds_since_print: float = 0
        self.init_event_system()

    def loop(self):
        TICK_RATE_HZ = 30

        last_time = time.perf_counter()
        while True:
            start = time.perf_counter()

            dt_seconds = start - last_time
            last_time = start

            # use .update for continuous responsibilities and events for discrete moments/reactions
            self.spawner.update(dt_seconds)
            self.customer_system.update(dt_seconds)
            self.advance_state(dt_seconds)

            if len(self.state.customers) > 0:
                self.checkout()

            duration_s = time.perf_counter() - start
            time.sleep(max(0, 1 / TICK_RATE_HZ - duration_s))


    def init_event_system(self):
        self.events.subscribe("checkout_started", lambda customer: print(f"{customer.name}'s checkout started."))
        self.events.subscribe("incorrect_total", lambda: print("Register total rejected."))
        self.events.subscribe("sale_completed", lambda customer, total: print(f"{customer.name} paid ${total/100:.2f}"))
        self.events.subscribe("customer_patience_expired", lambda customer: print(f"{customer.name} left."))

    def print_customers(self, dt: float, period_s: int=1):
        self.seconds_since_print += dt

        if self.seconds_since_print >= period_s:
            print([(c.uuid[:3],round(c.patience,2)) for c in self.state.customers])
            self.seconds_since_print = 0

    def checkout(self):
        """
        Catch-up spawns lose the entire blocked checkout duration and may leave immediately.
        """
        if len(self.state.customers) == 0:
            return

        customer = self.state.customers[0]
        customer.state = CustomerState.CHECKING_OUT
        self.events.emit("checkout_started", customer=customer) # emit after state update

        player_total = -999
        total = sum(item.price for item in customer.basket.items)

        def incorrect_total():
            customer.patience -= 0.5
            self.events.emit("incorrect_total")

        print('\n')
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
                    incorrect_total()
            except ValueError as _:
                incorrect_total()

            if customer.patience <= 0:
                self.events.emit("customer_patience_expired", customer=customer)
                break
        self.state.customers.remove(customer)



    def advance_state(self, dt: float):
        self.print_customers(dt)

if __name__ == "__main__":
    GameManager().loop()
