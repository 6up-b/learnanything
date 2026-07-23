"""Grader identity + calibration model layer (spec_p0_measurement_correctness §3.2).

Immutable, versioned, asymmetric Dirichlet channel models over the JOINT emission
``E = (G, confidence_bucket)``. Marginalizing confidence yields the reported class
confusion ``P(G | Z)``. Resolution partially pools the most specific available
scope toward the fixed parent order ``global -> grader_identity -> outcome_schema
-> domain -> length_bucket``; a missing child inherits the parent posterior (the
Dirichlet alpha rows), never a point estimate. If no scoped model exists at all a
wide global heuristic prior is returned with a recorded fallback reason -- never a
crash, never the old 0.90 point channel (§4.1).

The heuristic priors seed from the existing symmetric 0.90/0.80 reliability means
(``probe_families.GRADER_CHANNEL_RELIABILITY``) with a DELIBERATELY LOW Dirichlet
concentration so their intervals are deliberately wide (§3.2, §5). Model rows never
mutate; activation/retirement/quarantine are measurement_events.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services.activities import _canonical_hash, _json
from learnloop.services.outcome_schemas import (
    BUILTIN_SCHEMAS,
    ensure_builtin_schemas,
)
from learnloop.services.probe_families import GRADER_CHANNEL_RELIABILITY

# The Dirichlet concentration for heuristic priors (§3.2/§5): deliberately LOW so
# intervals are deliberately WIDE. Must pass the planted-misgrade sensitivity suite
# before a model can be promoted to simulation_validated.
PRIOR_CONCENTRATION = 2.0  # decision parameter: heuristic

# Authored split of a class's confusion mass across the confidence-bucket columns
# of the joint emission (§3.2/§5). Because this split is identical across true
# classes, it cancels in the heuristic-seed posterior -- so the raw confidence
# bucket does not shift the seed interpretation, matching the current channel that
# ignores grader_confidence entirely. A CALIBRATED model may break this symmetry.
CONFIDENCE_MASS_SPLIT: dict[str, float] = {  # decision parameter: heuristic
    "unknown": 0.05,
    "low": 0.15,
    "medium": 0.40,
    "high": 0.40,
}
CONFIDENCE_BUCKETS = ("unknown", "low", "medium", "high")

# Deterministic robustness ensemble (§4.2). Registered heuristic decision
# parameters; the planted-learner suite is the mechanism gate for promotion.
ENSEMBLE_DRAWS = 128  # decision parameter: heuristic
ROBUST_QUANTILE = 0.10  # decision parameter: heuristic

# Grader-identity tuple version pins used by the heuristic seeds + dual-write.
GRADING_PROMPT_VERSION = "grading_prompt_v1"
GRADER_OUTPUT_SCHEMA_VERSION = "grading_proposal_v1"

CALIBRATION_ALGORITHM_VERSION = "grader_calibration_v1"

# The two legacy policies -> a nominal reliability + provider identity used only to
# seed heuristic grader-identity priors (§5). Symmetry preserved so the mean still
# describes the char-test channel, while the machinery can now represent asymmetry.
_HEURISTIC_POLICY_PROVIDERS = {
    "diagnostic_microprobe_v1": ("ai", "diagnostic_microprobe_v1"),
    "diagnostic_longform_v1": ("ai", "diagnostic_longform_v1"),
}


def grader_identity_hash(
    *,
    provider: str | None,
    model_revision: str | None,
    prompt_version: str | None,
    output_schema_version: str | None,
) -> str | None:
    """32-char canonical hash of the grader identity tuple (§3.2). None when the
    provider is absent (i.e. the global scope has no identity)."""

    if provider is None:
        return None
    return _canonical_hash(
        {
            "provider": provider,
            "model_revision": model_revision,
            "prompt_version": prompt_version,
            "output_schema_version": output_schema_version,
        }
    )


# ---------------------------------------------------------------------------
# Heuristic alpha construction (§5)
# ---------------------------------------------------------------------------

def symmetric_mean_confusion(
    true_classes: Sequence[str], observed_classes: Sequence[str], reliability: float
) -> dict[str, dict[str, float]]:
    """Diagonal ``reliability``, off-diagonal ``(1-r)/(n-1)`` -- exactly the
    ``probe_families.grader_channel_matrix`` mean the Dirichlet centers on."""

    r = min(max(reliability, 0.0), 1.0)
    n = len(observed_classes)
    spread = (1.0 - r) / (n - 1) if n > 1 else 0.0
    return {
        z: {g: (r if g == z else spread) for g in observed_classes}
        for z in true_classes
    }


def heuristic_alphas(
    *,
    true_classes: Sequence[str],
    observed_classes: Sequence[str],
    reliability: float,
    concentration: float = PRIOR_CONCENTRATION,
) -> dict[str, dict[str, float]]:
    """Spread the symmetric mean over the joint ``(G, conf_bucket)`` cells with a
    low concentration (wide intervals). ``alpha = concentration * mean_joint``."""

    mean = symmetric_mean_confusion(true_classes, observed_classes, reliability)
    alphas: dict[str, dict[str, float]] = {}
    for z in true_classes:
        row: dict[str, float] = {}
        for g in observed_classes:
            for bucket in CONFIDENCE_BUCKETS:
                row[f"{g}|{bucket}"] = concentration * mean[z][g] * CONFIDENCE_MASS_SPLIT[bucket]
        alphas[z] = row
    return alphas


def _model_content_hash(*, identity: Mapping[str, Any], scope: Mapping[str, Any],
                        alphas: Mapping[str, Mapping[str, float]], status: str) -> str:
    return _canonical_hash(
        {
            "identity": {k: identity.get(k) for k in sorted(identity)},
            "scope": {k: scope.get(k) for k in sorted(scope)},
            "alphas": {
                z: {e: alphas[z][e] for e in sorted(alphas[z])} for z in sorted(alphas)
            },
            "status": status,
        }
    )


def seed_heuristic_priors(
    repository: Repository, *, clock: Clock | None = None
) -> dict[str, str]:
    """Idempotently seed the heuristic global + grader-identity priors (§5).

    Content-addressed on ``content_hash``: a re-run mints nothing. Seeds one
    ``global`` prior per response outcome schema, plus ``grader_identity`` priors
    for the two known policies. Returns a map of a stable key -> model id.
    """

    ensure_builtin_schemas(repository, clock=clock)
    seeded: dict[str, str] = {}

    response_schemas = [s for s in BUILTIN_SCHEMAS if s.kind == "response"]
    # Global schema prior: the per-policy channel means, floored by the fitted
    # grader-channel prior knob (P4). The old bare 0.80 longform default implied
    # the grader mislabels 1 in 5 responses on the coarse 3-class schema — very
    # pessimistic, and permanent while nothing feeds calibration counts.
    from learnloop.services.fitted_params import resolve_grader_channel_prior

    reliability_floor = resolve_grader_channel_prior(repository).reliability_floor
    global_reliability = max(
        GRADER_CHANNEL_RELIABILITY["diagnostic_longform_v1"], reliability_floor
    )

    for schema in response_schemas:
        version_row = repository.fetch_outcome_schema_version(slug=schema.slug)
        if version_row is None:  # pragma: no cover - just seeded
            continue
        schema_id = version_row["schema_id"]
        schema_version = int(version_row["version"])
        alphas = heuristic_alphas(
            true_classes=schema.true_classes,
            observed_classes=schema.observed_classes,
            reliability=global_reliability,
        )
        identity = {
            "grader_provider": None,
            "grader_model_revision": None,
            "grading_prompt_version": None,
            "grader_output_schema_version": None,
            "grader_identity_hash": None,
        }
        scope = {
            "scope_level": "global",
            "outcome_schema_id": schema_id,
            "outcome_schema_version": schema_version,
            "domain": None,
            "length_bucket": None,
        }
        content_hash = _model_content_hash(
            identity=identity, scope=scope, alphas=alphas, status="heuristic"
        )
        existing = repository.find_calibration_model_by_hash(content_hash)
        if existing is not None:
            seeded[f"global::{schema.slug}"] = existing["id"]
            continue
        model_id = repository.insert_calibration_model(
            model={
                **identity,
                **scope,
                "semver": "0.1.0",
                "parent_model_id": None,
                "content_hash": content_hash,
                "backoff_chain_json": _json([]),
                "status": "heuristic",
                "count_heuristic_prior": int(PRIOR_CONCENTRATION),
                "prior_concentration": PRIOR_CONCENTRATION,
                "provenance_json": _json(
                    {
                        "source": "GRADER_CHANNEL_RELIABILITY",
                        "reliability": global_reliability,
                        "policy": "diagnostic_longform_v1",
                        "scope": "global",
                    }
                ),
            },
            alphas=alphas,
            clock=clock,
        )
        seeded[f"global::{schema.slug}"] = model_id

        # Grader-identity priors for the two known policies (mapped onto this
        # response schema), pooling toward the global prior.
        for policy, policy_reliability in GRADER_CHANNEL_RELIABILITY.items():
            reliability = max(policy_reliability, reliability_floor)
            provider, revision = _HEURISTIC_POLICY_PROVIDERS[policy]
            gih = grader_identity_hash(
                provider=provider,
                model_revision=revision,
                prompt_version=GRADING_PROMPT_VERSION,
                output_schema_version=GRADER_OUTPUT_SCHEMA_VERSION,
            )
            gi_alphas = heuristic_alphas(
                true_classes=schema.true_classes,
                observed_classes=schema.observed_classes,
                reliability=reliability,
            )
            gi_identity = {
                "grader_provider": provider,
                "grader_model_revision": revision,
                "grading_prompt_version": GRADING_PROMPT_VERSION,
                "grader_output_schema_version": GRADER_OUTPUT_SCHEMA_VERSION,
                "grader_identity_hash": gih,
            }
            gi_scope = {
                "scope_level": "grader_identity",
                "outcome_schema_id": schema_id,
                "outcome_schema_version": schema_version,
                "domain": None,
                "length_bucket": None,
            }
            gi_hash = _model_content_hash(
                identity=gi_identity, scope=gi_scope, alphas=gi_alphas, status="heuristic"
            )
            if repository.find_calibration_model_by_hash(gi_hash) is not None:
                continue
            gi_model_id = repository.insert_calibration_model(
                model={
                    **gi_identity,
                    **gi_scope,
                    "semver": "0.1.0",
                    "parent_model_id": model_id,
                    "content_hash": gi_hash,
                    "backoff_chain_json": _json([model_id]),
                    "status": "heuristic",
                    "count_heuristic_prior": int(PRIOR_CONCENTRATION),
                    "prior_concentration": PRIOR_CONCENTRATION,
                    "provenance_json": _json(
                        {
                            "source": "GRADER_CHANNEL_RELIABILITY",
                            "reliability": reliability,
                            "policy": policy,
                            "scope": "grader_identity",
                        }
                    ),
                },
                alphas=gi_alphas,
                clock=clock,
            )
            seeded[f"identity::{policy}::{schema.slug}"] = gi_model_id
    return seeded


def import_calibration_bundle(
    repository: Repository,
    bundle: Mapping[str, Any],
    *,
    clock: Clock | None = None,
) -> list[str]:
    """Import a shipped grader-calibration bundle (warm priors, §grader cold start).

    Grader reliability is a property of provider + model revision + prompt +
    schema — not of the vault — so a new vault should not relearn it from a
    concentration-2 heuristic prior. A bundle carries pre-fitted Dirichlet
    alphas per grader identity/scope with their evidence manifest; models
    import as ``simulation_validated`` (never ``live_calibrated`` — that
    promotion still requires this vault's adjudicated anchors). Idempotent via
    the same content-hash used by the heuristic seeds.
    """

    imported: list[str] = []
    for entry in bundle.get("models", []):
        schema_slug = str(entry.get("outcome_schema_slug") or "")
        version_row = repository.fetch_outcome_schema_version(slug=schema_slug)
        if version_row is None:
            raise ValueError(f"bundle references unknown outcome schema {schema_slug!r}")
        alphas = {str(k): dict(v) for k, v in (entry.get("alphas") or {}).items()}
        if not alphas:
            raise ValueError("bundle model entry has no alphas")
        identity = {
            "grader_provider": entry.get("grader_provider"),
            "grader_model_revision": entry.get("grader_model_revision"),
            "grading_prompt_version": entry.get("grading_prompt_version") or GRADING_PROMPT_VERSION,
            "grader_output_schema_version": (
                entry.get("grader_output_schema_version") or GRADER_OUTPUT_SCHEMA_VERSION
            ),
        }
        identity["grader_identity_hash"] = grader_identity_hash(
            provider=identity["grader_provider"],
            model_revision=identity["grader_model_revision"],
            prompt_version=identity["grading_prompt_version"],
            output_schema_version=identity["grader_output_schema_version"],
        )
        scope = {
            "scope_level": str(entry.get("scope_level") or "grader_identity"),
            "outcome_schema_id": version_row["schema_id"],
            "outcome_schema_version": int(version_row["version"]),
            "domain": entry.get("domain"),
            "length_bucket": entry.get("length_bucket"),
        }
        status = "simulation_validated"
        content_hash = _model_content_hash(
            identity=identity, scope=scope, alphas=alphas, status=status
        )
        if repository.find_calibration_model_by_hash(content_hash) is not None:
            continue
        model_id = repository.insert_calibration_model(
            model={
                **identity,
                **scope,
                "semver": str(entry.get("semver") or "0.1.0"),
                "parent_model_id": None,
                "content_hash": content_hash,
                "backoff_chain_json": _json([]),
                "status": status,
                "count_heuristic_prior": 0,
                "prior_concentration": float(entry.get("prior_concentration") or 0.0),
                "provenance_json": _json(
                    {
                        "source": "calibration_bundle",
                        "bundle_name": bundle.get("name"),
                        "bundle_version": bundle.get("version"),
                        "evidence_manifest": entry.get("evidence_manifest") or {},
                    }
                ),
            },
            alphas=alphas,
            clock=clock,
        )
        imported.append(model_id)
    return imported


# ---------------------------------------------------------------------------
# Resolution (§3.2, §4.1 step 5)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ResolvedModel:
    model_id: str
    model_hash: str
    joint_alpha: dict[str, dict[str, float]]  # {Z: {emission: alpha}}
    true_classes: tuple[str, ...]
    observed_classes: tuple[str, ...]
    contributing_model_ids: list[str]
    parent_contribution_share: float
    fallback_reason: str | None = None
    status: str = "heuristic"

    def emission_likelihoods(self, true_class: str) -> dict[str, float]:
        row = self.joint_alpha[true_class]
        total = sum(row.values()) or 1.0
        return {e: v / total for e, v in row.items()}

    def marginal_confusion(self) -> dict[str, dict[str, float]]:
        """P(G | Z): marginalize the joint emission over confidence buckets."""

        result: dict[str, dict[str, float]] = {}
        for z, row in self.joint_alpha.items():
            total = sum(row.values()) or 1.0
            marg: dict[str, float] = {}
            for emission, alpha in row.items():
                g = emission.split("|", 1)[0]
                marg[g] = marg.get(g, 0.0) + alpha / total
            result[z] = marg
        return result


def _sum_alphas(rows: Sequence[Mapping[str, Mapping[str, float]]]) -> dict[str, dict[str, float]]:
    combined: dict[str, dict[str, float]] = {}
    for alphas in rows:
        for z, row in alphas.items():
            dest = combined.setdefault(z, {})
            for emission, value in row.items():
                dest[emission] = dest.get(emission, 0.0) + float(value)
    return combined


def resolve_calibration_model(
    repository: Repository,
    *,
    grader_identity_hash: str | None,
    outcome_schema_id: str,
    outcome_schema_version: int,
    domain: str | None = None,
    length_bucket: str | None = None,
    clock: Clock | None = None,
) -> ResolvedModel:
    """Resolve the partial-pooling mixture for a context (§3.2). Walks the fixed
    parent order and sums the present descendants' alphas onto the global prior."""

    # The global schema prior is the mandatory root. Seeding is content-addressed
    # and idempotent, so run it unconditionally: a retuned fitted channel knob
    # (P4) mints a NEW prior row that latest-wins resolution below picks up even
    # in vaults that were seeded under the old constants.
    seed_heuristic_priors(repository, clock=clock)
    globals_ = repository.find_calibration_models(
        scope_level="global",
        outcome_schema_id=outcome_schema_id,
        outcome_schema_version=outcome_schema_version,
    )

    if not globals_:
        # No scoped model at all -- synthesize a wide uniform heuristic prior and
        # record the fallback (§4.1). Never crash, never restore the point channel.
        return _uniform_fallback(repository, outcome_schema_id, outcome_schema_version)

    # Latest seeded global wins (rows are ordered created_at ASC): a retuned
    # heuristic prior re-seeds a NEW content-addressed row, and picking the
    # oldest would silently pin existing vaults to the superseded prior forever.
    # Matches the descendants' ``matches[-1]`` convention below. Pinned
    # interpretations are untouched — they persist their model hash + LCB.
    global_model = globals_[-1]
    global_alpha = repository.fetch_calibration_alphas(global_model["id"])
    contributing: list[dict[str, Any]] = [global_model]
    alpha_stack: list[Mapping[str, Mapping[str, float]]] = [global_alpha]

    # Descendants in specificity order (child last), pooled onto the parent.
    for scope_level, filters in (
        ("grader_identity", {"grader_identity_hash": grader_identity_hash}),
        ("domain", {"grader_identity_hash": grader_identity_hash, "domain": domain}),
        ("length_bucket", {
            "grader_identity_hash": grader_identity_hash,
            "domain": domain,
            "length_bucket": length_bucket,
        }),
    ):
        if scope_level == "grader_identity" and grader_identity_hash is None:
            continue
        if scope_level == "domain" and domain is None:
            continue
        if scope_level == "length_bucket" and length_bucket is None:
            continue
        matches = repository.find_calibration_models(
            scope_level=scope_level,
            outcome_schema_id=outcome_schema_id,
            outcome_schema_version=outcome_schema_version,
            **filters,
        )
        if matches:
            model = matches[-1]
            contributing.append(model)
            alpha_stack.append(repository.fetch_calibration_alphas(model["id"]))

    combined = _sum_alphas(alpha_stack)
    parent_mass = sum(sum(r.values()) for r in global_alpha.values())
    total_mass = sum(sum(r.values()) for r in combined.values()) or 1.0
    parent_share = parent_mass / total_mass

    resolved_model = contributing[-1]
    true_classes = tuple(sorted(combined.keys()))
    observed_classes = tuple(
        sorted({e.split("|", 1)[0] for row in combined.values() for e in row})
    )
    composite_hash = _canonical_hash(
        [[m["id"], m["content_hash"]] for m in contributing]
    )
    statuses = {m["status"] for m in contributing}
    status = "live_calibrated" if statuses == {"live_calibrated"} else (
        "simulation_validated" if "live_calibrated" not in statuses
        and "simulation_validated" in statuses else "heuristic"
    )
    return ResolvedModel(
        model_id=resolved_model["id"],
        model_hash=composite_hash,
        joint_alpha=combined,
        true_classes=true_classes,
        observed_classes=observed_classes,
        contributing_model_ids=[m["id"] for m in contributing],
        parent_contribution_share=parent_share,
        fallback_reason=None,
        status=status,
    )


def _uniform_fallback(
    repository: Repository, outcome_schema_id: str, outcome_schema_version: int
) -> ResolvedModel:
    row = repository.fetch_outcome_schema_version_by_id(outcome_schema_id, outcome_schema_version)
    if row is not None:
        import json

        true_classes = tuple(json.loads(row["true_classes_json"]))
        observed_classes = tuple(json.loads(row["observed_classes_json"]))
    else:  # pragma: no cover - defensive
        true_classes = observed_classes = ("success", "partial_success", "other")
    alphas = heuristic_alphas(
        true_classes=true_classes,
        observed_classes=observed_classes,
        reliability=0.5,  # maximally-uncertain wide prior
    )
    return ResolvedModel(
        model_id="",
        model_hash=_canonical_hash({"fallback": True, "schema": outcome_schema_id}),
        joint_alpha=alphas,
        true_classes=tuple(sorted(true_classes)),
        observed_classes=tuple(sorted(observed_classes)),
        contributing_model_ids=[],
        parent_contribution_share=1.0,
        fallback_reason="no_scoped_model_global_prior",
        status="heuristic",
    )


# ---------------------------------------------------------------------------
# Interpretation math (§4.2, §4.3)
# ---------------------------------------------------------------------------

def posterior_over_true_class(
    resolved: ResolvedModel,
    *,
    observed_class: str,
    confidence_bucket: str,
    prior: Mapping[str, float] | None = None,
) -> dict[str, float]:
    """P(Z | E, context) conditioning on the observed emission E=(G, conf_bucket).

    Uses the mean generative channel P(E | Z); the raw numeric confidence is never
    multiplied -- only the bucket selects the emission column (§9.1)."""

    emission = f"{observed_class}|{confidence_bucket}"
    classes = list(resolved.true_classes)
    if prior is None:
        prior = {z: 1.0 / len(classes) for z in classes}
    unnormalized: dict[str, float] = {}
    for z in classes:
        likelihoods = resolved.emission_likelihoods(z)
        unnormalized[z] = likelihoods.get(emission, 0.0) * prior.get(z, 0.0)
    total = sum(unnormalized.values())
    if total <= 0:
        return {z: 1.0 / len(classes) for z in classes}
    return {z: v / total for z, v in unnormalized.items()}


def certainty(posterior: Mapping[str, float]) -> float:
    """1 - H(p)/log(k): 0 for uniform, 1 for a point mass (§4.3)."""

    k = len(posterior)
    if k <= 1:
        return 1.0
    entropy = 0.0
    for p in posterior.values():
        if p > 0:
            entropy -= p * math.log(p)
    return max(0.0, min(1.0, 1.0 - entropy / math.log(k)))


def _dirichlet_sample(rng: random.Random, alpha: Sequence[float]) -> list[float]:
    draws = [rng.gammavariate(max(a, 1e-9), 1.0) for a in alpha]
    total = sum(draws) or 1.0
    return [d / total for d in draws]


def credible_interval(
    resolved: ResolvedModel,
    *,
    observed_class: str,
    confidence_bucket: str,
    prior: Mapping[str, float] | None = None,
    draws: int = ENSEMBLE_DRAWS,
) -> dict[str, float]:
    """Deterministic Dirichlet ensemble interval on the leading-class posterior
    (§4.2). Seeded by the model hash + emission so replay is byte-stable. Wider
    with lower concentration -> the heuristic prior's deliberately wide interval."""

    posterior = posterior_over_true_class(
        resolved, observed_class=observed_class, confidence_bucket=confidence_bucket, prior=prior
    )
    leading = max(posterior, key=posterior.get)
    emission = f"{observed_class}|{confidence_bucket}"
    classes = list(resolved.true_classes)
    if prior is None:
        prior = {z: 1.0 / len(classes) for z in classes}
    seed = int(_canonical_hash({"h": resolved.model_hash, "e": emission})[:12], 16)
    rng = random.Random(seed)
    samples: list[float] = []
    # Emission index for each Z row.
    for _ in range(draws):
        unnormalized: dict[str, float] = {}
        for z in classes:
            row = resolved.joint_alpha[z]
            keys = sorted(row.keys())
            sampled = _dirichlet_sample(rng, [row[k] for k in keys])
            like = dict(zip(keys, sampled)).get(emission, 0.0)
            unnormalized[z] = like * prior.get(z, 0.0)
        total = sum(unnormalized.values()) or 1.0
        samples.append(unnormalized[leading] / total)
    samples.sort()
    lo = samples[max(0, int(ROBUST_QUANTILE * draws) - 1)]
    hi = samples[min(draws - 1, int((1 - ROBUST_QUANTILE) * draws))]
    return {
        "leading_class": leading,
        "point": posterior[leading],
        "low": lo,
        "high": hi,
        "width": hi - lo,
    }


# ---------------------------------------------------------------------------
# Promotion guard (§3.2, §9.1) + denominator-source rule (§4.7, §9.1)
# ---------------------------------------------------------------------------

class ModelPromotionError(ValueError):
    """A model cannot be promoted to the requested status."""


def validate_promotion(model: Mapping[str, Any], *, to_status: str) -> None:
    """Enforce §3.2 promotion rules. Exploratory-EM rows cannot promote to
    live_calibrated; live_calibrated requires an evidence manifest with adjudicated
    anchors + held-out scores. Raises :class:`ModelPromotionError` on refusal."""

    if to_status == "live_calibrated":
        manifest = model.get("evidence_manifest_json")
        if not manifest:
            raise ModelPromotionError(
                "live_calibrated requires an activated evidence manifest (§3.2)"
            )
        if int(model.get("count_adjudicated_anchor", 0) or 0) <= 0:
            raise ModelPromotionError(
                "live_calibrated requires adjudicated-anchor counts (§3.2)"
            )
        if int(model.get("count_held_out_evaluation", 0) or 0) <= 0:
            raise ModelPromotionError(
                "live_calibrated requires held-out evaluation counts (§3.2)"
            )
    elif to_status == "simulation_validated":
        # Simulation can promote only to simulation_validated (§6); it never
        # narrows authority. Exploratory-EM alone is not a mechanism check.
        planted = int(model.get("count_planted_sim", 0) or 0)
        if planted <= 0:
            raise ModelPromotionError(
                "simulation_validated requires planted_sim counts (§3.2)"
            )


# Only these provenances bear a calibration denominator (§4.7, §9.1). MNAR
# error-intake taps never change a confusion row.
DENOMINATOR_BEARING_STREAMS = frozenset({"calibration", "adjudicated_anchor"})


def denominator_counts_from_samples(
    samples: Sequence[Mapping[str, Any]]
) -> dict[str, float]:
    """IPW-reweighted denominator contribution per sample stream (§4.7). Only
    ``calibration`` and ``adjudicated_anchor`` contribute; ``error_intake``
    contributes zero -- MNAR taps never change a confusion row (§9.1)."""

    totals: dict[str, float] = {}
    for sample in samples:
        stream = sample["stream"]
        if stream not in DENOMINATOR_BEARING_STREAMS:
            continue
        if not sample.get("selected", 1):
            continue
        p = float(sample["inclusion_probability"])
        weight = 1.0 / p if p > 0 else 0.0
        totals[stream] = totals.get(stream, 0.0) + weight
    return totals
