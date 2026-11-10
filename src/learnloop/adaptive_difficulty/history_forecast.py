"""Router objective RO2: ``llm_history_v1``, the frontier LLM full-history forecaster (spec_router_objective_v1 §6).

A new outside forecaster beside ``llm_v3:llm`` (:mod:`learnloop.adaptive_difficulty.outside`), on its
machinery, behind ``adaptive_difficulty.outside_forecasters`` (and so behind ``forecast_receipts`` and
the master switch). No successor tag (as AD1): it writes receipts only, and nothing serving, scoring,
scheduling, evidence, mastery, FSRS or certification reads them (A2, A12; the import contract
``adaptive-difficulty-never-writes-evidence`` holds for this module too). RO4's sensor layer reads
the receipts.

**At the serve** (:func:`freeze_history_inputs`, in the serve transaction, inside AD's serve
savepoint): the seeded draw (H3 on every eligible presentation, plus one of H0, H1, H2 with
probability 1/3 each, the draw's seed and ``u`` logged with every rung's propensity), and the two
cards it asks for, read through the serve's material view and frozen exactly
(``item_forecast_payloads``, owner ``ad_llm_history_state:plan_presentation:<id>:<rung>``, with the
protection epoch and the served revision's identity). The draw row
(``ad_history_forecast_draws``) names what each frozen card holds and what its budget left out.
Eligible: every plan presentation AD records whose item is not protected (A8), as ``llm_v3``'s.

**After the serve, in the background** (:func:`forecast_history_presentation`, scheduled with
``llm_v3``'s job): each frozen rung is sent exactly as frozen, under its own durable claim, through
:mod:`~learnloop.adaptive_difficulty.sending` (the held-out predicate as it stands immediately before
each request and record; content held out since the serve refuses it, and a refused rung records
nothing that quotes it), on ``ai.routing.ad_forecast_llm`` inside
``adaptive_difficulty.daily_spend_cap_usd`` and the ChatGPT plan's usage pauses. One call per rung
answers ``p_now`` (kind ``item_unassisted_success``, binding ``plan_presentation``), ``p_cold_L`` for
L in 1, 7, 30 (kind ``lo_cold_success``, binding ``lo_cold_after_block``, one receipt per lag, each
with the whole curve), each strictly in (0, 1), and at most three sentences of rationale citing the
card's evidence ids (unvalidated; kept in the receipt's forecast body for the trace only). Accepted
verdicts append to ``judgment_ledger``.

**A skipped forecast is censored with its reason, never imputed**: the spend cap
(``refused_spend``), a plan usage pause, an unavailable route, an invalid answer each write the
rung's receipts with no probability, no binding and ``censor_reason`` ``skipped:<reason>``. The
paired comparison reads the draw row as its denominator, so a missing pair is reported.
"""

from __future__ import annotations

from learnloop.adaptive_difficulty.operation import entry

import hashlib
import json
import logging
import re
from collections.abc import Callable, Mapping
from contextlib import closing
from typing import Any

from learnloop.ai.errors import AIInterrupted, AIInvalidOutput, AIProviderUnavailable
from learnloop.ai.execution import content_key
from learnloop.ai.schemas import WireModel
from learnloop.ai.spend import SpendLimitExceeded
from learnloop.ai.transport import render_structured_prompt
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.stores import ad_receipts as store
from learnloop.scheduling.forecast_receipts import (
    ITEM_UNASSISTED_SUCCESS,
    LO_COLD_AFTER_BLOCK,
    LO_COLD_SUCCESS,
    NO_BINDING,
    ForecastReceipt,
    record_receipts,
)

from learnloop.adaptive_difficulty import history_card as HC
from learnloop.adaptive_difficulty import sending
from learnloop.adaptive_difficulty import spend as ad_spend
from learnloop.adaptive_difficulty.feature_audit import item_revision
from learnloop.adaptive_difficulty.forecasters import EVENT
from learnloop.adaptive_difficulty.material_view import current_view
from learnloop.adaptive_difficulty.outside import (
    LLM_ROUTE,
    PURPOSE,
    ForecastOutcome,
    Clients,
    _llm_client,
    _record_admission,
    _protected,
    _store_payloads,
    source_identity,
)
from learnloop.adaptive_difficulty.sending import ProtectedContent, SendGuard, refusal_status
from learnloop.adaptive_difficulty.switches import LLM_HISTORY, outside_forecasters

LOG = logging.getLogger(__name__)

FORECASTER = LLM_HISTORY
CARD_VERSION = HC.CARD_VERSION
PROMPT_VERSION = "ad-llm-history-v1"
DRAW_VERSION = "ad-history-draw-v1"
ANCHOR = "H3"
#: The lower rungs, one drawn beside H3 on each presentation with equal probability (structural: a
#: uniform draw over the three, the logged propensity of each).
DRAWN = ("H0", "H1", "H2")
#: ``keep``: the cold lags asked (days after the block): measurement points, nothing weights them.
LAGS = (1, 7, 30)
#: ``keep``: at most this many sentences of rationale are kept (spec §6.2), unvalidated.
RATIONALE_SENTENCES = 3
FROZEN_PREFIX = "ad_llm_history_state:plan_presentation:"
NOW_EVENT = EVENT
COLD_EVENT = "lo_cold_unassisted_success"
#: The label the receipts forecast (spec §6.2), stated on every receipt.
LABEL = {
    "version": "ad-history-label-v1",
    "p_now": "a completed, unassisted attempt on this presentation at the board's success threshold "
             "(AD §5.3's Y = 2; help, reveals and exclusions stay distinct states)",
    "p_cold": "a completed, unassisted attempt on an unseen item of this LO, L days after this block, "
              "had the learner no exposure to the LO in between",
}
QUESTION = ("Forecast this learner from their whole history. p_now: will the learner answer the item now "
            "presented fully or almost fully correctly, without help? p_cold_1, p_cold_7, p_cold_30: if the "
            "learner has no exposure to this topic in between, will they answer an unseen item on it fully or "
            "almost fully correctly, without help, 1, 7 and 30 days after this block?")


class HistoryForecastV1(WireModel):
    """The LLM's answer: four probabilities strictly between 0 and 1, and a short rationale."""

    p_now: float
    p_cold_1: float
    p_cold_7: float
    p_cold_30: float
    rationale: str = ""


def forecaster_name(rung: str) -> str:
    return f"{FORECASTER}:{rung}"


def frozen_key(presentation_id: str, rung: str) -> str:
    return f"{FROZEN_PREFIX}{presentation_id}:{rung}"


def draw_key(presentation_id: str) -> str:
    return f"{FORECASTER}:plan_presentation:{presentation_id}"


def receipt_keys(presentation_id: str, rung: str) -> dict[str, str]:
    """The canonical receipt keys of one rung's call: ``now`` and ``cold_<L>``."""

    name = forecaster_name(rung)
    keys = {"now": f"{ITEM_UNASSISTED_SUCCESS}:plan_presentation:{presentation_id}:{name}"}
    for lag in LAGS:
        keys[f"cold_{lag}"] = f"{LO_COLD_SUCCESS}:plan_presentation:{presentation_id}:{name}:L{lag}"
    return keys


def draw(presentation_id: str) -> dict[str, Any]:
    """The seeded draw of the lower rung: the seed (a digest of the draw version and the presentation),
    ``u`` in [0, 1) and the rung of its third, each rung's propensity 1/3."""

    seed = hashlib.sha256(f"{DRAW_VERSION}:{presentation_id}".encode()).hexdigest()[:16]
    u = int(seed, 16) / float(1 << 64)
    rung = DRAWN[min(int(u * len(DRAWN)), len(DRAWN) - 1)]
    propensities = {name: 1.0 / len(DRAWN) for name in DRAWN}
    return {"seed": seed, "u": u, "drawn_rung": rung, "propensity": propensities[rung],
            "propensities": propensities}


def _budget(vault: Any) -> int:
    section = getattr(getattr(vault, "config", None), "adaptive_difficulty", None)
    return int(getattr(section, "history_card_token_budget", 48_000) or 48_000)


def freeze_history_inputs(vault: Any, connection: Any, item: Any, *, presentation_id: str, served_at: str,
                          view: Any) -> str | None:
    """In the serve transaction: the draw and the exact request inputs of its two rungs.

    Returns the draw key, or None with ``llm_history_v1`` off (nothing is read or written then)."""

    if FORECASTER not in outside_forecasters(vault.config):
        return None
    if not store.has_table(connection, store.HISTORY_DRAWS):
        return None
    from learnloop.adaptive_difficulty.operation import epoch_of

    key = draw_key(presentation_id)
    if view.lookup(connection, store.HISTORY_DRAWS, "draw_key = ?", (key,))[0] != "missing":
        return key
    drawn = draw(presentation_id)
    built = HC.build_sections(vault, connection, item, served_at=served_at, view=view)
    content_hash, _json = item_revision(item)
    epoch = epoch_of(view)
    budget = _budget(vault)
    frozen: dict[str, Any] = {}
    for rung in (ANCHOR, drawn["drawn_rung"]):
        state, left_out = HC.rung_card(vault, item, built, rung, budget=budget)
        owner = frozen_key(presentation_id, rung)
        state_hash = content_key(state)
        store.insert_payload(connection, owner_key=owner, forecaster=FORECASTER, kind="request", content={
            "state": state, "state_version": CARD_VERSION, "state_hash": state_hash, "rung": rung,
            "practice_item_id": str(item.id), "learning_object_id": item.learning_object_id,
            "content_hash": content_hash, "inputs_as_of": served_at, "protection_epoch": epoch,
            "protection_identities": {"target": source_identity(item)},
            "latest_exposure_days_before": built["latest_exposure_days_before"],
        }, created_at=served_at)
        frozen[rung] = {"owner_key": owner, "state_hash": state_hash, "bytes": HC._size(state),
                        "left_out": {level: {name: record["entries"] for name, record in sections.items()}
                                     for level, sections in left_out.items()},
                        "evidence_entries": len(HC.evidence_ids(state))}
    store.insert_history_draw(connection, {
        "draw_key": key, "plan_presentation_id": presentation_id, "practice_item_id": str(item.id),
        "learning_object_id": item.learning_object_id, "draw_version": DRAW_VERSION, "seed": drawn["seed"],
        "u": drawn["u"], "anchor_rung": ANCHOR, "drawn_rung": drawn["drawn_rung"],
        "propensity": drawn["propensity"], "propensities_json": drawn["propensities"],
        "card_version": CARD_VERSION, "frozen_json": {**frozen, "row_limits_reached": built["row_limits_reached"]},
        "protection_epoch": epoch, "served_at": served_at, "created_at": served_at,
    })
    return key


def _frozen(connection: Any, presentation_id: str, rung: str) -> tuple[str, dict[str, Any] | None]:
    """``(status, content)``: ``ok`` and the frozen inputs; ``withheld`` (frozen at another protection
    epoch or naming withheld material: expired, never sent); ``missing``."""

    status, row = current_view().lookup(connection, store.PAYLOADS, "owner_key = ? AND kind = 'request'",
                                        (frozen_key(presentation_id, rung),))
    if row is None:
        return status, None
    content = row.get("content")
    if content is None:
        try:
            content = json.loads(row.get("content_json") or "null")
        except (TypeError, ValueError):
            content = None
    if not (isinstance(content, dict) and isinstance(content.get("state"), dict)
            and isinstance((content.get("protection_identities") or {}).get("target"), dict)
            and isinstance(content.get("protection_epoch"), str)
            and content.get("state_hash") == content_key(content["state"])):
        return "missing", None
    return "ok", content


def _done(connection: Any, presentation_id: str, rung: str) -> bool:
    key = receipt_keys(presentation_id, rung)["now"]
    return current_view().lookup(connection, "forecast_receipts", "receipt_key = ?", (key,))[0] != "missing"


@entry(durable="it sends to a model: its claim, spend and receipts commit per unit")
def forecast_history_presentation(vault: Any, repository: Any, presentation_id: str, *,
                                  clients: Clients | None = None, clock: Clock | None = None, fence: Any = None,
                                  live_vault: Callable[[], Any] | None = None) -> list[ForecastOutcome]:
    """``llm_history_v1`` for one plan presentation: its frozen rungs, H3 first, each sent exactly as frozen."""

    from learnloop.adaptive_difficulty.claims import LeaseLost, claimed, history_key
    from learnloop.adaptive_difficulty.material_view import material_view

    clients = clients or Clients()
    if FORECASTER not in outside_forecasters(vault.config):
        return []
    view = material_view(vault, repository)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if not store.has_table(connection, store.HISTORY_DRAWS):
            return []
        found, presentation = view.presentation_status(connection, presentation_id)
        drawn_status, drawn = view.lookup(connection, store.HISTORY_DRAWS, "draw_key = ?",
                                          (draw_key(presentation_id),))
        if found == "missing" or drawn_status == "missing":
            return [ForecastOutcome(FORECASTER, "no_frozen_inputs")]
        if drawn_status != "ok" or drawn is None or presentation is None:
            # The draw (and with it the frozen rungs) of another protection epoch, or its item withheld
            # now: expired, never sent (E2; A8).
            return [ForecastOutcome(FORECASTER, "protected")]
        rungs = [ANCHOR, str(drawn["drawn_rung"])]
        pending = [rung for rung in rungs if not _done(connection, presentation_id, rung)]
        frozen = {rung: _frozen(connection, presentation_id, rung) for rung in pending}
    if not pending:
        return []
    item_id = str(presentation["practice_item_id"])
    item = view.item(item_id)
    outcomes: list[ForecastOutcome] = []
    try:
        with claimed(repository, history_key(presentation_id), fence=fence) as worker:
            if worker is None:
                return [ForecastOutcome(forecaster_name(rung), "busy") for rung in pending]
            for rung in pending:
                status, content = frozen[rung]
                if content is None:
                    outcomes.append(ForecastOutcome(forecaster_name(rung),
                                                    "protected" if status == "withheld" else "no_frozen_inputs"))
                    continue
                with closing(connect(repository.sqlite_path, read_only=True)) as connection:
                    if _done(connection, presentation_id, rung):
                        continue
                send = SendGuard(vault, repository, items=[item], item_ids=[item_id],
                                 identities=[content["protection_identities"]["target"]],
                                 epoch=content["protection_epoch"], live_vault=live_vault)
                try:
                    send.check("the history forecast")
                except ProtectedContent as exc:
                    outcomes.append(ForecastOutcome(forecaster_name(rung), refusal_status(exc), reason=str(exc)[:200]))
                    continue
                outcomes.append(_forecast_rung(vault, worker, rung, presentation, content, dict(drawn),
                                               clients=clients, clock=clock, send=send))
    except LeaseLost:
        done = {outcome.forecaster for outcome in outcomes if outcome.status != "stale"}
        outcomes = [outcome for outcome in outcomes if outcome.forecaster in done]
        outcomes += [ForecastOutcome(forecaster_name(rung), "stale") for rung in pending
                     if forecaster_name(rung) not in done]
    return outcomes


def prompt_for(state: Mapping[str, Any]) -> str:
    """The request ``llm_history_v1`` sends for one frozen state (the audit's dry run plans it too)."""

    return render_structured_prompt("Forecast the learner from their whole history", PROMPT_VERSION, {
        "instructions": (f"{QUESTION} Judge only from the state: the item and the learner's history, all of which "
                         "was known before this item was shown; days_before says how long before. Return p_now, "
                         "p_cold_1, p_cold_7 and p_cold_30, each your probability strictly between 0 and 1, and a "
                         f"rationale of at most {RATIONALE_SENTENCES} sentences citing the evidence_id of each "
                         "entry you rely on."),
        "state": dict(state),
    })


def _skip_reason(exc: BaseException | None, why: str | None = None) -> str:
    """Why a forecast was not made, as a censoring reason."""

    text = f"{type(exc).__name__ if exc is not None else ''} {why or ''} {exc or ''}".lower()
    if isinstance(exc, SpendLimitExceeded):
        return "spend_cap"
    if "usageexhausted" in text or "usage exhausted" in text or "usage limit" in text or "paused" in text:
        return "plan_paused"
    if why == "models_off":
        return "models_off"
    if exc is None:
        return "unavailable"
    if isinstance(exc, AIInvalidOutput):
        return "invalid_output"
    return f"failed:{type(exc).__name__}"


def _sentences(text: str) -> tuple[str, bool]:
    parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", " ".join(str(text or "").split())) if part.strip()]
    return " ".join(parts[:RATIONALE_SENTENCES]), len(parts) > RATIONALE_SENTENCES


_ID = re.compile(r"\b(?:attempt|help|question|reveal|reading|reader_question|digest|gap|goal):[A-Za-z0-9_.\-]+")


def _validated(answer: Any) -> dict[str, float]:
    values = {}
    for name in ("p_now", "p_cold_1", "p_cold_7", "p_cold_30"):
        value = getattr(answer, name, None)
        if not isinstance(value, (int, float)) or not 0.0 < float(value) < 1.0:
            raise AIInvalidOutput(f"{name} not strictly between 0 and 1")
        values[name] = float(value)
    return values


def _ask(vault: Any, repository: Any, client: Any, *, prompt: str, owner_id: str, envelope: Any,
         send: SendGuard) -> tuple[Any, str]:
    from learnloop.practice_index.paid import plan_route

    route = plan_route(vault, LLM_ROUTE, client)  # type: ignore[arg-type]
    subscription = route.billing == "subscription"
    price = vault.config.adaptive_difficulty.price_per_million
    if not subscription and price is None:
        raise SpendLimitExceeded("a metered ad_forecast_llm route needs adaptive_difficulty.price_per_million")
    caps = dict(max_candidates=0, max_pairs=0, max_retries=1, max_calls=2,
                max_total_tokens=call_tokens(route, prompt)["with_retry"])
    answer, calls = sending.ask_llm(send, route, client, price=price, repository=repository, caps=caps,
                                    owner_kind=ad_spend.FORECAST_OWNER_KIND, owner_id=owner_id, purpose=PURPOSE,
                                    prompt=prompt, result_model=HistoryForecastV1, metadata={"owner_id": owner_id},
                                    envelope=envelope)
    model = str(calls.last_resolved_model or getattr(client, "model", None) or route.model or "unknown")
    return answer, model


def _receipts(*, presentation: Mapping[str, Any], content: Mapping[str, Any], drawn: Mapping[str, Any], rung: str,
              values: Mapping[str, float] | None, status: str, received: str, model: str | None, request_hash: str,
              rationale: Mapping[str, Any] | None, censor: str | None, suffix: str | None) -> list[ForecastReceipt]:
    presentation_id = str(presentation["id"])
    served_at = str(presentation["served_at"])
    name = forecaster_name(rung)
    keys = receipt_keys(presentation_id, rung)
    propensity = 1.0 if rung == ANCHOR else float(drawn.get("propensity") or 0.0)
    inputs = {"practice_item_id": str(content["practice_item_id"]), "plan_presentation_id": presentation_id,
              "content_hash": content["content_hash"], "state_version": CARD_VERSION, "rung": rung,
              "state_hash": content["state_hash"], "frozen_inputs": frozen_key(presentation_id, rung),
              "draw_key": draw_key(presentation_id), "draw_propensity": propensity,
              # The clocks (spec §6.2): the block's own time is the serve; the delay since the latest
              # exposure to the LO known then. Each resolution adds the realized lag.
              "clocks": {"block_at": served_at,
                         "latest_exposure_days_before_serve": content.get("latest_exposure_days_before")}}
    versions = {"state": CARD_VERSION, "prompt": PROMPT_VERSION, "model": model, "draw": DRAW_VERSION,
                "label": LABEL["version"]}
    columns = {"practice_item_id": str(content["practice_item_id"]),
               "learning_object_id": content.get("learning_object_id"), "plan_presentation_id": presentation_id,
               "decision_ref": presentation_id, "status": status, "received_at": received}
    if censor:
        columns["censor_reason"] = censor
    curve = None if values is None else {str(lag): round(values[f"p_cold_{lag}"], 8) for lag in LAGS}
    common = {"rung": rung, "request_hash": request_hash, "label": LABEL, "rationale_unvalidated": rationale}
    out = [ForecastReceipt(
        receipt_key=keys["now"] if suffix is None else f"{keys['now']}:{suffix}", kind=ITEM_UNASSISTED_SUCCESS,
        forecaster=name, forecaster_version=f"{PROMPT_VERSION}:{model or 'unknown'}", scope="presentation",
        decision_kind="serve", binding_kind=NO_BINDING if censor else "plan_presentation", event=NOW_EVENT,
        forecast={"p": None if values is None else round(values["p_now"], 8), "event": NOW_EVENT,
                  "p_categories": None, **common},
        inputs=inputs, parameters=[], versions=versions, inputs_as_of=served_at,
        p=None if values is None else values["p_now"], columns=columns)]
    for lag in LAGS:
        key = keys[f"cold_{lag}"]
        out.append(ForecastReceipt(
            receipt_key=key if suffix is None else f"{key}:{suffix}", kind=LO_COLD_SUCCESS, forecaster=name,
            forecaster_version=f"{PROMPT_VERSION}:{model or 'unknown'}", scope="presentation", decision_kind="serve",
            binding_kind=NO_BINDING if censor else LO_COLD_AFTER_BLOCK, event=COLD_EVENT,
            forecast={"p": None if values is None else round(values[f"p_cold_{lag}"], 8), "event": COLD_EVENT,
                      "lag_days": lag, "curve": curve, **common},
            inputs=inputs, parameters=[], versions=versions, inputs_as_of=served_at,
            p=None if values is None else values[f"p_cold_{lag}"], columns=columns))
    return out


def _write(repository: Any, vault: Any, receipts: list[ForecastReceipt], *, created_at: str, payload_key: str,
           request: Any, response: Any, received: str, judged: Mapping[str, Any] | None,
           admit: Callable[[], None] | None) -> list[str]:
    """One rung's payloads, its receipts and (accepted) their judgments, in one fenced transaction."""

    from dataclasses import replace

    from learnloop.db.stores.judgments import append_judgment

    stamped = [replace(receipt, columns={**dict(receipt.columns),
                                         "algorithm_version": vault.config.algorithms.algorithm_version},
                       versions={**dict(receipt.versions or {}), "protection_epoch": current_view().epoch})
               for receipt in receipts]
    with repository.atomic():
        if admit is not None:
            admit()
        _store_payloads(repository, payload_key, FORECASTER, request, response, received,
                        vault.config.router.payload_retention_days)
        written = record_receipts(repository, stamped, created_at=created_at)
        if judged is not None and len(written) == len(stamped):
            for receipt, receipt_id in zip(stamped, written, strict=True):
                if receipt.p is None:
                    continue
                append_judgment(
                    repository.connection(), task=PURPOSE, left_kind="plan_presentation",
                    left_id=str(receipt.columns["plan_presentation_id"]), right_kind="forecaster",
                    right_id=receipt.forecaster, judge="llm", judge_model=str(judged.get("model") or "unknown"),
                    prompt_version=PROMPT_VERSION, input_hash=str(judged["input_hash"]),
                    verdict=f"{float(receipt.p):.6f}", score=float(receipt.p), created_at=received,
                    rationale=json.dumps({"receipt_key": receipt.receipt_key, "receipt_id": receipt_id,
                                          "event": receipt.event, "kind": receipt.kind,
                                          "inputs_as_of": receipt.inputs_as_of,
                                          "lag_days": receipt.forecast.get("lag_days")}, sort_keys=True, default=str))
    return written


def _forecast_rung(vault: Any, worker: Any, rung: str, presentation: Mapping[str, Any], content: Mapping[str, Any],
                   drawn: Mapping[str, Any], *, clients: Clients, clock: Clock | None, send: SendGuard
                   ) -> ForecastOutcome:
    from learnloop.adaptive_difficulty.claims import LeaseLost, ReceiptWriteFailed

    repository = worker.repository
    presentation_id = str(presentation["id"])
    served_at = str(presentation["served_at"])
    name = forecaster_name(rung)
    outcome = ForecastOutcome(name, "ok")
    issued = utc_now_iso(clock)
    prompt = prompt_for(content["state"])
    request: dict[str, Any] = {"prompt": prompt}
    request_hash = content_key(request)
    envelope = ad_spend.ad_envelope(vault, worker.base, clock=clock)
    values: dict[str, float] | None = None
    rationale: dict[str, Any] | None = None
    response, model, failure, why = None, None, None, None
    status = "ok"
    client, why = _llm_client(vault, clients.llm)
    if client is None:
        status, failure = "failed", None
    else:
        try:
            worker.require_live()
            answer, model = _ask(vault, repository, client, prompt=prompt, owner_id=f"{presentation_id}:{rung}",
                                 envelope=envelope, send=send)
            values = _validated(answer)
            response = answer.model_dump(mode="json")
            text, truncated = _sentences(getattr(answer, "rationale", "") or "")
            cited = sorted(set(_ID.findall(text)))
            known = HC.evidence_ids(content["state"])
            rationale = {"text": text, "truncated": truncated, "cited": [i for i in cited if i in known],
                         "unknown_ids": [i for i in cited if i not in known]}
        except ProtectedContent as exc:
            return ForecastOutcome(name, refusal_status(exc), reason=str(exc)[:200])
        except ReceiptWriteFailed as exc:
            # Its start receipt could not be written, so nothing was sent (fix round 8).
            return ForecastOutcome(name, "failed", reason=str(exc)[:200])
        except (AIInterrupted, LeaseLost):
            raise
        except SpendLimitExceeded as exc:
            status, failure = "refused_spend", exc
        except (AIProviderUnavailable, AIInvalidOutput, TimeoutError, ValueError) as exc:
            status, failure = "failed", exc
        except Exception as exc:  # noqa: BLE001 - a failed forecaster is a censored receipt, never a crash
            status, failure = "failed", exc
    admit = _record_admission(send, outcome)
    if admit is None:
        return outcome
    received = utc_now_iso(clock)
    censor = None if status == "ok" else f"skipped:{_skip_reason(failure, why)}"
    suffix = None if status == "ok" else f"{status}:{received}"
    receipts = _receipts(presentation=presentation, content=content, drawn=drawn, rung=rung, values=values,
                         status=status, received=received, model=model, request_hash=request_hash,
                         rationale=rationale, censor=censor, suffix=suffix)
    final_key = receipts[0].receipt_key
    try:
        written = _write(repository, vault, receipts, created_at=max(issued, served_at), payload_key=final_key,
                         request=request, response=response, received=received,
                         judged={"model": model, "input_hash": request_hash} if status == "ok" else None,
                         admit=admit)
    except ProtectedContent as exc:
        _protected(outcome, exc)
        return outcome
    outcome.receipt_id = written[0] if written else None
    outcome.status = status if status == "ok" else status
    outcome.p = None if values is None else values["p_now"]
    outcome.reason = censor
    return outcome


def call_tokens(route: Any, prompt: str) -> dict[str, int]:
    """What one logical call on ``route`` is charged, as the paid path charges it (Codex review F5): the
    request is reserved at the route's own output budget (``route.output_tokens``, which
    :func:`sending.ask_llm` passes on), and its one allowed retry (``max_retries=1``: a provider failure
    at that budget, or a truncation at double it, held to the transport's ceiling) at most double. The
    background job's caps and the audit's dry run both read this, so the dry run plans exactly what the
    run admits. Metered tokens count each physical request (``METERED_REQUESTS_PER_CALL``)."""

    from learnloop.practice_index.paid import METERED_REQUESTS_PER_CALL, estimated_call_tokens

    output = int(route.output_tokens)
    initial = estimated_call_tokens(prompt, HistoryForecastV1, output) * METERED_REQUESTS_PER_CALL
    retry = estimated_call_tokens(prompt, HistoryForecastV1, 2 * output) * METERED_REQUESTS_PER_CALL
    return {"output_tokens": output, "initial": initial, "with_retry": initial + retry}


def expected_calls(vault: Any = None) -> dict[str, Any]:
    """What one eligible presentation costs (for the owner, before landing): two calls (H3 and the drawn
    rung), each the frozen card (at most ``history_card_token_budget`` bytes) plus the instructions in,
    and at most the route's output budget out (``ai.route_output_tokens.ad_forecast_llm``, else the
    serving profile's ``max_tokens``, else ``ai.output_tokens``), one retry at most double."""

    from learnloop.ai.output_budget import output_budget
    from learnloop.practice_index.paid import plan_route

    out = plan_route(vault, LLM_ROUTE).output_tokens if vault is not None else output_budget(None, LLM_ROUTE)
    return {"calls_per_presentation": 2, "rungs": [ANCHOR, "one of " + ", ".join(DRAWN)],
            "output_tokens_per_call": out, "retries_per_call": 1}


__all__ = [
    "ANCHOR", "CARD_VERSION", "COLD_EVENT", "DRAWN", "DRAW_VERSION", "FORECASTER", "HistoryForecastV1", "LABEL", "LAGS",
    "PROMPT_VERSION", "call_tokens", "draw", "draw_key", "expected_calls", "forecast_history_presentation", "forecaster_name",
    "freeze_history_inputs", "frozen_key", "prompt_for", "receipt_keys",
]
