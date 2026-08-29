---
title: "learnloop_sidecar.handlers.sessions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/sessions.py"
source_paths:
  - "src/learnloop_sidecar/handlers/sessions.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-08-18"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop_sidecar.handlers.sessions module"
  - "src/learnloop_sidecar/handlers/sessions.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.sessions`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps sessions behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]]. Its public surface centers on `SessionStartInput`, `SessionIdInput`, `SessionCheckpointInput`, `start_session`, `get_session`, `update_session_checkpoint`, `clear_session_checkpoint`, `end_session` and 1 more public symbols.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/sessions.py](../../../../../../src/learnloop_sidecar/handlers/sessions.py) |
| Source lines | 264 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class SessionStartInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 12)
- `class SessionIdInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 19)
- `class SessionCheckpointInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 23)
- `start_session(ctx: SidecarContext, params: SessionStartInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 35)
- `get_session(ctx: SidecarContext, params: SessionIdInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 55)
- `update_session_checkpoint(ctx: SidecarContext, params: SessionCheckpointInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 64)
- `clear_session_checkpoint(ctx: SidecarContext, params: SessionIdInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 71)
- `end_session(ctx: SidecarContext, params: SessionIdInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 78)
- `patch_checkpoint(repository, params: SessionCheckpointInput) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 108)

## Internal implementation anchors

- `_require_open_session(repository, session_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 135)
- `_merged_value(existing: dict[str, Any], params: SessionCheckpointInput, fields: set[str], name: str)` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 144)
- `_copy_mapping(value: dict[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 150)
- `_with_hints_used(focus: dict[str, Any] | None, hints_used: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 154)
- `_with_submission_id(focus: dict[str, Any] | None, submission_id: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 166) — Store the current attempt's stable retry key in the practice envelope.
- `_session_cold_checks(repository, session_id: str) -> dict[str, int]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 197) — Repair cold checks this session spent, and how many of them passed.
- `_session_followups_queued(repository, session_id: str) -> int` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 232)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `SessionCheckpointInput`, `patch_checkpoint`; statically calls `SessionCheckpointInput`, `patch_checkpoint`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `SessionCheckpointInput`, `_require_open_session`, `patch_checkpoint`; statically calls `SessionCheckpointInput`, `_require_open_session`, `patch_checkpoint`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/goals/forecast_ledger|learnloop.goals.forecast_ledger]] — imports `issue_goal_forecasts`, `resolve_due_forecasts`; calls `issue_goal_forecasts`, `resolve_due_forecasts`
- [[Reference/Modules/learnloop/learner/session_learning_diff|learnloop.learner.session_learning_diff]] — imports `session_learning_diff`; calls `session_learning_diff`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`, `session_snapshot`; calls `session_snapshot`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]], [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_sidecar_remediation_surfaces.py](../../../../../../tests/test_sidecar_remediation_surfaces.py) — direct import
  - `test_session_counts_cold_checks_answered_and_confirmed_separately`
- [tests/test_sidecar_teach_back.py](../../../../../../tests/test_sidecar_teach_back.py) — direct import
  - `test_sidecar_teach_back_finish_retry_returns_same_attempt`
  - `test_sidecar_teach_back_resume_merges_pending_learner_answer`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/sessions.py](../../../../../../src/learnloop_sidecar/handlers/sessions.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
