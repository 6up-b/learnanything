"""RW2d's receipts: what the predecessor's derivation and rule would have decided.

The learner field's F3 asks a change to what is served to write receipts,
"including what the old rule would have done where that is cheap to
compute" (spec_reader_workbench_v1 §5.11, G41). RW2d's workbench signals can
only add blocking signals to an LO, so a decision they change is one the old
rule took on fewer blocking signals: re-running that rule on the
predecessor's blocking set (``placement.signals.blocking_with_predecessor``)
is cheap, and the receipt keeps both verdicts side by side. Pure builders;
the callers write in their own decision transaction
(``db.stores.field_signal_receipts``).
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
from typing import Any

from learnloop.field.workbench_signals import WORKBENCH_SIGNAL_VERSION
from learnloop.ids import new_ulid


def _side(blocking: Sequence[str], verdict: Mapping[str, Any]) -> dict[str, Any]:
    return {"blocking_signal_ids": list(blocking), **dict(verdict)}


def receipt_row(
    *,
    algorithm_version: str,
    decision_kind: str,
    decision_ref: str | None,
    learning_object_id: str,
    blocking: Sequence[str],
    predecessor_blocking: Sequence[str],
    verdict: Mapping[str, Any],
    predecessor_verdict: Mapping[str, Any],
    now_iso: str,
) -> dict[str, Any]:
    """One ``field_signal_receipts`` row; its key repeats only for the same
    decision, LO, workbench signal set and predecessor verdict."""

    signal_ids = sorted(set(blocking) - set(predecessor_blocking))
    digest = hashlib.sha256(json.dumps(
        {"signals": signal_ids, "predecessor": {k: predecessor_verdict.get(k) for k in ("verdict", "reason")}},
        sort_keys=True,
    ).encode("utf-8")).hexdigest()
    return {
        "id": new_ulid(),
        "receipt_key": f"{decision_kind}:{decision_ref or ''}:{learning_object_id}:{digest}",
        "decision_kind": decision_kind,
        "decision_ref": decision_ref,
        "learning_object_id": learning_object_id,
        "signal_ids_json": json.dumps(signal_ids),
        "predecessor_json": json.dumps(_side(predecessor_blocking, predecessor_verdict), sort_keys=True),
        "successor_json": json.dumps(_side(blocking, verdict), sort_keys=True),
        "signal_version": WORKBENCH_SIGNAL_VERSION,
        "algorithm_version": algorithm_version,
        "created_at": now_iso,
    }


def fast_track_side(verdict: Any) -> dict[str, Any]:
    """A ``FastTrackVerdict`` as a receipt side."""

    return {"verdict": "fires" if verdict.fires else "withheld", "reason": verdict.reason, "p": verdict.p}


__all__ = ["fast_track_side", "receipt_row"]
