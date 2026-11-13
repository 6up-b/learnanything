"""What other test files use from ``tests/test_causal_p2_acceptance.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.diagnosis.causal_orchestrator import accept_probe_offer, causal_repair_status
from learnloop.diagnosis.causal_probe_coherence import (
    audit_manipulation_contract,
    create_probe_candidate,
    generate_blind_prediction_bundle,
    lock_causal_hypothesis_set,
    transition_probe_candidate,
)
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO, admit_probe_instrument_card
from tests.km2_write_path_helpers import KM2_OLD_TAG, SELECT, SHARED, build_mvp07_vault


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


def _acceptance_vault(tmp_path, *, version: str = KM2_OLD_TAG):
    """A synthetic vault (at ``version``; the tag its own tests were written at, which the learner/ gate's tests still
    read) with a probe surface and a cold surface.

    Both extra items live in their OWN source family: a cold verification is
    rejected outright when it shares a surface group with its source, and a
    near-clone probe never certifies (§4.3).
    """

    paths = build_mvp07_vault(tmp_path / "vault", version=version)
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
