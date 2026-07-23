"""Requested-items scheduling floor (spec_tutor_promotion.md §4a)."""

from __future__ import annotations

from datetime import UTC, datetime

from learnloop.clock import FrozenClock
from learnloop.db.repositories import MasteryState, Repository
from learnloop.services.scheduler import ScheduledItem, build_due_queue, _apply_requested_floor
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml
from tests.helpers import create_basic_vault

NOW = datetime(2026, 5, 19, 12, 0, tzinfo=UTC)
NOW_ISO = "2026-05-19T12:00:00Z"


def _scheduled(item_id: str, reward: float) -> ScheduledItem:
    return ScheduledItem(
        practice_item_id=item_id,
        learning_object_id="lo",
        priority=reward,
        components={"selection_reward": reward},
        readiness_factor=None,
        selected_mode="short_answer",
        plain_english=[],
    )


# ── pure reorder function ────────────────────────────────────────────────────


def test_requested_item_pulled_to_front():
    queue = [_scheduled("a", 0.9), _scheduled("b", 0.5)]
    result = _apply_requested_floor(queue, ["b"], cap=1)
    assert [item.practice_item_id for item in result] == ["b", "a"]
    assert result[0].plain_english[0].startswith("requested")


def test_cap_limits_number_pulled():
    queue = [_scheduled("a", 0.9), _scheduled("b", 0.6), _scheduled("c", 0.3)]
    # Both b and c are requested (oldest-first), but cap=1 pulls only the oldest.
    result = _apply_requested_floor(queue, ["b", "c"], cap=1)
    assert [item.practice_item_id for item in result] == ["b", "a", "c"]


def test_cap_two_pulls_both_in_requested_order():
    queue = [_scheduled("a", 0.9), _scheduled("b", 0.6), _scheduled("c", 0.3)]
    # requested oldest-first is c then b -> pulled front keeps that order, not reward order.
    result = _apply_requested_floor(queue, ["c", "b"], cap=2)
    assert [item.practice_item_id for item in result] == ["c", "b", "a"]


def test_ineligible_requested_item_is_never_forced_in():
    queue = [_scheduled("a", 0.9), _scheduled("b", 0.5)]
    # "z" passed neither eligibility nor gates (not in the built queue) -> skipped.
    result = _apply_requested_floor(queue, ["z", "b"], cap=2)
    assert [item.practice_item_id for item in result] == ["b", "a"]
    assert "z" not in {item.practice_item_id for item in result}


def test_noop_when_cap_zero_or_nothing_requested():
    queue = [_scheduled("a", 0.9), _scheduled("b", 0.5)]
    assert _apply_requested_floor(queue, ["b"], cap=0) == queue
    assert _apply_requested_floor(queue, [], cap=1) == queue
    assert _apply_requested_floor(queue, ["z"], cap=1) == queue  # none eligible


# ── end-to-end wiring through build_due_queue ────────────────────────────────


def _write_item(paths, item_id: str, *, prompt: str):
    write_yaml(
        paths.practice_item_path("linear-algebra", item_id),
        {
            "schema_version": 1,
            "id": item_id,
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": prompt,
            "expected_answer": "U, Sigma, V transpose.",
            "difficulty": 0.55,
            "tags": [],
            "hints": [],
            "hint_policy": {"max_useful_hints": 0, "fsrs_rating_cap_by_hint": {}, "mastery_alpha_dampening_by_hint": {}},
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}],
                "fatal_errors": [],
            },
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )


def _promote_item(repository, *, event_suffix: str, created_practice_item_id: str):
    event_id = repository.insert_question_event(
        {
            "context": "practice",
            "practice_item_id": "pi_svd_define_001",
            "session_id": f"sess_{event_suffix}",
            "question_md": "Chase this?",
            "answer_md": "A guiding question.",
            "question_type": "mechanism",
            "facets": ["recall"],
            "hint_equivalent": True,
            "answer_status": "answered",
            "created_at": NOW_ISO,
        }
    )
    repository.insert_question_promotion(
        question_event_id=event_id,
        intent="practice",
        route="auto_apply",
        created_practice_item_id=created_practice_item_id,
        clock=FrozenClock(NOW),
    )


def _setup_floor_vault(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _write_item(paths, "pi_requested", prompt="A promoted item the learner asked to chase.")
    _write_item(paths, "pi_inactive_requested", prompt="A promoted item that is inactive.")
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id="lo_svd_definition",
            logit_mean=0.0,
            logit_variance=1.0,
            evidence_count=1,
            last_evidence_at="2026-05-16T12:00:00Z",
            algorithm_version="mvp-0.1",
            updated_at=NOW_ISO,
        )
    )
    for item_id in ("pi_svd_define_001", "pi_requested"):
        repository.upsert_practice_item_state(
            item_id, difficulty=5.0, stability=2.0, due_at="2026-05-18T12:00:00Z",
            last_attempt_at="2026-05-16T12:00:00Z", active=True, clock=clock,
        )
    # Inactive item: eligible-by-gates fails (active=False) so the floor can never
    # surface it even though it is a requested item.
    repository.upsert_practice_item_state(
        "pi_inactive_requested", difficulty=5.0, stability=2.0, due_at="2026-05-18T12:00:00Z",
        last_attempt_at="2026-05-16T12:00:00Z", active=False, clock=clock,
    )
    # Quality-penalize the requested item so it sorts BEHIND pi_svd_define_001 by
    # reward — the floor is what must pull it forward, not its own reward.
    repository.upsert_practice_item_quality_state(
        {
            "practice_item_id": "pi_requested",
            "bad_item_suspicion": 0.80,
            "evidence_count": 3,
            "suspicion_reasons": ["test_penalty"],
            "last_flagged_at": NOW_ISO,
            "algorithm_version": "mvp-0.1",
            "updated_at": NOW_ISO,
        }
    )
    _promote_item(repository, event_suffix="req", created_practice_item_id="pi_requested")
    _promote_item(repository, event_suffix="inact", created_practice_item_id="pi_inactive_requested")
    return load_vault(paths.root), repository, clock


def test_requested_item_surfaces_and_respects_gates(tmp_path):
    loaded, repository, clock = _setup_floor_vault(tmp_path)

    # Floor off: the quality-penalized requested item does NOT lead.
    loaded.config.tutor_promotion.requested_items_per_session = 0
    baseline = build_due_queue(loaded, repository, clock=clock, persist_explanations=False)
    baseline_ids = [item.practice_item_id for item in baseline]
    assert baseline_ids[0] != "pi_requested"
    assert "pi_requested" in baseline_ids
    # Ineligible (inactive) requested item is never in the queue at all.
    assert "pi_inactive_requested" not in baseline_ids

    # Floor on (cap 1): the requested item is pulled to the front.
    loaded.config.tutor_promotion.requested_items_per_session = 1
    queue = build_due_queue(loaded, repository, clock=clock, persist_explanations=False)
    ids = [item.practice_item_id for item in queue]
    assert ids[0] == "pi_requested"
    assert "pi_inactive_requested" not in ids


def test_requested_floor_honored_before_limit_slice(tmp_path):
    loaded, repository, clock = _setup_floor_vault(tmp_path)
    loaded.config.tutor_promotion.requested_items_per_session = 1
    # Even a single-item session surfaces the requested item (prefix floor before slice).
    queue = build_due_queue(loaded, repository, clock=clock, limit=1, persist_explanations=False)
    assert [item.practice_item_id for item in queue] == ["pi_requested"]


def test_stateless_requested_item_survives_eligibility(tmp_path):
    """A freshly authored requested item — no attempts, no FSRS state, no
    due_at — must still enter the queue. Previously it zeroed out at the
    priority filter before the reorder floor ran, so a vault whose only items
    were requested variants scheduled an EMPTY queue."""

    paths = create_basic_vault(tmp_path / "vault")
    _write_item(paths, "pi_fresh_variant", prompt="A just-minted harder sibling.")
    repository = Repository(paths.sqlite_path)
    # NO practice_item_state, NO mastery, NO attempts for the variant: the
    # learner-request row is its only signal.
    _promote_item(repository, event_suffix="fresh", created_practice_item_id="pi_fresh_variant")
    vault = load_vault(paths.root)
    queue = build_due_queue(vault, repository, clock=FrozenClock(NOW), persist_explanations=False)
    ids = [item.practice_item_id for item in queue]
    assert "pi_fresh_variant" in ids
    assert ids[0] == "pi_fresh_variant"
    assert queue[0].plain_english[0].startswith("requested")
