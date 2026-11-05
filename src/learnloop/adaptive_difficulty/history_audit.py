"""Router objective RO2's owner-run audit, ``learnloop ad forecast-audit`` (spec_router_objective_v1 §6.4).

Two modes, both on the frozen inputs the serves kept (``item_forecast_payloads``, inside
``router.payload_retention_days`` and at the current protection epoch; an expired one is never sent):

* ``permuted`` (paid): each frozen H3 card is sent again with its ``history`` replaced by the history
  of another presentation of a similar level, its nearest neighbour by the incumbent's forecast
  (``mastery_ekf``'s ``p``) among presentations of another item served no later (so no permuted card
  carries an event after its own serve). Its receipts are forecaster ``llm_history_v1:H3_permuted``
  on the same presentation, scored by the same report beside the real H3 (permuted against real
  history). Sent through the same paid path as the background job (the held-out check before each
  request and record, the spend cap, the plan's pauses; a skip censored with its reason).
* ``prior-sweep`` (free; no model call): the calibration slopes refitted with the seeded prior's
  spread scaled by each of :data:`PRIOR_SCALES` (report T8), so the owner sees how much the prior,
  not the data, decides a slope.

The dry run (the default; ``--run`` sends) prints what would be sent, how many calls, their estimated
tokens and the route's billing, and calls and writes nothing.
"""

from __future__ import annotations

from learnloop.adaptive_difficulty.operation import entry

import json
from collections.abc import Mapping
from contextlib import closing
from typing import Any

from learnloop.ai.execution import content_key
from learnloop.clock import Clock
from learnloop.db.connection import connect
from learnloop.db.stores import ad_receipts as store

from learnloop.adaptive_difficulty import history_forecast as HF
from learnloop.adaptive_difficulty.forecasters import INCUMBENT, receipt_key
from learnloop.adaptive_difficulty.outside import Clients, ForecastOutcome

PERMUTED = "H3_permuted"
#: ``keep``: the prior-strength sweep's grid (multiples of the seeded prior's sd): report T8's points.
PRIOR_SCALES = (0.25, 0.5, 1.0, 2.0, 4.0)
MODES = ("permuted", "prior-sweep")


def _decoded(row: Mapping[str, Any]) -> dict[str, Any] | None:
    content = row.get("content")
    if content is None:
        try:
            content = json.loads(row.get("content_json") or "null")
        except (TypeError, ValueError):
            return None
    return content if isinstance(content, dict) else None


def _plan(connection: Any, view: Any, *, limit: int | None) -> list[dict[str, Any]]:
    """The permuted pairs: each frozen H3 card with a donor of a similar level served no later."""

    frozen = []
    for row in view.rows(connection, store.PAYLOADS, "owner_key LIKE ? AND kind = 'request'",
                         (f"{HF.FROZEN_PREFIX}%:{HF.ANCHOR}",), order="created_at, id"):
        content = _decoded(row)
        if not content or content.get("state_hash") != content_key(content.get("state")):
            continue
        pid = str(row["owner_key"])[len(HF.FROZEN_PREFIX):].rpartition(":")[0]
        incumbent = view.lookup(connection, "forecast_receipts", "receipt_key = ?",
                                (receipt_key("plan_presentation", pid, INCUMBENT),))[1]
        level = incumbent.get("p") if incumbent else None
        frozen.append({"plan_presentation_id": pid, "content": content, "level": level,
                       "served_at": str(content.get("inputs_as_of"))})
    pairs = []
    for target in frozen:
        if target["level"] is None:
            continue
        donors = [d for d in frozen if d["plan_presentation_id"] != target["plan_presentation_id"]
                  and d["level"] is not None and d["served_at"] <= target["served_at"]
                  and d["content"].get("practice_item_id") != target["content"].get("practice_item_id")]
        if not donors:
            continue
        donor = min(donors, key=lambda d: (abs(float(d["level"]) - float(target["level"])), d["plan_presentation_id"]))
        state = {**target["content"]["state"], "history": donor["content"]["state"].get("history", {}),
                 "permuted_from": "another presentation's history (forecast audit)"}
        content = {**target["content"], "state": state, "state_hash": content_key(state), "rung": PERMUTED}
        pairs.append({"plan_presentation_id": target["plan_presentation_id"],
                      "donor": donor["plan_presentation_id"], "content": content,
                      "levels": [target["level"], donor["level"]]})
        if limit is not None and len(pairs) >= limit:
            break
    return pairs


@entry(read_only=True)
def plan_audit(vault: Any, repository: Any, *, mode: str, limit: int | None = None) -> dict[str, Any]:
    """The dry run: what ``mode`` would send and what it would cost; no call, no write."""

    from learnloop.adaptive_difficulty.material_view import material_view
    from learnloop.practice_index.paid import plan_route

    if mode not in MODES:
        raise ValueError(f"mode is one of {', '.join(MODES)}")
    if mode == "prior-sweep":
        return {"status": "dry_run", "mode": mode, "model_calls": 0, "writes": 0, "scales": list(PRIOR_SCALES),
                "note": "free: the slopes are refitted on resolved receipts, no model call"}
    view = material_view(vault, repository)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        pairs = _plan(connection, view, limit=limit)
    # The route and the charge the run uses (Codex review F5): the route's own output budget reserved
    # on each call, and at most one retry at double it (``HF.call_tokens``, which the run's caps read).
    route = plan_route(vault, HF.LLM_ROUTE)
    charges = [HF.call_tokens(route, HF.prompt_for(pair["content"]["state"])) for pair in pairs]
    initial, worst = sum(c["initial"] for c in charges), sum(c["with_retry"] for c in charges)
    price = vault.config.adaptive_difficulty.price_per_million
    metered = route.billing != "subscription"

    def usd(tokens: int) -> float | None:
        if not metered:
            return 0.0
        return round(tokens / 1e6 * float(price), 4) if price is not None else None

    prompt_bytes = sum(len(HF.prompt_for(pair["content"]["state"]).encode("utf-8")) for pair in pairs)
    return {"status": "dry_run", "mode": mode, "model_calls": 0, "writes": 0, "calls": len(pairs),
            "output_tokens_per_call": route.output_tokens, "retries_per_call": 1,
            "estimated_tokens": initial, "estimated_tokens_with_retries": worst,
            # RO2 landing: what the estimate counts, so its size is not read as expected usage. It is the
            # charge the run's caps admit, an upper bound: each prompt's UTF-8 bytes (real tokens are
            # roughly a quarter to a third of them), the schema and framing, and the call's whole
            # reserved output budget, though an answer uses a few hundred tokens of it.
            "prompt_bytes": prompt_bytes, "reserved_output_tokens": route.output_tokens * len(pairs),
            "estimate_counts": ("an upper bound the spend caps reserve, not expected usage: each call's prompt "
                                "as UTF-8 bytes (real tokens are about a quarter to a third of that), the "
                                "answer schema and framing, and the whole reserved output budget "
                                "(output_tokens_per_call), of which an answer uses a few hundred tokens; "
                                "_with_retries adds one retry per call at double that budget"),
            "route": {"provider": route.provider, "model": route.model, "billing": route.billing},
            "estimated_usd": usd(initial), "estimated_usd_with_retries": usd(worst),
            "pairs": [{"plan_presentation_id": p["plan_presentation_id"], "donor": p["donor"], "levels": p["levels"],
                       "estimated_tokens": charges[index]["initial"],
                       "estimated_tokens_with_retry": charges[index]["with_retry"]}
                      for index, p in enumerate(pairs)]}


@entry(durable="it sends to a model: its claim, spend and receipts commit per unit")
def run_audit(vault: Any, repository: Any, *, mode: str, limit: int | None = None, clients: Clients | None = None,
              clock: Clock | None = None) -> dict[str, Any]:
    """The paid run (``permuted``) or the free sweep (``prior-sweep``)."""

    from learnloop.adaptive_difficulty.claims import LeaseLost, claimed, history_key
    from learnloop.adaptive_difficulty.material_view import material_view
    from learnloop.adaptive_difficulty.scoring import calibration_slopes
    from learnloop.adaptive_difficulty.sending import ProtectedContent, SendGuard, refusal_status

    if mode not in MODES:
        raise ValueError(f"mode is one of {', '.join(MODES)}")
    if mode == "prior-sweep":
        points = _version_points(vault, repository)
        return {"status": "ok", "mode": mode, "model_calls": 0, "writes": 0,
                "sweep": {str(scale): calibration_slopes(points, scale=scale) for scale in PRIOR_SCALES}}
    clients = clients or Clients()
    view = material_view(vault, repository)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        pairs = _plan(connection, view, limit=limit)
        presentations = {pid: view.presentation(connection, pid) for pid in {p["plan_presentation_id"] for p in pairs}}
    outcomes: list[ForecastOutcome] = []
    for pair in pairs:
        pid = pair["plan_presentation_id"]
        presentation = presentations.get(pid)
        if presentation is None:
            outcomes.append(ForecastOutcome(HF.forecaster_name(PERMUTED), "protected"))
            continue
        item_id = str(presentation["practice_item_id"])
        try:
            with claimed(repository, f"{history_key(pid)}:permuted") as worker:
                if worker is None:
                    outcomes.append(ForecastOutcome(HF.forecaster_name(PERMUTED), "busy"))
                    continue
                with closing(connect(repository.sqlite_path, read_only=True)) as connection:
                    if HF._done(connection, pid, PERMUTED):
                        continue
                send = SendGuard(vault, repository, items=[view.item(item_id)], item_ids=[item_id],
                                 identities=[pair["content"]["protection_identities"]["target"]],
                                 epoch=pair["content"]["protection_epoch"])
                try:
                    send.check("the forecast audit")
                except ProtectedContent as exc:
                    outcomes.append(ForecastOutcome(HF.forecaster_name(PERMUTED), refusal_status(exc)))
                    continue
                outcomes.append(HF._forecast_rung(vault, worker, PERMUTED, presentation, pair["content"],
                                                  {"propensity": 1.0}, clients=clients, clock=clock, send=send))
        except LeaseLost:
            outcomes.append(ForecastOutcome(HF.forecaster_name(PERMUTED), "stale"))
    return {"status": "ok", "mode": mode, "calls": sum(o.status in ("ok", "failed", "refused_spend") for o in outcomes),
            "outcomes": [o.as_dict() for o in outcomes]}


def _version_points(vault: Any, repository: Any) -> dict[str, list[tuple[float, float]]]:
    from learnloop.adaptive_difficulty.scoring import score_rows

    from learnloop.adaptive_difficulty.material_view import material_view

    view = material_view(vault, repository)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        receipts = {str(r["id"]): r for r in view.forecast_receipts(connection, kind="item_unassisted_success")
                    if str(r.get("forecaster", "")).startswith("llm_history_v1:")}
        points: dict[str, list[tuple[float, float]]] = {}
        for row in score_rows(connection, vault, repository):
            receipt = receipts.get(str(row.get("receipt_id")))
            if receipt is None or row.get("status") != "scored":
                continue
            versions = receipt.get("versions") or {}
            points.setdefault(f"{versions.get('model')}|{versions.get('prompt')}", []).append(
                (float(row["p"]), float(row["outcome"])))
    return points


__all__ = ["MODES", "PERMUTED", "PRIOR_SCALES", "plan_audit", "run_audit"]
