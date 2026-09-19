from collections.abc import Callable

from src.models import Command

Handler = Callable[[Command], bool]


class CommandDispatcher:
    def __init__(self):
        self.handlers: dict[type[Command], Handler] = {}

    def register(self, command_type: type[Command], callback: Handler):
        if command_type in self.handlers:
            raise ValueError(
                f"Command {command_type} already registered to handler {self.handlers[command_type]}"
            )
        self.handlers[command_type] = callback

    def dispatch(self, command: Command):
        callback = self.handlers[type(command)]
        return callback(command)
