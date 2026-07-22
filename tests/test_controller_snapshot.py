"""P4 step 1 -- ControllerSnapshot determinism, hash stability, bounded reads, and
no cold-answer leakage (spec_p4 §3.1, §16.10; design §F)."""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services import controller_snapshot as cs
from learnloop.services import controller_store as store
from learnloop.services.scheduler import SchedulerSession
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault, seed_due_item

CLOCK = FrozenClock(NOW)


@pytest.fixture
def wired(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    vault = load_vault(root)
    repo = Repository(paths.sqlite_path)
    sync_vault_state(vault, repo, clock=CLOCK)
    seed_due_item(paths)
    return vault, repo


def _session():
    return SchedulerSession(session_id="s1", available_minutes=15)


def test_snapshot_is_deterministic_and_hash_stable(wired):
    vault, repo = wired
    a = cs.build_snapshot(vault, repo, _session(), clock=CLOCK)
    b = cs.build_snapshot(vault, repo, _session(), clock=CLOCK)
    assert a.snapshot_hash == b.snapshot_hash
    assert isinstance(a.snapshot_hash, str) and len(a.snapshot_hash) == 32


def test_snapshot_persists_deduped_on_content_hash(wired):
    vault, repo = wired
    snap = cs.build_snapshot(vault, repo, _session(), clock=CLOCK)
    id1 = cs.persist_snapshot(repo, snap, clock=CLOCK)
    id2 = cs.persist_snapshot(repo, snap, clock=CLOCK)
    assert id1 == id2  # identical content reuses one immutable row
    row = store.snapshot_row(repo, id1)
    assert row["snapshot_hash"] == snap.snapshot_hash


def test_snapshot_construction_is_bounded_no_per_candidate_query(wired):
    """§3.1 operability bar: the read count is independent of candidate count."""

    vault, repo = wired

    calls = {"n": 0}
    original = repo.connection

    def counting_connection():
        calls["n"] += 1
        return original()

    small = [cs.Candidate(candidate_ref=f"c{i}") for i in range(2)]
    large = [cs.Candidate(candidate_ref=f"c{i}") for i in range(40)]

    repo.connection = counting_connection  # type: ignore[assignment]
    try:
        calls["n"] = 0
        cs.build_snapshot(vault, repo, _session(), candidates=small, clock=CLOCK)
        small_reads = calls["n"]
        calls["n"] = 0
        cs.build_snapshot(vault, repo, _session(), candidates=large, clock=CLOCK)
        large_reads = calls["n"]
    finally:
        repo.connection = original  # type: ignore[assignment]

    assert small_reads == large_reads  # no query per candidate
    assert large_reads <= 6  # a small fixed set of bulk reads


def test_snapshot_contains_no_cold_answer_material(wired):
    vault, repo = wired
    snap = cs.build_snapshot(vault, repo, _session(), clock=CLOCK)
    import json

    serialized = json.dumps({
        "candidates": [c.hashable() for c in snap.candidates],
        "commitments": [c.hashable() for c in snap.commitments],
        "projection_versions": dict(snap.projection_versions),
    })
    # A practice item's expected answer / prompt text must never enter the snapshot.
    for item in vault.practice_items.values():
        answer = item.expected_answer
        if isinstance(answer, str) and answer:
            assert answer not in serialized
        assert item.prompt not in serialized


def test_reserved_assessment_surfaces_load_into_snapshot(wired):
    vault, repo = wired
    snap = cs.build_snapshot(vault, repo, _session(), clock=CLOCK)
    assert isinstance(snap.reserved_assessment_surface_ids, frozenset)
    assert snap.remaining_minutes == 15.0
