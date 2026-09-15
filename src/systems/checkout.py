from src.events import EventBus
from src.models import CheckoutSystemState, Customer, CustomerState, GameState


class CheckoutSystem:
    def __init__(self, events: EventBus, state: GameState) -> None:
        self.current_customer_id = None
        self.checkout_state = CheckoutSystemState.WAITING_FOR_CUSTOMER
        self.state = state
        self.events = events
        self.events.subscribe("customer_left", self._handle_customer_left)

    def update(self, dt: float, player_input: str | None) -> None:
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
            self._update_enter_total_state(player_input)

    def _update_enter_total_state(self, player_input: str | None):
        if not player_input:
            return

        customer = next(
            c for c in self.state.customers if c.uuid == self.current_customer_id
        )
        total = sum(item.price for item in customer.basket.items)
        try:
            player_total = float(player_input)
            player_total = round(player_total * 100, 0)
            if player_total == total:
                self.state.money += total
                self.events.emit("sale_completed", customer=customer, total=total)
                self._reset_state()
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
