"""Frozen serve inputs (spec_adaptive_difficulty_v1 §7.5, §7.3; AD1, switch ``forecast_receipts``).

The features and signals an AD decision or update reads are fixed when the
item is served: one ``item_serve_inputs`` row per presentation of a
never-attempted item, in the serve transaction, holding

* the served revision's ``content_hash`` (also written to
  ``practice_item_snapshots``, INSERT OR IGNORE);
* the stamped tuple ``x_i``; per audited dimension the ``judgment_ledger`` id
  of the audit that had answered before the serve, or null; the resolved
  tuple AD reads (the audit where it answered, else the stamped value);
* the signal vector ``z_i`` (``z_llm``, ``z_panel``, ``z_v1``, ``z_origin``),
  each with its value, availability, receipt id and receipt time, and the
  ``z_v1`` recalibration (version, intercept, the past items it was fitted on);
* ``pre_exposed`` (§5.3: the reveal sum before the serve already reaches the
  auto-prime threshold) and ``ad_feature_resolution_v1``.

A signal or audit that arrives after the serve is used only by later
decisions: this row is never rewritten (append-only by trigger). An
``llm_v1:item`` receipt informs the serve only if it existed (was received)
when the serve wrote this row (G-AD1-9). Replay reads the row; it never
re-reads the item (G-AD1-8).
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from learnloop.clock import parse_utc
from learnloop.db.stores import ad_receipts as store

from learnloop.adaptive_difficulty.feature_audit import DIMENSIONS, canonical_audits, item_revision
from learnloop.adaptive_difficulty.switches import LLM_V1

RESOLUTION_VERSION = "ad_feature_resolution_v1"
#: z_v1's recalibration: field's logit-intercept MAP fit with an N(0, 1)
#: prior (``field.probability_arms.fit_intercept``), on past items only.
Z_V1_RECALIBRATION = "z_v1_logit_intercept_map_n01_v1"
LLM_ESTIMATE = "llm_estimate"
SOLVER_PANEL = "solver_panel"
_SUCCESS = 0.8
_CLIP = (0.001, 0.999)


def _logit(p: float) -> float:
    p = min(max(float(p), _CLIP[0]), _CLIP[1])
    return math.log(p / (1.0 - p))


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-700.0, min(700.0, x))))


def _before(value: Any, served_at: str) -> bool:
    stamp = parse_utc(str(value)) if value else None
    served = parse_utc(served_at)
    return stamp is not None and served is not None and stamp <= served


def never_attempted(connection: Any, practice_item_id: str, served_at: str, *, view: Any) -> bool:
    """No attempt of any kind on the item before (or at) the serve (read through the operation's
    material view: the served item is visible, or nothing reaches here)."""

    for row in view.attempts(connection):
        if str(row.get("practice_item_id")) == str(practice_item_id) and _before(row.get("created_at"), served_at):
            return False
    return True


def pre_exposed(repository: Any, item: Any, served_at: str, *, view: Any, connection: Any = None) -> bool:
    """§5.3: the item's reveal sum before ``served_at`` already reaches the auto-prime threshold.

    Read through the operation's material view (Codex verify F20, fix round 11): the reveals are
    the view's (a reveal belonging to an answer given to a held-out revision is not one) and the
    "last attempt" that opens the window is the item's last visible attempt, so a withheld answer
    neither adds exposure nor resets it. The rule itself is the incumbent's
    (``serve_eligibility.submit_exposure``); the incumbent's own reader is unchanged."""

    from contextlib import closing

    from learnloop.serve_eligibility import EligibilityInputs, RevealRow, submit_exposure

    def read(conn: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        reveals = [row for row in view.reveals(conn)
                   if str(row.get("practice_item_id") or "") == str(item.id)
                   or str(row.get("learning_object_id") or "") == str(item.learning_object_id)]
        attempts = [row for row in view.attempts(conn)
                    if str(row.get("practice_item_id")) == str(item.id) and _before(row.get("created_at"), served_at)]
        return reveals, attempts

    if connection is not None:
        reveals, attempts = read(connection)
    else:
        from learnloop.db.connection import connect

        with closing(connect(repository.sqlite_path, read_only=True)) as conn:
            reveals, attempts = read(conn)
    last = None
    for row in attempts:  # oldest first: the last one at the latest stamp, as the repository's read
        if last is None or str(row["created_at"]) >= str(last["created_at"]):
            last = row
    # The incumbent's inputs record, built from the view's rows alone (``gather`` would read the
    # raw attempts and tasks; the exposure rule reads only the reveals and the last attempt).
    inputs = EligibilityInputs(practice_item_id=str(item.id), learning_object_id=item.learning_object_id,
                               at=served_at, reveals=tuple(RevealRow.from_row(row) for row in reveals),
                               last_attempt=(str(last["id"]), str(last["created_at"])) if last is not None else None,
                               tasks=(), window_until=served_at)
    return bool(submit_exposure(inputs).primed_by_ledger)


# -- signals --------------------------------------------------------------------------------


def _z_llm(item: Any) -> dict[str, Any]:
    if getattr(item, "difficulty_source", None) == LLM_ESTIMATE and getattr(item, "difficulty", None) is not None:
        # The existing map (learner.mastery.item_irt_params): b = 2.5 (2d - 1).
        return {"value": round(2.5 * (2.0 * float(item.difficulty) - 1.0), 8), "available": True,
                "receipt_id": None, "received_at": None, "source": "item.difficulty"}
    return {"value": None, "available": False, "why": "not_llm_estimate"}


def _smoothed(rate: Any) -> float | None:
    try:
        agree, total = int(rate[0]), int(rate[1])
    except (TypeError, ValueError, IndexError):
        return None
    if total <= 0:
        return None
    return (agree + 0.5) / (total + 1.0)


def _z_panel(connection: Any, item: Any, served_at: str) -> dict[str, Any]:
    if getattr(item, "difficulty_source", None) != SOLVER_PANEL:
        return {"value": None, "available": False, "why": "not_solver_panel"}
    if not store.has_table(connection, "pf_candidates"):
        return {"value": None, "available": False, "why": "no_panel_rates"}
    import json

    from learnloop.adaptive_difficulty.material_view import current_view

    found = current_view().rows(connection, "pf_candidates", "published_item_id = ? AND status = 'published'",
                                (str(item.id),), order="published_at DESC, id DESC")
    row = (found[0]["id"], found[0]["panel_json"], found[0]["published_at"]) if found else None
    if row is None:
        return {"value": None, "available": False, "why": "no_panel_rates"}
    if not _before(row[2], served_at):
        return {"value": None, "available": False, "why": "received_after_serve", "receipt_id": str(row[0])}
    try:
        panel = json.loads(row[1] or "{}")
    except (TypeError, ValueError):
        panel = {}
    parent, variant = _smoothed(panel.get("parent_rate")), _smoothed(panel.get("variant_rate"))
    if parent is None or variant is None:
        return {"value": None, "available": False, "why": "no_panel_rates", "receipt_id": str(row[0])}
    return {"value": round(_logit(parent) - _logit(variant), 8), "available": True, "receipt_id": str(row[0]),
            "received_at": str(row[2]), "source": "pf_candidates.panel_json"}


def _outcome_of_first_presentation(connection: Any, content_hash: str, served_at: str, *,
                                   attempts: Any) -> float | None:
    """§5.3's binary event on a revision's first bound plan presentation, if it
    completed before ``served_at``; None when there is none or it was pre-exposed.
    ``attempts``: the material view's visible attempts, by presentation id."""

    from learnloop.adaptive_difficulty.material_view import current_view

    rows = [(row["plan_presentation_id"], row["served_at"], row["pre_exposed"]) for row in current_view().rows(
        connection, "item_serve_inputs", "content_hash = ? AND plan_presentation_id IS NOT NULL", (content_hash,),
        order="served_at, id")]
    for presentation_id, presentation_served, exposed in rows:
        if not _before(presentation_served, served_at):
            return None
        attempt = attempts.get(str(presentation_id))
        if attempt is None:
            continue
        if exposed or not _before(attempt.get("created_at"), served_at) or attempt.get("correctness") is None:
            return None
        success = (float(attempt["correctness"]) >= _SUCCESS and int(attempt.get("hints_used") or 0) == 0
                   and not bool(attempt.get("primed")))
        return 1.0 if success else 0.0
    return None


def z_v1_recalibration(connection: Any, served_at: str, *, view: Any, exclude_hash: str | None = None
                       ) -> dict[str, Any]:
    """The logit intercept fitted on past items only: item-scoped ``llm_v1:item``
    receipts received before the serve whose revision's first presentation was
    answered before it. Its observations come through the operation's material view (Codex
    verify F24): a forecast or answer on an item or revision withheld now is never one, whatever
    the current target's protection."""

    from learnloop.field.probability_arms import fit_intercept

    first: dict[str, dict[str, Any]] = {}
    for row in view.attempts(connection):
        if row.get("plan_presentation_id"):
            first.setdefault(str(row["plan_presentation_id"]), row)
    logits: list[float] = []
    outcomes: list[float] = []
    for receipt in view.forecast_receipts(connection, kind="item_unassisted_success"):
        if receipt["scope"] != "item" or receipt["forecaster"] != LLM_V1 or receipt.get("status") != "ok":
            continue
        if receipt.get("p") is None or receipt.get("item_content_hash") in (None, exclude_hash):
            continue
        if not _before(receipt.get("received_at") or receipt.get("created_at"), served_at):
            continue
        outcome = _outcome_of_first_presentation(connection, str(receipt["item_content_hash"]), served_at,
                                                 attempts=first)
        if outcome is None:
            continue
        logits.append(_logit(float(receipt["p"])))
        outcomes.append(outcome)
    intercept = float(fit_intercept(logits, outcomes)) if logits else 0.0
    return {"version": Z_V1_RECALIBRATION, "intercept": round(intercept, 8), "n": len(logits)}


def _z_v1(connection: Any, content_hash: str, served_at: str, recalibration: Mapping[str, Any], *,
          view: Any) -> dict[str, Any]:
    receipts = [
        receipt for receipt in view.forecast_receipts(connection, kind="item_unassisted_success")
        if receipt["scope"] == "item" and receipt["forecaster"] == LLM_V1
        and receipt.get("item_content_hash") == content_hash
    ]
    usable = [receipt for receipt in receipts if receipt.get("status") == "ok" and receipt.get("p") is not None
              and _before(receipt.get("received_at") or receipt.get("created_at"), served_at)]
    if not usable:
        why = "not_received_before_serve" if receipts else "no_item_forecast"
        return {"value": None, "available": False, "why": why}
    receipt = usable[0]
    calibrated = _sigmoid(_logit(float(receipt["p"])) + float(recalibration.get("intercept") or 0.0))
    # The sign makes it a difficulty, like the other signals (§7.3).
    return {"value": round(-_logit(calibrated), 8), "available": True, "receipt_id": str(receipt["id"]),
            "received_at": receipt.get("received_at") or receipt.get("created_at"), "p": float(receipt["p"]),
            "p_recalibrated": round(calibrated, 8)}


def _z_origin(item: Any) -> dict[str, Any]:
    canonical = getattr(item, "canonical_exercise", None) is not None
    return {"value": 0.0 if canonical else 1.0, "available": True, "receipt_id": None, "received_at": None,
            "source": "canonical_exercise" if canonical else "generated"}


def signal_vector(connection: Any, item: Any, content_hash: str, served_at: str, *,
                  view: Any) -> tuple[dict[str, Any], str]:
    recalibration = z_v1_recalibration(connection, served_at, view=view, exclude_hash=content_hash)
    signals = {
        "z_llm": _z_llm(item),
        "z_panel": _z_panel(connection, item, served_at),
        "z_v1": {**_z_v1(connection, content_hash, served_at, recalibration, view=view),
                 "recalibration": recalibration},
        "z_origin": _z_origin(item),
    }
    return signals, str(recalibration["version"])


# -- features -------------------------------------------------------------------------------


def _audited_value(dimension: str, value: str) -> Any:
    return int(value) if dimension == "complexity" else value


def feature_inputs(connection: Any, item: Any, content_hash: str, served_at: str) -> dict[str, Any]:
    stamped = dict(item.task_features) if isinstance(getattr(item, "task_features", None), Mapping) else None
    audits = canonical_audits(connection, content_hash, as_of=served_at)
    audit_json = {
        dimension: ({"judgment_id": audits[dimension]["judgment_id"], "value": audits[dimension]["value"],
                     "judge": audits[dimension]["judge"]} if dimension in audits else None)
        for dimension in DIMENSIONS
    }
    resolved: dict[str, Any] | None = dict(stamped or {})
    for dimension, audit in audits.items():
        resolved[dimension] = _audited_value(dimension, audit["value"])
    if not resolved:
        resolved = None
    return {"stamped_features": stamped, "task_feature_schema": getattr(item, "task_feature_schema", None),
            "audit": audit_json, "resolved_features": resolved}


def build_row(repository: Any, connection: Any, item: Any, *, presentation_kind: str, presentation_id: str,
              served_at: str, created_at: str, view: Any) -> dict[str, Any]:
    content_hash, item_json = item_revision(item)
    store.insert_item_snapshot(connection, content_hash_value=content_hash, practice_item_id=str(item.id),
                               item_json=item_json, created_at=created_at)
    signals, recalibration = signal_vector(connection, item, content_hash, served_at, view=view)
    row: dict[str, Any] = {
        "receipt_key": f"{presentation_kind}:{presentation_id}",
        "presentation_kind": presentation_kind,
        f"{presentation_kind}_id": presentation_id,
        "practice_item_id": str(item.id),
        "learning_object_id": item.learning_object_id,
        "content_hash": content_hash,
        "served_at": served_at,
        "signals": signals,
        "z_v1_recalibration": recalibration,
        "pre_exposed": pre_exposed(repository, item, served_at, view=view, connection=connection),
        "resolution_version": RESOLUTION_VERSION,
        "loadings": None,
        "coupling_version": None,
        "created_at": created_at,
        **feature_inputs(connection, item, content_hash, served_at),
    }
    return row


__all__ = [
    "RESOLUTION_VERSION",
    "Z_V1_RECALIBRATION",
    "build_row",
    "feature_inputs",
    "never_attempted",
    "pre_exposed",
    "signal_vector",
    "z_v1_recalibration",
]
