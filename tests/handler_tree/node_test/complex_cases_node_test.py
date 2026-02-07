from dispytch.listener.handler_tree import HandlerNode


def test_overlapping_wildcards():
    node = HandlerNode()
    node.insert(("*", "bar"), "wildcard_1")
    node.insert(("foo", "*"), "wildcard_2")
    node.insert(("foo", "bar"), "exact")

    result = node.get(("foo", "bar"))
    assert set(result) == {"wildcard_1", "wildcard_2", "exact"}


def test_shared_prefixes():
    node = HandlerNode()
    # should match
    node.insert(("a", "b", "c"), "abc")
    node.insert(("a", "*", "c"), "a_wc")
    node.insert(("*", "b", "*"), "w_b_w")

    # shouldn't match
    node.insert(("*", "*", "a"), "1")
    node.insert(("a", "c", "*"), "2")
    node.insert(("b", "*", "c"), "3")

    result = node.get(("a", "b", "c"))
    assert set(result) == {"abc", "a_wc", "w_b_w"}


def test_direct_wildcard_access():
    node = HandlerNode()
    node.insert(("*", "bar"), "wildcard_1")

    result = node.get(("*", "bar"))
    assert set(result) == {"wildcard_1"}
