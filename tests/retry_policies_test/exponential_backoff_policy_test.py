import random

import pytest

from dispytch.middleware.retry import ExponentialBackoffWithFullJitter


def test_should_retry_when_retry_on_is_none_retries_on_any_exception():
    policy = ExponentialBackoffWithFullJitter(retries=3, retry_on=None)

    assert policy.should_retry(attempt=0, error=ValueError()) is True
    assert policy.should_retry(attempt=1, error=KeyError()) is True
    assert policy.should_retry(attempt=2, error=RuntimeError()) is True
    assert policy.should_retry(attempt=3, error=Exception()) is False


def test_should_retry_filters_by_exception_type():
    policy = ExponentialBackoffWithFullJitter(retries=5, retry_on=[ValueError])

    assert policy.should_retry(attempt=0, error=ValueError()) is True
    assert policy.should_retry(attempt=0, error=KeyError()) is False


def test_should_retry_accepts_subclasses_of_retry_on():
    class CustomValueError(ValueError):
        pass

    policy = ExponentialBackoffWithFullJitter(retries=2, retry_on=[ValueError])

    assert policy.should_retry(attempt=0, error=CustomValueError()) is True
    assert policy.should_retry(attempt=2, error=CustomValueError()) is False


def test_retries_is_abs_value():
    policy = ExponentialBackoffWithFullJitter(retries=-2, retry_on=None)

    assert policy.should_retry(attempt=0, error=Exception()) is True
    assert policy.should_retry(attempt=1, error=Exception()) is True
    assert policy.should_retry(attempt=2, error=Exception()) is False


def test_get_delay_uses_exponential_backoff_and_passes_bound_to_jitter(monkeypatch):
    calls = []

    def fake_uniform(a, b):
        calls.append((a, b))
        return b  # deterministic: always return upper bound

    monkeypatch.setattr(random, "uniform", fake_uniform)

    policy = ExponentialBackoffWithFullJitter(retries=3, base_delay_sec=1.0, max_delay_sec=30.0)

    assert policy.get_delay(attempt=0, prev_delay=0.0) == 1.0
    assert policy.get_delay(attempt=1, prev_delay=999.0) == 2.0
    assert policy.get_delay(attempt=2, prev_delay=999.0) == 4.0

    assert calls == [(0, 1.0), (0, 2.0), (0, 4.0)]


def test_get_delay_is_capped_by_max_delay(monkeypatch):
    monkeypatch.setattr(random, "uniform", lambda a, b: b)  # always return upper bound

    policy = ExponentialBackoffWithFullJitter(retries=10, base_delay_sec=10.0, max_delay_sec=30.0)

    # attempt=0 => min(30, 10) = 10
    assert policy.get_delay(attempt=0, prev_delay=0.0) == 10.0

    # attempt=2 => min(30, 40) = 30
    assert policy.get_delay(attempt=2, prev_delay=0.0) == 30.0

    # higher attempts stay capped at max_delay
    assert policy.get_delay(attempt=10, prev_delay=0.0) == 30.0


def test_base_delay_is_never_negative(monkeypatch):
    # If base delay is negative, it is normalized to 0.0, so computed delay is 0 for any attempt.
    monkeypatch.setattr(random, "uniform", lambda a, b: b)

    policy = ExponentialBackoffWithFullJitter(retries=3, base_delay_sec=-123.0, max_delay_sec=30.0)

    assert policy.get_delay(attempt=0, prev_delay=0.0) == 0.0
    assert policy.get_delay(attempt=5, prev_delay=0.0) == 0.0
