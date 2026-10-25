"""An mvp-0.17 vault replays its grades exactly after the route check is gone.

``fixtures/mvp017_route_check_replay`` was graded under mvp-0.17's separate
route check (generated at e238fa07a, before route-check-in-grader deleted that
code; see its README): restored, disputed, clarified, flagged, unlocated, held,
a hold a failed regrade check kept, an adjudicated hold, a not-proof-like
reading, an unavailable checker and a wrong final answer. Its derived state
was rebuilt to the fixed point there. Replay reads the blind records and the
evidence rows, never the check, so a rebuild with today's code must reproduce
every grade and every hold, and leave every ledger as it was (playbook item
6). Its derived rows move once, by the rebuild-equivalence fix of 2026-10-25
(``REPLAY_CORRECTED_TABLES``), and are then at the fixed point. Upgrading the
copy rewrites nothing either. No model is called.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.table_roles import TableRole, tables_for_role
from learnloop.held_grades import held_attempt_ids
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault
from learnloop.vault.repository import open_vault_repository

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mvp017_route_check_replay"
EXPECTED = json.loads((FIXTURE / "expected.json").read_text(encoding="utf-8"))
CLOCK = FrozenClock(datetime.fromisoformat(EXPECTED["rebuild_clock"]))
#: What an attempt's grade is, as every reader sees it.
LEDGERS = (
    "practice_attempts", "grading_evidence", "blind_grade_records", "judgment_ledger",
    "grading_clarifications",
)
#: ``raw_grade_events`` is append-only and every rebuild appends one event per
#: replayed grade (new ids, at every version): the events are compared without
#: their surrogate ids (``id``, ``administration_id``, ``observation_id``).
RAW_GRADE_EVENT_KEY = (
    "attempt_id", "role", "grader_provider", "grading_prompt_version", "grader_output_schema_version",
    "grader_identity_hash", "raw_output_json", "criterion_evidence_json", "observed_class",
    "criterion_observed_classes_json", "created_at",
)


def _copy(tmp_path):
    root = tmp_path / "vault"
    copy_tree_with_databases(FIXTURE, root)
    return root, load_vault(root), open_vault_repository(root, root / "state.sqlite")


def _state(repository) -> dict[str, list[tuple]]:
    tables = sorted(set(tables_for_role(TableRole.DERIVED)) | set(LEDGERS))
    with connect(repository.sqlite_path, read_only=True) as connection:
        state = {
            table: sorted(tuple(row) for row in connection.execute(f'SELECT * FROM "{table}"'))
            for table in tables
        }
        columns = ", ".join(RAW_GRADE_EVENT_KEY)
        state["raw_grade_events (distinct, without ids)"] = sorted(
            tuple(row) for row in connection.execute(f"SELECT DISTINCT {columns} FROM raw_grade_events")
        )
    return state


def _assert_grades(repository) -> None:
    attempts = EXPECTED["attempts"]
    held = held_attempt_ids(repository, [row["attempt_id"] for row in attempts.values()])
    for label, expected in attempts.items():
        attempt = repository.fetch_practice_attempt(expected["attempt_id"])
        assert (attempt["rubric_score"], attempt["correctness"], attempt["manual_review_reason"]) == (
            expected["rubric_score"], expected["correctness"], expected["manual_review_reason"]
        ), label
        assert (expected["attempt_id"] in held) is expected["held"], label
        record = repository.latest_blind_grade_record(expected["attempt_id"])["record"]
        # The calibration identity replay reads is the one mvp-0.17 wrote.
        assert record["calibration_prompt_version"] == expected["calibration_prompt_version"], label


def test_the_fixture_holds_every_mvp017_outcome():
    attempts = EXPECTED["attempts"]
    assert EXPECTED["algorithm_version"] == "mvp-0.17"
    statuses = {row["proof_route_check"].get("status") for row in attempts.values()}
    assert statuses == {"checked", "unavailable", "not_proof_like"}
    checked = [row["proof_route_check"] for row in attempts.values()]
    for key in ("restored_criterion_ids", "disputed_criterion_ids", "flagged_criterion_ids",
                "unlocated_criterion_ids"):
        assert any(row.get(key) for row in checked), key
    assert sum(row["held"] for row in attempts.values()) == 2  # one held, one kept by a failed regrade
    assert any(row["proof_route_check"].get("hold_kept_from") for row in attempts.values())
    assert EXPECTED["clarification_triggers"] == ["route_check_disagreement"]
    with sqlite3.connect(FIXTURE / "state.sqlite") as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "delete"


#: Rebuild equivalence (2026-10-25): the fixture's derived rows were written by
#: the replay of e238fa07a, which read the attempts recorded after the one it
#: recomputed. Today's replay reads the ledger as the live write saw it, so the
#: first rebuild moves exactly these tables, on the LOs with more than one
#: attempt; the single-attempt LO's rows and every grade stay as written.
REPLAY_CORRECTED_TABLES = ["attempt_surprise", "learning_object_mastery", "practice_item_quality_state"]
SINGLE_ATTEMPT_LO = "lo_transpose"


def test_an_mvp017_vault_replays_its_grades_exactly(tmp_path):
    _root, vault, repository = _copy(tmp_path)
    assert vault.config.algorithms.algorithm_version == "mvp-0.17"
    before = _state(repository)
    _assert_grades(repository)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    after = _state(repository)
    changed = sorted(table for table in before if before[table] != after[table])
    assert changed == REPLAY_CORRECTED_TABLES
    single = [row for row in before["learning_object_mastery"] if row[0] == SINGLE_ATTEMPT_LO]
    assert single and single == [row for row in after["learning_object_mastery"] if row[0] == SINGLE_ATTEMPT_LO]
    _assert_grades(repository)
    # Then the fixed point: the recurrence fingerprint takes one more pass (it
    # is computed before learner replay appends this rebuild's hypothesis),
    # and from there a rebuild changes no derived row and no ledger row.
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    settled = _state(repository)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert _state(repository) == settled
    assert {table: settled[table] for table in LEDGERS} == {table: before[table] for table in LEDGERS}
    _assert_grades(repository)


def test_upgrading_the_mvp017_copy_to_the_successor_rewrites_no_grade(tmp_path):
    """The route rules apply to NEW answers only: the upgrade is a tag change
    plus the idempotent rebuild, so every mvp-0.17 grade, hold and identity
    stays as written, and the ledgers are untouched."""

    from learnloop.route_rules_upgrade import upgrade_to_mvp020

    root, _vault, repository = _copy(tmp_path)
    ledgers_before = {table: rows for table, rows in _state(repository).items() if table in LEDGERS}
    result = upgrade_to_mvp020(root, clock=CLOCK)
    assert (result.upgraded, result.from_version, result.to_version) == (True, "mvp-0.17", "mvp-0.20")
    vault = load_vault(root)
    assert vault.config.algorithms.algorithm_version == "mvp-0.20"
    _assert_grades(repository)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    _assert_grades(repository)
    after = _state(repository)
    assert {table: after[table] for table in LEDGERS} == ledgers_before
