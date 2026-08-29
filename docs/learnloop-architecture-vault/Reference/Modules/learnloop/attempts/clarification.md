---
title: "learnloop.attempts.clarification"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/clarification.py"
source_paths:
  - "src/learnloop/attempts/clarification.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempts.clarification module"
  - "src/learnloop/attempts/clarification.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.clarification`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.clarification` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: A8 clarification channel — one question that resolves a hedged grade.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/clarification.py](../../../../../../src/learnloop/attempts/clarification.py) |
| Source lines | 505 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class Clarification` ([source](../../../../../../src/learnloop/attempts/clarification.py), line 79) — One clarification request, with its derived status.
  - `status(self, *, now: str) -> str` (line 95; public) — ``pending`` | ``awaiting_regrade`` | ``answered`` | ``timed_out``.
  - `as_dict(self, *, now: str) -> dict[str, Any]` (line 116; public)
- `row_to_clarification(row: Any) -> Clarification` ([source](../../../../../../src/learnloop/attempts/clarification.py), line 133)
- `record_clarification(repository: Repository, *, attempt_id: str, clarification: dict[str, Any], agent_run_id: str | None=None, grading_prompt_version: str | None=None, ttl_hours: int=DEFAULT_CLARIFICATION_TTL_HOURS, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/attempts/clarification.py), line 152) — Persist an accepted clarification request; returns its id (or None).
- `pending_clarification(repository: Repository, attempt_id: str, *, clock: Clock | None=None) -> Clarification | None` ([source](../../../../../../src/learnloop/attempts/clarification.py), line 191) — The attempt's clarification if it is still askable, else None.
- `answer_clarification(vault: LoadedVault, repository: Repository, *, attempt_id: str, answer_md: str, runtime=None, client=None, grading_source: str='codex', clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/clarification.py), line 208) — Record the learner's answer and re-grade the attempt with it in hand.
- `resolve_awaiting_regrades(vault: LoadedVault, repository: Repository, *, runtime=None, client=None, grading_source: str='codex', limit: int | None=None, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/attempts/clarification.py), line 341) — Re-drive every clarification whose answer landed but whose re-grade did not.
- `expire_clarifications(repository: Repository, *, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/attempts/clarification.py), line 424) — Clear the provisional grade state on every attempt with no live question.
- `clarification_rate(repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/clarification.py), line 476) — §3.A8's revert criterion, as a metric with an explicit unavailable arm.

### Module constants

- `DEFAULT_CLARIFICATION_TTL_HOURS` ([src/learnloop/attempts/clarification.py](../../../../../../src/learnloop/attempts/clarification.py), line 57)
- `CLARIFICATION_RATE_WARN_THRESHOLD` ([src/learnloop/attempts/clarification.py](../../../../../../src/learnloop/attempts/clarification.py), line 65)
- `CLARIFICATION_RATE_MIN_ATTEMPTS` ([src/learnloop/attempts/clarification.py](../../../../../../src/learnloop/attempts/clarification.py), line 69)
- `RESOLVED_OUTCOMES` ([src/learnloop/attempts/clarification.py](../../../../../../src/learnloop/attempts/clarification.py), line 75)

## Internal implementation anchors

- `_latest_grading_revision(repository: Repository, attempt_id: str) -> int | None` ([source](../../../../../../src/learnloop/attempts/clarification.py), line 325) — The highest grading revision now live on ``attempt_id``, or None.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `record_clarification`; statically calls `record_clarification`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `record_clarification`; statically calls `record_clarification`
- [[Reference/Modules/learnloop/cli/clarification|learnloop.cli.clarification]] — imports `clarification_rate`, `expire_clarifications`, `resolve_awaiting_regrades`, `row_to_clarification`; statically calls `clarification_rate`, `expire_clarifications`, `resolve_awaiting_regrades`, `row_to_clarification`
- [[Reference/Modules/learnloop/ops/startup|learnloop.ops.startup]] — imports `expire_clarifications`, `resolve_awaiting_regrades`; statically calls `expire_clarifications`, `resolve_awaiting_regrades`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `answer_clarification`, `pending_clarification`; statically calls `answer_clarification`, `pending_clarification`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `clarification_rate`; statically calls `clarification_rate`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `PROVISIONAL_PENDING_CLARIFICATION`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `regrade_attempt`; calls `regrade_attempt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]], [[Reference/Modules/learnloop/cli/clarification|learnloop.cli.clarification]], [[Reference/Modules/learnloop/ops/startup|learnloop.ops.startup]], [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_provider_resolution_parity.py](../../../../../../tests/test_provider_resolution_parity.py) — direct import
  - `test_config_matrix_executes_all_six_production_resolution_paths`
- [tests/test_sidecar_trace_and_clarification.py](../../../../../../tests/test_sidecar_trace_and_clarification.py) — direct import
  - `test_an_answer_recorded_without_a_grader_is_awaiting_regrade_not_answered`
  - `test_the_retry_queue_is_empty_without_a_grader_rather_than_erroring`
  - `test_the_retry_queue_rebuilds_the_exchange_from_the_stored_question`

## Modification guidance

- Change clarification policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/clarification.py](../../../../../../src/learnloop/attempts/clarification.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
