---
title: "learnloop.diagnosis.probe_targeting"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/probe_targeting.py"
source_paths:
  - "src/learnloop/diagnosis/probe_targeting.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.probe_targeting module"
  - "src/learnloop/diagnosis/probe_targeting.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.probe_targeting`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.probe_targeting` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Unresolved-cause-set probe targeting (knowledge-model §11.1).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/probe_targeting.py](../../../../../../src/learnloop/diagnosis/probe_targeting.py) |
| Source lines | 886 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `prerequisite_already_demonstrated(vault: LoadedVault, repository: Repository, facet: str, capability: str) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 112) — True when a facet-capability already has direct/embedded certification.
- `should_suppress_prerequisite_probe(vault: LoadedVault, repository: Repository, prerequisite: dict[str, str]) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 123)
- `class CauseSetTargeting` ([source](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 137) — One open cause set plus its typed repair-mapping state.
  - `probe_worthy(self) -> bool` (line 159; public) — True only for a genuinely divergent set — never for missing data.
  - `needs_machine_backfill(self) -> bool` (line 165; public)
  - `coherence_gate_state(self) -> str` (line 169; public) — The same state spelled in `causal_probe_coherence`'s vocabulary.
  - `as_dict(self) -> dict[str, Any]` (line 174; public)
- `concrete_candidate_causes(causes: list[dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 203) — The closed-world arms of a cause set (the open-set arm is never one).
- `active_candidate_causes(causes: list[dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 209) — Concrete causes still in play — retired/refuted arms cannot be probed.
- `classify_cause_set(causes: list[dict[str, Any]], *, repository: Repository | None=None, factor_id: str | None=None, attempt_id: str | None=None, memo: dict[str, tuple[str | None, str | None]] | None=None) -> CauseSetTargeting` ([source](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 262) — Type one cause set as common-cover / divergent / incomplete mapping.
- `open_cause_set_states_for_learning_object(vault: LoadedVault, repository: Repository, learning_object_id: str) -> list[CauseSetTargeting]` ([source](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 363) — Every open, open-world cause set on this LO with its typed state.
- `open_cause_sets_for_learning_object(vault: LoadedVault, repository: Repository, learning_object_id: str) -> list[list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 429) — Probe-worthy candidate-cause sets from open factors on this LO.
- `repair_mapping_backfills(vault: LoadedVault, repository: Repository, learning_object_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 451) — Machine-side checks owed before any probe on this LO can be offered.
- `class RankedInstrument` ([source](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 483)
  - `item_id(self) -> str` (line 488; public)
- `class InstrumentRanking` ([source](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 493) — Ranked eligible instruments plus the rationale that ordered them.
  - `selected(self) -> Any | None` (line 503; public)
  - `as_dict(self) -> dict[str, Any]` (line 506; public)
- `rank_discriminating_instruments(candidate_causes: list[dict[str, Any]], eligible: list[Any], *, repository: Repository | None=None) -> InstrumentRanking` ([source](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 621) — Rank eligible instruments for a cause set, repair-class first.
- `select_discriminating_instrument(candidate_causes: list[dict[str, Any]], eligible: list[Any], *, repository: Repository | None=None) -> Any | None` ([source](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 694) — Pick the eligible instrument that best discriminates the candidate causes.
- `next_cause_set_instrument(vault: LoadedVault, repository: Repository, episode: Any, *, candidate_causes: list[dict[str, Any]] | None=None) -> Any | None` ([source](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 712) — Serve the discriminating instrument for a cause-set diagnostic episode.
- `integration_condition_target(vault: LoadedVault, repository: Repository, learning_object: LearningObject) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 741) — Components strong AND integration weak -> probe coordination, not components.
- `probe_priority(vault: LoadedVault, repository: Repository, learning_object: LearningObject, *, bottleneck: dict[str, Any] | None=None, transfer_target: dict[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 764) — Resolve the §11.1 priority order into one selected diagnostic target.

### Module constants

- `CAUSE_SET_COMMON_COVER` ([src/learnloop/diagnosis/probe_targeting.py](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 78)
- `CAUSE_SET_DIVERGENT` ([src/learnloop/diagnosis/probe_targeting.py](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 79)
- `CAUSE_SET_INCOMPLETE_MAPPING` ([src/learnloop/diagnosis/probe_targeting.py](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 80)
- `CAUSE_SET_STATES` ([src/learnloop/diagnosis/probe_targeting.py](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 82)
- `COHERENCE_GATE_STATE` ([src/learnloop/diagnosis/probe_targeting.py](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 88)
- `MAPPING_BASIS_REPAIR_CLASS` ([src/learnloop/diagnosis/probe_targeting.py](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 95)
- `MAPPING_BASIS_LEGACY_FACET` ([src/learnloop/diagnosis/probe_targeting.py](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 96)
- `REPAIR_BASIS_CAUSE_ROW` ([src/learnloop/diagnosis/probe_targeting.py](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 99)
- `REPAIR_BASIS_HYPOTHESIS_RECORD` ([src/learnloop/diagnosis/probe_targeting.py](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 100)
- `REPAIR_BASIS_UNRESOLVED` ([src/learnloop/diagnosis/probe_targeting.py](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 101)
- `_INACTIVE_CAUSE_STATUSES` ([src/learnloop/diagnosis/probe_targeting.py](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 104)

## Internal implementation anchors

- `_is_open_set(cause: Any) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 191)
- `_resolve_repair_class(cause: dict[str, Any], repository: Repository | None, memo: dict[str, tuple[str | None, str | None]]) -> tuple[str | None, str, str | None]` ([source](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 222) — Repair class for one cause: inline first, then the hypothesis record.
- `_candidate_labels(cause: dict[str, Any]) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 521) — Episode hypothesis labels this candidate cause could be observed under.
- `_candidate_slots(cause: dict[str, Any], eligible: Any) -> frozenset[str]` ([source](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 541) — Instrument rows this candidate cause can land on, if any are resolvable.
- `_instrument_action(eligible: Any, keys: frozenset[str] | tuple[str, ...]) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 563)
- `_score_instrument(eligible: Any, actives: list[dict[str, Any]], cause_facets: set[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_targeting.py), line 573)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `CAUSE_SET_INCOMPLETE_MAPPING`, `MAPPING_BASIS_LEGACY_FACET`, `classify_cause_set`; statically calls `classify_cause_set`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `open_cause_sets_for_learning_object`, `select_discriminating_instrument`; statically calls `open_cause_sets_for_learning_object`, `select_discriminating_instrument`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `OPEN_SET_CAUSE_ID`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `eligible_instruments`; calls `eligible_instruments`
- [[Reference/Modules/learnloop/diagnosis/probe_hypotheses|learnloop.diagnosis.probe_hypotheses]] — imports `triage_reason_for_label`; calls `triage_reason_for_label`
- [[Reference/Modules/learnloop/goals/goal_certification|learnloop.goals.goal_certification]] — imports `demonstrated_capabilities_for_facet`, `lo_certification`; calls `demonstrated_capabilities_for_facet`, `lo_certification`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LearningObject`, `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `itertools`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]], [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_p2_acceptance.py](../../../../../../tests/test_causal_p2_acceptance.py) — direct import
  - `test_causal_disambiguation_end_to_end_acceptance`
- [tests/test_causal_repair_mapping_p2.py](../../../../../../tests/test_causal_repair_mapping_p2.py) — direct import
  - `test_authored_divergent_repairs_fill_repair_class_id_end_to_end`
  - `test_repair_declared_by_criterion_maps_to_a_facet_targeted_cause`
  - `test_self_graded_attempt_records_no_repair_authored_not_a_silent_null`
  - `test_two_repairs_on_one_target_are_ambiguous_rather_than_a_guess`
- [tests/test_probe_targeting.py](../../../../../../tests/test_probe_targeting.py) — direct import
  - `test_cause_set_diagnostic_selects_discriminating_instrument`
  - `test_cause_set_state_vocabulary_matches_the_coherence_gate`
  - `test_embedded_evidence_suppresses_redundant_probe`
  - `test_incomplete_mapping_surfaces_as_a_machine_check_never_as_a_probe`
  - `test_instrument_ranking_prefers_discrimination_over_facet_coverage`
  - `test_integration_condition_probes_coordination_not_components`
  - `test_legacy_pre_p1_cause_set_keeps_the_distinct_facet_rule`
  - `test_p1_shared_repair_class_is_not_divergent_even_across_facets`
  - `test_p1_unmapped_hypothesis_is_incomplete_not_a_facet_fallback`
  - `test_repair_class_is_resolved_from_the_stored_hypothesis_record`

## Modification guidance

- Change probe targeting policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/probe_targeting.py](../../../../../../src/learnloop/diagnosis/probe_targeting.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
