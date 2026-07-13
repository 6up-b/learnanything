from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.codex.schemas import TutorAnswer
from learnloop.db.repositories import Repository
from learnloop.services.facet_diagnostics import mastery_diagnostic_view
from learnloop.services.tutor_qa import (
    QuestionLimitReached,
    TutorQAError,
    answer_leaks_expected,
    ask_question,
    hint_equivalents_for_submission,
    question_usage,
)
from learnloop.vault.loader import add_note, load_vault
from tests.helpers import NOW, NOW_ISO, create_basic_vault

YESTERDAY_ISO = "2026-05-18T12:00:00Z"


class FakeTutorClient:
    provider_name = "fake_tutor"
    provider_type = "fake"
    model = "fake-model"

    def __init__(self, *, question_type="mechanism", answer_md="Think about the factor shapes.", facets=None):
        self.question_type = question_type
        self.answer_md = answer_md
        self.facets = facets
        self.contexts = []

    def run_tutor_qa(self, context):
        self.contexts.append(context)
        facets = self.facets if self.facets is not None else list(context.candidate_facets)
        return TutorAnswer(answer_md=self.answer_md, question_type=self.question_type, facets=facets)


def _setup(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    return vault_root, vault, repository


def _insert_attempt(repository, *, attempt_id="att_1", session_id="sess_1", created_at=NOW_ISO):
    with repository.connection() as connection:
        connection.execute(
            """
            INSERT INTO practice_attempts(
              id, practice_item_id, learning_object_id, practice_mode, attempt_type,
              learner_answer_md, hints_used, created_at, session_id
            )
            VALUES (?, 'pi_svd_define_001', 'lo_svd_definition', 'short_answer',
                    'independent_attempt', 'my answer', 0, ?, ?)
            """,
            (attempt_id, created_at, session_id),
        )
        connection.commit()


# ── repository ────────────────────────────────────────────────────────────────


def test_question_event_repository_round_trip(tmp_path):
    _root, _vault, repository = _setup(tmp_path)
    clock = FrozenClock(NOW)

    event_id = repository.insert_question_event(
        {
            "context": "practice",
            "practice_item_id": "pi_svd_define_001",
            "session_id": "sess_1",
            "question_md": "Why orthogonal?",
            "answer_md": "Consider the geometry.",
            "question_type": "mechanism",
            "facets": ["recall"],
            "hint_equivalent": True,
            "leak_suspected": False,
            "seconds_into_attempt": 12.5,
            "provider": "fake_tutor",
        },
        clock=clock,
    )

    events = repository.question_events(context="practice", practice_item_id="pi_svd_define_001")
    assert len(events) == 1
    event = events[0]
    assert event["id"] == event_id
    assert event["facets"] == ["recall"]
    assert event["hint_equivalent"] is True
    assert event["leak_suspected"] is False
    assert event["rating"] is None
    assert event["created_at"] == NOW_ISO
    assert event["seconds_into_attempt"] == 12.5

    assert repository.count_question_events(context="practice", practice_item_id="pi_svd_define_001") == 1
    assert repository.count_question_events(context="library") == 0

    assert repository.set_question_event_rating(event_id, useful=True)
    assert repository.question_event(event_id)["rating"] == 1
    assert repository.set_question_event_rating(event_id, useful=False)
    assert repository.question_event(event_id)["rating"] == 0
    assert not repository.set_question_event_rating("missing", useful=True)

    assert repository.question_counts_by_facet() == {"recall": 1}


def test_hint_equivalent_count_windows(tmp_path):
    _root, _vault, repository = _setup(tmp_path)
    repository.insert_question_event(
        {
            "context": "practice",
            "practice_item_id": "pi_svd_define_001",
            "session_id": "sess_1",
            "question_md": "early question",
            "question_type": "strategy",
            "hint_equivalent": True,
            "created_at": "2026-05-19T11:00:00Z",
        }
    )
    repository.insert_question_event(
        {
            "context": "practice",
            "practice_item_id": "pi_svd_define_001",
            "session_id": "sess_1",
            "question_md": "late question",
            "question_type": "mechanism",
            "hint_equivalent": True,
            "created_at": "2026-05-19T13:00:00Z",
        }
    )
    # Non-substantive questions never count.
    repository.insert_question_event(
        {
            "context": "practice",
            "practice_item_id": "pi_svd_define_001",
            "session_id": "sess_1",
            "question_md": "what does the prompt mean?",
            "question_type": "clarification",
            "hint_equivalent": False,
            "created_at": "2026-05-19T13:30:00Z",
        }
    )

    assert (
        repository.count_hint_equivalent_question_events("pi_svd_define_001", "sess_1") == 2
    )
    assert (
        repository.count_hint_equivalent_question_events(
            "pi_svd_define_001", "sess_1", since="2026-05-19T12:00:00Z"
        )
        == 1
    )
    assert (
        repository.count_hint_equivalent_question_events(
            "pi_svd_define_001", "sess_1", until="2026-05-19T12:00:00Z"
        )
        == 1
    )
    assert repository.count_hint_equivalent_question_events("pi_svd_define_001", "other") == 0


def test_hint_equivalents_for_submission_window_starts_at_last_attempt(tmp_path):
    _root, _vault, repository = _setup(tmp_path)
    # Attempt at NOW; question asked before it (already dampened into it).
    _insert_attempt(repository, attempt_id="att_prev", created_at=NOW_ISO)
    repository.insert_question_event(
        {
            "context": "practice",
            "practice_item_id": "pi_svd_define_001",
            "session_id": "sess_1",
            "question_md": "asked before the previous attempt",
            "question_type": "mechanism",
            "hint_equivalent": True,
            "created_at": "2026-05-19T11:59:00Z",
        }
    )
    assert hint_equivalents_for_submission(repository, "pi_svd_define_001", "sess_1") == 0

    repository.insert_question_event(
        {
            "context": "practice",
            "practice_item_id": "pi_svd_define_001",
            "session_id": "sess_1",
            "question_md": "asked after the previous attempt",
            "question_type": "mechanism",
            "hint_equivalent": True,
            "created_at": "2026-05-19T12:30:00Z",
        }
    )
    assert hint_equivalents_for_submission(repository, "pi_svd_define_001", "sess_1") == 1


# ── service ───────────────────────────────────────────────────────────────────


def test_ask_question_classifies_and_marks_hint_equivalents(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    clock = FrozenClock(NOW)

    substantive = ask_question(
        vault,
        repository,
        FakeTutorClient(question_type="mechanism"),
        context="practice",
        question_md="Why are U and V orthogonal?",
        practice_item_id="pi_svd_define_001",
        session_id="sess_1",
        seconds_into_attempt=30.0,
        clock=clock,
    )
    assert substantive["question_type"] == "mechanism"
    assert substantive["facets"] == ["recall"]
    assert substantive["hint_equivalent"] is True
    assert substantive["leak_suspected"] is False
    assert substantive["remaining"] == 2

    clarifying = ask_question(
        vault,
        repository,
        FakeTutorClient(question_type="clarification"),
        context="practice",
        question_md="What does 'define' mean here?",
        practice_item_id="pi_svd_define_001",
        session_id="sess_1",
        clock=clock,
    )
    assert clarifying["hint_equivalent"] is False
    assert clarifying["remaining"] == 1

    events = repository.question_events(context="practice", practice_item_id="pi_svd_define_001")
    assert [event["hint_equivalent"] for event in events] == [True, False]
    assert events[0]["provider"] == "fake_tutor"
    assert events[0]["seconds_into_attempt"] == 30.0


def test_ask_question_drops_facets_outside_candidates(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    result = ask_question(
        vault,
        repository,
        FakeTutorClient(facets=["recall", "made_up_facet"]),
        context="practice",
        question_md="Why?",
        practice_item_id="pi_svd_define_001",
        session_id="sess_1",
        clock=FrozenClock(NOW),
    )
    assert result["facets"] == ["recall"]


def test_ask_question_enforces_practice_limit(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    clock = FrozenClock(NOW)
    client = FakeTutorClient()
    for _ in range(3):
        ask_question(
            vault,
            repository,
            client,
            context="practice",
            question_md="Why?",
            practice_item_id="pi_svd_define_001",
            session_id="sess_1",
            clock=clock,
        )
    with pytest.raises(QuestionLimitReached) as excinfo:
        ask_question(
            vault,
            repository,
            client,
            context="practice",
            question_md="One more?",
            practice_item_id="pi_svd_define_001",
            session_id="sess_1",
            clock=clock,
        )
    assert excinfo.value.limit == 3
    assert excinfo.value.used == 3

    # A different session has its own budget.
    other = ask_question(
        vault,
        repository,
        client,
        context="practice",
        question_md="Why?",
        practice_item_id="pi_svd_define_001",
        session_id="sess_2",
        clock=clock,
    )
    assert other["remaining"] == 2


def test_ask_question_feedback_limit_and_intervention_wiring(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    clock = FrozenClock(NOW)
    _insert_attempt(repository, attempt_id="att_1")
    need_id = repository.upsert_intervention_need(
        {
            "attempt_id": "att_1",
            "learning_object_id": "lo_svd_definition",
            "practice_item_id": "pi_svd_define_001",
            "desired_intent": "diagnose",
            "trigger_reason": "test",
            "target_facets": [],
            "error_types": [],
            "priority": 0.5,
            "status": "pending",
            "blocked_reason": "no_suitable_item",
            "candidate_requirements": {},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        }
    )

    client = FakeTutorClient(question_type="mechanism")
    result = ask_question(
        vault,
        repository,
        client,
        context="feedback",
        question_md="Why did I lose points?",
        attempt_id="att_1",
        clock=clock,
    )
    # Feedback questions never count as hints and derive the item from the attempt.
    assert result["hint_equivalent"] is False
    assert result["remaining"] == 4
    # The graded attempt is threaded into the AI context.
    assert client.contexts[0].learner_answer_md == "my answer"
    assert client.contexts[0].context == "feedback"

    need = repository.intervention_need_for_attempt("att_1")
    assert need["id"] == need_id
    assert need["target_facets"] == ["recall"]

    for _ in range(4):
        ask_question(
            vault,
            repository,
            client,
            context="feedback",
            question_md="More?",
            attempt_id="att_1",
            clock=clock,
        )
    with pytest.raises(QuestionLimitReached):
        ask_question(
            vault,
            repository,
            client,
            context="feedback",
            question_md="Over the limit",
            attempt_id="att_1",
            clock=clock,
        )


def test_ask_question_library_context_and_daily_limit(tmp_path):
    vault_root, vault, repository = _setup(tmp_path)
    add_note(
        vault_root,
        "linear-algebra",
        "note_svd_intro",
        "SVD intro",
        "SVD factorizes any matrix into rotations and scalings.",
        related_los=["lo_svd_definition"],
        clock=FrozenClock(NOW),
    )
    vault = load_vault(vault_root)
    clock = FrozenClock(NOW)
    client = FakeTutorClient(question_type="prerequisite")

    result = ask_question(
        vault,
        repository,
        client,
        context="library",
        question_md="What is an orthogonal matrix?",
        note_id="note_svd_intro",
        clock=clock,
    )
    # Library candidates come from the note's related LOs' required facets.
    assert result["facets"] == ["recall"]
    # Library questions are never hint equivalents.
    assert result["hint_equivalent"] is False
    assert result["remaining"] == 7
    assert "# SVD intro" in client.contexts[0].note_body

    # Yesterday's questions do not count against today's budget.
    repository.insert_question_event(
        {
            "context": "library",
            "note_id": "note_svd_intro",
            "question_md": "old question",
            "created_at": YESTERDAY_ISO,
        }
    )
    used, limit = question_usage(
        vault, repository, context="library", note_id="note_svd_intro", clock=clock
    )
    assert (used, limit) == (1, 8)


def test_ask_question_leak_check_flags_expected_answer(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    leaked = ask_question(
        vault,
        repository,
        FakeTutorClient(
            answer_md="It is a matrix factorization into U, Sigma, and V transpose."
        ),
        context="practice",
        question_md="Just tell me the answer",
        practice_item_id="pi_svd_define_001",
        session_id="sess_1",
        clock=FrozenClock(NOW),
    )
    assert leaked["leak_suspected"] is True
    event = repository.question_events(context="practice", practice_item_id="pi_svd_define_001")[0]
    assert event["leak_suspected"] is True


def test_answer_leaks_expected_heuristics():
    expected = "A matrix factorization into U, Sigma, and V transpose."
    assert answer_leaks_expected("the answer is: a matrix factorization into u, sigma, and v transpose!", expected)
    assert answer_leaks_expected(
        "Recall that any matrix admits a factorization into U, Sigma and V transpose factors.", expected
    )
    assert not answer_leaks_expected("Think about what orthogonality buys you.", expected)
    assert not answer_leaks_expected("", expected)


def test_ask_question_validation_errors(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    client = FakeTutorClient()
    with pytest.raises(TutorQAError):
        ask_question(vault, repository, client, context="practice", question_md="Why?")
    with pytest.raises(TutorQAError):
        ask_question(vault, repository, client, context="library", question_md="Why?")
    with pytest.raises(TutorQAError):
        ask_question(vault, repository, client, context="feedback", question_md="Why?")
    with pytest.raises(TutorQAError):
        ask_question(
            vault,
            repository,
            client,
            context="practice",
            question_md="   ",
            practice_item_id="pi_svd_define_001",
        )
    with pytest.raises(TutorQAError):
        ask_question(vault, repository, client, context="nope", question_md="Why?")


def test_practice_prompt_context_carries_guardrail_grounding(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    client = FakeTutorClient()
    ask_question(
        vault,
        repository,
        client,
        context="practice",
        question_md="First question",
        practice_item_id="pi_svd_define_001",
        session_id="sess_1",
        clock=FrozenClock(NOW),
    )
    ask_question(
        vault,
        repository,
        client,
        context="practice",
        question_md="Second question",
        practice_item_id="pi_svd_define_001",
        session_id="sess_1",
        clock=FrozenClock(NOW),
    )
    first, second = client.contexts
    assert first.practice_item_prompt == "Define SVD."
    assert first.candidate_facets == ["recall"]
    assert first.thread == []
    # Multi-turn: the second call sees the first Q&A as prior conversation.
    assert len(second.thread) == 1
    assert second.thread[0]["question_md"] == "First question"


def test_diagnostic_decision_attaches_after_probe_transition(tmp_path):
    """§12.1: the persisted typed decision steers post-diagnosis tutoring —
    attached once the LO's episode has closed, suppressed mid-measurement."""

    _root, vault, repository = _setup(tmp_path)
    clock = FrozenClock(NOW)
    decision = {
        "diagnosed_gap": "confuses_with:eigendecomposition",
        "tutor_move": "contrast_cases",
        "instructional_intent": "repair",
        "scaffold_level": 0.5,
        "answer_reveal_budget": 1,
        "target_facets": ["recall"],
    }
    episode_id = repository.insert_probe_episode(
        learning_object_id="lo_svd_definition",
        status="converted_to_tutoring",
        trigger="manual",
        hypothesis_set_id=None,
        active_state_segment_id=None,
        algorithm_version="test",
        target_decision=decision,
        clock=clock,
    )

    client = FakeTutorClient()
    ask_question(
        vault,
        repository,
        client,
        context="practice",
        question_md="What should I work on?",
        practice_item_id="pi_svd_define_001",
        session_id="sess_1",
        clock=clock,
    )
    assert client.contexts[0].diagnostic_decision is not None
    assert client.contexts[0].diagnostic_decision["tutor_move"] == "contrast_cases"

    # A newly opened episode means measurement is live again: the decision
    # must NOT attach (it would lift the no-reveal guardrail mid-block).
    repository.insert_probe_episode(
        learning_object_id="lo_svd_definition",
        status="in_progress",
        trigger="manual",
        hypothesis_set_id=None,
        active_state_segment_id=None,
        algorithm_version="test",
        clock=clock,
    )
    ask_question(
        vault,
        repository,
        client,
        context="practice",
        question_md="And now?",
        practice_item_id="pi_svd_define_001",
        session_id="sess_1",
        clock=clock,
    )
    assert client.contexts[1].diagnostic_decision is None
    assert repository.probe_episode(episode_id) is not None


# ── read-side uncertainty adjustment ──────────────────────────────────────────


def test_question_raises_diagnostic_uncertainty_read_side(tmp_path):
    _root, vault, repository = _setup(tmp_path)
    clock = FrozenClock(NOW)

    before = mastery_diagnostic_view(vault, repository, "lo_svd_definition", clock=clock)
    recall_before = next(f for f in before["facets"] if f["facet_id"] == "recall")
    assert recall_before["state"] == "unexamined"
    assert recall_before["uncertainty"] is None
    assert recall_before["question_uncertainty_bump"] == 0.0

    ask_question(
        vault,
        repository,
        FakeTutorClient(question_type="mechanism"),
        context="practice",
        question_md="Why orthogonal?",
        practice_item_id="pi_svd_define_001",
        session_id="sess_1",
        clock=clock,
    )

    after = mastery_diagnostic_view(vault, repository, "lo_svd_definition", clock=clock)
    recall_after = next(f for f in after["facets"] if f["facet_id"] == "recall")
    assert recall_after["state"] == "uncertain"
    assert recall_after["uncertainty"] == pytest.approx(0.15)
    assert recall_after["recent_question_count"] == 1
    # Mastery mean is never touched by questions.
    assert after["mastery_mean"] == before["mastery_mean"]

    # The bump is bounded: many questions cap at 3 x mass.
    for session in ("sess_2", "sess_3", "sess_4", "sess_5"):
        for _ in range(3):
            repository.insert_question_event(
                {
                    "context": "practice",
                    "practice_item_id": "pi_svd_define_001",
                    "session_id": session,
                    "question_md": "again?",
                    "question_type": "mechanism",
                    "facets": ["recall"],
                    "hint_equivalent": True,
                    "created_at": NOW_ISO,
                }
            )
    bounded = mastery_diagnostic_view(vault, repository, "lo_svd_definition", clock=clock)
    recall_bounded = next(f for f in bounded["facets"] if f["facet_id"] == "recall")
    assert recall_bounded["uncertainty"] == pytest.approx(0.45)

    # Config switch disables the effect entirely.
    vault.config.tutor_qa.apply_uncertainty_effect = False
    disabled = mastery_diagnostic_view(vault, repository, "lo_svd_definition", clock=clock)
    recall_disabled = next(f for f in disabled["facets"] if f["facet_id"] == "recall")
    assert recall_disabled["state"] == "unexamined"
    assert recall_disabled["uncertainty"] is None
