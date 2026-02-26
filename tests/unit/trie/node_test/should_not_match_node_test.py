from dispytch.dispatcher.trie import TrieNode


def test_get_nonexistent_key_returns_empty_list():
    node = TrieNode()
    node.insert(("foo", "bar"), "handler")

    result = node.get(("nope", "nah"))
    assert result == []


def test_partial_match_does_not_return_handler():
    node = TrieNode()
    node.insert(("foo", "bar", "baz"), "handler")

    result = node.get(("foo", "bar"))
    assert result == []


def test_partial_wildcard_match_does_not_return_handler():
    node = TrieNode()
    node.insert(("foo", "*", "baz"), "handler")

    result = node.get(("foo", "bar"))
    assert result == []


def test_redundant_wildcard_does_not_return_handler():
    node = TrieNode()
    node.insert(("foo", "*", "*"), "handler")

    result = node.get(("foo", "bar"))
    assert result == []
