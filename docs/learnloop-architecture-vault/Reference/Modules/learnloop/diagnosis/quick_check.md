---
title: "learnloop.diagnosis.quick_check"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/quick_check.py"
source_paths:
  - "src/learnloop/diagnosis/quick_check.py"
source_commit: "efc53a86c469ed562dc4cc1d950629151b840423"
source_commit_timestamp: "2026-10-17T02:09:17-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.diagnosis.quick_check module"
  - "src/learnloop/diagnosis/quick_check.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.quick_check`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.quick_check` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: The optional quick check, "Check what I already know" (learner field §5.2, D4).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/quick_check.py](../../../../../../src/learnloop/diagnosis/quick_check.py) |
| Source lines | 436 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `efc53a86c469ed562dc4cc1d950629151b840423` |
| Commit timestamp | `2026-10-17T02:09:17-04:00` |

## Public API

- `class QuickCheckError(ValueError)` ([source](../../../../../../src/learnloop/diagnosis/quick_check.py), line 84)
- `start_quick_check(vault: LoadedVault, repository: Repository, *, session_id: str, learning_object_ids: list[str], request_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/quick_check.py), line 117)
- `is_quick_check(repository: Repository, calibration_session_id: str) -> bool` ([source](../../../../../../src/learnloop/diagnosis/quick_check.py), line 175)
- `next_quick_check_item(vault: LoadedVault, repository: Repository, predictor: Any, *, undecided: set[str], excluded: frozenset[str]=frozenset(), clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/quick_check.py), line 247) — The never-seen item with the largest conditional gain; ties by id (G8).
- `quick_check_progress(vault: LoadedVault, repository: Repository, calibration_session_id: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/quick_check.py), line 334) — Calibration progress with the quick check's own target and results.

### Module constants

- `QUICK_CHECK_SELECTION` ([src/learnloop/diagnosis/quick_check.py](../../../../../../src/learnloop/diagnosis/quick_check.py), line 77)
- `_EXCLUDED_MODES` ([src/learnloop/diagnosis/quick_check.py](../../../../../../src/learnloop/diagnosis/quick_check.py), line 80)
- `_DECIDED` ([src/learnloop/diagnosis/quick_check.py](../../../../../../src/learnloop/diagnosis/quick_check.py), line 81)

## Internal implementation anchors

- `_existing_quick_check(repository: Repository, *, session_id: str, scope: list[str], request_id: str | None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/quick_check.py), line 88) — The check a retried start should recover, if any.
- `_candidate_items(vault: LoadedVault, repository: Repository, undecided: set[str], attempted: set[str], excluded: frozenset[str]=frozenset(), *, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/quick_check.py), line 179) — Never-seen ordinary items on undecided LOs that routine serving could offer (the shared exclusions apply, with the out-of-timing ones), minus ``excluded``.
- `_attempted_item_ids(repository: Repository) -> set[str]` ([source](../../../../../../src/learnloop/diagnosis/quick_check.py), line 240)
- `_present_next(vault: LoadedVault, repository: Repository, predictor: Any, record: dict[str, Any], presentations: list[dict[str, Any]], *, undecided: set[str], clock: Clock | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/quick_check.py), line 278) — The check's current presentation, or a new one while fewer than k exist.
- `_results(vault: LoadedVault, repository: Repository, outcome: dict[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/quick_check.py), line 409)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/calibration|learnloop_sidecar.handlers.calibration]] — imports `quick_check_progress`; statically calls `quick_check_progress`
- [[Reference/Modules/learnloop_sidecar/handlers/placement|learnloop_sidecar.handlers.placement]] — imports `QuickCheckError`, `start_quick_check`; statically calls `start_quick_check`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `COLD_FOLLOWUP_TASK_KINDS`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/placement|learnloop.db.stores.placement]] — imports `insert_quick_check`, `insert_quick_check_item`; calls `insert_quick_check`, `insert_quick_check_item`
- [[Reference/Modules/learnloop/diagnosis/calibration_sessions|learnloop.diagnosis.calibration_sessions]] — imports `CalibrationSessionError`, `calibration_session_progress`, `start_calibration_session`; calls `calibration_session_progress`, `start_calibration_session`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `COLD_RETRIEVAL_DELAY`
- [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]] — imports `bind_quick_check_answers`, `finish_quick_check_split`, `quick_check_answers`, `quick_check_presentations`, `quick_check_record`, `quick_check_split`, `quick_check_window_end`; calls `bind_quick_check_answers`, `finish_quick_check_split`, `quick_check_answers`, `quick_check_presentations`, `quick_check_record`, `quick_check_split`, `quick_check_window_end`
- [[Reference/Modules/learnloop/placement/predictor|learnloop.placement.predictor]] — imports `active_predictor`; calls `active_predictor`
- [[Reference/Modules/learnloop/placement/signals|learnloop.placement.signals]] — imports `blocking_signals_by_lo`; calls `blocking_signals_by_lo`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `diagnosis_can_arrive`, `load_answers`, `load_placement_state_from_connection`, `placement_active`; calls `diagnosis_can_arrive`, `load_answers`, `load_placement_state_from_connection`, `placement_active`
- [[Reference/Modules/learnloop/scheduling/serving_exclusions|learnloop.scheduling.serving_exclusions]] — imports `out_of_timing_serving_exclusions`; calls `out_of_timing_serving_exclusions`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `module`; calls `decide`, `decision_active`, `gather`, `log_decision`
- [[Reference/Modules/learnloop/substrate/instrument_serving|learnloop.substrate.instrument_serving]] — imports `unservable_reason`; calls `unservable_reason`
- [[Reference/Modules/learnloop/vault/lifecycle|learnloop.vault.lifecycle]] — imports `practice_item_servable`; calls `practice_item_servable`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/calibration|learnloop_sidecar.handlers.calibration]], [[Reference/Modules/learnloop_sidecar/handlers/placement|learnloop_sidecar.handlers.placement]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_assumed_known.py](../../../../../../tests/test_assumed_known.py) — direct import
  - `test_placement_receipts_survive_rebuild_with_zero_model_calls`
- [tests/test_quick_check.py](../../../../../../tests/test_quick_check.py) — direct import
  - `test_interrupted_creation_leaves_no_orphan_and_a_retry_recovers_the_check`
  - `test_quick_check_needs_placement`

## Modification guidance

- Change quick check policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/quick_check.py](../../../../../../src/learnloop/diagnosis/quick_check.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
