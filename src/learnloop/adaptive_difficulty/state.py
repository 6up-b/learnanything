"""The events of §5.6 on a :class:`~learnloop.adaptive_difficulty.model.Bank` (spec_adaptive_difficulty_v1).

A :class:`View` turns AD's events into the bank's linear algebra, in §5.6's
order (the replayer and the simulations order the events):

1. a claim re-anchors a mean (:meth:`View.claim`);
2. a reading opportunity applies its kind's next dose-curve increment
   (:meth:`View.reading`, subject view only), and a self-check verdict its
   learned term (:meth:`View.verdict`, D22);
3. an eligible attempt propagates its touched cells' drift, enters as one
   joint factor (:meth:`View.observe`), then applies the learning transition
   (practice increment, or an in-passage kind's increment in its place), with
   the transfer along couplings and loadings in the subject view;
4. any graded attempt closes its facets' reading windows
   (:meth:`View.close_windows`).

Predictions never create a coordinate: a subject, facet or cell not observed
yet enters as the coordinate it would be created as now
(:meth:`View.prediction`).

``ItemSpec`` is what a decision or an update reads about an item, frozen at
its serve (§7.5): never the item as it stands at rebuild time.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from learnloop.adaptive_difficulty import model as M
from learnloop.adaptive_difficulty import priors as P


@dataclass(frozen=True)
class ItemSpec:
    """An item (or a not-yet-written feature point, §5.7) as AD reads it."""

    item_id: str
    learning_object_id: str
    subject: str
    capability: str
    #: Normalized own facet weights ``w_{i,f}`` (they sum to 1).
    facet_weights: Mapping[str, float]
    #: The resolved ``p1_launch@1`` tuple (audit where answered, else stamped), or None.
    features: Mapping[str, Any] | None = None
    #: ``z_i``: the available signals' values (a missing signal contributes 0).
    signals: Mapping[str, float] = field(default_factory=dict)
    #: ``Q_{i,g}`` onto facets beyond its own (subject view), frozen at the serve.
    loadings: Mapping[str, float] = field(default_factory=dict)
    guess: float = 0.0

    def primary_facet(self) -> str:
        """The highest-weight facet, ties by facet id (§6.1)."""

        return sorted(self.facet_weights.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]

    def cell(self) -> tuple[str, str]:
        return self.primary_facet(), self.capability


def normalized_weights(weights: Mapping[str, float] | None, facets: Sequence[str] = ()) -> dict[str, float]:
    """``evidence_weights`` normalized, falling back to equal weights over ``evidence_facets`` (§5.1)."""

    positive = {str(f): float(w) for f, w in (weights or {}).items() if w is not None and float(w) > 0}
    if positive:
        total = sum(positive.values())
        return {f: w / total for f, w in sorted(positive.items())}
    unique = sorted(dict.fromkeys(str(f) for f in facets))
    if not unique:
        return {}
    return {f: 1.0 / len(unique) for f in unique}


class View:
    """One view's state: the subject view (a bank over the grid) or one LO's view (one filter)."""

    def __init__(self, bank: M.Bank, *, subject_view: bool, reading: bool = False, verdicts: bool = False,
                 signals: Sequence[str] = P.BASE_SIGNALS) -> None:
        self.bank = bank
        self.subject_view = subject_view
        self.reading_on = bool(reading and subject_view and bank.flags["reading"])
        self.verdicts_on = bool(verdicts and self.reading_on and bank.flags["verdict"])
        self.signals = tuple(signals)
        #: n_{κ,f}: each kind's dose on a facet since its last graded attempt (per row).
        self.windows: dict[tuple[str, str], np.ndarray] = {}

    # -- projections ------------------------------------------------------------------

    def _extended_weights(self, spec: ItemSpec) -> dict[str, np.ndarray]:
        """``w̃``: the own weights, less the loadings' share, plus the loaded facets (§5.4)."""

        B = self.bank.B
        loadings = {g: float(q) for g, q in spec.loadings.items() if g not in spec.facet_weights and q > 0}
        if not self.subject_view or not loadings:
            return {f: np.full(B, w) for f, w in spec.facet_weights.items()}
        q_plus = min(sum(loadings.values()), 1.0)
        chi = self.bank.implication
        weights = {f: (1.0 - chi * q_plus) * w for f, w in spec.facet_weights.items()}
        for g, q in loadings.items():
            weights[g] = weights.get(g, np.zeros(B)) + chi * q
        return weights

    def projection(self, spec: ItemSpec, warmth: float | np.ndarray = 0.0
                   ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """``ũ`` over the existing coordinates, plus the mean and variance not-yet-created
        coordinates would bring, created as they would be now (never created by a prediction)."""

        bank = self.bank
        B, d = bank.B, bank.d
        u = np.zeros((B, d))
        extra_mean = np.zeros(B)
        extra_var = np.zeros(B)
        a = P.A

        def add(name: str, coefficient: np.ndarray, *, virtual: tuple[np.ndarray, np.ndarray, np.ndarray] | None) -> None:
            nonlocal extra_mean, extra_var
            if bank.has(name):
                u[:, bank.index[name]] += coefficient
                return
            assert virtual is not None
            coef, mean, own = virtual
            u[:, :] += coefficient[:, None] * coef
            extra_mean = extra_mean + coefficient * mean
            extra_var = extra_var + coefficient * coefficient * own

        ones = np.full(B, a)
        add(M.subject_name(spec.subject), ones,
            virtual=None if bank.has(M.subject_name(spec.subject)) else
            (np.zeros((B, d)), np.zeros(B), bank.split.copy()))
        prior = P.PSI_PRIORS.get(spec.capability)
        if prior is not None:
            add(M.capability_name(spec.subject, spec.capability), ones,
                virtual=None if bank.has(M.capability_name(spec.subject, spec.capability)) else
                (np.zeros((B, d)), np.full(B, prior[0]), np.full(B, prior[1])))
        for facet, weight in sorted(self._extended_weights(spec).items()):
            coefficient = a * weight
            fname = M.facet_name(facet)
            add(fname, coefficient,
                virtual=None if bank.has(fname) else bank.virtual(
                    fname, bank.structure.facet_regression(facet, bank.has) if self.subject_view else None))
            cname = M.cell_name(facet, spec.capability)
            add(cname, coefficient,
                virtual=None if bank.has(cname) else bank.virtual(
                    cname, bank.structure.cell_regression(facet, spec.capability, bank.has)
                    if self.subject_view else None))
        for name, value in P.feature_coding(spec.features).items():
            u[:, bank.index[name]] -= a * value
        for signal in self.signals:
            value = spec.signals.get(signal)
            name = f"alpha:{signal}"
            if value is not None and bank.has(name):
                u[:, bank.index[name]] -= a * float(value)
        u[:, bank.index["zeta"]] += np.broadcast_to(np.asarray(warmth, dtype=np.float64), (B,))
        return u, extra_mean, extra_var

    def prediction(self, spec: ItemSpec, warmth: float | np.ndarray = 0.0) -> tuple[np.ndarray, np.ndarray]:
        """``(m(x), v_e(x))`` per row (§5.7)."""

        u, extra_mean, extra_var = self.projection(spec, warmth)
        return self.bank.moments(u, extra_mean, extra_var)

    def with_cell(self, subject: str, facet: str, capability: str) -> "View":
        """A copy of this view with one cell's coordinates created as they would be now (the
        selection's ``I_c`` reads the cell ability; nothing is created in this view)."""

        clone = View(self.bank.copy(), subject_view=self.subject_view, reading=self.reading_on,
                     verdicts=self.verdicts_on, signals=self.signals)
        clone.windows = {key: value.copy() for key, value in self.windows.items()}
        at = 0.0
        clone.bank.ensure_subject(subject, at)
        clone.bank.ensure_capability(subject, capability)
        clone.bank.ensure_facet(facet, at)
        clone.bank.ensure_cell(facet, capability, at)
        return clone

    def cell_vector(self, subject: str, facet: str, capability: str) -> np.ndarray:
        """The projection of the cell ability ``θ_{f,k}`` (its coordinates must exist)."""

        bank = self.bank
        vector = np.zeros(bank.d)
        for name in (M.subject_name(subject), M.capability_name(subject, capability), M.facet_name(facet),
                     M.cell_name(facet, capability)):
            if bank.has(name):
                vector[bank.index[name]] = 1.0
        return vector

    def cell_moments(self, spec: ItemSpec) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """``(m, v_e, Cov(η_e, θ_c), Var(θ_c))`` for the spec's cell. Call it on :meth:`with_cell`'s copy."""

        facet, capability = spec.cell()
        u, extra_mean, extra_var = self.projection(spec, 0.0)
        a_c = self.cell_vector(spec.subject, facet, capability)
        m, v = self.bank.moments(u, extra_mean, extra_var)
        cov = np.einsum("bi,bij,j->b", u, self.bank.S, a_c)
        var_c = np.einsum("i,bij,j->b", a_c, self.bank.S, a_c)
        return m, v, cov, var_c

    # -- coordinates ------------------------------------------------------------------

    def ensure(self, spec: ItemSpec, at: float) -> None:
        bank = self.bank
        bank.ensure_subject(spec.subject, at)
        bank.ensure_capability(spec.subject, spec.capability)
        for facet in sorted(self._extended_weights(spec)):
            bank.ensure_facet(facet, at)
            bank.ensure_cell(facet, spec.capability, at)

    def ensure_facet(self, subject: str, facet: str, at: float) -> None:
        self.bank.ensure_subject(subject, at)
        self.bank.ensure_facet(facet, at)

    # -- events -----------------------------------------------------------------------

    def observe(self, spec: ItemSpec, category: int | np.ndarray, at: float, *, warmth: float | np.ndarray = 0.0,
                rows: np.ndarray | None = None, in_passage_kind: str | None = None,
                rating: str | None = None, log_latency_ratio: float | None = None,
                learn: bool = True) -> M.UpdateRecord:
        """§5.6 steps 3-5 for one eligible attempt."""

        self.ensure(spec, at)
        weights = self._extended_weights(spec)
        for facet in sorted(weights):
            self.bank.drift(M.cell_name(facet, spec.capability), at)
        u, _m, _v = self.projection(spec, warmth)
        if rating is not None or log_latency_ratio is not None:
            record = self.bank.update_joint(u, category=int(np.asarray(category).reshape(-1)[0]), guess=spec.guess,
                                            rating=rating, log_latency_ratio=log_latency_ratio)
        else:
            record = self.bank.update(u, category, spec.guess, rows=rows)
        if learn:
            self.learn(spec, rows=rows, in_passage_kind=in_passage_kind)
        return record

    def learn(self, spec: ItemSpec, *, rows: np.ndarray | None = None, in_passage_kind: str | None = None) -> None:
        """§5.6 step 5: a practice opportunity for every topic the item draws on, with the
        coupled transfer; an in-passage answer takes its kind's increment in place of ``γ``."""

        bank = self.bank
        mask = np.ones(bank.B) if rows is None else rows.astype(np.float64)
        weights = self._extended_weights(spec)
        if in_passage_kind is not None and self.reading_on:
            doses = {facet: weight * mask for facet, weight in weights.items()}
            self._reading_transition(doses, in_passage_kind)
            return
        for facet, weight in sorted(weights.items()):
            target = M.cell_name(facet, spec.capability)
            bank.add_linear(target, {"gamma": weight * mask})
            if self.subject_view:
                for other in bank.structure.coupled_facets(facet):
                    coupled = M.cell_name(other, spec.capability)
                    if coupled == target or not bank.has(coupled):
                        continue
                    corr = bank.corr0(target, coupled)
                    if np.any(corr != 0):
                        bank.add_linear(coupled, {"gamma": corr * weight * mask})

    def _reading_transition(self, doses: Mapping[str, np.ndarray], kind: str) -> None:
        bank = self.bank
        for facet, dose in sorted(doses.items()):
            dose = np.broadcast_to(np.asarray(dose, dtype=np.float64), (bank.B,))
            if not np.any(dose > 0):
                continue
            n = self.windows.get((kind, facet), np.zeros(bank.B))
            increments = np.array([M.dose_increment(float(n_b), float(d_b)) for n_b, d_b in zip(n, dose)])
            coefficients = {}
            for m_index, scale in ((1, increments[:, 0]), (2, increments[:, 1])):
                coefficients[f"gbar:{m_index}"] = scale
                coefficients[f"delta:{kind}:{m_index}"] = scale
            target = M.facet_name(facet)
            bank.add_linear(target, coefficients)
            for other in bank.structure.coupled_facets(facet):
                coupled = M.facet_name(other)
                if coupled == target or not bank.has(coupled):
                    continue
                corr = bank.corr0(target, coupled)
                if np.any(corr != 0):
                    bank.add_linear(coupled, {name: corr * value for name, value in coefficients.items()})
            self.windows[(kind, facet)] = n + dose

    def reading(self, subject: str, kind: str, facet_doses: Mapping[str, float | np.ndarray], at: float) -> None:
        """A reading opportunity (§5.11): its kind's next dose-curve increment on each facet."""

        if not self.reading_on or kind not in P.READING_KINDS:
            return
        for facet in sorted(facet_doses):
            self.ensure_facet(subject, facet, at)
        self._reading_transition(facet_doses, kind)

    def verdict(self, subject: str, verdict_class: str, facet_doses: Mapping[str, float | np.ndarray],
                at: float) -> None:
        """A self-check verdict (D22): ``θ_f ← θ_f + λ_v·D_f``, with the coupled transfer."""

        coordinate = P.VERDICT_CLASSES.get(verdict_class)
        if not self.verdicts_on or coordinate is None:
            return
        bank = self.bank
        for facet, dose in sorted(facet_doses.items()):
            self.ensure_facet(subject, facet, at)
            dose = np.broadcast_to(np.asarray(dose, dtype=np.float64), (bank.B,))
            target = M.facet_name(facet)
            bank.add_linear(target, {coordinate: dose})
            for other in bank.structure.coupled_facets(facet):
                coupled = M.facet_name(other)
                if coupled == target or not bank.has(coupled):
                    continue
                corr = bank.corr0(target, coupled)
                if np.any(corr != 0):
                    bank.add_linear(coupled, {coordinate: corr * dose})

    def close_windows(self, facets: Sequence[str], rows: np.ndarray | None = None) -> None:
        """§5.6 step 5: a graded attempt on a facet resets its reading windows."""

        for key in list(self.windows):
            if key[1] in facets:
                if rows is None:
                    self.windows[key] = np.zeros(self.bank.B)
                else:
                    self.windows[key] = np.where(rows, 0.0, self.windows[key])

    def claim(self, coordinate: str, mean: float, prior_variance: np.ndarray | float) -> None:
        self.bank.reanchor_mean(coordinate, mean, prior_variance)


__all__ = ["ItemSpec", "View", "normalized_weights"]
