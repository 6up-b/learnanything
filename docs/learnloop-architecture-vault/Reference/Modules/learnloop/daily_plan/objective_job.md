---
title: "learnloop.daily_plan.objective_job"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/objective_job.py"
source_paths:
  - "src/learnloop/daily_plan/objective_job.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.daily_plan"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.daily_plan.objective_job module"
  - "src/learnloop/daily_plan/objective_job.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.objective_job`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.objective_job` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: The objective router's job at a block boundary: its threads, its deadlines, its early answer and its carried valuations.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/objective_job.py](../../../../../../src/learnloop/daily_plan/objective_job.py) |
| Source lines | 494 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class NumericPolicy` ([source](../../../../../../src/learnloop/daily_plan/objective_job.py), line 77) — What π_Q computed for one decision (its status, choice, evaluation and the trace's sections).
- `pooled(config: Any) -> Any` ([source](../../../../../../src/learnloop/daily_plan/objective_job.py), line 111) — Router speed stage 2, item 4 (its Codex review F2): the objective job's connection pool (``db.connection.reused_connections``) only at the follow-up batch's tag with ``[router_objective] pooled_connections``; off, a connection opened at every ``connect()`` (main e9ceaf8d44's job…
- `carry_on(config: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/objective_job.py), line 269)
- `drain_carry(sqlite_path: Any, *, deadline: float | None=None) -> int` ([source](../../../../../../src/learnloop/daily_plan/objective_job.py), line 286) — Run every deferred carried valuation of this database not yet run (a prefetch job's, after its own answer released the serve's wait; the no-model branch's thread, after its serve), each by ``deadline`` (the runner's own).
- `carried_for(repository: Any, decision_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/objective_job.py), line 310) — The deferred carried valuations ready to be recorded in this decision's trace (``carried_for``).
- `job_answers(entry: Any, readiness: Mapping[str, str | None]) -> tuple[dict[str, ComponentResult], str, NumericPolicy | None]` ([source](../../../../../../src/learnloop/daily_plan/objective_job.py), line 380) — What a serve takes from its job: every component's result (one still out is a timeout; a model not asked is ``not_ready`` with the readiness reason), the wall time they were taken, and the numeric answer that serves (:func:`_numeric_answer`) with its carried valuation if the job…
- `start_job(runtime: RouterRuntime, scope: str, key: str, *, vault: Any, sqlite_path: Any, session_id: str | None, plan_id: str | None, material: dict[str, Any], ready: tuple[str, ...], reads: Callable[[], Any], build_policy_request: Callable[[Any, Any, Prefetch], Any], numeric_policy: Callable[..., NumericPolicy]) -> Prefetch` ([source](../../../../../../src/learnloop/daily_plan/objective_job.py), line 394) — Register one boundary's job and start it (once per key): the asked models and the numeric policy, by ``router.prefetch_timeout_seconds`` from now.
- `await_job(runtime: RouterRuntime, entry: Prefetch, *, may_defer: bool, config: Any) -> None` ([source](../../../../../../src/learnloop/daily_plan/objective_job.py), line 416) — A step's wait for its boundary's job: none once it is complete; a read or a prefetch (``may_defer``) before the deadline leaves the decision open (``DecisionPending``); a serve waits up to ``router.timeout_seconds``.
- `answer_without_models(runtime: RouterRuntime, key: str, *, config: Any, card: Any, now_iso: str, numeric: Callable[..., NumericPolicy], tail_snapshot: Callable[[], Any]) -> _NoModels` ([source](../../../../../../src/learnloop/daily_plan/objective_job.py), line 423) — No model is set up, so no job: the numeric policy (``numeric``, bound to the boundary's inputs) runs on this thread by ``router.timeout_seconds`` from now, with no refinement (nothing is out).
- `defer_carry(numeric: NumericPolicy, entry: Any, decision_id: str, *, runtime: RouterRuntime, sqlite_path: Any, config: Any) -> NumericPolicy` ([source](../../../../../../src/learnloop/daily_plan/objective_job.py), line 447) — A decision served before its carried valuation existed hands it to the next boundary's job (with no models, to a thread of its own started after this decision), off the serving path; a later decision's trace records it.
- `join_carried(timeout: float | None=None) -> bool` ([source](../../../../../../src/learnloop/daily_plan/objective_job.py), line 477) — Wait for the carried valuations running on threads of their own (each up to ``timeout``; None: until done) and say whether none is still running.

### Module constants

- `LOG` ([src/learnloop/daily_plan/objective_job.py](../../../../../../src/learnloop/daily_plan/objective_job.py), line 57)
- `NUMERIC` ([src/learnloop/daily_plan/objective_job.py](../../../../../../src/learnloop/daily_plan/objective_job.py), line 59)
- `PUBLISHED` ([src/learnloop/daily_plan/objective_job.py](../../../../../../src/learnloop/daily_plan/objective_job.py), line 62)
- `CARRIED` ([src/learnloop/daily_plan/objective_job.py](../../../../../../src/learnloop/daily_plan/objective_job.py), line 65)
- `CARRY_LIMIT` ([src/learnloop/daily_plan/objective_job.py](../../../../../../src/learnloop/daily_plan/objective_job.py), line 71)
- `_CARRY_LOCK` ([src/learnloop/daily_plan/objective_job.py](../../../../../../src/learnloop/daily_plan/objective_job.py), line 72)
- `_CARRY` ([src/learnloop/daily_plan/objective_job.py](../../../../../../src/learnloop/daily_plan/objective_job.py), line 73)
- `_CARRY_THREADS` ([src/learnloop/daily_plan/objective_job.py](../../../../../../src/learnloop/daily_plan/objective_job.py), line 444)

### Explicit exports

`__all__` declares:

- `CARRIED`
- `CARRY_LIMIT`
- `NUMERIC`
- `PUBLISHED`
- `NumericPolicy`
- `answer_without_models`
- `await_job`
- `carried_for`
- `carry_on`
- `defer_carry`
- `drain_carry`
- `job_answers`
- `join_carried`
- `pooled`
- `start_job`

## Internal implementation anchors

- `_llm_forecasts(entry: Prefetch) -> Any` ([source](../../../../../../src/learnloop/daily_plan/objective_job.py), line 128) — The numeric job's view of the LLM policy's forecasts: None while it is out, else ``(per option, reference)`` (both None when it failed).
- `_objective_job(entry: Prefetch, *, runtime: RouterRuntime, vault: Any, sqlite_path: Any, session_id: str | None, plan_id: str | None, reads: Callable[[], Any], build_policy_request: Callable[[Any, Any, Prefetch], Any], numeric_policy: Callable[..., NumericPolicy]) -> None` ([source](../../../../../../src/learnloop/daily_plan/objective_job.py), line 143)
- `_with_carried(numeric: 'NumericPolicy | None', entry: Any) -> 'NumericPolicy | None'` ([source](../../../../../../src/learnloop/daily_plan/objective_job.py), line 248) — Landing ruling R12: the served answer's residual with the carried valuation if the job had it before this serve (``CARRIED``), else marked valued too late (``not_valued_before_the_serve``: the backup into this decision is censored ``cutoff_unmatched``).
- `_register_carry(sqlite_path: Any, decision_id: str, compute: Callable[[], dict[str, Any]]) -> None` ([source](../../../../../../src/learnloop/daily_plan/objective_job.py), line 276) — The follow-up batch's item 4: a decision served before its carried valuation existed leaves the valuation (its own frozen inputs, in ``compute``) to the next boundary's prefetch.
- `_wait_llm(entry: Prefetch, runtime: RouterRuntime) -> Any` ([source](../../../../../../src/learnloop/daily_plan/objective_job.py), line 346)
- `_numeric_answer(entry: Any, results: dict[str, ComponentResult]) -> 'NumericPolicy | None'` ([source](../../../../../../src/learnloop/daily_plan/objective_job.py), line 353) — The numeric policy's answer a serve takes: the no-model branch's own, the job's final one, or, while the job still waits on the LLM policy's forecasts for its optional correction, its uncorrected publication, labelled ``published_uncorrected`` (``results`` then names it answered…

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `NUMERIC`, `NumericPolicy`, `module`; statically calls `NumericPolicy`, `answer_without_models`, `await_job`, `carried_for`, `carry_on`, `defer_carry`, `job_answers`, `start_job`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]] — imports `_NoModels`, `_await`; calls `_NoModels`, `_await`
- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `ANSWERED`, `ComponentResult`, `DECIDER`, `FAILED`, `INVALID`, `LLM`, `NOT_READY`, `Prefetch`, `RECEIPT_OWNER`, `RouterRuntime`, `TIMEOUT`, `call_decider`, `call_llm`, `wall_now`; calls `ComponentResult`, `wall_now`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `reused_connections`; calls `reused_connections`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/router/requests|learnloop.router.requests]] — imports `module`; calls `BoundaryRequest`, `evidence_from_card`, `state_text`
- [[Reference/Modules/learnloop/router_objective/objective|learnloop.router_objective.objective]] — imports `module`
- [[Reference/Modules/learnloop/router_objective/price|learnloop.router_objective.price]] — imports `module`
- [[Reference/Modules/learnloop/router_objective/tail_data|learnloop.router_objective.tail_data]] — imports `module`; calls `carried_in_prefetch_on`
- [[Reference/Modules/learnloop/router_objective/tail_serve|learnloop.router_objective.tail_serve]] — imports `module`; calls `is_pending`, `not_before_the_serve`
- [[Reference/Modules/learnloop/router_objective/types|learnloop.router_objective.types]] — imports `module`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `followup_on`; calls `followup_on`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `contextvars`, `dataclasses`, `functools`, `logging`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/router_mixture_helpers.py](../../../../../../tests/router_mixture_helpers.py) — direct import
- [tests/test_ih4_preferences_inform_router.py](../../../../../../tests/test_ih4_preferences_inform_router.py) — direct import
- [tests/test_ro6_codex_review.py](../../../../../../tests/test_ro6_codex_review.py) — direct import
  - `test_f4_a_diagnosis_queued_after_the_decisions_moment_never_enters_its_features`
- [tests/test_rofu_carried.py](../../../../../../tests/test_rofu_carried.py) — direct import
  - `test_an_early_publication_served_keeps_its_carried_valuation`
- [tests/test_rospeed2_connections.py](../../../../../../tests/test_rospeed2_connections.py) — direct import
  - `test_the_job_opens_a_handful_of_connections`
  - `test_the_pool_and_the_held_map_follow_their_switches`
  - `test_the_pool_completes_more_draws_by_one_deadline_and_switched_off_is_mains`

## Modification guidance

- Make changes here when the responsibility remains objective job within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/objective_job.py](../../../../../../src/learnloop/daily_plan/objective_job.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
