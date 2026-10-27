"""Per-LO mastery EKF (spec_irt_difficulty.md §4).

KM3 demotion (knowledge-model §9.2): under mvp-0.7 the LO EKF is a
**prediction-only calibration residual**. It adjusts predicted performance
(consumed through ``selection_rewards.predicted_facet_recall`` as the mastery
backbone of a component's predicted recall) but carries **no certification
credit** — certification is derived independently from the immutable observation
ledger into ``facet_capability_evidence`` (see ``goal_certification``), never
from this filter. It also cannot absorb claims, item difficulty, familiarity, or
unidentified integration as interchangeable evidence: claims seed only the prior
(``initial_mastery_state_for_learning_object``), difficulty enters as the IRT
``b`` (an observation modifier, not a latent-skill term), and assistance enters
as the observation reliability weight. Legacy (mvp-0.6) behavior is unchanged.
"""

from __future__ import annotations

from collections.abc import Collection
from contextlib import nullcontext
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from math import copysign, exp, log, sqrt
from typing import TYPE_CHECKING, Any

from learnloop.algorithm_versions import CLAIM_FIXES_VERSIONS, SUPERSEDED_CLAIMS_VERSIONS
from learnloop.clock import parse_utc
from learnloop.config import MasteryConfig
from learnloop.db.repositories import ItemParameterState, MasteryState
from learnloop.numeric import clamp
from learnloop.attempts.evidence import attempt_evidence_mass

if TYPE_CHECKING:  # pragma: no cover - typing only
    from learnloop.vault.models import LearningObject, PracticeItem


@dataclass(frozen=True)
class MasteryObservation:
    rubric_score: int
    max_points: int
    evidence_coverage: float
    hint_dampening: float
    grader_confidence: float
    attempt_type: str
    observed_at: datetime
    item_coverage: float | None = None
    effective_coverage: float | None = None
    covered_facets: dict[str, float] | None = None
    facet_outcomes: dict[str, float] | None = None
    independent_evidence_discount: float = 1.0
    attempt_modifiers: dict[str, float] | None = None
    coverage_trace: dict[str, Any] | None = None
    reliability_trace: dict[str, Any] | None = None
    familiarity_trace: dict[str, Any] | None = None
    error_sharpening: float = 1.0
    observation_reliability: float | None = None
    observation_weight_override: float | None = None
    # Config-resolved evidence mass for attempt_type; None falls back to the
    # canonical defaults (DEFAULT_EVIDENCE) so test constructors keep working.
    attempt_evidence_mass: float | None = None
    # Primed retry (source just re-read): the belief still updates (with the
    # priming b-offset applied upstream) but last_evidence_at stays on the last
    # cold attempt so the spacing/drift clock is not reset.
    primed: bool = False
    # Prediction lane is mean-preserving (P1 revision): the EKF's y stays the
    # raw score fraction and grader-channel doubt enters ONLY through
    # interpretation_variance (Var[s(Z)|emission]) added to measurement noise.
    # soft_score_override remains for callers with a genuinely better point
    # observation (e.g. adjudicated regrades) — the attempt path passes None,
    # because substituting the channel posterior mean E[s(Z)|emission] shrank y
    # toward the prior and could move mastery against the observed direction.
    soft_score_override: float | None = None
    interpretation_variance: float = 0.0


@dataclass(frozen=True)
class MasteryDisplay:
    mastery_mean: float
    mastery_variance: float
    plausible_lower: float
    plausible_upper: float
    plausible_mass: float


@dataclass(frozen=True)
class IrtObservation:
    """The 2PL link linearized at the prior mean (spec_irt_difficulty.md §4.1).

    Shared by the Channel-1 mastery EKF and the probability-space surprise so
    both read the *same* observation mechanism for a given item.
    """

    p: float                    # predicted correctness sigma(a(mu - b)), clipped to p_clip
    sensitivity_h: float        # H = a * p(1-p)  (measurement sensitivity dp/dtheta)
    measurement_noise: float    # R_y = base * p(1-p) / max(weight, 0.10)
    predicted_variance: float   # P_pred = min(P + sigma2_drift * days_since, p_max)
    innovation_variance: float  # S = H^2 * P_pred + R_y
    kalman_gain: float          # K = P_pred * H / S


@dataclass(frozen=True)
class MasteryObservationTrace:
    """Full IRT picture of one mastery update, for debug logging (spec §7.1).

    Computed where the EKF math already runs; never re-queries state.
    """

    item_id: str
    difficulty_b: float
    discrimination_a: float
    theta_prior: float           # mu before
    expected_correctness: float  # p = sigma(a(mu - b))
    predicted_score: float       # max_points * p
    observed_y: float            # score / max_points
    innovation: float            # y - p (drives the mean move; the realized surprise)
    sensitivity_h: float         # H = a * p(1-p)
    fisher_information: float     # a^2 * p(1-p)  (the Channel-2 / selection quantity)
    measurement_noise: float     # R_y
    innovation_variance: float   # S = H^2 * P_pred + R_y
    kalman_gain: float           # K
    variance_reduction: float    # K * H  (fraction of P_pred removed)
    mu_before: float
    mu_after: float              # post step-cap and mu clamp
    mu_step: float               # mu_after - mu_before
    step_capped: bool
    mu_clamped: bool
    p_before: float
    p_after: float


def sigmoid(value: float) -> float:
    return 1 / (1 + exp(-value))


def logit(value: float) -> float:
    clipped = clamp(value, 0.02, 0.98)
    return log(clipped / (1 - clipped))


def display_mastery(state: MasteryState) -> MasteryDisplay:
    mean = sigmoid(state.logit_mean)
    variance = (mean * (1 - mean)) ** 2 * state.logit_variance
    # Central 80% interval of the Gaussian posterior in latent logit space,
    # transformed to the display probability scale. Computing it here avoids
    # the misleading probability-space approximation mean ± sqrt(variance).
    plausible_mass = 0.8
    central_80_z = 1.2815515655446004
    logit_sd = sqrt(max(state.logit_variance, 0.0))
    return MasteryDisplay(
        mastery_mean=mean,
        mastery_variance=variance,
        plausible_lower=sigmoid(state.logit_mean - central_80_z * logit_sd),
        plausible_upper=sigmoid(state.logit_mean + central_80_z * logit_sd),
        plausible_mass=plausible_mass,
    )


def initial_mastery_state(
    learning_object_id: str,
    algorithm_version: str,
    now_iso: str,
    *,
    logit_variance: float = 1.0,
) -> MasteryState:
    return MasteryState(
        learning_object_id=learning_object_id,
        logit_mean=0.0,
        logit_variance=logit_variance,
        evidence_count=0,
        last_evidence_at=None,
        algorithm_version=algorithm_version,
        updated_at=now_iso,
    )


def claim_fixes_live(vault) -> bool:
    """LP-min (a): the claim-fixes successor's tag AND its kill switch.

    ``mastery.claim_fixes_enabled`` off, or a version below
    ``CLAIM_FIXES_ALGORITHM_VERSION``: every claim seed, re-anchor, merge,
    ranking and replay is the predecessor's exactly. Read defensively because
    time-frozen callers (``field.priors``) pass a namespace vault.
    """

    config = getattr(vault, "config", None)
    algorithms = getattr(config, "algorithms", None)
    mastery = getattr(config, "mastery", None)
    return (
        getattr(algorithms, "algorithm_version", None) in CLAIM_FIXES_VERSIONS
        and bool(getattr(mastery, "claim_fixes_enabled", False))
    )


def replaced_claims_kept(vault) -> bool:
    """The successor mvp-0.36: the replace seam keeps a replaced claim (``superseded_by``).

    Below ``SUPERSEDED_CLAIMS_ALGORITHM_VERSION`` the seam deletes it, as the
    predecessor. No kill switch: no live reader sees a replaced row
    (``Repository.learner_claims`` reads the claims in force), so keeping it
    changes only what replay can apply."""

    config = getattr(vault, "config", None)
    algorithms = getattr(config, "algorithms", None)
    return getattr(algorithms, "algorithm_version", None) in SUPERSEDED_CLAIMS_VERSIONS


def _in_force(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The claims among ``claims`` that no claim among them replaced (successor mvp-0.36).

    ``claims`` are the claims made by one point of the stream: a replaced
    claim is in force there until the claim that replaced it was made. Rows
    written below the successor carry no ``superseded_by``, so this keeps
    them all."""

    made = {str(claim.get("id") or "") for claim in claims}
    return [claim for claim in claims if claim.get("superseded_by") is None or str(claim["superseded_by"]) not in made]


#: Claim sources whose writers re-anchor an already-materialized LO at the
#: claim's own time (``reanchor_mastery_from_claim``): rung-variant requests,
#: too-easy/too-hard reports and, from the claim-fixes successor on, tutor gap
#: declarations. Replay re-anchors exactly these at their own ``created_at``;
#: every other claim (the init wizard's global claim, a manual claim) acts
#: only when a mastery row is first materialized, as it does live.
REANCHORING_CLAIM_SOURCES: frozenset[str] = frozenset(
    {"rung_variant_request", "learner_report", "tutor_gap_declaration"}
)


def initial_mastery_state_for_learning_object(
    vault,
    repository,
    learning_object_id: str,
    now_iso: str,
    *,
    claims_made: Collection[str] | None = None,
) -> MasteryState:
    """The LO's prior: the cold start, or the covering claim's re-anchor.

    ``claims_made`` (replay under the claim-fixes successor): the ids of the
    claims made by this point of the stream, so a later claim never seeds an
    earlier observation. ``substrate.replay._ClaimStream`` places each claim
    among the LO's attempts where it was applied live (review F5, re-review
    F7). ``None`` reads every claim on record, which live is the same thing:
    no claim is created after now.

    Under the successor a claim moves the prior's mean only: the seeded
    variance never drops below the cold start's (spec §3.0b, "the variance
    never drops below the prior's"; AD §5.5; review F4). The floor is the
    configured cold-start variance itself, so no new number.

    Nor does a later claim drop the variance an earlier one left (re-review
    F8). Live, each re-anchor of a zero-evidence row keeps the row's variance
    when it is the larger (``_reanchor_in_transaction``). So the seed here is
    the covering claim's mean with the largest variance that any re-anchoring
    claim's own seed had at its point, in the order the claims were made. The
    rebuild of an attempt-free LO, the seed before the first replayed attempt
    and the activation's re-seed all read this, so each agrees with the live
    row. A structural ``max`` over seeds already computed, no new number.
    """

    mastery_config = vault.config.mastery
    cold = initial_mastery_state(
        learning_object_id,
        vault.config.algorithms.algorithm_version,
        now_iso,
        logit_variance=float(mastery_config.cold_start_prior_logit_variance),
    )
    fixes = claim_fixes_live(vault)
    made = _claims_made(vault, repository, learning_object_id, claims_made, fixes=fixes)
    claims = _in_force(made)
    claim = _winning_claim(claims, fixes=fixes)
    if claim is None:
        return cold
    state = _claim_seed(vault, claim, cold, now_iso, fixes=fixes)
    if fixes:
        retained = _retained_cold_variance(vault, made, learning_object_id, cold, now_iso)
        if retained > state.logit_variance:
            state = replace(state, logit_variance=retained)
    return state


def _claim_seed(vault, claim: dict[str, Any], cold: MasteryState, now_iso: str, *, fixes: bool) -> MasteryState:
    """The zero-evidence state ``claim`` seeds."""

    mastery_config = vault.config.mastery
    # Any covering claim seeds the prior (spec_tutor_promotion.md §3 G2): a low
    # self-rating (e.g. a tutor gap declaration at claimed_level 0.25, or an
    # init-wizard low claim) must move the prior, not silently no-op as it did
    # when this gated on claim_skip_threshold. That threshold keeps its role ONLY
    # in probes.py (probe skip / attempt-target). The low floor 0.05 stops a
    # claimed_level of 0 from seeding an absurdly confident prior; the high side
    # stays at logit()'s native 0.98 clamp. Claims move the mean; the variance
    # floor keeps a self-report from impersonating measured evidence.
    claimed_level = float(claim["claimed_level"])
    prior_pseudo_count = max(float(claim["prior_pseudo_count"]), 0.25)
    seeded_variance = max(1 / prior_pseudo_count, float(mastery_config.claim_prior_min_variance))
    if fixes:
        # Mean only (review F4): the claim never makes the prior more certain
        # than the cold start it replaces.
        seeded_variance = max(seeded_variance, cold.logit_variance)
    return MasteryState(
        learning_object_id=cold.learning_object_id,
        logit_mean=logit(clamp(claimed_level, 0.05, 0.98)),
        logit_variance=seeded_variance,
        evidence_count=0,
        last_evidence_at=None,
        algorithm_version=vault.config.algorithms.algorithm_version,
        updated_at=now_iso,
    )


def _retained_cold_variance(
    vault, claims: list[dict[str, Any]], learning_object_id: str, cold: MasteryState, now_iso: str
) -> float:
    """The largest variance a re-anchoring claim's seed left on the zero-evidence row (re-review F8).

    Each re-anchoring claim on this LO re-seeded the row from the claims made
    by its own point (those before it in the ``(created_at, id)`` order, then
    itself). Every claim in ``claims`` is placed before the point the caller
    seeds at, so in a zero-evidence stretch that order is the order they were
    applied in. ``claims`` are the claims made by the caller's point, replaced
    ones included (each anchor reads the claims in force at its own point)."""

    best = cold.logit_variance
    anchors = [
        claim
        for claim in claims
        if str(claim.get("source")) in REANCHORING_CLAIM_SOURCES
        and claim.get("scope_type") == "learning_object"
        and claim.get("scope_id") == learning_object_id
    ]
    for anchor in anchors:
        point = _made_order(anchor)
        # A replaced anchor re-seeded the row too (successor mvp-0.36): at its
        # point it was in force, and the claims replaced by then were not.
        winner = _winning_claim(_in_force([claim for claim in claims if _made_order(claim) <= point]), fixes=True)
        if winner is not None:
            best = max(best, _claim_seed(vault, winner, cold, now_iso, fixes=True).logit_variance)
    return best


def _made_order(claim: dict[str, Any]) -> tuple[float, str]:
    """A claim's place in the ``(created_at, id)`` order; an unparseable stamp sorts first."""

    created = _parse_instant(claim.get("created_at"))
    return (created.timestamp() if created is not None else float("-inf"), str(claim.get("id") or ""))


def apply_claim_evidence(
    state: MasteryState,
    *,
    claimed_level: float,
    prior_pseudo_count: float,
    now_iso: str,
    mean_only: bool = False,
) -> MasteryState:
    """Precision-weighted merge of a learner claim into an existing state.

    Claims arriving AFTER a mastery row exists (a rung-variant request, a
    too-easy report) were previously inert — covering_learner_claim only feeds
    first materialization. Treating the claim as a Gaussian observation in
    logit space (mean logit(level), variance 1/pseudo_count) gives learner
    reports standing weight against accumulated evidence: strong on a
    near-prior state, proportionally weaker once real observations exist.

    ``mean_only`` (the claim-fixes successor; AD §5.5, "a claim moves a mean
    and never shrinks a variance"): the mean moves by the same precision
    weights, but the variance is floored at the state's own variance, so a
    self-report never impersonates measured evidence. The floor is the state's
    variance itself (structural: ``max(merged, current)``), no new constant.
    """

    claim_mean = logit(clamp(float(claimed_level), 0.05, 0.98))
    claim_variance = 1 / max(float(prior_pseudo_count), 0.25)
    prior_precision = 1 / max(state.logit_variance, 1e-6)
    claim_precision = 1 / claim_variance
    merged_precision = prior_precision + claim_precision
    merged_mean = (
        state.logit_mean * prior_precision + claim_mean * claim_precision
    ) / merged_precision
    merged_variance = 1 / merged_precision
    if mean_only:
        merged_variance = max(merged_variance, state.logit_variance)
    return MasteryState(
        learning_object_id=state.learning_object_id,
        logit_mean=merged_mean,
        logit_variance=merged_variance,
        evidence_count=state.evidence_count,
        last_evidence_at=state.last_evidence_at,
        algorithm_version=state.algorithm_version,
        updated_at=now_iso,
    )


def reanchor_mastery_from_claim(
    vault,
    repository,
    learning_object_id: str,
    *,
    claimed_level: float,
    prior_pseudo_count: float,
    now_iso: str,
    claims_made: Collection[str] | None = None,
    claim_id: str | None = None,
) -> MasteryState:
    """Make a newly written claim take effect on an already-materialized LO.

    Zero-evidence states are fully re-seeded (the claim IS the prior); states
    with evidence get the precision-weighted merge, mean-only under the
    claim-fixes successor. ``claims_made`` is replay's: the re-seed reads only
    the claims made by the claim's own point in the stream. Under the
    successor a zero-evidence re-seed also keeps the state's own variance
    (review F4: the seed is floored at the cold start, and a materialized
    row's variance is never lowered by a claim). Persists and returns the
    updated state.

    Under the successor the read and the write are one ``BEGIN IMMEDIATE``
    transaction (review F1; a savepoint inside a caller's): a concurrent
    attempt's mastery update lands wholly before the read or after the write,
    never between them, so this cannot overwrite it with a stale state.

    ``claim_id`` is the live writer's: the claim it just wrote. In the same
    transaction the claim records how many of the LO's attempts had been
    applied (``learner_claims.applied_after_attempts``, re-review F7), which
    is the claim's place among them for replay. An attempt's id is reserved
    before grading, so a stamp and an id cannot give that place. Replay never
    passes it, and below the successor nothing is recorded.
    """

    # Gated with the successor so the predecessor's writes stay exactly its own.
    fixes = claim_fixes_live(vault)
    with repository.atomic() if fixes else nullcontext():
        if fixes and claim_id is not None:
            repository.record_learner_claim_application(claim_id, learning_object_id)
        return _reanchor_in_transaction(
            vault,
            repository,
            learning_object_id,
            claimed_level=claimed_level,
            prior_pseudo_count=prior_pseudo_count,
            now_iso=now_iso,
            claims_made=claims_made,
        )


def _reanchor_in_transaction(
    vault,
    repository,
    learning_object_id: str,
    *,
    claimed_level: float,
    prior_pseudo_count: float,
    now_iso: str,
    claims_made: Collection[str] | None,
) -> MasteryState:
    current = repository.mastery_state(learning_object_id)
    if current is None or current.evidence_count == 0:
        updated = initial_mastery_state_for_learning_object(
            vault, repository, learning_object_id, now_iso, claims_made=claims_made,
        )
        if current is not None and claim_fixes_live(vault) and current.logit_variance > updated.logit_variance:
            updated = replace(updated, logit_variance=current.logit_variance)
    else:
        updated = apply_claim_evidence(
            current,
            claimed_level=claimed_level,
            prior_pseudo_count=prior_pseudo_count,
            now_iso=now_iso,
            mean_only=claim_fixes_live(vault),
        )
    repository.upsert_mastery_state(updated)
    return updated


def covering_learner_claim(
    vault, repository, learning_object_id: str, *, claims_made: Collection[str] | None = None
) -> dict[str, Any] | None:
    """The one claim that seeds ``learning_object_id``'s prior, or None.

    The most specific covering claim wins. Among equally specific claims the
    predecessor preferred the larger pseudo-count, then the HIGHER claimed
    level; under the claim-fixes successor the most recent claim wins, then
    the larger pseudo-count, and the level never breaks a tie (a learner who
    revises a claim downward is believed). ``claims_made`` keeps only those
    claims (replay: the claims made by a point of the stream). It is honoured
    only under the successor, so the predecessor's replay is unchanged.
    """

    fixes = claim_fixes_live(vault)
    made = _claims_made(vault, repository, learning_object_id, claims_made, fixes=fixes)
    return _winning_claim(_in_force(made), fixes=fixes)


def _claims_made(
    vault, repository, learning_object_id: str, claims_made: Collection[str] | None, *, fixes: bool
) -> list[dict[str, Any]]:
    """The covering claims made by the caller's point: replay's ``claims_made``, else those in force now.

    Replay (``claims_made``, under the claim-fixes successor) reads the
    replaced claims too, so a claim replaced after its point is in force there
    (successor mvp-0.36; :func:`_in_force` drops the ones replaced by then).
    Live (``None``) reads the claims in force: no claim is made after now."""

    if not (fixes and claims_made is not None):
        return covering_claims(vault, repository, learning_object_id)
    return [
        claim
        for claim in covering_claims(vault, repository, learning_object_id, include_superseded=True)
        if str(claim.get("id") or "") in claims_made
    ]


def covering_claims(
    vault, repository, learning_object_id: str, *, include_superseded: bool = False
) -> list[dict[str, Any]]:
    """Every learner claim in force that covers ``learning_object_id`` (any scope).

    ``include_superseded`` (replay): the replaced claims too (successor
    mvp-0.36, ``learner_claims.superseded_by``)."""

    learning_object = vault.learning_objects.get(learning_object_id)
    if learning_object is None:
        return []
    rows = repository.learner_claims(include_superseded=True) if include_superseded else repository.learner_claims()
    return [claim for claim in rows if _claim_covers_learning_object(claim, learning_object)]


def _winning_claim(claims: list[dict[str, Any]], *, fixes: bool) -> dict[str, Any] | None:
    if not claims:
        return None
    return max(claims, key=_claim_rank_by_recency if fixes else _claim_rank)


def learning_objects_with_covering_claims(vault, repository, learning_object_ids) -> list[str]:
    """The given LOs that at least one learner claim covers, sorted.

    Exactly the LOs whose replay the claim-fixes successor can change: with no
    covering claim there is no seed, no re-anchor and no tie to break.
    """

    claims = repository.learner_claims()
    if not claims:
        return []
    covered: list[str] = []
    for learning_object_id in sorted(set(learning_object_ids)):
        learning_object = vault.learning_objects.get(learning_object_id)
        if learning_object is None:
            continue
        if any(_claim_covers_learning_object(claim, learning_object) for claim in claims):
            covered.append(learning_object_id)
    return covered


def _claim_covers_learning_object(claim: dict[str, Any], learning_object) -> bool:
    scope_type = claim.get("scope_type")
    scope_id = claim.get("scope_id")
    if scope_type == "global":
        return True
    if scope_type == "learning_object":
        return scope_id == learning_object.id
    if scope_type == "concept":
        return scope_id == learning_object.concept
    if scope_type in {"subject", "domain"}:
        return scope_id is None or scope_id in set(learning_object.subjects)
    return False


def _claim_rank(claim: dict[str, Any]) -> tuple[int, float, float, str, str]:
    specificity = {
        "learning_object": 4,
        "concept": 3,
        "subject": 2,
        "domain": 2,
        "global": 1,
    }.get(str(claim.get("scope_type")), 0)
    return (
        specificity,
        float(claim.get("prior_pseudo_count") or 0.0),
        float(claim.get("claimed_level") or 0.0),
        str(claim.get("created_at") or ""),
        str(claim.get("id") or ""),
    )


def _parse_instant(value: Any) -> datetime | None:
    try:
        return parse_utc(str(value)) if value else None
    except ValueError:
        return None


def _claim_rank_by_recency(claim: dict[str, Any]) -> tuple[int, float, float, str]:
    """The claim-fixes successor's order: specificity, recency, pseudo-count.

    Recency is the parsed ``created_at`` (an unparseable stamp sorts oldest);
    the id is the last, deterministic tie-break. ``claimed_level`` is not in
    the key at all.
    """

    created = _parse_instant(claim.get("created_at"))
    specificity = _claim_rank(claim)[0]
    return (
        specificity,
        created.timestamp() if created is not None else float("-inf"),
        float(claim.get("prior_pseudo_count") or 0.0),
        str(claim.get("id") or ""),
    )


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def observation_weight(observation: MasteryObservation) -> float:
    """Reliability weight of an observation (spec §4.1).

    Low-confidence / self-graded / hinted attempts move ``mu`` less.
    """

    if observation.observation_weight_override is not None:
        return max(0.0, observation.observation_weight_override)
    attempt_factor = (
        observation.attempt_evidence_mass
        if observation.attempt_evidence_mass is not None
        else attempt_evidence_mass(observation.attempt_type)
    )
    return (
        clamp(observation.evidence_coverage, 0.0, 1.0)
        * clamp(observation.hint_dampening, 0.0, 1.0)
        * clamp(observation.grader_confidence, 0.0, 1.0)
        * attempt_factor
    )


def predicted_logit_variance(
    prior: MasteryState,
    observation: MasteryObservation,
    config: MasteryConfig,
) -> float:
    """``P_pred = min(P + sigma2_drift * days_since, p_max)`` — prior variance grown by drift."""

    last_evidence_at = parse_utc(prior.last_evidence_at)
    days_since = 0.0
    if last_evidence_at is not None:
        days_since = max(0.0, (observation.observed_at - last_evidence_at).total_seconds() / 86400)
    return min(prior.logit_variance + config.sigma2_drift * days_since, config.p_max)


def item_irt_params(
    item: "PracticeItem | None",
    learning_object: "LearningObject | None",
    config: MasteryConfig,
) -> tuple[float, float]:
    """Resolve ``(a, b)`` for an item from **static** authored/LLM fields (spec §4.3).

    ``b`` falls back ``PracticeItem.difficulty`` -> ``LearningObject.difficulty_prior``
    -> ``difficulty_default``. The FSRS ``practice_item_state.difficulty`` is never
    consulted — only the static vault field.
    """

    irt = config.irt
    a = irt.discrimination_default
    if not irt.difficulty_from_prior:
        return a, irt.difficulty_default
    difficulty = getattr(item, "difficulty", None) if item is not None else None
    if difficulty is None and learning_object is not None:
        difficulty = getattr(learning_object, "difficulty_prior", None)
    if difficulty is None:
        return a, irt.difficulty_default
    b = irt.difficulty_prior_scale * (float(difficulty) - 0.5) * 2.0
    return a, clamp(b, -irt.b_abs_max, irt.b_abs_max)


def resolve_item_irt_params(
    item: "PracticeItem | None",
    learning_object: "LearningObject | None",
    config: MasteryConfig,
    item_state: "ItemParameterState | None" = None,
) -> tuple[float, float]:
    """(a, b) with the empirical-Bayes posterior b when enabled, else authored.

    The single seam through which the mastery EKF, surprise, and prediction all
    read item parameters — so a fitted b moves all three consistently.
    """

    a, authored_b = item_irt_params(item, learning_object, config)
    irt = config.irt
    if not irt.eb_difficulty_enabled or item_state is None:
        return a, authored_b
    return a, clamp(item_state.b_mean, -irt.b_abs_max, irt.b_abs_max)


def update_item_difficulty(
    prior: "ItemParameterState | None",
    *,
    practice_item_id: str,
    authored_b: float,
    item_a: float,
    learner_mu_posterior: float,
    observation: MasteryObservation,
    config: MasteryConfig,
    algorithm_version: str,
    updated_at: str,
) -> "ItemParameterState":
    """Alternating conditional EKF step on item difficulty b.

    Symmetric to the mu update but holding the learner's posterior mean fixed:
    dp/db = -a*p(1-p), same reliability-gated measurement noise. Identifiability
    at N=1 is handled by a strong prior (b_prior_variance), a slowed gain
    (b_learning_rate_scale) and a per-attempt step clamp — b must drift only
    when the evidence persistently contradicts the authored difficulty.
    """

    irt = config.irt
    b0 = prior.b_mean if prior is not None else authored_b
    v0 = prior.b_var if prior is not None else irt.b_prior_variance
    evidence_count = prior.evidence_count if prior is not None else 0

    p_raw = sigmoid(item_a * (learner_mu_posterior - b0))
    p = clamp(p_raw, irt.p_clip, 1.0 - irt.p_clip)
    pq = p * (1.0 - p)
    sensitivity_h = -item_a * pq  # success pushes b DOWN
    weight = observation_weight(observation)
    measurement_noise = config.base_observation_variance * pq / max(weight, 0.10)
    innovation_variance = sensitivity_h * sensitivity_h * v0 + measurement_noise
    gain = (v0 * sensitivity_h / innovation_variance) if innovation_variance > 0 else 0.0
    gain *= irt.b_learning_rate_scale

    y = observation.rubric_score / max(observation.max_points, 1)
    step = clamp(gain * (y - p), -irt.b_max_step, irt.b_max_step)
    b1 = clamp(b0 + step, -irt.b_abs_max, irt.b_abs_max)
    v1 = max((1.0 - gain * sensitivity_h) * v0, irt.b_var_min)  # no drift: items don't change
    return ItemParameterState(
        practice_item_id=practice_item_id,
        b_mean=b1,
        b_var=v1,
        evidence_count=evidence_count + 1,
        algorithm_version=algorithm_version,
        updated_at=updated_at,
    )


def irt_observation(
    item_a: float,
    item_b: float,
    prior: MasteryState,
    observation: MasteryObservation,
    config: MasteryConfig,
) -> IrtObservation:
    """Linearize the 2PL link at the prior mean (spec §4.1).

    ``R_y`` carries the Bernoulli variance ``p(1-p)`` so the ``p(1-p)`` cancels in
    ``K`` and the gain stays well-defined as ``p -> 0/1``.
    """

    irt = config.irt
    p_raw = sigmoid(item_a * (prior.logit_mean - item_b))
    p = clamp(p_raw, irt.p_clip, 1.0 - irt.p_clip)
    pq = p * (1.0 - p)
    sensitivity_h = item_a * pq
    weight = observation_weight(observation)
    measurement_noise = (
        config.base_observation_variance * pq / max(weight, 0.10)
        + max(0.0, observation.interpretation_variance)
    )
    predicted_variance = predicted_logit_variance(prior, observation, config)
    innovation_variance = sensitivity_h * sensitivity_h * predicted_variance + measurement_noise
    kalman_gain = predicted_variance * sensitivity_h / innovation_variance if innovation_variance > 0 else 0.0
    return IrtObservation(
        p=p,
        sensitivity_h=sensitivity_h,
        measurement_noise=measurement_noise,
        predicted_variance=predicted_variance,
        innovation_variance=innovation_variance,
        kalman_gain=kalman_gain,
    )


def update_mastery(
    prior: MasteryState,
    observation: MasteryObservation,
    config: MasteryConfig,
    algorithm_version: str,
    *,
    item_a: float = 1.0,
    item_b: float = 0.0,
) -> MasteryState:
    state, _trace = update_mastery_traced(
        prior, observation, config, algorithm_version, item_a=item_a, item_b=item_b
    )
    return state


def update_mastery_traced(
    prior: MasteryState,
    observation: MasteryObservation,
    config: MasteryConfig,
    algorithm_version: str,
    *,
    item_a: float = 1.0,
    item_b: float = 0.0,
    item_id: str = "",
) -> tuple[MasteryState, MasteryObservationTrace]:
    """Difficulty-aware mastery update returning the posterior plus an IRT trace.

    With ``config.irt.enabled`` the probability-space EKF of §4.1 runs; otherwise
    the legacy logit-space Kalman update is reproduced bit-for-bit (§6.2).
    """

    if not config.irt.enabled:
        return _legacy_update_mastery(prior, observation, config, algorithm_version, item_a, item_b, item_id)
    return _ekf_update_mastery(prior, observation, config, algorithm_version, item_a, item_b, item_id)


def _ekf_update_mastery(
    prior: MasteryState,
    observation: MasteryObservation,
    config: MasteryConfig,
    algorithm_version: str,
    item_a: float,
    item_b: float,
    item_id: str,
) -> tuple[MasteryState, MasteryObservationTrace]:
    irt = config.irt
    max_points = max(observation.max_points, 1)
    y = clamp(
        observation.soft_score_override
        if observation.soft_score_override is not None
        else observation.rubric_score / max_points,
        0.0,
        1.0,
    )
    obs = irt_observation(item_a, item_b, prior, observation, config)

    mu_before = prior.logit_mean
    innovation = y - obs.p
    mu_raw = mu_before + obs.kalman_gain * innovation

    # Step cap: the single linearization can overshoot on a broad prior with an
    # extreme observation; K is not bounded by 1 (spec §4.4).
    step = mu_raw - mu_before
    step_capped = abs(step) > irt.max_logit_step
    if step_capped:
        mu_raw = mu_before + copysign(irt.max_logit_step, step)

    # mu sanity clamp (mean only; leave P_new from the filter).
    mu_after = clamp(mu_raw, -irt.mu_abs_max, irt.mu_abs_max)
    mu_clamped = mu_after != mu_raw

    variance_reduction = obs.kalman_gain * obs.sensitivity_h
    next_variance = (1.0 - variance_reduction) * obs.predicted_variance

    state = MasteryState(
        learning_object_id=prior.learning_object_id,
        logit_mean=mu_after,
        logit_variance=next_variance,
        evidence_count=prior.evidence_count + 1,
        # Primed attempts keep the cold-attempt anchor: advancing it would let a
        # source-fresh retry suppress drift growth and defer the scheduled review.
        last_evidence_at=prior.last_evidence_at if observation.primed else _iso(observation.observed_at),
        algorithm_version=algorithm_version,
        updated_at=_iso(observation.observed_at),
    )
    trace = MasteryObservationTrace(
        item_id=item_id,
        difficulty_b=item_b,
        discrimination_a=item_a,
        theta_prior=mu_before,
        expected_correctness=obs.p,
        predicted_score=max_points * obs.p,
        observed_y=y,
        innovation=innovation,
        sensitivity_h=obs.sensitivity_h,
        fisher_information=item_a * obs.sensitivity_h,
        measurement_noise=obs.measurement_noise,
        innovation_variance=obs.innovation_variance,
        kalman_gain=obs.kalman_gain,
        variance_reduction=variance_reduction,
        mu_before=mu_before,
        mu_after=mu_after,
        mu_step=mu_after - mu_before,
        step_capped=step_capped,
        mu_clamped=mu_clamped,
        p_before=obs.p,
        p_after=sigmoid(item_a * (mu_after - item_b)),
    )
    return state, trace


def _legacy_update_mastery(
    prior: MasteryState,
    observation: MasteryObservation,
    config: MasteryConfig,
    algorithm_version: str,
    item_a: float,
    item_b: float,
    item_id: str,
) -> tuple[MasteryState, MasteryObservationTrace]:
    """The pre-IRT logit-space Kalman update, reproduced bit-for-bit (spec §6.2)."""

    y = clamp(observation.rubric_score / max(observation.max_points, 1), 0.02, 0.98)
    z_obs = logit(y)
    observation_variance = config.base_observation_variance / max(observation_weight(observation), 0.10)
    predicted_variance = predicted_logit_variance(prior, observation, config)
    kalman_gain = predicted_variance / (predicted_variance + observation_variance)
    next_mean = prior.logit_mean + kalman_gain * (z_obs - prior.logit_mean)
    next_variance = (1 - kalman_gain) * predicted_variance
    state = MasteryState(
        learning_object_id=prior.learning_object_id,
        logit_mean=next_mean,
        logit_variance=next_variance,
        evidence_count=prior.evidence_count + 1,
        last_evidence_at=prior.last_evidence_at if observation.primed else _iso(observation.observed_at),
        algorithm_version=algorithm_version,
        updated_at=_iso(observation.observed_at),
    )
    p_before = sigmoid(prior.logit_mean)
    observed_y = observation.rubric_score / max(observation.max_points, 1)
    trace = MasteryObservationTrace(
        item_id=item_id,
        difficulty_b=item_b,
        discrimination_a=item_a,
        theta_prior=prior.logit_mean,
        expected_correctness=p_before,
        predicted_score=max(observation.max_points, 1) * p_before,
        observed_y=observed_y,
        innovation=observed_y - p_before,
        sensitivity_h=0.0,
        fisher_information=0.0,
        measurement_noise=observation_variance,
        innovation_variance=predicted_variance + observation_variance,
        kalman_gain=kalman_gain,
        variance_reduction=kalman_gain,
        mu_before=prior.logit_mean,
        mu_after=next_mean,
        mu_step=next_mean - prior.logit_mean,
        step_capped=False,
        mu_clamped=False,
        p_before=p_before,
        p_after=sigmoid(next_mean),
    )
    return state, trace
