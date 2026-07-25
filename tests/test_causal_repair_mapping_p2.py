"""P2 repair-class mapping: the second inert lane (contract §10b).

``repair_class_id`` is the ONLY vocabulary allowed to say that two plausible
causes need different help — facets are the vocabulary under indictment (§5.3,
principle 8). With the facet fallback removed from ``probe_targeting``, a
cause-set discrimination probe can only ever fire if something actually fills
that field, so these tests run the whole path through ``apply_attempt`` rather
than hand-built dicts: hand-built dicts are precisely how the dead code passed
review the first time.

What they pin:

* an authored divergent episode really does reach ``divergent`` end to end, with
  ``repair_class_id`` on the ``causal_hypotheses`` row, on the hydrated cause
  row, in the receipt, and in ``probe_priority``'s selected target;
* a repair declared by criterion id maps to a cause declared by facet ref (the
  grading contract lets the model use either sub-vocabulary);
* the paths that genuinely cannot resolve a class record a TYPED reason and
  route to the machine-side backfill, never to a learner probe;
* the near-clone verdict on a cold verification carries its basis;
* the cause-row open-set id and the probe-set open-set label are different
  namespaces and neither pretends to be the other.
"""

from __future__ import annotations

import json
from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    apply_attempt,
    complete_self_graded_attempt,
    SelfGradeInput,
)
from learnloop.services.causal_attribution import (
    OPEN_SET_CAUSE_ID,
    REPAIR_MAPPING_BASIS_CRITERION_REF,
    REPAIR_MAPPING_BASIS_OPEN_SET,
    REPAIR_MAPPING_BASIS_TARGET_REF,
    REPAIR_MAPPING_BASIS_UNRESOLVED,
    REPAIR_MAPPING_UNRESOLVED_REASONS,
)
from learnloop.services.causal_probe_coherence import (
    build_causal_hypothesis_set,
    record_delayed_cold_verification,
)
from learnloop.services.probe_hypotheses import H_OTHER
from learnloop.services.probe_targeting import (
    CAUSE_SET_DIVERGENT,
    CAUSE_SET_INCOMPLETE_MAPPING,
    classify_cause_set,
    probe_priority,
    repair_mapping_backfills,
)
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO, add_followup_item, create_basic_vault
from tests.test_km2_write_path import SELECT, SHARED, _attempt, build_mvp07_vault

FACTORIZATION_REF = {
    "kind": "facet_capability",
    "facet_id": SHARED,
    "capability": "retrieval",
}
APPLICABILITY_REF = {
    "kind": "facet_capability",
    "facet_id": SELECT,
    "capability": "method_selection",
}


def _mvp07(tmp_path):
    paths = build_mvp07_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return vault, repository


def _ambiguous_failure(
    vault,
    repository,
    *,
    attempt_id,
    candidate_causes,
    repair_suggestions,
    target_criterion_ids=(),
):
    """A wrong answer on the ambiguous whole-item rubric, graded like the model
    grades: an unresolved attribution with several thin candidate causes plus
    whatever repairs the grader was able to propose."""

    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id="pi_svd_ambiguous_001",
                learner_answer_md="Something went wrong here.",
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=0,
                criterion_points={"whole_item": 0},
                evidence_rows=[
                    {
                        "id": f"ge_{attempt_id}",
                        "criterion_id": "whole_item",
                        "points_awarded": 0.0,
                        "evidence": "The answer is not the factorization.",
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
                        evidence="Cannot localize the failure from this answer.",
                        is_misconception=True,
                        misconception_statement=(
                            "The learner may not recall the factorization."
                        ),
                        resolution_status="unresolved",
                        cause_scope="learner_state",
                        operation="transpose_confusion",
                        target_criterion_ids=list(target_criterion_ids),
                        model_reported_causal_confidence=0.6,
                        candidate_causes=list(candidate_causes),
                        postdictive_claims=[
                            {"criterion_id": "whole_item", "must": "not_full_credit"}
                        ],
                    )
                ],
                grader_confidence=0.9,
                confidence=4,
                manual_review_reason=None,
                feedback_md="Review the factorization.",
                repair_suggestions=list(repair_suggestions),
            ),
        ),
        clock=FrozenClock(NOW),
    )


def _receipt(repository, attempt_id):
    debug = repository.attempt_debug_payload(attempt_id) or {}
    attribution = debug.get("causal_attribution") or {}
    return attribution.get("diagnosis_receipt") or {}


def _open_factor(repository):
    factors = repository.open_unresolved_cause_factors()
    assert factors, "the ambiguous whole-item failure must open a cause factor"
    return factors[0]


# --- the ship blocker: a filled repair_class_id --------------------------


def test_authored_divergent_repairs_fill_repair_class_id_end_to_end(tmp_path):
    """Two authored repairs on two targets => a genuinely divergent cause set.

    This is the regression guard for the second inert lane. Before the fix the
    only golden path exercised was self-graded, which authors no repair at all,
    and the facet fallback hid the resulting all-null column; with the fallback
    correctly gone, a null column means discrimination probes never fire.
    """

    vault, repository = _mvp07(tmp_path)
    result = _ambiguous_failure(
        vault,
        repository,
        attempt_id="att_divergent",
        candidate_causes=[
            {
                "statement": "The learner may not recall the factorization.",
                "cause_scope": "learner_state",
                "target_ref": FACTORIZATION_REF,
            },
            {
                "statement": "The learner may not know when SVD applies.",
                "cause_scope": "learner_state",
                "target_ref": APPLICABILITY_REF,
            },
        ],
        repair_suggestions=[
            {
                "practice_mode": "targeted_review",
                "operator": "restate_factorization",
                "rationale": "Re-establish the factorization statement.",
                "target_refs": [FACTORIZATION_REF],
                "expected_minutes": 4.0,
            },
            {
                "practice_mode": "targeted_review",
                "operator": "contrast_applicability",
                "rationale": "Contrast the cases where SVD applies.",
                "target_refs": [APPLICABILITY_REF],
                "expected_minutes": 6.0,
            },
        ],
    )

    # 1. The DURABLE row carries the class -- not just an in-memory receipt field.
    stored = repository.causal_hypotheses_for_attempt(result.attempt_id)
    concrete = [row for row in stored if row["status"] != "open_set"]
    assert len(concrete) == 2
    assert all(row["repair_class_id"] for row in concrete)
    assert len({row["repair_class_id"] for row in concrete}) == 2
    assert all(
        row["repair_class_basis"] == REPAIR_MAPPING_BASIS_TARGET_REF
        for row in concrete
    )
    assert all(row["repair_class_unresolved_reason"] is None for row in concrete)
    # The open-world arm names no cause, so it names no repair -- and is never
    # counted as an unmapped hypothesis owing a backfill.
    open_arm = [row for row in stored if row["status"] == "open_set"]
    assert len(open_arm) == 1
    assert open_arm[0]["repair_class_id"] is None
    assert open_arm[0]["repair_class_basis"] == REPAIR_MAPPING_BASIS_OPEN_SET
    assert open_arm[0]["repair_class_unresolved_reason"] is None

    # 2. The receipt agrees and states the NEED as divergent.
    receipt = _receipt(repository, result.attempt_id)
    assert receipt["probe_need"]["divergent"] is True
    assert receipt["probe_need"]["incomplete_repair_mapping"] is False
    assert len(receipt["probe_need"]["repair_class_ids"]) == 2
    assert receipt["unmapped_hypothesis_ids"] == []
    assert receipt["repair_mapping_gaps"] == {}

    # 3. The hydrated cause row -- what probe targeting actually reads.
    factor = _open_factor(repository)
    causes = factor["candidate_causes"]
    concrete_causes = [c for c in causes if not c.get("open_set")]
    assert len(concrete_causes) == 2
    assert all(c["repair_class_id"] for c in concrete_causes)

    # 4. The classifier finally returns divergent, on the repair-class basis --
    #    NOT incomplete_repair_mapping, and NOT a facet fallback.
    targeting = classify_cause_set(causes, repository=repository)
    assert targeting.state == CAUSE_SET_DIVERGENT
    assert targeting.basis == "repair_class"
    assert targeting.probe_worthy is True
    assert targeting.unmapped_hypothesis_ids == ()
    assert targeting.unmapped_reasons == ()

    # 5. ...and it reaches the priority orchestrator as a learner-actionable
    #    target with no backfill owed.
    priority = probe_priority(
        vault, repository, vault.learning_objects["lo_svd_definition"]
    )
    assert priority["machine_checks"] == []
    assert priority["selected"] is not None
    assert priority["selected"]["kind"] == "cause_set_discrimination"
    assert priority["selected"]["cause_set"]["state"] == CAUSE_SET_DIVERGENT
    assert repair_mapping_backfills(vault, repository, "lo_svd_definition") == []


def test_repair_declared_by_criterion_maps_to_a_facet_targeted_cause(tmp_path):
    """The grading contract lets a repair declare ``target_criterion_ids`` while
    the candidate cause declares a typed ``target_ref``. Matching only on
    ``target_ref`` produced a spurious null whenever the model used the two
    sub-vocabularies it was explicitly told it could use."""

    vault, repository = _mvp07(tmp_path)
    result = _ambiguous_failure(
        vault,
        repository,
        attempt_id="att_criterion_bridge",
        target_criterion_ids=["whole_item"],
        candidate_causes=[
            {
                "statement": "The learner may not recall the factorization.",
                "cause_scope": "learner_state",
                "target_ref": FACTORIZATION_REF,
            },
            {
                "statement": "The learner may not know when SVD applies.",
                "cause_scope": "learner_state",
                "target_ref": APPLICABILITY_REF,
            },
        ],
        repair_suggestions=[
            {
                "practice_mode": "targeted_review",
                "operator": "rework_the_failed_line",
                "rationale": "Rework the failed criterion end to end.",
                "target_criterion_ids": ["whole_item"],
                "expected_minutes": 5.0,
            }
        ],
    )

    concrete = [
        row
        for row in repository.causal_hypotheses_for_attempt(result.attempt_id)
        if row["status"] != "open_set"
    ]
    assert len(concrete) == 2
    assert all(row["repair_class_id"] for row in concrete)
    assert all(
        row["repair_class_basis"] == REPAIR_MAPPING_BASIS_CRITERION_REF
        for row in concrete
    )
    # One repair covers both causes: probing cannot change the action, so this
    # is a common cover, NOT a probe -- even though the causes sit on two
    # different facets. That is the whole point of the repair vocabulary.
    receipt = _receipt(repository, result.attempt_id)
    assert receipt["probe_need"]["divergent"] is False
    assert receipt["probe_need"]["incomplete_repair_mapping"] is False
    targeting = classify_cause_set(
        _open_factor(repository)["candidate_causes"], repository=repository
    )
    assert targeting.probe_worthy is False
    assert len(targeting.repair_class_ids) == 1


# --- the honest unresolvable cases --------------------------------------


def test_self_graded_attempt_records_no_repair_authored_not_a_silent_null(tmp_path):
    """The real mvp-0.7 golden path A5 measured.

    A self-graded attempt produces NO repair suggestion, so there is nothing to
    map to. That is a genuine authoring gap, not a dropped mapping: the honest
    outcome is a typed reason routed to the machine side. It must NOT be
    "fixed" by synthesizing a repair class per target ref -- one synthetic class
    per facet-capability would make divergence equivalent to facet difference
    and resurrect the removed fallback under a new name.
    """

    vault, repository = _mvp07(tmp_path)
    _attempt(
        vault, repository, "pi_svd_ambiguous_001", {"whole_item": 0}, FrozenClock(NOW)
    )

    concrete = [
        row
        for row in repository.causal_hypotheses_for_learning_object(
            "lo_svd_definition"
        )
        if row["status"] != "open_set"
    ]
    assert len(concrete) == 2
    assert all(row["repair_class_id"] is None for row in concrete)
    assert all(
        row["repair_class_basis"] == REPAIR_MAPPING_BASIS_UNRESOLVED
        for row in concrete
    )
    assert all(
        row["repair_class_unresolved_reason"] == "no_repair_authored"
        for row in concrete
    )

    targeting = classify_cause_set(
        _open_factor(repository)["candidate_causes"], repository=repository
    )
    assert targeting.state == CAUSE_SET_INCOMPLETE_MAPPING
    assert targeting.probe_worthy is False
    assert targeting.needs_machine_backfill is True
    assert dict(targeting.unmapped_reasons) == {
        row["id"]: "no_repair_authored" for row in concrete
    }

    # The backfill obligation names its remedy, so a consumer can act on it.
    backfills = repair_mapping_backfills(vault, repository, "lo_svd_definition")
    assert len(backfills) == 1
    assert backfills[0]["learner_actionable"] is False
    assert backfills[0]["unmapped_reasons"] == {
        row["id"]: "no_repair_authored" for row in concrete
    }
    priority = probe_priority(
        vault, repository, vault.learning_objects["lo_svd_definition"]
    )
    assert priority["selected"] is None  # never a learner probe
    assert priority["machine_checks"] == backfills


def test_two_repairs_on_one_target_are_ambiguous_rather_than_a_guess(tmp_path):
    """Two rival repair classes covering the same declared target, and the
    minimal-repair selector picked NEITHER (both were rejected as incomplete),
    so the machine cannot say which repair addresses this cause. Disambiguating
    that is machine-side work; buying it with a learner probe is a principle-8
    inversion.

    Contrast with the selected case: when the structural ordering does pick one
    of the rivals, that IS the disambiguation and the mapping resolves -- see
    tests/test_minimal_repair_selection_a1.py::
    test_the_persisted_repair_class_is_the_structurally_selected_one.
    """

    vault, repository = _mvp07(tmp_path)
    result = _ambiguous_failure(
        vault,
        repository,
        attempt_id="att_ambiguous_repair",
        candidate_causes=[
            {
                "statement": "The learner may not recall the factorization.",
                "cause_scope": "learner_state",
                "target_ref": FACTORIZATION_REF,
            },
            {
                "statement": "The learner may not know when SVD applies.",
                "cause_scope": "learner_state",
                "target_ref": APPLICABILITY_REF,
            },
        ],
        repair_suggestions=[
            {
                "practice_mode": "targeted_review",
                "operator": "restate_factorization",
                "rationale": "Re-establish the factorization statement.",
                "target_refs": [FACTORIZATION_REF],
                "expected_minutes": 4.0,
            },
            {
                "practice_mode": "worked_example",
                "operator": "walk_the_factorization",
                "rationale": "Walk one factorization end to end.",
                "target_refs": [FACTORIZATION_REF],
                "expected_minutes": 9.0,
            },
        ],
    )

    by_id = {
        row["id"]: row
        for row in repository.causal_hypotheses_for_attempt(result.attempt_id)
    }
    reasons = {
        row["id"]: row["repair_class_unresolved_reason"]
        for row in by_id.values()
        if row["status"] != "open_set"
    }
    receipt_now = _receipt(repository, result.attempt_id)
    # Neither rival survived validation, so there is no selected class to break
    # the tie -- that is WHY this is ambiguous rather than resolved.
    assert receipt_now["repair_selection"]["selected"] is None
    assert "ambiguous_repair_target" in set(reasons.values())
    # The other cause has a target no repair mentions at all -- a different gap
    # with a different remedy, and the receipt keeps them apart.
    assert "no_matching_repair_target" in set(reasons.values())
    receipt = _receipt(repository, result.attempt_id)
    assert receipt["repair_mapping_gaps"] == reasons
    assert set(receipt["repair_mapping_gaps"].values()) <= set(
        REPAIR_MAPPING_UNRESOLVED_REASONS
    )
    assert receipt["probe_need"]["incomplete_repair_mapping"] is True
    assert receipt["probe_need"]["divergent"] is False

    targeting = classify_cause_set(
        _open_factor(repository)["candidate_causes"], repository=repository
    )
    assert targeting.state == CAUSE_SET_INCOMPLETE_MAPPING
    assert targeting.probe_worthy is False


# --- near clone on a cold verification (contract §4.3) -------------------


def test_cold_verification_records_its_near_clone_basis(tmp_path):
    """``record_delayed_cold_verification`` has ALREADY proved the two items sit
    in different surface groups -- that is its own guard. Hardcoding
    ``near_clone=False`` threw the proof away; the verdict now carries the basis
    that produced it, so a certification-eligibility decision is auditable."""

    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    add_followup_item(root)
    vault = load_vault(root)
    repository = Repository(paths.sqlite_path)
    source = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001", learner_answer_md="U Sigma Q"
        ),
        SelfGradeInput(criterion_points={"correctness": 0}, confidence=4),
        clock=FrozenClock(NOW),
    )
    cold = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_002", learner_answer_md="U Sigma V^T"
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW + timedelta(days=2)),
    )

    record_delayed_cold_verification(
        vault,
        repository,
        source_attempt_id=source.attempt_id,
        cold_attempt_id=cold.attempt_id,
        repair_class_id="repair:transpose",
        hypothesis_ids=["hypothesis:transpose"],
        avoided_affordances=["single-letter-q-notation"],
        clock=FrozenClock(NOW + timedelta(days=2)),
    )

    events = repository.causal_activity_classification_events(cold.attempt_id)
    verification = [
        event
        for event in events
        if event["contamination_class"] == "verification"
    ]
    assert verification, "the cold attempt must be classified as verification"
    event = verification[-1]
    assert event["near_clone"] is False
    assert event["near_clone_basis"] == "distinct_surface_group"
    assert event["source"] == "cold_verification"
    detail = event["detail"]
    if isinstance(detail, str):
        detail = json.loads(detail)
    assessment = detail["near_clone_assessment"]
    assert assessment["near_clone_basis"] == "distinct_surface_group"
    assert assessment["surface_group"] != assessment["source_surface_group"]
    # ...and a non-near-clone verification still certifies.
    current = repository.causal_activity_classification(cold.attempt_id)
    assert current["eligible_for_certification"] is True


# --- the two open-set namespaces (contract §10b) -------------------------


def test_open_set_cause_id_and_probe_label_are_distinct_namespaces(tmp_path):
    """``probe_hypotheses.H_OTHER`` is a probe-set LABEL; ``OPEN_SET_CAUSE_ID``
    is the placeholder on a candidate CAUSE row. Comparing a cause row's
    ``hypothesis_id`` against the label can never match -- it was dead code in
    the shape of a safety net, correct only because the ``open_set`` flag beside
    it did all the work."""

    assert OPEN_SET_CAUSE_ID != H_OTHER
    vault, repository = _mvp07(tmp_path)
    _attempt(
        vault, repository, "pi_svd_ambiguous_001", {"whole_item": 0}, FrozenClock(NOW)
    )
    factor = _open_factor(repository)
    arms = [c for c in factor["candidate_causes"] if c.get("open_set")]
    assert len(arms) == 1
    # After P1 materialization the arm carries a ULID, never the probe label.
    assert arms[0]["hypothesis_id"] != H_OTHER

    # A hand-authored, never-materialized factor still resolves through the id.
    factor_id = repository.insert_unresolved_cause_factor(
        attempt_id=str(factor["attempt_id"]),
        candidate_causes=[
            *[
                {"hypothesis_id": c["hypothesis_id"], "version": c["version"]}
                for c in factor["candidate_causes"]
                if not c.get("open_set")
            ],
            # No `open_set` flag: only the placeholder id carries the arm.
            {"hypothesis_id": OPEN_SET_CAUSE_ID},
        ],
        algorithm_version="test",
        clock=FrozenClock(NOW),
    )
    plan = build_causal_hypothesis_set(repository, factor_id)
    assert H_OTHER in plan.prior  # the probe set always keeps its open arm
    assert OPEN_SET_CAUSE_ID not in plan.prior

    # The same factor WITHOUT any open arm is refused outright.
    closed_id = repository.insert_unresolved_cause_factor(
        attempt_id=str(factor["attempt_id"]),
        candidate_causes=[
            {"hypothesis_id": c["hypothesis_id"], "version": c["version"]}
            for c in factor["candidate_causes"]
            if not c.get("open_set")
        ],
        algorithm_version="test",
        clock=FrozenClock(NOW),
    )
    with pytest.raises(ValueError, match="open-set arm"):
        build_causal_hypothesis_set(repository, closed_id)
