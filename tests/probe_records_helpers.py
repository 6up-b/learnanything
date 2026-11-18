"""Production probe answers and explicit damaged-row fixtures for record tests."""

from dataclasses import replace

from learnloop import provenance
from learnloop.attempts.attempts import (
    ApplyAttemptInput, AttemptDraft, ResolvedGrade, SelfGradeInput, apply_attempt,
    complete_self_graded_attempt,
)
from learnloop.diagnosis.probe_episodes import enter_episode
from tests.causal_p2_acceptance_helpers import CLOCK, PROBE_ITEM, _acceptance_vault, _offered_probe
from tests.probe_episodes_helpers import ITEM_ID, LO_ID, _commit, _setup

DECLINES = (
    "pinned_bundles_empty", "candidate_not_current", "already_observed", "no_deterministic_rubric",
    "no_assessed_criterion", "pinned_bundle_missing", "declared_features_not_covered",
)


def answer(vault, repository, item_id, presentation_id, *, unassessed=False):
    draft = AttemptDraft(practice_item_id=item_id, learner_answer_md="private answer",
                         attempt_type="diagnostic_probe", probe_presentation_id=presentation_id)
    if not unassessed:
        return complete_self_graded_attempt(vault, repository, draft,
                                           SelfGradeInput(criterion_points={"correctness": 0}, confidence=3),
                                           clock=CLOCK)
    return apply_attempt(vault, repository, ApplyAttemptInput(
        draft=draft, attempt_id="att_unassessed_probe", grading_source="ai",
        unverified_criterion_ids=("correctness",),
        grade=ResolvedGrade(rubric_score=0, criterion_points={"correctness": 0},
                            evidence_rows=[{"id": "evidence_unassessed", "criterion_id": "correctness",
                                            "points_awarded": 0, "evidence": "private evidence",
                                            "notes": None, "local_grader_id": "test", "grader_tier": 3,
                                            "created_at": CLOCK.now().isoformat()}],
                            error_attributions=[], grader_confidence=0.9, confidence=3,
                            manual_review_reason="valid_alternative_unverified:correctness")), clock=CLOCK)


def declined_answer(tmp_path, code, patch):
    if code == "unpinned":
        root, vault, repository = _setup(tmp_path)
        episode = enter_episode(vault, repository, LO_ID, clock=CLOCK)
        offer = _commit(vault, repository, episode)
        with provenance.trace_scope("TRACE_PROBE_ANSWER"):
            result = answer(vault, repository, ITEM_ID, offer.id)
    else:
        vault, repository, paths = _acceptance_vault(tmp_path)
        root = paths.root
        features = None if code == "declared_features_not_covered" else (
            {"criterion:correctness:full_credit": False}, {"criterion:correctness:full_credit": True})
        source, _, _, _, offer = _offered_probe(vault, repository, features=features)
        with provenance.trace_scope("TRACE_PROBE_ANSWER"):
            result = answer(vault, repository, PROBE_ITEM, offer.presentation_id,
                            unassessed=code == "no_assessed_criterion")
        if code == "pinned_bundles_empty":
            # Serving refuses empty bundles; emulate a damaged persisted causal pin.
            patch.setattr("learnloop.diagnosis.causal_discrimination.pinned_causal_probe",
                          lambda *a: {"causal_probe_candidate_id": offer.candidate_id, "blind_bundle_ids": []})
        elif code == "candidate_not_current":
            # The serving ladder refuses obsolete candidates; emulate an old persisted pin.
            patch.setattr(repository, "causal_probe_candidate", lambda _id: {"id": offer.candidate_id,
                          "blind_input_contract_version": "obsolete"})
        elif code == "pinned_bundle_missing":
            # Current serving pins existing immutable bundles; emulate a damaged stored pin.
            patch.setattr(repository, "causal_blind_prediction_bundle", lambda _id: None)
        elif code == "no_deterministic_rubric":
            # The saved answer survives removing its authored item from the current vault.
            vault = replace(vault, practice_items={
                key: value for key, value in vault.practice_items.items() if key != PROBE_ITEM})
        elif code in ("already_observed", "own_observation"):
            from learnloop.diagnosis.causal_discrimination import record_probe_classification

            record_probe_classification(repository, presentation_id=offer.presentation_id,
                observed_features={"criterion:correctness:full_credit": False}, feature_source="deterministic",
                probe_attempt_id=source.attempt_id if code == "already_observed" else result.attempt_id, clock=CLOCK)
    return root, vault, repository, result
