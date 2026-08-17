"""P2 causal-lane fill / abstention telemetry (contract §8, v1 §12).

Standing constraint 2 watches BOTH tails of the lazy/eager spectrum: a field
that is null on 100% of rows is exactly the anomaly it names, and it is why the
inert P2 path passed review the first time.  ``support_scores`` was ``None`` on
every receipt ever written, ``repair_class_id`` was ``None`` on every hypothesis
ever minted, and nothing measured either.

This module is the measurement.  It is deliberately a *report*, not a schema:
every number is derived from rows that already exist, no table is added, and
nothing here can influence a routing decision.

Two-tailed reading.  For each channel the report gives ``fill_rate``,
``abstention_rate`` and a ``tail`` verdict:

* ``empty``      — nothing filled and nothing abstained (n >= ``min_rows``).
                   The channel has no producer; this is the inert-lane signature.
* ``saturated``  — everything filled.  Suspicious in the other direction: a
                   field no row ever declines to fill is usually not being
                   judged, it is being defaulted.
* ``mixed``      — the healthy shape.
* ``insufficient`` — fewer than ``min_rows`` rows to judge either way.

An ABSTENTION is a typed, recorded refusal (``unavailable_single_attempt``,
``no_repair_authored``, ``cohort_mismatch``, a ``defer_*`` probe verb).  It is
honest and healthy.  A MISSING value is an untyped null, which is not.  The two
are counted separately on purpose -- collapsing them is how the original defect
stayed invisible.

The triage section is the §8 hard-assertion target.  ``tier_one_basis`` records
which arm of the §2.1 AND gate committed a tier-one route.  ``causal_authority``
is expected to be ~absent until a validator-owned support channel exists (a
single-attempt receipt can never promote), so the metric that matters is that
the LEGACY arm survived: ``tier_one_without_basis`` must be 0 and
``tier_one_events`` must be non-zero wherever tier one used to fire.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from learnloop.db.repositories import Repository
from learnloop.services.causal_attribution import (
    APPROVED_SUPPORT_AUTHORITIES,
    OPEN_SET_CAUSE_ID,
)
from learnloop.services.causal_probe_coherence import (
    BLIND_INPUT_CONTRACT_VERSION,
    bundle_feature_row_report,
)

CAUSAL_HEALTH_VERSION = "causal_health_v1"

#: Below this many rows a channel cannot be called empty or saturated.
DEFAULT_MIN_ROWS = 5

CHANNELS = (
    "causal_support",
    "repair_mapping",
    "bundle_features",
    "discrimination_outcomes",
    "probe_decisions",
    "action_changing_outcomes",
    "diagnosis_support_updates",
    "discriminating_observations",
)

TAILS = ("empty", "saturated", "mixed", "insufficient")


@dataclass(frozen=True)
class ChannelHealth:
    """Fill / abstention counts for one causal channel."""

    channel: str
    total: int = 0
    filled: int = 0
    abstained: int = 0

    @property
    def missing(self) -> int:
        return max(0, self.total - self.filled - self.abstained)

    @property
    def fill_rate(self) -> float:
        return self.filled / self.total if self.total else 0.0

    @property
    def abstention_rate(self) -> float:
        return self.abstained / self.total if self.total else 0.0

    def tail(self, min_rows: int) -> str:
        if self.total < min_rows:
            return "insufficient"
        if self.filled == 0 and self.abstained == 0:
            return "empty"
        if self.filled == self.total:
            return "saturated"
        return "mixed"

    def as_dict(self, min_rows: int = DEFAULT_MIN_ROWS) -> dict[str, Any]:
        return {
            "channel": self.channel,
            "total": self.total,
            "filled": self.filled,
            "abstained": self.abstained,
            "missing": self.missing,
            "fill_rate": round(self.fill_rate, 6),
            "abstention_rate": round(self.abstention_rate, 6),
            "tail": self.tail(min_rows),
        }


class _Counter:
    def __init__(self, channel: str) -> None:
        self.channel = channel
        self.total = 0
        self.filled = 0
        self.abstained = 0

    def add(self, *, filled: bool, abstained: bool = False) -> None:
        self.total += 1
        if filled:
            self.filled += 1
        elif abstained:
            self.abstained += 1

    def health(self) -> ChannelHealth:
        return ChannelHealth(
            channel=self.channel,
            total=self.total,
            filled=self.filled,
            abstained=self.abstained,
        )


def _receipt_for(repository: Repository, attempt_id: str) -> Mapping[str, Any] | None:
    debug = repository.attempt_debug_payload(attempt_id) or {}
    attribution = debug.get("causal_attribution")
    if not isinstance(attribution, Mapping):
        return None
    receipt = attribution.get("diagnosis_receipt")
    return receipt if isinstance(receipt, Mapping) else None


def _is_open_set(row: Mapping[str, Any]) -> bool:
    return (
        row.get("open_set") is True
        or row.get("status") == "open_set"
        or str(row.get("hypothesis_id") or "") == OPEN_SET_CAUSE_ID
    )


def causal_lane_health(
    repository: Repository, *, min_rows: int = DEFAULT_MIN_ROWS
) -> dict[str, Any]:
    """Fill / abstention rates for every causal channel, plus the triage arms."""

    counters = {name: _Counter(name) for name in CHANNELS}
    attempts = repository.list_all_attempts()

    # -- causal support + repair mapping, per diagnosed attempt --------------
    authorities: dict[str, int] = {}
    for attempt in attempts:
        attempt_id = str(attempt["id"])
        receipt = _receipt_for(repository, attempt_id)
        if receipt is not None:
            authority = str(receipt.get("support_authority") or "unrecorded")
            authorities[authority] = authorities.get(authority, 0) + 1
            approved = authority in APPROVED_SUPPORT_AUTHORITIES
            scores = receipt.get("support_scores")
            scores = scores if isinstance(scores, Mapping) else {}
            for ref in receipt.get("hypotheses") or []:
                if not isinstance(ref, Mapping):
                    continue
                ref_id = str(ref.get("id") or ref.get("hypothesis_id") or "")
                if not ref_id or _is_open_set(ref):
                    continue
                counters["causal_support"].add(
                    filled=scores.get(ref_id) is not None,
                    # An honest "one attempt cannot own support" is an
                    # abstention, not a hole. A missing score under an APPROVED
                    # authority is a hole.
                    abstained=not approved,
                )
        for row in repository.causal_hypotheses_for_attempt(attempt_id):
            if _is_open_set(row):
                continue
            counters["repair_mapping"].add(
                filled=bool(row.get("repair_class_id")),
                abstained=bool(row.get("repair_class_unresolved_reason")),
            )

    # -- blind bundle feature rows ------------------------------------------
    for bundle in repository.causal_blind_prediction_bundles():
        if (
            bundle.get("blind_input_contract_version")
            != BLIND_INPUT_CONTRACT_VERSION
        ):
            counters["bundle_features"].add(filled=False, abstained=True)
            continue
        report = bundle_feature_row_report(bundle.get("predictions"))
        counters["bundle_features"].add(
            filled=report.usable, abstained=bool(report.skipped)
        )

    # -- discrimination outcomes, over every probe candidate ----------------
    factor_ids: list[str] = []
    for attempt in attempts:
        for factor in repository.unresolved_cause_factors_for_attempt(
            str(attempt["id"])
        ):
            factor_ids.append(str(factor["id"]))
    for factor_id in sorted(set(factor_ids)):
        for candidate in repository.causal_probe_candidates_for_factor(factor_id):
            discrimination = candidate.get("discrimination")
            discrimination = (
                discrimination if isinstance(discrimination, Mapping) else {}
            )
            counters["discrimination_outcomes"].add(
                filled=bool(discrimination.get("separable_pairs")),
                # `cohort_mismatch` / `unparsed_features` are typed refusals.
                abstained=bool(discrimination.get("reason"))
                and not discrimination.get("separable_pairs"),
            )

    # -- probe decisions + action-changing outcomes -------------------------
    decisions: dict[str, int] = {}
    for receipt in repository.causal_probe_decision_receipts(limit=100000):
        verb = str(receipt.get("decision") or "unrecorded")
        decisions[verb] = decisions.get(verb, 0) + 1
        counters["probe_decisions"].add(
            filled=bool(receipt.get("repair_class_ids")),
            abstained=verb.startswith("defer_"),
        )
        inputs = receipt.get("inputs")
        inputs = inputs if isinstance(inputs, Mapping) else {}
        if not inputs.get("instrument_available"):
            # No instrument means no action-change question was asked at all.
            continue
        counters["action_changing_outcomes"].add(
            filled=float(
                inputs.get("probability_information_changes_repair") or 0.0
            )
            > 0.0,
            abstained=(
                str(
                    (inputs.get("evsi_provenance") or {}).get(
                        "probability_information_changes_repair"
                    )
                    or ""
                )
                == "heuristic_default"
            ),
        )

    # -- diagnosis support updates on cold verifications --------------------
    for attempt in attempts:
        verification = repository.causal_cold_verification_for_attempt(
            str(attempt["id"])
        )
        if verification is None:
            continue
        update = verification.get("diagnosis_support_update")
        update = update if isinstance(update, Mapping) else {}
        delta = float(update.get("delta") or 0.0)
        counters["diagnosis_support_updates"].add(
            filled=delta != 0.0,
            # Zero-with-a-reason is the §6.2 invariant working, not a hole.
            abstained=delta == 0.0 and bool(update.get("reason")),
        )

    # -- discriminating observations (the classification -> resolution edge) --
    #
    # `empty` here is the inert-lane signature this whole report exists to
    # name: probes served, answered, classified, and nothing recorded.
    # `saturated` is the opposite tail and just as suspect -- an edge that
    # ADMITS every verdict is not judging them, and the outcomes that must
    # resolve nothing (`all_bundles_matched`, an unmeasured feature space) would
    # be silently closing factors.
    observation_outcomes: dict[str, int] = {}
    observation_sensors: dict[str, int] = {}
    for observation in repository.causal_discriminating_observations(
        probe_channel_only=True
    ):
        outcome = str(observation.get("outcome") or "unrecorded")
        observation_outcomes[outcome] = observation_outcomes.get(outcome, 0) + 1
        sensor = str(observation.get("feature_source") or "unrecorded")
        observation_sensors[sensor] = observation_sensors.get(sensor, 0) + 1
        counters["discriminating_observations"].add(
            filled=bool(observation.get("admitted")),
            # A typed refusal to admit is the edge working, not a hole.
            abstained=not observation.get("admitted")
            and bool(observation.get("admission_reason")),
        )

    return {
        "version": CAUSAL_HEALTH_VERSION,
        "min_rows": min_rows,
        "attempts": len(attempts),
        "channels": [
            counters[name].health().as_dict(min_rows) for name in CHANNELS
        ],
        "support_authorities": dict(sorted(authorities.items())),
        "probe_decisions_by_verb": dict(sorted(decisions.items())),
        "observation_outcomes": dict(sorted(observation_outcomes.items())),
        "observation_feature_sources": dict(sorted(observation_sensors.items())),
        "triage": triage_tier_one_health(repository),
    }


def triage_tier_one_health(repository: Repository) -> dict[str, Any]:
    """Which arm of the §2.1 gate committed each tier-one route.

    ``tier_one_without_basis > 0`` means a tier-one route fired that cannot say
    why -- the §8 metric's failure mode.  ``tier_one_events == 0`` on a vault
    that used to route tier one means the causal channel silently disabled the
    legacy arm, which is the original defect.
    """

    by_basis: dict[str, int] = {}
    tier_one = 0
    tier_two = 0
    for run in repository.golden_path_runs_all():
        for event in repository.failure_triage_events_for(str(run["id"])):
            if str(event.get("tier") or "") == "two":
                tier_two += 1
                continue
            if str(event.get("tier") or "") != "one":
                continue
            tier_one += 1
            try:
                payload = json.loads(event.get("inputs_snapshot_json") or "{}")
            except (TypeError, ValueError):
                payload = {}
            decision = payload.get("triage_decision")
            decision = decision if isinstance(decision, Mapping) else {}
            basis = decision.get("tier_one_basis")
            key = str(basis) if basis else "none"
            by_basis[key] = by_basis.get(key, 0) + 1
    return {
        "tier_one_events": tier_one,
        "tier_two_events": tier_two,
        "tier_one_by_basis": dict(sorted(by_basis.items())),
        "tier_one_without_basis": by_basis.get("none", 0),
    }


__all__ = [
    "CAUSAL_HEALTH_VERSION",
    "CHANNELS",
    "ChannelHealth",
    "DEFAULT_MIN_ROWS",
    "TAILS",
    "causal_lane_health",
    "triage_tier_one_health",
]
