from collections import defaultdict

from dispytch.listener.handler import Handler


class HandlerNode:
    def __init__(self):
        self.handlers: list[Handler] = []
        self.children: dict[str, HandlerNode] = defaultdict(HandlerNode)

    def insert(self, key: tuple[str, ...], *handlers: Handler):
        if len(key) == 0:
            self.handlers.extend(handlers)
            return

        self.children[key[0]].insert(key[1:], *handlers)

    def get(self, key: tuple[str, ...]) -> list[Handler]:
        if len(key) == 0:
            return self.handlers

        handlers = []

        # These checks prevent creating a new Node for every non-existing key.
        # Without them, we could end up generating a huge number of redundant objects, potentially exhausting memory.
        if key[0] in self.children:
            handlers += self.children[key[0]].get(key[1:])

        if "*" in self.children:
            handlers += self.children["*"].get(key[1:])

        return handlers
