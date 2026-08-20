---
title: "learnloop.content.authoring.contract_commissioning"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/authoring/contract_commissioning.py"
source_paths:
  - "src/learnloop/content/authoring/contract_commissioning.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.authoring"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.authoring.contract_commissioning module"
  - "src/learnloop/content/authoring/contract_commissioning.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-authoring"
---

# `learnloop.content.authoring.contract_commissioning`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.authoring.contract_commissioning` exists within [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] to own the behavior summarized by its module contract: Rung-correct commissioning: author at the capability the contract names.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/authoring/contract_commissioning.py](../../../../../../../src/learnloop/content/authoring/contract_commissioning.py) |
| Source lines | 523 |
| Owning package | [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class CommissionDisposition(StrEnum)` ([source](../../../../../../../src/learnloop/content/authoring/contract_commissioning.py), line 77) — What generation may do about one unreachable contract cell.
  - `authorable(self) -> bool` (line 105; public)
- `class CommissionedCell` ([source](../../../../../../../src/learnloop/content/authoring/contract_commissioning.py), line 120) — One queue row plus the rung that authors AT its required capability.
  - `learning_object_id(self) -> str` (line 135; public)
  - `facet_id(self) -> str` (line 139; public)
  - `capability(self) -> str` (line 143; public) — The capability the CONTRACT names (never the learner's band).
  - `as_dict(self) -> dict[str, Any]` (line 148; public) — Payload handed to the authoring model — the cell, not the whole report.
- `class CommissionPlan` ([source](../../../../../../../src/learnloop/content/authoring/contract_commissioning.py), line 177) — The commissioning queue, resolved to rungs and grouped by learning object.
  - `commissioned(self) -> tuple[CommissionedCell, ...]` (line 193; public)
  - `deferred(self) -> tuple[CommissionedCell, ...]` (line 197; public)
  - `for_learning_object(self, learning_object_id: str) -> tuple[CommissionedCell, ...]` (line 200; public) — Commissionable cells for one LO, in queue order (best remedy first).
  - `deferred_for_learning_object(self, learning_object_id: str) -> tuple[CommissionedCell, ...]` (line 207; public)
  - `learning_object_rank(self) -> dict[str, int]` (line 214; public) — LO -> queue rank of its best commissionable cell.
  - `capabilities_for(self, learning_object_id: str) -> tuple[str, ...]` (line 227; public)
  - `summary(self) -> dict[str, Any]` (line 230; public)
  - `as_dict(self) -> dict[str, Any]` (line 243; public)
- `commission_plan(vault: LoadedVault, repository: Repository, *, report: ContractReachabilityReport | None=None, learning_object_ids: Iterable[str] | None=None) -> CommissionPlan` ([source](../../../../../../../src/learnloop/content/authoring/contract_commissioning.py), line 283) — Resolve 3.1's commissioning queue into rung-correct authoring targets.
- `item_observed_cells(vault: LoadedVault, item: PracticeItem) -> frozenset[tuple[str, str]] | None` ([source](../../../../../../../src/learnloop/content/authoring/contract_commissioning.py), line 342) — ``(canonical facet, capability)`` cells ``item`` can put evidence into.
- `class ContractHitRate` ([source](../../../../../../../src/learnloop/content/authoring/contract_commissioning.py), line 377) — Step 0's "28%" as a recomputable metric (plan item 5.1's hypothesis).
  - `cell_hit_rate(self) -> float | None` (line 403; public) — ``None`` with nothing scored — never a fake 1.0 (3.1's discipline).
  - `facet_hit_rate(self) -> float | None` (line 411; public)
  - `rung_loss_share(self) -> float | None` (line 417; public) — Share discarded by the capability axis alone.
  - `as_dict(self) -> dict[str, Any]` (line 424; public)
- `contract_cell_hit_rate(vault: LoadedVault, repository: Repository, *, since: str | None=None, report: ContractReachabilityReport | None=None) -> ContractHitRate` ([source](../../../../../../../src/learnloop/content/authoring/contract_commissioning.py), line 445) — Share of attempts that landed in a cell their own LO's contract requires.

### Module constants

- `DEFERRAL_REASON` ([src/learnloop/content/authoring/contract_commissioning.py](../../../../../../../src/learnloop/content/authoring/contract_commissioning.py), line 112)

## Internal implementation anchors

- `_disposition_for(repository: Repository, row: CellReachability, rung_cache: dict[str, RungTarget | None]) -> tuple[CommissionDisposition, RungTarget | None]` ([source](../../../../../../../src/learnloop/content/authoring/contract_commissioning.py), line 254) — Disposition + rung for one queue row.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `contract_cell_hit_rate`; statically calls `contract_cell_hit_rate`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `commission_plan`; statically calls `commission_plan`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `commission_plan`; statically calls `commission_plan`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/curriculum/depth_rungs|learnloop.curriculum.depth_rungs]] — imports `RungTarget`, `capability_rung`; calls `capability_rung`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `compile_criterion_targets`, `default_capability_for`, `is_valid_capability`; calls `compile_criterion_targets`, `default_capability_for`, `is_valid_capability`
- [[Reference/Modules/learnloop/learner/contract_reachability|learnloop.learner.contract_reachability]] — imports `CAPABILITY_RANK`, `CellReachability`, `ContractReachabilityReport`, `OBSERVING_ROLES`, `ReachabilityVerdict`, `analyze_contract_reachability`; calls `analyze_contract_reachability`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `enum`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]], [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_contract_commissioning.py](../../../../../../../tests/test_contract_commissioning.py) — direct import
  - `test_authoring_at_the_contract_capability_makes_the_cell_reachable`
  - `test_contract_capabilities_include_reachable_cells`
  - `test_coordination_cell_is_deferred_with_a_typed_reason`
  - `test_hit_rate_excludes_attempts_with_no_contract_to_hit`
  - `test_hit_rate_partitions_attempts_into_cell_rung_and_off_contract`
  - `test_hit_rate_since_window_scopes_to_new_attempts`
  - `test_integration_cell_at_an_authorable_rung_is_commissioned_normally`
  - `test_mismatch_above_and_indeterminate_are_deferred_not_authored`
  - `test_queue_order_is_3_1s_order_not_a_second_priority`
  - `test_unrubricked_item_is_not_scored_as_a_miss`

## Modification guidance

- Change contract commissioning policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/authoring/contract_commissioning.py](../../../../../../../src/learnloop/content/authoring/contract_commissioning.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
