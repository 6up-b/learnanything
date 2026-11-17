"""Classify pinned probes and record discriminating observations.

A feature source must be known, and the pinned classification must name a factor.
The admission ladder first rejects non-discriminating outcomes, then incomplete
measurement of declared features, then a production assessed as non-independent.
An admitted matched_single resolves the factor before its receipt is recorded;
an admitted open-set outcome records evidence without resolving a factor.
Support marked validator_owned is recorded for its readers only when admitted
features came from the deterministic sensor. Learner questions record an inert
embedded prediction without classification or factor resolution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from learnloop.causal_activity_policy import DISCRIMINATING_OUTCOMES
from learnloop.clock import Clock
from learnloop.db.repositories import (
    OBSERVATION_CHANNEL_BLIND_PROBE,
    OBSERVATION_CHANNEL_LEARNER_QUESTION,
    Repository,
)
from learnloop.diagnosis.causal_attribution import (
    CAUSAL_DECISION_POLICY_VERSION,
    SUPPORT_BASIS_AUTHORITY,
)
from learnloop.diagnosis.causal_probe_coherence import (
    bundle_feature_row_report,
    candidate_has_current_blind_input_contract,
    classify_against_blind_bundles,
)
from learnloop.diagnosis.causal_reads import CAUSAL_ORCHESTRATOR_FORMULA_VERSION, CausalRepairError
from learnloop.diagnosis.content_ids import content_id
from learnloop.vault.models import LoadedVault

#: The §7 evidence basis a blind-bundle classification carries.  It is a key of
#: `causal_attribution.SUPPORT_BASIS_AUTHORITY`, which is also what
#: `record_delayed_cold_verification` validates a caller-supplied basis against —
#: so an observation recorded here is citable there by id.
BLIND_PROBE_BASIS = "blind_probe_match"

#: Where an observed feature vector came from.  `unknown` exists on purpose:
#: a sensor that cannot say what it is must fail closed rather than inherit the
#: deterministic grant (standing constraint 2 — every enum keeps its abstention
#: arm).
OBSERVATION_FEATURE_SOURCES = (
    "deterministic",
    "model_extracted",
    "learner_declared",
    "unknown",
)
#: ...and the ONE source that earns `validator_owned` support authority.
VALIDATOR_OWNED_FEATURE_SOURCES = frozenset({"deterministic"})

#: Deterministic probe-feature vocabulary (see `deterministic_probe_features`).
DETERMINISTIC_FEATURE_PREFIX = "criterion:"


def pinned_causal_probe(
    repository: Repository, presentation_id: str
) -> dict[str, Any] | None:
    presentation = repository.probe_presentation(presentation_id)
    if presentation is None:
        return None
    components = presentation.selection_components or {}
    pinned = components.get("causal_probe")
    return dict(pinned) if isinstance(pinned, Mapping) else None


def classify_probe_response(
    repository: Repository,
    *,
    presentation_id: str,
    observed_features: Mapping[str, Any],
) -> dict[str, Any]:
    """Classify an administered causal probe against its PINNED bundles.

    The bundle ids come from the presentation, which froze them when the probe
    was minted.  A fresh ``causal_blind_prediction_bundles`` query would let a
    later bundle rewrite an earlier replay, which is exactly what the append-only
    substrate exists to prevent (§3.4).

    This function is a pure read: it classifies and returns, so a caller may
    preview a verdict without committing to it.  Acting on the verdict — closing
    the factor, recording support — is :func:`record_probe_classification`, which
    writes the §7 discriminating-observation receipt.  Diagnosis support moves
    only through that receipt, never as a side effect of repair success, and its
    id is what a later ``record_delayed_cold_verification`` cites as
    ``diagnosis_support_update={"basis": "blind_probe_match", ...}``.
    """

    pinned = pinned_causal_probe(repository, presentation_id)
    if pinned is None:
        raise CausalRepairError(
            "presentation carries no pinned causal probe candidate"
        )
    candidate = repository.causal_probe_candidate(
        str(pinned.get("causal_probe_candidate_id") or "")
    )
    if (
        candidate is None
        or not candidate_has_current_blind_input_contract(candidate)
    ):
        raise CausalRepairError(
            "pinned causal probe uses an obsolete observation-exposed blind "
            "input contract"
        )
    presentation = repository.probe_presentation(presentation_id)
    assert presentation is not None
    result = classify_against_blind_bundles(
        repository,
        hypothesis_set_id=str(pinned["hypothesis_set_id"]),
        practice_item_id=str(presentation.practice_item_id),
        blind_bundle_ids=[str(value) for value in pinned.get("blind_bundle_ids") or []],
        observed_features=observed_features,
    )
    return {
        **result,
        "presentation_id": presentation_id,
        "causal_factor_id": pinned.get("causal_factor_id"),
        "causal_probe_candidate_id": pinned.get("causal_probe_candidate_id"),
        "formula_version": CAUSAL_ORCHESTRATOR_FORMULA_VERSION,
    }


# --- the classification -> resolution edge (§6, §7) --------------------------


@dataclass(frozen=True)
class DiscriminatingObservation:
    """One classification, judged: what it may close and what it may not."""

    classification: dict[str, Any]
    receipt: dict[str, Any] | None
    admitted: bool
    admission_reason: str
    resolved_factor: bool
    support_authority: str | None
    support_scores: dict[str, float]

    @property
    def outcome(self) -> str:
        return str(self.classification.get("outcome") or "")

    @property
    def observation_id(self) -> str | None:
        return str(self.receipt["id"]) if self.receipt is not None else None

    def as_dict(self) -> dict[str, Any]:
        return {
            **self.classification,
            "admitted": self.admitted,
            "admission_reason": self.admission_reason,
            "resolved_factor": self.resolved_factor,
            "support_authority": self.support_authority,
            "support_scores": dict(self.support_scores),
            "observation_id": self.observation_id,
            "basis": BLIND_PROBE_BASIS,
        }


def _measured_hypotheses(
    repository: Repository,
    classification: Mapping[str, Any],
    observed_features: Mapping[str, Any],
) -> tuple[set[str], set[str]]:
    """Which of the locked set's concrete hypotheses the observation MEASURED.

    The matcher is exact over a bundle row's declared key set, so a hypothesis
    whose declared key was never observed and one whose declared key was
    observed-and-different both report ``matched: False``.  Only the second is
    evidence.  A hypothesis counts as measured when at least one of its declared
    rows had every key present in ``observed_features`` — a row is a
    conjunction, and several rows for one hypothesis are alternatives.

    Every concrete hypothesis of the locked set is considered, not just the
    evaluable ones: a rival with no pinned bundle, a version mismatch, or no
    parsable feature row was not tested either, and letting those fall outside
    the coverage question would resolve a factor on an instrument that never
    put the rival at risk.

    Returns ``(measured, unmeasured)``.
    """

    measured: set[str] = set()
    unmeasured: set[str] = set()
    evaluable = {
        str(value) for value in classification.get("evaluable_hypothesis_ids") or []
    }
    for detail in classification.get("details") or []:
        if not isinstance(detail, Mapping):
            continue
        hypothesis_id = str(detail.get("hypothesis_id") or "")
        if not hypothesis_id:
            continue
        if hypothesis_id not in evaluable:
            # No pinned bundle, a locked-version mismatch, or no parsable
            # feature row: whatever the observation contained, this arm was not
            # put at risk by it.
            unmeasured.add(hypothesis_id)
            continue
        covered = False
        for bundle_id in detail.get("bundle_ids") or []:
            bundle = repository.causal_blind_prediction_bundle(str(bundle_id))
            if bundle is None:
                continue
            report = bundle_feature_row_report(bundle["predictions"])
            for row in report.rows:
                if all(key in observed_features for key in row.keys):
                    covered = True
                    break
            if covered:
                break
        (measured if covered else unmeasured).add(hypothesis_id)
    return measured, unmeasured


def _observation_support_scores(
    classification: Mapping[str, Any], measured: set[str]
) -> dict[str, float]:
    """Support mass a discriminating observation licenses, and nothing more.

    ``matched_single`` puts all of it on the one hypothesis whose pre-registered
    prediction was borne out; every other MEASURED hypothesis is scored 0.0
    because its prediction was tested and failed.  An unmeasured hypothesis gets
    no entry at all — the resulting gap is what makes
    ``normalize_causal_support`` report ``incomplete`` and refuse promotion,
    which is the honest outcome for an instrument that did not test everything.
    """

    outcome = str(classification.get("outcome") or "")
    if outcome not in DISCRIMINATING_OUTCOMES:
        return {}
    matched = {
        str(value)
        for value in classification.get("classified_as") or []
        if not classification.get("supports_open_set")
    }
    return {
        hypothesis_id: (1.0 if hypothesis_id in matched else 0.0)
        for hypothesis_id in sorted(measured)
    }


def _probe_production_admissibility(
    repository: Repository, *, probe_attempt_id: str | None
) -> "ProductionAdmissibility | None":  # noqa: F821  imported in the body; postponed annotations never evaluate it
    """Was the probe answer produced before anything was revealed to it?

    ``None`` when there is no probe attempt to assess (an out-of-band
    classification: a replayed transcript, an adjudicated review). That is
    stored as a NULL ``admissible_as_independent``, which says "not assessed" —
    a different claim from "assessed and clean".
    """

    from learnloop.attempts.reveal_ledger import ProductionAdmissibility, production_admissibility

    if not probe_attempt_id:
        return None
    attempt = repository.fetch_practice_attempt(probe_attempt_id)
    if attempt is None:
        return None
    from learnloop.followup_serve.workflow import probe_answer_exposed

    exposed = probe_answer_exposed(
        repository, str(attempt.get("probe_presentation_id") or ""),
        answered_at=str(attempt.get("created_at") or "") or None,
    )
    if exposed is not None:
        # FG1 §6.0, §7: the learner took "Show anyway", the feedback was released before a
        # wait, or the causes were displayed before this answer (a recorded exposure, FG1c):
        # an answer it can't resolve the cause with, whatever the ledger.
        return ProductionAdmissibility(False, exposed)
    return production_admissibility(
        repository,
        practice_item_id=str(attempt.get("practice_item_id") or "") or None,
        learning_object_id=str(attempt.get("learning_object_id") or "") or None,
        produced_at=str(attempt.get("created_at") or "") or None,
        # The production judged, by id (UX Phase 4 round 4): only its own
        # frozen self-grade disclosure is exempt, never one matched by time.
        production_id=probe_attempt_id,
    )


#: The learner-question channel writes an observation that classifies nothing:
#: no bundle was pinned, so no declared feature was read. `unparsed_features` is
#: the outcome vocabulary's word for "could not be read", and paired with
#: `admitted = 0` it is inert everywhere the six outcomes are interpreted. The
#: row's meaning lives in its `channel` and `admission_reason`, not here.
_EMBEDDED_PREDICTION_OUTCOME = "unparsed_features"


def record_learner_embedded_prediction(
    repository: Repository,
    *,
    factor_id: str,
    prediction: str,
    question_event_id: str,
    attempt_id: str | None = None,
    practice_item_id: str | None = None,
    remediation_episode_id: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Record a falsifiable expectation the learner's OWN question asserted.

    Why this is a discriminating observation and not a note: it is a statement
    about the world that the learner committed to, in their words, and a later
    production can bear it out or contradict it. That is the same shape as a
    pinned blind prediction — the difference is only who authored it, and the
    ledger already has a ``learner_declared`` feature source waiting for
    exactly this.

    Why it is never ADMITTED: nothing was classified. There is no bundle, no
    cohort, no declared feature vector; admitting it would grant routing
    authority to an unclassified sentence. It is recorded so the expectation is
    on the record and so the factor shows engagement, and it resolves nothing.

    Why it is nonetheless ADMISSIBLE AS INDEPENDENT, whatever has been revealed:
    the question was written before the answer to it existed. Post-hoc exposure
    cannot reach backwards into a sentence the learner had already typed. This
    is the one channel where a reveal in the window does not contaminate.

    COST-FREE: no probe was consumed, no supply burned, no item spent.
    """

    prediction = (prediction or "").strip()
    if not prediction or not factor_id:
        return None
    identity = {
        "question_event_id": question_event_id,
        "factor_id": factor_id,
        "prediction": prediction,
    }
    return repository.insert_causal_discriminating_observation(
        observation_id=content_id("cdo", identity),
        factor_id=factor_id,
        attempt_id=attempt_id,
        probe_attempt_id=None,
        # No presentation exists; the question event IS the surface this
        # observation came from. Both columns are free-form text with no
        # foreign key, so naming the real source beats minting a fake probe.
        presentation_id=f"question_event:{question_event_id}",
        hypothesis_set_id=f"unlocked:{factor_id}",
        blind_bundle_ids=(),
        outcome=_EMBEDDED_PREDICTION_OUTCOME,
        classified_as=[],
        supports_open_set=False,
        feature_source="learner_declared",
        observed_features={"embedded_prediction": prediction},
        declared_keys_observed=False,
        admitted=False,
        admission_reason="learner_question_embedded_prediction",
        support_authority=None,
        support_scores={},
        resolved_factor=False,
        detail={
            "basis": "learner_question_embedded_prediction",
            "question_event_id": question_event_id,
            "practice_item_id": practice_item_id,
            "remediation_episode_id": remediation_episode_id,
            "cost_free": True,
        },
        decision_policy_version=CAUSAL_DECISION_POLICY_VERSION,
        formula_version=CAUSAL_ORCHESTRATOR_FORMULA_VERSION,
        channel=OBSERVATION_CHANNEL_LEARNER_QUESTION,
        admissible_as_independent=True,
        inadmissibility_reason=None,
        clock=clock,
    )


def record_probe_classification(
    repository: Repository,
    *,
    presentation_id: str,
    observed_features: Mapping[str, Any],
    feature_source: str,
    probe_attempt_id: str | None = None,
    clock: Clock | None = None,
) -> DiscriminatingObservation:
    """Classify an administered probe AND act on the verdict (§6, §7).

    This is the edge the P2 lane was missing.  A probe could be offered,
    accepted, served with pinned bundles, answered and classified — and then
    nothing consumed the verdict: no factor closed, no diagnosis support moved.

    What it will and will not close:

    * ``matched_single`` over features that actually MEASURED every evaluable
      hypothesis resolves the factor and records support.  Exactly one
      pre-registered blind prediction was borne out and the rivals' were tested
      and failed; that is a discriminating observation.
    * ``no_bundle_matched`` over the same coverage is genuine open-set evidence
      for ``H_OTHER`` (§3.5) and is recorded as such — but it resolves NOTHING.
      An open-world arm names no cause, so there is no branch-specific repair to
      unblock.
    * ``matched_multiple`` and ``all_bundles_matched`` mean the instrument did
      not discriminate; ``cohort_mismatch`` and ``unparsed_features`` mean it
      could not be read.  All four are recorded and resolve nothing.  Agent A3
      split these outcomes apart precisely so "the instrument failed" stops
      being indistinguishable from "the answer fits none of our causes".
    * Any outcome whose declared features were not observed is inadmissible,
      whatever it says.  See :func:`_measured_hypotheses`.

    SUPPORT AUTHORITY — the deliberate split (argued, not assumed):

    Resolving the factor and granting routing authority are different powers and
    are gated differently.

    * The FACTOR closes on any admitted ``matched_single``.  The epistemic guard
      there is pre-registration: the prediction was committed before the response
      existed, is content-addressed and append-only, was cohort-pinned, and
      passed the register -> review -> activate ladder plus a manipulation-contract
      audit.  Requiring a deterministic sensor as well would make the lane
      unreachable for every short-answer probe, which is most of them.
    * ``validator_owned`` SUPPORT is granted only
      when the observed features came from a deterministic sensor
      (``feature_source == "deterministic"``).  The match is deterministic; the
      *sensor* need not be, and a model reading "did the answer transpose?" out
      of prose is a model-reported quantity however deterministic the comparison
      downstream is.  Standing constraint 4 (deterministic quantities outrank
      model-reported ones) is a per-input rule, so the provenance is recorded
      per input rather than inferred from the pipeline's last step.
    * A model-extracted observation records discriminating support without
      gaining deterministic authority.  Keeping its sensor provenance prevents
      consumers from treating model-read features as validator-owned evidence.

    Diagnosis support moves ONLY through this receipt.  It is never a side
    effect of repair success, and it is deliberately not written back onto the
    diagnosis receipt: that lives in ``attempt_debug_payloads``, which replay
    rebuilds, so support written there would be silently discarded.
    """

    if feature_source not in OBSERVATION_FEATURE_SOURCES:
        raise ValueError(f"unknown observed-feature source {feature_source!r}")
    classification = classify_probe_response(
        repository,
        presentation_id=presentation_id,
        observed_features=observed_features,
    )
    factor_id = classification.get("causal_factor_id")
    if not factor_id:
        raise CausalRepairError(
            "pinned causal probe names no causal factor to observe"
        )
    factor_id = str(factor_id)
    factor = repository.unresolved_cause_factor(factor_id)
    attempt_id = str((factor or {}).get("attempt_id") or "") or None

    outcome = str(classification.get("outcome") or "")
    measured, unmeasured = _measured_hypotheses(
        repository, classification, observed_features
    )
    declared_keys_observed = not unmeasured and bool(measured)

    # Independence (migration 155). A probe answered AFTER the item's or its
    # learning object's answer was revealed is not an independent production:
    # the learner may be reporting what they were shown. This is checked before
    # admission, not after, because an inadmissible-as-independent observation
    # must never resolve a factor — that is precisely the loop by which a
    # revealed solution would close the factor its reveal contaminated.
    independence = _probe_production_admissibility(
        repository, probe_attempt_id=probe_attempt_id
    )

    if outcome not in DISCRIMINATING_OUTCOMES:
        admitted, admission_reason = False, f"non_discriminating_outcome:{outcome}"
    elif not declared_keys_observed:
        # The verdict is an artefact of what was not measured, not of what was.
        admitted, admission_reason = False, "declared_features_not_observed"
    elif independence is not None and not independence.admissible:
        admitted, admission_reason = False, str(independence.reason)
    else:
        admitted, admission_reason = True, f"{outcome}_over_measured_features"

    support_scores = (
        _observation_support_scores(classification, measured) if admitted else {}
    )
    support_authority = (
        SUPPORT_BASIS_AUTHORITY[BLIND_PROBE_BASIS]
        if admitted and feature_source in VALIDATOR_OWNED_FEATURE_SOURCES
        else None
    )

    identity = {
        "presentation_id": presentation_id,
        "blind_bundle_ids": sorted(
            str(value) for value in classification.get("blind_bundle_ids") or []
        ),
        "observed_features": dict(observed_features),
        "feature_source": feature_source,
        "outcome": outcome,
    }
    observation_id = content_id("cdo", identity)

    # Resolve BEFORE recording so the receipt can state truthfully whether it
    # was the observation that closed the factor.  A factor already closed by
    # another channel is not re-closed and the receipt says so.
    resolved = False
    if admitted and outcome == "matched_single":
        resolved = repository.resolve_unresolved_cause_factor(
            factor_id,
            resolution_observation_ids=[observation_id],
            clock=clock,
        )
    receipt = repository.insert_causal_discriminating_observation(
        observation_id=observation_id,
        factor_id=factor_id,
        attempt_id=attempt_id,
        probe_attempt_id=probe_attempt_id,
        presentation_id=presentation_id,
        hypothesis_set_id=str(classification.get("hypothesis_set_id") or ""),
        candidate_id=(
            str(classification["causal_probe_candidate_id"])
            if classification.get("causal_probe_candidate_id")
            else None
        ),
        blind_bundle_ids=identity["blind_bundle_ids"],
        outcome=outcome,
        classified_as=[
            str(value) for value in classification.get("classified_as") or []
        ],
        supports_open_set=bool(classification.get("supports_open_set")) and admitted,
        feature_source=feature_source,
        observed_features=dict(observed_features),
        declared_keys_observed=declared_keys_observed,
        admitted=admitted,
        admission_reason=admission_reason,
        support_authority=support_authority,
        support_scores=support_scores,
        resolved_factor=resolved,
        detail={
            "basis": BLIND_PROBE_BASIS,
            "measured_hypothesis_ids": sorted(measured),
            "unmeasured_hypothesis_ids": sorted(unmeasured),
            "classification_details": classification.get("details") or [],
            "cohort": classification.get("cohort"),
        },
        decision_policy_version=CAUSAL_DECISION_POLICY_VERSION,
        formula_version=CAUSAL_ORCHESTRATOR_FORMULA_VERSION,
        channel=OBSERVATION_CHANNEL_BLIND_PROBE,
        admissible_as_independent=(
            None if independence is None else independence.admissible
        ),
        inadmissibility_reason=(
            None if independence is None else independence.reason
        ),
        contaminating_reveal_event_id=(
            None if independence is None else independence.reveal_event_id
        ),
        clock=clock,
    )
    return DiscriminatingObservation(
        classification=classification,
        receipt=receipt,
        admitted=admitted,
        admission_reason=admission_reason,
        resolved_factor=resolved,
        support_authority=support_authority,
        support_scores=support_scores,
    )


def deterministic_probe_features(
    vault: LoadedVault, repository: Repository, attempt_id: str
) -> dict[str, Any]:
    """The graded probe attempt's own criterion outcomes, as a feature vector.

    ``{"criterion:<id>:passed": bool, "criterion:<id>:full_credit": bool}``,
    for the assessed criteria only (a PF-c unassessed criterion has no
    feature).

    This is the one probe sensor that runs no model: the values come from
    recorded grading evidence against the item's authored rubric.  A blind
    bundle whose predictions are declared in this vocabulary can therefore be
    classified automatically, with ``feature_source="deterministic"`` and the
    ``validator_owned`` grant it earns.  A bundle that declares anything else
    needs a sensor that can read it, and :func:`auto_classify_pinned_probe`
    declines rather than guessing.

    It is deliberately NOT a global feature registry (§3.1): bundles still
    declare their own key sets, and this vocabulary is simply the subset a
    deterministic sensor can supply.
    """

    attempt = repository.fetch_practice_attempt(attempt_id) or {}
    item = vault.practice_items.get(str(attempt.get("practice_item_id") or ""))
    rubric = vault.rubric_for_item(item) if item is not None else None
    if item is None or rubric is None:
        return {}
    from learnloop.substrate.canonical_projection import unassessed_evidence_row

    evidence = {
        row.criterion_id: row for row in repository.fetch_grading_evidence(attempt_id)
    }
    features: dict[str, Any] = {}
    for criterion in rubric.criteria:
        row = evidence.get(criterion.id)
        if row is not None and unassessed_evidence_row(row.attribution_json):
            # PF-c (review F3): an unassessed criterion was not measured, so it
            # supplies no feature - whatever points the grader left on it. A
            # bundle that declares it then fails the declared-feature check in
            # ``auto_classify_pinned_probe``, which declines.
            continue
        awarded = float(
            evidence[criterion.id].points_awarded
            if criterion.id in evidence
            else 0.0
        )
        possible = float(criterion.points)
        fraction = max(0.0, min(1.0, awarded / possible)) if possible > 0 else 0.0
        features[f"{DETERMINISTIC_FEATURE_PREFIX}{criterion.id}:passed"] = (
            fraction >= 0.40
        )
        features[f"{DETERMINISTIC_FEATURE_PREFIX}{criterion.id}:full_credit"] = (
            fraction >= 1.0 - 1e-9
        )
    return features


def auto_classify_pinned_probe(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    clock: Clock | None = None,
) -> DiscriminatingObservation | None:
    """Close the loop automatically when a probe answer can be read by machine.

    Runs on the live post-attempt path.  Returns ``None`` — recording nothing —
    unless the attempt consumed a presentation carrying a pinned causal probe
    AND every declared feature key of the pinned bundles is in the deterministic
    vocabulary :func:`deterministic_probe_features` supplies.

    That gate is not squeamishness.  The matcher is exact over declared keys, so
    handing it a feature vector that simply lacks those keys yields
    ``no_bundle_matched`` — which §3.5 defines as open-set evidence for
    ``H_OTHER``.  Auto-classifying against an incapable sensor would therefore
    manufacture evidence that the learner's cause is outside the hypothesis set,
    from a probe that was never actually read.  Declining is the only honest
    default; a bundle authored in the deterministic vocabulary needs no learner
    or app involvement at all.
    """

    attempt = repository.fetch_practice_attempt(attempt_id)
    if attempt is None:
        return None
    presentation_id = attempt.get("probe_presentation_id")
    if not presentation_id:
        return None
    pinned = pinned_causal_probe(repository, str(presentation_id))
    if not pinned or not pinned.get("blind_bundle_ids"):
        return None
    candidate = repository.causal_probe_candidate(
        str(pinned.get("causal_probe_candidate_id") or "")
    )
    if (
        candidate is None
        or not candidate_has_current_blind_input_contract(candidate)
    ):
        return None
    if repository.causal_discriminating_observations(
        presentation_id=str(presentation_id)
    ):
        # Already observed. Re-classifying the same probe from a second hook
        # would append a duplicate verdict under a new attempt id.
        return None
    features = deterministic_probe_features(vault, repository, attempt_id)
    if not features:
        return None
    declared: set[str] = set()
    for bundle_id in pinned["blind_bundle_ids"]:
        bundle = repository.causal_blind_prediction_bundle(str(bundle_id))
        if bundle is None:
            return None
        for row in bundle_feature_row_report(bundle["predictions"]).rows:
            declared.update(row.keys)
    if not declared or not declared <= set(features):
        return None
    return record_probe_classification(
        repository,
        presentation_id=str(presentation_id),
        observed_features=features,
        feature_source="deterministic",
        probe_attempt_id=attempt_id,
        clock=clock,
    )

