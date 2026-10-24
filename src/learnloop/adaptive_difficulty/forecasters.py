"""The in-process forecasters (spec_adaptive_difficulty_v1 §8.1-8.2; AD1).

Written in the serve transaction, beside ``plan_presentations``, as kind
``item_unassisted_success`` receipts in the ``forecast_receipts`` family
(scope ``presentation``, binding ``plan_presentation``), with
``inputs_as_of`` no later than the serve:

* ``mastery_ekf``, the incumbent: the persisted per-LO 2PL posterior read
  through ``resolve_item_irt_params`` (placement's live adapter,
  :class:`learnloop.placement.predictor.LiveMasteryPredictor`).
* ``lo_general+composite``, the challenger (field §4.3): field's pure
  prequential EKF with every extension, fitted on the attempt rows completed
  no later than the serve (``field.outcomes.load_attempt_rows``), predicting
  the served item as a cold, unprimed first look.

No model call, nothing written beyond the receipt. A forecaster that cannot
compute (a vault below the field tables, an item without its LO) is skipped
and logged; the serve proceeds.
"""

from __future__ import annotations

from learnloop.adaptive_difficulty.logs import warn_failure
import hashlib
import json
import logging
from typing import Any

from learnloop.scheduling.forecast_receipts import ForecastReceipt, ITEM_UNASSISTED_SUCCESS
from learnloop.scheduling.voi_forecasts import parameter

from learnloop.adaptive_difficulty.switches import IN_PROCESS_FORECASTERS

LOG = logging.getLogger(__name__)

EVENT = "unassisted_success"
INCUMBENT = "mastery_ekf"
CHALLENGER = "lo_general+composite"
INCUMBENT_VERSION = "ad1-mastery-ekf-live-v1"
CHALLENGER_VERSION = "ad1-lo-general-composite-v1"


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def receipt_key(presentation_kind: str, presentation_id: str, forecaster: str) -> str:
    return f"{ITEM_UNASSISTED_SUCCESS}:{presentation_kind}:{presentation_id}:{forecaster}"


def _incumbent(vault: Any, repository: Any, item: Any, served_at: str) -> tuple[float, dict[str, Any], str]:
    from learnloop.placement.predictor import LiveMasteryPredictor

    states = repository.mastery_states()
    predictor = LiveMasteryPredictor(vault, repository, mastery_states=states, now_iso=served_at)
    prediction = predictor.predict_item(str(item.id))
    state = states.get(item.learning_object_id)
    inputs = {
        "practice_item_id": str(item.id),
        "learning_object_id": item.learning_object_id,
        "mastery_state": None if state is None else {
            "logit_mean": round(float(state.logit_mean), 8), "logit_variance": round(float(state.logit_variance), 8),
            "evidence_count": int(state.evidence_count or 0), "last_evidence_at": state.last_evidence_at,
        },
        "prediction_logit_variance": round(float(prediction.logit_variance), 8),
    }
    return float(prediction.p_success), inputs, str(predictor.version_hash)


def _features(vault: Any, item: Any, served_at: str) -> Any:
    from learnloop.field.types import ItemFeatures
    from learnloop.learner.mastery import resolve_item_irt_params

    llm_estimate = getattr(item, "difficulty_source", None) == "llm_estimate"
    # As the field replays history: an LLM-estimated difficulty is never a
    # point value (field §4.3), so it falls back to the default b.
    a, b = resolve_item_irt_params(None if llm_estimate else item, None, vault.config.mastery)
    subjects = vault.subjects_for_item(item)
    families = getattr(vault, "activity_families", {}) or {}
    family_id = getattr(item, "family_id", None)
    relation = getattr(item, "variant_relation", None)
    if family_id not in families:
        family_id, relation = None, None
    return ItemFeatures(
        item_id=str(item.id), lo_id=str(item.learning_object_id), observed_at=served_at,
        subject_id=(subjects[0] if subjects else "default"), a=float(a), b=float(b), primed=False, cold=True,
        capability=getattr(item, "capability", None), family_id=family_id, variant_relation=relation,
        difficulty_source=str(getattr(item, "difficulty_source", None) or "authored"),
        difficulty_variance=1.0 if llm_estimate else 0.0,
    )


def _challenger(vault: Any, connection: Any, item: Any, served_at: str, *,
                view: Any) -> tuple[float, dict[str, Any], str]:
    from learnloop.field.predictors import create_predictor

    # The history it rebuilds on comes through the serve's material view (Codex verify F24): an
    # answer on a withheld item never trains the challenger, whatever the served item is.
    rows = view.field_rows(connection, as_of=served_at)
    predictor = create_predictor(CHALLENGER, config=vault.config.mastery)
    predictor.rebuild(rows)
    features = _features(vault, item, served_at)
    prediction = predictor.predict_item(features)
    latest = max((row.features.observed_at for row in rows), default=None)
    inputs = {
        "practice_item_id": str(item.id),
        "learning_object_id": item.learning_object_id,
        "attempt_rows": len(rows),
        "latest_attempt_at": latest,
        "rows_digest": _digest([(row.attempt_id, row.outcome, row.effective_mass) for row in rows]),
        "features": {"subject_id": features.subject_id, "a": features.a, "b": features.b,
                     "capability": features.capability},
        "prediction_logit_variance": round(float(prediction.logit_variance), 8),
    }
    return float(prediction.p_success), inputs, str(predictor.version_hash)


def in_process_receipts(vault: Any, repository: Any, connection: Any, item: Any, *, presentation_kind: str,
                        presentation_id: str, served_at: str, view: Any) -> list[ForecastReceipt]:
    """The two in-process forecasts of one presentation (each skipped alone on failure)."""

    receipts: list[ForecastReceipt] = []
    for forecaster in IN_PROCESS_FORECASTERS:
        try:
            if forecaster == INCUMBENT:
                p, inputs, version_hash = _incumbent(vault, repository, item, served_at)
                version = INCUMBENT_VERSION
            else:
                p, inputs, version_hash = _challenger(vault, connection, item, served_at, view=view)
                version = CHALLENGER_VERSION
        except Exception:  # noqa: BLE001 - a forecaster that cannot compute is skipped, never the serve
            warn_failure(LOG, "AD1 in-process forecaster %s skipped for %s", forecaster, item.id)
            continue
        p = min(max(float(p), 0.0), 1.0)
        receipts.append(ForecastReceipt(
            receipt_key=receipt_key(presentation_kind, presentation_id, forecaster),
            kind=ITEM_UNASSISTED_SUCCESS,
            forecaster=forecaster,
            forecaster_version=f"{version}:{version_hash[:16]}",
            scope="presentation",
            decision_kind="serve",
            binding_kind=presentation_kind,
            event=EVENT,
            forecast={"p": round(p, 8), "event": EVENT, "p_categories": None},
            inputs=inputs,
            parameters=[parameter("forecaster_version_hash", version_hash, "structural", source="code+config")],
            versions={"forecaster": version, "forecaster_hash": version_hash},
            inputs_as_of=served_at,
            p=p,
            columns={
                "decision_ref": presentation_id,
                "practice_item_id": str(item.id),
                "learning_object_id": item.learning_object_id,
                f"{presentation_kind}_id": presentation_id,
            },
        ))
    return receipts


__all__ = ["CHALLENGER", "EVENT", "INCUMBENT", "in_process_receipts", "receipt_key"]
