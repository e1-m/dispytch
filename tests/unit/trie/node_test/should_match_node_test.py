from dispytch.dispatcher.trie import TrieNode


def test_get_empty_key_returns_root_handlers():
    node = TrieNode()
    handler = "root_handler"
    node.insert((), handler)

    result = node.get(())
    assert result == [handler]


def test_insert_and_get_exact_match():
    node = TrieNode()
    handler = "handler1"
    node.insert(("foo",), handler)

    result = node.get(("foo",))
    assert result == [handler]


def test_wildcard():
    node = TrieNode()
    node.insert(("*",), "wildcard")
    assert node.get(("anything",)) == ["wildcard"]


def test_two_wildcards_only():
    node = TrieNode()
    handler = "fallback"
    node.insert(("*", "*"), handler)

    result = node.get(("something", "else"))
    assert result == [handler]


def test_wildcard_handler_matches_any_segment():
    node = TrieNode()
    handler = "wildcard"
    node.insert(("foo", "*", "baz"), handler)

    result = node.get(("foo", "bar", "baz"))
    assert result == [handler]


def test_multiple_handlers_same_key():
    node = TrieNode()
    node.insert(("foo", "bar"), "h1")
    node.insert(("foo", "bar"), "h2")

    result = node.get(("foo", "bar"))
    assert result == ["h1", "h2"]
