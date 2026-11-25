"""Followups Oct 27 (3): answers on an LO one of whose items closed outside the attempt ledger.

The mobile PR-3/PR-4 landing found it on an owner copy: answering a row closed by
``set_practice_item_active(False)`` left ``rebuild --shadow`` at mastery 1 / schedule 1.
The cause is not the answered row's own write. The attempt path reads the
lifecycle of its LO's items: ``lo_relative_coverage`` (via ``required_facets``)
counts only the facets of the LO's *active* items, and so does the legacy
breadth denominator, so a sibling measuring a facet nothing else measures moves
the LO's coverage, mastery and the item's due date. Live, each attempt sees the
siblings as they were at its time. Below mvp-0.66 replay sees one state for the
whole history: an unattempted sibling's row is not reset, so it is closed
throughout (wrong for every answer before its closure); an attempted item's row
is rebuilt active and re-closed after the LO's last replayed attempt
(``keep_practice_items_inactive``), so it is open throughout (wrong for every
answer after its closure).

Production closes rows outside the ledger: ``retire_item`` (through
``deactivate_practice_item_serving``) and content sync (an item retired in its
YAML, removed from the vault, parked for review or superseded by a measurement
correction), probe retirement (``retire_probe_instance``), a probe dialogue's
single use and an applied proposal patch. None leaves a time replay can apply
the closure at. From mvp-0.66 the live grade application records the required
facet set it read (``attempt_lifecycle_inputs``) and replay and regrade read it
back, so every closure path is covered without one; the upgrade reconstructs the
set for earlier attempts from the predecessor's own replay
(``legacy_reconstructed``) and freezes it (docs/reviews/algorithm-mvp-0.66.md).
"""
from __future__ import annotations

import json

import pytest

from learnloop.db.repositories import Repository
from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    APPLICATION_ORDER_ALGORITHM_VERSION,
    LIFECYCLE_INPUTS_ALGORITHM_VERSION,
    LIFECYCLE_INPUTS_VERSIONS,
    SUCCESSOR_CHAIN,
    lifecycle_inputs_on,
)
from learnloop.clock import utc_now_iso
from learnloop.content.authoring.item_authoring import retire_item
from learnloop.ops.upgrades import upgrade
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW_ISO
from tests.rebuild_equivalence_helpers import ZERO, _answer, _at, _mastery, _shadow_summary, _vault

AT, BEFORE = LIFECYCLE_INPUTS_ALGORITHM_VERSION, APPLICATION_ORDER_ALGORITHM_VERSION
LO = "lo_svd_definition"
DEFINE_ITEM = "pi_svd_define_001"
APPLY_ITEM = "pi_svd_apply_001"
BOTH, RECALL_ONLY = ["application", "recall"], ["recall"]


def _with_an_application_item(tmp_path, *, version=LATEST_ALGORITHM_VERSION):
    """The placement vault plus a second facet on lo_svd_definition, measured only by one item (and its file)."""

    paths, _vault_before, repository = _vault(tmp_path, version=version)
    item_path = upsert_practice_item(
        paths.root,
        {
            "id": APPLY_ITEM,
            "learning_object_id": LO,
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["application"],
            "evidence_weights": {"application": 1.0},
            "prompt": "Use the SVD of a 2x2 matrix to find its rank.",
            "expected_answer": "The number of non-zero singular values.",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct rank."}],
                "fatal_errors": [],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=_at(0),
    )
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=_at(0.5))
    return paths, vault, repository, item_path


def _lifecycle_rows(repository) -> dict[str, tuple]:
    with repository.connection() as connection:
        return {
            str(row["attempt_id"]): (
                row["learning_object_id"], json.loads(row["required_facets_json"]), row["basis"],
                row["policy_version"], row["recorded_at"],
            )
            for row in connection.execute("SELECT * FROM attempt_lifecycle_inputs")
        }


def _required(repository) -> dict[str, list[str]]:
    return {attempt_id: row[1] for attempt_id, row in _lifecycle_rows(repository).items()}


def _read_by_both(repository, attempt_id) -> tuple[list[str], list[str]]:
    """The required facets the attempt's stored computation counted: its relative coverage's and its breadth's."""

    payload = repository.attempt_debug_payload(attempt_id)
    return (
        payload["lo_relative_coverage_trace"]["required_facets"],
        payload["covered_required_fraction_trace"]["required_facets"],
    )


def _close(repository, *, minutes):
    repository.set_practice_item_active(APPLY_ITEM, active=False, clock=_at(minutes))


# -- the tag ------------------------------------------------------------------------------------------------------


def test_the_tag():
    assert AT == "mvp-0.66" == SUCCESSOR_CHAIN[-11] and SUCCESSOR_CHAIN[-12] == BEFORE == "mvp-0.65"
    assert LIFECYCLE_INPUTS_VERSIONS == frozenset({AT, "mvp-0.67", "mvp-0.68", "mvp-0.69", "mvp-0.70", "mvp-0.71", "mvp-0.72", "mvp-0.73", "mvp-0.74", "mvp-0.75", "mvp-0.76"})
    for version, on in ((BEFORE, False), (AT, True)):
        config = type("C", (), {"algorithms": type("A", (), {"algorithm_version": version})()})()
        assert lifecycle_inputs_on(config) is on


# -- the gap's three cases (the strict xfails until mvp-0.66) -----------------------------------------------------


def test_an_answer_after_a_sibling_was_retired_rebuilds_to_live(tmp_path):
    """The production path: the sibling is retired, the primary load's content sync closes its row."""

    paths, vault, repository, _item_path = _with_an_application_item(tmp_path)
    _answer(vault, repository, DEFINE_ITEM, minutes=1)
    retire_item(paths.root, repository, practice_item_id=APPLY_ITEM, reason="duplicate_surface", clock=_at(2))
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=_at(3))
    assert repository.practice_item_state(APPLY_ITEM).active is False
    _answer(vault, repository, DEFINE_ITEM, minutes=61, points=2.0)

    assert _shadow_summary(paths)["summary"] == ZERO


def test_an_answer_after_the_landing_harness_closed_a_sibling_rebuilds_to_live(tmp_path):
    """The landing's case: the row closed directly, as content sync keeps a parked or superseded row."""

    paths, vault, repository, _item_path = _with_an_application_item(tmp_path)
    _answer(vault, repository, DEFINE_ITEM, minutes=1)
    _close(repository, minutes=2)
    _answer(vault, repository, DEFINE_ITEM, minutes=61, points=2.0)

    assert _shadow_summary(paths)["summary"] == ZERO


def test_a_sibling_retired_after_the_last_answer_rebuilds_to_live(tmp_path):
    """The most common order (retire an unanswered duplicate later): replay saw it closed from the start."""

    paths, vault, repository, _item_path = _with_an_application_item(tmp_path)
    _answer(vault, repository, DEFINE_ITEM, minutes=1)
    _answer(vault, repository, DEFINE_ITEM, minutes=61, points=2.0)
    retire_item(paths.root, repository, practice_item_id=APPLY_ITEM, reason="duplicate_surface", clock=_at(62))
    sync_vault_state(load_vault(paths.root), repository, clock=_at(63))
    assert repository.practice_item_state(APPLY_ITEM).active is False

    assert _shadow_summary(paths)["summary"] == ZERO


def test_control_every_sibling_open_rebuilds_to_live(tmp_path):
    paths, vault, repository, _item_path = _with_an_application_item(tmp_path)
    _answer(vault, repository, DEFINE_ITEM, minutes=1)
    _answer(vault, repository, DEFINE_ITEM, minutes=61, points=2.0)

    assert _shadow_summary(paths)["summary"] == ZERO


# -- what is captured, and who reads it ---------------------------------------------------------------------------


def test_each_answer_records_the_set_it_read_and_coverage_and_breadth_both_count_it(tmp_path):
    paths, vault, repository, _item_path = _with_an_application_item(tmp_path)
    first = _answer(vault, repository, DEFINE_ITEM, minutes=1).attempt_id
    _close(repository, minutes=2)
    second = _answer(vault, repository, DEFINE_ITEM, minutes=61, points=2.0).attempt_id

    rows = _lifecycle_rows(repository)
    assert rows == {
        first: (LO, BOTH, "captured_at_application", "active_item_evidence_facets_v1", utc_now_iso(_at(1))),
        second: (LO, RECALL_ONLY, "captured_at_application", "active_item_evidence_facets_v1", utc_now_iso(_at(61))),
    }
    assert _read_by_both(repository, first) == (BOTH, BOTH)
    assert _read_by_both(repository, second) == (RECALL_ONLY, RECALL_ONLY)

    # Reopened before the rebuild: replay still gives each answer the set it read, in both readings, and never
    # writes or replaces a row.
    repository.set_practice_item_active(APPLY_ITEM, active=True, clock=_at(70))
    rebuild_all_derived_state(load_vault(paths.root), repository)
    assert _lifecycle_rows(repository) == rows
    assert _read_by_both(repository, first) == (BOTH, BOTH)
    assert _read_by_both(repository, second) == (RECALL_ONLY, RECALL_ONLY)


def test_below_the_tag_nothing_is_recorded_and_replay_reads_todays_flags(tmp_path):
    paths, vault, repository, _item_path = _with_an_application_item(tmp_path, version=BEFORE)
    first = _answer(vault, repository, DEFINE_ITEM, minutes=1).attempt_id
    _close(repository, minutes=2)
    _answer(vault, repository, DEFINE_ITEM, minutes=61, points=2.0)

    assert _lifecycle_rows(repository) == {}
    assert _read_by_both(repository, first) == (BOTH, BOTH)
    # The predecessor's replay (the defect, kept below the tag): the closed sibling is closed for the first answer too.
    rebuild_all_derived_state(load_vault(paths.root), repository)
    assert _read_by_both(repository, first) == (RECALL_ONLY, RECALL_ONLY)
    assert _lifecycle_rows(repository) == {}


def test_an_attempted_sibling_closed_between_answers_rebuilds_to_live(tmp_path):
    # Replay rebuilds an attempted item's row active and re-closes it only after the learning object's last attempt,
    # so below the tag the later answer saw the closed sibling open.
    paths, vault, repository, _item_path = _with_an_application_item(tmp_path)
    _answer(vault, repository, APPLY_ITEM, minutes=1)
    _close(repository, minutes=2)
    later = _answer(vault, repository, DEFINE_ITEM, minutes=61, points=2.0).attempt_id

    assert _required(repository)[later] == RECALL_ONLY
    assert _shadow_summary(paths)["summary"] == ZERO
    rebuild_all_derived_state(load_vault(paths.root), repository)
    assert _read_by_both(repository, later) == (RECALL_ONLY, RECALL_ONLY)
    assert repository.practice_item_state(APPLY_ITEM).active is False


def test_a_sibling_closed_and_reopened_between_answers_rebuilds_to_live(tmp_path):
    paths, vault, repository, _item_path = _with_an_application_item(tmp_path)
    first = _answer(vault, repository, DEFINE_ITEM, minutes=1).attempt_id
    _close(repository, minutes=2)
    second = _answer(vault, repository, DEFINE_ITEM, minutes=61, points=2.0).attempt_id
    repository.set_practice_item_active(APPLY_ITEM, active=True, clock=_at(62))
    third = _answer(vault, repository, DEFINE_ITEM, minutes=60 * 24, points=3.0).attempt_id

    assert [_required(repository)[attempt] for attempt in (first, second, third)] == [BOTH, RECALL_ONLY, BOTH]
    assert _shadow_summary(paths)["summary"] == ZERO


def test_a_sibling_removed_from_the_vault_between_answers_rebuilds_to_live(tmp_path):
    # Once the item's file is gone, today's vault cannot say it was ever measured; the record can.
    paths, vault, repository, item_path = _with_an_application_item(tmp_path)
    first = _answer(vault, repository, DEFINE_ITEM, minutes=1).attempt_id
    item_path.unlink()
    vault = load_vault(paths.root)
    assert APPLY_ITEM not in vault.practice_items
    sync_vault_state(vault, repository, clock=_at(2))
    second = _answer(vault, repository, DEFINE_ITEM, minutes=61, points=2.0).attempt_id

    assert [_required(repository)[attempt] for attempt in (first, second)] == [BOTH, RECALL_ONLY]
    assert _shadow_summary(paths)["summary"] == ZERO
    rebuild_all_derived_state(load_vault(paths.root), repository)
    assert _read_by_both(repository, first) == (BOTH, BOTH)


def test_a_close_in_the_same_second_between_two_answers_rebuilds_to_live(tmp_path):
    # Nothing orders a closure against attempts by time; the answers' own records do, whatever the clock says.
    paths, vault, repository, _item_path = _with_an_application_item(tmp_path)
    first = _answer(vault, repository, DEFINE_ITEM, minutes=1).attempt_id
    _close(repository, minutes=1)
    second = _answer(vault, repository, DEFINE_ITEM, minutes=1, points=2.0).attempt_id

    assert repository.fetch_practice_attempt(first)["created_at"] == repository.fetch_practice_attempt(second)["created_at"]
    assert [_required(repository)[attempt] for attempt in (first, second)] == [BOTH, RECALL_ONLY]
    assert _shadow_summary(paths)["summary"] == ZERO


def test_a_regrade_reuses_the_original_capture(tmp_path):
    from tests.regrade_contract_replay_helpers import _regrade

    paths, vault, repository, _item_path = _with_an_application_item(tmp_path)
    first = _answer(vault, repository, DEFINE_ITEM, minutes=1).attempt_id
    _close(repository, minutes=2)
    rows = _lifecycle_rows(repository)

    _regrade(vault, repository, first, {"correctness": 1.0}, when=_at(90).now())
    assert repository.fetch_practice_attempt(first)["rubric_score"] == 1
    # The regrade re-applies the attempt under the set it was first applied with, not today's siblings.
    assert _lifecycle_rows(repository) == rows
    assert _read_by_both(repository, first) == (BOTH, BOTH)
    live = _mastery(repository)
    rebuild_all_derived_state(load_vault(paths.root), repository)
    assert _mastery(repository) == live


def test_a_rolled_back_application_leaves_neither_its_attempt_nor_its_capture(tmp_path, monkeypatch):
    paths, vault, repository, _item_path = _with_an_application_item(tmp_path)
    kept = _answer(vault, repository, DEFINE_ITEM, minutes=1).attempt_id

    def refused(*args, **kwargs):
        raise RuntimeError("injected failure after the attempt's own write")

    # The capture is written with the attempt's row; a failure later in the same transaction (its completion record,
    # the last write) takes both back.
    monkeypatch.setattr(repository, "save_attempt_completion", refused)
    with pytest.raises(RuntimeError, match="injected"):
        _answer(vault, repository, DEFINE_ITEM, minutes=61, points=2.0)
    monkeypatch.undo()

    assert set(_lifecycle_rows(repository)) == {kept}
    assert [row["id"] for row in repository.list_all_attempts()] == [kept]


def test_an_attempt_applied_at_the_tag_without_its_capture_refuses_to_replay(tmp_path):
    from learnloop.attempts.lifecycle_inputs import LifecycleInputsMissing

    paths, vault, repository, _item_path = _with_an_application_item(tmp_path, version=AT)
    attempt_id = _answer(vault, repository, DEFINE_ITEM, minutes=1).attempt_id
    with repository.connection() as connection:
        connection.execute("DELETE FROM attempt_lifecycle_inputs WHERE attempt_id = ?", (attempt_id,))
        connection.commit()
    before = _mastery(repository)

    with pytest.raises(LifecycleInputsMissing, match=attempt_id):
        rebuild_all_derived_state(load_vault(paths.root), repository)
    assert _mastery(repository) == before


# -- the upgrade --------------------------------------------------------------------------------------------------


def test_the_upgrade_freezes_the_predecessors_reading_then_new_answers_capture_their_own(tmp_path):
    # At mvp-0.65 the retirement after the last answer leaves live and rebuild apart (the defect). The upgrade cannot
    # recover when the sibling closed: it records the set the predecessor's replay reads (closed throughout), labelled
    # a reconstruction, and the rebuild under the tag normalizes the live rows to it.
    paths, vault, repository, _item_path = _with_an_application_item(tmp_path, version=BEFORE)
    first = _answer(vault, repository, DEFINE_ITEM, minutes=1).attempt_id
    second = _answer(vault, repository, DEFINE_ITEM, minutes=61, points=2.0).attempt_id
    _close(repository, minutes=62)
    predecessor_live = _mastery(repository)
    assert _shadow_summary(paths)["summary"] != ZERO

    result = upgrade(paths.root, to=AT)
    assert result.upgraded, result.problems
    rows = _lifecycle_rows(repository)
    assert {attempt: row[:4] for attempt, row in rows.items()} == {
        first: (LO, RECALL_ONLY, "legacy_reconstructed", "active_item_evidence_facets_v1"),
        second: (LO, RECALL_ONLY, "legacy_reconstructed", "active_item_evidence_facets_v1"),
    }
    assert _mastery(repository) != predecessor_live
    assert _shadow_summary(paths)["summary"] == ZERO

    # Frozen: reopening the sibling later reaches no reconstructed attempt, and a new answer records what it read.
    # (The writer fence: the repository opened for the predecessor's vault stays bound to it; the reload reopens it.)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    repository.set_practice_item_active(APPLY_ITEM, active=True, clock=_at(63))
    third = _answer(vault, repository, DEFINE_ITEM, minutes=60 * 24).attempt_id
    assert _lifecycle_rows(repository)[third][1:3] == (BOTH, "captured_at_application")
    live = _mastery(repository)
    rebuild_all_derived_state(vault, repository)
    assert _mastery(repository) == live
    assert {attempt: row for attempt, row in _lifecycle_rows(repository).items() if attempt != third} == rows
    assert _read_by_both(repository, first) == (RECALL_ONLY, RECALL_ONLY)

    # A second upgrade does nothing: the rebuild's receipt is the activation's.
    again = upgrade(paths.root, to=AT)
    assert not again.upgraded and again.problems == [f"vault is already {AT}"]
    assert set(_lifecycle_rows(repository)) == {first, second, third}


def test_the_upgrade_changes_nothing_where_no_sibling_changed(tmp_path):
    paths, vault, repository, _item_path = _with_an_application_item(tmp_path, version=BEFORE)
    _answer(vault, repository, DEFINE_ITEM, minutes=1)
    _answer(vault, repository, APPLY_ITEM, minutes=61, points=2.0)
    predecessor_live = _mastery(repository)

    assert upgrade(paths.root, to=AT).upgraded
    assert set(row[2] for row in _lifecycle_rows(repository).values()) == {"legacy_reconstructed"}
    assert _mastery(repository) == predecessor_live
    assert _shadow_summary(paths)["summary"] == ZERO


# -- canonical iteration ------------------------------------------------------------------------------------------


def test_at_the_tag_relative_coverage_sums_the_facets_in_their_sorted_order():
    from types import SimpleNamespace

    from learnloop.learner.facet_diagnostics import LoCoverageReads, lo_relative_coverage_from

    config = SimpleNamespace(kappa_uncertain=1.0, tau_facet_share=0.1)
    uncertainties = {facet: SimpleNamespace(uncertainty=value) for facet, value in (
        ("c", 0.1), ("a", 0.7), ("d", 0.3), ("b", 0.9))}
    weights = {"a": 1.0, "c": 1.0}
    reads = LoCoverageReads(required=("a", "b", "c", "d"), open_uncertainties=uncertainties, canonical=True)
    value, trace = lo_relative_coverage_from(reads, config, normalized_facet_weights=weights,
                                             effective_item_coverage=0.37)

    importance = [1.0 + uncertainties[facet].uncertainty for facet in sorted(uncertainties)]
    covered = [0.37 if facet in weights else 0.0 for facet in sorted(uncertainties)]
    expected = sum(i * c for i, c in zip(importance, covered, strict=True)) / sum(importance)
    assert value == expected
    assert trace["measured_facets"] == ["a", "b", "c", "d"]
