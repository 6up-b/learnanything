---
title: "learnloop.scheduling.predictive_targets"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/predictive_targets.py"
source_paths:
  - "src/learnloop/scheduling/predictive_targets.py"
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
  - "learnloop.scheduling.predictive_targets module"
  - "src/learnloop/scheduling/predictive_targets.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.predictive_targets`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.predictive_targets` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: P4 step 3b -- goal-conditioned predictive targets (spec §6.6, design §B step 3b).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/predictive_targets.py](../../../../../../src/learnloop/scheduling/predictive_targets.py) |
| Source lines | 165 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class TargetExemplar` ([source](../../../../../../src/learnloop/scheduling/predictive_targets.py), line 31)
  - `key(self) -> tuple[str, str]` (line 36; public)
  - `as_dict(self) -> dict[str, Any]` (line 39; public)
- `class TargetSet` ([source](../../../../../../src/learnloop/scheduling/predictive_targets.py), line 44) — A frozen goal-conditioned predictive target set (§6.6).
  - `weight_of(self, exemplar_id: str) -> float` (line 57; public)
  - `as_dict(self) -> dict[str, Any]` (line 63; public)
- `build_target_set(contract_body: Mapping[str, Any], *, contract_version_id: str | None=None, support_hash: str | None=None, candidate_id: str | None=None, available_capabilities: Sequence[str] | None=None) -> TargetSet` ([source](../../../../../../src/learnloop/scheduling/predictive_targets.py), line 84) — Build the frozen predictive target set from a pinned contract body (§6.6).
- `build_from_contract_version(contract_version: Any, *, candidate_id: str | None=None, available_capabilities: Sequence[str] | None=None) -> TargetSet` ([source](../../../../../../src/learnloop/scheduling/predictive_targets.py), line 150) — Convenience over a ``goal_contracts.ContractVersion`` (pins version id + support hash automatically).

### Module constants

- `TARGET_SET_SCHEMA_VERSION` ([src/learnloop/scheduling/predictive_targets.py](../../../../../../src/learnloop/scheduling/predictive_targets.py), line 27)

## Internal implementation anchors

- `_matches_candidate(ex: TargetExemplar, candidate_id: str | None) -> bool` ([source](../../../../../../src/learnloop/scheduling/predictive_targets.py), line 78)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/scheduling/reentry_adapter|learnloop.scheduling.reentry_adapter]] — imports `module`; statically calls `build_from_contract_version`, `build_target_set`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_hash`; calls `canonical_hash`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/scheduling/reentry_adapter|learnloop.scheduling.reentry_adapter]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_predictive_targets.py](../../../../../../tests/test_predictive_targets.py) — direct import
  - `test_candidate_is_excluded_from_its_own_target_set`
  - `test_construction_is_invariant_to_insertion_order`
  - `test_coverage_gaps_reported_against_available_capabilities`
  - `test_excluding_the_candidate_changes_the_hash`
  - `test_hash_tracks_the_pinned_support_not_candidate_order`
  - `test_held_out_flag_and_weights_are_preserved`

## Modification guidance

- Change predictive targets policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/predictive_targets.py](../../../../../../src/learnloop/scheduling/predictive_targets.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
