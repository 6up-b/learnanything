"""The harness arms (spec_adaptive_difficulty_v1 §10.4), scored prequentially on AD's own replay.

Each arm's probability of §5.3's event (an unassisted success) is recorded for
each eligible attempt **before** that attempt updates the arm (chronological,
prequential), with the splits that matter: field's first-attempt split (the
first attempt at a never-seen LO; the primary score, D17), the first surface in
a never-seen cell, first attempts after reading and after a self-check verdict.

* ``ad_threshold@subject`` (the live mixture), ``@subject_uniform`` (its
  uniform-sharing points, renormalized), ``@lo`` (topic-only);
* ``@subject:hyper_fixed[σ_G²/χ_C/χ_Q]`` for each grid point (read from the base
  run's filters: each grid point is one filter);
* ``@subject:noread``, ``@subject:noverdict``, ``@subject:hyper_fine``,
  ``+outside`` (adds ``z_v1``), ``+rating``, ``+timing`` (in both views), and
  ``:grid`` (a QUEST+-exact grid for the served cell's ability, every other
  coordinate at the base subject view's posterior means before that attempt);
* ``:ts`` is a decision-level comparison only (the simulations, ``learnloop.sim``);
* field's ``mastery_ekf`` and ``lo_general`` as external comparators, on field's
  own rows, prequentially (predict, then observe), joined by attempt id.

Constants: ``docs/reviews/adaptive-difficulty-ad23.md`` §1.3. Zero model calls:
everything reads the ledgers and receipts (A1).
"""

from __future__ import annotations

from learnloop.adaptive_difficulty.operation import entry

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any

import numpy as np

from learnloop.adaptive_difficulty import model as M
from learnloop.adaptive_difficulty import outcomes as O
from learnloop.adaptive_difficulty import priors as P
from learnloop.adaptive_difficulty import replay as RP
from learnloop.adaptive_difficulty.state import View

SUBJECT = "ad_threshold@subject"
UNIFORM = "ad_threshold@subject_uniform"
LO = "ad_threshold@lo"
NOREAD = "ad_threshold@subject:noread"
NOVERDICT = "ad_threshold@subject:noverdict"
HYPER_FINE = "ad_threshold@subject:hyper_fine"
GRID = "ad_threshold:grid"
FIELD_ARMS = ("mastery_ekf", "lo_general")
DEFAULT_ARMS = (SUBJECT, UNIFORM, LO, NOREAD, NOVERDICT, "hyper_fixed", HYPER_FINE, "ad_threshold+outside",
                "ad_threshold+rating", "ad_threshold+timing", GRID, *FIELD_ARMS)
GRID_POINTS = np.linspace(-6.0, 6.0, 241)


def hyper_fixed_name(point: P.HyperPoint) -> str:
    return f"ad_threshold@subject:hyper_fixed[{point.key()}]"


@dataclass
class Record:
    attempt_id: str
    learning_object_id: str
    cell: tuple[str, str]
    capability: str
    y: float
    category: int
    warmth: float
    first_attempt_lo: bool
    first_surface_cell: bool
    after_reading: bool
    after_verdict: bool
    created_at: str
    p: dict[str, float] = field(default_factory=dict)
    verdict_class: str | None = None
    doses: dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"attempt_id": self.attempt_id, "learning_object_id": self.learning_object_id,
                "cell": list(self.cell), "capability": self.capability, "y": self.y, "category": self.category,
                "warmth": round(self.warmth, 8), "first_attempt_lo": self.first_attempt_lo,
                "first_surface_cell": self.first_surface_cell, "after_reading": self.after_reading,
                "after_verdict": self.after_verdict, "created_at": self.created_at,
                "verdict_class": self.verdict_class, "doses": {k: round(v, 6) for k, v in sorted(self.doses.items())},
                "p": {name: (None if value is None else round(float(value), 10)) for name, value in sorted(self.p.items())}}


def _p(view: View, spec: Any, warmth: float, weights: np.ndarray | None = None) -> tuple[float, np.ndarray]:
    m, v = view.prediction(spec, warmth)
    rows = M.expected_success(m, v, spec.guess)
    if weights is None:
        weights = view.bank.weights()[0] if view.subject_view and view.bank.P > 1 else np.ones(view.bank.P)
    return float(np.dot(weights, rows)), rows


def _uniform_weights(view: View) -> np.ndarray:
    mask = np.array([p.uniform for p in view.bank.points])
    return view.bank.restricted_weights(mask)[0] if mask.any() else view.bank.weights()[0]


def _run(events: RP.Events, settings: RP.ReplaySettings, *, base: bool, sink: dict[str, Record],
         names: Mapping[str, str], grid: "_GridArm | None" = None) -> None:
    def observer(attempt: RP.AttemptEvent, subject: View, lo_view: View, context: RP.Context) -> None:
        spec = attempt.spec
        record = sink.get(attempt.attempt_id)
        if record is None:
            record = Record(attempt.attempt_id, attempt.learning_object_id, spec.cell(), spec.capability,
                            1.0 if attempt.category == 2 else 0.0, int(attempt.category), attempt.warmth,
                            context.first_attempt_lo, context.first_surface_cell, context.after_reading,
                            context.after_verdict, attempt.created_at, verdict_class=context.verdict_class,
                            doses=dict(context.doses))
            sink[attempt.attempt_id] = record
        if "subject" in names:
            p_subject, rows = _p(subject, spec, attempt.warmth)
            record.p[names["subject"]] = p_subject
            if base:
                record.p[UNIFORM] = float(np.dot(_uniform_weights(subject), rows))
                for index, point in enumerate(subject.bank.points):
                    record.p[hyper_fixed_name(point)] = float(rows[index])
        if "lo" in names:
            record.p[names["lo"]], _rows = _p(lo_view, replace(spec, loadings={}), attempt.warmth)
        if grid is not None:
            # The subject view as it stands before this attempt: the prefix only (review F7).
            grid.observe(attempt, subject, record)

    RP.run(events, settings, trace=False, observer=observer)


class _GridArm:
    """``:grid``: a QUEST+-exact grid for each cell's ability (cold-start prior), demand from the
    subject view's posterior feature effects and signal weights, learning at ``E[γ]``.

    Prequential (Codex review F7): the shared means are read from the subject view **as it
    stands before each attempt** (the base run's observer), never from the replay of the whole
    history, so a later answer never changes an earlier forecast."""

    def __init__(self) -> None:
        self.prior = np.exp(-0.5 * GRID_POINTS ** 2 / P.COLD_START_VARIANCE)
        self.grids: dict[tuple[str, str], np.ndarray] = {}

    def observe(self, attempt: RP.AttemptEvent, subject: View, record: Record | None) -> None:
        bank = subject.bank
        weights = bank.weights()[0]
        means = {name: float(np.dot(weights, bank.mu[:, i])) for name, i in bank.index.items()}
        gamma = means.get("gamma", P.GAMMA_PRIOR[1])
        spec = attempt.spec
        cell = spec.cell()
        prior = self.prior / self.prior.sum()
        posterior = self.grids.get(cell, prior)
        demand = sum(means.get(name, 0.0) * value for name, value in P.feature_coding(spec.features).items())
        demand += sum(means.get(f"alpha:{name}", 0.0) * value for name, value in spec.signals.items()
                      if f"alpha:{name}" in means)
        eta = GRID_POINTS - demand + means.get("zeta", 1.0) * attempt.warmth
        success = M.residual_success(eta, spec.guess)
        if record is not None:
            record.p[GRID] = float(np.dot(posterior, success))
        nodes = eta[:, None] - P.A * P.TAU0 * M.X32[None, :]
        likelihood = (M.W32 * M.category_likelihood(nodes, np.full(len(eta), spec.guess),
                                                     np.full(len(eta), attempt.category))).sum(1)
        updated = posterior * likelihood
        updated = updated / updated.sum()
        # Learning: the grid shifts by E[γ] (interpolated onto the grid).
        updated = np.interp(GRID_POINTS - gamma, GRID_POINTS, updated, left=0.0, right=0.0)
        self.grids[cell] = updated / updated.sum() if updated.sum() > 0 else prior


def _field_arms(connection: Any, vault: Any, view: Any, sink: dict[str, Record]) -> dict[str, int]:
    """Field's ``mastery_ekf`` and ``lo_general`` on field's rows (read through AD's history fallback),
    prequentially (predict, observe)."""

    from learnloop.field.predictors import create_predictor

    from learnloop.adaptive_difficulty.successor import history_fallback

    # The comparators read the same history as AD's replay (its history fallback and its material
    # view, A8), so every arm is scored on the same past and no attempt on a withheld item updates
    # one. With the predicate unavailable the view is empty: no comparator observes anything.
    rows = sorted(view.field_rows(connection, legacy_fallback=history_fallback(vault.config)),
                  key=lambda r: (r.observed_at, r.attempt_id))
    covered: dict[str, int] = {}
    for name in FIELD_ARMS:
        arm = create_predictor(name, config=vault.config.mastery)
        count = 0
        for row in rows:
            record = sink.get(row.attempt_id)
            if record is not None and math.isfinite(row.effective_mass) and row.effective_mass > 0:
                try:
                    record.p[name] = float(arm.predict(row.features))
                    count += 1
                except Exception:  # noqa: BLE001 - an arm that abstains is not scored
                    pass
            arm.observe(row)
        covered[name] = count
    return covered


@entry(read_only=True)
def prequential(vault: Any, repository: Any, connection: Any, *, arms: Sequence[str] = DEFAULT_ARMS,
                view: Any = None) -> dict[str, Any]:
    """Every arm's prequential predictions, keyed by attempt (zero model calls).

    The base run (``ad_threshold@subject`` and the arms read from its filters) replays with the
    settings serving and the replayer read, :meth:`RP.ReplaySettings.from_config` (Codex verify
    F12): with ``learned_coupling`` off the report scores the predictor that serves, with no
    learned coupling, never a coupled one the learner was not served. The ablation arms vary one
    part of those settings."""

    from learnloop.adaptive_difficulty.material_view import material_view

    selected = set(arms)
    view = material_view(vault, repository, view)
    base_settings = RP.ReplaySettings.from_config(vault.config)
    events = RP.load_events(connection, vault, repository, settings=base_settings, view=view)
    sink: dict[str, Record] = {}
    _run(events, base_settings, base=True, sink=sink, names={"subject": SUBJECT, "lo": LO},
         grid=_GridArm() if GRID in selected else None)
    runs: list[tuple[str, RP.ReplaySettings, dict[str, str]]] = []
    if NOREAD in selected:
        runs.append((NOREAD, replace(base_settings, reading=False, verdicts=False), {"subject": NOREAD}))
    if NOVERDICT in selected:
        runs.append((NOVERDICT, replace(base_settings, verdicts=False), {"subject": NOVERDICT}))
    if HYPER_FINE in selected:
        runs.append((HYPER_FINE, replace(base_settings, hyper=P.HYPER_FINE_VERSION), {"subject": HYPER_FINE}))
    for sub in ("outside", "rating", "timing"):
        name = f"ad_threshold+{sub}"
        if name in selected:
            runs.append((name, replace(base_settings, **{sub: True}),
                         {"subject": f"{SUBJECT}+{sub}", "lo": f"{LO}+{sub}"}))
    for _name, settings, names in runs:
        sub_events = RP.load_events(connection, vault, repository, settings=settings, view=view)
        _run(sub_events, settings, base=False, sink=sink, names=names)
    coverage = _field_arms(connection, vault, view, sink) if set(FIELD_ARMS) & selected else {}
    records = sorted(sink.values(), key=lambda r: (r.created_at, r.attempt_id))
    return {"records": records, "field_coverage": coverage, "events": events, "settings": base_settings,
            "view": view}


__all__ = ["DEFAULT_ARMS", "FIELD_ARMS", "GRID", "HYPER_FINE", "LO", "NOREAD", "NOVERDICT", "Record", "SUBJECT",
           "UNIFORM", "hyper_fixed_name", "prequential"]
