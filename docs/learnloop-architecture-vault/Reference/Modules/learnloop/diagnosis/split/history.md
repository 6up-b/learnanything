---
title: "learnloop.diagnosis.split.history"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/split/history.py"
source_paths:
  - "src/learnloop/diagnosis/split/history.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.split"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.split.history module"
  - "src/learnloop/diagnosis/split/history.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-split"
---

# `learnloop.diagnosis.split.history`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.split.history` exists within [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] to own the behavior summarized by its module contract: Typed, blind-grade-equivalent history for the diagnoser (Slice 1 §5.2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/split/history.py](../../../../../../../src/learnloop/diagnosis/split/history.py) |
| Source lines | 1427 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class AttemptRef` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 92) — Where an attempt sits on the global chronological axis.
  - `key(self) -> tuple[str, str]` (line 98; public)
- `class HistoryAttempt` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 103) — One prior attempt, rendered from blind-grade-equivalent fields only.
  - `key(self) -> tuple[str, str]` (line 150; public)
  - `evidence_units(self) -> list[tuple[frozenset[str], bool]]` (line 153; public) — Each non-pass observation as (facets it bears on, valid measurement?).
  - `recurrence_invalid_reason(self, targets: Iterable[str]) -> str | None` (line 200; public) — S4 on the overlapping target itself; ``None`` when a citation counts.
  - `non_pass(self) -> bool` (line 220; public) — Any non-full criterion, fatal error or error attribution.
  - `cold_unassisted(self) -> bool` (line 226; public)
  - `valid_measurement(self) -> bool` (line 230; public) — S4: at least one attribution is a valid measurement (or none flagged).
  - `facets(self) -> frozenset[str]` (line 237; public)
  - `failure_facets(self) -> frozenset[str]` (line 240; public) — Where this attempt's blind grade shows a non-pass (S4 overlap).
- `class HypothesisRecord` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 247) — A typed prior hypothesis, factor or durable misconception (no prose).
- `class RegistryRecord` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 265) — A durable misconception or a holding-pen candidate the diagnoser may match.
- `class RepairRecord` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 279) — A repair tried on these facets and how its cold verifications went.
- `class Neighborhood` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 292) — The LO and its one-hop prerequisite / confusable neighbours (§5.2).
  - `all_ids(self) -> tuple[str, ...]` (line 301; public)
  - `relation(self, learning_object_id: str) -> str` (line 312; public)
- `learning_object_neighborhood(vault: LoadedVault, learning_object_id: str) -> Neighborhood` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 326) — One hop over prerequisite and confusable edges, both directions.
- `class HistoryStore(Protocol)` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 389) — What the context assembler reads; every method applies ``before``.
  - `attempt(self, attempt_id: str) -> HistoryAttempt | None` (line 392; public)
  - `attempts_before(self, before: AttemptRef, learning_object_ids: Sequence[str] | None=None) -> list[HistoryAttempt]` (line 395; public) — Prior attempts in chronological order; ``None`` = the whole vault.
  - `hypotheses_before(self, before: AttemptRef, learning_object_ids: Sequence[str]) -> list[HypothesisRecord]` (line 401; public)
  - `registry_before(self, before: AttemptRef, learning_object_ids: Sequence[str] | None) -> list[RegistryRecord]` (line 406; public)
  - `repairs_before(self, before: AttemptRef, facets: Iterable[str] | None) -> list[RepairRecord]` (line 411; public)
  - `lagged_attempts(self, before: AttemptRef) -> int` (line 416; public) — Attempts that exist after the cutoff (async lag disclosure).
- `criterion_facets(vault: LoadedVault, item: PracticeItem | None) -> dict[str, tuple[str, ...]]` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 492) — Each criterion's measured facets: authored targets, else the item's facets.
- `history_attempt_from_blind_record(vault: LoadedVault, *, attempt_id: str, item: PracticeItem | None, learning_object_id: str, practice_item_id: str, completed_at: str, learner_answer_md: str, attempt_type: str, record: Mapping[str, Any], hints_used: int=0, primed: bool=False, contract: Mapping[str, Any] | None=None) -> HistoryAttempt` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 565) — Blind-grade-equivalent fields from a validated blind grade record.
- `class VaultHistoryStore` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 684) — History read from a vault database, with an optional blind-grade overlay.
  - `__init__(self, vault: LoadedVault, repository: Repository, *, blind_grades: Mapping[str, Mapping[str, Any]] | None=None, grading_marks: Mapping[str, str] | None=None) -> None` (line 692; internal)
  - `with_blind_grades(self, blind_grades: Mapping[str, Mapping[str, Any]]) -> 'VaultHistoryStore'` (line 729; public)
  - `blind_grade(self, attempt_id: str) -> Mapping[str, Any] | None` (line 737; public) — The overlay's blind record of ``attempt_id`` (read with its grading's identity by ``live.live_history_store``), or None.
  - `_held(self, attempt_id: str, ledger_held: frozenset[str]) -> bool` (line 743; internal) — Is the grade this store shows for ``attempt_id`` held for review?
  - `_load(self) -> None` (line 764; internal)
  - `_written_before(written: datetime | None, before: AttemptRef) -> bool` (line 1063; internal) — Whether a record was written strictly before the cutoff attempt.
  - `_visible(self, entry: _Written, before: AttemptRef) -> bool` (line 1073; internal)
  - `_hypotheses_as_of(self, before: AttemptRef) -> list[HypothesisRecord]` (line 1078; internal) — Every hypothesis as it stood at ``before``.
  - `_observed_before(self, cold_attempt_id: str, written: datetime | None, before: AttemptRef) -> bool` (line 1107; internal) — A cold verification counts as of ``before`` only when it was recorded before it AND its cold attempt (when known) precedes it.
  - `_repair_as_of(self, entry: tuple[Any, ...], visible_hypotheses: Sequence[HypothesisRecord], before: AttemptRef) -> RepairRecord | None` (line 1116; internal)
  - `_earliest_source(self, error_event_ids: Sequence[str]) -> str | None` (line 1134; internal)
  - `_from_stored(self, row: Mapping[str, Any], item: PracticeItem | None, points: Mapping[str, float], events: Sequence[Mapping[str, Any]], fatal: Sequence[str], *, has_unassessed: bool=False, contract: Mapping[str, Any] | None=None) -> HistoryAttempt` (line 1144; internal) — A stored joint grade, reduced to blind-grade-equivalent fields (S3).
  - `attempt(self, attempt_id: str) -> HistoryAttempt | None` (line 1226; public)
  - `ref(self, attempt_id: str) -> AttemptRef | None` (line 1230; public)
  - `all_attempts(self) -> list[HistoryAttempt]` (line 1235; public)
  - `grading_marks(self) -> dict[str, str]` (line 1239; public) — Each attempt's grading identity as this store read it, in one snapshot with what it shows (``write_provenance.grading_marks``: the payload, the contract and the provenance): a record frozen later names every grading replaced since (diagnosis input provenance, codex review F3 and…
  - `_cutoff(self, before: AttemptRef) -> datetime | None` (line 1249; internal) — When the decision at ``before`` was made: when its attempt became known (an import's receipt), else when it happened.
  - `_known_by(self, attempt_id: str, cutoff: datetime | None) -> bool` (line 1255; internal) — RO1 §5.3: True unless the attempt became known after the cutoff (always True with the gate off or below the tag, where nothing is held in ``_known``).
  - `attempts_before(self, before: AttemptRef, learning_object_ids: Sequence[str] | None=None) -> list[HistoryAttempt]` (line 1262; public)
  - `_source_before(self, source_attempt_id: str | None, before: AttemptRef) -> bool` (line 1276; internal)
  - `hypotheses_before(self, before: AttemptRef, learning_object_ids: Sequence[str]) -> list[HypothesisRecord]` (line 1283; public)
  - `registry_before(self, before: AttemptRef, learning_object_ids: Sequence[str] | None) -> list[RegistryRecord]` (line 1290; public)
  - `repairs_before(self, before: AttemptRef, facets: Iterable[str] | None) -> list[RepairRecord]` (line 1302; public)
  - `lagged_attempts(self, before: AttemptRef) -> int` (line 1315; public) — Attempts the cutoff does not show: after it, and (RO1 §5.3) before it but not yet known.
- `class StaticHistoryStore` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 1325) — An explicit history, e.g.
  - `__post_init__(self) -> None` (line 1333; internal)
  - `add(self, attempt: HistoryAttempt) -> None` (line 1337; public)
  - `replace_attempt(self, attempt: HistoryAttempt) -> None` (line 1341; public)
  - `attempt(self, attempt_id: str) -> HistoryAttempt | None` (line 1347; public)
  - `ref(self, attempt_id: str) -> AttemptRef | None` (line 1350; public)
  - `all_attempts(self) -> list[HistoryAttempt]` (line 1354; public)
  - `attempts_before(self, before: AttemptRef, learning_object_ids: Sequence[str] | None=None) -> list[HistoryAttempt]` (line 1357; public)
  - `_before(self, source: str | None, before: AttemptRef) -> bool` (line 1368; internal)
  - `hypotheses_before(self, before: AttemptRef, learning_object_ids: Sequence[str]) -> list[HypothesisRecord]` (line 1372; public)
  - `registry_before(self, before: AttemptRef, learning_object_ids: Sequence[str] | None) -> list[RegistryRecord]` (line 1382; public)
  - `repairs_before(self, before: AttemptRef, facets: Iterable[str] | None) -> list[RepairRecord]` (line 1393; public)
  - `lagged_attempts(self, before: AttemptRef) -> int` (line 1404; public)
- `with_blind_overlay(attempt: HistoryAttempt, **changes: Any) -> HistoryAttempt` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 1408)

### Module constants

- `NON_MEASURING_ATTEMPT_TYPES` ([src/learnloop/diagnosis/split/history.py](../../../../../../../src/learnloop/diagnosis/split/history.py), line 63)
- `ASSISTED_ATTEMPT_TYPES` ([src/learnloop/diagnosis/split/history.py](../../../../../../../src/learnloop/diagnosis/split/history.py), line 64)
- `_VALIDITY_FROM_JOINT` ([src/learnloop/diagnosis/split/history.py](../../../../../../../src/learnloop/diagnosis/split/history.py), line 70)
- `_HYPOTHESIS_LIFECYCLE` ([src/learnloop/diagnosis/split/history.py](../../../../../../../src/learnloop/diagnosis/split/history.py), line 76)
- `_FACTOR_LIFECYCLE` ([src/learnloop/diagnosis/split/history.py](../../../../../../../src/learnloop/diagnosis/split/history.py), line 83)
- `_MISCONCEPTION_LIFECYCLE` ([src/learnloop/diagnosis/split/history.py](../../../../../../../src/learnloop/diagnosis/split/history.py), line 84)

### Explicit exports

`__all__` declares:

- `ASSISTED_ATTEMPT_TYPES`
- `AttemptRef`
- `HistoryAttempt`
- `HistoryStore`
- `HypothesisRecord`
- `Neighborhood`
- `NON_MEASURING_ATTEMPT_TYPES`
- `RegistryRecord`
- `RepairRecord`
- `StaticHistoryStore`
- `VaultHistoryStore`
- `criterion_facets`
- `history_attempt_from_blind_record`
- `learning_object_neighborhood`

## Internal implementation anchors

- `_instant(value: Any) -> datetime | None` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 421) — A stored timestamp as an aware UTC instant; unparseable -> None.
- `class _Written` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 433) — A history record with the instant it was written (F5, as of a cutoff).
- `_learner_text_candidate_ids(connection: Any, vault: LoadedVault) -> frozenset[str]` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 453) — Holding-pen candidates a learner's text named (learner-text gaps), while the pipeline and its sightings are switched on.
- `_decode_json(value: Any, default: Any) -> Any` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 471)
- `_max_points_by_criterion(vault: LoadedVault, item: PracticeItem | None) -> tuple[dict[str, float], float | None]` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 482)
- `_failed_facets(vault: LoadedVault, item: PracticeItem | None, failed: Sequence[str]) -> tuple[str, ...]` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 512)
- `_criterion_facet_sets(vault: LoadedVault, item: PracticeItem | None, criteria: Sequence[str]) -> tuple[tuple[str, ...], ...]` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 518) — Per criterion (in order), the facets it measures.
- `_attribution_alignment(vault: LoadedVault, item: PracticeItem | None, attributions: Sequence[Mapping[str, Any]]) -> tuple[tuple[tuple[str, ...], ...], tuple[tuple[str, ...], ...]]` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 526) — Per attribution: (facets it bears on, criteria it targets).
- `_target_facets_from(attribution: Mapping[str, Any], vault: LoadedVault) -> list[str]` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 547)
- `_quote_from(first_divergence: Any) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 558)
- `_with_confidence(record: HistoryAttempt, tap: Any, hedge: str | None, *, held: bool) -> HistoryAttempt` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 649) — TE0: the attempt with its tap and confidence event (unchanged with neither).
- `_ledger_marks(connection: Any, vault: Any) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 660) — FG1c: every mark by attempt; none with the kill switch off (the history is its predecessor's).
- `_marks_as_of(attempt: HistoryAttempt, before: AttemptRef) -> HistoryAttempt` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 674) — The marks a context cut off at ``before`` could have read: nothing written after it.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/offline_review/planted|learnloop.diagnosis.offline_review.planted]] — imports `HistoryAttempt`, `HypothesisRecord`, `StaticHistoryStore`, `learning_object_neighborhood`; statically calls `HistoryAttempt`, `HypothesisRecord`, `StaticHistoryStore`, `learning_object_neighborhood`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `HistoryAttempt`, `StaticHistoryStore`, `VaultHistoryStore`, `learning_object_neighborhood`; statically calls `StaticHistoryStore`, `VaultHistoryStore`, `learning_object_neighborhood`
- [[Reference/Modules/learnloop/diagnosis/offline_review/spot_check|learnloop.diagnosis.offline_review.spot_check]] — imports `VaultHistoryStore`; statically calls `VaultHistoryStore`
- [[Reference/Modules/learnloop/diagnosis/split/context|learnloop.diagnosis.split.context]] — imports `AttemptRef`, `HistoryAttempt`, `HistoryStore`, `HypothesisRecord`, `Neighborhood`, `RegistryRecord`, `RepairRecord`, `learning_object_neighborhood`; statically calls `AttemptRef`, `learning_object_neighborhood`
- [[Reference/Modules/learnloop/diagnosis/split/diagnoser|learnloop.diagnosis.split.diagnoser]] — imports `HistoryStore`
- [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]] — imports `VaultHistoryStore`; statically calls `VaultHistoryStore`
- [[Reference/Modules/learnloop/diagnosis/split/retrieval|learnloop.diagnosis.split.retrieval]] — imports `HistoryAttempt`, `RegistryRecord`
- [[Reference/Modules/learnloop/diagnosis/split/snapshot|learnloop.diagnosis.split.snapshot]] — imports `AttemptRef`, `HistoryAttempt`, `HistoryStore`, `HypothesisRecord`, `RegistryRecord`, `RepairRecord`
- [[Reference/Modules/learnloop/diagnosis/split/validation|learnloop.diagnosis.split.validation]] — imports `HistoryAttempt`, `HistoryStore`
- [[Reference/Modules/learnloop/field/probability_states|learnloop.field.probability_states]] — imports `AttemptRef`, `HistoryAttempt`, `HypothesisRecord`, `VaultHistoryStore`, `learning_object_neighborhood`; statically calls `AttemptRef`, `VaultHistoryStore`, `learning_object_neighborhood`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `resolved_rubric`; calls `resolved_rubric`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/confidence_events|learnloop.confidence_events]] — imports `module`; calls `Reading`, `enabled`, `event_text`, `hedge_from_record`, `read_hedges`, `result_class`, `valid_tap`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/answered_contracts|learnloop.db.stores.answered_contracts]] — imports `answered_contracts`; calls `answered_contracts`
- [[Reference/Modules/learnloop/db/stores/hypothesis_marks|learnloop.db.stores.hypothesis_marks]] — imports `module`; calls `all_marks`, `present`
- [[Reference/Modules/learnloop/db/stores/write_provenance|learnloop.db.stores.write_provenance]] — imports `UNIDENTIFIED_GRADING`, `grading_marks`, `read_snapshot`, `replaced_error_event_attempts`; calls `grading_marks`, `read_snapshot`, `replaced_error_event_attempts`
- [[Reference/Modules/learnloop/followup_serve/gates|learnloop.followup_serve.gates]] — imports `hypothesis_marks_on`; calls `hypothesis_marks_on`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `grade_held_for_review`; calls `grade_held_for_review`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `attempt_time_sql`, `known_at`, `validated_resolution_ids`; calls `attempt_time_sql`, `known_at`, `validated_resolution_ids`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `UNVERIFIED_CRITERION_BLOCK`, `held_for_review_attempts`, `surface_group_id`, `unverified_evidence_row`; calls `held_for_review_attempts`, `surface_group_id`, `unverified_evidence_row`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `answered_prompt`; calls `answered_prompt`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/offline_review/planted|learnloop.diagnosis.offline_review.planted]], [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]], [[Reference/Modules/learnloop/diagnosis/offline_review/spot_check|learnloop.diagnosis.offline_review.spot_check]], [[Reference/Modules/learnloop/diagnosis/split/context|learnloop.diagnosis.split.context]], [[Reference/Modules/learnloop/diagnosis/split/diagnoser|learnloop.diagnosis.split.diagnoser]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/learner_blindness_relax_helpers.py](../../../../../../../tests/learner_blindness_relax_helpers.py) — direct import
- [tests/test_chatgpt_plan_workspace.py](../../../../../../../tests/test_chatgpt_plan_workspace.py) — direct import
- [tests/test_diagnosis_context.py](../../../../../../../tests/test_diagnosis_context.py) — direct import
  - `test_a_stored_grade_without_criterion_rows_is_still_a_non_pass`
  - `test_assembly_and_hash_are_deterministic`
  - `test_current_attempt_renders_last_with_its_blind_grade`
  - `test_exact_mode_selects_neighbourhood_failures_and_successes_as_of`
  - `test_legacy_joint_attempts_are_stripped_of_causal_fields`
  - `test_neighbourhood_and_as_of_prerequisite_status`
  - `test_repair_chain_source_is_visible_to_the_diagnoser`
  - `test_truncation_drops_oldest_first_and_discloses`
- [tests/test_diagnosis_contract.py](../../../../../../../tests/test_diagnosis_contract.py) — direct import
  - `test_citation_validity_is_judged_on_the_overlapping_target_itself`
  - `test_citation_without_target_overlap_or_valid_measurement_is_not_counted`
- [tests/test_diagnosis_history_modes.py](../../../../../../../tests/test_diagnosis_history_modes.py) — direct import
  - `test_as_of_history_needs_each_record_written_before_the_cutoff`
  - `test_every_mode_keeps_s3_and_validates_evidence_ids`
  - `test_full_budget_truncates_oldest_attempts_before_any_hypothesis`
  - `test_full_includes_every_neighbour_attempt_chronologically`
  - `test_full_stable_prefix_is_shared_by_consecutive_diagnoses_on_one_lo`
  - `test_hybrid_degrades_to_exact_when_embeddings_fail`
  - `test_hybrid_fuses_exact_and_knn_and_records_provenance`
  - `test_repairs_before_filters_owners_and_cold_outcomes_by_the_cutoff`
  - `test_snapshot_export_is_as_of_and_stripped`
  - `test_snapshot_is_unavailable_without_the_capability`
  - `test_snapshot_workspace_is_deleted_on_success_and_on_failure`
- [tests/test_diagnosis_input_provenance.py](../../../../../../../tests/test_diagnosis_input_provenance.py) — direct import
  - `test_a_regrade_keeps_the_ids_a_belief_lists_resolvable`
  - `test_f3_a_grading_replaced_after_the_history_was_read_is_unaccountable`
  - `test_f4_a_regrade_to_no_errors_keeps_the_retired_events_answer`
  - `test_rereview_f3_a_payload_its_caller_supplied_is_never_certified`
  - `test_rereview_f3_the_overlay_s_payload_is_validated_by_the_identity_captured_with_it`
- [tests/test_followup_fg1c_codex_review.py](../../../../../../../tests/test_followup_fg1c_codex_review.py) — direct import
  - `test_f1_a_history_attempt_folds_the_causes_its_marks_show_as_of_its_cutoff`
  - `test_f1_a_rediagnosis_records_the_cause_it_was_shown_through_a_mark`
  - `test_f1_only_the_causes_a_context_still_shows_are_folded`
  - `test_f1_the_snapshot_entry_of_a_marked_attempt_carries_the_cause`
- [tests/test_hypothesis_marks.py](../../../../../../../tests/test_hypothesis_marks.py) — direct import
  - `test_the_diagnoser_reads_only_marks_made_before_the_attempt_it_is_on`
  - `test_the_switch_off_keeps_the_diagnosers_context_as_it_was_whatever_rows_exist`
- [tests/test_learner_text_gaps.py](../../../../../../../tests/test_learner_text_gaps.py) — direct import
  - `test_a_tutor_question_that_states_a_belief_reaches_the_holding_pen`
- [tests/test_pfc_unassessed_readers.py](../../../../../../../tests/test_pfc_unassessed_readers.py) — direct import
  - `test_a_later_diagnosis_cannot_cite_an_unassessed_shortfall_as_a_recurrence`
- [tests/test_required_method_round3_review.py](../../../../../../../tests/test_required_method_round3_review.py) — direct import
  - `test_f3_the_diagnosers_history_and_current_attempt_read_the_question_given`
- [tests/test_ro1_availability_reads.py](../../../../../../../tests/test_ro1_availability_reads.py) — direct import
  - `test_the_diagnosers_prior_history_has_no_exam_before_its_import_at_the_tag`
  - `test_the_exam_rows_before_an_imported_target_follow_the_import`
- [tests/test_ro1_projection.py](../../../../../../../tests/test_ro1_projection.py) — direct import
- [tests/test_ro1_self_report.py](../../../../../../../tests/test_ro1_self_report.py) — direct import
- [tests/test_teacher_te0_confidence_events.py](../../../../../../../tests/test_teacher_te0_confidence_events.py) — direct import
  - `test_the_diagnosers_history_and_current_attempt_carry_the_events`
- [tests/test_teacher_te0_review_fixes.py](../../../../../../../tests/test_teacher_te0_review_fixes.py) — direct import
  - `test_switched_off_every_reader_gets_its_predecessor_context`

## Modification guidance

- Change history policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/split/history.py](../../../../../../../src/learnloop/diagnosis/split/history.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
