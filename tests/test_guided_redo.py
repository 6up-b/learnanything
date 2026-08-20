"""Guided partial redo (Fix 3) + repair-class-targeted ranking (Fix 4).

Covers: the redo context served from a stored repair selection; episode binding
of a redo on the ORIGINAL item as the primed attempt; the full funnel closing
end-to-end (primed redo → cold_retry task with a non-null repair class → cold
attempt → causal_cold_verifications receipt); and the `_rank_items` ordering
(checkpoint targeting, recent-attempt penalty).
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    SelfGradeInput,
    apply_attempt,
    complete_self_graded_attempt,
)
from learnloop.diagnosis.followups import evaluate_attempt_intervention_followup
from learnloop.diagnosis.guided_redo import (
    GuidedRedoUnavailable,
    guided_redo_available,
    start_guided_redo,
)
from learnloop.diagnosis.remediation import _rank_items, start_remediation_episode
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO, add_followup_item, create_basic_vault, seed_due_item

LO_ID = "lo_svd_definition"
ITEM = "pi_svd_define_001"
SIBLING = "pi_svd_define_002"


def failed_attempt_with_repair(
    vault,
    repository,
    attempt_id: str,
    *,
    item_id: str = ITEM,
    primed: bool = False,
    clock=None,
):
    """A wrong attempt whose grade carries one repair suggestion with a
    preserved-prefix repaired trace — the raw material of the redo."""

    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id,
                learner_answer_md="U Sigma Q",
                primed=primed,
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=0,
                criterion_points={"correctness": 0},
                evidence_rows=[
                    {
                        "id": f"ge_{attempt_id}",
                        "criterion_id": "correctness",
                        "points_awarded": 0.0,
                        "evidence": "Q was used where Q transpose was required.",
                        "notes": None,
                        "local_grader_id": "test",
                        "grader_tier": 1,
                        "created_at": NOW_ISO,
                    }
                ],
                error_attributions=[
                    GradeAttribution(
                        error_type="conceptual_slip",
                        severity=0.7,
                        evidence="The final factor is not transposed.",
                        is_misconception=True,
                        misconception_statement="Treats Q and Q transpose as identical.",
                        resolution_status="unresolved",
                        cause_scope="learner_state",
                        operation="transpose_confusion",
                        first_divergence={
                            "anchor_kind": "span",
                            "criterion_id": "correctness",
                            "quote": "Q",
                        },
                        candidate_causes=[
                            {
                                "statement": "Treats Q and Q transpose as identical.",
                                "cause_scope": "learner_state",
                                "target_ref": {
                                    "kind": "facet_capability",
                                    "facet_id": "recall",
                                    "capability": "retrieval",
                                },
                            }
                        ],
                        postdictive_claims=[
                            {"criterion_id": "correctness", "must": "not_full_credit"}
                        ],
                    )
                ],
                grader_confidence=0.9,
                confidence=4,
                manual_review_reason=None,
                feedback_md="Check the transpose on the final factor.",
                repair_suggestions=[
                    {
                        "practice_mode": "targeted_review",
                        "operator": "insert_transpose",
                        "rationale": "Preserve the factorization and repair only the transpose.",
                        "target_refs": [
                            {
                                "kind": "facet_capability",
                                "facet_id": "recall",
                                "capability": "retrieval",
                            }
                        ],
                        "expected_minutes": 2.0,
                        "answer_reveal_budget": 0.5,
                        "repaired_trace": {
                            "learner_work_prefix": "U Sigma ",
                            "repair_insertion_point": {
                                "anchor_kind": "span",
                                "criterion_id": "correctness",
                                "quote": "Q",
                                "char_start": 8,
                                "char_end": 9,
                            },
                            "minimal_edit": "replace Q with Q^T",
                            "regenerated_work": "",
                            "repaired_answer_md": "U Sigma Q^T",
                            "changed_latent_claims": [
                                "the right singular-vector factor is transposed"
                            ],
                            "changed_checkpoint_ids": [],
                        },
                    }
                ],
            ),
        ),
        clock=clock or FrozenClock(NOW),
    )


def _self_graded(vault, repository, item_id, *, clock, primed=False, points=4):
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=item_id,
            learner_answer_md="U Sigma V transpose.",
            primed=primed,
        ),
        SelfGradeInput(criterion_points={"correctness": points}, fatal_errors=[], confidence=4),
        clock=clock,
    )


def _setup(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)
    add_followup_item(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    return vault, repository


def _link_misconception(repository, failed_attempt_id: str) -> str:
    """Mint the durable misconception from the failed attempt's error event."""

    events = repository.error_events_for_attempt(failed_attempt_id)
    assert events, "the failed attempt should have minted an error event"
    misconception_id = repository.insert_misconception(
        learning_object_id=LO_ID,
        statement="Treats Q and Q transpose as identical.",
        correction_statement="The right factor is V transpose, not V.",
        facet_ids=["recall"],
        target_facet="recall",
        confused_with_facet="application",
        severity=0.8,
        source_error_event_ids=[events[0]["id"]],
        clock=FrozenClock(NOW),
    )
    repository.set_error_event_misconception(
        str(events[0]["id"]), misconception_id, clock=FrozenClock(NOW)
    )
    return misconception_id


# --- the redo context ---------------------------------------------------------


def test_guided_redo_requires_a_repair_selection(tmp_path):
    vault, repository = _setup(tmp_path)
    clean = _self_graded(vault, repository, ITEM, clock=FrozenClock(NOW))
    with pytest.raises(GuidedRedoUnavailable) as excinfo:
        start_guided_redo(vault, repository, clean.attempt_id)
    assert excinfo.value.reason == "no_repair_selection"


def test_guided_redo_serves_prefix_and_instruction(tmp_path):
    vault, repository = _setup(tmp_path)
    failed = failed_attempt_with_repair(vault, repository, "att_redo_ctx")
    redo = start_guided_redo(vault, repository, failed.attempt_id)
    assert redo["practice_item_id"] == ITEM
    assert redo["learner_work_prefix"] == "U Sigma "
    assert redo["redo_instruction"] == (
        "Preserve the factorization and repair only the transpose."
    )
    # G9: composition is always prefix + rewrite — the trace schema preserves
    # only a prefix, so the dead "mid_splice" signal is gone from the contract.
    assert "insertion_kind" not in redo
    assert redo["repair_class_id"]


# --- episode binding + the full funnel ---------------------------------------


def test_guided_redo_binds_open_episode_and_closes_the_funnel(tmp_path):
    """failed attempt → episode → guided redo (primed, SAME item) → cold_retry
    task carrying a repair class → cold attempt → causal_cold_verifications."""

    vault, repository = _setup(tmp_path)
    failed = failed_attempt_with_repair(vault, repository, "att_redo_e2e")
    misconception_id = _link_misconception(repository, failed.attempt_id)

    episode = start_remediation_episode(
        repository, misconception_id, clock=FrozenClock(NOW)
    )
    assert episode["state"] == "diagnosis"

    redo = start_guided_redo(vault, repository, failed.attempt_id)
    # The open episode is committed to the ORIGINAL item as the primed surface,
    # with an independent-surface cold item.
    assert redo["episode_id"] == episode["id"]
    bound = repository.remediation_episode(episode["id"])
    assert bound["state"] == "treatment"
    assert bound["primed_item_id"] == ITEM
    assert redo["cold_item_id"] == SIBLING
    assert bound["cold_item_id"] == SIBLING

    # The primed redo attempt (correct this time) binds to the episode and
    # schedules the delayed cold retry with the §6.2 context resolved NOW.
    primed_clock = FrozenClock(NOW + timedelta(minutes=10))
    primed = _self_graded(vault, repository, ITEM, clock=primed_clock, primed=True)
    scheduled = repository.remediation_episode(episode["id"])
    assert scheduled["state"] == "cold_scheduled"
    assert scheduled["primed_attempt_id"] == primed.attempt_id

    task = repository.active_followup_task_for_item(
        SIBLING,
        kind="cold_retry",
        at=(NOW + timedelta(days=2)).isoformat().replace("+00:00", "Z"),
    )
    assert task is not None
    context = task["context"]
    assert context["kind"] == "causal_cold_verification"
    assert context["source_attempt_id"] == primed.attempt_id
    # The clean primed attempt has no receipt of its own; the case-level
    # fallback reads the DIAGNOSING attempt's receipt.
    assert context["repair_class_id"] == redo["repair_class_id"]

    # Day +2: the cold attempt consumes the task and the verification lands.
    cold_clock = FrozenClock(NOW + timedelta(days=2))
    cold = _self_graded(vault, repository, SIBLING, clock=cold_clock)
    evaluate_attempt_intervention_followup(
        vault, repository, result=cold, clock=cold_clock
    )
    completed = repository.remediation_episode(episode["id"])
    assert completed["state"] == "completed"
    assert completed["cold_attempt_id"] == cold.attempt_id
    verification = repository.causal_cold_verification_for_attempt(cold.attempt_id)
    assert verification is not None
    assert verification["source_attempt_id"] == primed.attempt_id
    assert verification["repair_class_id"] == redo["repair_class_id"]
    assert verification["success"] is True


def test_guided_redo_establishes_episode_without_overlay(tmp_path):
    """G6 E2E: fail → guided redo DIRECTLY (no Repair overlay visit).

    An episode is established through the sanctioned entry
    (``start_remediation_episode`` → ``causal_repair_status``), the primed
    redo schedules the cold retry with a non-null repair class, and the cold
    attempt lands a ``causal_cold_verifications`` row — no dead end."""

    vault, repository = _setup(tmp_path)
    failed = failed_attempt_with_repair(vault, repository, "att_redo_direct")
    _link_misconception(repository, failed.attempt_id)

    redo = start_guided_redo(vault, repository, failed.attempt_id)
    assert redo["episode_id"] is not None
    episode = repository.remediation_episode(redo["episode_id"])
    assert episode["state"] == "treatment"
    # Durable misconceptions rank first among the attempt's case candidates.
    assert episode["case_kind"] == "misconception"
    assert episode["primed_item_id"] == ITEM
    assert redo["cold_item_id"] == SIBLING
    assert redo["repair_class_id"]

    primed = _self_graded(
        vault,
        repository,
        ITEM,
        clock=FrozenClock(NOW + timedelta(minutes=10)),
        primed=True,
    )
    scheduled = repository.remediation_episode(redo["episode_id"])
    assert scheduled["state"] == "cold_scheduled"
    assert scheduled["primed_attempt_id"] == primed.attempt_id
    task = repository.active_followup_task_for_item(
        SIBLING,
        kind="cold_retry",
        at=(NOW + timedelta(days=2)).isoformat().replace("+00:00", "Z"),
    )
    assert task is not None
    assert task["context"]["repair_class_id"] == redo["repair_class_id"]

    cold_clock = FrozenClock(NOW + timedelta(days=2))
    cold = _self_graded(vault, repository, SIBLING, clock=cold_clock)
    evaluate_attempt_intervention_followup(
        vault, repository, result=cold, clock=cold_clock
    )
    completed = repository.remediation_episode(redo["episode_id"])
    assert completed["state"] == "completed"
    verification = repository.causal_cold_verification_for_attempt(cold.attempt_id)
    assert verification is not None
    assert verification["repair_class_id"] == redo["repair_class_id"]


def test_guided_redo_establishes_diagnosis_episode_from_hypothesis(tmp_path):
    """With NO durable misconception, the hypothesis (candidate belief) case
    still establishes a diagnosis-kind episode where the causal state permits."""

    vault, repository = _setup(tmp_path)
    failed = failed_attempt_with_repair(vault, repository, "att_redo_hyp")
    redo = start_guided_redo(vault, repository, failed.attempt_id)
    assert redo["episode_id"] is not None
    episode = repository.remediation_episode(redo["episode_id"])
    assert episode["case_kind"] == "diagnosis"
    assert episode["state"] == "treatment"
    assert episode["primed_item_id"] == ITEM
    assert redo["cold_item_id"] == SIBLING


def test_primed_attempt_without_episode_records_typed_disposition(tmp_path):
    """G6 fallback: a primed attempt carrying a diagnosed repair class that
    finds NO episode leaves a typed §4.3 disposition (reason ``no_episode``)
    instead of silently dropping the repair activity."""

    vault, repository = _setup(tmp_path)
    primed = failed_attempt_with_repair(
        vault, repository, "att_primed_orphan", primed=True
    )
    outcomes = repository.causal_cold_outcomes(
        outcome="unmeasurable_no_held_out_surface"
    )
    assert len(outcomes) == 1
    outcome = outcomes[0]
    assert outcome["source_attempt_id"] == primed.attempt_id
    assert outcome["remediation_episode_id"] is None
    assert outcome["repair_class_id"]
    assert outcome["servable_opportunity"] is False
    assert outcome["detail"] == {"stage": "schedule", "reason": "no_episode"}


def test_clean_primed_attempt_without_receipt_records_nothing(tmp_path):
    """An ordinary primed attempt with no diagnosed repair class is not repair
    activity — no disposition is fabricated for it."""

    vault, repository = _setup(tmp_path)
    _self_graded(vault, repository, ITEM, clock=FrozenClock(NOW), primed=True)
    assert repository.causal_cold_outcomes() == []


def test_guided_redo_reports_case_unresolvable(tmp_path, monkeypatch):
    """G7: an episode whose case no longer resolves reports
    ``case_unresolvable`` — not ``no_independent_surface``, which would send a
    reader authoring surfaces that change nothing."""

    import learnloop.diagnosis.remediation as remediation

    vault, repository = _setup(tmp_path)
    failed = failed_attempt_with_repair(vault, repository, "att_redo_nocase")
    misconception_id = _link_misconception(repository, failed.attempt_id)
    episode = start_remediation_episode(
        repository, misconception_id, clock=FrozenClock(NOW)
    )
    monkeypatch.setattr(remediation, "episode_case", lambda repository, episode: None)
    redo = start_guided_redo(vault, repository, failed.attempt_id)
    assert redo["episode_id"] == episode["id"]
    assert redo["cold_item_id"] is None
    assert redo["cold_unmeasurable_reason"] == "case_unresolvable"


def test_feedback_reports_guided_redo_availability(tmp_path):
    """G4: the feedback bundle carries the server truth the button gates on —
    the same rule ``start_guided_redo`` enforces."""

    from learnloop_sidecar.handlers.serializers import feedback_bundle

    vault, repository = _setup(tmp_path)
    clean = _self_graded(vault, repository, ITEM, clock=FrozenClock(NOW))
    failed = failed_attempt_with_repair(vault, repository, "att_redo_avail")
    assert guided_redo_available(repository, clean.attempt_id) is False
    assert guided_redo_available(repository, failed.attempt_id) is True
    assert (
        feedback_bundle(vault, repository, clean.attempt_id)["guidedRedoAvailable"]
        is False
    )
    assert (
        feedback_bundle(vault, repository, failed.attempt_id)["guidedRedoAvailable"]
        is True
    )


def test_guided_redo_never_steals_a_sibling_committed_episode(tmp_path):
    vault, repository = _setup(tmp_path)
    failed = failed_attempt_with_repair(vault, repository, "att_redo_sib")
    misconception_id = _link_misconception(repository, failed.attempt_id)
    episode = start_remediation_episode(
        repository, misconception_id, clock=FrozenClock(NOW)
    )
    # The treatment flow committed the episode to a SIBLING primed item.
    repository.update_remediation_episode(
        episode["id"], state="treatment", primed_item_id=SIBLING,
        cold_item_id=ITEM, clock=FrozenClock(NOW),
    )
    redo = start_guided_redo(vault, repository, failed.attempt_id)
    assert redo["episode_id"] is None
    untouched = repository.remediation_episode(episode["id"])
    assert untouched["primed_item_id"] == SIBLING
    assert untouched["cold_item_id"] == ITEM


# --- Fix 4: ranking -----------------------------------------------------------


def _add_item(
    root,
    item_id: str,
    *,
    facets: list[str],
    checkpoints: list[str] | None = None,
) -> None:
    payload: dict = {
        "id": item_id,
        "learning_object_id": LO_ID,
        "subjects": None,
        "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt"],
        "evidence_facets": facets,
        "evidence_weights": {facet: 1.0 for facet in facets},
        "prompt": f"Item {item_id}.",
        "expected_answer": "A matrix factorization into U, Sigma, and V transpose.",
        "grading_rubric": {
            "max_points": 4,
            "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}],
            "fatal_errors": [],
        },
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }
    if checkpoints:
        payload["trace_contract"] = {
            "status": "available",
            "recipes": [
                {
                    "id": f"recipe_{item_id}",
                    "checkpoints": checkpoints,
                    "dependencies": {checkpoint: [] for checkpoint in checkpoints},
                }
            ],
        }
    upsert_practice_item(root, payload, clock=FrozenClock(NOW))


def _misconception(repository) -> object:
    misconception_id = repository.insert_misconception(
        learning_object_id=LO_ID,
        statement="Confuses SVD with eigendecomposition.",
        facet_ids=["recall"],
        target_facet="recall",
        clock=FrozenClock(NOW),
    )
    return repository.misconception(misconception_id)


def test_rank_items_prefers_checkpoint_covering_item(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)
    # Lower facet overlap than ITEM, but it exercises the targeted checkpoint.
    _add_item(
        vault_root, "pi_svd_trace_003", facets=["application"],
        checkpoints=["apply_transpose"],
    )
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    misconception = _misconception(repository)

    untargeted, _ = _rank_items(
        vault, repository, misconception, clock=FrozenClock(NOW)
    )
    assert [item.id for item in untargeted][0] == ITEM

    targeted, _ = _rank_items(
        vault,
        repository,
        misconception,
        target_checkpoint_ids=("apply_transpose",),
        clock=FrozenClock(NOW),
    )
    assert [item.id for item in targeted][0] == "pi_svd_trace_003"


def test_rank_items_deprioritizes_recently_attempted_item(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)
    # No facet overlap with the case at all — ITEM beats it on overlap.
    _add_item(vault_root, "pi_svd_alt_004", facets=["application"])
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    misconception = _misconception(repository)

    # ITEM's last attempt (three days ago, from seed_due_item) is stale, so its
    # facet overlap wins.
    ranked, _ = _rank_items(vault, repository, misconception, clock=FrozenClock(NOW))
    assert [item.id for item in ranked] == [ITEM, "pi_svd_alt_004"]

    # Attempted five minutes ago, the same item drops behind the fresh sibling
    # despite the better overlap — a just-answered item measures short-term
    # memory of the question, not the repair.
    repository.upsert_practice_item_state(
        ITEM,
        difficulty=5.0,
        stability=2.0,
        due_at="2026-05-20T12:00:00Z",
        last_attempt_at=(NOW - timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
        active=True,
    )
    reranked, _ = _rank_items(vault, repository, misconception, clock=FrozenClock(NOW))
    assert [item.id for item in reranked] == ["pi_svd_alt_004", ITEM]
