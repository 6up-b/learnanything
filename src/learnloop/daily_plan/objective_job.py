"""The objective router's job at a block boundary: its threads, its deadlines, its early answer and its carried
valuations. The chooser (:mod:`learnloop.daily_plan.objective_chooser`) builds what the job computes and decides on
what the job answers; it starts no thread and reads no deadline.

The job's life:

* **Start** (:func:`start_job`): once per boundary key, the runtime runs :func:`_objective_job` on a thread of its own
  (or inline), with ``router.prefetch_timeout_seconds`` from now as the entry's deadline. The Decider and the LLM policy
  each run on a thread; the numeric policy runs on the job's, refining while the LLM is out and the deadline allows.
* **Early publication**: each complete uncorrected numeric answer is published into the job's material
  (``PUBLISHED``) before any wait on the LLM, so the numeric policy's availability never depends on the LLM's; the
  LLM's forecasts correct it afterwards when they come in time.
* **Await** (:func:`await_job`): a read or a prefetch before the deadline leaves the decision open
  (``DecisionPending``); a serve waits up to ``router.timeout_seconds``, then takes what has answered
  (:func:`job_answers`: a component still out is a timeout, and its late answer is discarded).
* **No models** (:func:`answer_without_models`): no job; the numeric policy runs on the serve's own thread by
  ``router.timeout_seconds`` from now.
* **Carry**: a served answer whose carried valuation (the backup at an earlier decision's cutoff) was not ready is
  registered at the serve (:func:`defer_carry`), off the serving path, and run by the next boundary's job after its own
  answer (:func:`drain_carry`), or, with no models, on a thread of its own; a later decision's trace records it
  (:func:`carried_for`). :func:`join_carried` waits for those threads.

What the job computes but cannot import, because the chooser's import cycle would then hold this module too (the
fit's read scope, the LLM policy's request and the numeric policy), the chooser hands :func:`start_job` as arguments.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
import logging
import threading
from typing import Any

from learnloop.daily_plan.router_chooser import _await, _NoModels
from learnloop.daily_plan.router_runtime import (
    ANSWERED,
    DECIDER,
    FAILED,
    INVALID,
    LLM,
    NOT_READY,
    RECEIPT_OWNER,
    TIMEOUT,
    ComponentResult,
    Prefetch,
    RouterRuntime,
    call_decider,
    call_llm,
    wall_now,
)
from learnloop.router import requests as rq
from learnloop.router_objective import price as P
from learnloop.router_objective import value as V

LOG = logging.getLogger(__name__)

NUMERIC = "numeric"
#: The prefetch material's key for the numeric policy's latest complete uncorrected answer (F1): a serve that finds
#: the job still waiting on the LLM policy's forecasts uses it instead of a timeout.
PUBLISHED = "numeric_published"
#: RO6's landing ruling R12: the prefetch material's key for the residual record with the carried valuation, set by
#: the job after the answer released the serve's wait; a serve that comes first censors that backup.
CARRIED = "numeric_carried_valuation"
#: The follow-up batch's item 4 (``carried_in_prefetch``): a decision's carried valuation deferred to the next
#: boundary's prefetch travels with the served answer (``NumericPolicy.carried``; Codex review F3), is registered at
#: the serve, run there, off the serving path, and recorded in a later trace.
#: ``keep`` (a resource bound): the most deferred carried valuations kept per database; past it the oldest is dropped
#: and its backup stays censored ``cutoff_unmatched``.
CARRY_LIMIT = 32
_CARRY_LOCK = threading.Lock()
_CARRY: dict[str, list[dict[str, Any]]] = {}


@dataclass
class NumericPolicy:
    """What π_Q computed for one decision (its status, choice, evaluation and the trace's sections)."""

    status: str
    choice: str | None = None
    tie: Mapping[str, Any] = field(default_factory=dict)
    evaluation: V.Evaluation | None = None
    inputs: V.Inputs | None = None
    actions: tuple[V.Action, ...] = ()
    sources: Mapping[str, Any] = field(default_factory=dict)
    price: P.Seeded | None = None
    frontier: Mapping[str, Any] = field(default_factory=dict)
    baselines: Mapping[str, Any] = field(default_factory=dict)
    corrected: bool = False
    latency_ms: int | None = None
    error: str | None = None
    #: ``final`` (the job's last answer), or ``published_uncorrected`` (served from the job's earlier publication
    #: while it was still waiting on the LLM policy's forecasts: F1)
    stage: str = "final"
    #: RO6 (§10): the learned tail's residual record (:mod:`learnloop.router_objective.tail_serve`); None below the
    #: tag, with the switch off, or on a decision it does not value (a mid-block follow-up)
    residual: Mapping[str, Any] | None = None
    #: The follow-up batch's item 4 (Codex review F3): this answer's own carried valuation, frozen to the inputs it
    #: used (``compute(deadline=...)``), when its residual is pending; whichever answer serves (an early publication
    #: or the final one) hands its own to the next boundary's prefetch. Never serialized.
    carried: Callable[..., dict[str, Any]] | None = field(default=None, repr=False, compare=False)
    #: Landing ruling R12: the follow-up batch's generator switches this answer was computed under (frozen at the
    #: job's start), which the trace records, never the serving config's; None below the batch's tag.
    switches: Mapping[str, bool] | None = None
    #: IH4 (spec_instruct_handoff_v1 §7): the choice model's frozen sensor and ``w_pref``
    #: (:mod:`learnloop.router_objective.preferences`); None with its switch off or nothing on record
    preference: Mapping[str, Any] | None = None


def pooled(config: Any) -> Any:
    """Router speed stage 2, item 4 (its Codex review F2): the objective job's connection pool
    (``db.connection.reused_connections``) only at the follow-up batch's tag with ``[router_objective]
    pooled_connections``; off, a connection opened at every ``connect()`` (main e9ceaf8d44's job, at its time per
    build, so a deadline-bound evaluation completes the draws it completed then)."""

    from contextlib import nullcontext

    from learnloop.router_objective_switches import followup_on

    if config is None or not followup_on(config, "pooled_connections"):
        return nullcontext()
    from learnloop.db.connection import reused_connections

    return reused_connections()


def _llm_forecasts(entry: Prefetch) -> Any:
    """The numeric job's view of the LLM policy's forecasts: None while it is out, else ``(per option, reference)``
    (both None when it failed)."""

    event = entry.events.get(LLM)
    if event is not None and not event.is_set():
        return None
    result = entry.components.get(LLM)
    parsed = getattr(result, "parsed", None)
    if result is None or result.status != ANSWERED or not isinstance(parsed, rq.ParsedPolicy):
        return ({}, None)
    by_ref = {ref: values.get("p_cold_7") for ref, values in parsed.forecasts.items()}
    return by_ref, parsed.reference.get("p_cold_7")


def _objective_job(entry: Prefetch, *, runtime: RouterRuntime, vault: Any, sqlite_path: Any, session_id: str | None,
                   plan_id: str | None, reads: Callable[[], Any],
                   build_policy_request: Callable[[Any, Any, Prefetch], Any],
                   numeric_policy: Callable[..., NumericPolicy]) -> None:
    import contextvars

    from learnloop.db.repositories import Repository

    material = entry.material
    repository = Repository.attach(sqlite_path)
    config = vault.config
    # The card's build and the numeric policy's share one read of the combiner's fit (``reads``), so no write
    # committed between them can give the two policies different fits. The job's own thread reuses its SQLite
    # connections (``pooled``: each given back reset, never shared across threads, never kept in a transaction); the
    # model calls' threads open their own. Behind ``[router_objective] pooled_connections``, because faster builds
    # leave the deadline-bound refinement more draws, and so a different choice.
    with pooled(config), runtime.spend.metered(repository, config, owner_kind=RECEIPT_OWNER,
                                               owner_id=entry.key), reads():
        threads: list[threading.Thread] = []

        def run(name: str, request: Any, parse: Any) -> None:
            with entry.lock:
                entry.started_components.add(name)
            budget = entry.remaining(runtime.clock())
            call = call_decider if name == DECIDER else call_llm
            try:
                result, raw = call(runtime, vault, repository, request, card_hash=material.get("card_hash"), budget=budget)
                if result.status == ANSWERED:
                    try:
                        result.parsed = parse(raw, request)
                    except rq.RouterResponseInvalid as exc:
                        result.status, result.error = INVALID, str(exc)[:300]
            except Exception as exc:  # noqa: BLE001 - a component never takes the job down
                result = ComponentResult(name=name, status=FAILED, error=type(exc).__name__)
            with entry.lock:
                entry.components[name] = result
            entry.events[name].set()

        def start(name: str, request: Any, parse: Any) -> None:
            if runtime.inline:
                run(name, request, parse)
                return
            context = contextvars.copy_context()
            thread = threading.Thread(target=context.run, args=(run, name, request, parse),
                                      name=f"learnloop-objective-{name}", daemon=True)
            thread.start()
            threads.append(thread)

        if DECIDER in entry.events:
            # The Decider: advice and a comparator only, on the learner-state card (v3) and the options.
            request = rq.BoundaryRequest(options=tuple(material["options"]),
                                         state=rq.state_text(material["card_text"], material["options"],
                                                             evidence=material["evidence"]),
                                         evidence=tuple(material["evidence"]))
            start(DECIDER, request, rq.parse_decider_choice)
        if LLM in entry.events:
            try:
                start(LLM, build_policy_request(vault, repository, entry), rq.parse_llm_policy)
            except Exception as exc:  # noqa: BLE001 - the card never blocks the plan: the LLM policy fails
                LOG.warning("router objective: the LLM policy's card was not built", exc_info=True)
                with entry.lock:
                    entry.components[LLM] = ComponentResult(name=LLM, status=FAILED, error=f"card: {type(exc).__name__}")
                entry.events[LLM].set()
        with entry.lock:
            entry.started_components.add(NUMERIC)

        def publish(policy: NumericPolicy) -> None:
            with entry.lock:
                entry.material[PUBLISHED] = policy

        deferred: list[Callable[[], dict[str, Any]]] = []

        numeric = numeric_policy(
            vault, repository, state=material["state"], support=material["support"], candidates=material["by_id"],
            now_iso=material["decided_at"], seed=material["numeric_seed"], deadline=entry.deadline,
            keep_going=lambda: LLM in entry.events and not entry.events[LLM].is_set() and runtime.clock() < entry.deadline,
            forecasts=(lambda: _wait_llm(entry, runtime)) if LLM in entry.events else None, clock=runtime.clock,
            publish=publish, learned_tail=True, tail_snapshot=material.get("tail_snapshot"),
            defer_carried=deferred.append)
        with entry.lock:
            entry.components[NUMERIC] = ComponentResult(name=NUMERIC, status=numeric.status, parsed=numeric,  # type: ignore[arg-type]
                                                        latency_ms=numeric.latency_ms, error=numeric.error)
        # The answer releases the serve's wait before any carried valuation runs: run first, the backup would keep
        # the serve waiting; a serve that has already taken the answer censors that backup (``_with_carried``).
        carry = carry_on(config)
        # With carries in the prefetch, this decision's own carried valuation waits for the next boundary's job;
        # each answer that can serve (the final one above, an early publication) carries its own (``carried``), so the
        # serve registers whichever it takes.
        entry.events[NUMERIC].set()
        if carry:
            # ... and this job runs the ones earlier decisions left, now that its own answer is out.
            drain_carry(sqlite_path, deadline=entry.deadline)
            deferred = []
        for compute in deferred:
            try:
                carried_record = compute()
            except Exception:  # noqa: BLE001 - the backup's value never fails the decision: it is censored
                LOG.warning("router objective: the carried valuation failed", exc_info=True)
                continue
            with entry.lock:
                entry.material[CARRIED] = carried_record
        for thread in threads:
            thread.join(timeout=entry.remaining(runtime.clock()) + 1.0)


def _with_carried(numeric: "NumericPolicy | None", entry: Any) -> "NumericPolicy | None":
    """Landing ruling R12: the served answer's residual with the carried valuation if the job had it before this
    serve (``CARRIED``), else marked valued too late (``not_valued_before_the_serve``: the backup into this
    decision is censored ``cutoff_unmatched``). An answer with nothing pending is returned as it is."""

    from learnloop.router_objective import tail_serve

    if numeric is None or not tail_serve.is_pending(numeric.residual):
        return numeric
    lock = getattr(entry, "lock", None)
    material = getattr(entry, "material", {}) or {}
    if lock is not None:
        with lock:
            carried = material.get(CARRIED)
    else:
        carried = material.get(CARRIED)
    if isinstance(carried, Mapping):
        return replace(numeric, residual=carried)
    return replace(numeric, residual=tail_serve.not_before_the_serve(numeric.residual))


def carry_on(config: Any) -> bool:
    # One predicate for the serving side and the reading side (tail_data.logged; Codex review F1).
    from learnloop.router_objective import tail_data as TD

    return TD.carried_in_prefetch_on(config)


def _register_carry(sqlite_path: Any, decision_id: str, compute: Callable[[], dict[str, Any]]) -> None:
    """The follow-up batch's item 4: a decision served before its carried valuation existed leaves the valuation
    (its own frozen inputs, in ``compute``) to the next boundary's prefetch."""

    with _CARRY_LOCK:
        waiting = _CARRY.setdefault(str(sqlite_path), [])
        waiting.append({"decision_id": decision_id, "compute": compute, "record": None, "carriers": []})
        del waiting[:-CARRY_LIMIT]


def drain_carry(sqlite_path: Any, *, deadline: float | None = None) -> int:
    """Run every deferred carried valuation of this database not yet run (a prefetch job's, after its own answer
    released the serve's wait; the no-model branch's thread, after its serve), each by ``deadline`` (the runner's
    own). Never the serving thread's work. Returns how many ran."""

    with _CARRY_LOCK:
        todo = [entry for entry in _CARRY.get(str(sqlite_path), []) if entry["record"] is None
                and not entry.get("running")]
        for entry in todo:
            entry["running"] = True
    ran = 0
    for entry in todo:
        try:
            record = entry["compute"](deadline=deadline)
        except Exception:  # noqa: BLE001 - the backup stays censored; the decision is untouched
            LOG.warning("router objective: a deferred carried valuation failed", exc_info=True)
            record = {"previous": {"q_status": "not_valued_in_the_next_prefetch"}}
        with _CARRY_LOCK:
            entry["record"] = record
            entry["running"] = False
        ran += 1
    return ran


def carried_for(repository: Any, decision_id: str) -> list[dict[str, Any]]:
    """The deferred carried valuations ready to be recorded in this decision's trace (``carried_for``). Each stays
    waiting until a trace that holds it is known to be written (a choice computed and never logged writes nothing),
    then is dropped, so a record is carried until one carrier is in the log."""

    key = str(repository.sqlite_path)
    with _CARRY_LOCK:
        waiting = list(_CARRY.get(key, []))
    carriers = sorted({carrier for entry in waiting for carrier in entry["carriers"]})
    written: set[str] = set()
    if carriers:
        marks = ",".join("?" for _ in carriers)
        with repository.connection() as connection:
            written = {str(row[0]) for row in connection.execute(
                f"SELECT decision_id FROM router_objective_traces WHERE decision_id IN ({marks})", carriers)}
    out: list[dict[str, Any]] = []
    with _CARRY_LOCK:
        kept = []
        for entry in _CARRY.get(key, []):
            if written & set(entry["carriers"]):
                continue
            record = entry["record"]
            valued = (isinstance(record, Mapping) and isinstance(record.get("previous"), Mapping)
                      and record["previous"].get("q_status") == "valued")
            if record is not None and not valued:
                continue  # it ran and found no value (deadline, failure): nothing to carry
            kept.append(entry)
            if valued:
                entry["carriers"].append(decision_id)
                out.append({"decision_id": entry["decision_id"], "previous": dict(record["previous"]),
                            "basis": "the decision's own frozen inputs, valued at its earlier decision's cutoff in a "
                                     "later boundary's prefetch (off the serving path)"})
        _CARRY[key] = kept
    return out


def _wait_llm(entry: Prefetch, runtime: RouterRuntime) -> Any:
    event = entry.events.get(LLM)
    if event is not None and not event.is_set():
        event.wait(entry.remaining(runtime.clock()))
    return _llm_forecasts(entry)


def _numeric_answer(entry: Any, results: dict[str, ComponentResult]) -> "NumericPolicy | None":
    """The numeric policy's answer a serve takes: the no-model branch's own, the job's final one, or, while the job
    still waits on the LLM policy's forecasts for its optional correction, its uncorrected publication, labelled
    ``published_uncorrected`` (``results`` then names it answered, so the numeric policy's availability never waits on
    the LLM's); else its status alone, or None with no job."""

    material = entry.material
    numeric_result = results.get(NUMERIC)
    numeric: NumericPolicy | None = material.get("numeric")
    if numeric is None and numeric_result is not None:
        lock = getattr(entry, "lock", None)
        if lock is not None:
            with lock:
                published = material.get(PUBLISHED)
        else:
            published = material.get(PUBLISHED)
        if isinstance(numeric_result.parsed, NumericPolicy):
            numeric = numeric_result.parsed
        elif numeric_result.status == TIMEOUT and isinstance(published, NumericPolicy):
            numeric = replace(published, stage="published_uncorrected")
            results[NUMERIC] = ComponentResult(name=NUMERIC, status=ANSWERED, parsed=numeric,  # type: ignore[arg-type]
                                               latency_ms=numeric.latency_ms)
        else:
            numeric = NumericPolicy(status=numeric_result.status, error=numeric_result.error)
    return numeric


def job_answers(entry: Any, readiness: Mapping[str, str | None]
                ) -> tuple[dict[str, ComponentResult], str, NumericPolicy | None]:
    """What a serve takes from its job: every component's result (one still out is a timeout; a model not asked is
    ``not_ready`` with the readiness reason), the wall time they were taken, and the numeric answer that serves
    (:func:`_numeric_answer`) with its carried valuation if the job had it first (:func:`_with_carried`)."""

    results = entry.results()
    results_at = wall_now()  # a model answering after this was discarded (``why``)
    for name in (DECIDER, LLM):
        if name not in results:
            results[name] = ComponentResult(name=name, status=NOT_READY, error=str(readiness.get(name) or "not_ready"))
    return results, results_at, _with_carried(_numeric_answer(entry, results), entry)


def start_job(runtime: RouterRuntime, scope: str, key: str, *, vault: Any, sqlite_path: Any, session_id: str | None,
              plan_id: str | None, material: dict[str, Any], ready: tuple[str, ...],
              reads: Callable[[], Any], build_policy_request: Callable[[Any, Any, Prefetch], Any],
              numeric_policy: Callable[..., NumericPolicy]) -> Prefetch:
    """Register one boundary's job and start it (once per key): the asked models and the numeric policy, by
    ``router.prefetch_timeout_seconds`` from now. ``reads()``: the scope in which the LLM's card and the numeric
    policy share one read of the combiner's fit; ``build_policy_request(vault, repository, entry)``: the LLM policy's
    request, built on the job's thread; ``numeric_policy``: the numeric policy (``objective_chooser.run_numeric``),
    which the job calls with the boundary's inputs from ``material`` and its own deadline, refinement, publication and
    deferral."""

    from functools import partial

    return runtime.start(
        scope, key, kind="plan_block", budget=float(vault.config.router.prefetch_timeout_seconds),
        material=material, components=(*ready, NUMERIC),
        job=partial(_objective_job, runtime=runtime, vault=vault, sqlite_path=sqlite_path, session_id=session_id,
                    plan_id=plan_id, reads=reads, build_policy_request=build_policy_request,
                    numeric_policy=numeric_policy),
    )


def await_job(runtime: RouterRuntime, entry: Prefetch, *, may_defer: bool, config: Any) -> None:
    """A step's wait for its boundary's job: none once it is complete; a read or a prefetch (``may_defer``) before the
    deadline leaves the decision open (``DecisionPending``); a serve waits up to ``router.timeout_seconds``."""

    _await(runtime, entry, may_defer=may_defer, timeout=float(config.router.timeout_seconds))


def answer_without_models(runtime: RouterRuntime, key: str, *, config: Any, card: Any, now_iso: str,
                          numeric: Callable[..., NumericPolicy], tail_snapshot: Callable[[], Any]) -> _NoModels:
    """No model is set up, so no job: the numeric policy (``numeric``, bound to the boundary's inputs) runs on this
    thread by ``router.timeout_seconds`` from now, with no refinement (nothing is out). With carries in the prefetch
    its carried valuation is deferred (:func:`defer_carry`); without, none is computed here. ``tail_snapshot()`` is
    read after the deadline is set, in the order the chooser read them, so a clock charged per read gives the same
    deadline."""

    # Never a second valuation on the serving path: deferred to a thread of its own after the serve, or none.
    no_model_deferred: list[Callable[..., dict[str, Any]]] = []
    carry = carry_on(config)
    computed = numeric(deadline=runtime.clock() + float(config.router.timeout_seconds), clock=runtime.clock,
                       tail_snapshot=tail_snapshot(),
                       carried_valuation=carry,
                       defer_carried=no_model_deferred.append if carry else None)
    # (the answer carries its own carried valuation, ``numeric.carried``, when one is pending)
    return _NoModels(key, {"card": card, "evidence": list(rq.evidence_from_card(card.json)),
                           "decided_at": now_iso, "numeric": computed}, runtime.clock())


#: The threads :func:`defer_carry` started (a no-model serve's carried valuation), for :func:`join_carried`.
_CARRY_THREADS: list[threading.Thread] = []


def defer_carry(numeric: NumericPolicy, entry: Any, decision_id: str, *, runtime: RouterRuntime, sqlite_path: Any,
                config: Any) -> NumericPolicy:
    """A decision served before its carried valuation existed hands it to the next boundary's job (with no models,
    to a thread of its own started after this decision), off the serving path; a later decision's trace records it.
    The decision's own record says where its value went.

    The valuation is the served answer's own (``numeric.carried``, frozen to that answer's inputs), so an early
    publication served before the job completes hands over its own, and a final answer its."""

    from learnloop.router_objective import tail_serve

    residual = numeric.residual if isinstance(numeric.residual, Mapping) else None
    previous = (residual or {}).get("previous")
    if not isinstance(previous, Mapping) or previous.get("q_status") != tail_serve.NOT_BEFORE_THE_SERVE:
        return numeric
    if numeric.carried is None:
        return numeric
    _register_carry(sqlite_path, decision_id, numeric.carried)
    no_models = isinstance(entry, _NoModels)
    if no_models:
        deadline = runtime.clock() + float(config.router.timeout_seconds)
        thread = threading.Thread(target=drain_carry, args=(sqlite_path,),
                                  kwargs={"deadline": deadline}, name="learnloop-objective-carried", daemon=True)
        thread.start()
        with _CARRY_LOCK:
            _CARRY_THREADS[:] = [*(running for running in _CARRY_THREADS if running.is_alive()), thread]
    return replace(numeric, residual={**dict(residual or {}), "previous": {
        **dict(previous), "deferred_to": "own_thread_after_the_serve" if no_models else "next_prefetch"}})


def join_carried(timeout: float | None = None) -> bool:
    """Wait for the carried valuations running on threads of their own (each up to ``timeout``; None: until done) and
    say whether none is still running. Whoever must not leave one reading a database behind calls it: a test that
    compares numbers across serves, or a host before it lets go of a vault."""

    with _CARRY_LOCK:
        threads = list(_CARRY_THREADS)
    for thread in threads:
        if thread is not threading.current_thread():
            thread.join(timeout)
    with _CARRY_LOCK:
        _CARRY_THREADS[:] = [thread for thread in _CARRY_THREADS if thread.is_alive()]
        return not _CARRY_THREADS


__all__ = ["CARRIED", "CARRY_LIMIT", "NUMERIC", "PUBLISHED", "NumericPolicy", "answer_without_models", "await_job",
           "carried_for", "carry_on", "defer_carry", "drain_carry", "job_answers", "join_carried", "pooled",
           "start_job"]
