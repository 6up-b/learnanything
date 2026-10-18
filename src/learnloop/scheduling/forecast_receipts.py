"""Saved forecasts: one receipt family for every expectation a decision states.

EVSI calibration Part B (:mod:`learnloop.scheduling.voi_forecasts`) records the
forecast each value-of-information decision runs on. This module generalizes
that machinery to any forecast a decision makes about an outcome it cannot yet
know, so diagnosis quality is scored on what happened next (calibration, Brier,
log loss, reliability) instead of judged by retrospective explanation
(owner go-ahead 2026-10-15; docs/reviews/diagnosis-forecast-receipts.md).

One receipt shape (``forecast_receipts``, migration 206):

* **forecaster** and **forecaster_version**: who forecast, and the version of
  its code, priors and config;
* **scope**: what the forecast is about (:data:`SCOPES`);
* **inputs** with their hash and **inputs_as_of**, the newest state the
  forecaster read (never after the receipt);
* the **forecast payload**: the ``voi_forecasts`` body format
  (``emission_alphabet``, ``predicted_outcomes``, ``prior``, ``likelihood``)
  plus ``p`` for a binary event; every number the forecast used is listed in
  ``parameters`` with the Part B provenance vocabulary
  (:func:`learnloop.scheduling.voi_forecasts.parameter`);
* the **binding**: the exact receipt chain the resolver may follow
  (:data:`BINDING_KINDS`), or ``none`` with a ``censor_reason`` when no exact
  binding exists (right-censored at birth, never guessed: the EVSI calibration
  F3/F6 rule);
* the **resolution**: derived at read time from the ledgers
  (``learnloop diagnosis calibration``), never written here.

``voi_forecasts`` rows are the same family read through an adapter (kind
``check_outcome``, forecaster = the decision site, binding = the site's own
receipt chain), so the report scores the three kinds side by side. Adaptive
difficulty AD1's ``item_forecasts`` (spec_adaptive_difficulty_v1 §8.1) is this
family with kind ``item_unassisted_success``, scope ``presentation`` (binding
``plan_presentation`` / ``probe_presentation``) or ``item``
(``item_content_hash``), ``p`` the forecast, and the outside forecasters'
``status`` (``failed`` / ``refused_spend``) and ``received_at``.

Receipts are written by :func:`record_receipts` INSIDE the deciding
transaction (a savepoint of it), so a decision and its receipts commit
together and a failed receipt rolls back alone: logging never breaks a
decision. Nothing serving, scoring or scheduling reads them, and replay never
does (RECEIPT). Kill switch: ``diagnosis.forecast_receipts``.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.db.stores import forecast_receipts as store

logger = logging.getLogger(__name__)

#: The receipt shape's version (bumped when a field's meaning changes).
RECEIPT_SHAPE_VERSION = "forecast_receipt_v1"

#: What a receipt forecasts. AD1 adds ``item_unassisted_success``; the report
#: reads ``voi_forecasts`` rows as ``check_outcome``.
DIAGNOSIS_NEXT_OBSERVATION = "diagnosis_next_observation"
REPAIR_COLD_OUTCOME = "repair_cold_outcome"
CHECK_OUTCOME = "check_outcome"
#: Adaptive difficulty AD1 (spec_adaptive_difficulty_v1 §8.1): the forecast of
#: unassisted success (§5.3's event) on one presentation, or on an item
#: revision's first presentation for an item-only forecaster. This family is
#: the spec's ``item_forecasts`` (no table of its own).
ITEM_UNASSISTED_SUCCESS = "item_unassisted_success"
FORECAST_KINDS = (DIAGNOSIS_NEXT_OBSERVATION, REPAIR_COLD_OUTCOME, ITEM_UNASSISTED_SUCCESS)

SCOPES = ("next_observation", "followup_task", "presentation", "item")

#: The exact chains a resolver may follow; ``none`` is censored at birth.
PRESENTED_ATTEMPT_ON_FACET = "presented_attempt_on_facet"
FOLLOWUP_TASK = "followup_task"
#: AD1's item-scoped forecast: scored against the first bound presentation of
#: the revision it names (``item_content_hash``).
FIRST_PRESENTATION = "first_presentation"
NO_BINDING = "none"
BINDING_KINDS = (PRESENTED_ATTEMPT_ON_FACET, FOLLOWUP_TASK, "plan_presentation", "probe_presentation",
                 FIRST_PRESENTATION, NO_BINDING)

#: ``serve`` (AD1): a presentation's forecasts, in-process in the serve
#: transaction or from an outside forecaster after it; ``item_prepare`` (AD1):
#: an item-only forecast made when the revision is prepared for the pool.
DECISION_KINDS = ("diagnosis", "cold_retry_schedule", "serve", "item_prepare")


@dataclass(frozen=True)
class ForecastReceipt:
    """One forecast, ready to append (the store fills its id)."""

    receipt_key: str
    kind: str
    forecaster: str
    forecaster_version: str
    scope: str
    decision_kind: str
    binding_kind: str
    event: str
    forecast: Mapping[str, Any]
    inputs: Mapping[str, Any]
    parameters: Sequence[Mapping[str, Any]]
    versions: Mapping[str, Any] = field(default_factory=dict)
    inputs_as_of: str | None = None
    p: float | None = None
    columns: Mapping[str, Any] = field(default_factory=dict)


def valid_for_serve(receipt: Mapping[str, Any], served_at: str | None) -> bool:
    """AD1's validity rule (spec_adaptive_difficulty_v1 §8.1): a forecast is
    valid for a presentation iff the inputs it read are no later than the
    serve (``inputs_as_of <= served_at``), whenever it arrived. A late outside
    forecast is still a true forecast for scoring; whether it could also
    inform the serve is the separate frozen-inputs rule (it must have been
    received before the serve). Unparseable times are invalid."""

    as_of = parse_utc(str(receipt.get("inputs_as_of") or "")) if receipt.get("inputs_as_of") else None
    served = parse_utc(str(served_at)) if served_at else None
    return as_of is not None and served is not None and as_of <= served


def receipts_enabled(vault: Any) -> bool:
    """The ``diagnosis.forecast_receipts`` kill switch (on without a vault config)."""

    config = getattr(getattr(vault, "config", None), "diagnosis", None)
    return bool(getattr(config, "forecast_receipts", True)) if config is not None else True


def inputs_digest(inputs: Mapping[str, Any]) -> str:
    canonical = json.dumps(inputs, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def categorical_body(
    likelihood: Mapping[str, Mapping[str, float]],
    prior: Mapping[str, float],
    *,
    alphabet: Sequence[str],
) -> dict[str, Any]:
    """The Part B body of a categorical forecast over ``alphabet``.

    ``predicted_outcomes`` is the prior-weighted mixture of the per-hypothesis
    likelihoods (each normalized over the alphabet), so the payload alone
    reproduces the prediction.
    """

    weights = {h: max(float(w), 0.0) for h, w in prior.items() if h in likelihood}
    total = sum(weights.values())
    if total <= 0:
        raise ValueError("a forecast needs a positive prior")
    weights = {h: w / total for h, w in weights.items()}
    rows: dict[str, dict[str, float]] = {}
    for h in sorted(weights):
        raw = {e: max(float(likelihood[h].get(e, 0.0)), 0.0) for e in alphabet}
        mass = sum(raw.values())
        if mass <= 0:
            raise ValueError(f"hypothesis {h!r} predicts nothing in the alphabet")
        rows[h] = {e: raw[e] / mass for e in alphabet}
    predicted = {e: sum(weights[h] * rows[h][e] for h in rows) for e in alphabet}
    return {
        "emission_alphabet": list(alphabet),
        "predicted_outcomes": {e: round(p, 8) for e, p in predicted.items()},
        "prior": {h: round(w, 8) for h, w in sorted(weights.items())},
        "likelihood": {h: {e: round(p, 8) for e, p in row.items()} for h, row in rows.items()},
    }


def clamped_as_of(value: str | None, created_at: str) -> str:
    """``inputs_as_of`` in the receipt's own format, never after the receipt."""

    parsed = parse_utc(value) if value else None
    created = parse_utc(created_at)
    if parsed is None or created is None or parsed > created:
        return created_at
    return parsed.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _validated(receipt: ForecastReceipt) -> None:
    if receipt.kind not in FORECAST_KINDS:
        raise ValueError(f"unknown forecast kind {receipt.kind!r}")
    if receipt.scope not in SCOPES:
        raise ValueError(f"unknown forecast scope {receipt.scope!r}")
    if receipt.binding_kind not in BINDING_KINDS:
        raise ValueError(f"unknown binding {receipt.binding_kind!r}")
    if receipt.decision_kind not in DECISION_KINDS:
        raise ValueError(f"unknown decision kind {receipt.decision_kind!r}")
    censored = receipt.columns.get("censor_reason")
    if (receipt.binding_kind == NO_BINDING) != bool(censored):
        raise ValueError("a receipt is censored at birth exactly when it has no binding")


def record_receipts(
    repository: Repository | None,
    receipts: Sequence[ForecastReceipt],
    *,
    vault: Any = None,
    clock: Clock | None = None,
    created_at: str | None = None,
) -> list[str]:
    """Append ``receipts`` in the caller's transaction; never raises.

    Call it inside the deciding ``repository.atomic()`` block: the writes are
    then a savepoint of the decision's own transaction, so the decision and
    its receipts commit together, and a failure here rolls back the receipts
    alone (logged) while the decision proceeds. Off with the kill switch, on a
    read-only repository, or on a database without the table, it writes
    nothing. ``created_at`` (default: now) is the issue time every receipt
    records. Returns the ids written (an existing receipt key writes nothing).
    """

    if repository is None or getattr(repository, "_read_only", False) or not receipts:
        return []
    if vault is not None and not receipts_enabled(vault):
        return []
    written: list[str] = []
    try:
        issued = created_at or utc_now_iso(clock)
        algorithm_version = None
        if vault is not None:
            algorithm_version = getattr(getattr(getattr(vault, "config", None), "algorithms", None),
                                        "algorithm_version", None)
        for receipt in receipts:
            _validated(receipt)
        with repository.atomic():
            connection = repository.connection()
            if not store.has_table(connection):
                return []
            for receipt in receipts:
                columns = dict(receipt.columns)
                columns.setdefault("algorithm_version", algorithm_version)
                if receipt.p is not None:
                    columns["p"] = float(receipt.p)
                receipt_id = store.insert_receipt(
                    connection,
                    receipt_key=receipt.receipt_key,
                    kind=receipt.kind,
                    forecaster=receipt.forecaster,
                    forecaster_version=receipt.forecaster_version,
                    scope=receipt.scope,
                    decision_kind=receipt.decision_kind,
                    binding_kind=receipt.binding_kind,
                    event=receipt.event,
                    forecast=receipt.forecast,
                    inputs=receipt.inputs,
                    inputs_hash=inputs_digest(receipt.inputs),
                    inputs_as_of=clamped_as_of(receipt.inputs_as_of, issued),
                    parameters=[dict(entry) for entry in receipt.parameters],
                    versions={"receipt_shape_version": RECEIPT_SHAPE_VERSION, **dict(receipt.versions)},
                    created_at=issued,
                    **columns,
                )
                if receipt_id is not None:
                    written.append(receipt_id)
    except Exception:  # noqa: BLE001 - a receipt must never break its decision
        logger.warning("forecast receipts not recorded (%s)", ", ".join(r.receipt_key for r in receipts),
                       exc_info=True)
        return []
    return written


__all__ = [
    "BINDING_KINDS",
    "CHECK_OUTCOME",
    "DECISION_KINDS",
    "DIAGNOSIS_NEXT_OBSERVATION",
    "FIRST_PRESENTATION",
    "FOLLOWUP_TASK",
    "FORECAST_KINDS",
    "ITEM_UNASSISTED_SUCCESS",
    "ForecastReceipt",
    "NO_BINDING",
    "PRESENTED_ATTEMPT_ON_FACET",
    "RECEIPT_SHAPE_VERSION",
    "REPAIR_COLD_OUTCOME",
    "SCOPES",
    "categorical_body",
    "clamped_as_of",
    "inputs_digest",
    "receipts_enabled",
    "record_receipts",
    "valid_for_serve",
]
