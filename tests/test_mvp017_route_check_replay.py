"""An mvp-0.17 vault replays its grades exactly after the route check is gone.

``fixtures/mvp017_route_check_replay`` was graded under mvp-0.17's separate
route check (generated at e238fa07a, before route-check-in-grader deleted that
code; see its README): restored, disputed, clarified, flagged, unlocated, held,
a hold a failed regrade check kept, an adjudicated hold, a not-proof-like
reading, an unavailable checker and a wrong final answer. Its derived state
was rebuilt to the fixed point there. Replay reads the blind records and the
evidence rows, never the check, so a rebuild with today's code must reproduce
every grade and every hold, and leave every ledger as it was (playbook item
6), apart from what a successor since reinterprets: the rebuild-equivalence
successor's bounded replay moves its derived rows once
(``REPLAY_CORRECTED_TABLES``), and the regrade-contract successor (mvp-0.26)
holds the one grade whose current epoch cites no contract under its own
reason. The rebuild after that changes nothing. No model is called.

Those successors' gates are gone (refactor D4: no vault that opens is below
them), so today's replay is the same at the fixture's own tag and at the floor;
the replay of mvp-0.17 itself (the derived rows the fixture holds) is no
longer served at any tag.
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
from tests.helpers import allow_below_floor

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
    allow_below_floor(root)
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


#: The grade the regrade-contract successor (mvp-0.26) reinterprets: a failed
#: regrade check kept its hold, and that regrade's epoch cites no contract, so
#: replay holds it under the successor's reason (it was held already; its score
#: and correctness are unchanged).
UNRECORDED = "held_kept_by_failed_regrade"


def _assert_grades(repository, *, replayed: bool = True) -> None:
    """Every grade as the fixture recorded it; once today's replay has run, the
    regrade-contract successor's reason on ``UNRECORDED``."""

    attempts = EXPECTED["attempts"]
    held = held_attempt_ids(repository, [row["attempt_id"] for row in attempts.values()])
    for label, expected in attempts.items():
        attempt = repository.fetch_practice_attempt(expected["attempt_id"])
        reason = "grade_contract_unrecorded" if replayed and label == UNRECORDED else expected["manual_review_reason"]
        assert (attempt["rubric_score"], attempt["correctness"], attempt["manual_review_reason"]) == (
            expected["rubric_score"], expected["correctness"], reason
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


def _ledgers_but_the_attempt_rows(state) -> dict[str, list[tuple]]:
    return {table: state[table] for table in LEDGERS if table != "practice_attempts"}


def test_an_mvp017_history_at_the_floor_replays_its_grades_and_then_changes_nothing(tmp_path):
    """The fixture's rows in a vault at the floor, as the owner's vaults hold
    such history: every grade and hold as recorded (``UNRECORDED`` under the
    successor's reason), every other ledger unchanged, and the rebuild after
    the first changes nothing."""

    from learnloop.algorithm_versions import OLDEST_SUPPORTED
    from learnloop.ops.upgrades import rewrite_algorithm_version

    root, _vault, repository = _copy(tmp_path)
    rewrite_algorithm_version(root / "learnloop.toml", "mvp-0.17", OLDEST_SUPPORTED)
    vault = load_vault(root)
    before = _state(repository)
    _assert_grades(repository, replayed=False)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    first = _state(repository)
    _assert_grades(repository)
    assert _ledgers_but_the_attempt_rows(first) == _ledgers_but_the_attempt_rows(before)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert _state(repository) == first


#: Rebuild equivalence (2026-10-25; its Codex review F3 and F4): the fixture's
#: derived rows were written by a replay that read the attempts recorded after
#: the one it recomputed (the replay of every version below that successor,
#: served now only with ``replay.ledger_bounded`` off); the successor's bounded
#: replay moves exactly these tables, on the LOs with more than one attempt.
REPLAY_CORRECTED_TABLES = ["attempt_surprise", "learning_object_mastery", "practice_item_quality_state"]
SINGLE_ATTEMPT_LO = "lo_transpose"


def test_the_bounded_replay_corrects_the_copy_in_one_rebuild_and_then_changes_nothing(tmp_path):
    """F3: the first rebuild completes what it starts. Its learner replay
    appends a causal-hypothesis version (a recurrence input), and the rebuild
    reconciles the recurrence projection itself, so the rebuild right after it
    changes no derived row, no hypothesis and no ledger row. At the fixture's
    own tag: the bounded replay and the regrade-contract reading apply at every
    tag a vault opens at, and the copy keeps every serving gate D5 and D6 have
    not yet removed at mvp-0.17's branch."""

    _root, vault, repository = _copy(tmp_path)
    before = _audited(repository)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    first = _audited(repository)
    changed = sorted(table for table in before if before[table] != first[table])
    # The appended hypothesis version restamps the recurrence fingerprint in
    # the same rebuild (the group map, empty here, is unchanged); the attempt
    # rows change only by UNRECORDED's reason.
    assert changed == sorted(
        [*REPLAY_CORRECTED_TABLES, "causal_hypotheses", "hypothesis_recurrence_state", "practice_attempts"]
    )
    single = [row for row in before["learning_object_mastery"] if row[0] == SINGLE_ATTEMPT_LO]
    assert single and single == [row for row in first["learning_object_mastery"] if row[0] == SINGLE_ATTEMPT_LO]
    _assert_grades(repository)

    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    second = _audited(repository)
    assert sorted(table for table in first if first[table] != second[table]) == []
    assert _ledgers_but_the_attempt_rows(second) == _ledgers_but_the_attempt_rows(before)
    _assert_grades(repository)


def _audited(repository) -> dict[str, list[tuple]]:
    """The semantic state plus the causal-hypothesis versions (a ledger the
    rebuild appends to, and a recurrence input), without surrogate ids."""

    state = _state(repository)
    with connect(repository.sqlite_path, read_only=True) as connection:
        columns = [row[1] for row in connection.execute("PRAGMA table_info(causal_hypotheses)")]
        kept = [column for column in columns if column not in {"id", "created_at", "updated_at"}]
        state["causal_hypotheses"] = sorted(
            tuple(row) for row in connection.execute(f"SELECT {', '.join(kept)} FROM causal_hypotheses")
        )
    return state
