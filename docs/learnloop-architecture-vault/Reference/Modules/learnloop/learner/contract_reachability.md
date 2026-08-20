---
title: "learnloop.learner.contract_reachability"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/contract_reachability.py"
source_paths:
  - "src/learnloop/learner/contract_reachability.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.learner"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Inspect Persistent State"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.learner.contract_reachability module"
  - "src/learnloop/learner/contract_reachability.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.contract_reachability`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.contract_reachability` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: Contract-cell reachability: can *any* authored item observe this cell?

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/contract_reachability.py](../../../../../../src/learnloop/learner/contract_reachability.py) |
| Source lines | 722 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ReachabilityVerdict(StrEnum)` ([source](../../../../../../src/learnloop/learner/contract_reachability.py), line 106) — §5.8.2's four verdicts, plus one abstention arm.
  - `reachable(self) -> bool` (line 140; public)
- `class ContractCell` ([source](../../../../../../src/learnloop/learner/contract_reachability.py), line 166) — One ``(LO, facet, required capability)`` obligation of a blueprint (§7.2).
  - `integration(self) -> bool` (line 183; public) — True when some recipe names this cell as its integration component.
  - `key(self) -> tuple[str, str, str]` (line 193; public)
  - `as_dict(self) -> dict[str, Any]` (line 196; public)
- `class CellReachability` ([source](../../../../../../src/learnloop/learner/contract_reachability.py), line 209) — A contract cell plus its verdict and the instrument evidence behind it.
  - `remedy(self) -> str` (line 231; public)
  - `as_dict(self) -> dict[str, Any]` (line 234; public)
- `class ContractReachabilityReport` ([source](../../../../../../src/learnloop/learner/contract_reachability.py), line 252) — Per-cell verdicts plus §5.8's aggregate proportions.
  - `counts(self) -> dict[str, int]` (line 286; public) — Cell count per verdict, every arm present (zeros included).
  - `integration_counts(self) -> dict[str, int]` (line 295; public)
  - `cell_count(self) -> int` (line 303; public)
  - `integration_cell_count(self) -> int` (line 307; public)
  - `reachable_count(self) -> int` (line 311; public)
  - `unreachable_count(self) -> int` (line 315; public)
  - `reachable_share(self) -> float | None` (line 319; public) — Reachable / total, or ``None`` when there are no contract cells.
  - `integration_reachable_share(self) -> float | None` (line 332; public)
  - `commissioning_queue(self) -> tuple[CellReachability, ...]` (line 338; public) — Non-reachable cells, cheapest remedy first (Stage 5.1's input).
  - `by_verdict(self, verdict: ReachabilityVerdict) -> tuple[CellReachability, ...]` (line 348; public)
  - `summary(self) -> dict[str, Any]` (line 351; public) — Aggregate-only payload (bounded size; safe to embed in doctor JSON).
  - `as_dict(self) -> dict[str, Any]` (line 373; public)
- `class InstrumentPool` ([source](../../../../../../src/learnloop/learner/contract_reachability.py), line 464) — facet -> capability -> instrument ids, plus the roles seen per facet.
  - `capabilities(self, facet_id: str) -> tuple[str, ...]` (line 476; public) — Observed capabilities for ``facet_id``, in ladder order.
  - `item_ids(self, facet_id: str, capability: str | None=None) -> tuple[str, ...]` (line 489; public)
- `build_instrument_pool(vault: LoadedVault, *, statuses: Iterable[str]=INSTRUMENT_STATUSES) -> InstrumentPool` ([source](../../../../../../src/learnloop/learner/contract_reachability.py), line 499) — Index every active practice item by the cells it can observe.
- `contract_cells(vault: LoadedVault) -> tuple[tuple[ContractCell, ...], int]` ([source](../../../../../../src/learnloop/learner/contract_reachability.py), line 561) — Every deduped contract cell in the vault, plus the advisory-component count.
- `classify_cell(required_capability: str, observed_capabilities: Iterable[str]) -> ReachabilityVerdict` ([source](../../../../../../src/learnloop/learner/contract_reachability.py), line 625) — The §5.8.2 verdict for one cell, given the capabilities its facet is observed at.
- `analyze_contract_reachability(vault: LoadedVault, *, statuses: Iterable[str]=INSTRUMENT_STATUSES) -> ContractReachabilityReport` ([source](../../../../../../src/learnloop/learner/contract_reachability.py), line 665) — Static reachability report over a whole vault (§5.8.2).

### Module constants

- `CAPABILITY_RANK` ([src/learnloop/learner/contract_reachability.py](../../../../../../src/learnloop/learner/contract_reachability.py), line 81)
- `CONTRACT_MODALITIES` ([src/learnloop/learner/contract_reachability.py](../../../../../../src/learnloop/learner/contract_reachability.py), line 91)
- `INSTRUMENT_STATUSES` ([src/learnloop/learner/contract_reachability.py](../../../../../../src/learnloop/learner/contract_reachability.py), line 97)
- `OBSERVING_ROLES` ([src/learnloop/learner/contract_reachability.py](../../../../../../src/learnloop/learner/contract_reachability.py), line 103)
- `_QUEUE_PRIORITY` ([src/learnloop/learner/contract_reachability.py](../../../../../../src/learnloop/learner/contract_reachability.py), line 147)
- `_REMEDY` ([src/learnloop/learner/contract_reachability.py](../../../../../../src/learnloop/learner/contract_reachability.py), line 156)

## Internal implementation anchors

- `_queue_sort_key(row: CellReachability) -> tuple[Any, ...]` ([source](../../../../../../src/learnloop/learner/contract_reachability.py), line 381)
- `_item_observed_capability(item: PracticeItem, tier: str) -> str` ([source](../../../../../../src/learnloop/learner/contract_reachability.py), line 394) — Capability a criterion of ``tier`` observes on ``item``.
- `class _Observation` ([source](../../../../../../src/learnloop/learner/contract_reachability.py), line 413)
- `_item_observations(vault: LoadedVault, item: PracticeItem) -> list[_Observation] | None` ([source](../../../../../../src/learnloop/learner/contract_reachability.py), line 419) — Cells ``item`` can put evidence into, or ``None`` when it cannot be graded.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `ReachabilityVerdict`, `analyze_contract_reachability`; statically calls `analyze_contract_reachability`
- [[Reference/Modules/learnloop/content/authoring/contract_commissioning|learnloop.content.authoring.contract_commissioning]] — imports `CAPABILITY_RANK`, `CellReachability`, `ContractReachabilityReport`, `OBSERVING_ROLES`, `ReachabilityVerdict`, `analyze_contract_reachability`; statically calls `analyze_contract_reachability`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `analyze_contract_reachability`; statically calls `analyze_contract_reachability`
- [[Reference/Modules/learnloop/curriculum/integration_backfill|learnloop.curriculum.integration_backfill]] — imports `CAPABILITY_RANK`, `CONTRACT_MODALITIES`, `build_instrument_pool`; statically calls `build_instrument_pool`
- [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] — imports `contract_cells`; statically calls `contract_cells`
- [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]] — imports `CONTRACT_MODALITIES`, `build_instrument_pool`; statically calls `build_instrument_pool`
- [[Reference/Modules/learnloop/goals/goal_certification|learnloop.goals.goal_certification]] — imports `CONTRACT_MODALITIES`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `ReachabilityVerdict`, `analyze_contract_reachability`; statically calls `analyze_contract_reachability`
- [[Reference/Modules/learnloop/learner/inference_precheck|learnloop.learner.inference_precheck]] — imports `CAPABILITY_RANK`, `CONTRACT_MODALITIES`, `CellReachability`, `ContractCell`, `ContractReachabilityReport`, `ReachabilityVerdict`, `analyze_contract_reachability`, `build_instrument_pool`; statically calls `analyze_contract_reachability`, `build_instrument_pool`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `analyze_contract_reachability`; statically calls `analyze_contract_reachability`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `analyze_contract_reachability`; statically calls `analyze_contract_reachability`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `compile_criterion_targets`, `default_capability_for`, `is_valid_capability`; calls `compile_criterion_targets`, `default_capability_for`, `is_valid_capability`
- [[Reference/Modules/learnloop/substrate/instrument_serving|learnloop.substrate.instrument_serving]] — imports `unservable_reason`; calls `unservable_reason`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `CAPABILITY_VOCABULARY`, `LoadedVault`, `PracticeItem`, `recipe_components`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `enum`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/authoring/contract_commissioning|learnloop.content.authoring.contract_commissioning]], [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]], [[Reference/Modules/learnloop/curriculum/integration_backfill|learnloop.curriculum.integration_backfill]], [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] and 6 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_contract_commissioning.py](../../../../../../tests/test_contract_commissioning.py) — direct import
  - `test_authoring_at_the_contract_capability_makes_the_cell_reachable`
- [tests/test_contract_reachability.py](../../../../../../tests/test_contract_reachability.py) — direct import
  - `test_advisory_modality_is_not_a_contract_cell`
  - `test_aggregate_counts_and_shares`
  - `test_classify_cell_ladder_direction_and_abstention`
  - `test_commissioning_queue_excludes_reachable_and_orders_cheapest_first`
  - `test_four_verdicts_on_purpose_built_vault`
  - `test_indeterminate_capability_is_counted_but_never_reachable`
  - `test_integration_cell_is_tracked_separately`
  - `test_legacy_vault_without_contracts_reports_empty_not_perfect`
  - `test_mismatch_above_wins_when_observed_both_sides`
  - `test_recipe_duplicate_cells_collapse_to_one_obligation`
  - `test_report_is_deterministic`
  - `test_retired_items_are_not_instruments`
  - `test_unrubricked_items_are_counted_not_silently_dropped`
- [tests/test_integration_backfill.py](../../../../../../tests/test_integration_backfill.py) — direct import
  - `test_apply_lowers_the_capability_in_place`
  - `test_drop_removes_the_cell_without_moving_the_reachable_count`
- [tests/test_scoreboard.py](../../../../../../tests/test_scoreboard.py) — direct import
  - `test_cells_cleared_per_question_divides_by_questions_served`

## Modification guidance

- Change contract reachability policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/contract_reachability.py](../../../../../../src/learnloop/learner/contract_reachability.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
