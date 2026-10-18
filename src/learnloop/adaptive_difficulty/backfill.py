"""AD1's owner-run backfills (spec_adaptive_difficulty_v1 §14 AD1, §7.2, §8.2, §5.11).

``learnloop ad backfill`` (``--dry-run`` first, on a backup copy):

* ``--audit``: the feature audit of every active item's current revision and
  of every other revision held in ``practice_item_snapshots`` (an answered or
  served revision), under ``adaptive_difficulty.daily_spend_cap_usd``;
* ``--llm-v1``: the one-time ``llm_v1:item`` forecast of the never-attempted
  active items that exist now;
* ``--reading``: the reading-opportunity sweep over the whole history (no
  model call).

A dry run opens the database read-only, calls nothing, writes nothing and
prints the plan through the spend framework (Codex review F9): per resolved
route its billing label (``estimated_only`` on the subscription, a metered
estimate otherwise), the input tokens and the output allowance of every
call (every permitted retry included, at its enlarged output allowance:
Codex re-review F13), the Decider at its listed input price, the LLM judge's fallback
exposure when the Decider is on (worst case: every revision falls back), a
refusal where a metered LLM route has no ``adaptive_difficulty.price_per_million``
(the real run would refuse each call before sending), and the worst-case
metered dollars against what is left of today's ``daily_spend_cap_usd``.
Protected revisions (held-out material, exam reservations) are never audited
or forecast (A8), each judged on its own source references (Codex review F1).
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from contextlib import closing
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.connection import connect

from learnloop.adaptive_difficulty.feature_audit import (
    DIMENSIONS,
    audit_revision,
    audit_state,
    canonical_audits,
    item_revision,
    question_for,
)
from learnloop.adaptive_difficulty.outside import Clients, forecast_item
from learnloop.adaptive_difficulty.protection import Protection, protection
from learnloop.adaptive_difficulty.reading import sweep
from learnloop.adaptive_difficulty.switches import (
    LLM_V1,
    feature_audit_enabled,
    outside_forecasters,
    receipts_enabled,
)


def _revisions(vault: Any, connection: Any, protected: Protection) -> tuple[list[tuple[Any, str]], int]:
    """``(item, content_hash)`` for every active item's current revision and every held snapshot.

    Each revision is checked against held-out material on its own source
    references (Codex review F1): a snapshot of a deleted item, or one whose
    provenance differs from the current revision's, is protected when its
    own canonical exercise or source refs lie in held-out material. Returns
    the revisions and how many were skipped as protected."""

    from learnloop.vault.models import PracticeItem

    seen: set[str] = set()
    skipped: set[str] = set()
    revisions: list[tuple[Any, str]] = []
    for item in sorted(vault.practice_items.values(), key=lambda value: value.id):
        if getattr(item, "status", "active") != "active":
            continue
        content_hash, _json = item_revision(item)
        if protected.covers(item):
            skipped.add(content_hash)
            continue
        if content_hash not in seen:
            seen.add(content_hash)
            revisions.append((item, content_hash))
    for content_hash, item_id, item_json in connection.execute(
        "SELECT content_hash, practice_item_id, item_json FROM practice_item_snapshots ORDER BY created_at, content_hash"
    ):
        if content_hash in seen or content_hash in skipped:
            continue
        if str(item_id) in protected:
            skipped.add(content_hash)
            continue
        try:
            item = PracticeItem.model_validate_json(item_json)
        except ValueError:
            continue
        # A snapshot audits as the revision it holds, under its stored hash.
        if item_revision(item)[0] != content_hash:
            continue
        if protected.covers(item):
            skipped.add(content_hash)
            continue
        seen.add(content_hash)
        revisions.append((item, content_hash))
    return revisions, len(skipped)


def _never_attempted(vault: Any, connection: Any, protected: Protection) -> list[Any]:
    attempted = {str(row[0]) for row in connection.execute("SELECT DISTINCT practice_item_id FROM practice_attempts")}
    return [item for item in sorted(vault.practice_items.values(), key=lambda value: value.id)
            if getattr(item, "status", "active") == "active" and item.id not in attempted
            and not protected.covers(item)]


# -- the dry run's spend plan (Codex review F9) -------------------------------------------------


def _llm_plan(vault: Any, route_task: str, prompts: list[str], result_model: Any, *, role: str,
              retries: int) -> dict[str, Any]:
    """The resolved LLM route's plan through the spend framework: tokens with the
    output allowance, the billing label, and a refusal when a metered route has
    no ``adaptive_difficulty.price_per_million``.

    Worst case (Codex re-review F13): each logical call may be retried
    ``retries`` times (the execution path's ``max_retries``), and a truncation
    retry asks for ``TRUNCATION_RETRY_FACTOR`` times the output allowance, so
    every permitted attempt is planned, each retry at the enlarged allowance
    (a transport ceiling can only lower it): the same estimate the execution
    reserves attempt by attempt."""

    from learnloop.ai.output_budget import TRUNCATION_RETRY_FACTOR
    from learnloop.ai.spend import SpendBudget, SpendCaps
    from learnloop.practice_index.paid import PaidCalls, estimated_call_tokens, plan_route

    route = plan_route(vault, route_task)  # type: ignore[arg-type]
    price = vault.config.adaptive_difficulty.price_per_million
    subscription = route.billing == "subscription"
    calls = PaidCalls(route=route, budget=SpendBudget(SpendCaps(max_estimated_usd=None), subscription=subscription),
                      price_per_million=price, repository=None, owner_kind="ad_backfill_plan", owner_id="dry_run")
    retry_output = route.output_tokens * TRUNCATION_RETRY_FACTOR
    tokens = [estimated_call_tokens(prompt, result_model, route.output_tokens)
              + retries * estimated_call_tokens(prompt, result_model, retry_output) for prompt in prompts]
    plan = {"role": role, "route": route.as_dict(), **calls.plan(tokens)}
    plan["output_tokens_per_call"] = route.output_tokens
    plan["attempts_per_call"] = 1 + retries
    plan["retry_output_tokens"] = retry_output if retries else None
    if not route.available:
        plan["refused"] = f"no provider is routed for ai.routing.{route_task}"
    elif not subscription and price is None and prompts:
        plan["refused"] = (f"a metered ai.routing.{route_task} route needs adaptive_difficulty.price_per_million; "
                           "every call would be refused before sending")
    return plan


def _decider_plan(vault: Any, route_task: str, bodies: list[str]) -> dict[str, Any]:
    """The Decider's plan: one admitted request per body at its listed input price
    (no output allowance: the Decider is exempt from the output-budget policy)."""

    from learnloop.ai.routing import provider_for_task
    from learnloop.config.schema import DEFAULT_DECIDER_PRICE_PER_MILLION_INPUT

    name = provider_for_task(vault.config, route_task, allow_env=False).provider_name  # type: ignore[arg-type]
    profile = vault.config.ai.providers.get(name) if name else None
    price, basis, model = float(DEFAULT_DECIDER_PRICE_PER_MILLION_INPUT), "code_default_listed_price", None
    if profile is not None:
        try:
            from learnloop.ai.providers.decider import resolved_decider_settings

            settings = resolved_decider_settings(profile)
            price, basis, model = float(settings.price_per_million_input), "listed_input_price", settings.model
        except Exception as exc:  # noqa: BLE001 - an unusable profile is a planning refusal, not a crash
            return {"route": route_task, "provider": name, "requests": len(bodies), "refused": str(exc)[:200],
                    "estimated_usd": None}
    tokens = sum(len(body.encode("utf-8")) + 512 for body in bodies)
    return {"route": route_task, "provider": name, "model": model, "billing": "metered",
            "cost_basis": basis, "price_per_million_input": price, "requests": len(bodies),
            "estimated_input_tokens": tokens, "output_tokens_per_call": 0,
            "estimated_usd": round(tokens * price / 1_000_000, 6)}


def _metered_usd(*parts: Mapping[str, Any] | None) -> float | None:
    """The worst-case metered dollars of the plan's parts (None: one is unpriced)."""

    total = 0.0
    for part in parts:
        if not part:
            continue
        if part.get("billing") == "subscription":
            continue
        if part.get("refused") or part.get("estimated_usd") is None:
            if part.get("requests") or part.get("calls"):
                return None
            continue
        total += float(part["estimated_usd"])
    return round(total, 6)


def _cap(vault: Any, repository: Any, worst: float | None, clock: Clock | None) -> dict[str, Any]:
    from learnloop.adaptive_difficulty.spend import ad_envelope

    cap = float(vault.config.adaptive_difficulty.daily_spend_cap_usd)
    try:
        spent = float(ad_envelope(vault, repository, clock=clock)._total())
    except Exception:  # noqa: BLE001 - a database below the spend ledger has spent nothing
        spent = 0.0
    remaining = max(0.0, cap - spent)
    return {"daily_spend_cap_usd": cap, "spent_today_usd": round(spent, 6), "remaining_today_usd": round(remaining, 6),
            "metered_worst_case_usd": worst,
            "fits_today": None if worst is None else worst <= remaining + 1e-12,
            "note": ("the cap is enforced per request; what does not fit today is refused (refused_spend) and "
                     "left for a later run")}


def _audit_plan(vault: Any, pending: list[tuple[Any, str, list[str]]]) -> dict[str, Any]:
    from learnloop import decider_judgments

    from learnloop.adaptive_difficulty.feature_audit import (
        _CAPS,
        DECIDER_ROUTE,
        LLM_ROUTE,
        FeatureAuditV1,
        llm_prompt,
    )

    decider_on = decider_judgments.enabled(vault.config, "ad_feature_audit")
    prompts = [llm_prompt(item, dims) for item, _hash, dims in pending]
    plan: dict[str, Any] = {"revisions": len(pending), "dimensions": sum(len(d) for _i, _h, d in pending)}
    if decider_on:
        bodies = [json.dumps({"state": audit_state(item), "questions": {d: question_for(d).wire() for d in dims}},
                             ensure_ascii=False) for item, _hash, dims in pending]
        plan["decider"] = _decider_plan(vault, DECIDER_ROUTE, bodies)
        # Fallback exposure: worst case, every dimension the Decider leaves
        # unanswered goes to the LLM judge (one call per revision).
        plan["llm"] = _llm_plan(vault, LLM_ROUTE, prompts, FeatureAuditV1, role="fallback_worst_case",
                                retries=int(_CAPS["max_retries"]))
    else:
        plan["decider"] = {"route": DECIDER_ROUTE, "requests": 0,
                           "disabled": "[decider_routes] ad_feature_audit is off: the LLM judges every dimension"}
        plan["llm"] = _llm_plan(vault, LLM_ROUTE, prompts, FeatureAuditV1, role="primary",
                                retries=int(_CAPS["max_retries"]))
    return plan


def backfill(vault: Any, repository: Any, *, audit: bool, llm_v1: bool, reading: bool, dry_run: bool,
             limit: int | None = None, clients: Clients | None = None,
             decider_factory: Callable[[], Any] | None = None, clock: Clock | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"dry_run": dry_run}
    protected = protection(vault, repository)
    skipped = 0
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        revisions, skipped = _revisions(vault, connection, protected) if audit else ([], 0)
        pending_audits = [(item, content_hash, [d for d in DIMENSIONS if d not in canonical_audits(connection, content_hash)])
                          for item, content_hash in revisions]
        pending_audits = [entry for entry in pending_audits if entry[2]]
        candidates = _never_attempted(vault, connection, protected) if llm_v1 else []
        existing = {str(row[0]) for row in connection.execute(
            "SELECT item_content_hash FROM forecast_receipts WHERE kind = 'item_unassisted_success' AND scope = 'item' "
            "AND forecaster = ? AND status = 'ok'", (LLM_V1,))} if candidates else set()
        pending_v1 = [item for item in candidates if item_revision(item)[0] not in existing]
    if limit is not None:
        pending_audits, pending_v1 = pending_audits[:limit], pending_v1[:limit]
    audit_plan: dict[str, Any] | None = None
    v1_plan: dict[str, Any] | None = None
    if audit:
        if not feature_audit_enabled(vault.config):
            result["audit"] = {"status": "disabled", "reason": "adaptive_difficulty.feature_audit is off"}
        else:
            audit_plan = {**_audit_plan(vault, pending_audits), "protected_skipped": skipped}
            if dry_run:
                result["audit"] = {"status": "planned", **audit_plan}
            else:
                outcomes = [audit_revision(vault, repository, item, decider_factory=decider_factory,
                                           llm_client=clients.llm if clients else None, clock=clock,
                                           protected=protected).as_dict()
                            for item, _hash, _dims in pending_audits]
                result["audit"] = {"status": "done", **audit_plan,
                                   "by_status": _count(outcome.get("status") for outcome in outcomes)}
    if llm_v1:
        if LLM_V1 not in outside_forecasters(vault.config):
            result["llm_v1"] = {"status": "disabled", "reason": "llm_v1:item is not in adaptive_difficulty.outside_forecasters"}
        else:
            from learnloop.adaptive_difficulty.outside import _CAPS, ItemForecastV1, LLM_ROUTE, item_prompt

            v1_plan = {"items": len(pending_v1),
                       "llm": _llm_plan(vault, LLM_ROUTE, [item_prompt(vault, item) for item in pending_v1],
                                        ItemForecastV1, role="primary", retries=int(_CAPS["max_retries"]))}
            if dry_run:
                result["llm_v1"] = {"status": "planned", **v1_plan}
            else:
                outcomes = [forecast_item(vault, repository, item, clients=clients, clock=clock,
                                          protected=protected).as_dict()
                            for item in pending_v1]
                result["llm_v1"] = {"status": "done", **v1_plan,
                                    "by_status": _count(outcome.get("status") for outcome in outcomes)}
    if dry_run and (audit_plan is not None or v1_plan is not None):
        audit_parts = (audit_plan or {})
        worst = _metered_usd(audit_parts.get("decider"), audit_parts.get("llm"), (v1_plan or {}).get("llm"))
        result["spend"] = _cap(vault, repository, worst, clock)
    if reading:
        if not receipts_enabled(vault.config):
            result["reading"] = {"status": "disabled", "reason": "adaptive_difficulty.forecast_receipts is off"}
        elif dry_run:
            result["reading"] = {"status": "planned", "model_calls": 0}
        else:
            swept = sweep(vault, repository, as_of=utc_now_iso(clock), sweep_kind="backfill", clock=clock)
            result["reading"] = {"status": "done", **swept.as_dict()}
    return result


def _count(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[str(value)] = counts.get(str(value), 0) + 1
    return dict(sorted(counts.items()))


__all__ = ["backfill"]
