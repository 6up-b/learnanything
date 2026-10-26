"""Pure prequential arms. No vault, repository, connection, or model clients.

The incumbent calls the existing mastery math. Its difficulty is ability-scale
``b``: the intercept in the field spec's notation is ``a*b``. All arms retain
this convention so the one-LO limit and priming agree with production.

Predictions operate on temporary augmented states: looking at a new item cannot
create a region or count evidence. Only positive-mass observations commit state.
"""

from __future__ import annotations

from dataclasses import asdict, replace
from hashlib import sha256
import json
from math import exp, isfinite, log
from typing import Callable, Iterable, Mapping

import numpy as np

from learnloop.clock import parse_utc
from learnloop.config import MasteryConfig
from learnloop.field.types import (
    ArmConstants, AttemptRow, FacetRow, ItemFeatures, ItemPrediction, LearnerPredictor,
    ObservationRow, Predictor, RegionEstimate, SignalRow,
)
from learnloop.learner.mastery import (
    MasteryObservation, initial_mastery_state, update_mastery,
)


def _probability(logit: float, clip: float = 1e-9) -> float:
    p = 1 / (1 + exp(-max(-700.0, min(700.0, logit))))
    return max(clip, min(1 - clip, p))


def _hash(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


#: Mastery keys an offline arm never reads: LP-min (a)'s claim-fixes kill switch
#: acts on live claim seeds and replay only, and these arms take their priors
#: as inputs, so it stays out of their version hashes (arms keep the hashes
#: recorded before the key existed; tests/test_eval_harness.py pins them).
_OFFLINE_INERT_MASTERY_KEYS = frozenset({"claim_fixes_enabled"})


def _mastery_hash_view(config: MasteryConfig) -> dict:
    """The mastery config as an offline arm's version hash reads it."""

    return {k: v for k, v in config.model_dump(mode="json").items() if k not in _OFFLINE_INERT_MASTERY_KEYS}


def _order(row: ObservationRow) -> tuple[str, str, str]:
    return (row.observed_at, getattr(row, "attempt_id", None) or "",
            row.signal_id if isinstance(row, SignalRow) else getattr(row, "facet_id", ""))


def _eligible(row: ObservationRow, mass: float | None = None) -> bool:
    mass = row.effective_mass if mass is None else mass
    return (
        isfinite(mass) and mass > 0
        and row.outcome is not None and isfinite(row.outcome)
        and getattr(row, "revision_status", "exact") != "excluded"
    )


class LoGeneral:
    """Small joint float64 probability-space EKF, with opt-in coarse factors."""

    granularity = "attempt"
    calibrated_uncertainty = True

    def __init__(
        self, *, name: str = "lo_general", extensions: Iterable[str] = (),
        constants: ArmConstants | None = None, config: MasteryConfig | None = None,
        items: Iterable[ItemFeatures] = (),
        general_means: Mapping[str, float] | None = None,
        lo_priors: Mapping[str, tuple[float, float]] | None = None,
    ) -> None:
        self.name = name
        self.extensions = frozenset(extensions)
        self.constants = constants or ArmConstants()
        self.config = config.model_copy(deep=True) if config is not None else MasteryConfig()
        self.items = {item.item_id: item for item in items}
        self.general_means = dict(general_means or {})
        self.lo_priors = dict(lo_priors or {})
        self.version_hash = _hash({
            "implementation": "field-ekf-v2-hint-mass-practice-gain",
            "name": name, "extensions": sorted(self.extensions),
            "constants": asdict(self.constants), "mastery": _mastery_hash_view(self.config),
            "general_means": self.general_means, "lo_priors": self.lo_priors,
        })
        self._reset()

    def _reset(self) -> None:
        self.keys: list[str] = []
        self.mean = np.zeros(0, dtype=np.float64)
        self.covariance = np.zeros((0, 0), dtype=np.float64)
        self._anchors: dict[str, str] = {}
        self._direct: set[str] = set()
        self._regions: dict[str, tuple[tuple[str, float], ...]] = {}
        self._prior_variances: dict[str, float] = {}
        self._signal_mass: dict[tuple[str, str, str], float] = {}
        self._known_items = dict(self.items)

    def _components(self, f: ItemFeatures) -> list[tuple[str, float, float]]:
        c = self.constants
        components = [
            (f"general:{f.subject_id}", self.general_means.get(f.subject_id, 0.0), c.general_variance),
            (f"lo:{f.lo_id}", 0.0, c.lo_variance),
        ]
        if "capability" in self.extensions and f.capability:
            components.append((f"capability:{f.subject_id}:{f.capability}", 0.0, c.offset_variance))
        if "transfer" in self.extensions and f.variant_relation not in (None, "same_target"):
            means = {"isomorph": 0.0, "near": -0.25, "far": -0.5}
            if f.variant_relation not in means:
                raise ValueError(f"unknown variant_relation: {f.variant_relation}")
            components.append((f"relation:{f.subject_id}:{f.variant_relation}",
                               means[f.variant_relation], c.offset_variance))
        if "family" in self.extensions and f.family_id:
            # idea_hier: an independent N(0, sigma_F^2) prior effect per PF-a
            # family. Posterior covariances with the LO and subject are kept.
            components.append((f"family:{f.family_id}", 0.0, c.family_variance))
        return components

    def _view(self, features: Iterable[ItemFeatures]):
        keys = list(self.keys)
        mean = self.mean.copy()
        covariance = self.covariance.copy()
        for f in features:
            for key, mu, variance in self._components(f):
                if key not in keys:
                    keys.append(key)
                    mean = np.append(mean, np.float64(mu))
                    covariance = np.pad(covariance, ((0, 1), (0, 1)))
                    covariance[-1, -1] = variance
        return keys, mean, covariance

    def _loadings(self, f: ItemFeatures, keys: list[str]) -> np.ndarray:
        result = np.zeros(len(keys), dtype=np.float64)
        for key, _, _ in self._components(f):
            result[keys.index(key)] = 1.0
        return result

    def _drift(self, f: ItemFeatures, keys: list[str], covariance: np.ndarray) -> np.ndarray:
        result = covariance.copy()
        for key, _, prior_variance in self._components(f):
            if prior_variance == 0:
                continue
            anchor = parse_utc(self._anchors.get(key))
            now = parse_utc(f.observed_at)
            if anchor is not None and now is not None:
                days = max(0.0, (now - anchor).total_seconds() / 86400)
                i = keys.index(key)
                # Only add variance. Shared general drift and local drift sum
                # to the incumbent rate in the base arm.
                fraction = (prior_variance / (self.constants.general_variance + self.constants.lo_variance)
                            if key.startswith(("general:", "lo:")) else 1.0)
                increment = self.config.sigma2_drift * days * fraction
                result[i, i] += max(0.0, min(increment, self.config.p_max * fraction - result[i, i]))
        return result

    def _features(self, item: ItemFeatures | str) -> ItemFeatures:
        return self._known_items[item] if isinstance(item, str) else item

    def _logit(self, f: ItemFeatures, keys: list[str], mean: np.ndarray) -> float:
        b = f.b - (self.config.irt.priming_b_offset if f.primed else 0.0)
        theta = float(self._loadings(f, keys) @ mean)
        if "practice" in self.extensions and f.cold:
            # The opportunity transition precedes the outcome, and is committed
            # only by observe. Repeated prediction does not add practice.
            theta += self.constants.practice_gamma
        result = f.a * (theta - b)
        if "retrievability" in self.extensions and f.retrievability is not None:
            r = max(1e-6, min(1 - 1e-6, f.retrievability))
            result += self.constants.retrievability_beta * log(r / (1 - r))
        return result

    def predict(self, features: ItemFeatures) -> float:
        if not isinstance(features, ItemFeatures):
            raise TypeError("predict requires outcome-free ItemFeatures")
        return self.predict_item(features).p_success

    def predict_item(self, item: ItemFeatures | str) -> ItemPrediction:
        f = self._features(item)
        keys, mean, covariance = self._view([f])
        covariance = self._drift(f, keys, covariance)
        loadings = self._loadings(f, keys) * f.a
        return ItemPrediction(
            _probability(self._logit(f, keys, mean), self.config.irt.p_clip),
            float(loadings @ covariance @ loadings),
            ((f.lo_id, f.a),) + tuple((key, f.a) for key, _, _ in self._components(f)[2:]),
        )

    def _noise(self, f: ItemFeatures, p: float, mass: float, interpretation: float = 0.0) -> float:
        pq = p * (1 - p)
        difficulty_variance = max(0.0, f.difficulty_variance)
        if f.difficulty_source in {"llm", "llm_estimated", "llm_estimate"}:
            difficulty_variance = max(difficulty_variance, 1.0)
        return (self.config.base_observation_variance * pq / mass
                + (f.a * pq) ** 2 * difficulty_variance + max(0.0, interpretation))

    def _register_regions(self, f: ItemFeatures) -> None:
        components = self._components(f)
        base = components[:2]
        self._regions[f.lo_id] = tuple((key, 1.0) for key, _, _ in base)
        self._prior_variances[f.lo_id] = sum(v for _, _, v in base)
        for key, _, variance in components[2:]:
            self._regions[key] = ((key, 1.0),)
            self._prior_variances[key] = variance

    def observe(self, row: ObservationRow) -> None:
        mass = row.effective_mass
        replace_assistance = (
            not isinstance(row, SignalRow) and "hints" in self.extensions
            and (row.hints_used or row.help_before_work)
        )
        if replace_assistance:
            if row.revision_status == "excluded":
                return
            if row.mass_without_assistance is None:
                raise ValueError("hint replacement requires mass_without_assistance")
            mass = row.mass_without_assistance
        # Must precede even region allocation, clocks, counts, and item caching.
        if not _eligible(row, mass):
            return
        if isinstance(row, SignalRow):
            if "tutor_signals" not in self.extensions:
                return
            day_key = (row.subject_id, row.lo_id, row.observed_at[:10])
            mass = min(row.effective_mass * self.constants.signal_scale,
                       max(0.0, self.constants.signal_daily_cap - self._signal_mass.get(day_key, 0.0)))
            if mass <= 0:
                return
            f = ItemFeatures(row.signal_id, row.lo_id, row.observed_at,
                             subject_id=row.subject_id, cold=False)
            outcome = float(row.outcome)
            interpretation = 0.0
        else:
            f, outcome = row.features, row.outcome
            interpretation = row.interpretation_variance
            if replace_assistance:
                cap = max(self.constants.hint_floor, 1 - self.constants.hint_step * row.hints_used)
                if row.help_before_work:
                    cap = min(cap, self.constants.early_help_cap)
                outcome = min(outcome, cap)
        keys, mean, covariance = self._view([f])
        covariance = self._drift(f, keys, covariance)
        p = _probability(self._logit(f, keys, mean), self.config.irt.p_clip)
        loadings = self._loadings(f, keys)
        if "practice" in self.extensions and f.cold:
            mean[keys.index(f"lo:{f.lo_id}")] += self.constants.practice_gamma
        h = f.a * p * (1 - p) * loadings
        noise = self._noise(f, p, mass, interpretation)
        ph = covariance @ h
        gain = ph / (float(h @ ph) + noise)
        step = gain * (max(0.0, min(1.0, outcome)) - p)
        # Same safety bounds as mastery, applied to the predicted total ability.
        total_step = float(loadings @ step)
        if abs(total_step) > self.config.irt.max_logit_step:
            step *= self.config.irt.max_logit_step / abs(total_step)
        mean += step
        total = float(loadings @ mean)
        bounded = max(-self.config.irt.mu_abs_max, min(self.config.irt.mu_abs_max, total))
        if bounded != total:
            mean[keys.index(f"lo:{f.lo_id}")] += bounded - total
        # Joseph form keeps covariance symmetric PSD without subtractive jitter.
        identity_minus_kh = np.eye(len(keys)) - np.outer(gain, h)
        covariance = identity_minus_kh @ covariance @ identity_minus_kh.T + noise * np.outer(gain, gain)
        covariance = (covariance + covariance.T) * 0.5
        self.keys, self.mean, self.covariance = keys, mean, covariance
        self._register_regions(f)
        if not isinstance(row, SignalRow):
            self._direct.add(f.lo_id)
            self._direct.update(key for key, _, _ in self._components(f)[2:])
            self._known_items[f.item_id] = f
        else:
            # Weak confusion is not direct graded evidence of competence.
            self._signal_mass[day_key] = self._signal_mass.get(day_key, 0.0) + mass
        if not f.primed:
            for key, _, _ in self._components(f):
                self._anchors[key] = f.observed_at

    def region_estimates(self, scope: Iterable[str] | None = None) -> dict[str, RegionEstimate]:
        # Explicitly supplied catalog items can expose an untested region, but
        # mere prediction of an unseen item never changes the posterior/catalog.
        catalog = list(self.items.values())
        keys, mean, covariance = self._view(catalog)
        regions = dict(self._regions)
        priors = dict(self._prior_variances)
        for f in catalog:
            components = self._components(f)
            regions[f.lo_id] = tuple((key, 1.0) for key, _, _ in components[:2])
            priors[f.lo_id] = sum(v for _, _, v in components[:2])
            for key, _, variance in components[2:]:
                regions[key] = ((key, 1.0),)
                priors[key] = variance
        wanted = set(scope) if scope is not None else set(regions)
        result = {}
        for region in sorted(wanted & regions.keys()):
            vector = np.zeros(len(keys))
            for key, loading in regions[region]:
                vector[keys.index(key)] = loading
            variance = max(0.0, float(vector @ covariance @ vector))
            result[region] = RegionEstimate(
                float(vector @ mean), variance,
                max(0.0, priors[region] / max(variance, 1e-15) - 1),
                region not in self._direct,
            )
        return result

    def conditional_gain(self, item: ItemFeatures | str, chosen: Iterable[ItemFeatures | str],
                         weights: Mapping[str, float]) -> float:
        f = self._features(item)
        selected = [self._features(other) for other in chosen]
        catalog = list(self.items.values())
        keys, mean, covariance = self._view([*catalog, *selected, f])
        covariance = self._drift(f, keys, covariance)

        def reduction(feature, prior):
            p = _probability(self._logit(feature, keys, mean), self.config.irt.p_clip)
            h = feature.a * p * (1 - p) * self._loadings(feature, keys)
            ph = prior @ h
            return np.outer(ph, ph) / (float(h @ ph) + self._noise(feature, p, 1.0))

        for other in selected:
            covariance -= reduction(other, covariance)
            # Carry each hypothetical opportunity forward, without observing
            # an outcome or changing the live posterior.
            if "practice" in self.extensions and other.cold:
                mean[keys.index(f"lo:{other.lo_id}")] += self.constants.practice_gamma
        delta = reduction(f, covariance)
        regions = dict(self._regions)
        for feature in [*catalog, *selected, f]:
            regions[feature.lo_id] = tuple((key, 1.0) for key, _, _ in self._components(feature)[:2])
            for key, _, _ in self._components(feature)[2:]:
                regions[key] = ((key, 1.0),)
        gain = 0.0
        for region, weight in weights.items():
            if weight < 0 or not isfinite(weight):
                raise ValueError("region weights must be finite and nonnegative")
            if region in regions:
                vector = np.zeros(len(keys))
                for key, loading in regions[region]:
                    vector[keys.index(key)] = loading
                gain += weight * max(0.0, float(vector @ delta @ vector))
        return gain

    def rebuild(self, rows: Iterable[ObservationRow]) -> None:
        self._reset()
        for row in sorted(rows, key=_order):
            self.observe(row)

    def snapshot_bytes(self) -> bytes:
        """Stable diagnostic serialization, including clocks and directness."""
        metadata = {
            "keys": self.keys, "anchors": self._anchors, "direct": sorted(self._direct),
            "regions": self._regions, "priors": self._prior_variances,
            "signals": sorted((list(key), value) for key, value in self._signal_mass.items()),
            "items": {key: asdict(value) for key, value in sorted(self._known_items.items())},
        }
        return (json.dumps(metadata, sort_keys=True, separators=(",", ":")).encode()
                + self.mean.tobytes() + self.covariance.tobytes())


class MasteryEKF(LoGeneral):
    """Independent-LO adapter: the update itself is production mastery math."""

    def __init__(self, **kwargs):
        super().__init__(name="mastery_ekf", **kwargs)

    def _components(self, f):
        mean, variance = self.lo_priors.get(
            f.lo_id, (0.0, self.config.cold_start_prior_logit_variance))
        return [(f"lo:{f.lo_id}", mean, variance)]

    def _drift(self, f, keys, covariance):
        result = covariance.copy()
        anchor = parse_utc(self._anchors.get(f"lo:{f.lo_id}"))
        now = parse_utc(f.observed_at)
        i = keys.index(f"lo:{f.lo_id}")
        days = max(0.0, (now - anchor).total_seconds() / 86400) if anchor and now else 0.0
        result[i, i] = min(result[i, i] + self.config.sigma2_drift * days, self.config.p_max)
        return result

    def observe(self, row: ObservationRow) -> None:
        if isinstance(row, SignalRow) or not _eligible(row):
            return
        f = row.features
        keys, mean, covariance = self._view([f])
        key = f"lo:{f.lo_id}"
        i = keys.index(key)
        prior = replace(
            initial_mastery_state(f.lo_id, "field-incumbent", f.observed_at),
            logit_mean=float(mean[i]), logit_variance=float(covariance[i, i]),
            last_evidence_at=self._anchors.get(key),
        )
        observation = MasteryObservation(
            rubric_score=row.outcome, max_points=1, evidence_coverage=1.0,
            hint_dampening=1.0, grader_confidence=1.0, attempt_type="standard",
            observed_at=parse_utc(f.observed_at), observation_weight_override=row.effective_mass,
            primed=f.primed, interpretation_variance=row.interpretation_variance,
        )
        state = update_mastery(
            prior, observation, self.config, "field-incumbent", item_a=f.a,
            item_b=f.b - (self.config.irt.priming_b_offset if f.primed else 0.0),
        )
        mean[i], covariance[i, i] = state.logit_mean, state.logit_variance
        self.keys, self.mean, self.covariance = keys, mean, covariance
        self._register_regions(f)
        self._direct.add(f.lo_id)
        self._known_items[f.item_id] = f
        if state.last_evidence_at:
            self._anchors[key] = state.last_evidence_at


class BetaPredictor:
    """Running beta counts, weighted once per attempt (or by facet share)."""

    calibrated_uncertainty = False  # Not a calibrated latent-region covariance.

    def __init__(self, *, name="base_rate_lo", **_kwargs):
        self.name = name
        self.granularity = "facet" if name == "facet_beta" else "attempt"
        self.version_hash = _hash({"implementation": "field-beta-v1", "name": name, "prior": [1, 1]})
        self.counts: dict[str, tuple[float, float]] = {}

    def predict(self, features: ItemFeatures) -> float:
        if not isinstance(features, ItemFeatures):
            raise TypeError("predict requires outcome-free ItemFeatures")
        key = features.facet_id if self.granularity == "facet" else features.lo_id
        alpha, beta = self.counts.get(key or "", (1.0, 1.0))
        return alpha / (alpha + beta)

    def observe(self, row: ObservationRow) -> None:
        if isinstance(row, SignalRow) or not _eligible(row):
            return
        if self.granularity == "facet" and not isinstance(row, FacetRow):
            raise TypeError("facet_beta requires FacetRow")
        key = row.facet_id if isinstance(row, FacetRow) and self.granularity == "facet" else row.lo_id
        mass = row.effective_mass * (row.facet_share if self.granularity == "facet" else 1.0)
        if mass <= 0:
            return
        alpha, beta = self.counts.get(key, (1.0, 1.0))
        self.counts[key] = (alpha + mass * row.outcome, beta + mass * (1 - row.outcome))

    def rebuild(self, rows: Iterable[ObservationRow]) -> None:
        self.counts.clear()
        for row in sorted(rows, key=_order):
            self.observe(row)

    def snapshot_bytes(self) -> bytes:
        return json.dumps(self.counts, sort_keys=True).encode()


# Frozen, store-free inputs the harness may hand to an arm factory. Each arm
# declares the subset it consumes; the others are simply not passed to it.
REPLAY_INPUTS = frozenset({"general_means", "lo_priors", "config", "fsrs_weights"})
_EKF_INPUTS = frozenset({"general_means", "lo_priors", "config", "constants", "items"})

_REGISTRY: dict[str, tuple[Callable[..., Predictor], frozenset[str]]] = {}
_SWEEPS: set[str] = set()
_GROUPS: dict[str, set[str]] = {}


def register_predictor(
    name: str, factory: Callable[..., Predictor], *, sweep: bool = False,
    inputs: Iterable[str] = _EKF_INPUTS, groups: Iterable[str] = (),
) -> None:
    """Phase 3's family arms register here without changing the harness.

    ``inputs`` names the frozen replay inputs the factory accepts; ``groups``
    lets a report select a named arm set (for example ``memory``).
    """
    if name in _REGISTRY:
        raise ValueError(f"predictor already registered: {name}")
    _REGISTRY[name] = (factory, frozenset(inputs))
    if sweep:
        _SWEEPS.add(name)
    for group in groups:
        _GROUPS.setdefault(group, set()).add(name)


def registered_predictors(*, include_sweeps: bool = True, group: str | None = None) -> tuple[str, ...]:
    members = _GROUPS.get(group, set()) if group is not None else None
    return tuple(
        name for name in _REGISTRY
        if (include_sweeps or name not in _SWEEPS) and (members is None or name in members)
    )


def create_predictor(name: str, **kwargs) -> Predictor:
    try:
        factory, inputs = _REGISTRY[name]
    except KeyError:
        raise ValueError(f"unknown predictor: {name}") from None
    unknown = set(kwargs) - REPLAY_INPUTS - inputs
    if unknown:
        raise TypeError(f"{name} does not accept: {', '.join(sorted(unknown))}")
    return factory(**{key: value for key, value in kwargs.items() if key in inputs})


def is_calibrated_predictor(predictor: str | Predictor) -> bool:
    if isinstance(predictor, str):
        if predictor not in _REGISTRY:
            return False
        predictor = create_predictor(predictor)
    return (isinstance(predictor, LearnerPredictor)
            and getattr(predictor, "calibrated_uncertainty", False) is True)


def validate_active_predictor(name: str, *, phase: str = "F1") -> None:
    if not is_calibrated_predictor(name):
        raise ValueError(f"{name} has no calibrated uncertainty and cannot be active")
    if phase == "F1" and name != "mastery_ekf":
        raise ValueError("F1 permits only mastery_ekf; activation needs a successor")


register_predictor("base_rate_lo", lambda **kw: BetaPredictor(name="base_rate_lo", **kw))
register_predictor("facet_beta", lambda **kw: BetaPredictor(name="facet_beta", **kw))
register_predictor("mastery_ekf", MasteryEKF, groups=("families",))
register_predictor("lo_general", LoGeneral, groups=("families",))
_EXTENSIONS = ("practice", "capability", "transfer", "retrievability", "hints", "tutor_signals")
for _extension in _EXTENSIONS:
    register_predictor(
        f"lo_general+{_extension}",
        lambda extension=_extension, **kw: LoGeneral(
            name=f"lo_general+{extension}", extensions=(extension,), **kw),
    )
register_predictor("lo_general+composite", lambda **kw: LoGeneral(
    name="lo_general+composite", extensions=_EXTENSIONS, **kw))
# Field §4.3 idea_hier: lo_general plus PF-a family effects, on the same EKF.
register_predictor("idea_hier", lambda **kw: LoGeneral(
    name="idea_hier", extensions=("family",), **kw), groups=("families",))
for _beta in (0.0, 0.5, 1.0):
    register_predictor(
        f"lo_general+retrievability:beta={_beta:g}",
        lambda beta=_beta, **kw: LoGeneral(
            name=f"lo_general+retrievability:beta={beta:g}", extensions=("retrievability",),
            constants=replace(kw.pop("constants", ArmConstants()), retrievability_beta=beta), **kw),
        sweep=True,
    )
for _scale in (0.5, 1.0, 2.0):
    register_predictor(
        f"lo_general+tutor_signals:scale={_scale:g}",
        lambda scale=_scale, **kw: LoGeneral(
            name=f"lo_general+tutor_signals:scale={scale:g}", extensions=("tutor_signals",),
            constants=replace(kw.pop("constants", ArmConstants()), signal_scale=scale), **kw),
        sweep=True,
    )
for _hint_step in (0.1, 0.2, 0.3):
    register_predictor(
        f"lo_general+hints:step={_hint_step:g}",
        lambda step=_hint_step, **kw: LoGeneral(
            name=f"lo_general+hints:step={step:g}", extensions=("hints",),
            constants=replace(kw.pop("constants", ArmConstants()), hint_step=step), **kw),
        sweep=True,
    )
