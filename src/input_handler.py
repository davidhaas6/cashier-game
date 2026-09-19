import sys
from queue import Queue

from src.events import EventBus


def read(queue: Queue, events: EventBus):
    while True:  # todo: make this more interruptable
        text = sys.stdin.readline()
        if text:
            queue.put(text)
