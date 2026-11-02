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


def test_new_ulid_after_sorts_after_a_floor_persisted_by_a_process_whose_clock_ran_ahead(wall_clock, monkeypatch):
    """Codex review F2 (followups-nov1c): process A mints an id an hour ahead and stores it;
    process B (fresh generator state, the corrected clock) must still mint above it, and two
    processes lifted to the same floor never mint the same id."""

    wall_clock["ms"] += 3_600_000
    stored = ids.new_ulid()  # process A, clock ahead
    wall_clock["ms"] -= 3_600_000
    minted = []
    for _process in range(2):  # two fresh processes reading the same stored floor
        monkeypatch.setattr(ids, "_last_timestamp_ms", -1)
        monkeypatch.setattr(ids, "_last_randomness", 0)
        assert ids.new_ulid() < stored  # plain process-local monotonicity cannot order them
        first = ids.new_ulid_after(stored)
        assert first > stored and ids.new_ulid() > first  # and later ids stay above it
        minted.append(first)
    assert minted[0] != minted[1]


def test_new_ulid_after_ignores_a_floor_that_is_not_a_ulid_or_is_behind(wall_clock):
    behind = ids.new_ulid()
    latest = ids.new_ulid()
    assert ids.new_ulid_after(behind) > latest
    for floor in ("", None, "not-a-ulid", "Z" * 26):
        assert ids.new_ulid_after(floor) > latest
