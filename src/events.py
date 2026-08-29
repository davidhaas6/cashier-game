from collections import defaultdict
from typing import Any
from collections.abc import Callable

Listener = Callable[..., None]

class EventBus:
    def __init__(self):
        self.listeners: dict[str, list[Listener]] = defaultdict(list)

    def subscribe(self, event_name: str, callback: Listener):
        self.listeners[event_name].append(callback)

    def emit(self, event_name: str, **data: Any):
        for callback in self.listeners[event_name]:
            callback(**data)
            print(f"{event_name} - {callback}")
