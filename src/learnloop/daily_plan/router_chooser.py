"""Router R2b + R2c: the mixture chooser and the restraint gate on Today.

docs/specs/plan_router_r2_v1.md §3.2-§3.5, owner decisions 2026-10-13.

**The block decision** (:class:`RouterChooser`, ``router_mixture_v1``). At a
plan boundary it starts from R2a's staged rule (``staged_v1``: DL1's
``lane_quota_v1`` over the staged-feasible candidates, owner Q1), then:

1. **Irreversible first** (G2). When the rule's pick is irreversible (it holds
   an open cold check or a reserved surface), it is chosen deterministically
   and no model is asked.
2. **Top-k reversible** (``router.k``, D3), in a deterministic order: the
   rule's pick, then each lane's best remaining candidate in lane-quota order,
   then the rest by the lane-quota key, then ``stop for today`` when the plan
   offers it. Feasible candidates beyond k have propensity 0 (R3 evaluates on
   the top-k support). ``router.ties_only`` keeps only the rule's lane.
3. **Readiness.** With no model set up, the rule chooses deterministically
   (``decided_by = not_ready``); nothing is explored without a model.
4. **The models** (prefetched, :mod:`learnloop.daily_plan.router_runtime`):
   the Decider's and the LLM's distributions over the options, the sensors
   (R2c, logged only), the similar decisions behind the inclusion coin (R2c).
   A read that finds them out raises :class:`DecisionPending` (nothing
   decided); a serving step waits up to ``router.timeout_seconds`` and lets
   the rule take any missing model's share.
5. **The draw** (:mod:`learnloop.router.mixture`): exact propensities, seeded
   by the boundary key and the decision's id, every option at
   ``router.epsilon_min`` or above, the floor kept on a full fallback (Q7).
6. **The why** (:mod:`learnloop.router.why`): by the component that drew.

The chooser writes nothing: its record (the card, the draw, both models'
answers, payloads, the context vector) rides on ``BlockChoice.router_record``
to the ``plan_block`` logger, in the block's own transaction.

**The restraint** (:class:`RestraintGate`, R2c; ``plan_interrupt``). A
mid-block follow-up the follow-up rules would place now (DL1's
``_insert_followups``) is first checked by the P4 constraint engine (R2a open
question 2: a refused follow-up is declined, logged with its named reason),
then decided by the same mixture over ``insert_now`` (the rule's choice) and
``continue_current`` (wait: it opens the next block), from each model's
``intervene_now`` P(yes). No hand-set 0.3 threshold (Q7): the models can make
waiting likelier, never force an interruption the rules would not place (G4).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
import hashlib
import json
import logging
import threading
import time
from typing import Any

from learnloop.daily_plan.chooser import LaneQuotaChooser, unspent_share
from learnloop.daily_plan.staged_frame import CardBuilder, StagedChooser
from learnloop.daily_plan.types import (
    CONTINUE_CURRENT,
    LANES,
    STOP_FOR_TODAY,
    STOP_OFFER_MINUTES,
    BlockCandidate,
    BlockChoice,
    DecisionPending,
    PlanState,
)
from learnloop.daily_plan.router_runtime import (
    ANSWERED,
    DECIDER,
    INVALID,
    LLM,
    NOT_READY,
    RECEIPT_OWNER,
    ComponentResult,
    Prefetch,
    RouterRuntime,
    call_decider,
    call_llm,
)
from learnloop.ids import new_ulid
from learnloop.router import mixture as mx
from learnloop.router import requests as rq
from learnloop.router import why as router_why

LOG = logging.getLogger(__name__)

CHOOSER_NAME = mx.POLICY
MODE = "mixture"
KEY_VERSION = 1
INSERT_NOW = "insert_now"


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def router_settings(config: Any) -> dict[str, Any]:
    """The router settings a decision's key and record carry."""

    router = config.router
    return {
        "weights": router.weights.model_dump(),
        "k": int(router.k),
        "epsilon_min": float(router.epsilon_min),
        "ties_only": bool(router.ties_only),
        "sensors": bool(router.sensors),
        "similar_decisions": bool(router.similar_decisions) and bool(config.embedding.enabled),
        "similar_k": int(router.similar_k),
        "similar_include_rate": float(router.similar_include_rate),
    }


def _latest_attempt(repository: Any) -> str | None:
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT id FROM practice_attempts ORDER BY created_at DESC, id DESC LIMIT 1"
        ).fetchone()
    return str(row["id"]) if row is not None else None


def support_order(
    state: PlanState, candidates: Sequence[BlockCandidate], staged_id: str, *, k: int, stop_offered: bool,
    ties_only: bool,
) -> list[str]:
    """The top-k options in the deterministic order of plan §3.3 item 3."""

    by_id = {candidate.candidate_id: candidate for candidate in candidates}
    staged = by_id.get(staged_id)
    reversible = [candidate for candidate in candidates if (candidate.annotations or {}).get("reversible", True)]
    if ties_only and staged is not None:
        reversible = [candidate for candidate in reversible if candidate.lane == staged.lane]
    order = {candidate.candidate_id: index for index, candidate in enumerate(candidates)}
    priority = tuple(getattr(state, "lane_priority", LANES) or LANES)

    def rank(lane: str) -> int:
        return priority.index(lane) if lane in priority else len(priority) + LANES.index(lane)

    def key(candidate: BlockCandidate) -> tuple:
        return (-round(unspent_share(candidate.lane, state), 9), rank(candidate.lane), -candidate.planner_value,
                order[candidate.candidate_id])

    ranked = sorted(reversible, key=key)
    chosen: list[str] = []
    if staged is not None and staged in reversible:
        chosen.append(staged.candidate_id)
    lanes_seen = {staged.lane} if staged is not None and staged in reversible else set()
    for candidate in ranked:
        if candidate.lane not in lanes_seen:
            lanes_seen.add(candidate.lane)
            chosen.append(candidate.candidate_id)
    for candidate in ranked:
        if candidate.candidate_id not in chosen:
            chosen.append(candidate.candidate_id)
    room = max(int(k) - (1 if stop_offered else 0), 1)
    support = chosen[:room]
    if stop_offered:
        support.append(STOP_FOR_TODAY)
    return support


def _rule_sentence(candidate: BlockCandidate | None, state: PlanState) -> tuple[str, str]:
    if candidate is None:
        code = router_why.stop_code(state.minutes_left, STOP_OFFER_MINUTES)
        return code, router_why.sentence(code)
    notes = dict(candidate.annotations or {})
    code = str(notes.get("reason_code") or "")
    return code, router_why.sentence(code, topic=notes.get("topic"), section=notes.get("section"))


def _option(candidate: BlockCandidate, titles: Mapping[str, str]) -> rq.BlockOption:
    _code, sentence = _rule_sentence(candidate, None)  # type: ignore[arg-type]
    return rq.BlockOption(
        ref=candidate.candidate_id,
        description=rq.option_description(
            why=sentence or candidate.reason, kind=candidate.action, item_count=len(candidate.item_ids),
            est_minutes=candidate.est_minutes,
            topics=[titles.get(lo, lo) for lo in candidate.learning_object_ids],
            section=candidate.reading.section_title if candidate.reading is not None else None,
        ),
    )


# -- the prefetch job ----------------------------------------------------------------------


def _run_components(runtime: RouterRuntime, entry: Prefetch, vault: Any, repository: Any, request: Any,
                    parse: Mapping[str, Any], card_hash: str | None) -> None:
    """Ask every component of ``entry`` (the Decider on this thread, the LLM on its own)."""

    def one(name: str) -> None:
        with entry.lock:
            entry.started_components.add(name)
        budget = entry.remaining(runtime.clock())
        call = call_decider if name == DECIDER else call_llm
        try:
            result, raw = call(runtime, vault, repository, request, card_hash=card_hash, budget=budget)
            if result.status == ANSWERED:
                try:
                    parsed = parse[name](raw, request)
                    if isinstance(parsed, tuple):  # restraint: (p_yes, rationale)
                        result.p_yes, result.rationale = parsed
                    elif isinstance(parsed, float):
                        result.p_yes = parsed
                    else:
                        result.parsed = parsed
                except rq.RouterResponseInvalid as exc:
                    result.status, result.error = INVALID, str(exc)[:300]
        except Exception as exc:  # noqa: BLE001 - a component never takes the job down
            result = ComponentResult(name=name, status="failed", error=type(exc).__name__)
        with entry.lock:
            entry.components[name] = result
        entry.events[name].set()

    names = list(entry.events)
    if runtime.inline or len(names) < 2:
        for name in names:
            one(name)
        return
    import contextvars

    threads = []
    for name in names[1:]:
        context = contextvars.copy_context()
        thread = threading.Thread(target=context.run, args=(one, name), name=f"learnloop-router-{name}", daemon=True)
        thread.start()
        threads.append(thread)
    one(names[0])
    for thread in threads:
        thread.join(timeout=entry.remaining(runtime.clock()) + 1.0)


def _block_job(entry: Prefetch, *, runtime: RouterRuntime, vault: Any, sqlite_path: Any, session_id: str | None,
               plan_id: str | None) -> None:
    from learnloop.daily_plan import router_retrieval
    from learnloop.db.repositories import Repository

    material = entry.material
    repository = Repository.attach(sqlite_path)
    # Every physical request of the decision (the query embedding, both
    # models, a retry or a repair) is admitted by the daily guard (F3, F4).
    with runtime.spend.metered(repository, vault.config, owner_kind=RECEIPT_OWNER, owner_id=entry.key):
        embedding = None
        try:
            embedding = runtime.models.embedding_client(vault)
        except Exception:  # noqa: BLE001
            embedding = None
        entry.similar = router_retrieval.prepare(
            vault=vault, repository=repository, embedding_client=embedding, card_json=material.get("card_json"),
            boundary_key=entry.key, decision_time=material["decided_at"], session_id=session_id, plan_id=plan_id,
        )
        options = material["options"]
        evidence = material["evidence"]
        request = rq.BoundaryRequest(
            options=tuple(options),
            state=rq.state_text(material["card_text"], options, similar=entry.similar.get("lines") or (),
                                evidence=evidence),
            sensors=tuple(material["sensors"]),
            evidence=tuple(evidence),
        )
        entry.request = request
        _run_components(runtime, entry, vault, repository, request,
                        {DECIDER: rq.parse_decider_choice, LLM: rq.parse_llm_choice}, material.get("card_hash"))


def _restraint_job(entry: Prefetch, *, runtime: RouterRuntime, vault: Any, sqlite_path: Any) -> None:
    from learnloop.db.repositories import Repository

    material = entry.material
    repository = Repository.attach(sqlite_path)
    with runtime.spend.metered(repository, vault.config, owner_kind=RECEIPT_OWNER, owner_id=entry.key):
        request = rq.RestraintRequest(topic=material["topic"], state=material["state"])
        entry.request = request
        _run_components(
            runtime, entry, vault, repository, request,
            {DECIDER: lambda raw, _request: rq.parse_decider_restraint(raw),
             LLM: lambda raw, _request: rq.parse_llm_restraint(raw)},
            material.get("card_hash"),
        )


# -- the decision ----------------------------------------------------------------------------


def _await(runtime: RouterRuntime, entry: Prefetch, *, may_defer: bool, timeout: float) -> None:
    if entry.complete:
        return
    now = runtime.clock()
    if may_defer and now < entry.deadline:
        raise DecisionPending(entry.key)
    entry.wait(min(float(timeout), entry.remaining(now)))


def _results(entry: Prefetch, readiness: Mapping[str, str | None]) -> dict[str, ComponentResult]:
    results = entry.results()
    for name in (DECIDER, LLM):
        if name not in results:
            results[name] = ComponentResult(name=name, status=NOT_READY, error=str(readiness.get(name) or "not_ready"))
    return results


def _payloads(results: Mapping[str, ComponentResult]) -> dict[str, Any]:
    payloads: dict[str, Any] = {}
    for name, result in results.items():
        if result.request_payload is not None:
            payloads[f"{name}_request"] = result.request_payload
        if result.response_payload is not None:
            payloads[f"{name}_response"] = result.response_payload
    return payloads


@dataclass
class _Card:
    payload: dict[str, Any] | None
    card_hash: str | None
    version: str | None
    text: str
    json: Mapping[str, Any] | None
    error: str | None = None


def _build_card(builder: CardBuilder | None, state: PlanState, feasible: Sequence[BlockCandidate]) -> _Card:
    if builder is None:
        return _Card(None, None, None, "", None)
    try:
        card = builder(state, feasible)
    except Exception as exc:  # noqa: BLE001 - the card never blocks the plan
        LOG.warning("router: the learner-state card was not built", exc_info=True)
        return _Card(None, None, None, "", None, error=type(exc).__name__)
    if card is None:
        return _Card(None, None, None, "", None)
    return _Card(card.payload(), card.card_hash, card.card_version, card.text, card.json)


def _card_fields(card: _Card) -> dict[str, Any]:
    if card.payload is None:
        return {"card_error": card.error} if card.error else {}
    return {"card_version": card.version, "card_hash": card.card_hash, "card": card.payload}


@dataclass
class RouterChooser:
    """``router_mixture_v1``: the logged model mixture over the staged frame's candidates."""

    vault: Any
    repository: Any
    runtime: RouterRuntime
    card_builder: CardBuilder | None = None
    session_id: str | None = None
    clock: Any = None
    #: True on reads and prefetches (Today's open, feedback): a decision whose
    #: models are still out is left open. False on a serving step: it waits.
    may_defer: bool = True
    name: str = CHOOSER_NAME

    @property
    def scope(self) -> str:
        return str(self.repository.sqlite_path)

    def _now_iso(self) -> str:
        from learnloop.clock import utc_now_iso

        return utc_now_iso(self.clock)

    def choose(self, state: PlanState, feasible: Sequence[BlockCandidate]) -> BlockChoice:
        staged = StagedChooser(card_builder=None).choose(state, feasible)
        config = self.vault.config
        settings = router_settings(config)
        record: dict[str, Any] = {**dict(staged.router_record or {}), "mode": MODE,
                                  "why_version": router_why.MIXTURE_WHY_VERSION}
        by_id = {candidate.candidate_id: candidate for candidate in feasible}
        staged_candidate = by_id.get(staged.candidate_id)
        stop_offered = state.minutes_left < STOP_OFFER_MINUTES or not feasible

        def deterministic(decided_by: str, **extra: Any) -> BlockChoice:
            card = _build_card(self.card_builder, state, feasible)
            record.update(policy=mx.STAGED_POLICY, decided_by=decided_by, **_card_fields(card), **extra)
            return replace(staged, router_record=record)

        if staged_candidate is None:
            return deterministic("single_option")
        if not (staged_candidate.annotations or {}).get("reversible", True):
            return deterministic("irreversible")
        support = support_order(state, feasible, staged.candidate_id, k=settings["k"], stop_offered=stop_offered,
                                ties_only=settings["ties_only"])
        if len(support) <= 1:
            return deterministic("single_option")
        readiness = self.runtime.readiness(self.vault)
        ready = tuple(name for name in (DECIDER, LLM) if readiness.get(name) is None)
        if not ready:
            return deterministic("not_ready", models={name: {"status": NOT_READY, "error": readiness.get(name)}
                                                      for name in (DECIDER, LLM)})
        key = _hash({
            "v": KEY_VERSION, "kind": "plan_block", "plan_id": state.plan_id,
            "state": {"minutes_left": round(state.minutes_left, 3), "items_left": state.items_left,
                      "lanes": {lane: round(value, 3) for lane, value in sorted(state.lane_minutes_left.items())},
                      "kind": state.kind},
            "support": [by_id[ref].log_row() if ref in by_id else ref for ref in support],
            "staged": staged.candidate_id, "as_of": _latest_attempt(self.repository),
            "version": config.algorithms.algorithm_version, "settings": settings, "ready": ready,
        })
        entry = self.runtime.lookup(self.scope, key)
        if entry is None:
            entry = self._start(key, state, feasible, support, by_id, ready)
        _await(self.runtime, entry, may_defer=self.may_defer, timeout=float(config.router.timeout_seconds))
        return self._decide(entry, state, staged, record, support, by_id, readiness, settings)

    def _start(self, key: str, state: PlanState, feasible: Sequence[BlockCandidate], support: Sequence[str],
               by_id: Mapping[str, BlockCandidate], ready: tuple[str, ...]) -> Prefetch:
        config = self.vault.config
        card = _build_card(self.card_builder, state, feasible)
        titles = {lo_id: lo.title for lo_id, lo in self.vault.learning_objects.items()}
        options = [
            _option(by_id[ref], titles) if ref in by_id else rq.BlockOption(ref=ref, description=rq.STOP_DESCRIPTION)
            for ref in support
        ]
        sensors: list[rq.SensorTopic] = []
        if bool(config.router.sensors):
            for ref in support:
                for lo in (by_id[ref].learning_object_ids if ref in by_id else ()):
                    if len(sensors) < rq.MAX_SENSOR_LOS and lo not in {topic.learning_object_id for topic in sensors}:
                        sensors.append(rq.SensorTopic(learning_object_id=lo, title=titles.get(lo, lo)))
        material = {
            "card": card, "card_hash": card.card_hash, "card_text": card.text, "card_json": card.json,
            "options": options, "sensors": sensors, "evidence": list(rq.evidence_from_card(card.json)),
            "decided_at": self._now_iso(),
        }
        from functools import partial

        return self.runtime.start(
            self.scope, key, kind="plan_block", budget=float(config.router.prefetch_timeout_seconds),
            material=material, components=ready,
            job=partial(_block_job, runtime=self.runtime, vault=self.vault, sqlite_path=self.repository.sqlite_path,
                        session_id=self.session_id, plan_id=state.plan_id),
        )

    def _decide(self, entry: Prefetch, state: PlanState, staged: BlockChoice, record: dict[str, Any],
                support: Sequence[str], by_id: Mapping[str, BlockCandidate], readiness: Mapping[str, str | None],
                settings: Mapping[str, Any]) -> BlockChoice:
        config = self.vault.config
        material = entry.material
        card: _Card = material["card"]
        results = _results(entry, readiness)
        distributions = {
            name: dict(result.parsed.distribution) for name, result in results.items()
            if result.status == ANSWERED and result.parsed is not None
        }
        failed = [name for name in mx.MODEL_COMPONENTS if name not in distributions]
        effective = mx.effective_weights(settings["weights"], failed)
        components = mx.component_distributions(list(support), staged.candidate_id, distributions)
        decision_id = new_ulid()
        seed = self.runtime.seed_for(entry.key, decision_id)
        drawn = mx.draw(list(support), components, effective, settings["epsilon_min"], seed)
        chosen = by_id.get(drawn.chosen)
        code, rule = _rule_sentence(chosen, state)
        evidence = {ref.attempt_id: ref.label for ref in material.get("evidence") or ()}
        llm = results.get(LLM)
        rationale = llm.parsed.rationale if llm is not None and llm.parsed is not None else None
        cited = tuple(llm.parsed.evidence_ids) if llm is not None and llm.parsed is not None else ()
        guard = router_why.rationale_guard(rationale, cited, set(evidence)) if rationale is not None else "absent"
        shown = drawn.component == "llm" and guard is None
        why, why_kind = router_why.model_why(drawn.component, rule, option_count=len(support), rationale=rationale,
                                             rationale_shown=shown)
        reasons = {name: results[name].status for name in failed}
        similar = dict(entry.similar or {})
        context_vector = similar.pop("context_vector", None)
        similar.pop("lines", None)
        sensors = {name: {kind: dict(values) for kind, values in result.parsed.sensors.items()}
                   for name, result in results.items()
                   if result.status == ANSWERED and result.parsed is not None and result.parsed.sensors}
        latencies = [result.latency_ms for result in results.values() if result.latency_ms is not None]
        costs = [result.cost_usd for result in results.values() if result.cost_usd is not None]
        request = entry.request
        record.update(
            policy=mx.POLICY,
            decided_by="mixture",
            decision_id=decision_id,
            design=mx.DESIGN,
            seed=seed,
            why_code=code or None,
            drawn_component=drawn.component,
            option_count=len(support),
            fallback=mx.fallback_label(failed),
            fallback_reasons=reasons,
            rationale_hidden=bool(drawn.component == "llm" and not shown),
            evidence_labels=[evidence[ref] for ref in cited if ref in evidence] if shown else [],
            mixture={
                "boundary_key": entry.key,
                "support": list(support),
                "staged_ref": staged.candidate_id,
                "k": settings["k"],
                "epsilon": settings["epsilon_min"],
                "ties_only": settings["ties_only"],
                "effective_weights": effective,
                "drawn_component": drawn.component,
                "u1": drawn.u1,
                "u2": drawn.u2,
                "pi": dict(drawn.pi),
                "models": {name: result.summary() for name, result in sorted(results.items())},
                "similar": similar or {"status": "disabled"},
                "sensor_source": str(config.router.sensor_source),
                "rationale": {"text": rationale, "guard": guard, "shown": shown, "evidence_ids": list(cited)},
                "prefetched_at": material.get("decided_at"),
                "waited_ms": int(round(max(self.runtime.clock() - entry.started, 0.0) * 1000)),
            },
            mixture_weights={"configured": dict(settings["weights"]), "effective": effective},
            model_distributions={name: distributions.get(name) for name in mx.MODEL_COMPONENTS},
            sensor_answers=sensors or None,
            question_set_version=getattr(request, "question_set_version", None),
            model_ids={
                "decider": results[DECIDER].model, "llm": results[LLM].model,
                "llm_schema_version": getattr(request, "llm_schema_version", None),
            },
            similar_decision_ids=similar.get("ids_shown") if similar.get("status") not in (None, "disabled") else None,
            latency_ms=max(latencies) if latencies else None,
            cost_usd=round(sum(costs), 8) if costs else 0.0,
            payloads=_payloads(results),
            **_card_fields(card),
        )
        if context_vector is not None:
            record["context_vector"] = context_vector
        return BlockChoice(
            candidate_id=drawn.chosen,
            chosen_by="mixture",
            propensity=1.0 if drawn.deterministic else drawn.propensity,
            why=why or staged.why,
            why_kind=why_kind,  # type: ignore[arg-type]
            router_record=record,
        )


# -- the restraint (R2c) ------------------------------------------------------------------------


@dataclass
class RestraintOutcome:
    """A follow-up's ``plan_interrupt`` decision, made outside any write."""

    chosen_ref: str
    propensity: float
    record: dict[str, Any]
    refused: dict[str, Any] = field(default_factory=dict)
    why: str = ""
    #: Whether waiting was a choice: the boundary still had room for the
    #: follow-up after the current block (Codex review F8).
    wait_feasible: bool = True

    @property
    def insert(self) -> bool:
        return self.chosen_ref == INSERT_NOW

    @property
    def wait(self) -> bool:
        return self.chosen_ref == CONTINUE_CURRENT


@dataclass
class RestraintGate:
    """``plan_interrupt``: insert a placeable mid-block follow-up now, or let it wait."""

    vault: Any
    repository: Any
    runtime: RouterRuntime
    frame: Any = None
    card_builder: CardBuilder | None = None
    session_id: str | None = None
    clock: Any = None
    may_defer: bool = True

    @property
    def scope(self) -> str:
        return str(self.repository.sqlite_path)

    def refusals(self, item: Any) -> tuple[dict[str, Any], ...]:
        """The P4 constraint engine's named refusals of one follow-up (none: placeable)."""

        return self._refusals(item)

    @staticmethod
    def declined(refusals: Sequence[Mapping[str, Any]]) -> RestraintOutcome:
        """A refused follow-up's deterministic ``decline`` (no model is asked)."""

        from learnloop.router import plan_log

        base = {"mode": MODE, "why_version": router_why.MIXTURE_WHY_VERSION, "policy": mx.STAGED_POLICY,
                "decided_by": "refused"}
        return RestraintOutcome(plan_log.DECLINE_REF, 1.0, base, refused={"reasons": [dict(r) for r in refusals]},
                                why="A follow-up was left out: it can't be served now.")

    def _refusals(self, item: Any) -> tuple[dict[str, Any], ...]:
        if self.frame is None:
            return ()
        try:
            material = self.frame.material([item])
        except Exception:  # noqa: BLE001 - the frame fails open for the whole pool, as at a boundary
            LOG.warning("router R2c: the follow-up's constraints could not be read", exc_info=True)
            return ()
        return tuple(material.refusals.get(item.practice_item_id) or ())

    def decide(self, record: Any, current: Any, item: Any, *, wait_feasible: bool = True) -> RestraintOutcome:
        """The decision for one follow-up the rules would place now (raises
        :class:`DecisionPending` on a read whose models are still out).

        ``wait_feasible`` False: the boundary would have no room for the
        follow-up after the current block, so waiting would drop it from
        today's plan. The restraint decides only now or at the boundary, never
        whether (VOI does), so it joins now deterministically and no model is
        asked (Codex review F8)."""

        base: dict[str, Any] = {"mode": MODE, "why_version": router_why.MIXTURE_WHY_VERSION}
        refusals = self._refusals(item)
        if refusals:
            return self.declined(refusals)
        config = self.vault.config
        settings = router_settings(config)
        state, candidates = self._state(record, current, item)
        if not wait_feasible:
            card = _build_card(self.card_builder, state, candidates)
            base.update(policy=mx.STAGED_POLICY, decided_by="no_room_to_wait", **_card_fields(card))
            return RestraintOutcome(INSERT_NOW, 1.0, base, why="", wait_feasible=False)
        readiness = self.runtime.readiness(self.vault)
        ready = tuple(name for name in (DECIDER, LLM) if readiness.get(name) is None)
        if not ready:
            card = _build_card(self.card_builder, state, candidates)
            base.update(policy=mx.STAGED_POLICY, decided_by="not_ready", **_card_fields(card))
            return RestraintOutcome(INSERT_NOW, 1.0, base, why="")
        key = _hash({
            "v": KEY_VERSION, "kind": "plan_interrupt", "plan_id": record.id, "block": current.id,
            "item": item.practice_item_id, "as_of": _latest_attempt(self.repository),
            "version": config.algorithms.algorithm_version, "settings": settings, "ready": ready,
        })
        entry = self.runtime.lookup(self.scope, key)
        if entry is None:
            entry = self._start(key, state, candidates, item, ready)
        _await(self.runtime, entry, may_defer=self.may_defer, timeout=float(config.router.timeout_seconds))
        results = _results(entry, readiness)
        support = [INSERT_NOW, CONTINUE_CURRENT]
        distributions = {
            name: {INSERT_NOW: float(result.p_yes), CONTINUE_CURRENT: 1.0 - float(result.p_yes)}
            for name, result in results.items() if result.status == ANSWERED and result.p_yes is not None
        }
        failed = [name for name in mx.MODEL_COMPONENTS if name not in distributions]
        effective = mx.effective_weights(settings["weights"], failed)
        decision_id = new_ulid()
        seed = self.runtime.seed_for(entry.key, decision_id)
        if all(sum(values.values()) <= 0 for values in distributions.values()) and distributions:
            distributions = {}
        components = mx.component_distributions(support, INSERT_NOW, distributions)
        drawn = mx.draw(support, components, effective, settings["epsilon_min"], seed)
        card: _Card = entry.material["card"]
        sensor = results.get(str(config.router.sensor_source))
        latencies = [result.latency_ms for result in results.values() if result.latency_ms is not None]
        costs = [result.cost_usd for result in results.values() if result.cost_usd is not None]
        base.update(
            policy=mx.POLICY,
            decided_by="mixture",
            decision_id=decision_id,
            design=mx.DESIGN,
            seed=seed,
            drawn_component=drawn.component,
            fallback=mx.fallback_label(failed),
            fallback_reasons={name: results[name].status for name in failed},
            mixture={
                "boundary_key": entry.key, "support": support, "staged_ref": INSERT_NOW,
                "k": len(support), "epsilon": settings["epsilon_min"], "effective_weights": effective,
                "drawn_component": drawn.component, "u1": drawn.u1, "u2": drawn.u2, "pi": dict(drawn.pi),
                "models": {name: result.summary() for name, result in sorted(results.items())},
                "sensor_source": str(config.router.sensor_source),
                "sensor_of_record": (sensor.p_yes if sensor is not None and sensor.status == ANSWERED else None),
                "rationale": {"text": results[LLM].rationale if LLM in results else None},
            },
            mixture_weights={"configured": dict(settings["weights"]), "effective": effective},
            model_distributions={name: distributions.get(name) for name in mx.MODEL_COMPONENTS},
            sensor_answers={name: {"intervene_now": result.p_yes} for name, result in results.items()
                            if result.status == ANSWERED and result.p_yes is not None} or None,
            question_set_version=rq.RESTRAINT_QUESTION_SET,
            model_ids={"decider": results[DECIDER].model, "llm": results[LLM].model,
                       "llm_schema_version": rq.LLM_RESTRAINT_SCHEMA},
            latency_ms=max(latencies) if latencies else None,
            cost_usd=round(sum(costs), 8) if costs else 0.0,
            payloads=_payloads(results),
            **_card_fields(card),
        )
        why = router_why.FOLLOWUP_WAITS if drawn.chosen == CONTINUE_CURRENT else ""
        return RestraintOutcome(drawn.chosen, 1.0 if drawn.deterministic else drawn.propensity, base, why=why)

    def _state(self, record: Any, current: Any, item: Any) -> tuple[PlanState, list[BlockCandidate]]:
        titles = {lo_id: lo.title for lo_id, lo in self.vault.learning_objects.items()}
        remaining = [entry for entry in current.items if not entry.resolved and not entry.displaced]
        state = PlanState(
            plan_id=record.id, kind=record.kind, minutes_budget=record.budget, minutes_left=record.minutes_left(),
            lane_minutes_left=record.lane_left(), days_since_last_activity=0, streak_days=0,
            current_block_id=current.id,
        )
        insert = BlockCandidate(
            candidate_id=INSERT_NOW, lane=item.lane or "repair", action="practice", subtype="completion_or_repair",
            learning_object_ids=(item.learning_object_id,), item_ids=(item.practice_item_id,), reading=None,
            est_minutes=float(item.est_minutes), planner_value=0.0, reason="a follow-up from this session's answer",
            annotations={"reason_code": "repair_followup", "topic": titles.get(item.learning_object_id, item.learning_object_id),
                         "reversible": True},
        )
        cont = BlockCandidate(
            candidate_id=CONTINUE_CURRENT, lane=current.lane or "maintain", action=current.action or "practice",
            subtype=current.subtype,
            learning_object_ids=tuple(dict.fromkeys(entry.learning_object_id for entry in remaining)),
            item_ids=tuple(entry.practice_item_id for entry in remaining), reading=None,
            est_minutes=float(sum(entry.est_minutes for entry in remaining)), planner_value=0.0,
            reason="the current block's remaining questions", annotations={"reversible": True},
        )
        return state, [insert, cont]

    def _start(self, key: str, state: PlanState, candidates: list[BlockCandidate], item: Any,
               ready: tuple[str, ...]) -> Prefetch:
        from functools import partial

        config = self.vault.config
        card = _build_card(self.card_builder, state, candidates)
        titles = {lo_id: lo.title for lo_id, lo in self.vault.learning_objects.items()}
        topic = titles.get(item.learning_object_id, item.learning_object_id)
        cont = candidates[1]
        options = [
            rq.BlockOption(INSERT_NOW, f"Ask the follow-up on {topic} now, inside the current block."),
            rq.BlockOption(
                CONTINUE_CURRENT,
                f"Finish the current block first ({len(cont.item_ids)} questions left, about "
                f"{max(1, round(cont.est_minutes))} min); the follow-up then opens the next block.",
            ),
        ]
        material = {
            "card": card, "card_hash": card.card_hash, "topic": topic,
            "state": rq.state_text(card.text, options, evidence=rq.evidence_from_card(card.json),
                                   extra=[f"A follow-up question on {topic} came out of the learner's last answer."]),
        }
        return self.runtime.start(
            self.scope, key, kind="plan_interrupt", budget=float(config.router.prefetch_timeout_seconds),
            material=material, components=ready,
            job=partial(_restraint_job, runtime=self.runtime, vault=self.vault, sqlite_path=self.repository.sqlite_path),
        )


__all__ = [
    "CHOOSER_NAME",
    "INSERT_NOW",
    "MODE",
    "RestraintGate",
    "RestraintOutcome",
    "RouterChooser",
    "router_settings",
    "support_order",
]
