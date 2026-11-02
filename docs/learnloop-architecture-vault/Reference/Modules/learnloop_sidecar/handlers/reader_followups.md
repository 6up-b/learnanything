---
title: "learnloop_sidecar.handlers.reader_followups"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/reader_followups.py"
source_paths:
  - "src/learnloop_sidecar/handlers/reader_followups.py"
source_commit: "fe0ac0f01bcff2dd7e0e322678f5c3449ca59299"
source_commit_timestamp: "2026-11-01T02:09:08-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop_sidecar.handlers.reader_followups module"
  - "src/learnloop_sidecar/handlers/reader_followups.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.reader_followups`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.reader_followups` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Reader workbench RW6b part 1: cold follow-ups (spec_reader_workbench_v1 §9.3; UX §4.8-§4.9, S15).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/reader_followups.py](../../../../../../src/learnloop_sidecar/handlers/reader_followups.py) |
| Source lines | 238 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `fe0ac0f01bcff2dd7e0e322678f5c3449ca59299` |
| Commit timestamp | `2026-11-01T02:09:08-05:00` |

## Public API

- `prepare_followups(ctx: SidecarContext, vault: Any, repository: Any) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_followups.py), line 71) — Before the day's plan: re-value the pending follow-ups (once a local day, no model call) and start planning any ended session in the background.
- `class ReaderFollowupsInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_followups.py), line 150)
- `reader_followups(ctx: SidecarContext, params: ReaderFollowupsInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_followups.py), line 158) — "Coming up": a dated timeline, never a count.
- `class FollowupUndoInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_followups.py), line 171)
- `reader_followup_undo(ctx: SidecarContext, params: FollowupUndoInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_followups.py), line 177) — Undo one scheduled check; ``reason`` is the optional "why?".
- `class FollowupUndoAllInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_followups.py), line 187)
- `reader_followup_undo_all(ctx: SidecarContext, params: FollowupUndoAllInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_followups.py), line 193)
- `class FollowupRestoreInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_followups.py), line 201)
- `reader_followup_restore(ctx: SidecarContext, params: FollowupRestoreInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_followups.py), line 206) — Undo a retirement (or an undo): the check is pending again.
- `class FollowupsPlanInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_followups.py), line 217)
- `reader_followups_plan(ctx: SidecarContext, params: FollowupsPlanInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_followups.py), line 222) — Plan the ended sessions' follow-ups now (synchronously; paid relevance calls).

### Module constants

- `READER_RW6B_RPCS` ([src/learnloop_sidecar/handlers/reader_followups.py](../../../../../../src/learnloop_sidecar/handlers/reader_followups.py), line 42)
- `JOB_NAME` ([src/learnloop_sidecar/handlers/reader_followups.py](../../../../../../src/learnloop_sidecar/handlers/reader_followups.py), line 49)
- `_PLANNING` ([src/learnloop_sidecar/handlers/reader_followups.py](../../../../../../src/learnloop_sidecar/handlers/reader_followups.py), line 50)

### Explicit exports

`__all__` declares:

- `JOB_NAME`
- `READER_RW6B_RPCS`
- `prepare_followups`

## Internal implementation anchors

- `_now() -> datetime` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_followups.py), line 53)
- `_search(vault: Any, repository: Any) -> Any` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_followups.py), line 57)
- `_valuer(vault: Any, repository: Any) -> Any` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_followups.py), line 65)
- `_require_on(vault: Any) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_followups.py), line 145)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `prepare_followups`; statically calls `prepare_followups`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/instructional/reader_digest|learnloop.instructional.reader_digest]] — imports `module`; calls `admission_problem`, `digests_waiting`, `narrate_waiting`, `narrative_enabled`, `sessions_to_summarize`, `summarize_ended_sessions`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `module`; calls `coming_up`, `default_search`, `default_valuer`, `exposure_refresh_waiting`, `followups_enabled`, `plan_ended_sessions`, `refresh_exposure`, `restore_followup`, `revalue_pending`, `sessions_to_plan`, `undo_all`, `undo_followup`
- [[Reference/Modules/learnloop/instructional/wiring|learnloop.instructional.wiring]] — imports `find_practice_injections`; calls `find_practice_injections`
- [[Reference/Modules/learnloop_sidecar/background_jobs|learnloop_sidecar.background_jobs]] — imports `background_jobs`; calls `background_jobs`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/practice_index|learnloop_sidecar.handlers.practice_index]] — imports `plan_minutes_estimator`; calls `plan_minutes_estimator`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `logging`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_rw6b_rpcs_are_all_of_them`
- [tests/test_reader_digest_narrative.py](../../../../../../tests/test_reader_digest_narrative.py) — direct import
  - `test_the_background_job_narrates_waiting_sessions`
  - `test_the_queue_build_narrates_a_session_with_follow_ups_off`
  - `test_with_the_narrative_off_the_queue_build_starts_no_narration_job`
- [tests/test_reader_rw6b_p2_landing.py](../../../../../../tests/test_reader_rw6b_p2_landing.py) — direct import

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/reader_followups.py](../../../../../../src/learnloop_sidecar/handlers/reader_followups.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
