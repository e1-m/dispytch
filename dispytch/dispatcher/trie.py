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

    def get(self, key: tuple[str, ...], override_wildcard: bool = False) -> list[T]:
        """
         :param override_wildcard: If True, returns the most exact match. If False, returns all matches.
         :param key: A tuple of key segments
        """
        return self.root.get(key, override_wildcard)


class TrieNode[T]:
    def __init__(self):
        self.values: list[T] = []
        self.children: dict[str, TrieNode] = defaultdict(TrieNode)

    def insert(self, key: tuple[str, ...], value: T):
        if len(key) == 0:
            self.values.append(value)
            return

        self.children[key[0]].insert(key[1:], value)

    def get(self, key: tuple[str, ...], override_wildcard: bool = False) -> list[T]:
        if len(key) == 0:
            return self.values

        values = []

        # These checks prevent creating a new Node for every non-existing key.
        # Without them, we could end up generating a huge number of redundant objects, potentially exhausting memory.
        if key[0] in self.children:
            values += self.children[key[0]].get(key[1:], override_wildcard)

        if not override_wildcard or (override_wildcard and key[0] not in self.children):
            if key[0] != "*" and "*" in self.children:
                values += self.children["*"].get(key[1:], override_wildcard)

        return values
