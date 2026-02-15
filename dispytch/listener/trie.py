from collections import defaultdict


class Trie[T]:
    def __init__(self):
        self.root: TrieNode = TrieNode()

    def insert(self, key: tuple[str, ...], value: T):
        segments = tuple(
            '*'
            if (segment.startswith('{') and segment.endswith('}'))
            else segment
            for segment in key
        )

        self.root.insert(segments, value)

    def get(self, key: tuple[str, ...]) -> list[T]:
        return self.root.get(key)


class TrieNode[T]:
    def __init__(self):
        self.values: list[T] = []
        self.children: dict[str, TrieNode] = defaultdict(TrieNode)

    def insert(self, key: tuple[str, ...], value: T):
        if len(key) == 0:
            self.values.append(value)
            return

        self.children[key[0]].insert(key[1:], value)

    def get(self, key: tuple[str, ...]) -> list[T]:
        if len(key) == 0:
            return self.values

        values = []

        # These checks prevent creating a new Node for every non-existing key.
        # Without them, we could end up generating a huge number of redundant objects, potentially exhausting memory.
        if key[0] in self.children:
            values += self.children[key[0]].get(key[1:])

        if key[0] != "*" and "*" in self.children:
            values += self.children["*"].get(key[1:])

        return values
