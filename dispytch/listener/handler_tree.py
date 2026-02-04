from collections import defaultdict

from dispytch.listener.consumer import EventSubscription
from dispytch.listener.handler import Handler


class HandlerTree:
    def __init__(self):
        self.root: HandlerNode = HandlerNode()

    def insert(self, path: tuple[str, ...], *handlers: tuple[EventSubscription, Handler]):
        segments = tuple(
            '*'
            if (segment.startswith('{') and segment.endswith('}'))
            else segment
            for segment in path
        )

        self.root.insert(segments, *handlers)

    def get(self, key: tuple[str, ...]) -> list[tuple[EventSubscription, Handler]]:
        return self.root.get(key)


class HandlerNode:
    def __init__(self):
        self.handlers: list[tuple[EventSubscription, Handler]] = []
        self.children: dict[str, HandlerNode] = defaultdict(HandlerNode)

    def insert(self, key: tuple[str, ...], *handlers: tuple[EventSubscription, Handler]):
        if len(key) == 0:
            self.handlers.extend(handlers)
            return

        self.children[key[0]].insert(key[1:], *handlers)

    def get(self, key: tuple[str, ...]) -> list[tuple[EventSubscription, Handler]]:
        if len(key) == 0:
            return self.handlers

        handlers = []

        # These checks prevent creating a new Node for every non-existing key.
        # Without them, we could end up generating a huge number of redundant objects, potentially exhausting memory.
        if key[0] in self.children:
            handlers += self.children[key[0]].get(key[1:])

        if key[0] != "*" and "*" in self.children:
            handlers += self.children["*"].get(key[1:])

        return handlers
