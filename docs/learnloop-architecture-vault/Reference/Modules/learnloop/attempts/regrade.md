---
title: "learnloop.attempts.regrade"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/regrade.py"
source_paths:
  - "src/learnloop/attempts/regrade.py"
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
  - "learnloop.attempts.regrade module"
  - "src/learnloop/attempts/regrade.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.regrade`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps regrade behavior inside its owning package, [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]]. Its public surface centers on `DeferredRegradeResult`, `run_deferred_regrades`, `run_deferred_ai_regrades`, `regrade_attempt`.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/regrade.py](../../../../../../src/learnloop/attempts/regrade.py) |
| Source lines | 401 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class DeferredRegradeResult` ([source](../../../../../../src/learnloop/attempts/regrade.py), line 41)
  - `as_dict(self) -> dict[str, int | str | None]` (line 47; public)
- `run_deferred_regrades(vault: LoadedVault, repository: Repository, *, runtime: CodexRuntimeReport, codex_client: AIProviderClient | None, limit: int | None=None, clock: Clock | None=None) -> DeferredRegradeResult` ([source](../../../../../../src/learnloop/attempts/regrade.py), line 56)
- `run_deferred_ai_regrades(vault: LoadedVault, repository: Repository, *, runtime: AIRuntimeReport, ai_client: AIProviderClient | None, limit: int | None=None, clock: Clock | None=None) -> DeferredRegradeResult` ([source](../../../../../../src/learnloop/attempts/regrade.py), line 77)
- `regrade_attempt(vault: LoadedVault, repository: Repository, attempt: dict, *, runtime, client: AIProviderClient, grading_source: str, clock: Clock | None, clarification_exchange: dict[str, str] | None=None, purpose: str='grading_regrade') -> 'ValidatedCodexGrade'` ([source](../../../../../../src/learnloop/attempts/regrade.py), line 136) — Re-grade one attempt, superseding its evidence and replaying the LO.

### Module constants

- `LOGGER` ([src/learnloop/attempts/regrade.py](../../../../../../src/learnloop/attempts/regrade.py), line 37)

## Internal implementation anchors

- `_run_deferred_agent_regrades(vault: LoadedVault, repository: Repository, *, runtime, client: AIProviderClient | None, missing_client_reason: str, grading_source: str, limit: int | None, clock: Clock | None) -> DeferredRegradeResult` ([source](../../../../../../src/learnloop/attempts/regrade.py), line 98)
- `_agent_run_provider_fields(client: AIProviderClient, runtime) -> dict[str, str | None]` ([source](../../../../../../src/learnloop/attempts/regrade.py), line 374)
- `_manual_review_reason(existing: str | None, attempt: dict) -> str | None` ([source](../../../../../../src/learnloop/attempts/regrade.py), line 390)
- `_disagreement_summary(old_evidence, new_evidence_rows, old_score: int, new_score: int) -> str` ([source](../../../../../../src/learnloop/attempts/regrade.py), line 398)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/clarification|learnloop.attempts.clarification]] — imports `regrade_attempt`; statically calls `regrade_attempt`
- [[Reference/Modules/learnloop/ops/startup|learnloop.ops.startup]] — imports `DeferredRegradeResult`, `run_deferred_ai_regrades`, `run_deferred_regrades`; statically calls `run_deferred_ai_regrades`, `run_deferred_regrades`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `regrade_attempt`; statically calls `regrade_attempt`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `AIProviderClient`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]] — imports `CodexRuntimeReport`
- [[Reference/Modules/learnloop/ai/runs|learnloop.ai.runs]] — imports `finish_agent_run`; calls `finish_agent_run`
- [[Reference/Modules/learnloop/ai/runtime|learnloop.ai.runtime]] — imports `AIRuntimeReport`
- [[Reference/Modules/learnloop/attempts/ai_contracts|learnloop.attempts.ai_contracts]] — imports `GRADING_PROMPT_VERSION`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `GradeAttribution`; calls `GradeAttribution`
- [[Reference/Modules/learnloop/attempts/clarification|learnloop.attempts.clarification]] — imports `record_clarification`; calls `record_clarification`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `GradingValidationError`, `ValidatedCodexGrade`, `build_grading_context`, `grading_context_hash`, `request_grading_proposal`, `resolved_rubric`, `validate_codex_grading_proposal`; calls `build_grading_context`, `grading_context_hash`, `request_grading_proposal`, `resolved_rubric`, `validate_codex_grading_proposal`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/error_taxonomy|learnloop.diagnosis.error_taxonomy]] — imports `persist_unknown_error_type_proposals`; calls `persist_unknown_error_type_proposals`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `replay_learning_object`; calls `replay_learning_object`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `TEACH_BACK_ATTEMPT_TYPE`, `asked_rubric_score`, `core_criteria`, `restrict_grading_context_to_criteria`; calls `asked_rubric_score`, `core_criteria`, `restrict_grading_context_to_criteria`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `logging`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/clarification|learnloop.attempts.clarification]], [[Reference/Modules/learnloop/ops/startup|learnloop.ops.startup]], [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_deferred_regrade.py](../../../../../../tests/test_deferred_regrade.py) — direct import
  - `test_deferred_ai_regrade_records_provider_and_ai_origin`
  - `test_deferred_regrade_failure_leaves_self_grade_current_and_agent_failed`
  - `test_deferred_regrade_preserves_blank_answer_manual_review`
  - `test_deferred_regrade_recomputes_downstream_attempts_for_learning_object`
  - `test_deferred_regrade_records_disagreement_event`
  - `test_deferred_regrade_replays_attempt_derived_state`
  - `test_deferred_regrade_replays_targeted_error_attribution_facets`
  - `test_deferred_regrade_skips_when_runtime_not_ready`
  - `test_deferred_regrade_supersedes_self_grade_and_updates_mastery`
  - `test_deferred_regrade_validates_repaired_trace_against_learner_answer`
- [tests/test_learner_review_system_entries.py](../../../../../../tests/test_learner_review_system_entries.py) — direct import
- [tests/test_provider_resolution_parity.py](../../../../../../tests/test_provider_resolution_parity.py) — direct import
  - `test_config_matrix_executes_all_six_production_resolution_paths`
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
  - `test_regrade_teach_back_attempt_restricts_to_graded_criteria`
  - `test_regrade_teach_back_attempt_without_evidence_falls_back_to_core`

## Modification guidance

- Change regrade policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/regrade.py](../../../../../../src/learnloop/attempts/regrade.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
