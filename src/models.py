from enum import Enum, auto
import random
from dataclasses import dataclass
from uuid import uuid4

class CustomerState(Enum):
    WAITING_IN_LINE = auto()
    CHECKING_OUT = auto()
    # SHOPPING = auto()


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
    basket: Basket
    name: str
    description: str
    patience: float
    state: CustomerState

@dataclass
class GameState:
    customers: list[Customer]
    money: int
