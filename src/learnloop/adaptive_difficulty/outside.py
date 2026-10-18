"""The outside forecasters (spec_adaptive_difficulty_v1 §8.1-8.2, §7.3, D4; AD1, switch ``outside_forecasters``).

* ``llm_v1:item``: an item-only LLM forecast of "the probability a typical
  learner studying this topic answers correctly" (field V1's question,
  no learner data): the item stem, its LO and facet names, its capability
  and practice mode (never the reference answer, rubric, hints or the
  item's own ``difficulty`` label). Once per item revision, when the
  revision is prepared for the pool (in the background after a plan build,
  after its feature audit) and once in the owner-run backfill; never at a
  presentation. Scope ``item`` (``item_content_hash``), scored against the
  revision's first bound presentation; it becomes the signal ``z_v1`` of a
  serve only when it was received before that serve (§7.3, G-AD1-9).
* ``llm_v3:llm`` and ``llm_v3:decider``: competing experts (§8.4), never an
  offset prior. The serve transaction freezes their exact request inputs
  (:func:`freeze_presentation_inputs`, Codex review F2): the served
  revision's V1 item view plus a card of the learner's history restricted to
  the item's LO and its prerequisites as it stood at the serve (the
  incumbent's numbers from its receipt, and the attempts completed before
  it with their grades as they then stood: result category, hints, primed,
  the question asked; never an answer text). After the serve, in the
  background, they are sent exactly as frozen (``inputs_as_of`` = the
  serve, true whatever was regraded or edited since); a presentation
  without frozen inputs is never forecast. With them the serve freezes the
  identity and own source references of every revision they quote (the
  target and each history item), and the job revalidates those against
  the held-out predicate as it stands when it sends: content marked held
  out after the serve refuses the forecast (Codex re-review F11). The LLM
  is asked field's V3 question as structured output; the Decider a
  ``noul`` question.

Every receipt is kind ``item_unassisted_success`` in the ``forecast_receipts``
family, written once when the answer arrives (``created_at`` = when the
request was issued, ``received_at`` = when it arrived; ``status`` ok /
failed / refused_spend). A forecast is valid for its presentation iff its
inputs predate the serve, whenever it arrives
(:func:`learnloop.scheduling.forecast_receipts.valid_for_serve`). Raw
requests and responses go to ``item_forecast_payloads`` (WORKFLOW, pruned
after ``router.payload_retention_days``); the receipt keeps the hash. An
accepted forecast also appends its verdict to ``judgment_ledger`` (task
``ad_item_forecast``: model, prompt version, request hash, the receipt key;
Codex review F8), in the receipt's transaction. Each unit of paid work runs
under a durable, fenced claim (:mod:`learnloop.adaptive_difficulty.claims`;
Codex review F5, F6).

Routes: ``ai.routing.ad_forecast_llm`` (Codex on the subscription is
``estimated_only``) and ``ai.routing.ad_forecast_decider`` (decider-only),
inside ``adaptive_difficulty.daily_spend_cap_usd``. Exam protection (A8): a
protected item is never forecast, and protected items never appear in a
history card.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, Mapping
from contextlib import closing
from dataclasses import asdict, dataclass, field
from datetime import timedelta
from typing import Any

from learnloop.ai.decisions import NoulQuestion
from learnloop.ai.errors import AIInterrupted, AIInvalidOutput, AIProviderUnavailable
from learnloop.ai.execution import content_key
from learnloop.ai.schemas import WireModel
from learnloop.ai.spend import SpendBudget, SpendCaps, SpendLimitExceeded, spend_envelopes
from learnloop.ai.transport import render_structured_prompt
from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.stores import ad_receipts as store
from learnloop.db.stores import forecast_receipts as receipt_store
from learnloop.scheduling.forecast_receipts import (
    FIRST_PRESENTATION,
    ITEM_UNASSISTED_SUCCESS,
    ForecastReceipt,
    record_receipts,
)

from learnloop.adaptive_difficulty import spend as ad_spend
from learnloop.adaptive_difficulty.feature_audit import item_revision
from learnloop.adaptive_difficulty.forecasters import EVENT, INCUMBENT, receipt_key
from learnloop.adaptive_difficulty.protection import guard
from learnloop.adaptive_difficulty.switches import LLM_V1, LLM_V3_DECIDER, LLM_V3_LLM, outside_forecasters

LOG = logging.getLogger(__name__)

STATE_VERSION = "ad-forecast-state-v1"
V1_PROMPT_VERSION = "ad-llm-v1-item-v1"
V3_PROMPT_VERSION = "ad-llm-v3-v1"
DECIDER_QUESTION_SET = "ad-llm-v3-decider-v1"
LLM_ROUTE = "ad_forecast_llm"
DECIDER_ROUTE = "ad_forecast_decider"
PURPOSE = "ad_item_forecast"
STEM_LIMIT = 1_500
HISTORY_STEM_LIMIT = 200
HISTORY_LIMIT = 25
V1_QUESTION = "What is the probability that a typical learner studying this topic answers this item correctly?"
V3_QUESTION = "Will the learner answer this item correctly on this attempt?"
DECIDER_QUESTIONS = {
    "will_pass": NoulQuestion(
        instructions=(f"{V3_QUESTION} Judge only from the state: the item and the learner's earlier work, "
                      "which all happened before this item was shown."),
        when_true="The learner's answer to this item will be fully or almost fully correct, without help.",
        when_false="The answer will be wrong or incomplete, the learner will need help, or will not know.",
    ),
}
_CAPS = dict(max_candidates=0, max_pairs=0, max_retries=1, max_calls=2, max_total_tokens=80_000)


class ItemForecastV1(WireModel):
    """The LLM's answer: a probability strictly between 0 and 1."""

    p_correct: float


def _excerpt(text: Any, limit: int) -> str:
    value = " ".join(str(text or "").split())
    return value if len(value) <= limit else value[: limit - 1] + "…"


def item_view(vault: Any, item: Any) -> dict[str, Any]:
    """V1's content: the stem, LO and facet names; no answer, rubric, hints or label."""

    lo = vault.learning_objects.get(item.learning_object_id)
    facets = []
    for facet_id in item.evidence_facets:
        entry = vault.evidence_facets.get(vault.canonical_facet_id(str(facet_id)))
        title = (entry.title if entry is not None and entry.title else str(facet_id)).strip()
        if title and title not in facets:
            facets.append(title)
    return {
        "stem": _excerpt(item.prompt, STEM_LIMIT),
        "topic": lo.title if lo is not None else "an unnamed topic",
        "skills": facets,
        "capability": getattr(item, "capability", None),
        "practice_mode": item.practice_mode,
    }


def _result(correctness: Any) -> str:
    if correctness is None:
        return "ungraded"
    value = float(correctness)
    if value >= 0.8:
        return "correct"
    if value < 0.4:
        return "incorrect"
    return "partial"


def source_identity(item: Any, practice_item_id: str | None = None) -> dict[str, Any]:
    """A revision's protection identity: its item id and its own source references.

    What :meth:`~learnloop.adaptive_difficulty.protection.Protection.covers_identity`
    revalidates later (Codex re-review F11): the block keys and whole
    extractions of the revision's canonical exercise and provenance refs, as
    the revision quoted then had them. ``item`` None (an attempt's item no
    longer in the vault, whose text is not quoted) has only its id."""

    from learnloop.content.sources.exam_material import item_source_keys

    if item is None:
        return {"practice_item_id": str(practice_item_id), "keys": [], "whole": []}
    keys, whole = item_source_keys(item)
    return {"practice_item_id": str(practice_item_id or item.id),
            "keys": sorted([str(extraction), str(span)] for extraction, span in keys),
            "whole": sorted(str(extraction) for extraction in whole)}


def history_card(vault: Any, connection: Any, item: Any, *, served_at: str, protected: frozenset[str],
                 incumbent: Mapping[str, Any] | None,
                 identities: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """The learner's history on the item's LO and its prerequisites, as of the serve.

    ``identities``, when given, receives the :func:`source_identity` of each
    attempt's item the card includes (Codex re-review F11)."""

    lo = vault.learning_objects.get(item.learning_object_id)
    scope = [item.learning_object_id, *[str(prerequisite) for prerequisite in (getattr(lo, "prerequisites", None) or [])]]
    scope = list(dict.fromkeys(scope))
    served = parse_utc(served_at)
    marks = ",".join("?" for _ in scope)
    rows = connection.execute(
        "SELECT id, practice_item_id, learning_object_id, attempt_type, correctness, hints_used, primed, created_at "
        f"FROM practice_attempts WHERE learning_object_id IN ({marks}) AND attempt_type != 'self_report' "
        "ORDER BY created_at DESC, id DESC", scope,
    ).fetchall()
    attempts = []
    for row in rows:
        stamp = parse_utc(str(row[7])) if row[7] else None
        if stamp is None or served is None or stamp >= served or str(row[1]) in protected:
            continue
        past = vault.practice_items.get(str(row[1]))
        if identities is not None:
            identities.append(source_identity(past, str(row[1])))
        attempts.append({
            "item": _excerpt(past.prompt, HISTORY_STEM_LIMIT) if past is not None else "(an item no longer in the vault)",
            "topic": (vault.learning_objects[str(row[2])].title if str(row[2]) in vault.learning_objects else str(row[2])),
            "same_item": str(row[1]) == str(item.id),
            "result": _result(row[4]),
            "hints_used": int(row[5] or 0),
            "answer_was_shown": bool(row[6]),
            "attempt_type": str(row[3]),
            "days_before": round(max(0.0, (served - stamp).total_seconds() / 86400.0), 2),
        })
        if len(attempts) >= HISTORY_LIMIT:
            break
    topics = [vault.learning_objects[lo_id].title for lo_id in scope if lo_id in vault.learning_objects]
    return {
        "topics": topics,
        "incumbent": dict(incumbent or {}),
        "recent_attempts": list(reversed(attempts)),
        "not_recorded": "LearnLoop does not record when an ordinary hint was revealed relative to the work.",
    }


@dataclass
class ForecastOutcome:
    forecaster: str
    status: str
    receipt_id: str | None = None
    p: float | None = None
    reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass
class Clients:
    """Injected clients (tests, a sidecar's ``ad_clients``); None resolves the route."""

    llm: Any | None = None
    decider: Any | None = None


def _llm_client(vault: Any, injected: Any | None) -> tuple[Any | None, str | None]:
    from learnloop.practice_index.paid import plan_route, resolve_client

    if injected is not None:
        return injected, None
    if ad_spend.models_off():
        return None, "models_off"
    return resolve_client(vault, plan_route(vault, LLM_ROUTE))  # type: ignore[arg-type]


def _decider_client(vault: Any, injected: Any | None) -> Any | None:
    if injected is not None:
        return injected
    if ad_spend.models_off():
        return None
    from learnloop.ai.routing import ready_client_for_task

    resolved = ready_client_for_task(vault.root, vault.config, DECIDER_ROUTE, allow_env=False)
    return resolved.client if resolved.ready else None


def _store_payloads(repository: Any, owner_key: str, forecaster: str, request: Any, response: Any,
                    now: str, retention_days: int) -> None:
    with repository.atomic():
        connection = repository.connection()
        cutoff = (parse_utc(now) - timedelta(days=int(retention_days))).isoformat().replace("+00:00", "Z")
        store.prune_payloads(connection, before=cutoff)
        store.insert_payload(connection, owner_key=owner_key, forecaster=forecaster, kind="request",
                             content=request, created_at=now)
        if response is not None:
            store.insert_payload(connection, owner_key=owner_key, forecaster=forecaster, kind="response",
                                 content=response, created_at=now)


def _ask_llm(vault: Any, repository: Any, client: Any, *, prompt: str, owner_id: str,
             envelope: Any) -> tuple[float | None, dict[str, Any], str]:
    from learnloop.practice_index.paid import PaidCalls, plan_route

    route = plan_route(vault, LLM_ROUTE, client)  # type: ignore[arg-type]
    subscription = route.billing == "subscription"
    price = vault.config.adaptive_difficulty.price_per_million
    if not subscription and price is None:
        raise SpendLimitExceeded("a metered ad_forecast_llm route needs adaptive_difficulty.price_per_million")
    calls = PaidCalls(route=route, budget=SpendBudget(SpendCaps(max_estimated_usd=None, **_CAPS),
                                                      subscription=subscription),
                      price_per_million=price, repository=repository, owner_kind=ad_spend.FORECAST_OWNER_KIND,
                      owner_id=owner_id)
    with spend_envelopes(envelope):
        answer = calls.call(client, purpose=PURPOSE, prompt=prompt, result_model=ItemForecastV1,
                            output_tokens=route.output_tokens, metadata={"owner_id": owner_id})
    verdict = answer.model_dump(mode="json")
    value = verdict.get("p_correct")
    model = str(calls.last_resolved_model or getattr(client, "model", None) or route.model or "unknown")
    if not isinstance(value, (int, float)) or not 0.0 <= float(value) <= 1.0:
        raise AIInvalidOutput("p_correct outside [0, 1]")
    return float(value), verdict, model


def _ask_decider(vault: Any, repository: Any, client: Any, *, state: Any, owner_id: str,
                 envelope: Any) -> tuple[float, dict[str, Any], str]:
    from learnloop.decider_judgments import ask_decider

    with spend_envelopes(envelope):
        result = ask_decider(client, config=vault.config, repository=repository, task=PURPOSE, state=state,
                             questions=DECIDER_QUESTIONS, owner_id=owner_id, route=DECIDER_ROUTE,
                             question_set_version=DECIDER_QUESTION_SET)
    p = float(result.answers["will_pass"].p_yes)
    return p, {"noul": p, "model": result.model, "id": getattr(result, "response_id", None)}, str(
        result.model or getattr(client, "model", None) or "unknown")


def _receipt(*, key: str, forecaster: str, version: str, scope: str, decision_kind: str, binding_kind: str,
             inputs: Mapping[str, Any], inputs_as_of: str, p: float | None, status: str, received_at: str,
             columns: Mapping[str, Any], model: str | None, request_hash: str) -> ForecastReceipt:
    return ForecastReceipt(
        receipt_key=key, kind=ITEM_UNASSISTED_SUCCESS, forecaster=forecaster,
        forecaster_version=f"{version}:{model or 'unknown'}", scope=scope, decision_kind=decision_kind,
        binding_kind=binding_kind, event=EVENT,
        forecast={"p": None if p is None else round(float(p), 8), "event": EVENT, "p_categories": None,
                  "request_hash": request_hash},
        inputs=dict(inputs), parameters=[], versions={"state": STATE_VERSION, "prompt": version, "model": model},
        inputs_as_of=inputs_as_of, p=p,
        columns={**dict(columns), "status": status, "received_at": received_at},
    )


def _existing(connection: Any, key: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM forecast_receipts WHERE receipt_key = ? LIMIT 1", (key,),
    ).fetchone() is not None


def _verdict_text(p: float) -> str:
    return f"{float(p):.6f}"


def _write(repository: Any, vault: Any, receipt: ForecastReceipt, *, created_at: str, payload_key: str,
           request: Any, response: Any, received: str, judgment: Mapping[str, Any] | None) -> str | None:
    """The forecast's payloads, its receipt and (accepted) its judgment, in one transaction.

    ``repository`` is the claim's fenced repository: nothing lands once the
    job's claim or vault is lost. The judgment (Codex review F8, handoffs §0:
    every paid verdict appends to ``judgment_ledger``) is written only with
    the receipt it belongs to, so a receipt key written once has one
    judgment; a failed or refused forecast has a receipt and no verdict."""

    from dataclasses import replace

    from learnloop.db.stores.judgments import append_judgment

    receipt = replace(receipt, columns={**dict(receipt.columns),
                                        "algorithm_version": vault.config.algorithms.algorithm_version})
    with repository.atomic():
        _store_payloads(repository, payload_key, receipt.forecaster, request, response, received,
                        vault.config.router.payload_retention_days)
        written = record_receipts(repository, [receipt], created_at=created_at)
        receipt_id = written[0] if written else None
        if receipt_id is not None and judgment is not None and receipt.p is not None:
            append_judgment(
                repository.connection(), task=PURPOSE, left_kind=str(judgment["left_kind"]),
                left_id=str(judgment["left_id"]), right_kind="forecaster", right_id=receipt.forecaster,
                judge=str(judgment["judge"]), judge_model=str(judgment.get("model") or "unknown"),
                prompt_version=str(judgment["prompt_version"]), input_hash=str(judgment["input_hash"]),
                verdict=_verdict_text(receipt.p), score=float(receipt.p), created_at=received,
                rationale=json.dumps({"receipt_key": receipt.receipt_key, "receipt_id": receipt_id,
                                      "event": EVENT, "inputs_as_of": receipt.inputs_as_of,
                                      "practice_item_id": receipt.columns.get("practice_item_id"),
                                      "kind": ITEM_UNASSISTED_SUCCESS}, sort_keys=True, default=str),
            )
    return receipt_id


def item_prompt(vault: Any, item: Any) -> str:
    """``llm_v1:item``'s prompt for one revision (the backfill's dry run plans it too)."""

    return render_structured_prompt("Predict how hard an item is for a typical learner", V1_PROMPT_VERSION, {
        "instructions": f"{V1_QUESTION} Return p_correct, your probability strictly between 0 and 1.",
        "state": {"item": item_view(vault, item)},
    })


def forecast_item(vault: Any, repository: Any, item: Any, *, clients: Clients | None = None,
                  clock: Clock | None = None, protected: Any = None, fence: Any = None) -> ForecastOutcome:
    """``llm_v1:item`` for one item revision (once per revision, under its durable claim)."""

    from learnloop.adaptive_difficulty.claims import LeaseLost, claimed, item_forecast_key

    clients = clients or Clients()
    outcome = ForecastOutcome(LLM_V1, "disabled")
    if LLM_V1 not in outside_forecasters(vault.config):
        return outcome
    if guard(vault, repository, protected).covers(item):
        outcome.status = "protected"
        return outcome
    content_hash, _json = item_revision(item)
    key = f"{ITEM_UNASSISTED_SUCCESS}:item:{content_hash}:{LLM_V1}"
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if _existing(connection, key):
            outcome.status = "current"
            return outcome
    client, why = _llm_client(vault, clients.llm)
    if client is None:
        outcome.status, outcome.reason = "unavailable", why
        return outcome
    try:
        with claimed(repository, item_forecast_key(content_hash), fence=fence) as worker:
            if worker is None:
                outcome.status = "busy"
                return outcome
            with closing(connect(repository.sqlite_path, read_only=True)) as connection:
                if _existing(connection, key):
                    outcome.status = "current"
                    return outcome
            _forecast_item(vault, worker, item, client, content_hash=content_hash, key=key, outcome=outcome,
                           clock=clock)
    except LeaseLost:
        outcome.status, outcome.p, outcome.receipt_id = "stale", None, None
    return outcome


def _forecast_item(vault: Any, worker: Any, item: Any, client: Any, *, content_hash: str, key: str,
                   outcome: ForecastOutcome, clock: Clock | None) -> None:
    from learnloop.adaptive_difficulty.claims import LeaseLost

    repository = worker.repository
    issued = utc_now_iso(clock)
    state = {"item": item_view(vault, item)}
    prompt = item_prompt(vault, item)
    request_hash = content_key({"prompt": prompt})
    inputs = {"practice_item_id": str(item.id), "content_hash": content_hash, "state_version": STATE_VERSION,
              "state_hash": content_key(state)}
    envelope = ad_spend.ad_envelope(vault, worker.base, clock=clock)
    status, p, response, model = "ok", None, None, None
    try:
        worker.require_live()
        p, response, model = _ask_llm(vault, repository, client, prompt=prompt, owner_id=content_hash,
                                      envelope=envelope)
    except (AIInterrupted, LeaseLost):
        raise
    except SpendLimitExceeded as exc:
        status, outcome.reason = "refused_spend", str(exc)[:200]
    except (AIProviderUnavailable, AIInvalidOutput, TimeoutError, ValueError) as exc:
        status, outcome.reason = "failed", f"{type(exc).__name__}"
    received = utc_now_iso(clock)
    final_key = key if status == "ok" else f"{key}:{status}:{received}"
    outcome.receipt_id = _write(repository, vault, _receipt(
        key=final_key, forecaster=LLM_V1, version=V1_PROMPT_VERSION, scope="item", decision_kind="item_prepare",
        binding_kind=FIRST_PRESENTATION, inputs=inputs, inputs_as_of=issued, p=p, status=status,
        received_at=received, model=model, request_hash=request_hash,
        columns={"practice_item_id": str(item.id), "learning_object_id": item.learning_object_id,
                 "item_content_hash": content_hash, "decision_ref": content_hash},
    ), created_at=issued, payload_key=final_key, request={"prompt": prompt}, response=response, received=received,
        judgment={"left_kind": "practice_item_revision", "left_id": content_hash, "judge": "llm", "model": model,
                  "prompt_version": V1_PROMPT_VERSION, "input_hash": request_hash})
    outcome.status, outcome.p = status, p


def _presentation(connection: Any, presentation_id: str) -> dict[str, Any] | None:
    row = connection.execute("SELECT * FROM plan_presentations WHERE id = ?", (presentation_id,)).fetchone()
    return dict(row) if row is not None else None


def _incumbent_inputs(connection: Any, presentation_id: str) -> dict[str, Any] | None:
    key = receipt_key("plan_presentation", presentation_id, INCUMBENT)
    row = connection.execute(
        "SELECT p, inputs_json FROM forecast_receipts WHERE receipt_key = ?", (key,),
    ).fetchone()
    if row is None:
        return None
    try:
        inputs = json.loads(row[1] or "{}")
    except (TypeError, ValueError):
        inputs = {}
    return {"p_success": row[0], "mastery_state": inputs.get("mastery_state")}


#: The ``item_forecast_payloads`` owner key of a presentation's frozen
#: ``llm_v3`` request inputs (Codex review F2).
FROZEN_STATE_PREFIX = "ad_llm_v3_state:plan_presentation:"
FROZEN_STATE_FORECASTER = "llm_v3"


def frozen_state_key(presentation_id: str) -> str:
    return f"{FROZEN_STATE_PREFIX}{presentation_id}"


def freeze_presentation_inputs(vault: Any, connection: Any, item: Any, *, presentation_id: str, served_at: str,
                               protected: Any) -> str | None:
    """In the serve transaction: the exact ``llm_v3`` request inputs of one presentation.

    Codex review F2: the background forecasters run after the serve, when an
    earlier attempt may have been regraded or the item edited; reading the
    history or the item then would claim pre-serve inputs it did not have.
    So the serve freezes them: the served revision's item view and the
    learner's history card as the serve saw them (the incumbent's numbers
    from its receipt, just written in this transaction; each earlier
    attempt's grade as it stood). The background job sends exactly this and
    nothing else; a presentation without it (served while the forecasters
    were off, or before AD1) is never forecast. Beside the state (never
    sent) it keeps the :func:`source_identity` of the served revision and of
    each history item the card quotes, which the job revalidates against
    the held-out predicate as it stands when it sends (Codex re-review F11).
    Returns the owner key, or None when no ``llm_v3`` forecaster is on."""

    if not ({LLM_V3_LLM, LLM_V3_DECIDER} & set(outside_forecasters(vault.config))):
        return None
    content_hash, _json = item_revision(item)
    history: list[dict[str, Any]] = []
    state = {"item": item_view(vault, item),
             "learner": history_card(vault, connection, item, served_at=served_at, protected=protected,
                                     incumbent=_incumbent_inputs(connection, presentation_id), identities=history)}
    key = frozen_state_key(presentation_id)
    store.insert_payload(connection, owner_key=key, forecaster=FROZEN_STATE_FORECASTER, kind="request", content={
        "state": state, "state_version": STATE_VERSION, "state_hash": content_key(state),
        "practice_item_id": str(item.id), "learning_object_id": item.learning_object_id,
        "content_hash": content_hash, "inputs_as_of": served_at,
        "protection_identities": {"target": source_identity(item), "history": history},
    }, created_at=served_at)
    return key


def _frozen_inputs(connection: Any, presentation_id: str) -> dict[str, Any] | None:
    rows = store.payloads(connection, [frozen_state_key(presentation_id)])
    for row in rows:
        content = row.get("content")
        if row.get("kind") == "request" and isinstance(content, dict) and isinstance(content.get("state"), dict):
            identities = content.get("protection_identities")
            # Without the identities of what the state quotes, the frozen
            # inputs cannot be revalidated, so they are never sent (F11).
            if not (isinstance(identities, dict) and isinstance(identities.get("target"), dict)
                    and isinstance(identities.get("history"), list)):
                continue
            if content.get("state_hash") == content_key(content["state"]):
                return content
    return None


def _frozen_protected(protection: Any, frozen: Mapping[str, Any]) -> bool:
    """Whether any revision the frozen state quotes is protected now (Codex re-review F11).

    The frozen state was made under the predicate as it stood at the serve; a
    unit marked held out (or an item reserved for an exam) since then must
    not reach a model through it. Each quoted revision is judged by its id
    and by its own source references as frozen, so a revision since replaced
    by ordinary practice is still judged by what the state quotes."""

    identities = frozen["protection_identities"]
    return any(protection.covers_identity(identity)
               for identity in [identities["target"], *identities["history"]])


def forecast_presentation(vault: Any, repository: Any, presentation_id: str, *, clients: Clients | None = None,
                          clock: Clock | None = None, fence: Any = None) -> list[ForecastOutcome]:
    """``llm_v3:llm`` and ``llm_v3:decider`` for one plan presentation, from its frozen serve inputs.

    The request is exactly what :func:`freeze_presentation_inputs` stored in
    the serve transaction (Codex review F2), so ``inputs_as_of`` = the serve
    is true. Without them (``no_frozen_inputs``) nothing is sent. Under the
    presentation's durable claim (Codex review F5, F6)."""

    from learnloop.adaptive_difficulty.claims import LeaseLost, claimed, presentation_key

    clients = clients or Clients()
    chosen = [name for name in (LLM_V3_LLM, LLM_V3_DECIDER) if name in outside_forecasters(vault.config)]
    if not chosen:
        return []
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        presentation = _presentation(connection, presentation_id)
        if presentation is None:
            return [ForecastOutcome(name, "not_found") for name in chosen]
        frozen = _frozen_inputs(connection, presentation_id)
        pending = [name for name in chosen
                   if not _existing(connection, receipt_key("plan_presentation", presentation_id, name))]
    if not pending:
        return []
    if frozen is None:
        return [ForecastOutcome(name, "no_frozen_inputs") for name in pending]
    item_id = str(presentation["practice_item_id"])
    item = vault.practice_items.get(item_id)
    outcomes: list[ForecastOutcome] = []
    try:
        with claimed(repository, presentation_key(presentation_id), fence=fence) as worker:
            if worker is None:
                return [ForecastOutcome(name, "busy") for name in pending]
            with closing(connect(repository.sqlite_path, read_only=True)) as connection:
                pending = [name for name in pending
                           if not _existing(connection, receipt_key("plan_presentation", presentation_id, name))]
            # Revalidated under the claim, just before sending (Codex
            # re-review F11): the current item, and every revision the frozen
            # state quotes, against the predicate as it stands now.
            protection = guard(vault, repository)
            if (item_id in protection or (item is not None and protection.covers(item))
                    or _frozen_protected(protection, frozen)):
                return [ForecastOutcome(name, "protected") for name in pending]
            for name in pending:
                outcomes.append(_forecast_one(vault, worker, name, presentation, frozen, clients=clients,
                                              clock=clock))
    except LeaseLost:
        done = {outcome.forecaster for outcome in outcomes if outcome.status != "stale"}
        outcomes = [outcome for outcome in outcomes if outcome.forecaster in done]
        outcomes += [ForecastOutcome(name, "stale") for name in pending if name not in done]
    return outcomes


def _forecast_one(vault: Any, worker: Any, name: str, presentation: Mapping[str, Any], frozen: Mapping[str, Any], *,
                  clients: Clients, clock: Clock | None) -> ForecastOutcome:
    from learnloop.adaptive_difficulty.claims import LeaseLost

    repository = worker.repository
    presentation_id = str(presentation["id"])
    served_at = str(presentation["served_at"])
    state = frozen["state"]
    inputs = {"practice_item_id": str(frozen["practice_item_id"]), "plan_presentation_id": presentation_id,
              "content_hash": frozen["content_hash"], "state_version": frozen.get("state_version", STATE_VERSION),
              "state_hash": frozen["state_hash"], "frozen_inputs": frozen_state_key(presentation_id)}
    envelope = ad_spend.ad_envelope(vault, worker.base, clock=clock)
    outcome = ForecastOutcome(name, "ok")
    key = receipt_key("plan_presentation", presentation_id, name)
    issued = utc_now_iso(clock)
    p, response, model = None, None, None
    status = "ok"
    if name == LLM_V3_LLM:
        client, why = _llm_client(vault, clients.llm)
        prompt = render_structured_prompt("Predict the learner's next answer", V3_PROMPT_VERSION, {
            "instructions": (f"{V3_QUESTION} Judge only from the state: the item and the learner's earlier "
                             "work, which all happened before this item was shown. Return p_correct, your "
                             "probability strictly between 0 and 1 that the answer will be fully or almost fully "
                             "correct without help."),
            "state": state,
        })
        request: Any = {"prompt": prompt}
        if client is None:
            return ForecastOutcome(name, "unavailable", reason=why)
    else:
        client = _decider_client(vault, clients.decider)
        request = {"state": state, "questions": {key_: q.wire() for key_, q in DECIDER_QUESTIONS.items()}}
        if client is None:
            return ForecastOutcome(name, "unavailable", reason="no Decider")
    try:
        worker.require_live()
        if name == LLM_V3_LLM:
            p, response, model = _ask_llm(vault, repository, client, prompt=request["prompt"],
                                          owner_id=presentation_id, envelope=envelope)
        else:
            p, response, model = _ask_decider(vault, repository, client, state=state, owner_id=presentation_id,
                                              envelope=envelope)
    except (AIInterrupted, LeaseLost):
        raise
    except SpendLimitExceeded as exc:
        status, outcome.reason = "refused_spend", str(exc)[:200]
    except Exception as exc:  # noqa: BLE001 - a failed forecaster is a failed receipt, never a crash
        status, outcome.reason = "failed", type(exc).__name__
    received = utc_now_iso(clock)
    final_key = key if status == "ok" else f"{key}:{status}:{received}"
    version = V3_PROMPT_VERSION if name == LLM_V3_LLM else DECIDER_QUESTION_SET
    request_hash = content_key(request)
    outcome.receipt_id = _write(repository, vault, _receipt(
        key=final_key, forecaster=name, version=version,
        scope="presentation", decision_kind="serve", binding_kind="plan_presentation", inputs=inputs,
        inputs_as_of=served_at, p=p, status=status, received_at=received, model=model,
        request_hash=request_hash,
        columns={"practice_item_id": str(frozen["practice_item_id"]),
                 "learning_object_id": frozen.get("learning_object_id"),
                 "plan_presentation_id": presentation_id, "decision_ref": presentation_id},
    ), created_at=max(issued, served_at), payload_key=final_key, request=request, response=response,
        received=received,
        judgment={"left_kind": "plan_presentation", "left_id": presentation_id,
                  "judge": "llm" if name == LLM_V3_LLM else "decider", "model": model,
                  "prompt_version": version, "input_hash": request_hash})
    outcome.status, outcome.p = status, p
    return outcome


__all__ = [
    "Clients",
    "DECIDER_QUESTIONS",
    "ForecastOutcome",
    "ItemForecastV1",
    "forecast_item",
    "forecast_presentation",
    "freeze_presentation_inputs",
    "frozen_state_key",
    "history_card",
    "item_prompt",
    "item_view",
    "source_identity",
]
