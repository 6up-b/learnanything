"""The unit-inventory and synthesis job types: ``inventory``, ``bootstrap_synthesis`` and ``append_synthesis``,
with the inventory and synthesis clients the runner's services fall back on.

The durable host that runs them is :mod:`learnloop.content.pipeline.jobs`; what each type is (its handler and its
flags) is its row in :mod:`learnloop.content.pipeline.job_types`.
"""

from __future__ import annotations

import concurrent.futures
import logging
import queue
import threading
import time
from contextvars import copy_context
from typing import TYPE_CHECKING, Any, Callable, Mapping

from learnloop.ai.transport import INTERRUPT, interrupt_callback
from learnloop.content.pipeline.import_jobs import _optional_int
from learnloop.content.pipeline.job_contracts import IngestRunnerError, JobCancelled
from learnloop.db.repositories import Repository

if TYPE_CHECKING:
    from learnloop.content.pipeline.runner import JobContext


# Handler execution defaults remain here with the concrete jobs they govern.
_MAX_INVENTORY_WORKERS = 2
INGEST_CODEX_TIMEOUT_SECONDS = 8 * 60
# The parallel inventory loop wakes on every worker request or completion,
# so this only bounds how late a batch cancellation is noticed. Each check
# opens two connections (job and batch), so polling faster costs runner CPU.
_INVENTORY_CANCEL_POLL_SECONDS = 0.25


def inventory_client_identity(client: Any) -> tuple[str, str]:
    return (
        str(getattr(client, "provider_type", None) or "codex"),
        str(getattr(client, "model", None) or "unknown"),
    )


def default_inventory_identity(ctx: JobContext) -> tuple[str, str] | None:
    """Resolve the primary inventory cache key without a runtime probe.

    A miss still validates runtime readiness before executing. If that selects a
    fallback provider, ``handle_inventory`` rechecks the miss under the actual
    client's identity before making a model call.
    """

    from learnloop.content.synthesis.source_unit_inventory import current_inventory_identity
    from learnloop.vault.loader import load_vault

    return current_inventory_identity(load_vault(ctx.vault_root).config)


def default_inventory_client(
    ctx: JobContext,
    *,
    codex_timeout_seconds: int | None = None,
) -> Any:
    """Resolve the unit-inventory/quick-check client through ai routing (§7).

    Routed via the ``canonical_ingest`` task (empty routing follows
    ai.active_provider), except codex-family routes are pinned to the
    LOW-effort codex profile: unit inventories deliberately stay cheap while
    synthesis follows the routed medium-effort profile
    (``default_synthesis_client``). The inventory/quick-check methods are
    getattr-discovered on the client, so a provider lacking them degrades to
    an explicit unavailable error rather than fabricating rows."""

    from learnloop.ai.routing import ready_client_for_task
    from learnloop.vault.loader import load_vault

    vault = load_vault(ctx.vault_root)
    resolved = ready_client_for_task(
        ctx.vault_root,
        vault.config,
        "canonical_ingest",
        timeout_seconds=codex_timeout_seconds,
    )
    if resolved.client is not None:
        return resolved.client
    raise IngestRunnerError(
        resolved.runtime.message
        or f"AI provider {resolved.provider_name!r} is {resolved.runtime.status}."
    )


def default_synthesis_client(ctx: JobContext) -> Any:
    """Resolve the canonical-ingest route for judgment-heavy synthesis.

    Unit inventories deliberately keep the low-effort legacy Codex client;
    synthesis follows the routed medium-effort profile and its fallback. Codex
    SDK turns get an eight-minute deadline because source-set bootstrap and
    append synthesis routinely exceed the interactive default.
    """

    return _routed_task_client(
        ctx,
        "canonical_ingest",
        codex_timeout_seconds=INGEST_CODEX_TIMEOUT_SECONDS,
    )


def _routed_task_client(
    ctx: JobContext,
    task: str,
    *,
    codex_timeout_seconds: int | None = None,
) -> Any:
    from learnloop.ai.routing import ready_client_for_task
    from learnloop.vault.loader import load_vault

    vault = load_vault(ctx.vault_root)
    resolved = ready_client_for_task(
        ctx.vault_root,
        vault.config,
        task,
        timeout_seconds=codex_timeout_seconds,
    )
    if resolved.client is None:
        raise IngestRunnerError(
            resolved.runtime.message
            or f"Synthesis provider is {resolved.runtime.status}."
        )
    return resolved.client


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


class _InventoryInterruptGroup:
    """One job-scoped interrupt hook covering its active inventory clients."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._clients: dict[int, tuple[Any, int]] = {}

    def add(self, client: Any) -> None:
        with self._lock:
            existing = self._clients.get(id(client))
            self._clients[id(client)] = (
                client,
                1 if existing is None else existing[1] + 1,
            )

    def discard(self, client: Any) -> None:
        with self._lock:
            existing = self._clients.get(id(client))
            if existing is None:
                return
            if existing[1] <= 1:
                self._clients.pop(id(client), None)
            else:
                self._clients[id(client)] = (existing[0], existing[1] - 1)

    def interrupt(self) -> None:
        with self._lock:
            clients = [entry[0] for entry in self._clients.values()]
        for client in clients:
            interrupt = interrupt_callback(client)
            if interrupt is None:
                continue
            try:
                interrupt()
            except Exception:
                # Cancellation is best-effort per provider; continue through
                # the group so one broken hook cannot strand another call.
                pass

    def supports(self, capability: str) -> bool:
        return capability == INTERRUPT


class _RunnerMailbox:
    """Carry inventory workers' requests to the runner thread and back.

    Workers own provider clients, but every SQL write runs on the runner
    thread, where the job's ownership fence and progress reporting live. A
    worker posts a callback and waits for the runner to answer it. Once the
    runner closes the mailbox nothing answers any more, so every unanswered
    and later request fails with :class:`JobCancelled` instead of waiting
    forever on a runner that has stopped.
    """

    _ANSWER_POLL_SECONDS = 0.25

    def __init__(self) -> None:
        # ``None`` is a wake-up with nothing to answer.
        self._requests: queue.SimpleQueue[
            tuple[Callable[[], Any], concurrent.futures.Future] | None
        ] = queue.SimpleQueue()
        self._closed = threading.Event()

    def call(self, callback: Callable[[], Any]) -> Any:
        """Worker side: run ``callback`` on the runner thread; return its result."""

        answer: concurrent.futures.Future = concurrent.futures.Future()
        self._requests.put((callback, answer))
        while not answer.done():
            if self._closed.is_set():
                raise JobCancelled()
            concurrent.futures.wait((answer,), timeout=self._ANSWER_POLL_SECONDS)
        return answer.result()

    def wake(self, *_ignored: Any) -> None:
        """Wake a runner waiting in :meth:`answer_pending` (a worker finished)."""

        self._requests.put(None)

    def answer_pending(self, *, wait_seconds: float = 0.0) -> BaseException | None:
        """Runner side: answer every queued request; return the first failure.

        Waits up to ``wait_seconds`` for the first request or wake-up, then
        answers whatever else is already queued without waiting.
        """

        first_failure: BaseException | None = None
        timeout = wait_seconds
        while True:
            try:
                if timeout > 0:
                    request = self._requests.get(timeout=timeout)
                else:
                    request = self._requests.get_nowait()
            except queue.Empty:
                return first_failure
            timeout = 0.0
            if request is None:
                continue
            callback, answer = request
            try:
                answer.set_result(callback())
            except BaseException as exc:
                answer.set_exception(exc)
                first_failure = first_failure or exc

    def close(self) -> None:
        """Runner side: stop answering and fail every unanswered request."""

        self._closed.set()
        while True:
            try:
                request = self._requests.get_nowait()
            except queue.Empty:
                return
            if request is not None:
                _callback, answer = request
                answer.set_exception(JobCancelled())


def handle_inventory(ctx: JobContext) -> dict[str, Any]:
    """inventory: role-aware per-unit inventories for the selected units (§7).

    Depends on extraction (the runner enforces this via job dependencies).
    Payload: ``extraction_id`` and ``units`` = [{unit_id, role, profile?}]. Each
    unit is inventoried through the cache: a cache hit records ZERO tokens
    (``run_unit_inventory`` returns ``cache_hit``), and only semantic-hash-changed
    units are ever re-inventoried across collections/revisions (§3.2)."""

    from learnloop.content.synthesis.source_unit_inventory import (
        InventoryResult,
        PreparedInventory,
        execute_prepared_inventory,
        persist_prepared_inventory,
        prepare_unit_inventory,
        window_checkpoint,
    )

    payload = ctx.payload
    extraction_id, units = _inventory_inputs(ctx, payload)
    if not extraction_id:
        raise IngestRunnerError("inventory job requires an 'extraction_id'.")
    if not units:
        raise IngestRunnerError("inventory job requires at least one unit.")
    from learnloop.content.pipeline.add_source import admit_auto_build_job

    admit_auto_build_job(ctx)
    units = _effective_inventory_inputs(ctx.repo, extraction_id, units)
    budgets = _ingest_budgets(ctx)
    budget = _optional_int(payload.get("input_budget_tokens")) or budgets.inventory_input_tokens
    unlimited_token_budget = bool(payload.get("unlimited_token_budget", False))
    output_budget = (
        None
        if unlimited_token_budget
        else _optional_int(payload.get("output_budget_tokens")) or budgets.inventory_output_tokens
    )
    output_ceiling = None if unlimited_token_budget else budgets.inventory_output_ceiling_tokens

    specs: list[dict[str, Any]] = []
    for spec in units:
        unit_id = str(spec.get("unit_id") or "").strip()
        if not unit_id:
            raise IngestRunnerError("every inventory unit needs a 'unit_id'.")
        specs.append(
            {
                **dict(spec),
                "unit_id": unit_id,
                "unit_ids": [
                    str(value) for value in spec.get("unit_ids") or [unit_id]
                ],
            }
        )

    ctx.report("extracted", message="Checking unit inventory cache")
    warm_client: Any = None
    identity = ctx.services.inventory_identity(ctx)
    if identity is None:
        # Custom factories may not expose a cheap identity resolver on their
        # first job. Retain this client for the first execution lane.
        warm_client = ctx.services.inventory_client(
            ctx, bind_interruptible=False
        )
        identity = inventory_client_identity(warm_client)

    results_by_index: dict[int, InventoryResult] = {}
    work_by_index: dict[int, PreparedInventory] = {}

    def prepare(index: int, provider_identity: tuple[str, str], client: Any = None) -> None:
        spec = specs[index]
        resolved = prepare_unit_inventory(
            ctx.repo,
            extraction_id,
            spec["unit_id"],
            unit_ids=spec["unit_ids"],
            role=str(spec.get("role") or "reference"),
            profile=spec.get("profile"),
            client=client,
            provider=provider_identity[0],
            model=provider_identity[1],
            input_budget_tokens=budget,
            output_budget_tokens=output_budget,
            output_ceiling_tokens=output_ceiling,
            clock=ctx.clock,
        )
        if isinstance(resolved, InventoryResult):
            results_by_index[index] = resolved
            work_by_index.pop(index, None)
        else:
            work_by_index[index] = resolved
            results_by_index.pop(index, None)

    for index in range(len(specs)):
        prepare(index, identity)

    if work_by_index:
        if warm_client is None:
            warm_client = ctx.services.inventory_client(
                ctx, bind_interruptible=False
            )
        # Prepare the misses again with the client that will run them. Window
        # checkpoint keys include its settings (endpoint, reasoning effort),
        # matching run_unit_inventory's keys for the same inputs, and runtime
        # routing may have selected the configured fallback, whose identity
        # the unit inventory cache must be checked under.
        identity = inventory_client_identity(warm_client)
        for index in list(work_by_index):
            prepare(index, identity, warm_client)

    # Units read before (their inventory is cached) are not asked for again: said beside the windows still to read.
    _record_step(ctx, reused=len(specs) - len(work_by_index))
    if work_by_index:
        worker_count = min(_MAX_INVENTORY_WORKERS, len(work_by_index))
        clients = [warm_client]
        for _ in range(1, worker_count):
            client = ctx.services.inventory_client(
                ctx, bind_interruptible=False
            )
            if inventory_client_identity(client) != identity:
                raise IngestRunnerError(
                    "Inventory provider routing changed while preparing parallel workers."
                )
            clients.append(client)

        # A worker owns one client and one unit at a time. The runner accepts
        # receipt/checkpoint events before acknowledging them, keeping all SQL
        # on this thread and saving paid work before scheduling more work.
        from learnloop.ai.execution import observe_model_calls

        interrupt_group = _InventoryInterruptGroup()
        ctx.bind_interruptible(interrupt_group)
        mailbox = _RunnerMailbox()
        stopped = threading.Event()
        total_model_windows = sum(len(prepared.windows) for prepared in work_by_index.values())
        completed_model_windows = 0
        ctx.report("inventoried", message="Inventorying uncached units", current_window=0, total_windows=total_model_windows)

        def run_unit(client, index, prepared):
            interrupt_group.add(client)
            def observe(action, event):
                if action == "start" and stopped.is_set():
                    raise JobCancelled()
                return mailbox.call(lambda: ctx.repo.record_model_event(action, event, owner_kind="ingest_job", owner_id=ctx.job["id"]))
            def checkpoint(key, result, usage):
                mailbox.call(lambda: window_checkpoint(ctx.repo, key, prepared.valid_span_ids).save(result, usage))
            def report_window(current, total):
                def report():
                    nonlocal completed_model_windows
                    completed_model_windows += 1
                    ctx.report("inventoried", message=f"Inventoried {prepared.unit_id} window {current} of {total}", current_window=completed_model_windows, total_windows=total_model_windows)
                mailbox.call(report)
                if stopped.is_set():
                    raise JobCancelled()
            try:
                with observe_model_calls(observe):
                    execution = execute_prepared_inventory(prepared, client, progress=report_window, checkpoint=checkpoint)
                return index, prepared, execution
            finally:
                interrupt_group.discard(client)

        work = iter(sorted(work_by_index.items()))
        failure: BaseException | None = None
        with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="learnloop-inventory") as executor:
            pending: dict[concurrent.futures.Future, Any] = {}
            def submit(client):
                item = next(work, None)
                if item is not None:
                    index, prepared = item
                    future = executor.submit(copy_context().run, run_unit, client, index, prepared)
                    future.add_done_callback(mailbox.wake)
                    pending[future] = client
            try:
                for client in clients:
                    submit(client)
                next_cancel_check = time.monotonic()
                while pending:
                    answer_failure = mailbox.answer_pending(wait_seconds=_INVENTORY_CANCEL_POLL_SECONDS)
                    failure = failure or answer_failure
                    if time.monotonic() >= next_cancel_check:
                        next_cancel_check = time.monotonic() + _INVENTORY_CANCEL_POLL_SECONDS
                        try:
                            if ctx.cancelled():
                                raise JobCancelled()
                        except BaseException as exc:
                            failure = failure or exc
                    done = [future for future in pending if future.done()]
                    free_clients = []
                    for future in done:
                        free_clients.append(pending.pop(future))
                        try:
                            index, prepared, execution = future.result()
                            result = persist_prepared_inventory(ctx.repo, prepared, execution, clock=ctx.clock)
                            ctx.record_usage(dict(result.usage or {}))
                            results_by_index[index] = result
                        except BaseException as exc:
                            failure = failure or exc
                    if failure is not None:
                        if not stopped.is_set():
                            stopped.set()
                            interrupt_group.interrupt()
                    else:
                        for client in free_clients:
                            submit(client)
            finally:
                if pending:
                    # The loop ended with workers still running, e.g. on a
                    # KeyboardInterrupt raised on this thread. Stop their
                    # provider calls; closing the mailbox releases any worker
                    # waiting for an answer, so the executor can join them.
                    stopped.set()
                    interrupt_group.interrupt()
                mailbox.close()
            if failure is not None:
                raise failure

    results: list[dict[str, Any]] = []
    for index, spec in enumerate(specs):
        result = results_by_index[index]
        results.append(
            {
                "unit_id": result.inventory.unit_id,
                "unit_ids": spec["unit_ids"],
                "inventory_id": result.inventory_id,
                "profile": result.profile,
                "cache_hit": result.cache_hit,
                "reused_profile": result.reused_profile,
            }
        )

    cache_hits = sum(1 for row in results if row["cache_hit"])
    ctx.report(
        "inventoried",
        message=(
            "Unit inventories ready"
            if cache_hits == 0
            else f"Unit inventories ready · reused {cache_hits} cached"
        ),
    )
    return {
        "extraction_id": extraction_id,
        "units": results,
        "cache_hits": cache_hits,
    }


def _ingest_budgets(ctx: JobContext):
    """Load vault budgets, retaining service defaults for isolated workers/tests."""

    from learnloop.config import IngestBudgetsConfig
    from learnloop.vault.loader import load_vault

    try:
        return load_vault(ctx.vault_root).config.ingest.budgets
    except FileNotFoundError:
        return IngestBudgetsConfig()


def _inventory_inputs(
    ctx: JobContext, payload: Mapping[str, Any]
) -> tuple[str, list[dict[str, Any]]]:
    """Resolve public import→inventory shorthand from the completed dependency."""

    extraction_id = str(payload.get("extraction_id") or "").strip()
    units = [dict(unit) for unit in payload.get("units") or [] if isinstance(unit, Mapping)]
    if not extraction_id:
        for dep_id in ctx.repo.ingest_job_dependency_ids(ctx.job_id):
            dependency = ctx.repo.get_ingest_job(dep_id)
            if dependency is None or dependency.get("job_type") != "import":
                continue
            result = dependency.get("result") or {}
            extraction_id = str(result.get("extraction_id") or "").strip()
            if extraction_id:
                break
    if extraction_id and not units:
        ir = ctx.repo.load_document_ir(extraction_id)
        role = str(payload.get("role") or "reference")
        units = [{"unit_id": unit.unit_id, "role": role} for unit in (ir.units if ir else [])]
    return extraction_id, units


def _effective_inventory_inputs(
    repo: Repository,
    extraction_id: str,
    units: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Fold explicit same-role ``merge_with_next`` groups into one model input.

    Boundary overrides describe the learner-confirmed semantic unit shape, not a
    presentation-only grouping.  A merge is honored only when every source member
    is selected with the same effective role/profile.  Exam units remain separate
    because held-out and paper-level accounting is member-scoped.
    """

    selection = repo.get_unit_selection(extraction_id)
    ir = repo.load_document_ir(extraction_id)
    if ir is None or not selection or not selection.get("boundary_overrides"):
        return units

    from learnloop.content.sources.role_authority import default_inventory_profile
    from learnloop.content.synthesis.source_unit_inventory import normalize_profile
    from learnloop.content.synthesis.source_unit_selection import effective_scope_groups

    requested: dict[str, dict[str, Any]] = {}
    input_order: list[str] = []
    for spec in units:
        source_id = str(spec.get("unit_id") or "").strip()
        if not source_id or source_id in requested:
            continue
        requested[source_id] = dict(spec)
        input_order.append(source_id)

    effective_specs: list[dict[str, Any]] = []
    role_by_unit = {
        source_id: str(spec.get("role") or "reference")
        for source_id, spec in requested.items()
    }
    groups = effective_scope_groups(
        ir,
        selection.get("boundary_overrides") or [],
        input_order,
        role_by_unit=role_by_unit,
    )
    for group in groups:
        source_ids = [str(value) for value in group["unit_ids"]]
        member_specs = [requested[source_id] for source_id in source_ids]
        if group["merged"]:
            profiles = {
                normalize_profile(
                    spec.get("profile")
                    or default_inventory_profile(
                        str(spec.get("role") or "reference")
                    )
                )
                for spec in member_specs
            }
        else:
            profiles = set()
        if group["merged"] and len(profiles) == 1:
            role = str(group["role"])
            profile = next(iter(profiles))
            effective_specs.append(
                {
                    "unit_id": str(group["unit_id"]),
                    "unit_ids": source_ids,
                    "role": role,
                    "profile": profile,
                }
            )
            continue
        for source_id in source_ids:
            effective_specs.append(requested[source_id])
    return effective_specs


def _build_trace_id(ctx: JobContext) -> str:
    """The trace a synthesis job's decision records (and model receipts) join: the automatic build's planner job
    when there is one, so its scope, the inventory rows the run read and what it applied answer as one trace in
    ``learnloop why``; the job itself otherwise. The ingest drain opens no trace of its own."""

    auto = ctx.payload.get("auto_build")
    planner = auto.get("planner_job_id") if isinstance(auto, Mapping) else None
    return str(planner or ctx.job_id)


def handle_bootstrap_synthesis(ctx: JobContext) -> dict[str, Any]:
    """bootstrap_synthesis: N-way study-map synthesis over a source set (ING M6).

    Depends on all selected unit-inventory jobs (the runner enforces this via
    job dependencies). Payload: ``source_set_id`` plus optional ``brief``,
    ``mode``, ``apply``, ``create_goal``. Emits the dependency-closed proposal
    through the existing pipeline; the manifest hash is the agent-run cache seam
    so an identical manifest re-drains at zero tokens."""

    from learnloop import provenance

    with provenance.trace_scope(_build_trace_id(ctx)):
        return _bootstrap_synthesis(ctx)


def _bootstrap_synthesis(ctx: JobContext) -> dict[str, Any]:
    from learnloop.content.synthesis.source_set_synthesis import (
        StudyMapError,
        create_study_map,
        revalidate_synthesis_candidate,
    )

    payload = ctx.payload
    source_set_id = str(payload.get("source_set_id") or "").strip()
    if not source_set_id:
        raise IngestRunnerError("bootstrap_synthesis job requires a 'source_set_id'.")
    from learnloop.content.pipeline.add_source import AutoApplyGate, admit_auto_build_job, after_auto_build

    if not payload.get("reuse_candidate"):
        # A model run: automatic builds are admitted again (kill switch, Undo
        # generation, money) on every attempt.
        admit_auto_build_job(ctx)

    # `auto` is a product journey, not an alias for bootstrap: once this subject
    # has a live map, new sources reconcile into it through the bounded append
    # vocabulary instead of re-creating it with bootstrap.
    if str(payload.get("mode") or "auto") == "auto" and not payload.get("reuse_candidate"):
        from learnloop.content.synthesis.source_append import subject_has_applied_study_map
        from learnloop.vault.loader import load_vault

        vault = load_vault(ctx.vault_root)
        source_set = next((item for item in vault.source_sets if item.id == source_set_id), None)
        if source_set is not None and subject_has_applied_study_map(vault, source_set.subject_id):
            return _append_synthesis(ctx)

    ctx.report("inventoried", message="Preparing study-map synthesis")
    try:
        if payload.get("reuse_candidate") and payload.get("synthesis_run_id"):
            # Recovery path: finish the pipeline from the preserved candidate —
            # no provider client and ZERO model calls.
            ctx.report("synthesized", message="Revalidating the preserved synthesis candidate")
            result = revalidate_synthesis_candidate(
                ctx.vault_root,
                str(payload["synthesis_run_id"]),
                apply=bool(payload.get("apply", False)),
                apply_gate=AutoApplyGate(ctx),
                create_goal=bool(payload.get("create_goal", False)),
                repair=bool(payload.get("repair_candidate", False)),
                repair_ops=[dict(op) for op in payload.get("repair_ops") or []],
                repository=ctx.repo,
                clock=ctx.clock,
                progress=_synthesis_progress(ctx),
            )
        else:
            client = ctx.services.synthesis_client(ctx)
            result = create_study_map(
                ctx.vault_root,
                source_set_id,
                client=client,
                brief=payload.get("brief") or {},
                mode=str(payload.get("mode") or "auto"),
                apply=bool(payload.get("apply", False)),
                apply_gate=AutoApplyGate(ctx),
                create_goal=bool(payload.get("create_goal", False)),
                repository=ctx.repo,
                clock=ctx.clock,
                budget_overrides=dict(payload.get("synthesis_budgets") or {}),
                unlimited_token_budget=bool(payload.get("unlimited_token_budget", False)),
                progress=_synthesis_progress(ctx),
            )
    except StudyMapError as exc:
        raise IngestRunnerError(
            str(exc),
            code=exc.code,
            details={
                "diagnostics": exc.diagnostics,
                "stage": "synthesis",
                "completed_dependencies_preserved": True,
                "candidate_preserved": exc.candidate_preserved,
                "synthesis_run_id": exc.synthesis_run_id,
            },
            # Every bootstrap failure is retryable (the identity-lock refusal,
            # the one that was not, went with facet locks).
            retryable=True,
        ) from exc

    run = ctx.repo.synthesis_run(result.synthesis_run_id) if result.synthesis_run_id else None
    ctx.record_usage(
        (run or {}).get("actual_usage")
        or {"calls": 0 if result.reused else ((result.item_counts and 1) or 0)}
    )
    ctx.report("synthesized", message="Study map synthesized")
    if result.nothing_new:
        ctx.report("applied", message="Nothing new: the study map already holds this build")
    elif result.applied:
        ctx.report("applied", message="Study map applied")
    else:
        ctx.report("proposed", message="Study-map proposal ready for review")
    after_auto_build(ctx)
    return result.as_dict()


# Synthesis-service progress stages -> checkpoint-ladder phases. Shard work
# happens between "inventoried" and "synthesized"; gates run after the model
# output exists; persistence/apply match their ladder rungs.
_SYNTH_STAGE_PHASE = {
    "synthesis": "inventoried",
    "validation": "synthesized",
    "persistence": "proposed",
    "apply": "applied",
}


def _synthesis_progress(ctx: JobContext):
    """A ProgressFn bridging create_study_map to the durable job heartbeat.

    Every callback refreshes the lease and re-checks cancellation, so a long
    multi-shard synthesis can be cancelled at the next shard boundary instead
    of only before/after the whole model stage."""

    def progress(stage: str, message: str, current: int | None = None, total: int | None = None, *,
                 step: str | None = None, drafted_topics: int | None = None) -> None:
        ctx.report(
            _SYNTH_STAGE_PHASE.get(stage, "inventoried"),
            message=message,
            current_window=current,
            total_windows=total,
        )
        if step is not None:
            _record_step(ctx, step=step, drafted_topics=drafted_topics)

    # The synthesis names its step to a progress function that takes one (``source_set_synthesis._notify``).
    progress.takes_step = True  # type: ignore[attr-defined]
    return progress


def _record_step(ctx: JobContext, **facts: Any) -> None:
    """What the job is doing, for a waiting screen (``ingest_job_progress``); never a reason for the job to fail."""

    try:
        ctx.repo.record_ingest_job_progress(ctx.job_id, attempt_count=int(ctx.job.get("attempt_count") or 0),
                                            clock=ctx.clock, **facts)
    except Exception:  # noqa: BLE001 - what a wait shows never stops the work it shows
        logging.getLogger(__name__).warning("Could not record the progress of ingest job %s", ctx.job_id, exc_info=True)


def handle_append_synthesis(ctx: JobContext) -> dict[str, Any]:
    """append_synthesis: bounded reconciliation against an existing study map."""

    from learnloop import provenance

    with provenance.trace_scope(_build_trace_id(ctx)):
        return _append_synthesis(ctx)


def _append_synthesis(ctx: JobContext) -> dict[str, Any]:
    from learnloop.content.synthesis.source_append import APPEND_INPUT_OVER_CEILING, append_source
    from learnloop.content.synthesis.source_set_synthesis import StudyMapError

    from learnloop.content.pipeline.add_source import AutoApplyGate, admit_auto_build_job, after_auto_build

    payload = ctx.payload
    source_set_id = str(payload.get("source_set_id") or payload.get("set_id") or "").strip()
    if not source_set_id:
        raise IngestRunnerError("append_synthesis job requires a 'source_set_id'.")
    # Idempotent when the bootstrap lane already admitted this attempt.
    admit_auto_build_job(ctx)
    ctx.report("inventoried", message="Preparing bounded source reconciliation")
    client = ctx.services.synthesis_client(ctx)
    try:
        result = append_source(
            ctx.vault_root,
            source_set_id,
            client=client,
            new_revision_ids=[str(value) for value in payload.get("new_revision_ids") or []] or None,
            # {revision_id: [unit_id]}: the units a planned build chose. Absent
            # (an explicit append, a job queued before the filter), every unit
            # of the revisions goes.
            new_unit_ids=(
                {str(revision): [str(unit) for unit in units] for revision, units in payload["new_unit_ids"].items()}
                if isinstance(payload.get("new_unit_ids"), Mapping) else None
            ),
            change_kind=str(payload.get("change_kind") or "source_added"),
            revision_diff=dict(payload.get("revision_diff") or {}),
            brief=dict(payload.get("brief") or {}),
            auto_apply=bool(payload.get("apply", payload.get("auto_apply", True))),
            apply_gate=AutoApplyGate(ctx),
            repository=ctx.repo,
            clock=ctx.clock,
            budget_overrides=dict(payload.get("synthesis_budgets") or {}),
            unlimited_token_budget=bool(payload.get("unlimited_token_budget", False)),
        )
    except StudyMapError as exc:
        # Same mapping as the bootstrap lane above. Flattening the code into the
        # message left every append failure as `invalid_job`, dropped the gate
        # diagnostics the Activity panel renders, and asserted retryable=False
        # for a gate rejection. A gate rejection drops the answer it judged, so
        # a retry pays for a fresh one; a retry after any other failure reads
        # the checkpointed answer (zero calls). An input over
        # append_input_ceiling refuses the same way every time.
        raise IngestRunnerError(
            str(exc),
            code=exc.code,
            details={
                "diagnostics": exc.diagnostics,
                "stage": "synthesis",
                "completed_dependencies_preserved": True,
                "synthesis_run_id": exc.synthesis_run_id,
            },
            retryable=exc.code not in {"source_set_not_found", APPEND_INPUT_OVER_CEILING},
        ) from exc
    ctx.record_usage({"calls": result.calls})
    ctx.report("synthesized", message="Source reconciliation synthesized")
    if result.nothing_new:
        ctx.report("applied", message="Nothing new: the study map already holds this update")
    elif result.auto_applied_item_ids:
        ctx.report("applied", message="Safe source additions applied")
    else:
        ctx.report("proposed", message="Source reconciliation ready for review")
    after_auto_build(ctx)
    return result.as_dict()
