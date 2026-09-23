from __future__ import annotations

import pytest

from learnloop import ids


@pytest.fixture
def wall_clock(monkeypatch):
    """Drive new_ulid's millisecond clock and restore the generator state afterwards."""

    monkeypatch.setattr(ids, "_last_timestamp_ms", -1)
    monkeypatch.setattr(ids, "_last_randomness", 0)
    current = {"ms": 1_700_000_000_123}
    monkeypatch.setattr(ids, "_wall_clock_ms", lambda: current["ms"])
    return current


def test_ulids_minted_in_one_millisecond_sort_in_creation_order(wall_clock):
    minted = [ids.new_ulid() for _ in range(200)]
    assert minted == sorted(minted)
    assert len(set(minted)) == len(minted)
    assert {value[:10] for value in minted} == {minted[0][:10]}


def test_ulids_stay_ordered_when_the_wall_clock_steps_backwards(wall_clock):
    first = ids.new_ulid()
    wall_clock["ms"] -= 400
    second = ids.new_ulid()
    assert first < second


def test_ulid_moves_to_the_next_millisecond_when_randomness_is_exhausted(wall_clock, monkeypatch):
    ids.new_ulid()
    monkeypatch.setattr(ids, "_last_randomness", ids._RANDOMNESS_MAX)
    following = ids.new_ulid()
    assert following[:10] == ids._encode_crockford(wall_clock["ms"] + 1, 10)


def test_a_new_millisecond_restarts_from_fresh_randomness(wall_clock, monkeypatch):
    ids.new_ulid()
    wall_clock["ms"] += 1
    monkeypatch.setattr(ids.secrets, "randbits", lambda bits: 7)
    following = ids.new_ulid()
    assert following == ids._encode_crockford(wall_clock["ms"], 10) + ids._encode_crockford(7, 16)
