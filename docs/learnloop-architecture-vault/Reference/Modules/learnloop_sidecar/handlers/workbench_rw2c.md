---
title: "learnloop_sidecar.handlers.workbench_rw2c"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/workbench_rw2c.py"
source_paths:
  - "src/learnloop_sidecar/handlers/workbench_rw2c.py"
source_commit: "5825048f775dc44bf0dc7d1a4b5bcaa1b0bf7b9f"
source_commit_timestamp: "2026-10-22T16:23:31-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.handlers.workbench_rw2c module"
  - "src/learnloop_sidecar/handlers/workbench_rw2c.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.workbench_rw2c`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.workbench_rw2c` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Reader workbench RW2c RPCs: what helps this learner (spec_reader_workbench_v1 §5.10, G39, G40).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/workbench_rw2c.py](../../../../../../src/learnloop_sidecar/handlers/workbench_rw2c.py) |
| Source lines | 332 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `5825048f775dc44bf0dc7d1a4b5bcaa1b0bf7b9f` |
| Commit timestamp | `2026-10-22T16:23:31-04:00` |

## Public API

- `start_example_after_hint(ctx: SidecarContext, meta: Any, result: dict[str, Any], *, after_job_id: str | None=None) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_rw2c.py), line 118) — After a shown hint at level 3 or higher in the Reader, the example in the background (never delaying the hint); None when it does not apply.
- `class ShowExampleInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_rw2c.py), line 145)
- `show_example(ctx: SidecarContext, params: ShowExampleInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_rw2c.py), line 151) — "Show me a similar example" (§5.10): a job, read with ``workbench.help_job``.
- `class AnotherPassageInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_rw2c.py), line 166)
- `another_passage(ctx: SidecarContext, params: AnotherPassageInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_rw2c.py), line 172) — "another passage": the next of a draw's options (no search, no call).
- `class CompareInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_rw2c.py), line 221)
- `compare_offer(ctx: SidecarContext, params: CompareInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_rw2c.py), line 226) — Whether "Compare with the book's method" is offered for the attempt.
- `open_compare_methods(ctx: SidecarContext, params: CompareInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_rw2c.py), line 237) — Open the comparison: the reveal on the item is written with its row BEFORE the reference is returned; the lines follow as a job.

### Module constants

- `BRIDGE_WAIT_SECONDS` ([src/learnloop_sidecar/handlers/workbench_rw2c.py](../../../../../../src/learnloop_sidecar/handlers/workbench_rw2c.py), line 45)
- `WORKBENCH_RW2C_RPCS` ([src/learnloop_sidecar/handlers/workbench_rw2c.py](../../../../../../src/learnloop_sidecar/handlers/workbench_rw2c.py), line 48)

### Explicit exports

`__all__` declares:

- `WORKBENCH_RW2C_RPCS`
- `start_example_after_hint`

## Internal implementation anchors

- `_start_job(ctx: SidecarContext, kind: str, session_id: str, item_id: str, work: Callable[[Any, Callable[[], bool]], dict[str, Any]]) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_rw2c.py), line 56)
- `_example_work(ctx: SidecarContext, vault: Any, *, session_id: str, item: Any, trigger: str, about_step_id: str | None, hint_assist_id: str | None, after: Any | None=None, verdicts: list[dict[str, Any]] | None=None)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_rw2c.py), line 63)
- `_live_example_vault(ctx: SidecarContext, worker_repo: Any, session_id: str, item_id: str) -> Any | None` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_rw2c.py), line 95) — The sidecar's CURRENT vault while an example may still be searched for the problem: the same database, help and examples (with the sources spec's S3) on, the item still there and the problem's statement not withheld; otherwise None (fix round 2, 1).
- `_withheld_options(vault: Any, repository: Any, item: Any, session_id: str, assist_id: str) -> set[str]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_rw2c.py), line 201) — Fix round 2 (2): the cached options of the passage on screen that may not be shown NOW (exam or held-out material, the item's own passages, an exercise or solution, the answer; :func:`passage_draw.option_withheld`), read before the pick's transaction, with no search and no model…
- `_live_compare_vault(ctx: SidecarContext, worker_repo: Any) -> Any | None` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_rw2c.py), line 290) — The sidecar's CURRENT vault while compare methods may still call: the same database, help and compare methods on; else None (L4).
- `_refuse_withheld_attempt(vault: Any, repository: Any, attempt_id: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_rw2c.py), line 305) — Fix round 3 (L6): the compare RPCs pass the workbench's statement gate (``_refuse_withheld_exercise``) on the attempt's problem, as every statement-bearing workbench RPC does.
- `_compare_jobs(ctx: SidecarContext) -> dict[str, str]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_rw2c.py), line 322) — The comparison lines job kept for each comparison (assist id -> job id).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]] — imports `start_example_after_hint`; statically calls `start_example_after_hint`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/help_assists|learnloop.db.stores.help_assists]] — imports `assist`; calls `assist`
- [[Reference/Modules/learnloop/db/stores/workbench|learnloop.db.stores.workbench]] — imports `module`; calls `session_for_attempt`
- [[Reference/Modules/learnloop/reader/workbench|learnloop.reader.workbench]] — imports `module`; calls `session_row`, `submission_id_for`
- [[Reference/Modules/learnloop/workbench/bridge|learnloop.workbench.bridge]] — imports `COMPARE_LINE`
- [[Reference/Modules/learnloop/workbench/check|learnloop.workbench.check]] — imports `module`; calls `daily_envelope`, `session_calls`
- [[Reference/Modules/learnloop/workbench/compare_methods|learnloop.workbench.compare_methods]] — imports `compare_enabled`, `module`; calls `compare_enabled`, `compare_lines`, `offer`, `open_comparison`
- [[Reference/Modules/learnloop/workbench/ladder|learnloop.workbench.ladder]] — imports `module`; calls `bridge_view`, `help_enabled`, `hint_context`, `live_workbench_steps`
- [[Reference/Modules/learnloop/workbench/passage_draw|learnloop.workbench.passage_draw]] — imports `module`; calls `another_passage`, `option_withheld`, `options_of`
- [[Reference/Modules/learnloop/workbench/route_example|learnloop.workbench.route_example]] — imports `module`; calls `available`, `example_for`, `example_line`, `example_view`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `to_camel`, `versioned`; calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `_refuse_withheld_exercise`; calls `_refuse_withheld_exercise`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]] — imports `module`; calls `_JobMeta`, `_guard`, `_jobs`, `_meta`, `_payload`, `_require`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_rw2c_rpcs_are_all_of_them`
- [tests/test_rw2c_fix_round3.py](../../../../../../tests/test_rw2c_fix_round3.py) — direct import
  - `test_l8_an_example_that_cannot_start_never_fails_the_delivered_hints_read`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/workbench_rw2c.py](../../../../../../src/learnloop_sidecar/handlers/workbench_rw2c.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
