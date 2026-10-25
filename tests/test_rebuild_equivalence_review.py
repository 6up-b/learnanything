"""Codex review of the rebuild-equivalence fix (2026-10-25).

* **F1**: a direct per-LO replay (integration backfill, regrade's replay)
  publishes nothing until it has finished: no historical prefix of the
  vault-wide canonical cache, no reset LO, no reopened retired item is ever
  visible to another connection, and an interrupted replay leaves live state
  exactly as it was, so a retry starts from the right lifecycle.
* **F3**: a rebuild completes the recurrence reconciliation its own learner
  replay made necessary, so the rebuild right after it changes nothing.
* **F4**: the bounded replay is the successor ``REPLAY_LEDGER_ALGORITHM_VERSION``
  behind ``replay.ledger_bounded``; below it (or switched off) replay is
  the predecessor's, byte for byte.
* **F2** (rejected, out of scope): the same-second reverse-completion case is
  pinned as a strict xfail so its fix is noticed.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.clock import FrozenClock
from learnloop.content.authoring.item_authoring import retire_item
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.substrate import replay as replay_module
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import NOW, add_followup_item, create_placement_vault
from tests.test_rebuild_equivalence import _answer, _at

#: The vault-wide and per-LO state a direct replay rewrites.
DERIVED = (
    "learning_object_mastery", "facet_recall_state", "facet_capability_evidence",
    "practice_item_state", "practice_item_quality_state", "attempt_surprise",
    "unresolved_cause_factors",
)


def _read(paths) -> dict[str, list[tuple]]:
    """What another connection sees (a fresh read-only connection)."""

    with connect(paths.sqlite_path, read_only=True) as connection:
        return {
            table: sorted(tuple(row) for row in connection.execute(f'SELECT * FROM "{table}"'))
            for table in DERIVED
        }


def _declare_integration(paths) -> None:
    """Give lo_svd_definition a conjunctive recipe with an integration cell,
    so the integration backfill has a verdict to apply (and replays it)."""

    path = paths.learning_object_path("linear-algebra", "lo_svd_definition")
    payload = read_yaml(path)
    payload["blueprints"] = [{
        "id": "bp_svd", "weight": 1.0,
        "recipes": [{
            "id": "recipe_svd", "composition": "conjunctive",
            "all_of": [
                {"facet": "recall", "capability": "retrieval", "modality": "hard"},
                {"facet": "apply_it", "capability": "procedure_execution", "modality": "hard"},
            ],
            "integration": {"facet": "recall", "capability": "coordination", "modality": "hard"},
        }],
    }]
    write_yaml(path, payload)


def _history(tmp_path):
    """Interleaved attempts on two LOs, then a retirement and a primary load:
    a bounded fold through the first svd attempt would drop lo_diag's later
    evidence from the vault-wide cache, and the retired item is inactive."""

    paths = create_placement_vault(tmp_path / "vault", version=LATEST_ALGORITHM_VERSION)
    add_followup_item(paths.root)
    _declare_integration(paths)
    repository = Repository(paths.sqlite_path)
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=_at(0))
    _answer(vault, repository, "pi_svd_define_002", minutes=1, points=1.0)
    _answer(vault, repository, "pi_diag_easy", minutes=2, points=3.0)
    _answer(vault, repository, "pi_svd_define_001", minutes=3, points=2.0)
    _answer(vault, repository, "pi_diag_mid", minutes=4, points=0.0)
    retire_item(paths.root, repository, practice_item_id="pi_svd_define_002", reason="duplicate_surface",
                clock=_at(5))
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=_at(6))
    assert repository.practice_item_state("pi_svd_define_002").active is False
    return paths, vault, repository


def _inject(monkeypatch, paths, *, fail_on: int):
    """Wrap replay's per-attempt step: before attempt ``fail_on`` replays,
    read the database from another connection, then raise."""

    real = replay_module.replay_existing_attempt
    seen: list[dict[str, list[tuple]]] = []
    calls = {"n": 0}

    def step(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == fail_on:
            seen.append(_read(paths))
            raise RuntimeError("injected replay failure")
        return real(*args, **kwargs)

    monkeypatch.setattr(replay_module, "replay_existing_attempt", step)
    return seen


@pytest.mark.durability
def test_an_interrupted_integration_backfill_replay_publishes_nothing(tmp_path, monkeypatch):
    """F1 through a direct production caller: the backfill replays the LO
    outside any umbrella transaction."""

    from learnloop.curriculum.integration_backfill import (
        COORDINATION,
        apply_integration_backfill_and_recalibrate,
        plan_integration_backfill,
    )

    paths, vault, repository = _history(tmp_path)
    before = _read(paths)
    report = plan_integration_backfill(vault, capabilities=[COORDINATION])
    assert report.verdicts, "the fixture must give the backfill a verdict to apply"
    seen = _inject(monkeypatch, paths, fail_on=2)

    with pytest.raises(RuntimeError, match="injected"):
        apply_integration_backfill_and_recalibrate(
            vault, repository, report.verdicts, dry_run=False, clock=FrozenClock(NOW)
        )

    # Mid-replay, another connection read the state as it was: no reset LO,
    # no historical prefix of the canonical cache, no reopened retired item.
    assert seen == [before]
    # And the failure left it so.
    assert _read(paths) == before
    assert repository.practice_item_state("pi_svd_define_002").active is False


@pytest.mark.durability
def test_a_retry_after_an_interrupted_direct_replay_keeps_the_lifecycle(tmp_path, monkeypatch):
    """F1's second half: the inactive flags are read inside the replay's
    transaction, so an interruption cannot leave the retired item active
    for a retry to snapshot."""

    from learnloop.substrate.replay import replay_learning_object

    paths, vault, repository = _history(tmp_path)
    before = _read(paths)
    seen = _inject(monkeypatch, paths, fail_on=2)
    with pytest.raises(RuntimeError, match="injected"):
        replay_learning_object(vault, repository, "lo_svd_definition")
    assert seen == [before]
    assert _read(paths) == before
    monkeypatch.undo()

    replay_learning_object(vault, repository, "lo_svd_definition")
    assert repository.practice_item_state("pi_svd_define_002").active is False


def _answer_at(vault, repository, item_id, *, minutes, points, attempt_id):
    """A self-graded attempt with a chosen id (ids are allocated before
    grading, so the id order need not be the commit order)."""

    import learnloop.attempts.attempts as attempts_module

    real = attempts_module.new_ulid
    pending = [attempt_id]
    attempts_module.new_ulid = lambda: pending.pop() if pending else real()
    try:
        return _answer(vault, repository, item_id, minutes=minutes, points=points)
    finally:
        attempts_module.new_ulid = real


@pytest.mark.xfail(
    strict=True,
    reason=(
        "F2, rejected for this stage: two grades of one LO committed in the same second in reverse id "
        "order replay in (created_at, id) order, not commit order. Pre-existing (replay's fold order); "
        "the fix needs a persisted commit sequence (a migration) and a new ledger order everywhere."
    ),
)
def test_two_same_second_attempts_committed_in_reverse_id_order_rebuild_to_live(tmp_path):
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
    from tests.test_rebuild_equivalence import _mastery, _vault

    paths, vault, repository = _vault(tmp_path)
    # B (the later id) commits first; A (the earlier id) commits in the same second.
    _answer_at(vault, repository, "pi_svd_define_001", minutes=1, points=4.0,
               attempt_id="01ZZZZZZZZZZZZZZZZZZZZZZZB")
    _answer_at(vault, repository, "pi_svd_define_001", minutes=1, points=0.0,
               attempt_id="01ZZZZZZZZZZZZZZZZZZZZZZZA")
    live = _mastery(repository)

    rebuild_all_derived_state(vault, repository)

    assert _mastery(repository) == live
