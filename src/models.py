from collections import deque
from dataclasses import dataclass
from enum import Enum, auto


class CustomerState(Enum):
    WAITING_IN_LINE = auto()
    CHECKING_OUT = auto()
    SHOPPING = auto()


class CheckoutSystemState(Enum):
    WAITING_FOR_CUSTOMER = auto()
    ENTERING_TOTAL = auto()


@dataclass
class Item:
    name: str
    price: int


@dataclass
class Basket:
    items: list[Item]


@dataclass
class Customer:
    uuid: str
    name: str
    description: str
    patience: float
    state: CustomerState

    basket: Basket
    target_item_count: int  # end number of items in their cart
    item_pickup_period: float  # number of seconds between item pickup
    seconds_until_next_item: float


@dataclass
class GameState:
    customers: list[Customer]
    checkout_line: deque[str]
    money: int
    inventory: list[Item]
