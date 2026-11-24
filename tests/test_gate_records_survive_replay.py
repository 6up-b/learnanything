"""The follow-up gate's records survive every replay.

The live gate writes its decision onto the attempt's surprise row after the grade: the actions it queued
(``triggered_actions_json``), the ones it held back (``suppressed_actions_json``) and what it read and scored
(``gate_diagnostics_json``). Replay never runs the gate, so these are carried across every replay of the row by attempt
id: the whole-vault rebuild, a per-LO replay and a regrade's replay. What history shows from them (the attempt's
feedback and detail, the "answered the follow-up from" link the rating path uses, the session's follow-up count and
the scheduler's legacy pending list) reads the same after a rebuild as before, and the shadow rebuild compares them.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.replay import replay_learning_object
from learnloop.vault.loader import load_vault

from tests import pinned_draws
from tests.diagnosis_journey_helpers import CASES, freeze_ids, freeze_wall, pin_journey_draws, run_case
from tests.helpers import NOW

GATE_COLUMNS = ("triggered_actions_json", "suppressed_actions_json", "gate_diagnostics_json")


def _journey(case: str, root: Path):
    with pytest.MonkeyPatch.context() as patch:
        freeze_wall(patch)
        freeze_ids(patch, 104)
        pin_journey_draws(patch, case)
        pushed = pinned_draws.push(f"diagnosis-journey:{case}")
        try:
            journey = run_case(case, root, patch)
        finally:
            if pushed:
                pinned_draws.pop()
    repository = journey.repository
    vault_root = next(p for p in Path(repository.sqlite_path).resolve().parents if (p / "learnloop.toml").exists())
    return vault_root, repository


def _records(repository) -> dict[str, tuple]:
    with repository.connection() as connection:
        return {str(row[0]): tuple(row[1:]) for row in connection.execute(
            f"SELECT attempt_id, {', '.join(GATE_COLUMNS)} FROM attempt_surprise ORDER BY attempt_id")}


def _recorded(records: dict[str, tuple]) -> dict[str, tuple]:
    """The rows the gate wrote something on (anything but the grade's own empty values)."""

    return {k: v for k, v in records.items() if (v[0] not in (None, "[]") or v[1] not in (None, "[]")
                                                 or v[2] not in (None, "null"))}


@pytest.mark.parametrize("case", CASES)
def test_a_whole_vault_rebuild_keeps_the_gates_records(case, tmp_path):
    root, repository = _journey(case, tmp_path)
    before = _records(repository)
    rebuild_all_derived_state(load_vault(root), repository)
    assert _records(repository) == before


def test_the_journeys_hold_gate_records_to_keep(tmp_path):
    root, repository = _journey("recurrence_judge", tmp_path)
    recorded = _recorded(_records(repository))
    assert len(recorded) == 3 and all(row[0] != "[]" and row[2] != "null" for row in recorded.values())


def test_a_per_lo_replay_keeps_them(tmp_path):
    root, repository = _journey("recurrence_judge", tmp_path)
    before = _records(repository)
    vault = load_vault(root)
    for learning_object_id in repository.learning_object_ids_with_attempts():
        replay_learning_object(vault, repository, learning_object_id)
    assert _records(repository) == before and _recorded(before)


def test_a_regrade_keeps_them(tmp_path):
    from tests.regrade_contract_replay_helpers import _regrade

    root, repository = _journey("recurrence_judge", tmp_path)
    before = _records(repository)
    vault = load_vault(root)
    regraded = sorted(_recorded(before))[0]
    _regrade(vault, repository, regraded, {"correctness": 4.0}, when=NOW + timedelta(days=30))
    assert _records(repository) == before


def test_what_history_shows_reads_the_same_after_a_rebuild(tmp_path):
    from learnloop_sidecar.handlers.serializers import feedback_bundle
    from learnloop_sidecar.handlers.sessions import _session_followups_queued

    root, repository = _journey("recurrence_judge", tmp_path)
    vault = load_vault(root)
    with repository.connection() as connection:
        attempts = [(str(r[0]), str(r[1]), str(r[2])) for r in connection.execute(
            "SELECT id, practice_item_id, created_at FROM practice_attempts ORDER BY created_at, id")]
    # The live gate's queued actions, as it writes them (``update_attempt_surprise_actions``): one for an item answered
    # later (the follow-up link), one for an item nobody answered since (the scheduler's pending list).
    first_id, first_item, _ = attempts[0]
    later_item = next(item for _, item, _ in attempts[1:] if item == first_item)
    repository.update_attempt_surprise_actions(
        first_id, triggered_actions=[f"negative_surprise_followup:{later_item}"])
    last_id = attempts[-1][0]
    repository.update_attempt_surprise_actions(
        last_id, triggered_actions=["intervention_followup:queued:pi_svd_define_001"],
        suppressed_actions=["intervention_followup:session_cap_reached:pi_svd_compute_002"])
    session_id = repository.create_session(clock=FrozenClock(NOW - timedelta(days=60)))
    repository.end_session(session_id, clock=FrozenClock(NOW + timedelta(days=60)))

    def shown() -> dict:
        return {
            "feedback": {aid: feedback_bundle(vault, repository, aid) for aid, _, _ in attempts},
            "answered_followup_of": {aid: repository.followup_source_attempt(aid) for aid, _, _ in attempts},
            "session_followups_queued": _session_followups_queued(repository, session_id),
            "pending": repository.pending_followup_practice_items(clock=FrozenClock(NOW + timedelta(days=60))),
        }

    before = shown()
    assert before["session_followups_queued"] == 2
    assert {"practice_item_id": "pi_svd_define_001", "action_type": "intervention_followup"} in before["pending"]
    assert any(before["answered_followup_of"].values())
    rebuild_all_derived_state(vault, repository)
    after = shown()
    # The causal overlay is the diagnosis receipt's, not the gate's: it is compared by its own tests.
    for state in (before, after):
        for bundle in state["feedback"].values():
            bundle.pop("causalFeedback", None)
    assert after == before


def test_the_shadow_rebuild_compares_the_gates_records(tmp_path):
    from learnloop.substrate.shadow_rebuild import shadow_rebuild

    root, repository = _journey("recurrence_judge", tmp_path)
    report = shadow_rebuild(load_vault(root))
    gate = report.as_dict()["followup_gate_records"]
    assert gate["recorded_before"] == 3
    assert (gate["changed"], gate["added"], gate["removed"]) == (0, 0, 0)
