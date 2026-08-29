---
title: "learnloop.substrate.card_lineage"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/card_lineage.py"
source_paths:
  - "src/learnloop/substrate/card_lineage.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.substrate"
layer: "domain"
concepts:
  - "Learning System"
  - "State and Persistence"
workflows:
  - "Inspect Persistent State"
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.substrate.card_lineage module"
  - "src/learnloop/substrate/card_lineage.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.card_lineage`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.card_lineage` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: P1 step 4 -- edit classification, durable card-lineage state, and the authoritative card-level scheduling projection (spec_p1_shared_substrate §3.7, §3.8).

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/card_lineage.py](../../../../../../src/learnloop/substrate/card_lineage.py) |
| Source lines | 375 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class EditClassification` ([source](../../../../../../src/learnloop/substrate/card_lineage.py), line 88)
  - `as_dict(self) -> dict[str, Any]` (line 94; public)
- `classify_edit(prev_contract: Mapping[str, Any], new_contract: Mapping[str, Any]) -> EditClassification` ([source](../../../../../../src/learnloop/substrate/card_lineage.py), line 110) — Classify a proposed card edit (§3.7).
- `start_lineage(repository: Repository, *, genesis_card_version_id: str, family_id: str | None=None, card_id: str | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/substrate/card_lineage.py), line 156) — Create a durable lineage and record its genesis edge (from_ = NULL).
- `append_minor_successor(repository: Repository, *, lineage_id: str, from_card_version_id: str, to_card_version_id: str, rationale: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/substrate/card_lineage.py), line 179) — Append a surface-preserving successor version INSIDE the lineage; scheduling state is retained on the same lineage (§3.7).
- `fork_card(repository: Repository, *, predecessor_card_version_id: str, forked_card_version_id: str, scheduler_algorithm_version: str, family_id: str | None=None, card_id: str | None=None, model_label: str='fsrs', learner_id: str='local', informed_difficulty_prior: float | None=None, predecessor_lineage_id: str | None=None, rationale: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/card_lineage.py), line 202) — Fork: a NEW lineage + a NEW ``activity_card_state`` row that inherits an evidence-informed *difficulty* prior at most, and NEVER inherits stability or certification (§3.7).
- `split_lineage(repository: Repository, *, from_card_version_id: str, split_card_version_id: str, family_id: str | None=None, card_id: str | None=None, rationale: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/substrate/card_lineage.py), line 251) — Split a new lineage off an existing version (append-only ``split_from`` edge).
- `merge_lineage(repository: Repository, *, into_lineage_id: str, from_card_version_id: str, merged_card_version_id: str, rationale: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/substrate/card_lineage.py), line 276) — Record a ``merged_from`` edge folding another lineage's version in.
- `replay_review_events(review_events: Sequence[Mapping[str, Any]], *, weights: tuple[float, ...]=FSRS6_DEFAULT_WEIGHTS) -> MemoryState | None` ([source](../../../../../../src/learnloop/substrate/card_lineage.py), line 306) — Deterministically replay an ordered stream of eligible review events into an FSRS memory state.
- `rebuild_card_state(repository: Repository, *, card_lineage_id: str, scheduler_algorithm_version: str, review_events: Sequence[Mapping[str, Any]] | None=None, model_label: str='fsrs', learner_id: str='local', due_at: str | None=None, weights: tuple[float, ...]=FSRS6_DEFAULT_WEIGHTS, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/substrate/card_lineage.py), line 322) — Rebuild ``activity_card_state`` from its authoritative review-event stream.

### Module constants

- `LINEAGE_CLASSIFIER_VERSION` ([src/learnloop/substrate/card_lineage.py](../../../../../../src/learnloop/substrate/card_lineage.py), line 50)
- `SEMANTIC_COMPONENTS` ([src/learnloop/substrate/card_lineage.py](../../../../../../src/learnloop/substrate/card_lineage.py), line 54)
- `COSMETIC_COMPONENTS` ([src/learnloop/substrate/card_lineage.py](../../../../../../src/learnloop/substrate/card_lineage.py), line 74)

## Internal implementation anchors

- `_normalized_components(contract: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/card_lineage.py), line 103) — Extract the comparable contract components.
- `_rating(value: Any) -> Rating` ([source](../../../../../../src/learnloop/substrate/card_lineage.py), line 302)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/curriculum/depth_transition|learnloop.curriculum.depth_transition]] — imports `module`; statically calls `classify_edit`
- [[Reference/Modules/learnloop/reader/reader_authoring|learnloop.reader.reader_authoring]] — imports `module`; statically calls `append_minor_successor`, `classify_edit`, `fork_card`, `merge_lineage`, `split_lineage`, `start_lineage`
- [[Reference/Modules/learnloop/substrate/administration_adapters|learnloop.substrate.administration_adapters]] — imports `module`; statically calls `rebuild_card_state`
- [[Reference/Modules/learnloop/substrate/compat/substrate_cutover|learnloop.substrate.compat.substrate_cutover]] — imports `module`; statically calls `start_lineage`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `FSRS6_DEFAULT_WEIGHTS`, `MemoryState`, `Rating`, `apply_review`; calls `Rating`, `apply_review`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/curriculum/depth_transition|learnloop.curriculum.depth_transition]], [[Reference/Modules/learnloop/reader/reader_authoring|learnloop.reader.reader_authoring]], [[Reference/Modules/learnloop/substrate/administration_adapters|learnloop.substrate.administration_adapters]], [[Reference/Modules/learnloop/substrate/compat/substrate_cutover|learnloop.substrate.compat.substrate_cutover]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_administration_adapters.py](../../../../../../tests/test_administration_adapters.py) — direct import
  - `test_ineligible_practice_observation_leaves_card_state_untouched`
  - `test_only_practice_eligible_updates_card_state`
- [tests/test_card_lineage.py](../../../../../../tests/test_card_lineage.py) — direct import
  - `test_answer_key_or_solution_change_forks`
  - `test_fork_starts_new_lineage_and_state_without_inherited_stability`
  - `test_minor_successor_retains_lineage_and_state`
  - `test_no_change_is_surface_preserving`
  - `test_rebuild_is_deterministic_and_independent_of_practice_item_cache`
  - `test_rubric_clarification_alone_is_surface_preserving`
  - `test_rubric_clarification_with_semantics_delta_is_parked`
  - `test_semantic_change_forks`
  - `test_unknown_changed_component_is_parked_for_review`
  - `test_wording_only_edit_is_surface_preserving`
- [tests/test_event_sufficiency.py](../../../../../../tests/test_event_sufficiency.py) — direct import
  - `test_every_admin_obs_pair_carries_card_version_outcome_and_context`
  - `test_replay_prefers_active_interpretation_head`
  - `test_replay_reads_ledger_events_only_no_live_tables`
  - `test_u014_resume_shape_emits_card_level_counts`
- [tests/test_journey6.py](../../../../../../tests/test_journey6.py) — direct import
  - `test_journey6_end_to_end_on_fresh_mvp08_vault`
- [tests/test_reader_authoring.py](../../../../../../tests/test_reader_authoring.py) — direct import
  - `test_cosmetic_edit_retains_state_only_through_classifier`
  - `test_split_merge_spawn_create_lineage`
- [tests/test_substrate_cutover.py](../../../../../../tests/test_substrate_cutover.py) — direct import

## Modification guidance

- Change card lineage policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/card_lineage.py](../../../../../../src/learnloop/substrate/card_lineage.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
