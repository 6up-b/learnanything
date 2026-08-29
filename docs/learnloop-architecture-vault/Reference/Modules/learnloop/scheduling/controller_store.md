---
title: "learnloop.scheduling.controller_store"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/controller_store.py"
source_paths:
  - "src/learnloop/scheduling/controller_store.py"
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
  - "learnloop.scheduling.controller_store module"
  - "src/learnloop/scheduling/controller_store.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.controller_store`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.controller_store` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: P4 steps 1-2 -- persistence for the staged-controller substrate (spec §3.2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/controller_store.py](../../../../../../src/learnloop/scheduling/controller_store.py) |
| Source lines | 512 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `bulk_commitment_rows(repository: Repository) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/controller_store.py), line 27) — All commitment header rows in one read.
- `bulk_exposure_events(repository: Repository) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/controller_store.py), line 38) — The whole ``activity_exposure_events`` ledger in one read (the ONE ledger, §3.6).
- `upsert_snapshot(repository: Repository, *, snapshot_hash: str, session_id: str | None, body: Mapping[str, Any], param_manifest_hash: str | None, projection_versions: Mapping[str, Any], clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/scheduling/controller_store.py), line 57) — Persist a snapshot, deduped on its content hash.
- `snapshot_row(repository: Repository, snapshot_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/scheduling/controller_store.py), line 91)
- `upsert_constraint_manifest(repository: Repository, *, manifest_hash: str, definitions: Any, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/scheduling/controller_store.py), line 104)
- `create_attention_block(repository: Repository, *, session_id: str | None, commitment_id: str | None, action: str, subtype: str | None, budget_minutes: float, neighborhood: Mapping[str, Any], exit_rules: Any, short_circuit_reason: str | None, content_hash: str, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/scheduling/controller_store.py), line 133)
- `append_block_event(repository: Repository, *, block_id: str, kind: str, detail: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/scheduling/controller_store.py), line 163)
- `block_events(repository: Repository, block_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/controller_store.py), line 196)
- `decision_by_receipt_key(repository: Repository, receipt_key: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/scheduling/controller_store.py), line 211)
- `persist_decision(repository: Repository, *, receipt_key: str | None, snapshot_id: str, snapshot_hash: str, session_id: str | None, mode: str, commitment_id: str | None, staged_rule: str, action: str, subtype: str | None, attention_block_id: str | None, chosen_candidate_ref: str | None, stop_reason: str | None, constraint_manifest_hash: str | None, decision_params_hash: str | None, policy_version: str | None, comparator: Mapping[str, Any] | None, trace: Mapping[str, Any], candidates: list[Mapping[str, Any]], clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/controller_store.py), line 221) — Write the decision + all candidate rows in one transaction.
- `decision_row(repository: Repository, decision_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/scheduling/controller_store.py), line 303)
- `candidates_for_decision(repository: Repository, decision_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/controller_store.py), line 311)
- `persist_shadow_prediction(repository: Repository, *, decision_id: str | None, snapshot_hash: str, scorer_kind: str, model_version: str | None, prediction: Mapping[str, Any], usable: bool=True, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/scheduling/controller_store.py), line 328)
- `shadow_predictions_for_decision(repository: Repository, decision_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/controller_store.py), line 354)
- `persist_experiment_assignment(repository: Repository, *, experiment_id: str, decision_id: str | None, unit_kind: str, unit_id: str | None, variant: str, propensity: float, seed: str, draw: float | None, epsilon_margin: float | None, near_equivalent: bool, design: str, grade: str, candidate_refs: Any=None, detail: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/scheduling/controller_store.py), line 372) — Write one randomization assignment with its true propensity (§9.3).
- `assignment_row(repository: Repository, assignment_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/scheduling/controller_store.py), line 412)
- `assignments_for_experiment(repository: Repository, experiment_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/controller_store.py), line 420)
- `open_outcome_window(repository: Repository, *, decision_id: str | None, assignment_id: str | None, candidate_ref: str | None, commitment_id: str | None, card_ref: str | None, anchor_kind: str, anchor_ref: str | None, due_at: str | None, hypothesis_grade: bool, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/scheduling/controller_store.py), line 437)
- `resolve_outcome_window(repository: Repository, window_id: str, *, outcome: Mapping[str, Any], status: str='resolved', clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/scheduling/controller_store.py), line 469)
- `outcome_window_row(repository: Repository, window_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/scheduling/controller_store.py), line 486)
- `outcome_windows_for_decision(repository: Repository, decision_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/controller_store.py), line 494)
- `pending_outcome_windows(repository: Repository) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/controller_store.py), line 506)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/scheduling/controller_cutover|learnloop.scheduling.controller_cutover]] — imports `module`; statically calls `decision_row`
- [[Reference/Modules/learnloop/scheduling/controller_snapshot|learnloop.scheduling.controller_snapshot]] — imports `module`; statically calls `bulk_commitment_rows`, `bulk_exposure_events`, `upsert_snapshot`
- [[Reference/Modules/learnloop/scheduling/randomization_layer|learnloop.scheduling.randomization_layer]] — imports `module`; statically calls `open_outcome_window`, `persist_experiment_assignment`
- [[Reference/Modules/learnloop/scheduling/shadow_components|learnloop.scheduling.shadow_components]] — imports `module`; statically calls `persist_shadow_prediction`
- [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]] — imports `module`; statically calls `append_block_event`, `create_attention_block`, `decision_by_receipt_key`, `persist_decision`, `persist_shadow_prediction`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_json`; calls `canonical_json`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/scheduling/controller_cutover|learnloop.scheduling.controller_cutover]], [[Reference/Modules/learnloop/scheduling/controller_snapshot|learnloop.scheduling.controller_snapshot]], [[Reference/Modules/learnloop/scheduling/randomization_layer|learnloop.scheduling.randomization_layer]], [[Reference/Modules/learnloop/scheduling/shadow_components|learnloop.scheduling.shadow_components]], [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_controller_cutover.py](../../../../../../tests/test_controller_cutover.py) — direct import
  - `test_bridge_goes_live_and_is_decision_equivalent_when_owned`
- [tests/test_controller_snapshot.py](../../../../../../tests/test_controller_snapshot.py) — direct import
  - `test_snapshot_persists_deduped_on_content_hash`
- [tests/test_prequential.py](../../../../../../tests/test_prequential.py) — direct import
  - `test_composed_selector_report_is_secondary`
  - `test_report_ignores_unresolved_and_immediate_outcomes`
- [tests/test_randomization_layer.py](../../../../../../tests/test_randomization_layer.py) — direct import
  - `test_epsilon_tiebreak_is_inert_when_not_near_equivalent`
  - `test_epsilon_tiebreak_randomizes_near_equivalents_with_logged_propensity`
  - `test_micro_randomize_only_on_reversible`
  - `test_outcome_window_anchored_to_next_spaced_cold_review`
- [tests/test_shadow_components.py](../../../../../../tests/test_shadow_components.py) — direct import
- [tests/test_staged_policy.py](../../../../../../tests/test_staged_policy.py) — direct import
  - `test_decision_persists_snapshot_decision_candidates_and_block`
  - `test_legacy_comparator_is_logged_but_not_authority`
  - `test_shadow_scorer_has_zero_authority`
- [tests/test_staged_policy_evsi.py](../../../../../../tests/test_staged_policy_evsi.py) — direct import
  - `test_evsi_selector_ranks_only_within_feasible_set`

## Modification guidance

- Change controller store policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/controller_store.py](../../../../../../src/learnloop/scheduling/controller_store.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
