"""Pure offline predictors. No model client, content generator or store access."""
from __future__ import annotations

from datetime import datetime
import math

import numpy as np

from learnloop.offline_outcomes import OutcomeRow, PredictionRow, digest
from learnloop.scheduling.family_memory_model import FamilyMemory  # re-export for harness clients


class IdeaHier:
    """Joint probability-space EKF with independent Gaussian *prior* effects.

    Posterior covariances are retained: observing a family couples it to its LO
    and subject. Dropping those covariances would double-count shared evidence.
    """
    name = "idea_hier"
    granularity = "attempt"

    def __init__(self, *, base_observation_variance: float = 1.0,
                 sigma2_drift: float = 0.0, p_max: float = 10.0):
        self.base_variance = base_observation_variance
        self.drift, self.p_max = sigma2_drift, p_max
        self.version_hash = digest(["idea-hier-ekf-v1", .75, 2.25, .5,
                                    base_observation_variance, sigma2_drift, p_max])
        self.keys: list[tuple[str, str]] = []
        self.mean = np.zeros(0, dtype=np.float64)
        self.cov = np.zeros((0, 0), dtype=np.float64)
        self.last: dict[str, datetime] = {}
        self.direct: dict[tuple[str, str], int] = {}
        self.subject_for_key: dict[tuple[str, str], str] = {}

    def _design(self, row: PredictionRow) -> np.ndarray:
        existing_dimensions = len(self.keys)
        effects = [(("general", row.subject), .75), (("lo", row.lo_id), 2.25)]
        if row.family_id:
            effects.append((("family", row.family_id), .5))
        for key, variance in effects:
            if key not in self.keys:
                self.keys.append(key)
                self.subject_for_key[key] = row.subject
                self.mean = np.pad(self.mean, (0, 1))
                self.cov = np.pad(self.cov, ((0, 1), (0, 1)))
                self.cov[-1, -1] = variance
        previous = self.last.get(row.subject)
        days = max(0, (row.observed_at-previous).total_seconds()/86400) if previous else 0
        # Drift once per subject time step, with diagonal-only positive growth.
        if days and self.drift:
            for i in range(existing_dimensions):
                if self.subject_for_key[self.keys[i]] == row.subject:
                    self.cov[i, i] += min(self.drift*days, max(0, self.p_max-self.cov[i, i]))
        self.last[row.subject] = row.observed_at
        x = np.zeros(len(self.keys))
        for key, _ in effects:
            x[self.keys.index(key)] = row.discrimination
        return x

    def predict(self, row: PredictionRow) -> float:
        x = self._design(row)
        z = float(x @ self.mean) - row.difficulty
        return 1/(1+math.exp(-max(-20, min(20, z))))

    def observe(self, row: OutcomeRow) -> None:
        if row.exclusion or row.features.effective_mass <= 0:
            return
        f = row.features
        p = self.predict(f)
        x = self._design(f)
        h = x*p*(1-p)
        r = self.base_variance*p*(1-p)/f.effective_mass
        r += (p*(1-p))**2 * max(0, f.difficulty_variance)
        ph = self.cov @ h
        innovation = float(h @ ph) + r
        gain = ph/innovation
        self.mean += gain*(row.outcome-p)
        # Joseph form preserves positive semidefiniteness in float64.
        a = np.eye(len(x)) - np.outer(gain, h)
        self.cov = a @ self.cov @ a.T + np.outer(gain, gain)*r
        for i in np.flatnonzero(x):
            key = self.keys[i]
            self.direct[key] = self.direct.get(key, 0)+1

    def region_estimates(self) -> list[dict]:
        priors = {"general": .75, "lo": 2.25, "family": .5}
        return [{"kind": key[0], "id": key[1], "mean": float(self.mean[i]),
                 "variance": float(self.cov[i, i]),
                 "n_eff": max(0, priors[key[0]]/self.cov[i, i]-1),
                 "untested": self.direct.get(key, 0) == 0}
                for i, key in enumerate(self.keys)]
