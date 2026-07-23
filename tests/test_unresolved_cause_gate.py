"""Unresolved-cause factors open on OBSERVED failures only (§5.3).

The calibrated E[true-score] residual under a cold grader-calibration model is
epistemic uncertainty about the measurement: it discounts certification credit
but must never fabricate a "something failed; diagnose the cause" event on a
fully-correct answer. The observed/authoritative outcome (raw criterion
fraction, overridden by an adjudicated class when an adjudication heads the
interpretation chain) is what gates unresolved-cause creation.
"""

from __future__ import annotations

import json

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import (
    AttemptDraft,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.services.canonical_projection import project_canonical_facet_state
from learnloop.services.grade_resolution import append_adjudication
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, set_algorithm_version
from tests.test_km2_write_path import build_mvp07_vault

ITEM = "pi_svd_ambiguous_001"  # one criterion, two candidate facets, no attribution

CLOCK = FrozenClock(NOW)


def _vault(tmp_path, algorithm_version="mvp-0.8"):
    paths = build_mvp07_vault(tmp_path / "vault")
    set_algorithm_version(paths, algorithm_version)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=CLOCK)
    return vault, repository


def _attempt(vault, repository, points):
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=ITEM,
            learner_answer_md="An answer.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"whole_item": points}, fatal_errors=[], confidence=4),
        clock=CLOCK,
    )


def _adjudicate(repository, attempt_id, resolved_class):
    observation = repository.observation_by_attempt(attempt_id)
    raw = repository.raw_grade_events_for_observation(observation["id"])[0]
    return append_adjudication(
        repository,
        observation_id=observation["id"],
        administration_id=observation["administration_id"],
        reviewed_raw_event_ids=[raw["id"]],
        adjudicator_source="human_owner",
        resolved_class=resolved_class,
        clock=CLOCK,
    )


def _total_certification_credit(repository):
    return sum(c.certification_credit for c in repository.facet_capability_evidence_all())


def test_full_credit_cold_calibration_opens_no_cause_factor(tmp_path):
    vault, repository = _vault(tmp_path)
    result = _attempt(vault, repository, 4)

    # The scenario really is the cold one: a soft calibrated posterior and a
    # certainty LCB strictly inside (0, 1), i.e. calibrated residual mass > 0.
    ledger = repository.canonical_observation_ledger_v2()
    interp = next(r for r in ledger if r["attempt_id"] == result.attempt_id)[
        "active_interpretation"
    ]
    posterior = json.loads(interp["response_posterior_json"])
    assert posterior["success"] < 1.0
    assert 0.0 < float(interp["shared_certainty_lcb"]) < 1.0

    # No fabricated failure to diagnose on a fully-correct answer.
    assert not repository.open_unresolved_cause_observation_ids()


def test_cold_calibration_still_discounts_certification_credit(tmp_path):
    p0_vault, p0_repository = _vault(tmp_path / "p0")
    _attempt(p0_vault, p0_repository, 4)
    p0_credit = _total_certification_credit(p0_repository)

    v1_vault, v1_repository = _vault(tmp_path / "v1", algorithm_version="mvp-0.7")
    _attempt(v1_vault, v1_repository, 4)
    raw_credit = _total_certification_credit(v1_repository)

    # Shrinkage still binds: credit accrues but stays below the raw-grade
    # baseline, without an unresolved-cause factor being minted (above).
    assert 0.0 < p0_credit < raw_credit


def test_observed_multi_facet_failure_opens_cause_factor(tmp_path):
    vault, repository = _vault(tmp_path)
    _attempt(vault, repository, 0)
    assert repository.open_unresolved_cause_observation_ids()


def test_partial_credit_observed_deduction_still_opens_factor(tmp_path):
    # Pins the deliberate `< 1.0` gate semantics: any OBSERVED deduction on an
    # unattributed multi-facet criterion is an unresolved failure, even above
    # the pass/fail FAILURE_THRESHOLD.
    vault, repository = _vault(tmp_path)
    _attempt(vault, repository, 2)
    assert repository.open_unresolved_cause_observation_ids()


def test_adjudicated_success_to_failure_opens_cause_factor(tmp_path):
    vault, repository = _vault(tmp_path)
    result = _attempt(vault, repository, 4)
    assert not repository.open_unresolved_cause_observation_ids()

    _adjudicate(repository, result.attempt_id, "other")
    project_canonical_facet_state(vault, repository, clock=CLOCK)

    # Raw points stay 4/4 (append-only), but the authoritative outcome is now a
    # failure with two candidate causes and no attribution.
    assert repository.open_unresolved_cause_observation_ids()


def test_adjudicated_failure_to_success_retires_cause_factor(tmp_path):
    vault, repository = _vault(tmp_path)
    result = _attempt(vault, repository, 0)
    assert repository.open_unresolved_cause_observation_ids()

    _adjudicate(repository, result.attempt_id, "success")
    project_canonical_facet_state(vault, repository, clock=CLOCK)

    # Raw points stay 0 (append-only), but the adjudicated outcome is a
    # success: the fabricated factor is retired by the reconciling sync.
    assert not repository.open_unresolved_cause_observation_ids()
