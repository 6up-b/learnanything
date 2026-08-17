"""Cross-channel reveal accounting (migration 154).

The hole this closes: a tutor answer given from the FEEDBACK screen could fully
restate a graded solution, and the next attempt on that same practice item was
still recorded as clean, unassisted, unprimed evidence. These tests pin the four
pieces that close it — the leak quantity, the ledger write, the context-blind
hint window, and the auto-prime forcing that the cold-retry guard must see.
"""

from __future__ import annotations

import sqlite3
from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.codex.schemas import TutorAnswer
from learnloop.db.connection import connect
from learnloop.db.migrate import apply_migrations
from learnloop.db.repositories import Repository
from learnloop.services.attempts import (
    AUTO_PRIME_REVEAL_THRESHOLD,
    AttemptDraft,
    AttemptValidationError,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.services.remediation import (
    prescribe_remediation,
    start_remediation_episode,
    start_remediation_treatment,
)
from learnloop.services.tutor_qa import (
    answer_leak_overlap,
    answer_leaks_expected,
    ask_question,
    hint_equivalents_for_submission,
)
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO, add_followup_item, create_basic_vault, seed_due_item

ITEM = "pi_svd_define_001"
LO_ID = "lo_svd_definition"
EXPECTED = "A matrix factorization into U, Sigma, and V transpose."


class FakeTutorClient:
    provider_name = "fake_tutor"
    provider_type = "fake"
    model = "fake-model"

    def __init__(self, *, question_type="mechanism", answer_md="Think about the factor shapes."):
        self.question_type = question_type
        self.answer_md = answer_md
        self.contexts = []

    def run_tutor_qa(self, context):
        self.contexts.append(context)
        return TutorAnswer(
            answer_md=self.answer_md,
            question_type=self.question_type,
            facets=list(context.candidate_facets),
        )


def _setup(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)
    vault = load_vault(vault_root)
    return vault, Repository(paths.sqlite_path)


def _attempt(vault, repository, item_id=ITEM, *, clock, primed=False, hints_used=0):
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=item_id,
            learner_answer_md="U Sigma V transpose.",
            attempt_type="independent_attempt",
            hints_used=hints_used,
            primed=primed,
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, fatal_errors=[], confidence=4),
        clock=clock,
    )


def _seed_reveal(repository, amount, *, clock, item_id=ITEM, source_kind="tutor_answer"):
    return repository.insert_reveal_event(
        {
            "practice_item_id": item_id,
            "learning_object_id": LO_ID,
            "source_kind": source_kind,
            "amount": amount,
            "basis": "test",
        },
        clock=clock,
    )


# ── (a) the leak quantity ─────────────────────────────────────────────────────


def test_answer_leak_overlap_scores_a_verbatim_restatement_as_a_full_reveal():
    assert answer_leak_overlap(f"Well, it is {EXPECTED} Does that help?", EXPECTED) == 1.0
    assert answer_leaks_expected(f"Well, it is {EXPECTED}", EXPECTED) is True


def test_answer_leak_overlap_is_a_fraction_not_a_flag():
    # Half the expected answer's content tokens present: a partial reveal, which
    # a boolean at the 0.8 threshold would have thrown away entirely.
    overlap = answer_leak_overlap(
        "The factorization produces a matrix Sigma of singular values.", EXPECTED
    )
    assert 0.0 < overlap < 1.0
    # ... and the boolean is exactly the thresholded quantity.
    assert answer_leaks_expected(
        "The factorization produces a matrix Sigma of singular values.", EXPECTED
    ) is (overlap >= 0.8)


def test_answer_leak_overlap_is_zero_when_it_cannot_be_computed():
    assert answer_leak_overlap("", EXPECTED) == 0.0
    assert answer_leak_overlap("anything at all", "") == 0.0
    # Too few content tokens to distinguish overlap from incidental vocabulary.
    assert answer_leak_overlap("the matrix is U", "U V") == 0.0


def test_answer_leak_overlap_accepts_a_structured_expected_answer():
    assert answer_leak_overlap("nothing related whatsoever", {"steps": ["one", "two"]}) < 0.8


# ── (b) feedback-context questions are scored and debited ─────────────────────


def _insert_attempt(repository, *, attempt_id="att_1", session_id="sess_1", created_at=NOW_ISO):
    with repository.connection() as connection:
        connection.execute(
            """
            INSERT INTO practice_attempts(
              id, practice_item_id, learning_object_id, practice_mode, attempt_type,
              learner_answer_md, hints_used, created_at, session_id
            )
            VALUES (?, ?, ?, 'short_answer', 'independent_attempt', 'my answer', 0, ?, ?)
            """,
            (attempt_id, ITEM, LO_ID, created_at, session_id),
        )
        connection.commit()


def test_feedback_question_is_hint_equivalent_and_writes_a_reveal_event(tmp_path):
    vault, repository = _setup(tmp_path)
    _insert_attempt(repository)
    client = FakeTutorClient(answer_md=f"The answer is: {EXPECTED}")

    result = ask_question(
        vault,
        repository,
        client,
        context="feedback",
        question_md="Why did I lose points?",
        attempt_id="att_1",
        clock=FrozenClock(NOW),
    )

    assert result["hint_equivalent"] is True
    assert result["leak_suspected"] is True
    assert result["leak_overlap"] == 1.0

    event = repository.question_event(result["event_id"])
    assert event["context"] == "feedback"
    assert event["hint_equivalent"] is True
    assert event["leak_overlap"] == 1.0
    # The session is inherited from the graded attempt so the hint window (which
    # is session-scoped) can actually see this row.
    assert event["session_id"] == "sess_1"

    reveals = repository.reveal_events(practice_item_id=ITEM)
    assert [(r["source_kind"], r["amount"]) for r in reveals] == [("tutor_answer", 1.0)]
    assert reveals[0]["question_event_id"] == result["event_id"]
    assert reveals[0]["attempt_id"] == "att_1"
    assert reveals[0]["learning_object_id"] == LO_ID


def test_reader_questions_bind_no_item_so_they_debit_nothing(tmp_path):
    vault, repository = _setup(tmp_path)
    client = FakeTutorClient()
    with pytest.raises(Exception):
        # No extraction/span: the point here is only that nothing was charged.
        ask_question(
            vault, repository, client, context="reader", question_md="?", clock=FrozenClock(NOW)
        )
    assert repository.reveal_events() == []


def test_reveal_events_are_append_only(tmp_path):
    _vault, repository = _setup(tmp_path)
    row_id = _seed_reveal(repository, 0.5, clock=FrozenClock(NOW))
    with repository.connection() as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE reveal_events SET amount = 0.1 WHERE id = ?", (row_id,))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("DELETE FROM reveal_events WHERE id = ?", (row_id,))


# ── (c) the hint window spans the feedback screen ─────────────────────────────


def test_feedback_questions_count_as_hints_for_the_next_attempt(tmp_path):
    vault, repository = _setup(tmp_path)
    clock = FrozenClock(NOW)
    first = _attempt(vault, repository, clock=clock)

    # Between attempt N and N+1 the learner opens feedback and asks a mechanism
    # question. Before migration 154 this was invisible to the submit path.
    ask_question(
        vault,
        repository,
        FakeTutorClient(),
        context="feedback",
        question_md="Why does Sigma have to be diagonal?",
        attempt_id=first.attempt_id,
        session_id="sess_1",
        clock=FrozenClock(NOW + timedelta(minutes=1)),
    )

    assert hint_equivalents_for_submission(repository, ITEM, "sess_1") == 1
    # And it is scoped: a different session's next attempt is unaffected.
    assert hint_equivalents_for_submission(repository, ITEM, "other") == 0


def test_hint_window_still_starts_at_the_previous_attempt(tmp_path):
    vault, repository = _setup(tmp_path)
    _insert_attempt(repository, attempt_id="att_old", created_at="2026-05-18T12:00:00Z")
    ask_question(
        vault,
        repository,
        FakeTutorClient(),
        context="feedback",
        question_md="Why?",
        attempt_id="att_old",
        session_id="sess_1",
        clock=FrozenClock(NOW - timedelta(days=1)),
    )
    # A newer attempt closes the window: the question above was already dampened
    # into it and must not be charged twice.
    _insert_attempt(repository, attempt_id="att_new", created_at=NOW_ISO)
    assert hint_equivalents_for_submission(repository, ITEM, "sess_1") == 0


# ── (d) auto-priming from the ledger ──────────────────────────────────────────


def test_reveal_over_threshold_forces_primed_and_records_why(tmp_path):
    vault, repository = _setup(tmp_path)
    _seed_reveal(repository, AUTO_PRIME_REVEAL_THRESHOLD + 0.05, clock=FrozenClock(NOW))

    # The client submits an ordinary, undeclared attempt.
    result = _attempt(vault, repository, clock=FrozenClock(NOW + timedelta(minutes=1)), primed=False)

    attempt = repository.fetch_practice_attempt(result.attempt_id)
    assert attempt["primed"] == 1
    debug = repository.attempt_debug_payload(result.attempt_id) or {}
    assert debug["auto_primed_reveal_total"] == pytest.approx(AUTO_PRIME_REVEAL_THRESHOLD + 0.05)


def test_reveal_under_threshold_leaves_the_attempt_unprimed(tmp_path):
    vault, repository = _setup(tmp_path)
    _seed_reveal(repository, AUTO_PRIME_REVEAL_THRESHOLD - 0.05, clock=FrozenClock(NOW))

    result = _attempt(vault, repository, clock=FrozenClock(NOW + timedelta(minutes=1)))

    attempt = repository.fetch_practice_attempt(result.attempt_id)
    assert attempt["primed"] == 0
    debug = repository.attempt_debug_payload(result.attempt_id) or {}
    assert debug["auto_primed_reveal_total"] is None


def test_reveals_accumulate_across_channels(tmp_path):
    vault, repository = _setup(tmp_path)
    # Neither channel alone crosses the line; together they do.
    _seed_reveal(repository, 0.2, clock=FrozenClock(NOW), source_kind="tutor_answer")
    _seed_reveal(repository, 0.2, clock=FrozenClock(NOW), source_kind="repair_display")

    result = _attempt(vault, repository, clock=FrozenClock(NOW + timedelta(minutes=1)))
    assert repository.fetch_practice_attempt(result.attempt_id)["primed"] == 1


def test_reveals_before_the_last_attempt_do_not_prime_the_next_one(tmp_path):
    vault, repository = _setup(tmp_path)
    _seed_reveal(repository, 1.0, clock=FrozenClock(NOW))
    first = _attempt(vault, repository, clock=FrozenClock(NOW + timedelta(minutes=1)))
    assert repository.fetch_practice_attempt(first.attempt_id)["primed"] == 1

    # The exposure was already absorbed by the attempt above; the window moves.
    second = _attempt(vault, repository, clock=FrozenClock(NOW + timedelta(minutes=5)))
    assert repository.fetch_practice_attempt(second.attempt_id)["primed"] == 0


def test_a_tutor_answer_that_gives_the_solution_primes_the_next_attempt(tmp_path):
    """End to end, the exact trace the audit found."""

    vault, repository = _setup(tmp_path)
    first = _attempt(vault, repository, clock=FrozenClock(NOW))
    ask_question(
        vault,
        repository,
        FakeTutorClient(answer_md=f"Sure — {EXPECTED}"),
        context="feedback",
        question_md="So what was the answer?",
        attempt_id=first.attempt_id,
        session_id="sess_1",
        clock=FrozenClock(NOW + timedelta(minutes=1)),
    )

    second = _attempt(vault, repository, clock=FrozenClock(NOW + timedelta(minutes=2)))
    attempt = repository.fetch_practice_attempt(second.attempt_id)
    assert attempt["primed"] == 1


def test_an_auto_primed_attempt_replays_as_primed(tmp_path):
    """Replay reads what was recorded; it must not re-derive from the ledger.

    By replay time the window has moved past the reveal, so a re-derivation
    would quietly turn a primed attempt back into clean evidence."""

    from learnloop.services.attempts import replay_existing_attempt

    vault, repository = _setup(tmp_path)
    _seed_reveal(repository, 0.9, clock=FrozenClock(NOW))
    result = _attempt(vault, repository, clock=FrozenClock(NOW + timedelta(minutes=1)))
    assert repository.fetch_practice_attempt(result.attempt_id)["primed"] == 1

    stored = repository.fetch_practice_attempt(result.attempt_id)
    replay_existing_attempt(
        vault, repository, stored, clock=FrozenClock(NOW + timedelta(days=30))
    )

    replayed = repository.fetch_practice_attempt(result.attempt_id)
    assert replayed["primed"] == 1
    debug = repository.attempt_debug_payload(result.attempt_id) or {}
    assert debug["primed"] is True
    assert debug["auto_primed_reveal_total"] == pytest.approx(0.9)


# ── (e) the cold-retry guard sees the forced value ────────────────────────────


def _drive_to_cold_scheduled(vault, repository):
    misconception_id = repository.insert_misconception(
        learning_object_id=LO_ID,
        statement="Confuses SVD with eigendecomposition.",
        correction_statement="SVD applies to any matrix.",
        facet_ids=["recall"],
        target_facet="recall",
        confused_with_facet="application",
        severity=0.8,
        clock=FrozenClock(NOW),
    )
    episode = start_remediation_episode(repository, misconception_id, clock=FrozenClock(NOW))
    prescribe_remediation(vault, repository, episode["id"], clock=FrozenClock(NOW))
    treatment = start_remediation_treatment(vault, repository, episode["id"], clock=FrozenClock(NOW))
    _attempt(
        vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True
    )
    return repository.remediation_episode(episode["id"]), treatment["cold_item_id"]


def test_a_revealed_cold_item_cannot_burn_its_cold_measurement(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)
    add_followup_item(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)

    episode, cold_item = _drive_to_cold_scheduled(vault, repository)
    assert episode["state"] == "cold_scheduled"
    due = FrozenClock(NOW + timedelta(days=1))

    # The learner reads the answer off some surface, then submits the cold retry
    # as if it were clean. The forcing runs BEFORE the guard, so the guard sees
    # a primed attempt and refuses rather than recording a false cold success.
    _seed_reveal(repository, 0.9, clock=due, item_id=cold_item)
    with pytest.raises(AttemptValidationError, match="unassisted and unprimed"):
        _attempt(vault, repository, cold_item, clock=due)

    # Nothing was consumed: the opportunity survives for an honest retry.
    task = repository.active_followup_task_for_item(
        cold_item, at=(NOW + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    assert task is not None and task["status"] != "consumed"


def test_a_reveal_inside_a_live_repair_is_attributed_to_its_episode(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)
    add_followup_item(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    episode, cold_item = _drive_to_cold_scheduled(vault, repository)

    _insert_attempt(repository, attempt_id="att_cold")
    with repository.connection() as connection:
        connection.execute(
            "UPDATE practice_attempts SET practice_item_id = ? WHERE id = 'att_cold'",
            (cold_item,),
        )
        connection.commit()

    result = ask_question(
        vault,
        repository,
        FakeTutorClient(answer_md=f"It is {EXPECTED}"),
        context="feedback",
        question_md="What was it?",
        attempt_id="att_cold",
        clock=FrozenClock(NOW + timedelta(hours=1)),
    )
    assert result["remediation_episode_id"] == episode["id"]
    reveal = repository.reveal_events(practice_item_id=cold_item)[0]
    assert reveal["remediation_episode_id"] == episode["id"]
    assert repository.reveal_events(remediation_episode_id=episode["id"])


# ── repair-display debits ─────────────────────────────────────────────────────


def _seed_graded_attempt_with_repairs(repository, budgets):
    _insert_attempt(repository)
    repository.upsert_attempt_feedback_metadata(
        attempt_id="att_1",
        grading_source="ai",
        feedback_md="Here is what went wrong.",
        repair_suggestions=[
            {"id": f"rc_{index}", "operator": "targeted_repair", "answer_reveal_budget": budget}
            for index, budget in enumerate(budgets)
        ],
        clock=FrozenClock(NOW),
    )


def test_repair_display_budget_debits_the_ledger_once_per_attempt(tmp_path):
    """A declared `answer_reveal_budget` used to debit nothing anywhere."""

    from learnloop_sidecar.handlers.feedback import _debit_repair_display_reveals

    vault, repository = _setup(tmp_path)
    _seed_graded_attempt_with_repairs(repository, [0.4, 0.0])
    attempt = repository.fetch_practice_attempt("att_1")
    stored = repository.fetch_attempt_feedback_metadata("att_1")

    _debit_repair_display_reveals(vault, repository, attempt, stored)

    reveals = repository.reveal_events(source_kind="repair_display")
    # Only the suggestion that declared a budget is charged.
    assert [(r["amount"], r["basis"]) for r in reveals] == [(0.4, "repair_display:rc_0")]
    assert reveals[0]["attempt_id"] == "att_1"
    assert reveals[0]["learning_object_id"] == LO_ID


def test_reopening_feedback_does_not_charge_again(tmp_path):
    import io
    import json

    from learnloop_sidecar.server import serve

    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)
    repository = Repository(paths.sqlite_path)
    _seed_graded_attempt_with_repairs(repository, [0.5])

    def _get_feedback():
        messages = [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"vaultPath": str(vault_root)},
            },
            {"jsonrpc": "2.0", "id": 2, "method": "get_feedback", "params": {"attemptId": "att_1"}},
        ]
        stdin = io.StringIO("".join(json.dumps(m) + "\n" for m in messages))
        stdout = io.StringIO()
        serve(stdin, stdout)
        return [json.loads(line) for line in stdout.getvalue().splitlines()]

    assert "result" in _get_feedback()[1]
    assert len(repository.reveal_events(source_kind="repair_display")) == 1
    # Re-reading the same suggestions reveals nothing new; charging every reopen
    # would make an attentive learner look contaminated.
    assert "result" in _get_feedback()[1]
    assert len(repository.reveal_events(source_kind="repair_display")) == 1


# ── (f) the migration ─────────────────────────────────────────────────────────


def test_migration_154_adds_the_ledger_and_the_question_event_columns(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path)
    with connect(sqlite_path) as connection:
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        assert "reveal_events" in tables
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(question_events)")
        }
        assert {"leak_overlap", "remediation_episode_id"} <= columns
        triggers = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'trigger' "
                "AND tbl_name = 'reveal_events'"
            )
        }
        assert triggers == {"reveal_events_no_update", "reveal_events_no_delete"}
        # The 0..1 contract is enforced by the schema, not only by callers.
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO reveal_events(id, practice_item_id, source_kind, amount, created_at) "
                "VALUES ('r1', 'pi', 'tutor_answer', 1.5, ?)",
                (NOW_ISO,),
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO reveal_events(id, practice_item_id, source_kind, amount, created_at) "
                "VALUES ('r2', 'pi', 'not_a_channel', 0.5, ?)",
                (NOW_ISO,),
            )
