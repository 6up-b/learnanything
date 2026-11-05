"""Router objective RO1 §5.3, landing ruling R1: every decision-time read of ``practice_attempts`` with a
time cutoff goes through one availability predicate (``router_objective_switches.attempt_time_sql`` in
SQL, ``known_at`` over a loaded row).

* Codex's reproductions (scoped verify 20261104-185356-AhtxsL): an exam that happened May 1 and was
  imported May 19 is not in the adaptive-difficulty frozen history card, the diagnoser's prior
  history, the confidence taps or the learner context at a May 5 cutoff, at the tag with
  ``[router_objective] available_at_reads`` on; with the switch off and below the tag it is, as in
  mvp-0.45; after the import every gate reads it, dated when it happened;
* below the tag or switched off the predicate is the predecessor's column, so every such read's SQL is
  the predecessor's text;
* :func:`test_every_time_cutoff_read_of_attempts_uses_the_predicate_or_is_allowlisted`: an upper time
  bound on ``created_at`` in any SQL that reads ``practice_attempts`` in ``src/`` either sits in a
  function that asks the predicate or is named, with its reason, on :data:`OCCURRENCE_TIME_READS`
  (outcomes, FSRS, mastery, write paths and reports keep occurrence time, spec §5.3).

Fakes only; no model call.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from learnloop.algorithm_versions import FOLLOWUP_SERVE_ALGORITHM_VERSION, INTERVAL_FACTOR_ALGORITHM_VERSION
from learnloop.clock import FrozenClock
from learnloop.goals.exam_seeding import seed_exam_attempts
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

from tests.helpers import append_config_toml, set_algorithm_version
from tests.test_exam_seeding import EXAM_DATE, _exam_vault, _outcomes

TAG = INTERVAL_FACTOR_ALGORITHM_VERSION
PREDECESSOR = FOLLOWUP_SERVE_ALGORITHM_VERSION
#: Codex's reproduction: the exam happened on May 1 and was imported on May 19 ...
IMPORTED_AT = datetime(2026, 5, 19, 15, 30, 7, tzinfo=UTC)
#: ... and a decision on May 5 could not have known it.
CUTOFF = "2026-05-05T09:00:00Z"
AFTER = "2026-05-20T00:00:00Z"
OFF = "[router_objective]\navailable_at_reads = false\n"
GATES = pytest.mark.parametrize("version, toml, sees_exam", [
    (TAG, None, False),
    (TAG, OFF, True),
    (PREDECESSOR, None, True),
], ids=["tag", "off", "below"])
LO = "lo_svd_definition"


def _seeded(tmp_path, version: str, toml: str | None):
    vault_root, _loaded, repository = _exam_vault(tmp_path)
    set_algorithm_version(VaultPaths(vault_root, load_vault(vault_root).config), version)
    if toml:
        append_config_toml(vault_root, toml)
    seed_exam_attempts(load_vault(vault_root), repository, outcomes=_outcomes(), clock=FrozenClock(IMPORTED_AT))
    return load_vault(vault_root), repository


# -- the adaptive-difficulty frozen history card (adaptive_difficulty/outside.py) -----------------------


class _View:
    """The material view's reads the card makes, over the vault's own rows (every column)."""

    def __init__(self, vault: Any, repository: Any) -> None:
        self.vault, self.repository = vault, repository

    def attempts(self, _connection: Any) -> list[dict[str, Any]]:
        with self.repository.connection() as connection:
            return [dict(row) for row in connection.execute("SELECT * FROM practice_attempts ORDER BY created_at, id")]

    def item(self, item_id: Any) -> Any:
        return self.vault.practice_items.get(str(item_id))


@GATES
def test_the_frozen_history_card_has_no_exam_before_its_import_at_the_tag(tmp_path, version, toml, sees_exam):
    from learnloop.adaptive_difficulty import outside

    vault, repository = _seeded(tmp_path, version, toml)
    item = vault.practice_items["pi_exam_q1"]
    view = _View(vault, repository)
    card = outside.history_card(vault, None, item, served_at=CUTOFF, view=view, incumbent=None, answers=True)
    if sees_exam:
        # mvp-0.45, and the switch off: the exam's result and its answer excerpt are on the card.
        assert len(card["recent_attempts"]) == 3
        assert any(entry.get("answer_excerpt") == "Half-right setup." for entry in card["recent_attempts"])
    else:
        assert card["recent_attempts"] == []
    # After the import every gate shows it, dated when it happened (it happened at noon on May 1).
    later = outside.history_card(vault, None, item, served_at=AFTER, view=view, incumbent=None, answers=True)
    assert len(later["recent_attempts"]) == 3
    assert all(entry["days_before"] == 18.5 for entry in later["recent_attempts"])


# -- the diagnoser's prior history (diagnosis/split/history.py) ------------------------------------------


@GATES
def test_the_diagnosers_prior_history_has_no_exam_before_its_import_at_the_tag(tmp_path, version, toml, sees_exam):
    from learnloop.diagnosis.split.history import AttemptRef, VaultHistoryStore

    vault, repository = _seeded(tmp_path, version, toml)
    store = VaultHistoryStore(vault, repository)
    before = AttemptRef("01ZZZZZZZZZZZZZZZZZZZZZZZZ", CUTOFF)
    prior = store.attempts_before(before, [LO])
    whole = store.attempts_before(before, None)
    if sees_exam:
        assert len(prior) == 3 and len(whole) == 3 and store.lagged_attempts(before) == 0
    else:
        # The context assembler and the snapshot export read exactly this; what the cutoff could not
        # know is disclosed as lag, like an attempt after it.
        assert prior == [] and whole == [] and store.lagged_attempts(before) == 3
    later = AttemptRef("01ZZZZZZZZZZZZZZZZZZZZZZZZ", AFTER)
    shown = store.attempts_before(later, [LO])
    assert len(shown) == 3 and all(attempt.completed_at.startswith(EXAM_DATE) for attempt in shown)


@GATES
def test_the_exam_rows_before_an_imported_target_follow_the_import(tmp_path, version, toml, sees_exam):
    """Diagnosing the import itself: its siblings from the same import are known with it."""

    from learnloop.diagnosis.split.history import VaultHistoryStore

    vault, repository = _seeded(tmp_path, version, toml)
    store = VaultHistoryStore(vault, repository)
    last = max(store.all_attempts(), key=lambda attempt: attempt.key())
    ref = store.ref(last.attempt_id)
    assert ref is not None and len(store.attempts_before(ref, None)) == 2


# -- a backdated ordinary attempt (the confidence taps, the reader's learner state) ---------------------------
#
# Exam material is withheld from these contexts and an exam import carries no tap, so the cutoff is shown
# on an ordinary answer written with a past created_at and its receipt time, as ruling R5 requires of any
# future backdating writer.


def _backdated(tmp_path, version: str, toml: str | None):
    from contextlib import closing

    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
    from learnloop.db.connection import connect

    vault, repository = _seeded(tmp_path, version, toml)
    result = complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="A backdated answer.",
                     answer_confidence=2),
        SelfGradeInput(criterion_points={"correctness": 2}, confidence=2),
        clock=FrozenClock(datetime(2026, 5, 1, 12, 0, tzinfo=UTC)))
    with closing(connect(repository.sqlite_path)) as connection:
        connection.execute("UPDATE practice_attempts SET received_at = ?, received_at_source = 'recorded' WHERE id = ?",
                           ("2026-05-19T15:30:07Z", result.attempt_id))
        connection.commit()
    return vault, repository


@GATES
def test_the_taps_before_a_cutoff_exclude_an_attempt_not_yet_known(tmp_path, version, toml, sees_exam):
    from learnloop import confidence_events

    vault, repository = _backdated(tmp_path, version, toml)
    with repository.connection() as connection:
        taps = confidence_events.taps_before(connection, CUTOFF, vault.config)
        later = confidence_events.taps_before(connection, AFTER, vault.config)
    assert taps == ([2] if sees_exam else [])
    assert later == [2]
    events = confidence_events.learner_events(vault, repository, learning_object_ids=[LO], before_iso=CUTOFF)
    assert (events is not None) is sees_exam
    assert confidence_events.learner_events(vault, repository, learning_object_ids=[LO], before_iso=AFTER)


@GATES
def test_the_readers_learner_state_excludes_an_attempt_not_yet_known(tmp_path, version, toml, sees_exam):
    from learnloop import reader_learner_state

    vault, repository = _backdated(tmp_path, version, toml)
    before = reader_learner_state._build(vault, repository, [LO], CUTOFF)
    after = reader_learner_state._build(vault, repository, [LO], AFTER)
    assert before.counts["attempts"] == (1 if sees_exam else 0)
    assert after.counts["attempts"] == 1


# -- the learner context's answer traces ------------------------------------------------------------------


@GATES
def test_the_learner_contexts_traces_exclude_an_exam_not_yet_imported(tmp_path, version, toml, sees_exam):
    from learnloop.learner_context import learning_context

    vault, repository = _seeded(tmp_path, version, toml)
    before = learning_context(vault, repository, learning_object_ids=[LO],
                              now=datetime(2026, 5, 5, 9, 0, tzinfo=UTC))
    after = learning_context(vault, repository, learning_object_ids=[LO], now=datetime(2026, 5, 20, tzinfo=UTC))
    assert bool(before["recent_answer_traces"]) is sees_exam
    assert len(after["recent_answer_traces"]) == 3


# -- the predicate: the predecessor's column below the tag or switched off ---------------------------------


@GATES
def test_the_predicate_is_the_predecessors_column_below_the_tag_or_switched_off(tmp_path, version, toml, sees_exam):
    from learnloop.router_objective_switches import AVAILABLE_AT_SQL, attempt_time_sql, known_at

    vault, repository = _seeded(tmp_path, version, toml)
    row = {"created_at": "2026-05-01T12:00:00Z", "received_at": "2026-05-19T15:30:07Z"}
    with repository.connection() as connection:
        bare = attempt_time_sql(vault.config, connection)
        aliased = attempt_time_sql(vault.config, connection, alias="a")
    if sees_exam:
        assert (bare, aliased) == ("created_at", "a.created_at")
        assert known_at(row, vault.config) == "2026-05-01T12:00:00Z"
    else:
        assert (bare, aliased) == (AVAILABLE_AT_SQL, "COALESCE(a.received_at, a.created_at)")
        assert known_at(row, vault.config) == "2026-05-19T15:30:07Z"
    # A database without the column (below migration 244) reads by the predecessor's column at any gate.
    import sqlite3

    bare_db = sqlite3.connect(":memory:")
    bare_db.execute("CREATE TABLE practice_attempts (id TEXT, created_at TEXT)")
    assert attempt_time_sql(vault.config, bare_db) == "created_at"
    assert known_at({"created_at": "2026-05-01T12:00:00Z"}, vault.config) == "2026-05-01T12:00:00Z"


# -- the structural guard -------------------------------------------------------------------------------------

SRC = Path(__file__).resolve().parents[1] / "src"
#: The predicate's two forms: a function that asks either filters by what was known at its cutoff.
PREDICATE = frozenset({"attempt_time_sql", "known_at"})
_READS_ATTEMPTS = re.compile(r"\b(?:FROM|JOIN)\s+practice_attempts\b", re.I)
#: An upper time bound on ``created_at`` (``created_at < ?``, ``<= ?``, ``? > created_at``, BETWEEN).
_UPPER_BOUND = re.compile(
    r"\bcreated_at\s*(?:<=|<(?!>))|(?:>=|>)\s*(?:\w+\.)?created_at\b|\bcreated_at\s+BETWEEN\b", re.I)

#: Reads that keep occurrence time (spec §5.3: outcomes, FSRS, mastery and reports; and write paths,
#: which label the attempt being written), each with its reason. ``(module, function)``.
OCCURRENCE_TIME_READS: dict[tuple[str, str], str] = {
    ("learnloop/db/repositories.py", "list_recent_attempts_by_practice_item"):
        "FSRS and replay: the ledger before the attempt being recomputed (before=), and a historical "
        "writer's instant (until=, serve_eligibility Q33, exam seeding)",
    ("learnloop/db/repositories.py", "count_clean_attempts_since"):
        "mastery: clean attempts that resolve a misconception, by when they happened",
    ("learnloop/db/repositories.py", "clean_attempt_ids_since"):
        "mastery: the attempts count_clean_attempts_since counts",
    ("learnloop/db/repositories.py", "followup_source_attempt"):
        "outcome: which queued follow-up an attempt answered, written with the attempt and replayed",
    ("learnloop/db/repositories.py", "session_attempt_counts"): "report: a session's own window",
    ("learnloop/db/repositories.py", "session_attempt_rows"): "report: a session's own window",
    ("learnloop/db/repositories.py", "review_session_rows"): "report: the Review surface's session spine",
    ("learnloop/db/repositories.py", "practice_attempts_for_items_before"):
        "outcome: the coldness receipt's prior administrations, written with the attempt it labels",
    ("learnloop/db/repositories.py", "_insert_learning_outcome_labels"):
        "outcome: learning-outcome labels written with the attempt",
    ("learnloop/db/stores/practice_index.py", "attempts_after"): "report: the practice index's usage join",
    ("learnloop/evsi_calibration/live_report.py", "_queue_serving_at"): "report: EVSI live calibration",
    ("learnloop/goals/goal_series.py", "_attempt_counts"):
        "report: the goal series replays the ledger as it happened at each checkpoint",
    ("learnloop/hints/report.py", "_other_assistance"): "report: the hints report",
    ("learnloop/learner/lesson_weight.py", "recorded_trajectory"):
        "outcome: the lesson check's recorded mastery updates, in the order they were applied",
    ("learnloop/learner/lesson_weight.py", "qualifying_outcomes"):
        "outcome: the cold attempts that resolve a lesson check",
    ("learnloop/placement/decisions.py", "bind_quick_check_answers"):
        "write path: binds a placement quick check's answers inside its own session window",
    ("learnloop/placement/state.py", "evaluate_independence"):
        "outcome: an attempt's independence, by the attempts that happened before it",
    ("learnloop_sidecar/handlers/sessions.py", "_session_cold_checks"): "report: a session's summary",
    ("learnloop_sidecar/handlers/sessions.py", "_session_followups_queued"): "report: a session's summary",
}


def _literal(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(part.value if isinstance(part, ast.Constant) else "{}" for part in node.values)
    return None


def _calls(function: ast.AST) -> set[str]:
    names = set()
    for node in ast.walk(function):
        if isinstance(node, ast.Call):
            names.add(node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", ""))
    return names


def _cutoff_reads() -> Iterator[tuple[str, str, int, bool]]:
    """(module, function, line, asks the predicate) for each SQL literal reading attempts with an upper
    time bound on ``created_at``."""

    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
        for node in ast.walk(tree):
            text = _literal(node)
            if text is None or isinstance(parents.get(node), ast.JoinedStr):
                continue
            if not (_READS_ATTEMPTS.search(text) and _UPPER_BOUND.search(text)):
                continue
            function: ast.AST = node
            while function in parents and not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function = parents[function]
            name = getattr(function, "name", "<module>")
            yield str(path.relative_to(SRC)), name, node.lineno, bool(_calls(function) & PREDICATE)


def test_every_time_cutoff_read_of_attempts_uses_the_predicate_or_is_allowlisted():
    reads = list(_cutoff_reads())
    unexplained = [f"{module}:{line} {function}" for module, function, line, asks in reads
                   if not asks and (module, function) not in OCCURRENCE_TIME_READS]
    assert unexplained == [], (
        "a time-cutoff read of practice_attempts neither asks router_objective_switches.attempt_time_sql / "
        "known_at nor is on OCCURRENCE_TIME_READS with its reason (RO1 §5.3, landing ruling R1)")
    # Every allowlisted read still exists and still keeps occurrence time (no stale entry).
    found = {(module, function) for module, function, _line, asks in reads if not asks}
    assert set(OCCURRENCE_TIME_READS) <= found, sorted(set(OCCURRENCE_TIME_READS) - found)


def test_the_decision_time_readers_ask_the_predicate():
    """The readers ruling R1 names, and every other decision-time one: they ask the predicate (a
    Python-side cutoff over loaded rows is not visible to the SQL scan, so these are named)."""

    expected = {
        ("learnloop/adaptive_difficulty/outside.py", "history_card"),
        ("learnloop/diagnosis/split/history.py", "_load"),
        ("learnloop/daily_plan/router_card.py", "inputs"),
        ("learnloop/daily_plan/router_card.py", "_attempts"),
        ("learnloop/daily_plan/router_card.py", "_interaction"),
        ("learnloop/confidence_events.py", "taps_before"),
        ("learnloop/confidence_events.py", "learner_events"),
        ("learnloop/learner_context.py", "_traces"),
        ("learnloop/reader_learner_state.py", "_build"),
    }
    asking = set()
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _calls(node) & PREDICATE:
                asking.add((str(path.relative_to(SRC)), node.name))
    assert expected <= asking, sorted(expected - asking)
