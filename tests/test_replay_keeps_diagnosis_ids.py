"""Replay reproduces the diagnosis ids history shows and other rows reference: a causal hypothesis's id and the
diagnosis receipt's id. A later live version of a hypothesis (a recurrence promotion, a withdrawal, a learner's
confirmation) is never reverted by a fresh copy on replay, so the receipt replay rebuilds has the recorded content and
the recorded id, and the cause factors' refs still name the versions live materialization named."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.replay import replay_learning_object
from learnloop.vault.loader import load_vault

from tests import pinned_draws
from tests.diagnosis_journey_helpers import CASES, freeze_ids, freeze_wall, pin_journey_draws, run_case


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


def _diagnosis_state(repository) -> dict:
    with repository.connection() as connection:
        hypotheses = [tuple(row) for row in connection.execute(
            "SELECT id, episode_key, version, supersedes_id, status FROM causal_hypotheses ORDER BY episode_key, version")]
        receipts = {}
        for attempt_id, payload in connection.execute("SELECT attempt_id, payload_json FROM attempt_debug_payloads"):
            attribution = (json.loads(payload) or {}).get("causal_attribution") or {}
            current = attribution.get("diagnosis_receipt") or {}
            receipts[attempt_id] = (current.get("id"), [ref.get("id") for ref in current.get("hypotheses") or []],
                                    [receipt.get("id") for receipt in attribution.get("diagnosis_receipts") or []])
        factors = {str(row[0]): row[1] for row in connection.execute(
            "SELECT id, candidate_causes_json FROM unresolved_cause_factors ORDER BY id")}
    return {"hypotheses": hypotheses, "receipts": receipts, "factor_refs": factors}


@pytest.mark.parametrize("case", CASES)
def test_a_rebuild_keeps_every_hypothesis_and_receipt_id(case, tmp_path):
    root, repository = _journey(case, tmp_path)
    before = _diagnosis_state(repository)
    rebuild_all_derived_state(load_vault(root), repository)
    assert _diagnosis_state(repository) == before


def test_a_promoted_hypothesis_stays_promoted_and_its_receipt_keeps_its_id(tmp_path):
    root, repository = _journey("recurrence_judge", tmp_path)
    before = _diagnosis_state(repository)
    # The journey promoted the recurring misconception after the first two attempts were diagnosed: their episodes
    # hold a later live version than the one their receipts cite.
    advanced = {episode for _id, episode, version, _sup, _status in before["hypotheses"] if version > 1}
    assert len(advanced) == 2
    rebuild_all_derived_state(load_vault(root), repository)
    after = _diagnosis_state(repository)
    assert after == before
    # Every reference still resolves: each receipt's hypotheses and each factor's refs name stored versions.
    ids = {row[0] for row in after["hypotheses"]}
    assert all(ref in ids for _rid, refs, _all in after["receipts"].values() for ref in refs)
    for refs in after["factor_refs"].values():
        assert all(ref["hypothesis_id"] in ids for ref in json.loads(refs or "[]")
                   if isinstance(ref, dict) and ref.get("hypothesis_id"))


def test_a_per_lo_replay_appends_no_version(tmp_path):
    root, repository = _journey("recurrence_judge", tmp_path)
    before = _diagnosis_state(repository)
    vault = load_vault(root)
    for learning_object_id in repository.learning_object_ids_with_attempts():
        replay_learning_object(vault, repository, learning_object_id)
    assert _diagnosis_state(repository) == before


def test_the_shadow_rebuild_reports_no_difference(tmp_path):
    from learnloop.substrate.shadow_rebuild import shadow_rebuild

    root, _repository = _journey("recurrence_judge", tmp_path)
    report = shadow_rebuild(load_vault(root)).as_dict()
    # No hypothesis version, no text provenance: the replay appended nothing to the diagnosis ledgers.
    assert {"causal_hypotheses", "text_write_provenance"}.isdisjoint(report["ledger_rows_added"])
    assert report["followup_gate_records"]["changed"] == 0
    diff = report["learner_state_diff"]
    assert (diff["summary"]["facet"], diff["summary"]["schedule"]) == (0, 0)
    # The journey's vault never ran the bootstrap, so the rebuild adds a cold row for each LO with no attempt (as
    # ``_run_learning_state`` says it must); no row with evidence differs.
    assert all(change["change"] == "added" and change["after"]["evidence_count"] == 0
               for change in diff["mastery"]["changes"])
