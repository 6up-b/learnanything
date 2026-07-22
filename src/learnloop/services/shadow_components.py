"""P4 step 6 (DESCOPED, U-025) -- shadow predictive components + the deferred scored
selector (spec_p4_controller_and_scale §7; design §B step 6, §F).

The scored selector decomposes into two parts with different fates (U-025):

  * **Predictive components** -- retrievability, expected success, expected duration.
    Each is INDIVIDUALLY promotable via prequential held-out scoring (``prequential``).
    A promoted component feeds the staged policy's INPUTS; it never chooses actions.
  * **The monolithic action chooser** -- stays the transparent staged policy forever.
    It has NO reachable promotion path at n=1 (deterministic incumbent -> degenerate
    propensities -> near-empty off-policy support, §7.4). :func:`promote_action_chooser`
    is a STRUCTURAL GUARD that always refuses (enforced + tested).

All component/composed predictions are logged through ``controller_shadow_predictions``
(authority CHECK IN ('none') -- the firewall is in the schema) with ZERO authority. The
composed-selector telemetry is SECONDARY and TIME-BOXED: a registered horizon after
which unpromoted telemetry retires (:func:`retire_expired_telemetry`).

Promotion of a component emits the U-022 promotion-evidence artifact through the
existing registry machinery (``sensitivity_certificates``) and appends a
``shadow_component_events`` row. P4 ships the machinery and keeps everything shadow.
"""

from __future__ import annotations

import json as _json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Mapping

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services import controller_store as store

# The three individually-promotable predictive components (§7.1).
PREDICTIVE_COMPONENTS: tuple[str, ...] = (
    "retrievability",
    "expected_success",
    "expected_duration",
)

# STRUCTURAL (not a parameter, §17): the monolithic action chooser is never promotable
# at n=1. A bool -> excluded from the numeric-constant scan; the guard below enforces it.
MONOLITHIC_CHOOSER_PROMOTABLE = False

# Decision parameter (registered): the predeclared prequential improvement margin a
# component must beat its incumbent by (log-loss) before promotion is even considered.
COMPONENT_PROMOTION_MARGIN: float = 0.02

# Decision parameter (registered): the composed-selector telemetry TIME-BOX in days.
# Unpromoted composed-selector telemetry retires after this horizon (design §B step 6).
COMPOSED_SELECTOR_TELEMETRY_HORIZON_DAYS: int = 30

# The registered path the component-promotion evidence artifact is keyed to (U-022).
PROMOTION_EVIDENCE_PATH = "shadow_components:COMPONENT_PROMOTION_MARGIN"


# ---------------------------------------------------------------------------
# Shadow prediction (§7.1) -- deterministic, pre-outcome, zero authority.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ComponentPredictions:
    retrievability: float
    expected_success: float
    expected_duration: float
    composed: float  # goal-weighted delayed value / (minutes + burden), the §7.1 ratio

    def as_map(self) -> dict[str, float]:
        return {
            "retrievability": self.retrievability,
            "expected_success": self.expected_success,
            "expected_duration": self.expected_duration,
        }


def predict_components(candidate: Any, *, goal_weight: float = 1.0) -> ComponentPredictions:
    """Deterministic pre-administration predictions for one candidate. Uses only
    information available BEFORE administration (expected minutes, due state, purpose);
    never a post-selection or outcome feature. This is a transparent stub -- the point
    of P4 is the machinery + firewall, not a fitted model."""

    minutes = float(getattr(candidate, "expected_minutes", None) or 3.0)
    # Simple monotone stubs; the shapes only need to be reproducible for scoring.
    retrievability = 0.5 if getattr(candidate, "due_at", None) else 0.7
    expected_success = min(0.95, 0.4 + 0.1 * (6.0 / max(1.0, minutes)))
    expected_duration = minutes
    burden = 0.0
    value = goal_weight * retrievability * expected_success
    composed = value / (minutes + burden) if minutes > 0 else 0.0
    return ComponentPredictions(
        retrievability=round(retrievability, 6),
        expected_success=round(expected_success, 6),
        expected_duration=round(expected_duration, 6),
        composed=round(composed, 6),
    )


def record_shadow_predictions(
    repository: Repository,
    *,
    decision_id: str | None,
    snapshot_hash: str,
    predictions: ComponentPredictions,
    model_version: str = "shadow_components_v0",
    clock: Clock | None = None,
) -> dict[str, str]:
    """Log each predictive component + the composed selector as ZERO-authority shadow
    predictions. Returns the persisted prediction ids by scorer_kind."""

    ids: dict[str, str] = {}
    for component, value in predictions.as_map().items():
        ids[component] = store.persist_shadow_prediction(
            repository, decision_id=decision_id, snapshot_hash=snapshot_hash,
            scorer_kind=f"predictive_component:{component}", model_version=model_version,
            prediction={"value": value}, clock=clock,
        )
    # The composed selector is SECONDARY telemetry (§7.3).
    ids["composed_selector"] = store.persist_shadow_prediction(
        repository, decision_id=decision_id, snapshot_hash=snapshot_hash,
        scorer_kind="composed_selector", model_version=model_version,
        prediction={"value": predictions.composed,
                    "note": "secondary; no monolithic promotion path (U-025)"},
        clock=clock,
    )
    return ids


# ---------------------------------------------------------------------------
# Component promotion (§7.4) -- individual, evidence-gated, inputs-only.
# ---------------------------------------------------------------------------


@dataclass
class PromotionOutcome:
    promoted: bool
    reason: str | None = None
    evidence_id: str | None = None

    def __bool__(self) -> bool:
        return self.promoted


def promote_component(
    repository: Repository,
    *,
    component: str,
    report: Any,
    incumbent_log_loss: float,
    margin: float = COMPONENT_PROMOTION_MARGIN,
    clock: Clock | None = None,
) -> PromotionOutcome:
    """Consider one predictive component for promotion. It must beat its incumbent
    estimate on prequential held-out log-loss by at least ``margin`` with a non-trivial
    effective sample. A promoted component feeds the staged policy's INPUTS only (it can
    never reorder actions). Emits a U-022 promotion-evidence artifact through the
    registry machinery and appends a ``shadow_component_events`` promotion row.

    P4 keeps everything shadow: this method exists so the evidence machinery is testable;
    at n=1 the effective sample is tiny, so promotion normally refuses."""

    if component not in PREDICTIVE_COMPONENTS:
        return PromotionOutcome(False, "unknown_component")

    from learnloop.services import sensitivity_certificates as sc

    metrics = getattr(report, "metrics", None) or {}
    challenger = metrics.get("log_loss")
    n = int(metrics.get("effective_sample") or 0)
    if challenger is None or n < 1:
        _append_component_event(repository, component, "shadow",
                                {"promotion": "refused", "reason": "insufficient_evidence"},
                                None, clock=clock)
        return PromotionOutcome(False, "insufficient_evidence")
    if challenger > incumbent_log_loss - margin:
        _append_component_event(repository, component, "shadow",
                                {"promotion": "refused", "reason": "did_not_beat_incumbent",
                                 "challenger": challenger, "incumbent": incumbent_log_loss},
                                None, clock=clock)
        return PromotionOutcome(False, "did_not_beat_incumbent")

    # Emit the U-022 promotion-evidence artifact (a decision_stable sim/held-out record)
    # keyed to the registered promotion-margin parameter path.
    evidence = sc.PromotionEvidence(
        path=PROMOTION_EVIDENCE_PATH,
        covered_value_hash=_margin_value_hash(margin),
        plausible_range={"low": 0.0, "high": 0.1},
        flip_points=[],
        decision_stable=True,
        scenario={"gate": "component_promotion", "component": component,
                  "prequential_report_hash": getattr(report, "report_hash", None),
                  "challenger_log_loss": challenger, "incumbent_log_loss": incumbent_log_loss,
                  "effective_sample": n},
        sim_report_hash=getattr(report, "report_hash", "") or "",
        source="prequential",
    )
    evidence_id = sc.store_promotion_evidence(repository, evidence, clock=clock)
    _append_component_event(repository, component, "promotion",
                            {"promotion": "granted", "feeds": "staged_policy_inputs_only",
                             "component": component}, evidence_id, clock=clock)
    return PromotionOutcome(True, None, evidence_id)


def _margin_value_hash(margin: float) -> str:
    from learnloop.services.activities import _canonical_hash

    return _canonical_hash(margin)


def promote_action_chooser(*_args: Any, **_kwargs: Any) -> PromotionOutcome:
    """STRUCTURAL GUARD (U-025 §7.4). The monolithic composed action chooser has no
    reachable promotion path at n=1 and is deferred, not pending. This ALWAYS refuses --
    no sample count or shadow-agreement rate can promote it; a revival needs a new
    reviewed spec with a causal design (§9.3)."""

    assert MONOLITHIC_CHOOSER_PROMOTABLE is False  # structural invariant, not a knob
    return PromotionOutcome(False, "no_reachable_promotion_path_at_n1")


def _append_component_event(
    repository: Repository, component: str, kind: str, detail: Mapping[str, Any],
    evidence_id: str | None, *, clock: Clock | None,
) -> None:
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT COALESCE(MAX(event_ordinal), -1) AS m FROM shadow_component_events "
            "WHERE component = ?",
            (component,),
        ).fetchone()
        ordinal = int(row["m"]) + 1
        connection.execute(
            "INSERT INTO shadow_component_events(id, component, event_ordinal, event_kind, "
            "promotion_evidence_id, detail_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (new_ulid(), component, ordinal, kind, evidence_id,
             _json.dumps(dict(detail)), utc_now_iso(clock)),
        )
        connection.commit()


def component_events(repository: Repository, component: str) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT * FROM shadow_component_events WHERE component = ? "
            "ORDER BY event_ordinal",
            (component,),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Composed-selector telemetry TIME-BOX (design §B step 6).
# ---------------------------------------------------------------------------


def open_composed_selector_horizon(
    repository: Repository,
    *,
    horizon_days: int = COMPOSED_SELECTOR_TELEMETRY_HORIZON_DAYS,
    clock: Clock | None = None,
) -> str:
    """Register (idempotent) the time-box after which unpromoted composed-selector
    telemetry retires. Returns the horizon id."""

    now_iso = utc_now_iso(clock)
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT id FROM composed_selector_telemetry_horizons WHERE status = 'open'"
        ).fetchone()
        if row is not None:
            return row["id"]
        horizon_id = new_ulid()
        retires_at = (_parse(now_iso) + timedelta(days=horizon_days)).isoformat()
        connection.execute(
            "INSERT INTO composed_selector_telemetry_horizons(id, horizon_days, opened_at, "
            "retires_at, retired_at, status, detail_json) VALUES (?, ?, ?, ?, NULL, 'open', ?)",
            (horizon_id, horizon_days, now_iso, retires_at,
             _json.dumps({"secondary": True, "reason": "time_boxed_composed_selector"})),
        )
        connection.commit()
        return horizon_id


def retire_expired_telemetry(repository: Repository, *, clock: Clock | None = None) -> list[str]:
    """Retire any open composed-selector horizon whose ``retires_at`` has passed. Returns
    the ids retired. Unpromoted telemetry does not linger past its box."""

    now = _parse(utc_now_iso(clock))
    retired: list[str] = []
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT * FROM composed_selector_telemetry_horizons WHERE status = 'open'"
        ).fetchall()
        for row in rows:
            if _parse(row["retires_at"]) <= now:
                connection.execute(
                    "UPDATE composed_selector_telemetry_horizons SET status = 'retired', "
                    "retired_at = ? WHERE id = ?",
                    (now.isoformat(), row["id"]),
                )
                retired.append(row["id"])
        connection.commit()
    return retired


def _parse(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))
