---
title: "learnloop_sidecar.prefetch_runtime"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/prefetch_runtime.py"
source_paths:
  - "src/learnloop_sidecar/prefetch_runtime.py"
source_commit: "cb5b8773979685c93c470bf76e9a5cf5840bb53c"
source_commit_timestamp: "2026-11-02T15:58:22-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
aliases:
  - "learnloop_sidecar.prefetch_runtime module"
  - "src/learnloop_sidecar/prefetch_runtime.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar"
---

# `learnloop_sidecar.prefetch_runtime`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.prefetch_runtime` exists within [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] to own the behavior summarized by its module contract: Reader RW5d P5: the desktop sidecar's prefetch runtime (spec_reader_show_me_figures_v1 §10b.1, §10b.4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/prefetch_runtime.py](../../../../../src/learnloop_sidecar/prefetch_runtime.py) |
| Source lines | 198 |
| Owning package | [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `cb5b8773979685c93c470bf76e9a5cf5840bb53c` |
| Commit timestamp | `2026-11-02T15:58:22-05:00` |

## Public API

- `class PrefetchRuntime` ([source](../../../../../src/learnloop_sidecar/prefetch_runtime.py), line 36) — One context's trigger queue and its single drain thread.
  - `__init__(self) -> None` (line 39; internal)
  - `running(self) -> bool` (line 47; public) — A pass is draining the queue now (Codex re-review F18: the Reader's ``prefetchPending``).
  - `submit(self, ctx: Any, trigger: Any) -> None` (line 53; public)
  - `_drain(self, ctx: Any, epoch: int | None) -> None` (line 68; internal)
- `environment(ctx: Any, epoch: int | None) -> Any` ([source](../../../../../src/learnloop_sidecar/prefetch_runtime.py), line 91) — The pass's environment from the context as loaded now (None: no vault, or switched off).
- `runs_here(ctx: Any) -> bool` ([source](../../../../../src/learnloop_sidecar/prefetch_runtime.py), line 133) — Whether prefetch runs in this context now (the desktop sidecar, the switch on, the env).
- `pass_running(ctx: Any) -> bool` ([source](../../../../../src/learnloop_sidecar/prefetch_runtime.py), line 145) — Whether this context's prefetch pass is running now (never creates the runtime).
- `notify(ctx: Any, kind: str, ref: str='', **fields: Any) -> bool` ([source](../../../../../src/learnloop_sidecar/prefetch_runtime.py), line 152) — Queue one trigger (spec §10b.2); False when prefetch does not run here (switched off, a phone or MCP host, no vault).
- `notify_offer(ctx: Any, origin: str, offer_ref: str | None) -> bool` ([source](../../../../../src/learnloop_sidecar/prefetch_runtime.py), line 171) — RW5b's offers (spec §10b.2): the blocks the tutor's answer or the library organizer's notes said were explorable, confirmed by their ledger rows (the press's own check), queued once per offer as an ``offer`` trigger.

### Module constants

- `_LOG` ([src/learnloop_sidecar/prefetch_runtime.py](../../../../../src/learnloop_sidecar/prefetch_runtime.py), line 33)
- `PREFETCH_ENV` ([src/learnloop_sidecar/prefetch_runtime.py](../../../../../src/learnloop_sidecar/prefetch_runtime.py), line 130)

### Explicit exports

`__all__` declares:

- `PREFETCH_ENV`
- `PrefetchRuntime`
- `environment`
- `notify`
- `notify_offer`
- `pass_running`
- `runs_here`

## Internal implementation anchors

- `_runtime(ctx: Any) -> PrefetchRuntime` ([source](../../../../../src/learnloop_sidecar/prefetch_runtime.py), line 119)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `notify`; statically calls `notify`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `notify`, `runs_here`; statically calls `notify`, `runs_here`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `pass_running`; statically calls `pass_running`
- [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]] — imports `notify`; statically calls `notify`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `notify_offer`; statically calls `notify_offer`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `notify`, `notify_offer`; statically calls `notify`, `notify_offer`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/figures/power|learnloop.figures.power]] — imports `module`; calls `prefetch_switch`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `Trigger`, `module`; calls `PrefetchEnv`, `Trigger`, `enabled`, `run_trigger`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `module`; calls `rich_enabled`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `_rich_spawner`, `offered_spans`, `retry_plan_wait`; calls `_rich_spawner`, `offered_spans`, `retry_plan_wait`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `logging`, `os`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]], [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]], [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]], [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]], [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figures_prefetch.py](../../../../../tests/test_figures_prefetch.py) — direct import
  - `test_reading_progress_queues_the_section_trigger_on_the_desktop_only`
- [tests/test_figures_prefetch_review_fixes.py](../../../../../tests/test_figures_prefetch_review_fixes.py) — direct import
  - `test_f11_reader_figures_says_a_prebuild_is_coming_until_it_lands`
  - `test_f15_figures_ahead_of_need_are_on_by_default_and_the_suite_keeps_hooks_inert`
  - `test_f18_an_unstarted_decision_is_pending_only_while_a_pass_runs_and_never_on_battery`
- [tests/test_followups_batch6_prefetch_plan_wait.py](../../../../../tests/test_followups_batch6_prefetch_plan_wait.py) — direct import
  - `test_the_runtime_wires_the_paced_requeue`
- [tests/test_followups_batch6_verify_fixes.py](../../../../../tests/test_followups_batch6_verify_fixes.py) — direct import
  - `test_v2_a_trigger_that_names_no_provenance_never_retries`
  - `test_v2_an_offer_from_the_learners_own_question_carries_learner_activity`
- [tests/test_followups_batch7_prefetch_link_served.py](../../../../../tests/test_followups_batch7_prefetch_link_served.py) — direct import

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/prefetch_runtime.py](../../../../../src/learnloop_sidecar/prefetch_runtime.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
