---
title: "learnloop_sidecar.handlers.workbench_help"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/workbench_help.py"
source_paths:
  - "src/learnloop_sidecar/handlers/workbench_help.py"
source_commit: "5fe3a22558905593434e76e97a9375a41bf0354f"
source_commit_timestamp: "2026-11-08T19:24:01-05:00"
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
  - "learnloop_sidecar.handlers.workbench_help module"
  - "src/learnloop_sidecar/handlers/workbench_help.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.workbench_help`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.workbench_help` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Reader workbench RW2b RPCs: "Check my work" and the help ladder (spec_reader_workbench_v1 §5.2-5.6).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/workbench_help.py](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py) |
| Source lines | 724 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `5fe3a22558905593434e76e97a9375a41bf0354f` |
| Commit timestamp | `2026-11-08T19:24:01-05:00` |

## Public API

- `class WorkbenchCheckInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 179)
- `workbench_check(ctx: SidecarContext, params: WorkbenchCheckInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 184) — "Check my work" (``Ctrl+K``, a job): the steps' verdicts, counted as one hint once shown.
- `class SuggestHelpInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 211)
- `suggest_help(ctx: SidecarContext, params: SuggestHelpInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 232) — Help opened (``Ctrl+H``): the five rungs at once, and the suggested rung when the chooser returns (a job; the ladder works without it).
- `class RequestHelpInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 269)
- `request_help(ctx: SidecarContext, params: RequestHelpInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 288) — Take a rung (choose and take are separate keys on the ladder), reply to a hint or pick the book's way or a smaller step (a job).
- `class HelpJobInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 360)
- `help_job(ctx: SidecarContext, params: HelpJobInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 540) — A check, suggestion, hint or bridge job's state, at once (never a wait).
- `cancel_help(ctx: SidecarContext, params: HelpJobInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 565) — Cancel a check or hint before it is shown: never delivered, its row stays unshown and counts nothing.
- `class WorkbenchDiscriminateInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 639)
- `answer_discriminating(ctx: SidecarContext, params: WorkbenchDiscriminateInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 646) — The learner's answer to a question before a hint (§5.8): an assist row on the question's step, never a step and never the submitted answer; it moves no posterior and writes no probe observation.
- `class WorkbenchHelpStyleInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 664)
- `set_help_style(ctx: SidecarContext, params: WorkbenchHelpStyleInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 670) — The header's help style for this problem only (D31); null follows the stored preference again.
- `class WorkbenchHelpStateInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 682)
- `help_state(ctx: SidecarContext, params: WorkbenchHelpStateInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 687) — What a resumed problem restores (§5.1 "the same assistance history"): the last shown check and every shown hint under its step.

### Module constants

- `LOG` ([src/learnloop_sidecar/handlers/workbench_help.py](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 50)
- `WORKBENCH_HELP_RPCS` ([src/learnloop_sidecar/handlers/workbench_help.py](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 53)
- `PASSAGE_JOBS` ([src/learnloop_sidecar/handlers/workbench_help.py](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 68)

### Explicit exports

`__all__` declares:

- `WORKBENCH_HELP_RPCS`

## Internal implementation anchors

- `class _JobMeta` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 72)
- `_jobs(ctx: SidecarContext) -> HintJobs` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 81)
- `_meta(ctx: SidecarContext) -> dict[str, _JobMeta]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 89)
- `_guard(ctx: SidecarContext)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 97) — The common switch guard of all eight RPCs: with ``workbench.help_enabled`` (or ``workbench.enabled``) off, refuse ``help_disabled`` before anything is read or changed (fix round 4, item 7: ``workbench.cancel_help`` too).
- `_live_symbolic_switch(ctx: SidecarContext) -> Callable[[], bool]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 108) — Fix round 12: the sidecar's CURRENT ``workbench.symbolic_checks_enabled`` (after a reload too), for a job that outlives a switch change.
- `_require(ctx: SidecarContext, session_id: str, *, bound: bool=True, open_: bool=True)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 121)
- `_start(ctx: SidecarContext, kind: str, session: dict[str, Any], item: Any, work: Callable[[Any, Callable[[], bool]], dict[str, Any]], *, book_way: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 143)
- `_diagnostic_block(repository: Any, item: Any) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 150)
- `_queue_stuck(ctx: SidecarContext, vault: Any, repository: Any, session_id: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 156) — In-session updates (§5.2): the stuck steps' newest text to learner-text gaps.
- `_queue_text(ctx: SidecarContext, vault: Any, repository: Any, source_id: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 166)
- `_hint_clients(ctx: SidecarContext) -> tuple[Any, Any, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 217)
- `_context_labels(context: hint_workbench.WorkbenchHintContext) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 224)
- `_immediate(result: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 364)
- `class _RevealNotRecorded(Exception)` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 368)
- `_deliver(ctx: SidecarContext, meta: _JobMeta, assist_id: str, *, hint: bool) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 372) — Show a prepared workbench row; a hint's key overlap goes to the reveal ledger in the same transaction (a failed reveal shows nothing).
- `_check_payload(ctx: SidecarContext, meta: _JobMeta, result: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 401)
- `_payload(ctx: SidecarContext, job_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 416)
- `_rw2c_fields_now(vault: Any, kind: str, result: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 513) — RW2c fix round 2 (3): a cached job result carries RW2c's fields only while their switches are on NOW (a reload may have turned them off since the job finished): a hint's example job, a bridge's draw and book, an example's draw.
- `_record(ctx: SidecarContext, session_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 532)
- `_start_bridge(ctx: SidecarContext, meta: _JobMeta, hint_assist_id: str) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 586) — "Compare with the book" (§5.2 bridging): in the background after a hint is shown in the Reader, never delaying it.
- `_show_bridge(repository: Any, assist_id: str, *, kind: str=BRIDGE, book_session_id: str | None=None) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 624)
- `_example_state(vault: Any, repository: Any, session: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py), line 714)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]] — imports `module`; statically calls `_JobMeta`, `_guard`, `_jobs`, `_meta`, `_payload`, `_require`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `record_reveal_strict`, `reveal_episode_id`; calls `record_reveal_strict`, `reveal_episode_id`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/help_assists|learnloop.db.stores.help_assists]] — imports `assist`, `mark_bridge_shown`, `workbench_rows`; calls `assist`, `mark_bridge_shown`, `workbench_rows`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `enqueue_workbench_text`; calls `enqueue_workbench_text`
- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `HintRequestError`, `HintRequestV1`, `adaptive_enabled`, `module`; calls `HintRequestV1`, `HintResultV1`, `adaptive_enabled`, `default_chooser_client`, `hints_envelope`, `record_discriminate_answer`, `request_hint`, `reveal_amount`, `reveal_exempt`, `shown_text`, `undelivered_result`
- [[Reference/Modules/learnloop/hints/state|learnloop.hints.state]] — imports `assemble_state`; calls `assemble_state`
- [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]] — imports `module`; calls `apply_context`, `current_map_for`, `deliver_workbench`, `reveal_basis`, `step_labels`, `suggest`, `symbolic_enabled`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/reader/workbench|learnloop.reader.workbench]] — imports `module`; calls `count_book_passage`, `log_help_offered`, `session_row`, `set_help_style`, `submission_id_for`
- [[Reference/Modules/learnloop/symbolic_view|learnloop.symbolic_view]] — imports `hint_result_view`, `switch`; calls `hint_result_view`, `switch`
- [[Reference/Modules/learnloop/workbench/bridge|learnloop.workbench.bridge]] — imports `bridge_for_hint`; calls `bridge_for_hint`
- [[Reference/Modules/learnloop/workbench/check|learnloop.workbench.check]] — imports `module`; calls `check_view`, `daily_envelope`, `hint_claim_verifier`, `run_check`, `session_calls`
- [[Reference/Modules/learnloop/workbench/compare_methods|learnloop.workbench.compare_methods]] — imports `compare_enabled`; calls `compare_enabled`
- [[Reference/Modules/learnloop/workbench/ladder|learnloop.workbench.ladder]] — imports `module`; calls `fallback_level`, `help_enabled`, `hint_context`, `hint_views`, `last_shown_check`, `live_workbench_steps`, `passage_draw_enabled`, `queue_stuck_texts`, `served_claims`, `standalone_examples`, `unavailable_message`
- [[Reference/Modules/learnloop/workbench/route_example|learnloop.workbench.route_example]] — imports `module`; calls `examples_enabled`, `s3_available`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `to_camel`, `versioned`; calls `to_camel`, `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `HintJobs`, `_as_sidecar_error`; calls `HintJobs`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `_in_diagnostic_block`; calls `_in_diagnostic_block`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `_refuse_withheld_exercise`, `_run`, `record_line`; calls `_refuse_withheld_exercise`, `_run`, `record_line`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]] — imports `start_example_after_hint`; calls `start_example_after_hint`
- [[Reference/Modules/learnloop_sidecar/logging|learnloop_sidecar.logging]] — imports `log_event`; calls `log_event`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `dataclasses`, `logging`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_rw2b_rpcs_are_all_of_them`
- [tests/test_reader_rw2b_review.py](../../../../../../tests/test_reader_rw2b_review.py) — direct import
  - `test_f9_the_search_takes_its_place_before_it_runs_so_a_second_one_is_refused`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/workbench_help.py](../../../../../../src/learnloop_sidecar/handlers/workbench_help.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
