from src.events import EventBus
from src.models import CheckoutSystemState, Customer, CustomerState, GameState


class CheckoutSystem:
    def __init__(self, events: EventBus, state: GameState) -> None:
        self.current_customer_id = None
        self.checkout_state = CheckoutSystemState.WAITING_FOR_CUSTOMER
        self.state = state
        self.events = events
        self.events.subscribe("customer_left", self._handle_customer_left)

    def update(self, dt: float) -> None:
        if (
            self.checkout_state == CheckoutSystemState.WAITING_FOR_CUSTOMER
            and len(self.state.checkout_line) > 0
        ):
            self.current_customer_id = self.state.checkout_line.popleft()
            customer = next(
                c for c in self.state.customers if c.uuid == self.current_customer_id
            )

            self.checkout_state = CheckoutSystemState.ENTERING_TOTAL
            customer.state = CustomerState.CHECKING_OUT
            self.events.emit("checkout_started", customer=customer)

        if self.checkout_state == CheckoutSystemState.ENTERING_TOTAL:
            customer = next(
                c for c in self.state.customers if c.uuid == self.current_customer_id
            )
            player_total = -999
            total = sum(item.price for item in customer.basket.items)

            print("=*" * 20 + "=")
            print(f"Cash: {self.state.money / 100:.2f}\n")
            print(f"{customer.name} - {customer.description}")
            print("=" * 20)

            print(f"\nPatience: {customer.patience:.1f}")
            print("Basket:")
            for item in customer.basket.items:
                print(f"\t{item.name}\t${item.price / 100:.2f}")
            try:
                player_total = float(input("\nTotal: $"))
                player_total = round(player_total * 100, 0)
                if player_total == total:
                    self.state.money += total
                    self.events.emit("sale_completed", customer=customer, total=total)
                    return
                else:
                    self.events.emit("incorrect_total", customer=customer)
            except ValueError as _:
                self.events.emit("incorrect_total", customer=customer)

    def _handle_customer_left(self, customer: Customer) -> None:
        if customer.uuid == self.current_customer_id:
            self._reset_state()

    def _reset_state(self):
        self.checkout_state = CheckoutSystemState.WAITING_FOR_CUSTOMER
        self.current_customer_id = None
