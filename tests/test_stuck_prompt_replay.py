"""mvp-0.13 replay: stuck answers rebuild exactly; historical dont_know is unchanged.

Durability lane: replay and rebuild are where WAL and the production pragmas
matter, and these tests compare whole derived snapshots.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.ai import transport as transport_module
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.attempts.stuck import stuck_answers, stuck_prompt_active
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
from tests.stuck_prompt_helpers import StuckFake, _draft, _grade

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


def _engagement_factors(repository: Repository, attempt_ids) -> dict[str, list[float]]:
    """The coverage trace's response-engagement factor each attempt's debug payload recorded (1.0 for an empty answer sent
    with "I'm stuck", 0.5 for an accidental blank): what replay re-derives from the stored declaration."""

    def found(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "response_engagement_factor":
                    yield value
                else:
                    yield from found(value)
        elif isinstance(node, list):
            for value in node:
                yield from found(value)

    with connect(repository.sqlite_path, read_only=True) as connection:
        rows = connection.execute("SELECT attempt_id, payload_json FROM attempt_debug_payloads").fetchall()
    return {row["attempt_id"]: sorted(found(json.loads(row["payload_json"]))) for row in rows
            if row["attempt_id"] in attempt_ids}


def test_a_stuck_vault_rebuilds_to_a_fixed_point_with_no_model_call(tmp_path, monkeypatch):
    _paths, vault, repository = split_vault(tmp_path, version=LATEST_ALGORITHM_VERSION)
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
    # Live state against the FIRST rebuild (review note): every stuck
    # attempt's field row, the stuck read-back and its confusion signal are
    # what the live doors wrote.
    rebuilt_rows, rebuilt_signals, rebuilt_stuck = _field(vault, repository)
    stuck_ids = {row["attempt_id"] for row in before_field[2]}
    live_rows = {row.attempt_id: row for row in before_field[0] if row.attempt_id in stuck_ids}
    assert {row.attempt_id: row for row in rebuilt_rows if row.attempt_id in stuck_ids} == live_rows
    assert rebuilt_stuck == before_field[2]
    assert [signal for signal in rebuilt_signals if signal.signal_type == "stuck_confusion"] == [
        signal for signal in before_field[1] if signal.signal_type == "stuck_confusion"
    ]
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
    paths, vault, repository = split_vault(tmp_path, version=LATEST_ALGORITHM_VERSION)
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
    """A vault whose dont_know history an older tag (mvp-0.12) recorded keeps its attempt rows through a rebuild at the head,
    reads them as the ordinary dont_know attempts they were (no stuck declaration), and the learner field gives them
    the configured mass under both tags."""

    paths, vault, repository = split_vault(tmp_path, version=BEFORE_STUCK_PROMPT)
    for offset, item in ((20, "pi_svd_compute_001"), (21, "pi_transpose_001")):
        complete_self_graded_attempt(
            vault,
            repository,
            AttemptDraft(practice_item_id=item, learner_answer_md="", attempt_type="dont_know"),
            SelfGradeInput(criterion_points={}, confidence=3),
            clock=FrozenClock(at(offset)),
        )
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    previous_rows = {row.attempt_id: row for row in _field(vault, repository)[0]}
    with connect(repository.sqlite_path, read_only=True) as connection:
        attempts_before = [tuple(row) for row in connection.execute("SELECT * FROM practice_attempts ORDER BY id")]

    set_algorithm_version(paths, LATEST_ALGORITHM_VERSION)
    vault = load_vault(paths.root)
    assert vault.config.algorithms.algorithm_version == LATEST_ALGORITHM_VERSION
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    with connect(repository.sqlite_path, read_only=True) as connection:
        assert [tuple(row) for row in connection.execute("SELECT * FROM practice_attempts ORDER BY id")] == attempts_before
        dont_know_ids = [
            row[0] for row in connection.execute("SELECT id FROM practice_attempts WHERE attempt_type = 'dont_know'")
        ]
        assert connection.execute("SELECT COUNT(*) FROM practice_attempts WHERE declared_stuck = 1").fetchone()[0] == 0
    successor_rows = {row.attempt_id: row for row in _field(vault, repository)[0]}
    assert len(dont_know_ids) == 2
    for attempt_id in dont_know_ids:
        assert successor_rows[attempt_id] == previous_rows[attempt_id]
    # The first one is a first answer on its LO: the configured 0.7, undiscounted.
    assert previous_rows[dont_know_ids[0]].effective_mass == pytest.approx(0.7) or previous_rows[
        dont_know_ids[1]
    ].effective_mass == pytest.approx(0.7)


#: A tag before the successor. No vault that opens is below it, so the tag no longer decides whether "I'm stuck" is
#: offered (``stuck_prompt.enabled`` does); replay under it still runs the older tag's remaining paths.
BEFORE_STUCK_PROMPT = "mvp-0.12"


def test_a_recorded_stuck_answer_replays_as_stuck_under_an_older_tag_with_the_prompt_off(tmp_path):
    """Replay reconstructs the stored declaration (``declared_stuck`` on the ledger row); the switch decides only whether a
    NEW stuck answer is accepted, so a vault that stops offering the prompt, and replays under an older tag, keeps its
    stuck history."""

    paths, vault, repository = split_vault(tmp_path, version=LATEST_ALGORITHM_VERSION)
    confused = StuckFake(
        reading={"attempts_answer": False, "describes_confusion": True, "confusion_quote": "where Sigma comes from"}
    )
    _grade(vault, repository, confused, _draft("I can't see where Sigma comes from"), when=20)
    _grade(vault, repository, StuckFake(), _draft("", item_id="pi_svd_compute_002"), when=21)
    drain_jobs(vault, repository, confused, clock=FrozenClock(at(22)))
    with connect(repository.sqlite_path, read_only=True) as connection:
        stuck_ids = {row[0] for row in connection.execute("SELECT id FROM practice_attempts WHERE declared_stuck = 1")}
    live_rows, _signals, live_stuck = _field(vault, repository)
    live_stuck_rows = {row.attempt_id: row for row in live_rows if row.attempt_id in stuck_ids}
    assert len(stuck_ids) == 2 and len(live_stuck) == 2 and len(live_stuck_rows) == 2
    live_factors = _engagement_factors(repository, stuck_ids)
    assert any(factors == [1.0] for factors in live_factors.values())  # the empty stuck answer counts as engaged

    set_algorithm_version(paths, BEFORE_STUCK_PROMPT)
    with open(paths.root / "learnloop.toml", "a", encoding="utf-8") as handle:
        handle.write("\n[stuck_prompt]\nenabled = false\n")
    older = load_vault(paths.root)
    assert older.config.algorithms.algorithm_version == BEFORE_STUCK_PROMPT and not stuck_prompt_active(older)
    rebuild_all_derived_state(older, repository, clock=CLOCK)
    rebuild_all_derived_state(older, repository, clock=CLOCK)
    with connect(repository.sqlite_path, read_only=True) as connection:
        assert {row[0] for row in connection.execute("SELECT id FROM practice_attempts WHERE declared_stuck = 1")} == stuck_ids
    rows, _signals, stuck = _field(older, repository)
    assert stuck == live_stuck
    assert {row.attempt_id: row for row in rows if row.attempt_id in stuck_ids} == live_stuck_rows
    # The derived trace is what reads the declaration back: an empty stuck answer stays engaged, not a blank.
    assert _engagement_factors(repository, stuck_ids) == live_factors


def test_an_attempt_an_older_tag_wrote_replays_with_no_stuck_declaration_at_the_head(tmp_path):
    """Rows written before the prompt existed carry ``declared_stuck = 0``; replay at the head, where the prompt is
    offered, keeps them ordinary attempts (it reads the stored flag, never infers one from the empty answer)."""

    paths, vault, repository = split_vault(tmp_path, version=BEFORE_STUCK_PROMPT)
    for offset, item in ((20, "pi_svd_compute_001"), (21, "pi_transpose_001")):
        complete_self_graded_attempt(
            vault,
            repository,
            AttemptDraft(practice_item_id=item, learner_answer_md="", attempt_type="independent_attempt"),
            SelfGradeInput(criterion_points={}, confidence=3),
            clock=FrozenClock(at(offset)),
        )
    with connect(repository.sqlite_path, read_only=True) as connection:
        before = [tuple(row) for row in connection.execute("SELECT * FROM practice_attempts ORDER BY id")]
    assert len(before) >= 2

    set_algorithm_version(paths, LATEST_ALGORITHM_VERSION)
    head = load_vault(paths.root)
    assert stuck_prompt_active(head)
    rebuild_all_derived_state(head, repository, clock=CLOCK)
    with connect(repository.sqlite_path, read_only=True) as connection:
        assert [tuple(row) for row in connection.execute("SELECT * FROM practice_attempts ORDER BY id")] == before
        assert connection.execute("SELECT COUNT(*) FROM practice_attempts WHERE declared_stuck = 1").fetchone()[0] == 0
    assert _field(head, repository)[2] == []


def test_a_joint_stuck_reading_survives_rebuild_with_no_model_call(tmp_path, monkeypatch):
    """Review F3/F6: with the split off the reading lives only in its
    judgment_ledger verdict (a raw ledger), so rebuild reads it back as is."""

    _paths, vault, repository = split_vault(
        tmp_path, version=LATEST_ALGORITHM_VERSION, config="[diagnosis]\nsplit_enabled = false"
    )
    confused = StuckFake(
        reading={"attempts_answer": False, "describes_confusion": True, "confusion_quote": "where Sigma comes from"}
    )
    _grade(vault, repository, confused, _draft("I can't see where Sigma comes from"), when=20)
    live = _field(vault, repository)

    def refuse(*_args, **_kwargs):
        raise AssertionError("replay must not call a model")

    monkeypatch.setattr(transport_module, "execute_structured_operation", refuse)
    monkeypatch.setattr("learnloop.attempts.grading.execute_structured_operation", refuse)
    monkeypatch.setattr("learnloop.ai.routing.ready_client_for_task", refuse)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    _rows, signals, stuck = _field(vault, repository)
    assert stuck == live[2] and stuck[0]["describes_confusion"] is True
    assert [signal for signal in signals if signal.signal_type == "stuck_confusion"] == [
        signal for signal in live[1] if signal.signal_type == "stuck_confusion"
    ]
