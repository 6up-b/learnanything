"""The active learner predictor as placement consumes it (field §4.1, G10).

Placement reads predictions only through the ``LearnerPredictor`` contract.
At launch the active predictor is the incumbent ``mastery_ekf`` (D1): the
per-LO 2PL EKF that LearnLoop already maintains in ``learning_object_mastery``.
This adapter serves that persisted state live; it never re-fits, observes or
writes. Offline replay uses the field harness's own ``mastery_ekf`` arm.

``cross_lo_sharing`` is False: the incumbent propagates nothing across LOs, so
it can never assume an LO before any attempt (field §5.2 "prediction" source).
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from hashlib import sha256
import json
from math import exp
from typing import Any

from learnloop.db.repositories import MasteryState, Repository
from learnloop.field.types import ItemFeatures, ItemPrediction, LearnerPredictor, RegionEstimate
from learnloop.learner.mastery import initial_mastery_state_for_learning_object, resolve_item_irt_params
from learnloop.vault.models import LoadedVault

LIVE_INCUMBENT_VERSION = "live-mastery-ekf-v1"


class PredictorNotActivatable(ValueError):
    """The configured active predictor has no live adapter (needs Phase 4)."""


def _sigmoid(value: float) -> float:
    value = max(-700.0, min(700.0, value))
    return 1.0 / (1.0 + exp(-value))


class LiveMasteryPredictor:
    """``mastery_ekf`` served from the persisted per-LO posterior."""

    name = "mastery_ekf"
    granularity = "attempt"
    calibrated_uncertainty = True
    cross_lo_sharing = False

    def __init__(
        self,
        vault: LoadedVault,
        repository: Repository,
        *,
        mastery_states: Mapping[str, MasteryState] | None = None,
        now_iso: str = "1970-01-01T00:00:00Z",
    ) -> None:
        self._vault = vault
        self._repository = repository
        self._states = dict(mastery_states if mastery_states is not None else repository.mastery_states())
        self._item_params = repository.item_parameter_states()
        self._now_iso = now_iso
        self._priors: dict[str, MasteryState] = {}
        mastery = vault.config.mastery.model_dump(mode="json")
        self.version_hash = sha256(
            json.dumps({"implementation": LIVE_INCUMBENT_VERSION, "mastery": mastery},
                       sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    # -- state -------------------------------------------------------------

    def _state(self, learning_object_id: str) -> tuple[MasteryState, bool]:
        """(posterior or claim-anchored prior, untested)."""

        state = self._states.get(learning_object_id)
        if state is not None and state.last_evidence_at is not None:
            return state, False
        prior = self._priors.get(learning_object_id)
        if prior is None:
            prior = state or initial_mastery_state_for_learning_object(
                self._vault, self._repository, learning_object_id, self._now_iso
            )
            self._priors[learning_object_id] = prior
        return prior, True

    def _item(self, item: ItemFeatures | str) -> tuple[str, float, float]:
        if isinstance(item, ItemFeatures):
            return item.lo_id, item.a, item.b
        practice_item = self._vault.practice_items.get(item)
        if practice_item is None:
            raise KeyError(f"unknown practice item {item!r}")
        learning_object = self._vault.learning_object_for_item(practice_item)
        a, b = resolve_item_irt_params(
            practice_item, learning_object, self._vault.config.mastery, self._item_params.get(item),
        )
        return str(practice_item.learning_object_id), float(a), float(b)

    # -- LearnerPredictor ----------------------------------------------------

    def predict(self, features: ItemFeatures) -> float:
        return self.predict_item(features).p_success

    def predict_item(self, item: ItemFeatures | str) -> ItemPrediction:
        lo_id, a, b = self._item(item)
        state, _untested = self._state(lo_id)
        p = _sigmoid(a * (state.logit_mean - b))
        clip = self._vault.config.mastery.irt.p_clip
        p = max(clip, min(1 - clip, p))
        return ItemPrediction(p, a * a * state.logit_variance, ((lo_id, a),))

    def region_estimates(self, scope: Iterable[str] | None = None) -> dict[str, RegionEstimate]:
        wanted = sorted(set(scope) if scope is not None else set(self._vault.learning_objects))
        prior_variance = float(self._vault.config.mastery.cold_start_prior_logit_variance)
        result: dict[str, RegionEstimate] = {}
        for lo_id in wanted:
            state, untested = self._state(lo_id)
            variance = max(float(state.logit_variance), 0.0)
            result[lo_id] = RegionEstimate(
                float(state.logit_mean),
                variance,
                max(0.0, prior_variance / max(variance, 1e-15) - 1.0),
                untested,
            )
        return result

    def conditional_gain(
        self,
        item: ItemFeatures | str,
        chosen: Iterable[ItemFeatures | str],
        weights: Mapping[str, float],
    ) -> float:
        """Expected posterior-variance reduction, weighted by region.

        Each already-chosen item first reduces its own LO's variance; LOs are
        independent, so only same-LO choices interact. Deterministic.
        """

        variances: dict[str, float] = {}

        def variance(lo_id: str) -> float:
            if lo_id not in variances:
                variances[lo_id] = float(self._state(lo_id)[0].logit_variance)
            return variances[lo_id]

        def reduction(target: ItemFeatures | str) -> tuple[str, float]:
            lo_id, a, _b = self._item(target)
            p = self.predict_item(target).p_success
            h = a * p * (1 - p)
            noise = self._vault.config.mastery.base_observation_variance * p * (1 - p)
            prior = variance(lo_id)
            return lo_id, (prior * h) ** 2 / (h * h * prior + noise)

        for other in chosen:
            lo_id, delta = reduction(other)
            variances[lo_id] = max(variance(lo_id) - delta, 0.0)
        lo_id, delta = reduction(item)
        weight = weights.get(lo_id, 0.0)
        if weight < 0:
            raise ValueError("region weights must be nonnegative")
        return weight * delta

    def observe(self, row: Any) -> None:  # pragma: no cover - contract guard
        raise NotImplementedError("the live incumbent observes only through the attempt path")

    def rebuild(self, rows: Iterable[Any]) -> None:  # pragma: no cover - contract guard
        raise NotImplementedError("the live incumbent is rebuilt by derived-state replay")


def active_predictor(
    vault: LoadedVault,
    repository: Repository,
    *,
    mastery_states: Mapping[str, MasteryState] | None = None,
    now_iso: str = "1970-01-01T00:00:00Z",
) -> LearnerPredictor:
    """The configured ``field.active_predictor``, served live.

    Only the incumbent exists live. Activating a challenger is its own
    algorithm successor (field §7.4, Slice A Phase 4), which adds its adapter.
    """

    name = vault.config.field.active_predictor
    if name != "mastery_ekf":
        raise PredictorNotActivatable(f"{name} has no live adapter; activation needs its successor")
    return LiveMasteryPredictor(vault, repository, mastery_states=mastery_states, now_iso=now_iso)
