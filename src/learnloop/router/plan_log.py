"""Router R1: daily-plan block decisions as ``plan_block`` router decisions.

Owner decision 2026-10-12 (R1 merged after daily-loop DL1): DL1's engine hands
every block decision and chooser stop ``_boundary`` makes to the loggers
registered through ``register_plan_decision_logger``, on the block's own
connection inside its transaction. :func:`log_plan_block_decision` is R1's
logger. It writes one append-only ``router_decisions`` row of kind
``plan_block`` and returns its id, which DL1 stores as the block's
``decision_ref`` (on its row and its ``block_chosen`` receipt), so plan
decisions get router decision ids.

The row (spec_action_router_v1 §9; R1's DL1 checklist):

* **candidates**: the source's block candidates (lane, items, learning
  objects, minutes, planner value) with their feasibility, plus
  ``continue_current`` (never feasible: decisions happen at block boundaries)
  and ``stop_for_today`` (feasible when the chooser may stop). A block of
  requested or follow-up items only, placed when no candidate was feasible, is
  its own candidate (``forced:<origin>``).
* **chosen**: the chooser's choice with its propensity. ``lane_quota_v1`` is
  deterministic (1). A block of the learner's own requests is a learner pick
  (no propensity); follow-ups the rules place are deterministic. A stop is
  ``stop_for_today``. A fallback names the chooser's refused pick in
  ``fallback`` (``Decision.fallback_from``) and its reason in the detail.
  A pick from the full list (DL1's ``learner_pick``: a one-item block outside
  the source's candidates) is chosen as ``pick:<item>``, a learner pick with
  no propensity (R2a, G9).
* **the action** an outcome follows is the block's first planned item
  (forced items first), attempted at or after the decision in its session.

Router R2a (mvp-0.23, plan_router_r2_v1 §3.2): the router's chooser never
writes rows. It hands its record to the container (``BlockChoice.router_record``),
which passes it here with the decision, so the row and its payload commit or
roll back with the block. With a record the row carries the chooser's ``mode``
and ``policy`` (``staged`` / ``staged_v1``), the staged controller decision it
names, the learner-state card's hash (``card_hash``), and the card itself is
stored in ``router_decision_payloads`` (pruned after
``router.payload_retention_days``). Every item the staged frame refused is
logged under ``exclusions_json.named.<constraint key>``, and each block
candidate keeps the frame's annotations (its ladder rungs, whether serving it
is reversible, its reason code).

Not logged: a decision whose chooser already set its own ``decision_ref``
(R1's compatibility rule; R2a's chooser never does), and every decision while
``router.log_decisions`` is off. The insert runs in its own savepoint
(``append_router_decision``): a row the ledger refuses rolls back alone with a
warning and the plan's block still commits, without a ``decision_ref``.

This module is part of the router leaf: it reads the decision as plain data
and never imports the plan, the scheduler or the substrate.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import timedelta
import hashlib
import json
from typing import Any

from learnloop.clock import parse_utc, utc_now_iso
from learnloop.db.stores.router import (
    ROUTER_LOG_VERSION,
    append_router_decision,
    append_router_payload,
    prune_router_payloads,
)
from learnloop.ids import new_ulid

DECISION_KIND = "plan_block"
SURFACE = "daily_plan"
MODE = "daily_plan"
CONTINUE_REF = "continue_current"
STOP_REF = "stop_for_today"
#: A learner pick's candidate id (``pick:<practice item>``, DL1's learner_pick).
PICK_PREFIX = "pick:"
#: DL1's rule 2: a chooser whose choice cannot stand falls back to lane quota.
FALLBACK_POLICY = "lane_quota_v1"
#: A chooser's choices are probabilities within this of 1 are deterministic.
_DETERMINISTIC_TOLERANCE = 1e-12


def _dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def _hash(value: Any) -> str:
    return hashlib.sha256(_dumps(value).encode("utf-8")).hexdigest()


def _logging_enabled(config: Any) -> bool:
    if config is None:
        # A decision with no configuration (a caller outside the engine): the
        # modelled default, logging on.
        return True
    router = getattr(config, "router", None)
    return bool(getattr(router, "log_decisions", True))


def _ledger_present(connection: Any) -> bool:
    return (
        connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='router_decisions'"
        ).fetchone()
        is not None
    )


def _probability(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def build_plan_block_decision(decision: Any) -> dict[str, Any]:
    """The ``router_decisions`` row for one plan block decision (pure)."""

    detail: Mapping[str, Any] = decision.detail
    router_record: Mapping[str, Any] = getattr(decision, "router_record", None) or {}
    frame: Mapping[str, Any] = detail.get("staged_frame") or {}
    config = getattr(decision, "config", None)
    algorithms = getattr(config, "algorithms", None)
    algorithm_version = str(getattr(algorithms, "algorithm_version", None) or "unknown")
    stop = bool(decision.stop)
    feasible_ids = {str(value) for value in detail.get("feasible_ids") or ()}
    choice_id = str(detail.get("candidate_id") or "")
    chosen_by = str(getattr(decision, "chosen_by", None) or detail.get("chosen_by") or "lane_quota")
    forced = [dict(entry) for entry in detail.get("forced") or ()]
    items = [(str(item), str(lo)) for item, lo in (getattr(decision, "items", ()) or ())]

    candidate_rows = [dict(row) for row in detail.get("candidate_set") or ()]
    learner_pick = chosen_by == "learner_pick"
    picked = learner_pick and choice_id.startswith(PICK_PREFIX) and not stop
    if stop:
        chosen_ref = STOP_REF
    elif choice_id in feasible_ids:
        chosen_ref = choice_id
    elif picked:
        # R2a (G9): a pick from the full list is its own one-item block, the
        # learner's choice outside the source's candidates.
        chosen_ref = choice_id
    else:
        # Nothing feasible: the block is the requested or follow-up items the
        # container places whatever is chosen (DL1's _boundary).
        origin = str(forced[0].get("origin")) if forced else "forced"
        chosen_ref = f"forced:{origin}"
    if learner_pick:
        propensity, propensity_kind = None, "none"
    else:
        raw = _probability(detail.get("propensity"))
        if chosen_ref.startswith("forced:") or raw is None or raw >= 1.0 - _DETERMINISTIC_TOLERANCE:
            # The rules placed it (follow-ups), or the chooser is deterministic.
            propensity, propensity_kind = 1.0, "deterministic"
        else:
            propensity, propensity_kind = raw, "exact"

    mixture: Mapping[str, Any] = router_record.get("mixture") or {}
    pi: Mapping[str, Any] = mixture.get("pi") or {}

    def candidate_propensity(ref: str) -> float | None:
        if propensity_kind == "none":
            return None
        if ref == chosen_ref:
            return propensity
        if pi and not detail.get("fallback"):
            # R2b: the mixture's exact distribution; a candidate outside its
            # top-k support (or irreversible) has propensity 0.
            value = pi.get(ref)
            return float(value) if value is not None else 0.0
        # A deterministic choice puts no mass elsewhere; a sampled chooser that
        # logs no distribution of its own leaves the others unknown.
        return 0.0 if propensity_kind == "deterministic" else None

    candidates: list[dict[str, Any]] = []
    for row in candidate_rows:
        ref = str(row.get("candidate_id"))
        entry = {
            "ref": ref,
            "kind": "block",
            "lane": row.get("lane"),
            "item_ids": list(row.get("item_ids") or ()),
            "learning_object_ids": list(row.get("learning_object_ids") or ()),
            "reading": row.get("reading"),
            "est_minutes": row.get("est_minutes"),
            "planner_value": row.get("planner_value"),
            "feasible": ref in feasible_ids,
            "propensity": candidate_propensity(ref),
        }
        if row.get("annotations"):
            # R2a: the staged frame's annotations (ladder rungs, reversibility,
            # reason code).
            entry["annotations"] = dict(row["annotations"])
        candidates.append(entry)
    if picked:
        candidates.append(
            {
                "ref": chosen_ref,
                "kind": "pick",
                "item_ids": [item for item, _lo in items],
                "learning_object_ids": [lo for _item, lo in items],
                "feasible": True,
                "propensity": candidate_propensity(chosen_ref),
            }
        )
    if chosen_ref.startswith("forced:"):
        candidates.append(
            {
                "ref": chosen_ref,
                "kind": "forced",
                "item_ids": [entry.get("practice_item_id") for entry in forced],
                "feasible": True,
                "propensity": candidate_propensity(chosen_ref),
            }
        )
    candidates.append({"ref": CONTINUE_REF, "kind": "continue", "feasible": False, "propensity": candidate_propensity(CONTINUE_REF)})
    candidates.append(
        {
            "ref": STOP_REF,
            "kind": "stop",
            "feasible": bool(detail.get("stop_offered")) or stop,
            "propensity": candidate_propensity(STOP_REF),
        }
    )

    chosen_item, chosen_lo = (items[0] if items and not stop else (None, None))
    if learner_pick:
        policy = "learner"
    elif detail.get("fallback"):
        policy = FALLBACK_POLICY
    else:
        policy = str(router_record.get("policy") or detail.get("chooser") or "unknown")
    excluded = sorted(
        str(row.get("candidate_id")) for row in candidate_rows if str(row.get("candidate_id")) not in feasible_ids
    )
    named: dict[str, list[str]] = {"infeasible": excluded} if excluded else {}
    for item_id, reasons in sorted((frame.get("refused") or {}).items()):
        # R2a: an item a named hard constraint refused never reached packing.
        for reason in reasons or ():
            key = str(reason.get("constraint_key") or "unknown")
            ids = named.setdefault(key, [])
            if item_id not in ids:
                ids.append(str(item_id))
    exclusions = {"named": {key: sorted(ids) for key, ids in sorted(named.items())}} if named else {}
    inputs = {
        "plan_id": decision.plan_id,
        "plan_kind": decision.plan_kind,
        "local_date": decision.local_date,
        "candidates": candidates,
        "state": detail.get("state"),
        "redistribution": detail.get("redistribution"),
        "forced": forced,
        "source": detail.get("source"),
        "chooser": detail.get("chooser"),
        "algorithm_version": algorithm_version,
        **({"staged_frame_snapshot": frame.get("snapshot_hash")} if frame else {}),
        **({"card_hash": router_record.get("card_hash")} if router_record.get("card_hash") else {}),
    }
    row_detail = {
        "block_id": decision.block_id,
        "plan_id": decision.plan_id,
        "plan_kind": decision.plan_kind,
        "local_date": decision.local_date,
        "stop": stop,
        "chosen_by": chosen_by,
        "chooser_choice": choice_id or None,
        "source": detail.get("source"),
        "chooser": detail.get("chooser"),
        "fallback": bool(detail.get("fallback")),
        "fallback_from": detail.get("fallback_from"),
        "why": detail.get("why"),
        "why_kind": detail.get("why_kind"),
        "fallback_reason": detail.get("fallback_reason"),
        "stop_reason": detail.get("stop_reason"),
        "items": [{"practice_item_id": item, "learning_object_id": lo} for item, lo in items],
        "forced": forced,
        "state": detail.get("state"),
        "redistribution": detail.get("redistribution"),
    }
    if detail.get("voi_decisions"):
        # mvp-0.21: value-of-information stop/continue decisions (due project
        # probes) with their forecasts; absent below it.
        row_detail["voi_decisions"] = list(detail["voi_decisions"])
    if detail.get("router"):
        row_detail["router"] = dict(detail["router"])
    if mixture:
        # R2b: the draw's own record (support, staged pick, effective weights,
        # epsilon, drawn component, uniforms), each model's status, latency,
        # cost and error, the sensors' source, and similar decisions (R2c).
        row_detail["mixture"] = {key: value for key, value in mixture.items() if key != "pi"}
    if frame:
        # The frame's snapshot and constraint manifest; its refusals are the
        # row's named exclusions.
        row_detail["staged_frame"] = {
            key: frame.get(key) for key in ("source", "snapshot_hash", "manifest_hash", "evaluated_items", "error")
            if frame.get(key) is not None
        }
        row_detail["staged_frame"]["refused"] = {
            str(item_id): [
                {key: reason.get(key) for key in ("constraint_key", "constraint_version", "reason", "kind")}
                for reason in reasons or ()
            ]
            for item_id, reasons in sorted((frame.get("refused") or {}).items())
        }
    sampled = bool(mixture) and propensity_kind == "exact" and not detail.get("fallback")
    container_fallback = (
        str(detail.get("fallback_from")) if detail.get("fallback") and detail.get("fallback_from") else None
    )
    return {
        "id": str(router_record.get("decision_id") or new_ulid()),
        "receipt_key": f"{DECISION_KIND}:{decision.block_id}",
        "decision_kind": DECISION_KIND,
        "surface": SURFACE,
        "mode": str(router_record.get("mode") or MODE),
        "policy": policy,
        "algorithm_version": algorithm_version,
        "log_version": ROUTER_LOG_VERSION,
        "session_id": decision.session_id,
        "parent_decision_id": None,
        "scheduler_slate_id": None,
        "controller_decision_id": router_record.get("controller_decision_id"),
        "snapshot_hash": _hash(inputs),
        "design": router_record.get("design") if sampled else None,
        "seed": router_record.get("seed") if sampled else None,
        **_model_columns(router_record),
        "candidates_json": _dumps(candidates),
        "exclusions_json": _dumps(exclusions),
        "candidate_count": len(candidates),
        "chosen_ref": chosen_ref,
        "chosen_practice_item_id": chosen_item,
        "chosen_learning_object_id": chosen_lo,
        "chosen_scheduler_candidate_id": None,
        "propensity": propensity,
        "propensity_kind": propensity_kind,
        "learner_pick": 1 if learner_pick else 0,
        # R1: the chooser's refused pick on a container fallback; R2b: the
        # models whose weight went to the rule (``decider`` | ``llm`` | ``both``).
        "fallback": container_fallback or router_record.get("fallback"),
        "card_hash": router_record.get("card_hash"),
        "detail_json": _dumps(row_detail),
        "created_at": getattr(decision, "decided_at", None) or utc_now_iso(),
    }


def _model_columns(record: Mapping[str, Any]) -> dict[str, Any]:
    """The R2b columns (reserved since R1, migration 181) from a router record."""

    def dumped(key: str) -> str | None:
        value = record.get(key)
        return _dumps(value) if value is not None else None

    latency = record.get("latency_ms")
    cost = record.get("cost_usd")
    return {
        "mixture_weights_json": dumped("mixture_weights"),
        "model_distributions_json": dumped("model_distributions"),
        "sensor_answers_json": dumped("sensor_answers"),
        "question_set_version": record.get("question_set_version"),
        "model_ids_json": dumped("model_ids"),
        "similar_decision_ids_json": dumped("similar_decision_ids"),
        "latency_ms": int(latency) if isinstance(latency, (int, float)) and not isinstance(latency, bool) else None,
        "cost_usd": float(cost) if isinstance(cost, (int, float)) and not isinstance(cost, bool) else 0.0,
    }


#: R2b: the payload kinds the models' requests and raw answers are stored as.
MODEL_PAYLOAD_KINDS = ("decider_request", "decider_response", "llm_request", "llm_response")


def _store_payloads(connection: Any, record: Mapping[str, Any], row: Mapping[str, Any]) -> None:
    """R2b: both models' requests and raw answers, beside the decision (own savepoints)."""

    for kind in MODEL_PAYLOAD_KINDS:
        payload = (record.get("payloads") or {}).get(kind)
        if not isinstance(payload, Mapping):
            continue
        content_json = payload.get("json")
        content_text = payload.get("text")
        append_router_payload(
            connection,
            {
                "id": new_ulid(),
                "decision_id": row["id"],
                "kind": kind,
                "format_version": str(payload.get("format_version") or "unknown"),
                "content_hash": _hash({"json": content_json, "text": content_text}),
                "content_json": _dumps(content_json) if content_json is not None else None,
                "content_text": content_text,
                "created_at": row["created_at"],
            },
        )


def _store_context_vector(connection: Any, record: Mapping[str, Any], row: Mapping[str, Any]) -> None:
    """R2c: the decision's ``decision/context`` vector (computed at prefetch,
    written after the decision, in its own savepoint; a cache replay never reads)."""

    vector = record.get("context_vector")
    if not isinstance(vector, Mapping) or vector.get("vector") is None:
        return
    from learnloop.db.stores.embedding_vectors import put_vector

    connection.execute("SAVEPOINT router_context_vector")
    try:
        put_vector(
            connection,
            record_kind=str(vector["record_kind"]),
            record_id=str(row["id"]),
            field=str(vector["field"]),
            content_hash=str(vector["content_hash"]),
            model_id=str(vector["model_id"]),
            task_prefix=str(vector["task_prefix"]),
            vector=vector["vector"],
            created_at=row["created_at"],
        )
    except Exception:  # noqa: BLE001 - a cache write never blocks the plan
        connection.execute("ROLLBACK TO router_context_vector")
        connection.execute("RELEASE router_context_vector")
        import logging

        logging.getLogger(__name__).warning("router R2c: the decision's context vector was not stored", exc_info=True)
        return
    connection.execute("RELEASE router_context_vector")


def _store_card(connection: Any, decision: Any, row: Mapping[str, Any]) -> None:
    """R2a: the learner-state card the chooser built, beside its decision.

    Written in the block's transaction (its own savepoint); payloads older than
    ``router.payload_retention_days`` are pruned on the way (the hash stays on
    every row). R2b adds both models' requests and raw answers; R2c the
    decision's context vector."""

    record: Mapping[str, Any] = getattr(decision, "router_record", None) or {}
    card = record.get("card")
    if isinstance(card, Mapping):
        append_router_payload(
            connection,
            {
                "id": new_ulid(),
                "decision_id": row["id"],
                "kind": "card",
                "format_version": str(card.get("card_version") or "unknown"),
                "content_hash": str(record.get("card_hash") or card.get("card_hash") or ""),
                "content_json": _dumps(card.get("json")),
                "content_text": card.get("text"),
                "created_at": row["created_at"],
            },
        )
    _store_payloads(connection, record, row)
    _store_context_vector(connection, record, row)
    if not isinstance(card, Mapping) and not record.get("payloads"):
        return
    router_config = getattr(getattr(decision, "config", None), "router", None)
    days = getattr(router_config, "payload_retention_days", None)
    created = parse_utc(str(row["created_at"]))
    if days and created is not None:
        cutoff = (created - timedelta(days=int(days))).strftime("%Y-%m-%dT%H:%M:%SZ")
        try:
            prune_router_payloads(connection, before=cutoff)
        except Exception:  # noqa: BLE001 - pruning never blocks the plan
            import logging

            logging.getLogger(__name__).warning("router payload pruning failed", exc_info=True)


def log_plan_block_decision(connection: Any, decision: Any) -> str | None:
    """DL1's plan-decision logger: write the ``plan_block`` row, return its id.

    ``None`` (nothing written) while ``router.log_decisions`` is off, when the
    chooser already logged its own decision, when the ledger is absent, or when
    the ledger refuses the row (reported as a warning by the store).
    """

    if getattr(decision, "kind", DECISION_KIND) != DECISION_KIND:
        return None
    if not _logging_enabled(getattr(decision, "config", None)):
        return None
    if (decision.detail or {}).get("decision_ref"):
        return None
    if not _ledger_present(connection):
        return None
    row = build_plan_block_decision(decision)
    if append_router_decision(connection, row):
        _store_card(connection, decision, row)
        return str(row["id"])
    return None


# -- router R2c: a mid-block follow-up's restraint decision -----------------------------

INTERRUPT_KIND = "plan_interrupt"
INSERT_REF = "insert_now"
DECLINE_REF = "decline"


def build_plan_interrupt_decision(decision: Mapping[str, Any]) -> dict[str, Any]:
    """The ``router_decisions`` row of one ``plan_interrupt`` decision (pure).

    ``decision`` holds the plan and its current block, the follow-up item,
    the chosen ref (``insert_now``: the follow-up joins the current block now;
    ``continue_current``: it waits and opens the next block; ``decline``: a
    hard constraint refused it), the choice's propensity, the constraint
    engine's named refusals, whether waiting was feasible (``wait_feasible``:
    the boundary keeps room for it; Codex review F8) and the router record
    (the mixture's draw, the card, the models' answers and payloads)."""

    record: Mapping[str, Any] = decision.get("router_record") or {}
    mixture: Mapping[str, Any] = record.get("mixture") or {}
    pi: Mapping[str, Any] = mixture.get("pi") or {}
    followup: Mapping[str, Any] = decision["followup"]
    chosen_ref = str(decision["chosen_ref"])
    refused: Mapping[str, Any] = decision.get("refused") or {}
    raw = _probability(decision.get("propensity"))
    if raw is None or raw >= 1.0 - _DETERMINISTIC_TOLERANCE:
        propensity, propensity_kind = 1.0, "deterministic"
    else:
        propensity, propensity_kind = raw, "exact"
    # Waiting is infeasible when the boundary would have no room for the
    # follow-up after the current block (Codex review F8): it joins now.
    wait_feasible = bool(decision.get("wait_feasible", True))
    feasible = {INSERT_REF: not refused, CONTINUE_REF: not refused and wait_feasible, DECLINE_REF: bool(refused)}

    def candidate_propensity(ref: str) -> float:
        if ref == chosen_ref:
            return propensity
        if pi:
            return float(pi.get(ref, 0.0))
        return 0.0

    item_id = str(followup["practice_item_id"])
    candidates = [
        {"ref": INSERT_REF, "kind": "insert", "item_ids": [item_id], "feasible": feasible[INSERT_REF],
         "propensity": candidate_propensity(INSERT_REF)},
        {"ref": CONTINUE_REF, "kind": "continue", "item_ids": [], "feasible": feasible[CONTINUE_REF],
         "propensity": candidate_propensity(CONTINUE_REF)},
        {"ref": DECLINE_REF, "kind": "decline", "item_ids": [], "feasible": feasible[DECLINE_REF],
         "propensity": candidate_propensity(DECLINE_REF)},
    ]
    named: dict[str, list[str]] = {}
    for reason in refused.get("reasons") or ():
        named.setdefault(str(reason.get("constraint_key") or "unknown"), []).append(item_id)
    exclusions = {"named": {key: sorted(set(ids)) for key, ids in sorted(named.items())}} if named else {}
    config = decision.get("config")
    algorithms = getattr(config, "algorithms", None)
    algorithm_version = str(getattr(algorithms, "algorithm_version", None) or "unknown")
    inputs = {
        "plan_id": decision.get("plan_id"),
        "block_id": decision.get("block_id"),
        "followup": dict(followup),
        "candidates": candidates,
        "algorithm_version": algorithm_version,
        **({"card_hash": record.get("card_hash")} if record.get("card_hash") else {}),
    }
    detail = {
        "plan_id": decision.get("plan_id"),
        "plan_kind": decision.get("plan_kind"),
        "local_date": decision.get("local_date"),
        "block_id": decision.get("block_id"),
        "followup": dict(followup),
        "why": decision.get("why"),
        **({} if wait_feasible or refused else {"wait": {"feasible": False, "reason": "no_room_after_block"}}),
        "refused": [
            {key: reason.get(key) for key in ("constraint_key", "constraint_version", "reason", "kind")}
            for reason in refused.get("reasons") or ()
        ],
        **({"router": dict(decision["summary"])} if decision.get("summary") else {}),
        **({"mixture": {key: value for key, value in mixture.items() if key != "pi"}} if mixture else {}),
    }
    sampled = bool(mixture) and propensity_kind == "exact"
    return {
        "id": str(record.get("decision_id") or new_ulid()),
        "receipt_key": f"{INTERRUPT_KIND}:{decision.get('block_id')}:{item_id}",
        "decision_kind": INTERRUPT_KIND,
        "surface": SURFACE,
        "mode": str(record.get("mode") or "mixture"),
        "policy": str(record.get("policy") or "staged_v1"),
        "algorithm_version": algorithm_version,
        "log_version": ROUTER_LOG_VERSION,
        "session_id": decision.get("session_id"),
        "parent_decision_id": decision.get("parent_decision_id"),
        "scheduler_slate_id": None,
        "controller_decision_id": None,
        "snapshot_hash": _hash(inputs),
        "design": record.get("design") if sampled else None,
        "seed": record.get("seed") if sampled else None,
        **_model_columns(record),
        "candidates_json": _dumps(candidates),
        "exclusions_json": _dumps(exclusions),
        "candidate_count": len(candidates),
        "chosen_ref": chosen_ref,
        # The action an outcome follows: the follow-up served now. Waiting has
        # no action of its own here (the next block's decision serves it).
        "chosen_practice_item_id": item_id if chosen_ref == INSERT_REF else None,
        "chosen_learning_object_id": str(followup.get("learning_object_id")) if chosen_ref == INSERT_REF else None,
        "chosen_scheduler_candidate_id": None,
        "propensity": propensity,
        "propensity_kind": propensity_kind,
        "learner_pick": 0,
        "fallback": record.get("fallback"),
        "card_hash": record.get("card_hash"),
        "detail_json": _dumps(detail),
        "created_at": decision.get("decided_at") or utc_now_iso(),
    }


def log_plan_interrupt_decision(connection: Any, decision: Mapping[str, Any]) -> str | None:
    """Write one ``plan_interrupt`` row on the caller's transaction; returns its id.

    None while ``router.log_decisions`` is off, when the ledger is absent, or
    when the ledger refuses the row (a warning). The card and the models'
    payloads are stored beside it."""

    if not _logging_enabled(decision.get("config")):
        return None
    if not _ledger_present(connection):
        return None
    row = build_plan_interrupt_decision(decision)
    if not append_router_decision(connection, row):
        return None

    class _Carrier:
        router_record = decision.get("router_record") or {}
        config = decision.get("config")

    _store_card(connection, _Carrier(), row)
    return str(row["id"])


__all__ = [
    "DECISION_KIND",
    "DECLINE_REF",
    "INSERT_REF",
    "INTERRUPT_KIND",
    "MODEL_PAYLOAD_KINDS",
    "build_plan_block_decision",
    "build_plan_interrupt_decision",
    "log_plan_block_decision",
    "log_plan_interrupt_decision",
]
