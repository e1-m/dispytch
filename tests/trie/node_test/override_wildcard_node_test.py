from dispytch.listener.trie import TrieNode


def test_node_override_wildcard_true_exact_match_found():
    node = TrieNode()
    h_exact = "exact"
    h_wildcard = "wildcard"

    node.insert(("foo",), h_exact)
    node.insert(("*",), h_wildcard)

    assert node.get(("foo",), override_wildcard=True) == [h_exact]


def test_node_override_wildcard_true_no_exact_match():
    node = TrieNode()
    h_wildcard = "wildcard"

    node.insert(("*",), h_wildcard)

    assert node.get(("foo",), override_wildcard=True) == [h_wildcard]


def test_node_override_wildcard_false_returns_both():
    node = TrieNode()
    h_exact = "exact"
    h_wildcard = "wildcard"

    node.insert(("foo",), h_exact)
    node.insert(("*",), h_wildcard)

    result = node.get(("foo",), override_wildcard=False)
    assert set(result) == {h_exact, h_wildcard}


def test_node_override_wildcard_recursive():
    root = TrieNode()
    # level 1 exact, level 2 wildcard
    # level 1 wildcard, level 2 exact

    h1 = "h1"  # foo:bar
    h2 = "h2"  # foo:*
    h3 = "h3"  # *:bar
    h4 = "h4"  # *:*

    root.insert(("foo", "bar"), h1)
    root.insert(("foo", "*"), h2)
    root.insert(("*", "bar"), h3)
    root.insert(("*", "*"), h4)

    # override_wildcard=True should only return h1 for ("foo", "bar")
    assert root.get(("foo", "bar"), override_wildcard=True) == [h1]

    # For ("foo", "other"), should return h2
    assert root.get(("foo", "other"), override_wildcard=True) == [h2]

    # For ("other", "bar"), should return h3
    assert root.get(("other", "bar"), override_wildcard=True) == [h3]

    # For ("other", "other"), should return h4
    assert root.get(("other", "other"), override_wildcard=True) == [h4]

    # For ("*", "*"), should return h4
    assert root.get(("*", "*"), override_wildcard=True) == [h4]

    # For ("*", "other"), should return h4
    assert root.get(("*", "other"), override_wildcard=True) == [h4]
