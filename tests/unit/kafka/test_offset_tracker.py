import pytest
from dispytch.kafka.offset_tracker import OffsetManager


def test_initial_state():
    om = OffsetManager(starting_offset=100)
    assert om.next_expected_offset == 100
    assert om.last_committed == 99
    assert len(om.completed_pool) == 0


def test_sequential_processing():
    om = OffsetManager(starting_offset=100)

    assert om.mark_processed(100) == 100
    assert om.next_expected_offset == 101
    assert om.last_committed == 100

    assert om.mark_processed(101) == 101
    assert om.next_expected_offset == 102
    assert om.last_committed == 101


def test_out_of_order_processing():
    om = OffsetManager(starting_offset=100)

    # Gap: 100 is missing, but 101 arrives
    assert om.mark_processed(101) is None
    assert om.next_expected_offset == 100
    assert om.last_committed == 99
    assert 101 in om.completed_pool

    # Another out of order
    assert om.mark_processed(103) is None
    assert om.next_expected_offset == 100
    assert 101 in om.completed_pool
    assert 103 in om.completed_pool


def test_filling_gap():
    om = OffsetManager(starting_offset=100)
    om.mark_processed(101)
    om.mark_processed(102)

    # Now fill the gap
    assert om.mark_processed(100) == 102
    assert om.next_expected_offset == 103
    assert om.last_committed == 102
    assert len(om.completed_pool) == 0


def test_duplicate_processing():
    om = OffsetManager(starting_offset=100)

    # First time
    assert om.mark_processed(100) == 100
    # Second time for same offset

    assert om.mark_processed(100) is None
    assert om.next_expected_offset == 101
    assert 100 not in om.completed_pool


def test_complex_scenario():
    om = OffsetManager(starting_offset=0)

    # Process 1, 3, 4
    om.mark_processed(1)
    om.mark_processed(3)
    om.mark_processed(4)

    assert om.last_committed == -1

    # Process 0 -> should commit up to 1
    assert om.mark_processed(0) == 1
    assert om.last_committed == 1
    assert om.next_expected_offset == 2

    # Process 2 -> should commit up to 4
    assert om.mark_processed(2) == 4
    assert om.last_committed == 4
    assert om.next_expected_offset == 5
    assert len(om.completed_pool) == 0


def test_duplicate_processing_revisit():
    om = OffsetManager(starting_offset=100)

    # Process 100
    assert om.mark_processed(100) == 100
    assert om.next_expected_offset == 101

    # Process 100 again (duplicate)
    assert om.mark_processed(100) is None
    assert 100 not in om.completed_pool

    # Process 102 (gap)
    assert om.mark_processed(102) is None
    assert 102 in om.completed_pool

    assert om.mark_processed(101) == 102
    assert 100 not in om.completed_pool
