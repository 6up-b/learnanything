"""T8 learner success head: pure prequential arms and the pre-registered analysis.

Offline research only (Slice 2 §11); no live consumer, never active (G11).
No vault, repository, connection or model client. An arm sees outcome-free
``ItemFeatures`` at prediction time, the observation rows the harness hands it
after every prediction, and a frozen item-side :class:`ContentIndex`: the stem
the learner saw, its KC names and MRL-truncated vectors, keyed by attempt
identity. It looks up only the attempt it is asked about.

Item difficulty enters only from the solver panel (``difficulty_source =
"solver_panel"``), never from an LLM label (2609.27063: rho = 0.06). The
internal ability filter is the incumbent's EKF run with ``a = 1, b = 0``.

The constants below are a priori and versioned (field F5); they are recorded,
with the kill rule, in ``docs/reviews/slice-2-t8.md`` before any run.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field, replace
from hashlib import sha256
import json
from math import exp, isfinite, log, log1p, pi, sqrt
from types import MappingProxyType

import numpy as np

from learnloop.clock import parse_utc
from learnloop.field.predictors import MasteryEKF, _eligible
from learnloop.field.types import FacetRow, ItemFeatures, ObservationRow, SignalRow


SOLVER_PANEL = "solver_panel"
STEM_VIEW, SKELETON_VIEW = "stem", "skeleton"
EMBEDDING_DIMENSIONS = 32
EXPLICIT_ARMS = ("base_rate_lo", "mastery_ekf", "lo_general", "tag_logistic")
PRIMARY_ARM = "emb_ridge"
GATED_ARMS = ("success_head", "success_head+difficulty")
LLM_ARMS = ("llm_zero_data", "llm_zero_data:recalibrated")


@dataclass(frozen=True)
class HeadPriors:
    """Gaussian prior per feature block, fixed before any replay (F5)."""

    bias_variance: float = 1.0
    ability_mean: float = 1.0
    ability_variance: float = 0.25
    feature_variance: float = 0.25
    tag_variance: float = 0.25
    embedding_variance: float = 0.25
    difficulty_mean: float = -1.0
    difficulty_variance: float = 0.25
    recency_half_life_days: float = 1.0

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if not isfinite(value) or (name.endswith(("variance", "days")) and value <= 0):
                raise ValueError(f"{name} must be finite (and positive for variances)")


PREREGISTRATION: Mapping[str, object] = MappingProxyType({
    "version": "t8-preregistration-v2",
    # v2 (2026-10-12, before any run on owner data): embedding block variance
    # 1.0 -> 0.25 per dimension, after a synthetic-only check; see the review.
    "registered": "2026-10-12",
    "question": "Does a frozen-embedding success predictor add held-out value over explicit arms?",
    "primary_arm": PRIMARY_ARM,
    "explicit_arms": list(EXPLICIT_ARMS),
    "baseline_rule": "lowest mean log loss in explicit_arms on the common attempts",
    "gated_arms": list(GATED_ARMS),
    "descriptive_arms": [*LLM_ARMS, "emb_ridge_vs_tag_logistic"],
    "margin_nats_per_attempt": 0.0,
    "min_common_attempts": 100,
    "coverage_caveat_below": 0.8,
    "bootstrap": {"samples": 1000, "seed": 0, "unit": "attempt", "paired": True,
                  "interval": "percentile_95"},
    "embedding_view": {"dimensions": EMBEDDING_DIMENSIONS, "projection": "mrl_prefix_l2",
                       "centering": "mean_of_previously_observed_attempts", "renormalize": True},
    "priors": asdict(HeadPriors()),
    "fit": "prequential Newton MAP on all past positive-mass attempts, weighted by mass",
    "moderation": "mackay_probit",
    "difficulty": "solver_panel only; the internal ability filter uses a=1, b=0",
    "llm": {"history_window": 25, "stem_char_cap": 6000,
            "recalibration": "one logit intercept, MAP under N(0, 1) on past predictions only"},
})


def preregistration_hash() -> str:
    return _hash(dict(PREREGISTRATION))


def _hash(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             allow_nan=False).encode()).hexdigest()


def _sigmoid(value: float) -> float:
    return 1 / (1 + exp(-max(-700.0, min(700.0, value))))


def _logit(p: float, clip: float = 1e-6) -> float:
    p = max(clip, min(1 - clip, p))
    return log(p / (1 - p))


@dataclass(frozen=True)
class AttemptContent:
    """Item-side content of one attempt; never an answer, grade or outcome.

    ``stem`` is the text the learner actually saw (the graded snapshot, or the
    explicitly reconstructed current content); ``vectors`` maps a view name to
    its MRL-truncated unit vector for exactly that text.
    """

    stem: str | None = None
    stem_source: str = "unavailable"
    kcs: tuple[str, ...] = ()
    vectors: Mapping[str, tuple[float, ...]] = field(default_factory=dict)


class ContentIndex:
    """Frozen content keyed by attempt identity ``(item_id, observed_at)``.

    Lookups take the features being predicted, so an arm can only read the
    attempt it is asked about. Ambiguous keys are resolved by the loader.
    """

    def __init__(self, entries: Mapping[tuple[str, str], AttemptContent], *,
                 embedding_model: str | None = None, views: Iterable[str] = (STEM_VIEW,),
                 dimensions: int = EMBEDDING_DIMENSIONS):
        self._entries = MappingProxyType(dict(entries))
        self.embedding_model = embedding_model
        self.views = tuple(views)
        self.dimensions = dimensions
        for content in self._entries.values():
            for view, vector in content.vectors.items():
                if view not in self.views or len(vector) != dimensions:
                    raise ValueError("content vectors must match the declared views and dimensions")
        self.digest = _hash({
            "model": embedding_model, "views": list(self.views), "dimensions": dimensions,
            "entries": sorted(
                [list(key), content.stem_source, _hash(content.stem), list(content.kcs),
                 {view: _hash([round(v, 12) for v in vector])
                  for view, vector in sorted(content.vectors.items())}]
                for key, content in self._entries.items()
            ),
        })

    def get(self, features: ItemFeatures) -> AttemptContent | None:
        if not isinstance(features, ItemFeatures):
            raise TypeError("content lookups take outcome-free ItemFeatures")
        return self._entries.get((features.item_id, features.observed_at))

    def vector(self, features: ItemFeatures, view: str) -> np.ndarray | None:
        content = self.get(features)
        vector = None if content is None else content.vectors.get(view)
        return None if vector is None else np.asarray(vector, dtype=np.float64)


EMPTY_CONTENT = ContentIndex({})


def _days(earlier, later) -> float:
    return max(0.0, (later - earlier).total_seconds() / 86400) if earlier and later else 0.0


class LogisticHead:
    """Prequential Bayesian logistic regression over fixed feature blocks.

    After every observed outcome the MAP is refit by Newton on all past
    positive-mass attempts. ``moderated`` predicts with the Laplace posterior
    (MacKay's probit approximation), so predictions widen toward 0.5 where the
    data give little support; otherwise the MAP point (ridge-logistic) is used.
    Features for a past row are frozen at the time it was predicted, except the
    embedding centring, which always uses the current past-only mean.
    """

    granularity = "attempt"
    calibrated_uncertainty = False  # Research only; G11 keeps it inactive.

    def __init__(self, *, name: str, views: Iterable[str] = (), moderated: bool = False,
                 difficulty: bool = False, content: ContentIndex | None = None,
                 config=None, lo_priors: Mapping[str, tuple[float, float]] | None = None,
                 priors: HeadPriors | None = None):
        self.name = name
        self.views = tuple(views)
        self.moderated = moderated
        self.difficulty = difficulty
        self.content = content or EMPTY_CONTENT
        if self.views and STEM_VIEW not in self.views:
            raise ValueError("embedding arms require the stem view")
        if any(view not in self.content.views for view in self.views):
            raise ValueError("embedding view missing from the content index")
        self.priors = priors or HeadPriors()
        self._config = config
        self._lo_priors = dict(lo_priors or {})
        self.version_hash = _hash({
            "implementation": "t8-logistic-head-v1", "name": name, "views": list(self.views),
            "moderated": moderated, "difficulty": difficulty, "priors": asdict(self.priors),
            "dimensions": self.content.dimensions if self.views else 0,
            "content": self.content.digest if self.views else None,
            "mastery": config.model_dump(mode="json") if config is not None else None,
            "lo_priors": self._lo_priors,
        })
        self._reset()

    # -- state ---------------------------------------------------------------

    def _reset(self) -> None:
        self._ability = MasteryEKF(config=self._config, lo_priors=self._lo_priors)
        # Dense explicit values over the names known when each row was
        # observed (names only append, and an absent feature is zero), plus the
        # raw view vectors, outcomes and masses.
        self._rows: list[np.ndarray] = []
        self._raw_rows: dict[str, list[np.ndarray | None]] = {view: [] for view in self.views}
        self._outcomes: list[float] = []
        self._masses: list[float] = []
        self._names: list[str] = []
        self._index: dict[str, int] = {}
        self._weights = np.zeros(0)
        self._covariance = np.zeros((0, 0))
        self._lo: dict[str, tuple[float, float, int]] = {}
        self._lo_last: dict[str, object] = {}
        self._item_last: dict[str, tuple[object, float]] = {}
        # Decayed running sums of (outcome - 0.5) and weight, as of _recent_at.
        self._recent = (0.0, 0.0)
        self._recent_at = None
        self._view_sum = {view: np.zeros(self.content.dimensions) for view in self.views}
        self._view_count = {view: 0 for view in self.views}
        for view in self.views:
            for k in range(self.content.dimensions):
                self._add_name(f"{view}:{k}")

    def _add_name(self, name: str) -> None:
        if name not in self._index:
            self._index[name] = len(self._names)
            self._names.append(name)
            self._weights = np.append(self._weights, self._prior(name)[0])
            self._covariance = np.pad(self._covariance, ((0, 1), (0, 1)))
            self._covariance[-1, -1] = self._prior(name)[1]

    def _prior(self, name: str) -> tuple[float, float]:
        p = self.priors
        if name == "bias":
            return 0.0, p.bias_variance
        if name == "ability":
            return p.ability_mean, p.ability_variance
        if name == "difficulty":
            return p.difficulty_mean, p.difficulty_variance
        if name.startswith(tuple(f"{view}:" for view in (STEM_VIEW, SKELETON_VIEW))):
            return 0.0, p.embedding_variance
        if name.startswith(("lo:", "capability:", "relation:")):
            return 0.0, p.tag_variance
        return 0.0, p.feature_variance

    @staticmethod
    def _neutral(features: ItemFeatures) -> ItemFeatures:
        # No item difficulty reaches the ability filter (only solver-panel b
        # may enter, through the explicit difficulty block).
        return replace(features, a=1.0, b=0.0, difficulty_variance=0.0)

    def _explicit(self, f: ItemFeatures) -> dict[str, float]:
        when = parse_utc(f.observed_at)
        if when is None:
            raise ValueError("every attempt needs a valid timestamp")
        alpha, beta, count = self._lo.get(f.lo_id, (1.0, 1.0, 0))
        values = {
            "bias": 1.0,
            "ability": _logit(self._ability.predict(self._neutral(f))),
            "lo_rate": log(alpha / beta),
            "practice": log1p(count),
            "since_lo": log1p(_days(self._lo_last.get(f.lo_id), when)),
            "recency": self._recency(when),
            "primed": float(f.primed),
            "warm": float(not f.cold),
            f"lo:{f.lo_id}": 1.0,
        }
        last = self._item_last.get(f.item_id)
        if last is not None:
            values.update(seen_item=1.0, item_last=last[1] - 0.5,
                          since_item=log1p(_days(last[0], when)))
        if f.capability:
            values[f"capability:{f.capability}"] = 1.0
        if f.variant_relation:
            values[f"relation:{f.variant_relation}"] = 1.0
        if self.difficulty and f.difficulty_source == SOLVER_PANEL and isfinite(f.b):
            values["difficulty"] = float(f.b)
        return values

    def _decayed(self, when) -> tuple[float, float]:
        decay = 0.5 ** (_days(self._recent_at, when) / self.priors.recency_half_life_days)
        return self._recent[0] * decay, self._recent[1] * decay

    def _recency(self, when) -> float:
        # A 1-day half-life time-decay summary of every past outcome, shrunk
        # toward zero by one pseudo-observation. Replay order is chronological,
        # so the decayed running sums equal the full weighted sums.
        total, weight = self._decayed(when)
        return total / (weight + 1.0)

    def _raw(self, f: ItemFeatures) -> dict[str, np.ndarray | None]:
        return {view: self.content.vector(f, view) for view in self.views}

    def _centred(self, view: str, vector: np.ndarray | None) -> np.ndarray:
        dims = self.content.dimensions
        if vector is None or not self._view_count[view]:
            return np.zeros(dims)
        centred = vector - self._view_sum[view] / self._view_count[view]
        norm = float(np.linalg.norm(centred))
        return centred / norm if norm > 1e-12 else np.zeros(dims)

    def _design_row(self, explicit: Mapping[str, float], raw: Mapping[str, np.ndarray | None]):
        """Dense values over known names, plus (value, prior) for unseen names."""
        x = np.zeros(len(self._names))
        unseen = []
        for name, value in explicit.items():
            if name in self._index:
                x[self._index[name]] = value
            else:
                unseen.append((value, *self._prior(name)))
        for view in self.views:
            start = self._index[f"{view}:0"]
            x[start:start + self.content.dimensions] = self._centred(view, raw[view])
        return x, unseen

    # -- harness contract ----------------------------------------------------

    def covers(self, features: ItemFeatures) -> bool:
        if self.difficulty and features.difficulty_source != SOLVER_PANEL:
            return False
        return not self.views or self.content.vector(features, STEM_VIEW) is not None

    def predict(self, features: ItemFeatures) -> float:
        if not isinstance(features, ItemFeatures):
            raise TypeError("predict requires outcome-free ItemFeatures")
        x, unseen = self._design_row(self._explicit(features), self._raw(features))
        mean = float(x @ self._weights) + sum(value * m for value, m, _ in unseen)
        if self.moderated:
            variance = float(x @ self._covariance @ x) + sum(value * value * v for value, _, v in unseen)
            mean /= sqrt(1 + pi * max(0.0, variance) / 8)
        return min(1 - 1e-6, max(1e-6, _sigmoid(mean)))

    def observe(self, row: ObservationRow) -> None:
        if isinstance(row, (SignalRow, FacetRow)) or not _eligible(row):
            return
        f = row.features
        explicit, raw = self._explicit(f), self._raw(f)
        for name in explicit:
            self._add_name(name)
        dense = np.zeros(len(self._names))
        for name, value in explicit.items():
            dense[self._index[name]] = value
        self._rows.append(dense)
        for view, vector in raw.items():
            self._raw_rows[view].append(vector)
        self._outcomes.append(float(row.outcome))
        self._masses.append(float(row.effective_mass))
        # State changes only after this row's features are frozen.
        self._ability.observe(replace(row, features=self._neutral(f)))
        when = parse_utc(f.observed_at)
        alpha, beta, count = self._lo.get(f.lo_id, (1.0, 1.0, 0))
        mass = row.effective_mass
        self._lo[f.lo_id] = (alpha + mass * row.outcome, beta + mass * (1 - row.outcome), count + 1)
        self._lo_last[f.lo_id] = when
        self._item_last[f.item_id] = (when, float(row.outcome))
        total, weight = self._decayed(when)
        self._recent = (total + float(row.outcome) - 0.5, weight + 1.0)
        self._recent_at = when
        for view, vector in raw.items():
            if vector is not None:
                self._view_sum[view] = self._view_sum[view] + vector
                self._view_count[view] += 1
        self._fit()

    def rebuild(self, rows: Iterable[ObservationRow]) -> None:
        self._reset()
        for row in sorted(rows, key=lambda r: (r.observed_at, getattr(r, "attempt_id", ""))):
            self.observe(row)

    # -- fit -------------------------------------------------------------------

    def _design(self) -> np.ndarray:
        X = np.zeros((len(self._rows), len(self._names)))
        for i, dense in enumerate(self._rows):
            X[i, :dense.size] = dense
        dims = self.content.dimensions
        for view in self.views:
            start = self._index[f"{view}:0"]
            present = np.array([vector is not None for vector in self._raw_rows[view]], dtype=bool)
            if not present.any():
                continue
            V = np.stack([vector for vector in self._raw_rows[view] if vector is not None])
            centred = V - self._view_sum[view] / self._view_count[view]
            norms = np.linalg.norm(centred, axis=1, keepdims=True)
            Z = np.divide(centred, norms, out=np.zeros_like(centred), where=norms > 1e-12)
            X[np.flatnonzero(present), start:start + dims] = Z
        return X

    def _fit(self) -> None:
        X = self._design()
        y = np.asarray(self._outcomes)
        s = np.asarray(self._masses)
        prior_mean = np.array([self._prior(name)[0] for name in self._names])
        precision = 1 / np.array([self._prior(name)[1] for name in self._names])
        weights, hessian = newton_map(X, y, s, prior_mean, precision, self._weights)
        self._weights = weights
        self._covariance = _symmetric_inverse(hessian)


def _objective(X, y, s, prior_mean, precision, w):
    eta = X @ w
    return float(s @ (np.logaddexp(0.0, eta) - y * eta) + 0.5 * precision @ (w - prior_mean) ** 2)


def newton_map(X, y, s, prior_mean, precision, start, *, tolerance=1e-10, max_iterations=100):
    """Weighted logistic MAP under independent Gaussian priors; strictly convex.

    Returns ``(weights, hessian_at_map)``. Damped Newton with backtracking.
    """
    w = np.asarray(start, dtype=np.float64).copy()
    for _ in range(max_iterations):
        p = 1 / (1 + np.exp(-np.clip(X @ w, -700, 700)))
        gradient = X.T @ (s * (p - y)) + precision * (w - prior_mean)
        hessian = (X.T * (s * p * (1 - p))) @ X + np.diag(precision)
        step = np.linalg.solve(hessian, gradient)
        current = _objective(X, y, s, prior_mean, precision, w)
        t = 1.0
        while t > 1e-12 and _objective(X, y, s, prior_mean, precision, w - t * step) > (
            current - 1e-4 * t * float(gradient @ step)
        ):
            t /= 2
        w = w - t * step
        if float(np.max(np.abs(t * step), initial=0.0)) < tolerance:
            break
    p = 1 / (1 + np.exp(-np.clip(X @ w, -700, 700)))
    hessian = (X.T * (s * p * (1 - p))) @ X + np.diag(precision)
    return w, hessian


def _symmetric_inverse(matrix: np.ndarray) -> np.ndarray:
    if not matrix.size:
        return matrix
    inverse = np.linalg.inv(matrix)
    return (inverse + inverse.T) * 0.5


def success_head_arms(content: ContentIndex, *, config=None, lo_priors=None,
                      include_difficulty: bool = False) -> tuple[LogisticHead, ...]:
    """Fresh T8 arms. Embedding views are whatever the index carries."""
    views = content.views
    arms = [
        LogisticHead(name="tag_logistic", config=config, lo_priors=lo_priors),
        LogisticHead(name="emb_ridge", views=views, content=content, config=config, lo_priors=lo_priors),
        LogisticHead(name="success_head", views=views, content=content, moderated=True,
                     config=config, lo_priors=lo_priors),
    ]
    if include_difficulty:
        arms.append(LogisticHead(name="success_head+difficulty", views=views, content=content,
                                 moderated=True, difficulty=True, config=config, lo_priors=lo_priors))
    return tuple(arms)
