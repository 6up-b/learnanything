---
title: "learnloop.diagnosis.split.history"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/split/history.py"
source_paths:
  - "src/learnloop/diagnosis/split/history.py"
source_commit: "b732478c02a0b96a364ed9023ef132ae28acaedf"
source_commit_timestamp: "2026-10-25T09:19:45-04:00"
source_worktree_state: "clean"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.split.history` exists within [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] to own the behavior summarized by its module contract: Typed, blind-grade-equivalent history for the diagnoser (Slice 1 §5.2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/split/history.py](../../../../../../../src/learnloop/diagnosis/split/history.py) |
| Source lines | 1359 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `b732478c02a0b96a364ed9023ef132ae28acaedf` |
| Commit timestamp | `2026-10-25T09:19:45-04:00` |

## Public API

- `class AttemptRef` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 91) — Where an attempt sits on the global chronological axis.
  - `key(self) -> tuple[str, str]` (line 97; public)
- `class HistoryAttempt` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 102) — One prior attempt, rendered from blind-grade-equivalent fields only.
  - `key(self) -> tuple[str, str]` (line 146; public)
  - `evidence_units(self) -> list[tuple[frozenset[str], bool]]` (line 149; public) — Each non-pass observation as (facets it bears on, valid measurement?).
  - `recurrence_invalid_reason(self, targets: Iterable[str]) -> str | None` (line 196; public) — S4 on the overlapping target itself; ``None`` when a citation counts.
  - `non_pass(self) -> bool` (line 216; public) — Any non-full criterion, fatal error or error attribution.
  - `cold_unassisted(self) -> bool` (line 222; public)
  - `valid_measurement(self) -> bool` (line 226; public) — S4: at least one attribution is a valid measurement (or none flagged).
  - `facets(self) -> frozenset[str]` (line 233; public)
  - `failure_facets(self) -> frozenset[str]` (line 236; public) — Where this attempt's blind grade shows a non-pass (S4 overlap).
- `class HypothesisRecord` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 243) — A typed prior hypothesis, factor or durable misconception (no prose).
- `class RegistryRecord` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 261) — A durable misconception or a holding-pen candidate the diagnoser may match.
- `class RepairRecord` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 275) — A repair tried on these facets and how its cold verifications went.
- `class Neighborhood` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 288) — The LO and its one-hop prerequisite / confusable neighbours (§5.2).
  - `all_ids(self) -> tuple[str, ...]` (line 297; public)
  - `relation(self, learning_object_id: str) -> str` (line 308; public)
- `learning_object_neighborhood(vault: LoadedVault, learning_object_id: str) -> Neighborhood` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 322) — One hop over prerequisite and confusable edges, both directions.
- `class HistoryStore(Protocol)` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 385) — What the context assembler reads; every method applies ``before``.
  - `attempt(self, attempt_id: str) -> HistoryAttempt | None` (line 388; public)
  - `attempts_before(self, before: AttemptRef, learning_object_ids: Sequence[str] | None=None) -> list[HistoryAttempt]` (line 391; public) — Prior attempts in chronological order; ``None`` = the whole vault.
  - `hypotheses_before(self, before: AttemptRef, learning_object_ids: Sequence[str]) -> list[HypothesisRecord]` (line 397; public)
  - `registry_before(self, before: AttemptRef, learning_object_ids: Sequence[str] | None) -> list[RegistryRecord]` (line 402; public)
  - `repairs_before(self, before: AttemptRef, facets: Iterable[str] | None) -> list[RepairRecord]` (line 407; public)
  - `lagged_attempts(self, before: AttemptRef) -> int` (line 412; public) — Attempts that exist after the cutoff (async lag disclosure).
- `criterion_facets(vault: LoadedVault, item: PracticeItem | None) -> dict[str, tuple[str, ...]]` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 488) — Each criterion's measured facets: authored targets, else the item's facets.
- `history_attempt_from_blind_record(vault: LoadedVault, *, attempt_id: str, item: PracticeItem | None, learning_object_id: str, practice_item_id: str, completed_at: str, learner_answer_md: str, attempt_type: str, record: Mapping[str, Any], hints_used: int=0, primed: bool=False, contract: Mapping[str, Any] | None=None) -> HistoryAttempt` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 561) — Blind-grade-equivalent fields from a validated blind grade record.
- `class VaultHistoryStore` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 656) — History read from a vault database, with an optional blind-grade overlay.
  - `__init__(self, vault: LoadedVault, repository: Repository, *, blind_grades: Mapping[str, Mapping[str, Any]] | None=None, grading_marks: Mapping[str, str] | None=None) -> None` (line 664; internal)
  - `with_blind_grades(self, blind_grades: Mapping[str, Mapping[str, Any]]) -> 'VaultHistoryStore'` (line 696; public)
  - `blind_grade(self, attempt_id: str) -> Mapping[str, Any] | None` (line 704; public) — The overlay's blind record of ``attempt_id`` (read with its grading's identity by ``live.live_history_store``), or None.
  - `_held(self, attempt_id: str, ledger_held: frozenset[str]) -> bool` (line 710; internal) — Is the grade this store shows for ``attempt_id`` held for review?
  - `_load(self) -> None` (line 731; internal)
  - `_written_before(written: datetime | None, before: AttemptRef) -> bool` (line 1015; internal) — Whether a record was written strictly before the cutoff attempt.
  - `_visible(self, entry: _Written, before: AttemptRef) -> bool` (line 1025; internal)
  - `_hypotheses_as_of(self, before: AttemptRef) -> list[HypothesisRecord]` (line 1030; internal) — Every hypothesis as it stood at ``before``.
  - `_observed_before(self, cold_attempt_id: str, written: datetime | None, before: AttemptRef) -> bool` (line 1059; internal) — A cold verification counts as of ``before`` only when it was recorded before it AND its cold attempt (when known) precedes it.
  - `_repair_as_of(self, entry: tuple[Any, ...], visible_hypotheses: Sequence[HypothesisRecord], before: AttemptRef) -> RepairRecord | None` (line 1068; internal)
  - `_earliest_source(self, error_event_ids: Sequence[str]) -> str | None` (line 1086; internal)
  - `_from_stored(self, row: Mapping[str, Any], item: PracticeItem | None, points: Mapping[str, float], events: Sequence[Mapping[str, Any]], fatal: Sequence[str], *, has_unassessed: bool=False, contract: Mapping[str, Any] | None=None) -> HistoryAttempt` (line 1096; internal) — A stored joint grade, reduced to blind-grade-equivalent fields (S3).
  - `attempt(self, attempt_id: str) -> HistoryAttempt | None` (line 1178; public)
  - `ref(self, attempt_id: str) -> AttemptRef | None` (line 1182; public)
  - `all_attempts(self) -> list[HistoryAttempt]` (line 1187; public)
  - `grading_marks(self) -> dict[str, str]` (line 1191; public) — Each attempt's grading identity as this store read it, in one snapshot with what it shows (``write_provenance.grading_marks``: the payload, the contract and the provenance): a record frozen later names every grading replaced since (diagnosis input provenance, codex review F3 and…
  - `attempts_before(self, before: AttemptRef, learning_object_ids: Sequence[str] | None=None) -> list[HistoryAttempt]` (line 1201; public)
  - `_source_before(self, source_attempt_id: str | None, before: AttemptRef) -> bool` (line 1213; internal)
  - `hypotheses_before(self, before: AttemptRef, learning_object_ids: Sequence[str]) -> list[HypothesisRecord]` (line 1219; public)
  - `registry_before(self, before: AttemptRef, learning_object_ids: Sequence[str] | None) -> list[RegistryRecord]` (line 1226; public)
  - `repairs_before(self, before: AttemptRef, facets: Iterable[str] | None) -> list[RepairRecord]` (line 1238; public)
  - `lagged_attempts(self, before: AttemptRef) -> int` (line 1251; public)
- `class StaticHistoryStore` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 1257) — An explicit history, e.g.
  - `__post_init__(self) -> None` (line 1265; internal)
  - `add(self, attempt: HistoryAttempt) -> None` (line 1269; public)
  - `replace_attempt(self, attempt: HistoryAttempt) -> None` (line 1273; public)
  - `attempt(self, attempt_id: str) -> HistoryAttempt | None` (line 1279; public)
  - `ref(self, attempt_id: str) -> AttemptRef | None` (line 1282; public)
  - `all_attempts(self) -> list[HistoryAttempt]` (line 1286; public)
  - `attempts_before(self, before: AttemptRef, learning_object_ids: Sequence[str] | None=None) -> list[HistoryAttempt]` (line 1289; public)
  - `_before(self, source: str | None, before: AttemptRef) -> bool` (line 1300; internal)
  - `hypotheses_before(self, before: AttemptRef, learning_object_ids: Sequence[str]) -> list[HypothesisRecord]` (line 1304; public)
  - `registry_before(self, before: AttemptRef, learning_object_ids: Sequence[str] | None) -> list[RegistryRecord]` (line 1314; public)
  - `repairs_before(self, before: AttemptRef, facets: Iterable[str] | None) -> list[RepairRecord]` (line 1325; public)
  - `lagged_attempts(self, before: AttemptRef) -> int` (line 1336; public)
- `with_blind_overlay(attempt: HistoryAttempt, **changes: Any) -> HistoryAttempt` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 1340)

### Module constants

- `NON_MEASURING_ATTEMPT_TYPES` ([src/learnloop/diagnosis/split/history.py](../../../../../../../src/learnloop/diagnosis/split/history.py), line 62)
- `ASSISTED_ATTEMPT_TYPES` ([src/learnloop/diagnosis/split/history.py](../../../../../../../src/learnloop/diagnosis/split/history.py), line 63)
- `_VALIDITY_FROM_JOINT` ([src/learnloop/diagnosis/split/history.py](../../../../../../../src/learnloop/diagnosis/split/history.py), line 69)
- `_HYPOTHESIS_LIFECYCLE` ([src/learnloop/diagnosis/split/history.py](../../../../../../../src/learnloop/diagnosis/split/history.py), line 75)
- `_FACTOR_LIFECYCLE` ([src/learnloop/diagnosis/split/history.py](../../../../../../../src/learnloop/diagnosis/split/history.py), line 82)
- `_MISCONCEPTION_LIFECYCLE` ([src/learnloop/diagnosis/split/history.py](../../../../../../../src/learnloop/diagnosis/split/history.py), line 83)

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

- `_instant(value: Any) -> datetime | None` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 417) — A stored timestamp as an aware UTC instant; unparseable -> None.
- `class _Written` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 429) — A history record with the instant it was written (F5, as of a cutoff).
- `_learner_text_candidate_ids(connection: Any, vault: LoadedVault) -> frozenset[str]` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 449) — Holding-pen candidates a learner's text named (learner-text gaps), while the pipeline and its sightings are switched on.
- `_decode_json(value: Any, default: Any) -> Any` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 467)
- `_max_points_by_criterion(vault: LoadedVault, item: PracticeItem | None) -> tuple[dict[str, float], float | None]` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 478)
- `_failed_facets(vault: LoadedVault, item: PracticeItem | None, failed: Sequence[str]) -> tuple[str, ...]` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 508)
- `_criterion_facet_sets(vault: LoadedVault, item: PracticeItem | None, criteria: Sequence[str]) -> tuple[tuple[str, ...], ...]` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 514) — Per criterion (in order), the facets it measures.
- `_attribution_alignment(vault: LoadedVault, item: PracticeItem | None, attributions: Sequence[Mapping[str, Any]]) -> tuple[tuple[tuple[str, ...], ...], tuple[tuple[str, ...], ...]]` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 522) — Per attribution: (facets it bears on, criteria it targets).
- `_target_facets_from(attribution: Mapping[str, Any], vault: LoadedVault) -> list[str]` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 543)
- `_quote_from(first_divergence: Any) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 554)
- `_with_confidence(record: HistoryAttempt, tap: Any, hedge: str | None, *, held: bool) -> HistoryAttempt` ([source](../../../../../../../src/learnloop/diagnosis/split/history.py), line 645) — TE0: the attempt with its tap and confidence event (unchanged with neither).

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
- [[Reference/Modules/learnloop/db/stores/write_provenance|learnloop.db.stores.write_provenance]] — imports `UNIDENTIFIED_GRADING`, `grading_marks`, `read_snapshot`, `replaced_error_event_attempts`; calls `grading_marks`, `read_snapshot`, `replaced_error_event_attempts`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `grade_held_for_review`; calls `grade_held_for_review`
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

- [tests/test_chatgpt_plan_workspace.py](../../../../../../../tests/test_chatgpt_plan_workspace.py) — direct import
- [tests/test_codex_lockdown_round3.py](../../../../../../../tests/test_codex_lockdown_round3.py) — direct import
  - `test_a_snapshot_diagnosis_on_codex_is_inlined_and_gives_the_same_structured_output`
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
- [tests/test_learner_blindness_relax.py](../../../../../../../tests/test_learner_blindness_relax.py) — direct import
- [tests/test_learner_text_gaps.py](../../../../../../../tests/test_learner_text_gaps.py) — direct import
  - `test_a_tutor_question_that_states_a_belief_reaches_the_holding_pen`
- [tests/test_pfc_unassessed_readers.py](../../../../../../../tests/test_pfc_unassessed_readers.py) — direct import
  - `test_a_later_diagnosis_cannot_cite_an_unassessed_shortfall_as_a_recurrence`
- [tests/test_required_method_round3_review.py](../../../../../../../tests/test_required_method_round3_review.py) — direct import
  - `test_f3_the_diagnosers_history_and_current_attempt_read_the_question_given`
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
