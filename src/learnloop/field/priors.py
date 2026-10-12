"""Time-frozen claim priors, using only historical LO/subject identities.

Concept membership is not snapshotted with an attempt, so concept-scoped claims
cannot safely be mapped through today's vault. Later claims are likewise not
backdated into the initial prior. Both omissions are counted in reports.
"""
from __future__ import annotations

from types import SimpleNamespace

from learnloop.clock import parse_utc
from learnloop.learner.mastery import initial_mastery_state_for_learning_object


def load_frozen_priors(connection, attempts, config):
    attempts = tuple(attempts)
    claims = [dict(row) for row in connection.execute("SELECT * FROM learner_claims")]
    cutoff = min((parse_utc(row.observed_at) for row in attempts), default=None)
    eligible, later, unmapped = [], 0, 0
    for claim in claims:
        when = parse_utc(claim["created_at"])
        if cutoff is None or when is None or when >= cutoff:
            later += 1
        elif claim["scope_type"] == "concept":
            unmapped += 1
        else:
            eligible.append(claim)
    los = {}
    for row in attempts:
        los.setdefault(row.lo_id, SimpleNamespace(
            id=row.lo_id, subjects=[row.features.subject_id], concept=None,
        ))
    vault = SimpleNamespace(config=config, learning_objects=los)
    repository = SimpleNamespace(learner_claims=lambda: eligible)
    lo_priors = {}
    for lo_id in sorted(los):
        state = initial_mastery_state_for_learning_object(vault, repository, lo_id, "frozen")
        lo_priors[lo_id] = (state.logit_mean, state.logit_variance)
    # The subject-level factor uses only claims covering the whole subject;
    # LO-specific claims seed the incumbent, not unrelated LO predictions.
    subject_claims = [c for c in eligible if c["scope_type"] != "learning_object"]
    repository = SimpleNamespace(learner_claims=lambda: subject_claims)
    general_means = {}
    for subject in sorted({row.features.subject_id for row in attempts}):
        subject_vault = SimpleNamespace(
            config=config,
            learning_objects={"subject": SimpleNamespace(id="subject", subjects=[subject], concept=None)},
        )
        state = initial_mastery_state_for_learning_object(subject_vault, repository, "subject", "frozen")
        general_means[subject] = state.logit_mean
    return general_means, lo_priors, {
        "version": "field-frozen-claims-v1",
        "claims": len(claims), "eligible_before_replay": len(eligible),
        "excluded_later_or_unordered": later, "excluded_missing_concept_mapping": unmapped,
        "policy": "Priors frozen strictly before the first historical attempt; no later claim is backdated.",
    }
