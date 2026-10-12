"""mvp-0.11 replay: stuck answers rebuild exactly; historical dont_know is unchanged.

Durability lane: replay and rebuild are where WAL and the production pragmas
matter, and these tests compare whole derived snapshots.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from learnloop.ai import transport as transport_module
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.attempts.stuck import stuck_answers
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.table_roles import TableRole, tables_for_role
from learnloop.field.outcomes import load_attempt_rows
from learnloop.field.signals import load_interaction_signals
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault

from tests.helpers import set_algorithm_version
from tests.split_live_helpers import at, drain_jobs, split_vault
from tests.test_stuck_prompt import StuckFake, _draft, _grade

pytestmark = pytest.mark.durability

CLOCK = FrozenClock(datetime(2026, 9, 1, 12, 0, tzinfo=UTC))
#: Raw ledgers that replay rewrites (error events, debug payloads) or appends
#: to (hypotheses), plus the factors the projection reconciles.
REWRITTEN = ("error_events", "causal_hypotheses", "attempt_debug_payloads", "unresolved_cause_factors")


def _snapshot(repository: Repository, tables, *, version_alias: tuple[str, str] | None = None) -> dict:
    out: dict[str, list[str]] = {}
    with connect(repository.sqlite_path, read_only=True) as connection:
        for table in sorted(tables):
            rows = [json.dumps(dict(row), sort_keys=True, default=str) for row in connection.execute(f'SELECT * FROM "{table}"')]
            if version_alias is not None:
                # The version stamp also appears inside nested JSON payloads.
                rows = [row.replace(version_alias[0], version_alias[1]) for row in rows]
            out[table] = sorted(rows)
    return out


def _field(vault, repository):
    with connect(repository.sqlite_path, read_only=True) as connection:
        rows = load_attempt_rows(connection, vault, legacy_fallback="current_content")
        signals = load_interaction_signals(connection, vault, rows)
        stuck = stuck_answers(connection)
    return rows, signals, stuck


def test_a_stuck_vault_rebuilds_to_a_fixed_point_with_no_model_call(tmp_path, monkeypatch):
    _paths, vault, repository = split_vault(tmp_path, version="mvp-0.11")
    confused = StuckFake(
        reading={"attempts_answer": False, "describes_confusion": True, "confusion_quote": "where Sigma comes from"}
    )
    _grade(vault, repository, confused, _draft("I can't see where Sigma comes from"), when=20)
    _grade(vault, repository, StuckFake(), _draft("", item_id="pi_svd_compute_002"), when=21)
    _grade(vault, repository, StuckFake(), _draft("A = U Sigma"), when=22)
    drain_jobs(vault, repository, confused, clock=FrozenClock(at(23)))
    tables = {*tables_for_role(TableRole.DERIVED), *REWRITTEN}
    before_field = _field(vault, repository)

    def refuse(*_args, **_kwargs):
        raise AssertionError("replay must not call a model")

    monkeypatch.setattr(transport_module, "execute_structured_operation", refuse)
    monkeypatch.setattr("learnloop.attempts.blind_grading.execute_structured_operation", refuse)
    monkeypatch.setattr("learnloop.attempts.grading_support.execute_structured_operation", refuse)
    monkeypatch.setattr("learnloop.diagnosis.split.contract.execute_structured_operation", refuse)
    monkeypatch.setattr("learnloop.ai.routing.ready_client_for_task", refuse)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    first = _snapshot(repository, tables)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert _snapshot(repository, tables) == first

    rows, signals, stuck = _field(vault, repository)
    assert stuck == before_field[2]
    assert [signal for signal in signals if signal.signal_type == "stuck_confusion"] == [
        signal for signal in before_field[1] if signal.signal_type == "stuck_confusion"
    ]
    assert len(stuck) == 3 and sum(row["describes_confusion"] for row in stuck) == 1
    with connect(repository.sqlite_path, read_only=True) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM practice_attempts WHERE declared_stuck = 1"
        ).fetchone()[0] == 3


def test_the_kill_switch_never_changes_how_stuck_answers_replay(tmp_path):
    paths, vault, repository = split_vault(tmp_path, version="mvp-0.11")
    _grade(vault, repository, StuckFake(), _draft(""), when=21)
    tables = {*tables_for_role(TableRole.DERIVED), *REWRITTEN}
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    on = _snapshot(repository, tables)
    with open(paths.root / "learnloop.toml", "a", encoding="utf-8") as handle:
        handle.write("\n[stuck_prompt]\nenabled = false\n")
    vault = load_vault(paths.root)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert _snapshot(repository, tables) == on


def test_historical_dont_know_rows_replay_unchanged_under_the_successor(tmp_path):
    """A vault with dont_know history rebuilds identically at mvp-0.10 and at
    mvp-0.11 (only the version stamp differs), and the learner field reads the
    dont_know rows at the configured mass under both."""

    paths, vault, repository = split_vault(tmp_path)  # mvp-0.10
    for offset, item in ((20, "pi_svd_compute_001"), (21, "pi_transpose_001")):
        complete_self_graded_attempt(
            vault,
            repository,
            AttemptDraft(practice_item_id=item, learner_answer_md="", attempt_type="dont_know"),
            SelfGradeInput(criterion_points={}, confidence=3),
            clock=FrozenClock(at(offset)),
        )
    tables = {*tables_for_role(TableRole.DERIVED), *REWRITTEN}
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    previous = _snapshot(repository, tables)
    previous_rows = {row.attempt_id: row for row in _field(vault, repository)[0]}
    with connect(repository.sqlite_path, read_only=True) as connection:
        attempts_before = [tuple(row) for row in connection.execute("SELECT * FROM practice_attempts ORDER BY id")]

    set_algorithm_version(paths, "mvp-0.11")
    vault = load_vault(paths.root)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    successor = _snapshot(repository, tables, version_alias=("mvp-0.11", "mvp-0.10"))
    assert successor == previous
    with connect(repository.sqlite_path, read_only=True) as connection:
        assert [tuple(row) for row in connection.execute("SELECT * FROM practice_attempts ORDER BY id")] == attempts_before
        dont_know_ids = [
            row[0] for row in connection.execute("SELECT id FROM practice_attempts WHERE attempt_type = 'dont_know'")
        ]
    successor_rows = {row.attempt_id: row for row in _field(vault, repository)[0]}
    assert len(dont_know_ids) == 2
    for attempt_id in dont_know_ids:
        assert successor_rows[attempt_id] == previous_rows[attempt_id]
    # The first one is a first answer on its LO: the configured 0.7, undiscounted.
    assert previous_rows[dont_know_ids[0]].effective_mass == pytest.approx(0.7) or previous_rows[
        dont_know_ids[1]
    ].effective_mass == pytest.approx(0.7)
