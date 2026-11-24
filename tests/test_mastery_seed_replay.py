"""mvp-0.67: the mastery seed a topic started from is recorded and replayed (refactor step D8, gap 3).

A learning object's mastery row is created once, from the claims then in force (vault sync, an attempt on a learning
object without a row, a re-anchoring claim on one), and a claim that does not re-anchor (a changed starting level, a
manual claim) leaves it as it is: the profile setter's explicit contract, which stays. Below the tag replay seeds a
practised learning object from the claims made before its first attempt and an attempt-free one from the claims in
force at rebuild time, so a rebuild after such a claim disagrees with live. From the tag the writer that first persists
the row records every claim its seed considered (``mastery_seed_inputs``); replay and the attempt-free rebuild seed
from the record and apply only the re-anchoring claims made after it. The upgrade reconstructs a record for every
learning object from the predecessor's own rebuild (``legacy_reconstructed``) and freezes it
(docs/reviews/algorithm-mvp-0.67.md).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from learnloop.algorithm_versions import (
    LIFECYCLE_INPUTS_ALGORITHM_VERSION,
    MASTERY_SEED_ALGORITHM_VERSION,
    MASTERY_SEED_VERSIONS,
    SUCCESSOR_CHAIN,
    mastery_seed_on,
)
from learnloop.content.authoring.item_authoring import retire_item
from learnloop.db.repositories import Repository
from learnloop.learner import mastery as learner_mastery
from learnloop.learner.learner_profile import seed_global_learner_claim
from learnloop.learner.mastery import initial_mastery_state_for_learning_object
from learnloop.ops.upgrades import upgrade
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.rebuild_equivalence_helpers import (
    ZERO,
    _answer,
    _at,
    _iso,
    _live_reanchoring_claim,
    _mastery,
    _shadow_summary,
    _vault,
)

AT, BEFORE = MASTERY_SEED_ALGORITHM_VERSION, LIFECYCLE_INPUTS_ALGORITHM_VERSION
LO = "lo_svd_definition"
ITEM = "pi_svd_define_001"
COLD_LO = "lo_diag"


def _seed_rows(repository) -> dict[str, tuple]:
    with repository.connection() as connection:
        return {
            row["learning_object_id"]: (
                [(claim["id"], claim["source"], claim["in_force"]) for claim in json.loads(row["claims_made_json"])],
                row["selected_claim_id"], row["materialized_at"], row["basis"], row["policy_version"],
                row["recorded_at"],
            )
            for row in connection.execute("SELECT * FROM mastery_seed_inputs")
        }


def _claim_ids(repository, source) -> list[str]:
    return [claim["id"] for claim in repository.learner_claims(include_superseded=True) if claim["source"] == source]


def _manual_claim(repository, lo_id, *, level, minutes):
    return repository.insert_learner_claim(
        {
            "claim_type": "self_rating", "scope_type": "learning_object", "scope_id": lo_id,
            "evidence_family": "recall", "claimed_level": level, "prior_pseudo_count": 2.0, "source": "manual_cli",
        },
        clock=_at(minutes),
    )


def _forget(repository, lo_id):
    """An LO no writer has materialized yet (as one added to the vault after the last sync)."""

    with repository.connection() as connection:
        connection.execute("DELETE FROM learning_object_mastery WHERE learning_object_id = ?", (lo_id,))
        connection.execute("DELETE FROM mastery_seed_inputs WHERE learning_object_id = ?", (lo_id,))
        connection.commit()


def _rebuilds_to_live(paths, repository):
    live = _mastery(repository)
    seeds = _seed_rows(repository)
    diff = _shadow_summary(paths)
    assert diff["summary"] == ZERO, {family: diff[family]["changes"][:3] for family in ZERO}
    for _ in range(2):
        rebuild_all_derived_state(load_vault(paths.root), repository)
        assert _mastery(repository) == live
        # The records are inputs: no rebuild writes, replaces or clears one.
        assert _seed_rows(repository) == seeds
    return live


def test_the_tag():
    assert AT == "mvp-0.67" == SUCCESSOR_CHAIN[-5] and SUCCESSOR_CHAIN[-6] == BEFORE == "mvp-0.66"
    assert MASTERY_SEED_VERSIONS == frozenset({AT, "mvp-0.68", "mvp-0.69", "mvp-0.70", "mvp-0.72"})
    for version in (BEFORE, AT):
        config = type("C", (), {"algorithms": type("A", (), {"algorithm_version": version})()})()
        assert mastery_seed_on(config) is (version == AT)


# -- the profile contract, which stays -------------------------------------------------------------------------------


@pytest.mark.parametrize("version", [BEFORE, AT])
def test_a_starting_level_changed_after_materialization_leaves_live_mastery_as_it_was(tmp_path, version):
    paths, vault, repository = _vault(tmp_path, version=version)
    before = _mastery(repository)
    seed_global_learner_claim(repository, "comfortable", clock=_at(1))
    sync_vault_state(load_vault(paths.root), repository, clock=_at(2))
    assert _mastery(repository) == before


def test_below_the_tag_nothing_is_recorded_and_the_rebuild_reads_the_claims_in_force_now(tmp_path):
    # The defect, kept below the tag: the attempt-free rebuild seeds every LO from the changed starting level.
    paths, vault, repository = _vault(tmp_path, version=BEFORE)
    seed_global_learner_claim(repository, "comfortable", clock=_at(1))
    assert _seed_rows(repository) == {}
    assert _shadow_summary(paths)["summary"]["mastery"] > 0


# -- what is recorded -------------------------------------------------------------------------------------------------


def test_sync_records_every_claim_the_seed_considered_with_its_row(tmp_path):
    paths, vault, repository = _vault(tmp_path, claims=[(LO, 0.8)])
    rows = _seed_rows(repository)
    assert set(rows) == set(vault.learning_objects)
    (manual,) = _claim_ids(repository, "manual_cli")
    claims, selected, materialized_at, basis, policy, recorded_at = rows[LO]
    assert claims == [(manual, "manual_cli", True)] and selected == manual
    assert (materialized_at, basis, policy, recorded_at) == (
        _iso(0), "captured_at_materialization", "covering_claims_seed_v1", _iso(0))
    # A cold start: nothing considered, nothing selected.
    assert rows[COLD_LO][:2] == ([], None)


def test_asking_for_a_hypothetical_prior_records_nothing(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    _forget(repository, COLD_LO)
    initial_mastery_state_for_learning_object(vault, repository, COLD_LO, _iso(1))
    assert COLD_LO not in _seed_rows(repository) and repository.mastery_state(COLD_LO) is None


def test_an_interrupted_materialization_leaves_neither_the_row_nor_its_record(tmp_path, monkeypatch):
    paths, vault, repository = _vault(tmp_path)
    _forget(repository, COLD_LO)

    def refused(*args, **kwargs):
        raise RuntimeError("injected failure after the row's write")

    monkeypatch.setattr(Repository, "record_mastery_seed_inputs", refused)
    with pytest.raises(RuntimeError, match="injected"):
        sync_vault_state(vault, repository, clock=_at(1))
    monkeypatch.undo()
    assert repository.mastery_state(COLD_LO) is None and COLD_LO not in _seed_rows(repository)

    seed_global_learner_claim(repository, "some_exposure", clock=_at(2))
    sync_vault_state(load_vault(paths.root), repository, clock=_at(3))
    (wizard,) = _claim_ids(repository, "init_wizard")
    assert _seed_rows(repository)[COLD_LO][:3] == ([(wizard, "init_wizard", True)], wizard, _iso(3))
    _rebuilds_to_live(paths, repository)


def test_an_attempt_on_an_lo_without_a_row_records_the_seed_its_prior_read(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    _forget(repository, LO)
    seed_global_learner_claim(repository, "some_exposure", clock=_at(1))
    _answer(vault, repository, ITEM, minutes=2, points=2.0)
    (wizard,) = _claim_ids(repository, "init_wizard")
    claims, selected, materialized_at, basis, _policy, _recorded = _seed_rows(repository)[LO]
    assert (claims, selected, materialized_at, basis) == (
        [(wizard, "init_wizard", True)], wizard, _iso(2), "captured_at_materialization")
    seed_global_learner_claim(repository, "comfortable", clock=_at(3))
    _rebuilds_to_live(paths, repository)


def test_a_rolled_back_attempt_leaves_neither_its_row_nor_the_seed_record(tmp_path, monkeypatch):
    paths, vault, repository = _vault(tmp_path)
    _forget(repository, LO)

    def refused(*args, **kwargs):
        raise RuntimeError("injected failure after the attempt's own write")

    monkeypatch.setattr(repository, "save_attempt_completion", refused)
    with pytest.raises(RuntimeError, match="injected"):
        _answer(vault, repository, ITEM, minutes=1)
    monkeypatch.undo()
    assert repository.mastery_state(LO) is None and LO not in _seed_rows(repository)
    assert repository.list_all_attempts() == []


def test_a_reanchoring_claim_that_materializes_the_row_is_in_its_seed_and_never_applied_again(tmp_path, monkeypatch):
    paths, vault, repository = _vault(tmp_path)
    _forget(repository, LO)
    _live_reanchoring_claim(vault, repository, LO, minutes=1, level=0.3)
    (gap,) = _claim_ids(repository, "tutor_gap_declaration")
    assert _seed_rows(repository)[LO][:4] == (
        [(gap, "tutor_gap_declaration", True)], gap, _iso(1), "captured_at_materialization")
    _answer(vault, repository, ITEM, minutes=2, points=3.0)
    seed_global_learner_claim(repository, "comfortable", clock=_at(3))
    _rebuilds_to_live(paths, repository)

    applied: list[str] = []
    original = learner_mastery.reanchor_mastery_from_claim

    def counting(vault, repository, learning_object_id, **kwargs):
        applied.append(learning_object_id)
        return original(vault, repository, learning_object_id, **kwargs)

    monkeypatch.setattr(learner_mastery, "reanchor_mastery_from_claim", counting)
    rebuild_all_derived_state(load_vault(paths.root), repository)
    assert LO not in applied


# -- the successor contract: a rebuild equals live --------------------------------------------------------------------


@pytest.mark.parametrize("answered", [True, False], ids=["with-an-attempt", "attempt-free"])
def test_a_starting_level_changed_after_materialization_rebuilds_to_live(tmp_path, answered):
    paths, vault, repository = _vault(tmp_path)
    seed_global_learner_claim(repository, "some_exposure", clock=_at(1))
    if answered:
        _answer(vault, repository, ITEM, minutes=2, points=2.0)
    live = _rebuilds_to_live(paths, repository)
    # An attempt-free LO still carries the cold start it was materialized with (sync ran before the claim).
    assert live[COLD_LO][:3] == (0.0, float(vault.config.mastery.cold_start_prior_logit_variance), 0)


@pytest.mark.parametrize("answered", [True, False], ids=["with-an-attempt", "attempt-free"])
def test_a_manual_claim_made_after_materialization_rebuilds_to_live(tmp_path, answered):
    paths, vault, repository = _vault(tmp_path)
    _manual_claim(repository, LO, level=0.9, minutes=1)
    if answered:
        _answer(vault, repository, ITEM, minutes=2, points=1.0)
    _rebuilds_to_live(paths, repository)


def test_several_starting_level_changes_around_an_attempt_rebuild_to_live(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    seed_global_learner_claim(repository, "new_to_this", clock=_at(1))
    _answer(vault, repository, ITEM, minutes=2, points=2.0)
    seed_global_learner_claim(repository, "comfortable", clock=_at(3))
    seed_global_learner_claim(repository, "some_exposure", clock=_at(4))
    assert len(_claim_ids(repository, "init_wizard")) == 3
    _rebuilds_to_live(paths, repository)


def test_a_reanchor_before_the_first_attempt_reads_the_claims_made_by_its_point(tmp_path):
    # Live, the gap declaration re-seeds the zero-evidence row from every claim in force at its time, the later
    # starting level included; replay applies it at the same point, on the recorded seed.
    paths, vault, repository = _vault(tmp_path)
    seed_global_learner_claim(repository, "comfortable", clock=_at(1))
    _live_reanchoring_claim(vault, repository, LO, minutes=2, level=0.3)
    _answer(vault, repository, ITEM, minutes=3, points=4.0)
    seed_global_learner_claim(repository, "new_to_this", clock=_at(4))
    _rebuilds_to_live(paths, repository)


def test_an_attempt_free_lo_replays_its_seed_then_the_reanchors_after_it(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    seed_global_learner_claim(repository, "comfortable", clock=_at(1))
    retire_item(paths.root, repository, practice_item_id="pi_diag_mid", reason="too_easy", clock=_at(2))
    seed_global_learner_claim(repository, "new_to_this", clock=_at(3))
    assert repository.list_attempts_by_learning_object(COLD_LO) == []
    _rebuilds_to_live(paths, repository)


def test_an_lo_no_writer_materialized_is_materialized_and_recorded_by_the_rebuild(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    _forget(repository, COLD_LO)
    seed_global_learner_claim(repository, "comfortable", clock=_at(1))
    rebuild_all_derived_state(vault, repository, clock=_at(2))
    (wizard,) = _claim_ids(repository, "init_wizard")
    assert _seed_rows(repository)[COLD_LO][:4] == (
        [(wizard, "init_wizard", True)], wizard, _iso(2), "captured_at_materialization")
    seed_global_learner_claim(repository, "new_to_this", clock=_at(3))
    _rebuilds_to_live(paths, repository)


# -- the upgrade ------------------------------------------------------------------------------------------------------


def test_the_upgrade_freezes_the_predecessors_seeds_then_new_claims_seed_nothing(tmp_path):
    # At mvp-0.66 a starting level changed after materialization leaves live and rebuild apart (the defect). The
    # upgrade cannot recover what the rows were first seeded from: it records the claims the predecessor's rebuild
    # seeds from, labelled a reconstruction, and the rebuild under the tag normalizes the live rows to them.
    paths, vault, repository = _vault(tmp_path, version=BEFORE)
    seed_global_learner_claim(repository, "some_exposure", clock=_at(1))
    _answer(vault, repository, ITEM, minutes=2, points=2.0)
    predecessor_live = _mastery(repository)
    assert _shadow_summary(paths)["summary"] != ZERO

    result = upgrade(paths.root, to=AT)
    assert result.upgraded, result.problems
    rows = _seed_rows(repository)
    (wizard,) = _claim_ids(repository, "init_wizard")
    assert set(rows) == set(vault.learning_objects)
    assert {row[3] for row in rows.values()} == {"legacy_reconstructed"}
    assert {row[2] for row in rows.values()} == {None}
    # The practised LO: the claims made before its first attempt; an attempt-free one: the claims in force now.
    assert rows[LO][:2] == ([(wizard, "init_wizard", True)], wizard)
    assert rows[COLD_LO][:2] == ([(wizard, "init_wizard", True)], wizard)
    assert _mastery(repository) != predecessor_live
    assert _shadow_summary(paths)["summary"] == ZERO

    # Frozen: a later starting level seeds nothing already materialized, live or rebuilt.
    seed_global_learner_claim(repository, "comfortable", clock=_at(3))
    _answer(load_vault(paths.root), repository, ITEM, minutes=60, points=3.0)
    _rebuilds_to_live(paths, repository)
    assert _seed_rows(repository) == rows

    again = upgrade(paths.root, to=AT)
    assert not again.upgraded and again.problems == [f"vault is already {AT}"]
    assert _seed_rows(repository) == rows


def test_the_upgrade_changes_nothing_where_no_claim_came_after_materialization(tmp_path):
    paths, vault, repository = _vault(tmp_path, claims=[(LO, 0.8)], version=BEFORE)
    _answer(vault, repository, ITEM, minutes=1, points=2.0)
    _live_reanchoring_claim(vault, repository, LO, minutes=2, level=0.4)
    predecessor_live = _mastery(repository)

    assert upgrade(paths.root, to=AT).upgraded
    assert {row[3] for row in _seed_rows(repository).values()} == {"legacy_reconstructed"}
    assert _mastery(repository) == predecessor_live
    assert _shadow_summary(paths)["summary"] == ZERO


# -- goldens: the values the three kinds of history derive, live and rebuilt ----------------------------------------

GOLDEN = Path(__file__).parent / "goldens" / "mastery_seed_replay.json"
WRITE = os.environ.get("MASTERY_SEED_WRITE_GOLDEN") == "1"


def _seed_only_profile_edits(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    seed_global_learner_claim(repository, "new_to_this", clock=_at(1))
    _answer(vault, repository, ITEM, minutes=2, points=2.0)
    seed_global_learner_claim(repository, "comfortable", clock=_at(3))
    _manual_claim(repository, COLD_LO, level=0.9, minutes=4)
    return paths, repository


def _actual_reanchors(tmp_path):
    paths, vault, repository = _vault(tmp_path, claims=[(LO, 0.8)])
    seed_global_learner_claim(repository, "comfortable", clock=_at(1))
    _live_reanchoring_claim(vault, repository, LO, minutes=2, level=0.3)
    _answer(vault, repository, ITEM, minutes=3, points=4.0)
    _live_reanchoring_claim(load_vault(paths.root), repository, LO, minutes=4, level=0.6)
    return paths, repository


def _attempt_free_replay(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    seed_global_learner_claim(repository, "comfortable", clock=_at(1))
    retire_item(paths.root, repository, practice_item_id="pi_diag_mid", reason="too_easy", clock=_at(2))
    retire_item(paths.root, repository, practice_item_id="pi_diag_hard", reason="too_easy", clock=_at(3))
    seed_global_learner_claim(repository, "new_to_this", clock=_at(4))
    return paths, repository


def _recorded(repository) -> dict:
    sources = {claim["id"]: claim["source"] for claim in repository.learner_claims(include_superseded=True)}
    return {
        lo_id: {
            "claims": [[source, in_force] for _claim_id, source, in_force in claims],
            "selected": sources.get(selected) if selected else None,
            "materialized_at": materialized_at, "basis": basis, "policy": policy,
        }
        for lo_id, (claims, selected, materialized_at, basis, policy, _recorded_at) in sorted(
            _seed_rows(repository).items())
    }


@pytest.mark.parametrize("scenario", [_seed_only_profile_edits, _actual_reanchors, _attempt_free_replay],
                         ids=lambda scenario: scenario.__name__.strip("_"))
def test_the_golden_values_live_and_rebuilt(tmp_path, scenario):
    paths, repository = scenario(tmp_path)
    live = {"mastery": {lo: list(values) for lo, values in sorted(_mastery(repository).items())},
            "seeds": _recorded(repository)}
    rebuild_all_derived_state(load_vault(paths.root), repository)
    rebuilt = {"mastery": {lo: list(values) for lo, values in sorted(_mastery(repository).items())},
               "seeds": _recorded(repository)}
    assert rebuilt == live
    name = scenario.__name__.strip("_")
    goldens = json.loads(GOLDEN.read_text()) if GOLDEN.exists() else {}
    if WRITE:
        goldens[name] = live
        # One scenario per line: the structure ratchet counts golden JSON lines.
        GOLDEN.write_text("{\n" + ",\n".join(
            f"{json.dumps(key)}: {json.dumps(goldens[key], sort_keys=True)}" for key in sorted(goldens)) + "\n}\n")
    assert goldens[name] == live
