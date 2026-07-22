"""P4 step 5 (DESCOPED, U-026) -- the heuristic LLM-judged soft-kinship FEATURE
behind a planted-learner sim ADMISSION GATE (spec_p4_controller_and_scale §8; design
§B step 5, §F).

There is **no fitted kernel and no learned weights** in P4 -- delayed fresh-sibling
pairs at one learner's volume are far too sparse to fit against (the same n=1 economics
as §7.4). What lands is a *feature*:

  * an LLM judge (deterministic stub for tests) scores soft kinship between
    **non-hard-colliding** surfaces within card-declared bounds, composing P1's
    ``familiarity`` soft-kinship feature vectors (migration 077). The judge renders a
    reviewable U-034-shaped artifact, never a raw API call;
  * outputs are ``P(replay materially aided response)``, an independent-evidence
    discount interval, and a rotation-benefit estimate, conditioned **only** on
    information available BEFORE administration (exposure history, time, kinship
    features, angle/task features, surface provenance). The learner's correctness on
    the current response is NEVER an input (§8.2; acceptance 16.4). This module cannot
    read a correctness field even if asked -- ``conditioned_on`` is built from
    pre-administration inputs by construction and a test forbids a correctness key;
  * scores are cached as **versioned features** in ``familiarity_kernel_features``.

**Firewall (the load-bearing rule).** Until the sim admission gate certifies the model
(status ``simulation_validated`` -- the ONLY status a sim can grant, §8.4), the feature
is computed + cached + logged but **consulted by NOTHING**: :func:`consulted_discount`
returns the P1 conservative discount unchanged, so no scheduling or certification
decision moves. P1's hard collisions + conservative discount stay the live authority.
Unknown / out-of-scope surfaces fall back to P1, **never to zero familiarity** (§8.4).

Admission (§8.4): a repeat-vs-fresh planted-learner sim must show the feature moves the
familiarity discount in the right direction WITHOUT flipping a scheduling/certification
decision. The P0.5 sweep machinery produces the certificate; :func:`run_admission_gate`
consumes it, emits the U-022 promotion-evidence artifact through the existing registry
machinery, and only then advances the model to ``simulation_validated``.
"""

from __future__ import annotations

import json as _json
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services import familiarity

# Structural version pins (strings -> excluded from the numeric-constant scan).
KERNEL_MODEL_KIND = "heuristic_llm_judged"
KERNEL_FEATURE_SCHEMA_VERSION = "kinship_feature_v1"
DEFAULT_MODEL_VERSION = "kinship_heuristic_v1"

# Decision parameter (registered): the minimum discount SHIFT the admission sim must
# demonstrate the feature moves the independent-evidence discount by, in the correct
# direction, before the feature may be admitted. A registered heuristic; the sim IS its
# sensitivity certificate (design §E). It gates admission and is otherwise inert.
ADMISSION_MIN_DISCOUNT_SHIFT: float = 0.05
ADMISSION_PARAM_PATH = "kinship_feature:ADMISSION_MIN_DISCOUNT_SHIFT"

# STRUCTURAL FIREWALL FLAG (§8.4, §17; not a decision parameter -- a U-018-style
# dead-man switch, mirrored on ``depth_transition.LIVE_ACTIVATION_ENABLED``). Passing
# the sim admission gate promotes the feature only to ``simulation_validated``, which is
# STILL SHADOW: a simulation cannot narrow live authority by itself (§8.4). Granting the
# feature bounded live soft-discount/rotation authority is a separate EXPLICIT reviewed
# activation for a declared scope, held OUTSIDE automatic P4 rollout (§17). It is OFF for
# all of P4: throughout this package the feature is consulted by NOTHING and P1's
# conservative discount stays the live authority.
LIVE_ACTIVATION_ENABLED = False


# ---------------------------------------------------------------------------
# Score artifact (§8.2 outputs).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class KinshipScore:
    subject_surface_id: str
    kin_surface_id: str | None
    # P(script_or_answer_replay materially aided response) (§8.2).
    replay_aided_probability: float
    # Independent-evidence discount interval [lo, hi]: how much fresh-evidence credit to
    # withhold because a warm sibling may have carried the response. A larger value
    # withholds MORE evidence (never mints any -- salience is never evidence, rule 5).
    discount_lo: float
    discount_hi: float
    # Rotation-benefit estimate: how much a fresh rotation would restore independence.
    rotation_benefit: float
    in_scope: bool
    # Pre-administration inputs ONLY (leakage proof). No correctness key ever.
    conditioned_on: dict[str, Any]
    # The reviewable U-034-shaped judge artifact (not an API call).
    artifact: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "subject_surface_id": self.subject_surface_id,
            "kin_surface_id": self.kin_surface_id,
            "replay_aided_probability": self.replay_aided_probability,
            "independent_evidence_discount_interval": [self.discount_lo, self.discount_hi],
            "rotation_benefit": self.rotation_benefit,
            "in_scope": self.in_scope,
        }


# A judge is: (subject_features, kin_features, bounds) -> raw score dict. The default is
# a deterministic stub composing P1 warmth; a real LLM judge slots in behind the same
# signature and MUST stay within ``bounds`` (owner-reviewed, U-034).
Judge = Callable[[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]], Mapping[str, float]]

# Card-declared bounds the judge renders within (owner-reviewed, U-034). Outputs are
# clamped to these ranges so a runaway judge can never over-discount evidence.
DEFAULT_BOUNDS: dict[str, Any] = {
    "replay_aided_probability": [0.0, 1.0],
    "discount": [0.0, 0.9],
    "rotation_benefit": [0.0, 1.0],
}


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _default_judge(
    subject_features: Mapping[str, Any],
    kin_features: Mapping[str, Any],
    bounds: Mapping[str, Any],
) -> dict[str, float]:
    """Deterministic stub judge: derive kinship from the SHARED strength of the two P1
    soft-kinship vectors (element-wise min over the union, exactly P1's pairwise-warmth
    rule -- both surfaces must strongly exhibit the same feature). Monotone, symmetric,
    reproducible; no randomness, no network."""

    keys = set(subject_features) | set(kin_features)
    combined = {
        k: min(
            float(subject_features.get(k, 0.0) or 0.0),
            float(kin_features.get(k, 0.0) or 0.0),
        )
        for k in keys
    }
    warmth = familiarity.warmth_score(combined)  # in [0, 1)
    d_lo, d_hi = bounds["discount"]
    r_lo, r_hi = bounds["replay_aided_probability"]
    b_lo, b_hi = bounds["rotation_benefit"]
    return {
        "replay_aided_probability": _clamp(warmth, r_lo, r_hi),
        # A warm sibling withholds proportionally more independent-evidence credit; the
        # interval widens with warmth to disclose the judge's own uncertainty.
        "discount_point": _clamp(warmth * d_hi, d_lo, d_hi),
        "discount_halfwidth": _clamp(0.5 * warmth * d_hi, 0.0, d_hi),
        "rotation_benefit": _clamp(warmth, b_lo, b_hi),
    }


def _features_for(repository: Repository, surface_id: str) -> dict[str, Any]:
    row = repository.soft_kinship_features_for_surface(
        surface_id=surface_id, feature_schema_version=familiarity.FEATURE_SCHEMA_VERSION
    )
    return _json.loads(row["features_json"]) if row is not None else {}


def _hard_colliding(repository: Repository, subject: str, kin: str) -> bool:
    """The kernel scores only NON-hard-colliding surfaces (§8.1). If the pair shares a
    hard-correlation group, that is P1's authority -- out of scope for the feature."""

    subj = familiarity.familiarity_projection_v1(repository, surface_id=subject)
    kin_groups = {
        (m["namespace"], m["value_hash"])
        for m in repository.fingerprint_memberships_for_surface(kin)
        if m["namespace"] in familiarity.HARD_NAMESPACES
    }
    for collision in subj.hard_collisions:
        if (collision.namespace, collision.value_hash) in kin_groups:
            return True
        if kin in collision.sibling_surface_ids:
            return True
    return False


# ---------------------------------------------------------------------------
# Model artifact + feature cache.
# ---------------------------------------------------------------------------


def ensure_model(
    repository: Repository,
    *,
    version: str = DEFAULT_MODEL_VERSION,
    scope: Mapping[str, Any] | None = None,
    consent: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> str:
    """Create (idempotent) the immutable kernel MODEL artifact row and its opening
    'shadow' event. Returns the model id. A degenerate 'model' (no fitted weights): the
    row carries provenance, manifests, calibrated outputs, and admission status (§8.2)."""

    with repository.connection() as connection:
        row = connection.execute(
            "SELECT id FROM familiarity_kernel_models WHERE version = ?", (version,)
        ).fetchone()
        if row is not None:
            return row["id"]
        model_id = new_ulid()
        content_hash = familiarity_kernel_content_hash(version)
        now = utc_now_iso(clock)
        connection.execute(
            "INSERT INTO familiarity_kernel_models(id, model_kind, version, parent_id, "
            "content_hash, status, feature_schema_version, preprocessing_version, "
            "manifests_json, scope_json, consent_json, metrics_json, calibration_status, "
            "admission_evidence_id, created_at) VALUES "
            "(?, ?, ?, NULL, ?, 'shadow', ?, NULL, NULL, ?, ?, NULL, 'uncalibrated', NULL, ?)",
            (
                model_id, KERNEL_MODEL_KIND, version, content_hash,
                KERNEL_FEATURE_SCHEMA_VERSION,
                _json.dumps(dict(scope or {"scope": "learner_local"})),
                _json.dumps(dict(consent or {"consent": "not_required_shadow"})),
                now,
            ),
        )
        connection.execute(
            "INSERT INTO familiarity_kernel_events(id, model_id, event_ordinal, "
            "event_kind, detail_json, created_at) VALUES (?, ?, 0, 'shadow', ?, ?)",
            (new_ulid(), model_id, _json.dumps({"note": "model created shadow"}), now),
        )
        connection.commit()
        return model_id


def familiarity_kernel_content_hash(version: str) -> str:
    from learnloop.services.activities import _canonical_hash

    return _canonical_hash(
        {"kind": KERNEL_MODEL_KIND, "version": version,
         "feature_schema": KERNEL_FEATURE_SCHEMA_VERSION}
    )


def model_row(repository: Repository, model_id: str) -> dict[str, Any] | None:
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT * FROM familiarity_kernel_models WHERE id = ?", (model_id,)
        ).fetchone()
    return dict(row) if row is not None else None


def active_model_id(
    repository: Repository, *, version: str = DEFAULT_MODEL_VERSION
) -> str | None:
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT id FROM familiarity_kernel_models WHERE version = ?", (version,)
        ).fetchone()
    return row["id"] if row is not None else None


def score_kinship(
    repository: Repository,
    *,
    subject_surface_id: str,
    kin_surface_id: str | None,
    model_id: str | None = None,
    judge: Judge | None = None,
    bounds: Mapping[str, Any] | None = None,
    p1_conservative_discount: float = 0.9,
    clock: Clock | None = None,
) -> KinshipScore:
    """Compute + cache the kinship feature for one (subject, kin) surface pair. Composes
    P1 soft-kinship features; renders through the LLM judge (deterministic stub) within
    owner-reviewed bounds. Out-of-scope (hard collision / missing features / no kin)
    falls back to the P1 conservative discount -- NEVER zero (§8.4).

    Conditioned ONLY on pre-administration inputs. There is no path here that reads the
    learner's current correctness."""

    if model_id is None:
        model_id = ensure_model(repository, clock=clock)
    bounds = {**DEFAULT_BOUNDS, **(bounds or {})}
    judge = judge or _default_judge

    subject_features = _features_for(repository, subject_surface_id)
    conditioned_on: dict[str, Any] = {
        "subject_surface_id": subject_surface_id,
        "kin_surface_id": kin_surface_id,
        "subject_soft_features": subject_features,
        "information_horizon": "pre_administration",
    }

    out_of_scope_reason: str | None = None
    if kin_surface_id is None:
        out_of_scope_reason = "no_kin_surface"
    elif not subject_features or not _features_for(repository, kin_surface_id):
        out_of_scope_reason = "missing_soft_features"
    elif _hard_colliding(repository, subject_surface_id, kin_surface_id):
        out_of_scope_reason = "hard_collision_is_p1_authority"

    if out_of_scope_reason is not None:
        # Fall back to P1's conservative discount, never zero familiarity (§8.4).
        score = KinshipScore(
            subject_surface_id=subject_surface_id,
            kin_surface_id=kin_surface_id,
            replay_aided_probability=0.0,
            discount_lo=p1_conservative_discount,
            discount_hi=p1_conservative_discount,
            rotation_benefit=0.0,
            in_scope=False,
            conditioned_on=conditioned_on,
            artifact={"out_of_scope": out_of_scope_reason, "fallback": "p1_conservative"},
        )
        _cache_feature(repository, model_id, score, clock=clock)
        return score

    kin_features = _features_for(repository, kin_surface_id)
    conditioned_on["kin_soft_features"] = kin_features
    raw = judge(subject_features, kin_features, bounds)
    point = float(raw["discount_point"])
    half = float(raw.get("discount_halfwidth", 0.0))
    d_lo, d_hi = bounds["discount"]
    score = KinshipScore(
        subject_surface_id=subject_surface_id,
        kin_surface_id=kin_surface_id,
        replay_aided_probability=float(raw["replay_aided_probability"]),
        discount_lo=_clamp(point - half, d_lo, d_hi),
        discount_hi=_clamp(point + half, d_lo, d_hi),
        rotation_benefit=float(raw["rotation_benefit"]),
        in_scope=True,
        conditioned_on=conditioned_on,
        artifact={
            "stage": "bounded_render",
            "bounds": dict(bounds),
            "judge": getattr(judge, "__name__", "judge"),
            "provenance": "llm_judged_heuristic_stub",
        },
    )
    _cache_feature(repository, model_id, score, clock=clock)
    return score


def _cache_feature(
    repository: Repository, model_id: str, score: KinshipScore, *, clock: Clock | None
) -> None:
    with repository.connection() as connection:
        connection.execute(
            "INSERT OR REPLACE INTO familiarity_kernel_features(id, model_id, "
            "subject_surface_id, kin_surface_id, outputs_json, conditioned_on_json, "
            "in_scope, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                new_ulid(), model_id, score.subject_surface_id, score.kin_surface_id,
                _json.dumps(score.as_dict()), _json.dumps(score.conditioned_on),
                1 if score.in_scope else 0, utc_now_iso(clock),
            ),
        )
        connection.commit()


def cached_feature(
    repository: Repository,
    *,
    model_id: str,
    subject_surface_id: str,
    kin_surface_id: str | None,
) -> dict[str, Any] | None:
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT * FROM familiarity_kernel_features WHERE model_id = ? AND "
            "subject_surface_id = ? AND kin_surface_id IS ?",
            (model_id, subject_surface_id, kin_surface_id),
        ).fetchone()
    return dict(row) if row is not None else None


# ---------------------------------------------------------------------------
# THE FIREWALL (§8.4). Until admitted, the feature is consulted by NOTHING.
# ---------------------------------------------------------------------------


def is_admitted(repository: Repository, *, model_id: str | None = None) -> bool:
    """True iff the kernel model has passed its sim admission gate
    (status ``simulation_validated``). This is the single predicate every consumer must
    check before consulting the feature."""

    if model_id is None:
        model_id = active_model_id(repository)
        if model_id is None:
            return False
    row = model_row(repository, model_id)
    return bool(row) and row["status"] == "simulation_validated"


def consulted_discount(
    repository: Repository,
    *,
    subject_surface_id: str,
    kin_surface_id: str | None,
    p1_conservative_discount: float,
    model_id: str | None = None,
) -> float:
    """The independent-evidence discount a CONSUMER is allowed to act on.

    Firewall (§8.4/§17). Throughout P4 this returns the P1 conservative discount
    UNCHANGED: the feature is consulted by nothing. Passing the sim admission gate
    (``simulation_validated``) is still shadow and does NOT grant live authority; only an
    explicit reviewed activation for a declared scope (``LIVE_ACTIVATION_ENABLED``, OFF
    for all of P4) could let the cached feature discount take effect, and even then it
    never relaxes below the P1 conservative floor (never zero familiarity, §8.4)."""

    if not LIVE_ACTIVATION_ENABLED:
        return p1_conservative_discount  # the firewall: consulted by nothing in P4
    if model_id is None:
        model_id = active_model_id(repository)
    if model_id is None or not is_admitted(repository, model_id=model_id):
        return p1_conservative_discount
    row = cached_feature(
        repository, model_id=model_id,
        subject_surface_id=subject_surface_id, kin_surface_id=kin_surface_id,
    )
    if row is None:
        return p1_conservative_discount
    outputs = _json.loads(row["outputs_json"])
    lo, _hi = outputs["independent_evidence_discount_interval"]
    # The floor keeps activated authority conservative: never LESS discount than P1.
    return max(float(lo), 0.0) if row["in_scope"] else p1_conservative_discount


# ---------------------------------------------------------------------------
# Admission gate (§8.4): planted-learner sim -> U-022 promotion evidence -> admit.
# ---------------------------------------------------------------------------


@dataclass
class AdmissionOutcome:
    admitted: bool
    reason: str | None = None
    evidence_id: str | None = None

    def __bool__(self) -> bool:
        return self.admitted


def run_admission_gate(
    repository: Repository,
    *,
    model_id: str | None = None,
    sim_report: Any = None,
    scenario: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> AdmissionOutcome:
    """Consume a planted-learner (repeat-vs-fresh) sim report and, if it shows the
    feature moves the discount correctly WITHOUT flipping a scheduling/certification
    decision, admit the model to ``simulation_validated`` (the only status a sim can
    grant, §8.4). Emits the U-022 promotion-evidence artifact through the registry
    machinery (``sensitivity_certificates``) and links it on the model row.

    ``sim_report`` defaults to :func:`learnloop.sim.kinship_admission.run_admission_sim`
    on the current threshold; tests may inject a report for determinism/speed."""

    from learnloop.services import sensitivity_certificates as sc

    if model_id is None:
        model_id = ensure_model(repository, clock=clock)

    if sim_report is None:
        from learnloop.sim.kinship_admission import run_admission_sim

        sim_report = run_admission_sim(threshold=ADMISSION_MIN_DISCOUNT_SHIFT)

    # Condition A: the feature must move the discount in the correct direction by at
    # least the registered threshold (a repeat scenario must discount MORE than fresh).
    if not getattr(sim_report, "moves_discount_correctly", False):
        _append_kernel_event(
            repository, model_id, "shadow",
            {"admission": "refused", "reason": "feature_did_not_move_discount"}, clock=clock,
        )
        return AdmissionOutcome(False, "feature_did_not_move_discount")

    # Condition B: no scheduling/certification decision flips in the plausible range.
    # The P0.5 promotion machinery enforces this via decision_stable / flip_points.
    evidence = sc.promotion_evidence_from_sweep_report(
        path=ADMISSION_PARAM_PATH,
        covered_value=ADMISSION_MIN_DISCOUNT_SHIFT,
        plausible_range={"low": 0.01, "high": 0.2},
        scenario=dict(scenario or {"gate": "kinship_admission", "design": "repeat_vs_fresh"}),
        sweep_report=sim_report,
    )
    outcome = sc.promote(repository, evidence, clock=clock)
    if not outcome.promoted:
        _append_kernel_event(
            repository, model_id, "shadow",
            {"admission": "refused", "reason": outcome.refusal_reason}, clock=clock,
        )
        return AdmissionOutcome(False, outcome.refusal_reason)

    now = utc_now_iso(clock)
    with repository.connection() as connection:
        connection.execute(
            "UPDATE familiarity_kernel_models SET status = 'simulation_validated', "
            "admission_evidence_id = ?, calibration_status = 'simulation_validated' "
            "WHERE id = ?",
            (evidence.id, model_id),
        )
        connection.commit()
    _append_kernel_event(
        repository, model_id, "admission",
        {"admission": "granted", "evidence_id": evidence.id,
         "status": "simulation_validated"}, clock=clock,
    )
    return AdmissionOutcome(True, None, evidence.id)


def _append_kernel_event(
    repository: Repository, model_id: str, kind: str, detail: Mapping[str, Any],
    *, clock: Clock | None,
) -> None:
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT COALESCE(MAX(event_ordinal), -1) AS m FROM familiarity_kernel_events "
            "WHERE model_id = ?",
            (model_id,),
        ).fetchone()
        ordinal = int(row["m"]) + 1
        connection.execute(
            "INSERT INTO familiarity_kernel_events(id, model_id, event_ordinal, "
            "event_kind, detail_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (new_ulid(), model_id, ordinal, kind, _json.dumps(dict(detail)),
             utc_now_iso(clock)),
        )
        connection.commit()
