---
title: "learnloop.substrate.recurrence_groups"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/recurrence_groups.py"
source_paths:
  - "src/learnloop/substrate/recurrence_groups.py"
source_commit: "877ad6d3f8d16d64b59c5d21a4b93a44cd291a06"
source_commit_timestamp: "2026-10-13T16:45:11-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.substrate"
layer: "domain"
concepts:
  - "Learning System"
  - "State and Persistence"
workflows:
  - "Inspect Persistent State"
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.substrate.recurrence_groups module"
  - "src/learnloop/substrate/recurrence_groups.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.recurrence_groups`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.recurrence_groups` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: Recurrence groups (Slice 2 T1, spec_embedding_consumers_v1 §3.4).

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/recurrence_groups.py](../../../../../../src/learnloop/substrate/recurrence_groups.py) |
| Source lines | 731 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `877ad6d3f8d16d64b59c5d21a4b93a44cd291a06` |
| Commit timestamp | `2026-10-13T16:45:11-04:00` |

## Public API

- `recurrence_active(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 82)
- `active_group_map(vault: LoadedVault, repository: Repository) -> dict[str, str]` ([source](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 90) — The group map in force for this vault's EFFECTIVE config, else empty.
- `class Episode` ([source](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 114)
- `class EpisodeIndex` ([source](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 125) — Statement classes over concrete episodes, by attempt.
  - `__init__(self, episodes: Sequence[Episode]) -> None` (line 128; internal)
  - `episode(self, ref: str) -> Episode | None` (line 145; public)
  - `classes_on(self, attempt_id: str) -> dict[str, list[Episode]]` (line 149; public)
  - `representative(self, attempt_id: str, statement: str) -> str | None` (line 152; public)
  - `resolve_on(self, attempt_id: str, *, prefer: str | None, facet: str | None) -> tuple[str | None, str]` (line 156; public)
- `load_episode_index(connection: Any) -> EpisodeIndex` ([source](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 173)
- `claim_for_citation(proposal: Mapping[str, Any], citation: Mapping[str, Any]) -> Mapping[str, Any] | None` ([source](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 194) — The pattern claim a validated citation came from.
- `class GroupBuild` ([source](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 534)
- `compute_groups(connection: Any) -> GroupBuild` ([source](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 545) — The projection's rows from the ledgers (pure read).
- `input_fingerprint(connection: Any, *, active: bool) -> str` ([source](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 616)
- `refresh_recurrence_groups(vault: LoadedVault, repository: Repository, *, force: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 658) — Recompute the projection when its inputs (or the switch) changed.
- `prepare_recurrence_groups(repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 672) — Build the groups as PREPARED (not in force): the upgrade's pre-switch step.
- `activate_recurrence_groups(vault: LoadedVault, repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 681) — Put prepared groups in force once the vault's config switch has landed.

### Module constants

- `BUILDER_VERSION` ([src/learnloop/substrate/recurrence_groups.py](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 64)
- `AUTHORITY` ([src/learnloop/substrate/recurrence_groups.py](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 67)
- `NOMINATED_BY_SHORTLIST` ([src/learnloop/substrate/recurrence_groups.py](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 74)
- `NOMINATED_BY_CITATION` ([src/learnloop/substrate/recurrence_groups.py](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 75)
- `NOMINATED_BY_M1_LINK` ([src/learnloop/substrate/recurrence_groups.py](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 76)
- `NOMINATED_OTHERWISE` ([src/learnloop/substrate/recurrence_groups.py](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 77)
- `_VERDICTS` ([src/learnloop/substrate/recurrence_groups.py](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 78)
- `CAUSE_REF_PREFIX` ([src/learnloop/substrate/recurrence_groups.py](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 79)

### Explicit exports

`__all__` declares:

- `AUTHORITY`
- `NOMINATED_BY_CITATION`
- `NOMINATED_BY_M1_LINK`
- `NOMINATED_BY_SHORTLIST`
- `NOMINATED_OTHERWISE`
- `activate_recurrence_groups`
- `active_group_map`
- `BUILDER_VERSION`
- `EpisodeIndex`
- `GroupBuild`
- `claim_for_citation`
- `compute_groups`
- `input_fingerprint`
- `load_episode_index`
- `prepare_recurrence_groups`
- `recurrence_active`
- `refresh_recurrence_groups`

## Internal implementation anchors

- `_facet_of(target_ref: Any) -> str | None` ([source](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 103)
- `_case_id(*parts: Any) -> str` ([source](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 109)
- `_primary_statement(event: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 226) — The event's highest-weight cause (first on ties), normalized.
- `_continuing_class(index: 'EpisodeIndex', proposal: Mapping[str, Any], attempt_id: str, episode_key: str) -> str | None` ([source](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 243)
- `_cause_of(proposal: Mapping[str, Any], ref: str) -> tuple[str, str | None] | None` ([source](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 258) — (normalized statement, target facet) of ``cause:<event>:<cause>``.
- `class _Build` ([source](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 276)
- `_source_citations(build: _Build, diagnoses: Sequence[Mapping[str, Any]]) -> None` ([source](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 374)
- `_source_taps(build: _Build, connection: Any) -> None` ([source](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 395)
- `_source_judgments(build: _Build, connection: Any) -> None` ([source](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 426)
- `_source_registry_disagreements(build: _Build, diagnoses: Sequence[Mapping[str, Any]]) -> None` ([source](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 498) — §3.5: the diagnoser's registry match vs the top-1 neighbour by embedding.
- `_write(repository: Repository, *, active: bool, force: bool, prepare: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 621)
- `_counts(state: Mapping[str, Any]) -> dict[str, int]` ([source](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 654)
- `_has_projection(connection: Any) -> bool` ([source](../../../../../../src/learnloop/substrate/recurrence_groups.py), line 707)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/error_hunt|learnloop.diagnosis.error_hunt]] — imports `active_group_map`; statically calls `active_group_map`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `active_group_map`, `refresh_recurrence_groups`; statically calls `active_group_map`, `refresh_recurrence_groups`
- [[Reference/Modules/learnloop/diagnosis/recurrence/backlog|learnloop.diagnosis.recurrence.backlog]] — imports `refresh_recurrence_groups`; statically calls `refresh_recurrence_groups`
- [[Reference/Modules/learnloop/diagnosis/recurrence/benchmarks|learnloop.diagnosis.recurrence.benchmarks]] — imports `AUTHORITY`, `NOMINATED_BY_CITATION`, `NOMINATED_BY_M1_LINK`, `NOMINATED_BY_SHORTLIST`, `compute_groups`; statically calls `compute_groups`
- [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] — imports `active_group_map`, `compute_groups`; statically calls `active_group_map`, `compute_groups`
- [[Reference/Modules/learnloop/diagnosis/recurrence/live|learnloop.diagnosis.recurrence.live]] — imports `active_group_map`, `recurrence_active`, `refresh_recurrence_groups`; statically calls `active_group_map`, `recurrence_active`, `refresh_recurrence_groups`
- [[Reference/Modules/learnloop/diagnosis/recurrence/upgrade|learnloop.diagnosis.recurrence.upgrade]] — imports `activate_recurrence_groups`, `prepare_recurrence_groups`; statically calls `activate_recurrence_groups`, `prepare_recurrence_groups`
- [[Reference/Modules/learnloop/diagnosis/split/card|learnloop.diagnosis.split.card]] — imports `refresh_recurrence_groups`; statically calls `refresh_recurrence_groups`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `claim_for_citation`, `recurrence_active`; statically calls `claim_for_citation`, `recurrence_active`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `active_group_map`, `refresh_recurrence_groups`; statically calls `active_group_map`, `refresh_recurrence_groups`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `refresh_recurrence_groups`; statically calls `refresh_recurrence_groups`
- [[Reference/Modules/learnloop/tutor/durable_promotion|learnloop.tutor.durable_promotion]] — imports `active_group_map`; statically calls `active_group_map`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `DECIDER_TIER1_VERSIONS`, `RECURRENCE_GROUP_VERSIONS`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/recurrence|learnloop.db.stores.recurrence]] — imports `module`; calls `activate_prepared_projection`, `clear_recurrence_projection`, `diagnoses_in_force`, `diagnosis_with_citations`, `hypothesis_episode_rows`, `input_fingerprint_parts`, `not_same_mistake_taps`, `projection_present`, `recurrence_state`, `replace_recurrence_projection`, `same_cause_judgments`
- [[Reference/Modules/learnloop/matching/union|learnloop.matching.union]] — imports `UnionEdge`, `union_with_refusals`; calls `UnionEdge`, `union_with_refusals`
- [[Reference/Modules/learnloop/recurrence|learnloop.recurrence]] — imports `GROUP_RECURRENCE_KEY_VERSION`, `group_key_for`, `normalize_statement`; calls `group_key_for`, `normalize_statement`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/error_hunt|learnloop.diagnosis.error_hunt]], [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]], [[Reference/Modules/learnloop/diagnosis/recurrence/backlog|learnloop.diagnosis.recurrence.backlog]], [[Reference/Modules/learnloop/diagnosis/recurrence/benchmarks|learnloop.diagnosis.recurrence.benchmarks]], [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] and 7 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_decider_landing.py](../../../../../../tests/test_decider_landing.py) — direct import
  - `test_a_link_recorded_at_main_mvp020_or_mvp021_has_no_decider_authority`
- [tests/test_method_explicit_upgrade.py](../../../../../../tests/test_method_explicit_upgrade.py) — direct import
  - `test_each_version_activates_exactly_its_features`
- [tests/test_mvp011_upgrade.py](../../../../../../tests/test_mvp011_upgrade.py) — direct import
  - `test_new_vaults_start_at_the_latest_version`
- [tests/test_mvp013_upgrade.py](../../../../../../tests/test_mvp013_upgrade.py) — direct import
  - `test_an_earlier_vault_goes_through_mvp012s_guard`
  - `test_kill_switch_keeps_the_version_and_every_predecessor`
  - `test_only_mvp013_offers_the_stuck_control`
  - `test_upgrade_from_mvp012_flips_rebuilds_and_preserves_raw_history`
- [tests/test_mvp014_upgrade.py](../../../../../../tests/test_mvp014_upgrade.py) — direct import
  - `test_an_earlier_vault_goes_through_mvp012s_guard`
  - `test_the_plan_serves_only_at_the_successor_with_the_switch_on`
  - `test_upgrade_from_mvp013_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp015_upgrade.py](../../../../../../tests/test_mvp015_upgrade.py) — direct import
  - `test_an_earlier_vault_goes_through_mvp012s_guard_when_it_is_required`
  - `test_each_version_activates_exactly_its_features`
- [tests/test_mvp016_upgrade.py](../../../../../../tests/test_mvp016_upgrade.py) — direct import
  - `test_an_earlier_vault_goes_through_mvp012s_guard_when_it_is_required`
  - `test_each_version_activates_exactly_its_features`
- [tests/test_mvp017_upgrade.py](../../../../../../tests/test_mvp017_upgrade.py) — direct import
  - `test_an_earlier_vault_goes_through_mvp012s_guard_when_it_is_required`
  - `test_each_version_activates_exactly_its_features`
- [tests/test_mvp018_upgrade.py](../../../../../../tests/test_mvp018_upgrade.py) — direct import
  - `test_each_version_keeps_its_predecessors_and_grades_as_mvp016`
- [tests/test_mvp020_upgrade.py](../../../../../../tests/test_mvp020_upgrade.py) — direct import
  - `test_an_earlier_vault_goes_through_mvp012s_guard_when_it_is_required`
  - `test_each_version_activates_exactly_its_features`
- [tests/test_mvp021_upgrade.py](../../../../../../tests/test_mvp021_upgrade.py) — direct import
  - `test_an_earlier_vault_goes_through_mvp012s_guard_when_it_is_required`
  - `test_each_version_activates_exactly_its_features`
- [tests/test_reading_step_switch.py](../../../../../../tests/test_reading_step_switch.py) — direct import
  - `test_the_reading_step_acts_wherever_the_plan_acts_behind_its_switch`
- [tests/test_recurrence_commands.py](../../../../../../tests/test_recurrence_commands.py) — direct import
  - `test_a_failure_after_preparation_leaves_no_group_in_force`
  - `test_the_kill_switch_takes_effect_at_vault_open_with_groups_already_populated`
- [tests/test_recurrence_groups.py](../../../../../../tests/test_recurrence_groups.py) — direct import
  - `test_a_different_verdict_inside_one_exact_class_is_a_review_case_not_a_split`
  - `test_a_later_same_at_the_judges_authority_is_refused_and_logged`
  - `test_a_same_verdict_merges_two_classes_into_one_group_key`
  - `test_an_owner_different_refuses_the_judge_merge_and_logs_it`
  - `test_an_unchanged_fingerprint_skips_the_rebuild`
  - `test_attempt_level_owner_verdicts_resolve_only_to_one_class_per_side`
  - `test_claim_lookup_survives_a_claim_dropped_by_validation`
  - `test_compute_groups_is_a_pure_read`
  - `test_no_merges_leave_every_key_exact_and_the_projection_empty`
  - `test_planted_subjects_never_touch_vault_groups`
  - `test_registry_disagreements_need_an_informative_ranking`
  - `test_supersession_is_how_a_judges_different_is_replaced`
  - `test_the_successor_and_its_kill_switch_gate_the_projection`
- [tests/test_recurrence_live.py](../../../../../../tests/test_recurrence_live.py) — direct import
  - `test_a_citation_of_an_existing_hypothesis_resolves_through_prior_hypothesis_id`
  - `test_a_verdict_after_a_promotion_moves_only_the_group_projection_and_rebuild_matches_live`
- [tests/test_recurrence_merge_composition.py](../../../../../../tests/test_recurrence_merge_composition.py) — direct import
  - `test_a_decider_same_cause_verdict_is_logged_but_joins_no_group`
- [tests/test_tier1_decider.py](../../../../../../tests/test_tier1_decider.py) — direct import
  - `test_only_new_authoritative_decider_links_reach_recurrence`

## Modification guidance

- Change recurrence groups policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/recurrence_groups.py](../../../../../../src/learnloop/substrate/recurrence_groups.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
