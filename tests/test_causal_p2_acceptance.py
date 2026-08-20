"""P2 causal attribution -- the end-to-end acceptance walk (contract §9, §10d).

Contract §10d is the reason this file exists: measured against the live
``fixtures/linear_algebra`` vault the causal lane has **never run** -- zero
``causal_hypotheses`` rows, zero probe attempts, three retired P0-era facet-pair
factors.  Nothing in any vault's history exercises this lane, so this test is not
a regression guard on observed behaviour; it is the *only* end-to-end evidence
the lane works at all.  It therefore authors everything and inherits nothing.

The walk::

    unresolved factor -> divergent repairs -> EVSI offer -> accepted probe
      -> locked H_OTHER set -> reviewed candidate -> pinned blind classification
      -> targeted repair unblocked -> fresh cross-surface cold result,
    with ZERO diagnosis delta unless independent evidence exists.

Every step goes through a real entry point -- ``apply_attempt``,
``failure_triage.triage``, ``causal_repair_status``, ``accept_probe_offer``
(which is ``enter_episode`` -> ``commit_presentation``),
``classify_probe_response``, ``record_unresolved_cause_self_report``,
``record_delayed_cold_verification``.  There are no hand-built receipt or
cause-set dicts anywhere in the walk: hand-built dicts are exactly how the
original P2 dead code passed review, and a test that builds its own inputs
cannot tell a wired lane from an inert one.

Two facts constrain the authoring (both established during this review):

* the mvp-0.7 golden path is **self-graded** and authors zero repair
  suggestions, so ``repair_classes == []`` and no cause set is ever divergent.
  The walk therefore grades through ``apply_attempt`` with real authored repair
  suggestions.  It must NOT be worked around by synthesizing a repair class per
  ``target_ref`` -- one synthetic class per facet-capability makes "divergent"
  mean "two distinct facets", i.e. the removed facet fallback under a new name.
* single-attempt receipts legitimately carry ``support_scores = {id: None}`` and
  ``support_authority = "unavailable_single_attempt"``.  The causal promotion
  arm is therefore expected to be ABSENT here; what must survive is the LEGACY
  arm (contract §8, §10b).

The classification -> resolution edge was the last open link and is now closed:
``record_probe_classification`` writes the §7 discriminating-observation receipt
and resolves the factor on an admitted ``matched_single``.  The walk goes
through it, so a regression that makes a classification inert again fails here
rather than passing quietly.  What the edge will NOT do is asserted alongside:
``matched_multiple`` / ``all_bundles_matched`` / ``no_bundle_matched`` /
``cohort_mismatch`` / ``unparsed_features`` resolve nothing, and a verdict whose
declared features were never measured is inadmissible whatever it says.
"""

from __future__ import annotations

import json
from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.diagnosis import failure_triage as FT
from learnloop.curriculum import golden_path_confirm as GPC
from learnloop.curriculum import golden_path_run as GPR
from learnloop.curriculum import task_blueprints as TB
from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    SelfGradeInput,
    apply_attempt,
    complete_self_graded_attempt,
)
from learnloop.diagnosis.causal_attribution import (
    APPROVED_SUPPORT_AUTHORITIES,
    record_unresolved_cause_self_report,
)
from learnloop.diagnosis.causal_health import ChannelHealth, causal_lane_health
from learnloop.diagnosis.causal_orchestrator import (
    accept_probe_offer,
    auto_classify_pinned_probe,
    causal_repair_status,
    classify_probe_response,
    episode_conflict_reason,
    pinned_causal_probe,
    record_probe_classification,
)
from learnloop.diagnosis.causal_probe_coherence import (
    audit_manipulation_contract,
    build_causal_hypothesis_set,
    create_probe_candidate,
    generate_blind_prediction_bundle,
    lock_causal_hypothesis_set,
    record_delayed_cold_verification,
    transition_probe_candidate,
)
from learnloop.diagnosis.followups import evaluate_attempt_intervention_followup
from learnloop.curriculum.golden_path_fixture import stub_blueprint
from learnloop.diagnosis.probe_hypotheses import H_OTHER
from learnloop.diagnosis.probe_targeting import CAUSE_SET_DIVERGENT, classify_cause_set
from learnloop.diagnosis.remediation import (
    prescribe_remediation,
    start_remediation_treatment,
)
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO, admit_probe_instrument_card
from tests.test_km2_write_path import SELECT, SHARED, build_mvp07_vault

CLOCK = FrozenClock(NOW)
LO_ID = "lo_svd_definition"
SOURCE_ITEM = "pi_svd_ambiguous_001"
PROBE_ITEM = "pi_causal_probe_e2e"
COLD_ITEM = "pi_svd_cold_e2e"

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


# --- fixture authoring ------------------------------------------------------


def _extra_item(root, item_id: str, *, source_family: str, prompt: str) -> None:
    upsert_practice_item(
        root,
        {
            "id": item_id,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": [
                "independent_attempt",
                "diagnostic_probe",
                "dont_know",
            ],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": prompt,
            "expected_answer": "U Sigma V^T",
            "evidence_fingerprint": {"source_family": source_family},
            "grading_rubric": {
                "max_points": 4,
                "criteria": [
                    {
                        "id": "correctness",
                        "points": 4,
                        "description": "Correct definition.",
                    }
                ],
                "fatal_errors": [],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=CLOCK,
    )


def _acceptance_vault(tmp_path):
    """A synthetic mvp-0.7 vault with a probe surface and a cold surface.

    Both extra items live in their OWN source family: a cold verification is
    rejected outright when it shares a surface group with its source, and a
    near-clone probe never certifies (§4.3).
    """

    paths = build_mvp07_vault(tmp_path / "vault")
    _extra_item(
        paths.root,
        PROBE_ITEM,
        source_family="chapter9-contrast",
        prompt="Which final factor makes the product valid?",
    )
    _extra_item(
        paths.root,
        COLD_ITEM,
        source_family="chapter11-cold",
        prompt="On a fresh surface: name the three SVD factors.",
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=CLOCK)
    return vault, repository, paths


def _divergent_failure(vault, repository, *, attempt_id: str = "att_causal_e2e"):
    """One graded miss whose diagnosis names two causes AND two authored repairs.

    This is the shape the *model-graded* path produces; the self-graded golden
    path authors no repair at all, which is why nothing on the live vault has
    ever reached a divergent cause set.
    """

    result = apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=SOURCE_ITEM,
                learner_answer_md="I multiplied the eigenvectors together.",
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
                        "evidence": "The product is not the factorization.",
                        "notes": None,
                        "local_grader_id": "test",
                        "grader_tier": 1,
                        "created_at": NOW_ISO,
                    }
                ],
                error_attributions=[
                    GradeAttribution(
                        error_type="wrong_method",
                        severity=0.7,
                        evidence="The answer does not localize the failure.",
                        is_misconception=True,
                        misconception_statement=(
                            "The learner may not recall the factorization."
                        ),
                        resolution_status="unresolved",
                        cause_scope="learner_state",
                        operation="wrong_method",
                        model_reported_causal_confidence=0.6,
                        candidate_causes=[
                            {
                                "statement": (
                                    "The learner may not recall the factorization."
                                ),
                                "cause_scope": "learner_state",
                                "target_ref": FACTORIZATION_REF,
                            },
                            {
                                "statement": (
                                    "The learner may not know when SVD applies."
                                ),
                                "cause_scope": "learner_state",
                                "target_ref": APPLICABILITY_REF,
                            },
                        ],
                        # Attributed per candidate.  A plan-level claim naming no
                        # candidate is `ambiguous_between_candidates` and is
                        # deliberately NOT smeared across rivals (§5.6), so both
                        # hypotheses would read `no_deterministic_claims` --
                        # absence of evidence, never corroboration.  Each cause
                        # here commits to something falsifiable of its own.
                        postdictive_claims=[
                            {
                                "criterion_id": "whole_item",
                                "must": "not_full_credit",
                                "candidate_index": 0,
                            },
                            {
                                "criterion_id": "whole_item",
                                "must": "not_full_credit",
                                "candidate_index": 1,
                            },
                        ],
                    )
                ],
                grader_confidence=0.9,
                confidence=4,
                manual_review_reason=None,
                feedback_md="Review the factorization.",
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
            ),
        ),
        clock=CLOCK,
    )
    # NOTHING mirrors the sidecar here.  ``attempt_feedback_metadata`` used to
    # have exactly one writer (``handlers/practice.py::_persist_feedback_metadata``)
    # while being the ONLY durable copy of the authored repair suggestions, so
    # on every non-sidecar path a learner confirmation re-materialized the
    # episode from an empty row and re-minted every hypothesis with
    # ``repair_class_id = None``.  ``apply_attempt`` now persists it itself; the
    # absence of a hand-written row here is what puts that under test.
    assert repository.fetch_attempt_feedback_metadata(result.attempt_id)[
        "repair_suggestions"
    ], "apply_attempt must make the repair mapping durable on every path"
    return result


def _mint_reviewed_candidate(
    repository, *, factor_id, first_id, second_id, features=None
):
    """Lock the causal set, generate BLIND bundles, audit, review, activate.

    Every step is the real API; ``lock_causal_hypothesis_set`` is what puts the
    ``H_OTHER`` arm into the probe set, and ``transition_probe_candidate`` is the
    register -> review -> activate ladder §10 requires before an instrument may
    be administered.

    ``features`` maps each hypothesis to the feature row its blind bundle
    predicts.  The default pair disagrees on a SEMANTIC feature, which only a
    model can read off prose; a ``criterion:...`` key authors the same instrument
    in the deterministic vocabulary ``deterministic_probe_features`` supplies.
    """

    features = features or {
        first_id: {"names_transpose": False},
        second_id: {"names_transpose": True},
    }
    # A bare mapping is one declared row; a `feature_rows` payload is passed
    # through so a test can author the multi-row (disjunctive) instruments the
    # separability guard would otherwise reject.
    features = {
        hypothesis_id: (
            dict(row)
            if {"feature_rows", "predicted_features", "outcomes"} & set(row)
            else {"predicted_features": dict(row)}
        )
        for hypothesis_id, row in features.items()
    }

    locked = lock_causal_hypothesis_set(
        repository,
        factor_id,
        probe_phase_id="phase_causal_e2e",
        algorithm_version="test",
        clock=CLOCK,
    )
    item = {
        "id": PROBE_ITEM,
        "prompt": "Which final factor makes the product valid?",
        "expected_answer": "U Sigma V^T",
        "practice_mode": "short_answer",
        "grading_rubric": {"criteria": [{"id": "correctness"}]},
    }
    bundles = {
        hypothesis_id: generate_blind_prediction_bundle(
            repository,
            hypothesis_id=hypothesis_id,
            item=item,
            rubric=item["grading_rubric"],
            trace_contract=None,
            generator=lambda _safe, row=row: dict(row),
            model_revision="model-r1",
            outcome_schema_version="probe-outcome-v1",
            clock=CLOCK,
        )
        for hypothesis_id, row in features.items()
    }
    audit = audit_manipulation_contract(
        repository,
        source_item={
            **item,
            "id": SOURCE_ITEM,
            "prompt": "Prompt for pi_svd_ambiguous_001.",
        },
        candidate_item={
            **item,
            "variant_contract": {
                "variant_kind": "rung_shift",
                "intended_manipulations": [
                    {"axis": "surface_wording", "direction": "increase"}
                ],
                "incidental_changes": [],
                "held_constant": ["answer_contract", "rubric", "measurement_targets"],
            },
        },
        source_kind="causal_probe",
        adversarial_review={
            "contract_consistent": True,
            "measurement_target_independence": True,
            "undeclared_differences": [],
        },
        generation_agent_run_id="agent_generate",
        reviewer_agent_run_id="agent_review",
        clock=CLOCK,
    )
    assert audit["status"] == "passed"
    candidate = create_probe_candidate(
        repository,
        factor_id=factor_id,
        practice_item_id=PROBE_ITEM,
        hypothesis_set_id=str(locked.id),
        manipulation_audit_id=audit["id"],
        measurement_contract={
            "independently_compiled": True,
            "inherited_parent_facet_weights": False,
            "criteria": [
                {
                    "criterion_id": "correctness",
                    "target_ref": {"kind": "criterion", "criterion_id": "correctness"},
                }
            ],
        },
        clock=CLOCK,
    )
    for status, reviewer in (("registered", None), ("reviewed", "owner"), ("active", None)):
        candidate = transition_probe_candidate(
            repository, candidate["id"], to_status=status, reviewer=reviewer, clock=CLOCK
        )
    return locked, candidate, bundles


# --- the acceptance walk ----------------------------------------------------


def test_causal_disambiguation_end_to_end_acceptance(tmp_path):
    vault, repository, _paths = _acceptance_vault(tmp_path)
    admit_probe_instrument_card(
        repository, learning_object_id=LO_ID, items=(PROBE_ITEM,)
    )

    # 1 -- unresolved factor, opened by the REAL attempt path.
    result = _divergent_failure(vault, repository)
    factors = repository.open_unresolved_cause_factors(learning_object_id=LO_ID)
    assert len(factors) == 1, "the ambiguous miss must open exactly one factor"
    factor = factors[0]
    factor_id = str(factor["id"])
    causes = factor["candidate_causes"]
    concrete = [cause for cause in causes if not cause.get("open_set")]
    open_arm = [cause for cause in causes if cause.get("open_set")]
    assert len(concrete) == 2 and len(open_arm) == 1

    # 2 -- divergent repairs.  Two distinct repair CLASSES, mapped from authored
    #      repair targets -- never derived from the facets the causes sit on.
    first_id = str(concrete[0]["hypothesis_id"])
    second_id = str(concrete[1]["hypothesis_id"])
    targeting = classify_cause_set(causes, repository=repository)
    assert targeting.state == CAUSE_SET_DIVERGENT
    assert targeting.basis == "repair_class"
    assert targeting.probe_worthy is True
    assert len(targeting.repair_class_ids) == 2

    receipt = (
        (repository.attempt_debug_payload(result.attempt_id) or {})
        .get("causal_attribution", {})
        .get("diagnosis_receipt", {})
    )
    assert receipt["probe_need"]["divergent"] is True
    assert receipt["probe_need"]["incomplete_repair_mapping"] is False
    # An honest single-attempt receipt: no fabricated support numbers.
    assert receipt["support_authority"] not in APPROVED_SUPPORT_AUTHORITIES
    assert set(receipt["support_scores"].values()) == {None}

    # 2b -- REQUIRED EXTRA ASSERTION (§9): the presence of that receipt must not
    #       silently downgrade the source attempt's triage to tier two.  This is
    #       the regression guard for the §2.1 dead-code defect: `_decisive_reason`
    #       used `elif`, so any receipt disabled the legacy route, and production
    #       receipts carry all-None support -- tier one was dead for every
    #       diagnosed attempt.
    run_id = _golden_path_run(repository)
    triaged = FT.triage(
        repository,
        run_id,
        attempt={
            "attempt_id": result.attempt_id,
            "coarse_class": "wrong",
            "error_signature": "wrong_method",
            "grader_confidence": 0.95,
        },
    )
    assert triaged.tier == "one", "a receipt must not force the tier-two aid"
    assert triaged.decisive is True
    # `legacy_dominance`, NOT `causal_authority`: causal promotion requires an
    # approved support authority, which a single-attempt receipt never has.
    assert triaged.tier_one_basis == FT.TIER_ONE_BASIS_LEGACY
    event = repository.failure_triage_event(triaged.event_id)
    decision = json.loads(event["inputs_snapshot_json"])["triage_decision"]
    assert decision["tier_one_basis"] == FT.TIER_ONE_BASIS_LEGACY
    assert decision["causal_support_available"] is True
    assert decision["causal_support_authority_approved"] is False

    # 3 -- with no reviewed instrument the divergent factor BLOCKS the targeted
    #      repair rather than serving one branch of it.
    blocked = causal_repair_status(
        vault, repository, misconception_id=first_id, clock=CLOCK
    )
    assert blocked.status == "blocked_pending_review"
    assert blocked.episode is None

    # 4 -- reviewed candidate + locked H_OTHER set.
    locked, candidate, bundles = _mint_reviewed_candidate(
        repository, factor_id=factor_id, first_id=first_id, second_id=second_id
    )
    assert H_OTHER in locked.prior, "the probe set always keeps its open-world arm"
    assert set(candidate["blind_bundle_ids"]) == {
        bundles[first_id]["id"],
        bundles[second_id]["id"],
    }
    assert all(
        bundle["generated_without_observation"] is True for bundle in bundles.values()
    )

    # 5 -- EVSI offer.  Both information terms are COMPUTED off the recorded
    #      blind-bundle separability, not asked of a model.
    offered = causal_repair_status(
        vault, repository, misconception_id=first_id, clock=CLOCK
    )
    assert offered.status == "needs_disambiguation"
    assert offered.probe_decision == "probe_now"
    assert offered.probe_offered is True
    assert [action.id for action in offered.actions] == [
        "take_quick_check",
        "teach_me_now",
        "not_now",
    ]
    decision_receipt = repository.causal_probe_decision_receipts(factor_id=factor_id)[-1]
    assert decision_receipt["inputs"]["expected_information_gain"] == 1.0
    assert decision_receipt["inputs"]["probability_information_changes_repair"] == 1.0
    assert decision_receipt["inputs"]["evsi_provenance"][
        "expected_information_gain"
    ] == "deterministic"

    # 6a -- the episode that is ALREADY open.  ``sync_vault_state`` cold-starts
    #       an ``initial`` placement episode on every active learning object,
    #       and at most one episode may be open per LO.  It has measured
    #       nothing, so the offer relocks it onto the cause set rather than
    #       refusing (refusing unconditionally made this journey unreachable in
    #       the running app).  Locking a causal set over an episode that HAS
    #       interpreted observations is the case that must still refuse, and
    #       ``episode_conflict_reason`` is the single predicate for it.
    placement = repository.open_probe_episode(LO_ID)
    assert placement is not None and placement.trigger == "initial"
    assert episode_conflict_reason(repository, placement) is None

    # 6b -- accepted probe: a factor-aware episode with the bundles PINNED.
    offer = accept_probe_offer(
        vault,
        repository,
        factor_id=factor_id,
        decision_receipt_id=offered.decision_receipt_id,
        clock=CLOCK,
    )
    assert offer.accepted, offer.reason
    assert offer.episode_id == placement.id, "the placement episode is relocked"
    episode = repository.probe_episode(offer.episode_id)
    assert episode.origin == f"causal_factor:{factor_id}"
    episode_set = repository.fetch_hypothesis_set(episode.hypothesis_set_id)
    assert {row["label"] for row in episode_set["hypotheses"]} == {
        first_id,
        second_id,
        H_OTHER,
    }
    pinned = pinned_causal_probe(repository, offer.presentation_id)
    assert set(pinned["blind_bundle_ids"]) == set(candidate["blind_bundle_ids"])

    # 7 -- pinned blind classification: the administered answer is matched
    #      against exactly those frozen bundles.
    classified = classify_probe_response(
        repository,
        presentation_id=offer.presentation_id,
        observed_features={"names_transpose": False},
    )
    assert classified["outcome"] == "matched_single"
    assert classified["classified_as"] == [first_id]
    assert classified["causal_factor_id"] == factor_id

    # 8 -- the classification -> resolution edge.  `classify_probe_response` is
    #      a pure read; `record_probe_classification` is what ACTS on the
    #      verdict, and it is the only channel through which diagnosis support
    #      may move (§6, §7).  Before this existed the walk had to close the
    #      factor through the learner self-report instead, which is a different
    #      evidence channel entirely.
    observation = record_probe_classification(
        repository,
        presentation_id=offer.presentation_id,
        observed_features={"names_transpose": False},
        # This walk's features are semantic, not read off the rubric, so the
        # sensor is a model. The factor still closes; the `validator_owned`
        # grant does not -- see step 8b.
        feature_source="model_extracted",
        clock=CLOCK,
    )
    assert observation.admitted is True
    assert observation.resolved_factor is True
    assert observation.support_scores == {first_id: 1.0, second_id: 0.0}
    assert repository.unresolved_cause_factor(factor_id)["status"] == "resolved"
    assert repository.unresolved_cause_factor(factor_id)[
        "resolution_observation_ids"
    ] == [observation.observation_id]

    # 8b -- the authority the sensor did NOT earn.  A model-extracted feature
    #       vector is real discriminating evidence and may veto a route, but it
    #       is not a deterministic verifier and must never PROMOTE one (§2.1).
    assert observation.support_authority is None
    receipt_row = repository.causal_discriminating_observation(
        observation.observation_id
    )
    assert receipt_row["support_authority"] is None
    assert receipt_row["feature_source"] == "model_extracted"
    assert receipt_row["declared_keys_observed"] is True
    assert receipt_row["admission_reason"] == "matched_single_over_measured_features"

    # 8c -- targeted repair unblocked, on the hypothesis the blind instrument
    #       selected.  The factor no longer holds it.
    believed_id = first_id
    assert repository.causal_hypothesis(believed_id)["repair_class_id"] == str(
        concrete[0]["repair_class_id"]
    )

    unblocked = causal_repair_status(
        vault, repository, misconception_id=believed_id, clock=CLOCK
    )
    assert unblocked.repair_permitted is True
    assert unblocked.status == "started"
    assert unblocked.episode is not None

    # 9 -- fresh cross-surface cold result, carried through the follow-up task.
    episode_id = unblocked.episode["id"]
    prescribe_remediation(vault, repository, episode_id, clock=CLOCK)
    treatment = start_remediation_treatment(vault, repository, episode_id, clock=CLOCK)
    assert treatment["primed_item_id"] != treatment["cold_item_id"]

    primed = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=treatment["primed_item_id"],
            learner_answer_md="U Sigma Q",
            primed=True,
        ),
        SelfGradeInput(criterion_points=_zero_points(vault, treatment["primed_item_id"]), confidence=4),
        clock=CLOCK,
    )
    # The primed attempt is a repair activity: it certifies nothing.
    primed_activity = repository.causal_activity_classification(primed.attempt_id)
    assert primed_activity["contamination_class"] == "repair_activity"
    assert primed_activity["eligible_for_certification"] is False
    assert primed_activity["eligible_for_fsrs"] is False

    later = FrozenClock(NOW + timedelta(days=2))
    cold = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=treatment["cold_item_id"],
            learner_answer_md="U, Sigma and V transpose.",
        ),
        SelfGradeInput(
            criterion_points=_full_points(vault, treatment["cold_item_id"]), confidence=5
        ),
        clock=later,
    )
    evaluate_attempt_intervention_followup(vault, repository, result=cold, clock=later)
    verification = repository.causal_cold_verification_for_attempt(cold.attempt_id)
    assert verification is not None, "the cold retry must fire the §6.2 verification"
    assert verification["source_attempt_id"] == primed.attempt_id
    assert verification["success"] is True
    assert verification["source_surface_family"] != verification["cold_surface_family"]

    # 10 -- ZERO diagnosis delta.  A successful repair never retroactively proves
    #       the diagnosis (§6.2 hard invariant).
    assert verification["diagnosis_support_update"]["delta"] == 0.0
    assert "does not retroactively prove" in (
        verification["diagnosis_support_update"]["reason"]
    )
    cold_activity = repository.causal_activity_classification(cold.attempt_id)
    assert cold_activity["contamination_class"] == "verification"
    assert cold_activity["near_clone"] is False
    assert cold_activity["eligible_for_certification"] is True


def test_diagnosis_support_moves_only_on_independent_discriminating_evidence(tmp_path):
    """The other half of "ZERO delta unless independent evidence exists".

    A non-zero diagnosis delta is accepted ONLY when the caller names an
    independent discriminating observation; repair success alone is refused.
    Both branches run against a real cold pair built by the attempt path.
    """

    vault, repository, _paths = _acceptance_vault(tmp_path)
    source = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id=PROBE_ITEM, learner_answer_md="U Sigma Q"),
        SelfGradeInput(criterion_points={"correctness": 0}, confidence=4),
        clock=CLOCK,
    )
    later = FrozenClock(NOW + timedelta(days=2))
    cold = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id=COLD_ITEM, learner_answer_md="U Sigma V^T"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=later,
    )

    with pytest.raises(ValueError, match="independent discriminating evidence"):
        record_delayed_cold_verification(
            vault,
            repository,
            source_attempt_id=source.attempt_id,
            cold_attempt_id=cold.attempt_id,
            repair_class_id="repair:recall",
            hypothesis_ids=["h_recall"],
            avoided_affordances=["primed_repair_context"],
            diagnosis_support_update={"delta": 0.4, "basis": "repair_success"},
            clock=later,
        )

    receipt = record_delayed_cold_verification(
        vault,
        repository,
        source_attempt_id=source.attempt_id,
        cold_attempt_id=cold.attempt_id,
        repair_class_id="repair:recall",
        hypothesis_ids=["h_recall"],
        avoided_affordances=["primed_repair_context"],
        diagnosis_support_update={
            "delta": 0.4,
            "basis": "blind_probe_match",
            "observation_id": "obs_blind_probe_1",
        },
        clock=later,
    )
    assert receipt["diagnosis_support_update"]["delta"] == 0.4
    assert receipt["diagnosis_support_update"]["basis"] == "blind_probe_match"


# --- the classification -> resolution edge, and what it refuses -------------


def _offered_probe(vault, repository, *, features=None):
    """Everything up to and including a served, pinned causal probe.

    ``features`` is passed straight through to the blind bundles, so a caller
    can author an instrument that fails to discriminate, or one whose two arms
    declare disjoint keys, and still reach a served probe.  The offer is
    read-only (``start_repair=False``) because these cases deliberately include
    decisions that would otherwise start a repair episode.
    """

    admit_probe_instrument_card(
        repository, learning_object_id=LO_ID, items=(PROBE_ITEM,)
    )
    result = _divergent_failure(vault, repository)
    factor = repository.open_unresolved_cause_factors(learning_object_id=LO_ID)[0]
    factor_id = str(factor["id"])
    concrete = [
        cause for cause in factor["candidate_causes"] if not cause.get("open_set")
    ]
    first_id = str(concrete[0]["hypothesis_id"])
    second_id = str(concrete[1]["hypothesis_id"])
    _mint_reviewed_candidate(
        repository,
        factor_id=factor_id,
        first_id=first_id,
        second_id=second_id,
        features=(
            {first_id: features[0], second_id: features[1]}
            if features is not None
            else None
        ),
    )
    status = causal_repair_status(
        vault,
        repository,
        misconception_id=first_id,
        start_repair=False,
        clock=CLOCK,
    )
    offer = accept_probe_offer(
        vault,
        repository,
        factor_id=factor_id,
        decision_receipt_id=status.decision_receipt_id,
        clock=CLOCK,
    )
    assert offer.accepted, offer.reason
    return result, factor_id, first_id, second_id, offer


def test_an_instrument_that_did_not_discriminate_resolves_nothing(tmp_path):
    """``all_bundles_matched`` is the INSTRUMENT failing, not open-set evidence.

    Agent A3 split this outcome out of the old ``ambiguous`` verdict precisely
    because "every prediction fits" and "no prediction fits" had been
    indistinguishable, and only the second is evidence for ``H_OTHER``.
    """

    vault, repository, _paths = _acceptance_vault(tmp_path)
    # The second arm's FIRST row conflicts with everything the first arm
    # declares, so the pair is separable and `create_probe_candidate` accepts
    # it -- but its second, disjoint row also fits the observation below, so
    # both arms match and the instrument distinguishes nothing.
    _result, factor_id, _first, _second, offer = _offered_probe(
        vault,
        repository,
        features=(
            {"names_transpose": False},
            {
                "feature_rows": [
                    {"names_transpose": True},
                    {"vague_marker": True},
                ]
            },
        ),
    )
    observation = record_probe_classification(
        repository,
        presentation_id=offer.presentation_id,
        observed_features={"names_transpose": False, "vague_marker": True},
        feature_source="deterministic",
        clock=CLOCK,
    )
    assert observation.outcome == "all_bundles_matched"
    assert observation.admitted is False
    assert observation.admission_reason == (
        "non_discriminating_outcome:all_bundles_matched"
    )
    assert observation.resolved_factor is False
    assert observation.support_authority is None
    assert observation.support_scores == {}
    assert observation.receipt["supports_open_set"] is False
    assert repository.unresolved_cause_factor(factor_id)["status"] == "open"


def test_no_bundle_matched_supports_the_open_set_but_closes_nothing(tmp_path):
    """The other half of the asymmetry: real evidence, no resolution.

    An open-world arm names no cause, so there is no branch-specific repair to
    unblock -- the factor stays open even though the observation is admitted.
    """

    vault, repository, _paths = _acceptance_vault(tmp_path)
    _result, factor_id, first_id, second_id, offer = _offered_probe(vault, repository)
    observation = record_probe_classification(
        repository,
        presentation_id=offer.presentation_id,
        observed_features={"names_transpose": "neither"},
        feature_source="deterministic",
        clock=CLOCK,
    )
    assert observation.outcome == "no_bundle_matched"
    assert observation.admitted is True
    assert observation.receipt["supports_open_set"] is True
    assert observation.classification["classified_as"] == [H_OTHER]
    assert observation.resolved_factor is False
    assert repository.unresolved_cause_factor(factor_id)["status"] == "open"
    # Every concrete prediction was tested and failed: that is 0.0 support, not
    # absent support, and it must not be readable as a dominant cause.
    assert observation.support_scores == {first_id: 0.0, second_id: 0.0}


def test_a_probe_answered_after_a_reveal_is_not_independent_evidence(tmp_path):
    """Migration 155. Independence is a separate question from discrimination.

    The instrument worked perfectly: the answer matched exactly one pinned
    prediction over fully measured features. But the learner had been shown the
    answer first, so what the observation measures is reading comprehension.
    Admitting it would let a revealed solution CLOSE the factor its own reveal
    contaminated, which is the loop the reveal ledger exists to break.
    """

    from learnloop.attempts.reveal_ledger import record_reveal

    vault, repository, _paths = _acceptance_vault(tmp_path)
    result, factor_id, first_id, _second, offer = _offered_probe(vault, repository)
    probe_attempt = repository.fetch_practice_attempt(result.attempt_id)
    record_reveal(
        repository,
        practice_item_id=str(probe_attempt["practice_item_id"]),
        learning_object_id=str(probe_attempt["learning_object_id"]),
        source_kind="repair_display",
        amount=0.8,
        # Strictly before the attempt, so the attempt is downstream of it.
        clock=FrozenClock(NOW - timedelta(hours=1)),
    )

    observation = record_probe_classification(
        repository,
        presentation_id=offer.presentation_id,
        observed_features={"names_transpose": False},
        feature_source="deterministic",
        probe_attempt_id=result.attempt_id,
        clock=CLOCK,
    )

    # The verdict itself is unchanged -- the instrument is not at fault.
    assert observation.outcome == "matched_single"
    # ...but it earns nothing and closes nothing.
    assert observation.admitted is False
    assert observation.admission_reason == "post_reveal_not_independent"
    assert observation.resolved_factor is False
    assert observation.support_authority is None
    assert repository.unresolved_cause_factor(factor_id)["status"] == "open"

    receipt = repository.causal_discriminating_observation(observation.observation_id)
    assert receipt["admissible_as_independent"] is False
    assert receipt["inadmissibility_reason"] == "post_reveal_not_independent"
    assert receipt["contaminating_reveal_event_id"]
    assert receipt["channel"] == "blind_probe"


def test_a_probe_answered_with_no_reveal_is_marked_independent(tmp_path):
    vault, repository, _paths = _acceptance_vault(tmp_path)
    result, factor_id, first_id, _second, offer = _offered_probe(vault, repository)

    observation = record_probe_classification(
        repository,
        presentation_id=offer.presentation_id,
        observed_features={"names_transpose": False},
        feature_source="deterministic",
        probe_attempt_id=result.attempt_id,
        clock=CLOCK,
    )
    assert observation.admitted is True
    receipt = repository.causal_discriminating_observation(observation.observation_id)
    assert receipt["admissible_as_independent"] is True
    assert receipt["inadmissibility_reason"] is None


def test_a_verdict_over_unmeasured_features_is_inadmissible(tmp_path):
    """The exact-key matcher cannot tell "measured and different" from "not measured".

    Hypothesis B's declared key is absent from the observation, so B reports
    ``matched: False`` for a reason that is not evidence -- and the outcome reads
    ``matched_single`` for A.  Admitting that would resolve a factor on a probe
    that never tested the rival, so coverage is checked separately from the
    match.
    """

    vault, repository, _paths = _acceptance_vault(tmp_path)
    first_features = {"names_transpose": False}
    second_features = {
        "feature_rows": [{"names_transpose": True}, {"never_observed": True}]
    }
    _result, factor_id, first_id, _second, offer = _offered_probe(
        vault, repository, features=(first_features, second_features)
    )
    # Only the second arm's DISJOINT row is observed. It matches; the first arm
    # declared a key nothing measured, so its "no match" is not evidence.
    observation = record_probe_classification(
        repository,
        presentation_id=offer.presentation_id,
        observed_features={"never_observed": True},
        feature_source="deterministic",
        clock=CLOCK,
    )
    assert observation.outcome == "matched_single"
    assert observation.admitted is False
    assert observation.admission_reason == "declared_features_not_observed"
    assert observation.resolved_factor is False
    assert observation.support_authority is None
    assert observation.support_scores == {}
    assert repository.unresolved_cause_factor(factor_id)["status"] == "open"
    assert observation.receipt["detail"]["unmeasured_hypothesis_ids"] == [first_id]


def test_a_deterministic_sensor_earns_validator_owned_and_reaches_triage(tmp_path):
    """The full deterministic lane -- the FIRST producer of approved authority.

    Agent A1 established that nothing in the system ever set an approved
    support authority, so §2.1's ``causal_authority`` promotion arm (agent A2's)
    was unreachable outside a hand-supplied snapshot.  A blind bundle authored in
    the deterministic criterion vocabulary is classified with no model in the
    loop at all: the answer is graded, the criterion outcomes ARE the observed
    features, and the post-attempt hook fires the classification itself.
    """

    vault, repository, _paths = _acceptance_vault(tmp_path)
    result, factor_id, first_id, second_id, offer = _offered_probe(
        vault,
        repository,
        features=(
            {"criterion:correctness:full_credit": False},
            {"criterion:correctness:full_credit": True},
        ),
    )

    probe = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=PROBE_ITEM,
            learner_answer_md="U Sigma Q",
            attempt_type="diagnostic_probe",
            probe_presentation_id=offer.presentation_id,
        ),
        SelfGradeInput(criterion_points={"correctness": 0}, confidence=3),
        clock=CLOCK,
    )
    # The live post-attempt path is the caller; nothing here classifies by hand.
    evaluate_attempt_intervention_followup(
        vault, repository, result=probe, clock=CLOCK
    )
    observations = repository.causal_discriminating_observations(factor_id=factor_id)
    assert len(observations) == 1
    observation = observations[0]
    assert observation["outcome"] == "matched_single"
    assert observation["classified_as"] == [first_id]
    assert observation["feature_source"] == "deterministic"
    assert observation["probe_attempt_id"] == probe.attempt_id
    assert observation["support_authority"] == "validator_owned"
    assert observation["support_scores"] == {first_id: 1.0, second_id: 0.0}
    assert observation["resolved_factor"] is True
    assert repository.unresolved_cause_factor(factor_id)["status"] == "resolved"

    # ...and re-running the hook does not append a second verdict.
    evaluate_attempt_intervention_followup(
        vault, repository, result=probe, clock=CLOCK
    )
    assert len(repository.causal_discriminating_observations(factor_id=factor_id)) == 1

    # The observation reaches triage as SUPPORT. Grader confidence is far too
    # low for the legacy arm, so a tier-one route here can only be the causal
    # one -- which is exactly the arm that had no producer.
    run_id = _golden_path_run(repository)
    promoted = FT.triage(
        repository,
        run_id,
        attempt={
            "attempt_id": result.attempt_id,
            "coarse_class": "wrong",
            "error_signature": "wrong_method",
            "grader_confidence": 0.2,
        },
    )
    assert promoted.tier == "one"
    assert promoted.tier_one_basis == FT.TIER_ONE_BASIS_CAUSAL
    event = repository.failure_triage_event(promoted.event_id)
    decision = json.loads(event["inputs_snapshot_json"])["triage_decision"]
    assert decision["causal_support_authority_approved"] is True

    # ...and the §8 two-tailed watch can now see the edge is alive.
    health = causal_lane_health(repository)
    channels = {row["channel"]: row for row in health["channels"]}
    assert channels["discriminating_observations"]["total"] == 1
    assert channels["discriminating_observations"]["filled"] == 1
    assert health["observation_outcomes"] == {"matched_single": 1}
    assert health["observation_feature_sources"] == {"deterministic": 1}


def test_auto_classification_declines_a_sensor_it_cannot_read(tmp_path):
    """The gate that stops the automatic hook manufacturing open-set evidence.

    The default instrument declares a semantic feature. Handing the exact-key
    matcher a criterion-outcome vector instead would report ``no_bundle_matched``
    -- which §3.5 defines as evidence FOR ``H_OTHER`` -- from a probe no sensor
    ever read. The hook must record nothing at all.
    """

    vault, repository, _paths = _acceptance_vault(tmp_path)
    _result, factor_id, _first, _second, offer = _offered_probe(vault, repository)
    probe = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=PROBE_ITEM,
            learner_answer_md="U Sigma Q",
            attempt_type="diagnostic_probe",
            probe_presentation_id=offer.presentation_id,
        ),
        SelfGradeInput(criterion_points={"correctness": 0}, confidence=3),
        clock=CLOCK,
    )
    assert (
        auto_classify_pinned_probe(
            vault, repository, attempt_id=probe.attempt_id, clock=CLOCK
        )
        is None
    )
    assert repository.causal_discriminating_observations(factor_id=factor_id) == []
    assert repository.unresolved_cause_factor(factor_id)["status"] == "open"


# --- the learner-confirmation channel, on a non-sidecar path ----------------


def test_self_report_keeps_the_repair_mapping_and_returns_a_live_id(tmp_path):
    """Two defects that only ever showed up away from the sidecar.

    1. ``attempt_feedback_metadata`` had a single writer, in the sidecar, and it
       is the only durable copy of the authored repair suggestions.
       ``record_unresolved_cause_self_report`` re-materializes the causal
       episode from that row, so on a CLI/replay/service path the confirmation
       re-minted every hypothesis with ``repair_class_id = None``.
    2. The report returned the hypothesis version IT wrote, which its own
       follow-on ``materialize_causal_episode`` then superseded -- so the
       returned id no longer resolved through ``misconception_candidate_by_id``
       and the repair surface 404'd on the belief just confirmed.

    Nothing here writes feedback metadata by hand; that is the point.
    """

    vault, repository, _paths = _acceptance_vault(tmp_path)
    _divergent_failure(vault, repository)
    factor = repository.open_unresolved_cause_factors(learning_object_id=LO_ID)[0]
    factor_id = str(factor["id"])
    concrete = [
        cause for cause in factor["candidate_causes"] if not cause.get("open_set")
    ]
    believed_index = [
        index
        for index, cause in enumerate(factor["candidate_causes"])
        if not cause.get("open_set")
    ][0]
    expected_repair_class = str(concrete[0]["repair_class_id"])
    assert expected_repair_class

    report = record_unresolved_cause_self_report(
        vault,
        repository,
        factor_id=factor_id,
        response="believed_candidate",
        candidate_index=believed_index,
        clock=CLOCK,
    )
    assert report["resolved"] is True
    belief_id = str(report["provisional_belief_id"])

    # (2) the returned id is the LIVE head, not the superseded version.
    assert repository.misconception_candidate_by_id(belief_id) is not None
    # (1) ...and the repair mapping survived re-materialization.
    assert (
        repository.causal_hypothesis(belief_id)["repair_class_id"]
        == expected_repair_class
    )
    # The repair the id names is servable, which is what the 404 blocked.
    status = causal_repair_status(
        vault, repository, misconception_id=belief_id, clock=CLOCK
    )
    assert status.repair_permitted is True


# --- projection v3: the single authored cause is UNIONED, never replaced ----


def _single_cause_failure(vault, repository, *, attempt_id="att_single_cause"):
    """A graded miss whose diagnosis names exactly ONE candidate cause.

    The item's whole-item criterion carries two measurement targets, so the
    failure is still unresolved and still opens a factor -- but the model
    committed to one cause, which is the case the projection used to discard.
    """

    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=SOURCE_ITEM,
                learner_answer_md="I used the eigenvectors directly.",
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
                        "evidence": "Not the factorization.",
                        "notes": None,
                        "local_grader_id": "test",
                        "grader_tier": 1,
                        "created_at": NOW_ISO,
                    }
                ],
                error_attributions=[
                    GradeAttribution(
                        error_type="wrong_method",
                        severity=0.7,
                        evidence="One cause fits the answer.",
                        is_misconception=True,
                        misconception_statement=(
                            "The learner may not recall the factorization."
                        ),
                        resolution_status="unresolved",
                        cause_scope="learner_state",
                        operation="wrong_method",
                        candidate_causes=[
                            {
                                "statement": (
                                    "The learner may not recall the factorization."
                                ),
                                "cause_scope": "learner_state",
                                "target_ref": FACTORIZATION_REF,
                            }
                        ],
                        postdictive_claims=[],
                    )
                ],
                grader_confidence=0.9,
                confidence=4,
                manual_review_reason=None,
                feedback_md="Review the factorization.",
            ),
        ),
        clock=CLOCK,
    )


def test_one_authored_cause_is_unioned_with_the_synthesized_arms(tmp_path):
    """Projection v3.  The model's own asserted cause must be an ARM.

    Before the fix ``_open_candidate_causes`` REPLACED the single authored cause
    with one synthesized facet-target cause per criterion target.  The authored
    cause was still minted as a ``causal_hypotheses`` row -- so it looked
    present -- but ``build_causal_hypothesis_set`` reads the FACTOR's arms, and
    those no longer contained it.  Every probe locked for that factor therefore
    tested a set that excluded the one cause the diagnosis actually claimed, and
    no administered probe could confirm or refute it.

    Fixing this changes projected cause sets, which is why it lands with a
    ``CANONICAL_PROJECTION_VERSION`` bump rather than as a silent correction.
    """

    vault, repository, _paths = _acceptance_vault(tmp_path)
    result = _single_cause_failure(vault, repository)

    factor = repository.open_unresolved_cause_factors(learning_object_id=LO_ID)[0]
    causes = factor["candidate_causes"]
    concrete = [cause for cause in causes if not cause.get("open_set")]
    statements = {str(cause["statement"]) for cause in concrete}

    # The authored cause survived...
    assert "The learner may not recall the factorization." in statements
    # ...alongside a synthesized arm for the OTHER measurement target...
    assert any(
        str(cause.get("facet")) == SELECT for cause in concrete
    ), "the second criterion target must still get its open-world arm"
    # ...and NOT a duplicate arm restating the authored cause's own target in
    # the facet vocabulary under indictment.
    factorization_arms = [
        cause
        for cause in concrete
        if (cause.get("target_ref") or {}).get("facet_id") == SHARED
    ]
    assert len(factorization_arms) == 1
    # ...plus the open-world arm, always.
    assert len([cause for cause in causes if cause.get("open_set")]) == 1

    # The locked probe set now contains the asserted cause. This is the
    # assertion that actually failed before the fix.
    authored_id = next(
        str(cause["hypothesis_id"])
        for cause in concrete
        if str(cause["statement"]) == "The learner may not recall the factorization."
    )
    plan = build_causal_hypothesis_set(repository, str(factor["id"]))
    assert authored_id in plan.prior
    assert H_OTHER in plan.prior

    # The stored hypothesis for the authored cause is the SAME row the receipt
    # names -- the arm is the model's cause, not a facet paraphrase of it.
    receipt = (
        (repository.attempt_debug_payload(result.attempt_id) or {})
        .get("causal_attribution", {})
        .get("diagnosis_receipt", {})
    )
    assert authored_id in {
        str(ref.get("id")) for ref in receipt.get("hypotheses") or []
    }


def test_projection_bulk_loads_candidate_cause_error_events_once(
    tmp_path, monkeypatch
):
    """Unresolved failures do not issue one error-event read per criterion."""

    from learnloop.substrate.canonical_projection import project_canonical_facet_state

    vault, repository, _paths = _acceptance_vault(tmp_path)
    _single_cause_failure(vault, repository)
    calls = 0
    original_bulk = repository.all_error_events_by_attempt

    def bulk_once():
        nonlocal calls
        calls += 1
        return original_bulk()

    monkeypatch.setattr(repository, "all_error_events_by_attempt", bulk_once)
    monkeypatch.setattr(
        repository,
        "error_events_for_attempt",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("canonical replay must not query errors per attempt")
        ),
    )

    project_canonical_facet_state(vault, repository, clock=CLOCK)

    assert calls == 1
    assert repository.open_unresolved_cause_factors(learning_object_id=LO_ID)


def test_projection_version_names_the_open_cause_union(tmp_path):
    """The version bump is the replay boundary; a rebuild records it.

    ...and the FIRST-ever rebuild is a boundary too, whenever it recomputed
    estimates the learner had already seen.  Every real vault is in exactly that
    position: ``fixtures/linear_algebra`` carries 22 attempts and ZERO
    ``derived_state_rebuilds`` rows, so the projection cutover's first rebuild
    would have recomputed months of visible estimates and told the learner
    nothing.  A silent state change is the failure mode
    (`spec_diagnostic_augmentation_v1.md` A6: the system must be able to say it
    was wrong), and skipping the first row unconditionally is what made it one.
    """

    from learnloop.substrate.canonical_projection import CANONICAL_PROJECTION_VERSION
    from learnloop.learner.learner_review_feed import build_learner_review_feed
    from learnloop.substrate.replay import rebuild_derived_state

    # Pinned deliberately so changing what the fold derives is always a conscious
    # bump. Each version supersedes without replacing: the open-cause UNION
    # semantics (v3), item-declared capability for compiled criterion targets
    # (v4), and v5's Meas §3.A1 guards (supporting credit requires A6 trace
    # evidence; per-cell embedded-share cap) all remain in force, v6 makes
    # absent grading evidence inert, v7 carries priming provenance into replay,
    # and v8 separates certification eligibility from the assistance display so
    # pure diagnostics / recorded near clones cannot certify. Update this literal
    # whenever the projection semantics move.
    assert CANONICAL_PROJECTION_VERSION == "canonical_projection_v8_activity_eligibility"

    vault, repository, _paths = _acceptance_vault(tmp_path)
    _single_cause_failure(vault, repository)
    rebuild = rebuild_derived_state(vault, repository, clock=CLOCK)
    marker = repository.latest_derived_state_rebuild()
    assert marker is not None and str(marker["id"]) == str(rebuild.marker_id)
    assert marker["canonical_projection_version"] == CANONICAL_PROJECTION_VERSION
    assert int(marker["replayed_attempts"]) > 0

    # The first rebuild on a vault with prior attempts IS a recalibration
    # boundary, and it reaches the learner review feed.
    first_only = repository.derived_state_rebuild_version_changes()
    assert [
        (
            change["previous_canonical_projection_version"],
            change["canonical_projection_version"],
        )
        for change in first_only
    ] == [(None, CANONICAL_PROJECTION_VERSION)]
    changelog = build_learner_review_feed(vault, repository)["changelog"]
    assert [
        entry["id"] for entry in changelog if entry["kind"] == "recalibration"
    ] == [f"recalibration:{first_only[0]['id']}"]

    # ...and a vault rebuilt ACROSS the v2 boundary surfaces that crossing as
    # its own entry, which is what the learner review feed renders (A4's
    # wiring).  Recorded an hour earlier, so it sorts ahead of the v3 rebuild.
    repository.record_derived_state_rebuild(
        scope="all",
        learning_object_ids=[LO_ID],
        algorithm_version=vault.config.algorithms.algorithm_version,
        rebuilt_learning_objects=1,
        replayed_attempts=1,
        canonical_projection_version="canonical_projection_v2_causal_activity",
        clock=FrozenClock(NOW - timedelta(hours=1)),
    )
    changes = repository.derived_state_rebuild_version_changes()
    assert [
        (
            change["previous_canonical_projection_version"],
            change["canonical_projection_version"],
        )
        for change in changes
    ] == [
        (None, "canonical_projection_v2_causal_activity"),
        ("canonical_projection_v2_causal_activity", CANONICAL_PROJECTION_VERSION),
    ]


def test_a_first_rebuild_with_nothing_to_replay_narrates_nothing(tmp_path):
    """The scoping half of the rule: housekeeping the learner never saw.

    A first rebuild on a vault with no replayed attempts recomputed no estimate
    anyone has seen. Announcing it would be exactly the "narrate every internal
    event" failure the collapse-to-one-entry rule exists to prevent.
    """

    vault, repository, _paths = _acceptance_vault(tmp_path)
    repository.record_derived_state_rebuild(
        scope="all",
        learning_object_ids=[],
        algorithm_version=vault.config.algorithms.algorithm_version,
        rebuilt_learning_objects=0,
        replayed_attempts=0,
        canonical_projection_version="canonical_projection_v3_open_cause_union",
        clock=CLOCK,
    )
    assert repository.derived_state_rebuild_version_changes() == []


# --- §8: the metric that would have caught this -----------------------------


def test_causal_lane_health_watches_both_tails_and_pins_the_tier_one_basis(tmp_path):
    """The §8 hard assertion, plus the two-tailed fill-rate watch around it.

    The original defect was invisible because nothing measured it: every
    receipt's ``support_scores`` were ``None`` and every hypothesis's
    ``repair_class_id`` was ``None``, on 100% of rows, and no metric named
    either tail.  ``causal_lane_health`` names both.

    The HARD assertion is the triage one.  ``causal_authority`` is expected to
    be absent -- a single-attempt receipt can never promote -- so the arm that
    must survive is the LEGACY one.  Under the pre-fix gate (``elif``: the mere
    existence of a receipt replaced the legacy route) this same walk produced
    ``tier_one_events == 0`` and a tier-two decision aid instead, which is
    exactly what this assertion would have caught.
    """

    vault, repository, _paths = _acceptance_vault(tmp_path)
    result = _divergent_failure(vault, repository)
    run_id = _golden_path_run(repository)
    FT.triage(
        repository,
        run_id,
        attempt={
            "attempt_id": result.attempt_id,
            "coarse_class": "wrong",
            "error_signature": "wrong_method",
            "grader_confidence": 0.95,
        },
    )

    health = causal_lane_health(repository)
    triage_health = health["triage"]
    # --- the hard assertion -------------------------------------------------
    assert triage_health["tier_one_events"] >= 1
    assert triage_health["tier_one_without_basis"] == 0
    assert triage_health["tier_one_by_basis"] == {FT.TIER_ONE_BASIS_LEGACY: 1}

    channels = {row["channel"]: row for row in health["channels"]}
    # An honest abstention, not a hole: one attempt owns no validator support,
    # so every score is None AND the authority says so.
    support = channels["causal_support"]
    assert support["total"] == 2
    assert support["fill_rate"] == 0.0
    assert support["abstention_rate"] == 1.0
    assert support["missing"] == 0
    # (one receipt, two concrete hypotheses under it)
    assert health["support_authorities"] == {"unavailable_single_attempt": 1}
    # ...while the repair mapping IS filled, which is what wave 2 fixed.  A
    # metric that could not tell these two channels apart is the metric that
    # let the inert lane through.
    repair = channels["repair_mapping"]
    assert repair["total"] == 2 and repair["filled"] == 2
    assert repair["missing"] == 0
    # Nothing has been probed yet, so those channels are honestly empty and say
    # so rather than reporting a vacuous 100%.
    assert channels["probe_decisions"]["total"] == 0
    assert channels["bundle_features"]["tail"] == "insufficient"
    # ...including the classification -> resolution edge itself. `empty` here is
    # the inert-lane signature: probes served, answered, and nothing recorded.
    assert channels["discriminating_observations"]["total"] == 0
    assert health["observation_outcomes"] == {}
    assert health["observation_feature_sources"] == {}

    # Both tails are named, not just the empty one: a field NOTHING ever
    # declines to fill is as suspect as a field nothing ever fills (standing
    # constraint 2), and "insufficient" refuses to judge either way on n < 5.
    assert ChannelHealth("c", total=8, filled=0, abstained=0).tail(5) == "empty"
    assert ChannelHealth("c", total=8, filled=8, abstained=0).tail(5) == "saturated"
    assert ChannelHealth("c", total=8, filled=3, abstained=5).tail(5) == "mixed"
    assert ChannelHealth("c", total=2, filled=0, abstained=0).tail(5) == "insufficient"
    assert ChannelHealth("c", total=8, filled=3, abstained=1).missing == 4


def test_dominance_veto_is_reachable_through_the_real_triage_entrypoint(tmp_path):
    """The causal VETO arm, proven reachable -- with a SYNTHETIC receipt.

    Contract §10b: on live data the dominance veto cannot fire at all, because
    all-``None`` support leaves ``dominant_reason`` None.  Live traffic is
    therefore no evidence this arm works, and this test does not pretend
    otherwise -- it supplies a validator-owned support snapshot explicitly, the
    way a future validator channel will.  What it adds over the unit-level
    coverage is that the arm is reachable through ``triage()`` itself and lands
    on the persisted event, rather than only through the private gate function.
    """

    vault, repository, _paths = _acceptance_vault(tmp_path)
    result = _divergent_failure(vault, repository)
    run_id = _golden_path_run(repository)

    # A legacy-decisive signature, but the (synthetic) validator-owned causal
    # mass names a DIFFERENT reason. The route must downgrade, not commit.
    vetoed = FT.triage(
        repository,
        run_id,
        attempt={
            "attempt_id": result.attempt_id,
            "coarse_class": "wrong",
            "error_signature": "wrong_method",
            "grader_confidence": 0.95,
            "causal_support": {
                "support_authority": "validator_owned",
                "hypotheses": [
                    {
                        "hypothesis_id": "h_execution",
                        "triage_reason": "procedure_execution",
                        "support_score": 0.9,
                        "trace_consistency": "consistent_with_claims",
                    },
                    {
                        "hypothesis_id": "h_method",
                        "triage_reason": "method_selection",
                        "support_score": 0.1,
                        "trace_consistency": "consistent_with_claims",
                    },
                ],
            },
        },
    )
    assert vetoed.tier == "two"
    assert vetoed.tier_one_basis is None
    assert vetoed.decisive is False
    event = repository.failure_triage_event(vetoed.event_id)
    decision = json.loads(event["inputs_snapshot_json"])["triage_decision"]
    assert decision["causal_support_authority_approved"] is True
    assert decision["causal_dominant_reason"] == "procedure_execution"

    # ...and the same authority CONCENTRATED on the signature's own reason
    # promotes instead, on the causal arm.
    promoted = FT.triage(
        repository,
        run_id,
        attempt={
            "attempt_id": f"{result.attempt_id}_promote",
            "coarse_class": "wrong",
            "error_signature": "wrong_method",
            "grader_confidence": 0.2,  # the LEGACY arm cannot fire here
            "causal_support": {
                "support_authority": "validator_owned",
                "hypotheses": [
                    {
                        "hypothesis_id": "h_method",
                        "triage_reason": "method_selection",
                        "support_score": 0.95,
                        "trace_consistency": "consistent_with_claims",
                    }
                ],
            },
        },
    )
    assert promoted.tier == "one"
    assert promoted.tier_one_basis == FT.TIER_ONE_BASIS_CAUSAL


# --- helpers ----------------------------------------------------------------


def _zero_points(vault, item_id: str) -> dict[str, float]:
    item = vault.practice_items[item_id]
    return {criterion.id: 0.0 for criterion in item.grading_rubric.criteria}


def _full_points(vault, item_id: str) -> dict[str, float]:
    item = vault.practice_items[item_id]
    return {criterion.id: criterion.points for criterion in item.grading_rubric.criteria}


def _golden_path_run(repository: Repository) -> str:
    """A ``practice_only`` golden-path run in THIS vault, parked at ``triaging``.

    ``triage()`` reads the attempt (and therefore its diagnosis receipt) out of
    the repository it is handed, so the run has to live in the same sqlite as
    the causal attempt.  It is minted through the real confirm service rather
    than a hand-seeded row: no assessment surface is reserved, so the run is
    ``practice_only`` and makes no terminal claim -- all this walk needs is a
    legitimate run for the triage event to hang off.
    """

    spec = stub_blueprint()
    blueprint = TB.register_blueprint_version(
        repository, blueprint_slug="bp_causal_acceptance", spec=spec, clock=CLOCK
    )
    reviewed = TB.review_blueprint_version(
        repository,
        blueprint_version_id=blueprint.id,
        checks={"source_grounded": True, "rubric_verbatim": True, "one_family": True},
        clock=CLOCK,
    )
    receipt = GPC.confirm_exemplar_and_start(
        repository,
        goal_id="goal_causal_acceptance",
        blueprint_version_id=reviewed.id,
        contract_body={
            "purpose": "Recall and apply the SVD factorization",
            "facet_scope": {"concepts": ["singular_value_decomposition"]},
            "required_capabilities": ["retrieval", "method_selection"],
            "baseline_milestone": "m_svd_definition",
            "administration_conditions": {"tools": "none", "open_book": False},
            "exemplars": [
                {
                    "id": SOURCE_ITEM,
                    "surface_ref": SOURCE_ITEM,
                    "weight": 1.0,
                }
            ],
        },
        depth_preset="master_tasks_like_these",
        source_rev=spec["source_rev"],
        unit_id=spec["unit_id"],
        clock=CLOCK,
    )
    run_id = str(receipt.run_id)
    GPR.advance(
        repository, run_id, to_state="measuring", reason="baseline", idempotency_key="m"
    )
    GPR.advance(
        repository, run_id, to_state="triaging", reason="triage", idempotency_key="t"
    )
    return run_id
