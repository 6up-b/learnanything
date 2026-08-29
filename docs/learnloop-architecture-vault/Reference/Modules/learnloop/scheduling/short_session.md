---
title: "learnloop.scheduling.short_session"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/short_session.py"
source_paths:
  - "src/learnloop/scheduling/short_session.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.short_session module"
  - "src/learnloop/scheduling/short_session.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.short_session`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.short_session` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: P4 §12.2 -- the three-minute / short-session block-planner adapter (spec §12.2, §16.1 "one three-minute activity completes a session", §16.9).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/short_session.py](../../../../../../src/learnloop/scheduling/short_session.py) |
| Source lines | 117 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ShortSessionPlan` ([source](../../../../../../src/learnloop/scheduling/short_session.py), line 43) — The outcome of one short-session decision.
  - `as_dict(self) -> dict[str, Any]` (line 56; public)
- `plan_short_session(vault: LoadedVault, repository: Repository, session: Any, *, signals: sp.StateSignals | None=None, candidates: Sequence[cs.Candidate] | None=None, continuation: Mapping[str, Any] | None=None, diagnostic: sp.DiagnosticSelector | None=None, mode: str='shadow', owned_item_refs: set[str] | None=None, receipt_key: str | None=None, clock: Clock | None=None) -> ShortSessionPlan` ([source](../../../../../../src/learnloop/scheduling/short_session.py), line 70) — Plan one short session (§12.2).

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

No live LearnLoop module directly imports this module in the static graph.

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/scheduling/controller_actions|learnloop.scheduling.controller_actions]] — imports `module`
- [[Reference/Modules/learnloop/scheduling/controller_snapshot|learnloop.scheduling.controller_snapshot]] — imports `module`
- [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]] — imports `module`; calls `decide`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

No live LearnLoop module imports it directly; its current reach is tests, repository tooling, dynamic registration, or explicit manual invocation where documented above.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reentry_short_session.py](../../../../../../tests/test_reentry_short_session.py) — direct import
  - `test_short_session_prefers_admitted_short_p1_patterns`
  - `test_short_session_retry_after_commit_is_idempotent`
  - `test_short_session_stops_honestly_when_nothing_fits`
  - `test_three_minute_activity_completes_a_session`

## Modification guidance

- Change short session policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/short_session.py](../../../../../../src/learnloop/scheduling/short_session.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
