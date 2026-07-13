"""W2 learner-model & scheduler tests for tutor-question promotion.

Covers spec_tutor_promotion.md §3 G2 (claim seeding + gap-declaration signal),
§3 G3 (tutor_gap staleness). Scheduler floor lives in
tests/test_scheduler_requested_floor.py.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.mastery import initial_mastery_state_for_learning_object, logit
from learnloop.services.practice_generation import build_diagnostic_practice_plan
from learnloop.services.question_signal import (
    collect_question_signal,
    question_adjusted_uncertainty_states,
    resolve_gap_declaration_likelihood,
)
from learnloop.vault.loader import load_vault
from tests.helpers import NOW, NOW_ISO, create_basic_vault

LO_ID = "lo_svd_definition"
ITEM_ID = "pi_svd_define_001"
QUESTION_ISO = "2026-05-19T11:00:00Z"
LATER_ISO = "2026-05-19T11:30:00Z"


def _setup(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    return load_vault(vault_root), Repository(paths.sqlite_path)


def _insert_claim(repository, *, claimed_level, prior_pseudo_count=2.0, source="tutor_gap_declaration"):
    repository.insert_learner_claim(
        {
            "claim_type": "self_rating",
            "scope_type": "learning_object",
            "scope_id": LO_ID,
            "evidence_family": "recall",
            "claimed_level": claimed_level,
            "prior_pseudo_count": prior_pseudo_count,
            "source": source,
        },
        clock=FrozenClock(NOW),
    )


def _insert_gap_declaration(
    repository,
    *,
    created_at=QUESTION_ISO,
    attributed_facets=("recall",),
    question_nature="core_recall",
    question_type="clarification",
    practice_item_id=ITEM_ID,
):
    event_id = repository.insert_question_event(
        {
            "context": "practice",
            "practice_item_id": practice_item_id,
            "session_id": "sess_1",
            "question_md": "Can you unpack why the factors are orthogonal?",
            "answer_md": "Consider the geometry of the transformation.",
            "question_type": question_type,
            "facets": [],
            "hint_equivalent": True,
            "answer_status": "answered",
            "created_at": created_at,
        }
    )
    repository.insert_question_promotion(
        question_event_id=event_id,
        intent="gap",
        route="diagnostic_pending",
        attributed_facets=list(attributed_facets),
        question_nature=question_nature,
        clock=FrozenClock(NOW),
    )
    return event_id


def _insert_attempt(repository, *, attempt_id, created_at, correctness, facets=("recall",), attempt_type="independent_attempt"):
    with repository.connection() as connection:
        connection.execute(
            """
            INSERT INTO practice_attempts(
              id, practice_item_id, learning_object_id, practice_mode, attempt_type,
              learner_answer_md, hints_used, correctness, evidence_facets_json,
              created_at, session_id
            )
            VALUES (?, ?, ?, 'short_answer', ?, 'ans', 0, ?, ?, ?, 'sess_1')
            """,
            (
                attempt_id,
                ITEM_ID,
                LO_ID,
                attempt_type,
                correctness,
                '["' + '","'.join(facets) + '"]',
                created_at,
            ),
        )
        connection.commit()


def _insert_facet_recall_state(repository, facet_id, *, alpha, beta):
    total = alpha + beta
    with repository.connection() as connection:
        connection.execute(
            """
            INSERT INTO evidence_facet_recall_state(
              id, learning_object_id, facet_id, practice_item_id,
              recall_alpha, recall_beta, recall_mean, recall_variance,
              independent_evidence_mass, raw_coverage_mass, last_attempt_at,
              last_error_at, consecutive_failures, algorithm_version,
              created_at, updated_at
            )
            VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, NULL, 0, 'mvp-0.1', ?, ?)
            """,
            (
                f"facet_{facet_id}",
                LO_ID,
                facet_id,
                alpha,
                beta,
                alpha / total,
                alpha * beta / ((total**2) * (total + 1.0)),
                total - 2.0,
                total - 2.0,
                NOW_ISO,
                NOW_ISO,
                NOW_ISO,
            ),
        )
        connection.commit()


# ── claim seeding (spec §3 G2 generalization) ────────────────────────────────


def test_low_claim_now_seeds_prior(tmp_path):
    vault, repository = _setup(tmp_path)
    _insert_claim(repository, claimed_level=0.25, prior_pseudo_count=2.0)
    state = initial_mastery_state_for_learning_object(vault, repository, LO_ID, NOW_ISO)
    assert state.logit_mean == pytest.approx(logit(0.25))
    assert state.logit_variance == pytest.approx(0.5)  # 1 / max(2.0, 0.25)
    assert state.evidence_count == 0


def test_high_claim_seeds_identically_to_pre_change(tmp_path):
    vault, repository = _setup(tmp_path)
    _insert_claim(repository, claimed_level=0.9, prior_pseudo_count=4.0, source="manual_cli")
    state = initial_mastery_state_for_learning_object(vault, repository, LO_ID, NOW_ISO)
    # 0.9 is inside [0.05, 0.98] so the added clamp is a no-op: identical seeding.
    assert state.logit_mean == pytest.approx(logit(0.9))
    assert state.logit_variance == pytest.approx(0.25)


def test_very_high_claim_matches_native_logit_clamp(tmp_path):
    vault, repository = _setup(tmp_path)
    _insert_claim(repository, claimed_level=1.0, prior_pseudo_count=4.0, source="manual_cli")
    state = initial_mastery_state_for_learning_object(vault, repository, LO_ID, NOW_ISO)
    # High side stays at logit()'s native 0.98 clamp so claims > 0.95 are still
    # seeded bit-identically to the pre-change raw logit(claimed_level).
    assert state.logit_mean == pytest.approx(logit(1.0))


def test_no_claim_leaves_neutral_prior(tmp_path):
    vault, repository = _setup(tmp_path)
    state = initial_mastery_state_for_learning_object(vault, repository, LO_ID, NOW_ISO)
    assert state.logit_mean == 0.0
    assert state.logit_variance == 1.0


# ── gap-declaration signal (spec §3 G2 + §4b) ────────────────────────────────


def test_gap_declaration_bumps_facet_independent_of_question_type(tmp_path):
    vault, repository = _setup(tmp_path)
    # Non-substantive question_type + no event facets: the ordinary channel ignores
    # it entirely, but the explicit gap promotion still registers on 'recall'.
    _insert_gap_declaration(repository, question_type="clarification")
    signal = collect_question_signal(vault, repository, LO_ID, clock=FrozenClock(NOW))
    assert signal.events_by_facet == {}  # ordinary channel untouched
    assert "recall" in signal.gap_events_by_facet

    states, signal = question_adjusted_uncertainty_states(
        vault, repository, LO_ID, clock=FrozenClock(NOW)
    )
    virtual = [state for state in states if state.opened_reason == "tutor_question"]
    assert len(virtual) == 1
    ratio = signal.gap_likelihood.value
    expected_solid = (0.5 * ratio) / (0.5 * ratio + 0.5)
    assert virtual[0].hypothesis_marginal["facet_solid:recall"] == pytest.approx(expected_solid)


def test_gap_likelihood_uses_own_fallback_below_min_samples(tmp_path):
    vault, repository = _setup(tmp_path)
    _insert_gap_declaration(repository)
    resolved = resolve_gap_declaration_likelihood(repository, vault.config.tutor_promotion)
    assert resolved.source == "absolute_fallback"
    assert resolved.value == vault.config.tutor_promotion.gap_declaration_solid_likelihood_ratio
    # Distinct from the ordinary channel's fallback.
    assert resolved.value != vault.config.tutor_qa.question_solid_likelihood_ratio


def test_gap_likelihood_calibrates_from_declaration_failure_lift(tmp_path):
    vault, repository = _setup(tmp_path)
    # 12 gap declarations each followed by a failing attempt, against 12 base passes.
    for index in range(12):
        q_at = f"2026-05-19T10:{index:02d}:00Z"
        a_at = f"2026-05-19T10:{index:02d}:30Z"
        _insert_gap_declaration(repository, created_at=q_at)
        _insert_attempt(repository, attempt_id=f"att_fail_{index}", created_at=a_at, correctness=0.0)
    for index in range(12):
        _insert_attempt(
            repository, attempt_id=f"att_pass_{index}", created_at=f"2026-05-19T09:{index:02d}:00Z", correctness=1.0
        )
    resolved = resolve_gap_declaration_likelihood(repository, vault.config.tutor_promotion)
    assert resolved.source == "empirical"
    assert resolved.sample_size == 12
    assert resolved.value < vault.config.tutor_promotion.gap_declaration_solid_likelihood_ratio


def test_transfer_gap_on_solid_facet_is_skipped(tmp_path):
    vault, repository = _setup(tmp_path)
    _insert_facet_recall_state(repository, "recall", alpha=9.0, beta=1.0)  # solid (mass 8 > 0.5)
    _insert_gap_declaration(repository, question_nature="transfer")
    signal = collect_question_signal(vault, repository, LO_ID, clock=FrozenClock(NOW))
    # Frontier-boundary gap on a solid facet must not degrade core state.
    assert "recall" not in signal.gap_events_by_facet


def test_core_recall_gap_on_solid_facet_still_applies(tmp_path):
    vault, repository = _setup(tmp_path)
    _insert_facet_recall_state(repository, "recall", alpha=9.0, beta=1.0)  # solid
    _insert_gap_declaration(repository, question_nature="core_recall")
    signal = collect_question_signal(vault, repository, LO_ID, clock=FrozenClock(NOW))
    # A core_recall gap on an established facet feeds the frontier / follow-up gate.
    assert "recall" in signal.gap_events_by_facet


def test_gap_declaration_resolved_by_later_success(tmp_path):
    vault, repository = _setup(tmp_path)
    _insert_gap_declaration(repository, created_at=QUESTION_ISO)
    _insert_attempt(repository, attempt_id="att_pass", created_at=LATER_ISO, correctness=1.0)
    signal = collect_question_signal(vault, repository, LO_ID, clock=FrozenClock(NOW))
    assert signal.gap_events_by_facet == {}


def test_failed_attempt_does_not_resolve_gap_declaration(tmp_path):
    vault, repository = _setup(tmp_path)
    _insert_gap_declaration(repository, created_at=QUESTION_ISO)
    _insert_attempt(repository, attempt_id="att_fail", created_at=LATER_ISO, correctness=0.1)
    signal = collect_question_signal(vault, repository, LO_ID, clock=FrozenClock(NOW))
    assert "recall" in signal.gap_events_by_facet


# ── tutor_gap staleness (spec §3 G3) ─────────────────────────────────────────


def _file_gap_need(repository, *, created_at, target_facets=("recall",), trigger_reason="tutor_gap_declaration"):
    return repository.upsert_intervention_need(
        {
            "id": f"need_{created_at}_{trigger_reason}",
            "learning_object_id": LO_ID,
            "desired_intent": "diagnose",
            "trigger_reason": trigger_reason,
            "target_facets": list(target_facets),
            "blocked_reason": trigger_reason,
            "priority": 0.5,
            "created_at": created_at,
            "updated_at": created_at,
        }
    )


def test_gap_need_goes_stale_when_facets_succeed(tmp_path):
    vault, repository = _setup(tmp_path)
    need_id = _file_gap_need(repository, created_at="2026-05-19T09:00:00Z")
    _insert_attempt(repository, attempt_id="att_ok", created_at="2026-05-19T10:00:00Z", correctness=1.0)
    build_diagnostic_practice_plan(vault, repository, clock=FrozenClock(NOW))
    need = repository.intervention_need(need_id)
    assert need["status"] == "stale"
    assert need["blocked_reason"] == "tutor_gap_facets_resolved"


def test_gap_need_goes_stale_after_ttl(tmp_path):
    vault, repository = _setup(tmp_path)
    # 30 days before NOW; default gap_need_ttl_days is 21. No successful attempts.
    need_id = _file_gap_need(repository, created_at="2026-04-19T12:00:00Z")
    build_diagnostic_practice_plan(vault, repository, clock=FrozenClock(NOW))
    need = repository.intervention_need(need_id)
    assert need["status"] == "stale"
    assert need["blocked_reason"] == "tutor_gap_ttl:21d"


def test_gap_need_survives_before_ttl_without_success(tmp_path):
    vault, repository = _setup(tmp_path)
    need_id = _file_gap_need(repository, created_at="2026-05-14T12:00:00Z")  # 5 days old
    plan = build_diagnostic_practice_plan(vault, repository, clock=FrozenClock(NOW))
    need = repository.intervention_need(need_id)
    assert need["status"] == "pending"
    assert need_id in [target.need_id for target in plan.targets]


def test_non_gap_need_unaffected_by_gap_staleness(tmp_path):
    vault, repository = _setup(tmp_path)
    # A stale-looking (old) need whose reason neither staleness family handles.
    need_id = _file_gap_need(
        repository, created_at="2026-01-01T12:00:00Z", trigger_reason="manual_review"
    )
    build_diagnostic_practice_plan(vault, repository, clock=FrozenClock(NOW))
    need = repository.intervention_need(need_id)
    assert need["status"] == "pending"
