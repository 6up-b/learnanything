---
title: "learnloop.db.stores.attempts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/attempts.py"
source_paths:
  - "src/learnloop/db/stores/attempts.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.db.stores.attempts module"
  - "src/learnloop/db/stores/attempts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.attempts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.attempts` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Practice attempts, assessment contracts and cold-check receipts.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/attempts.py](../../../../../../../src/learnloop/db/stores/attempts.py) |
| Source lines | 2689 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class GradingEvidenceRecord` ([source](../../../../../../../src/learnloop/db/stores/attempts.py), line 62)
- `reserve_application_sequence(connection: Any, attempt_id: str, *, algorithm_version: str, recorded_at: str) -> int` ([source](../../../../../../../src/learnloop/db/stores/attempts.py), line 185) — The attempt's sequence: the next one, reserved now, or the one it already has.
- `rank_legacy_attempts(connection: Any, *, algorithm_version: str, recorded_at: str) -> int` ([source](../../../../../../../src/learnloop/db/stores/attempts.py), line 205) — Give every attempt without a sequence one, in the predecessor's ``(created_at, id)`` order, after every sequence that exists; how many were ranked.
- `record_legacy_lifecycle_inputs(connection: Any, inputs_by_attempt: Mapping[str, LifecycleInputs], *, recorded_at: str) -> int` ([source](../../../../../../../src/learnloop/db/stores/attempts.py), line 236) — Record the upgrade's reconstructed inputs for attempts that have no row, in attempt id order; how many.
- `class AttemptStoreMixin` ([source](../../../../../../../src/learnloop/db/stores/attempts.py), line 246)
  - `attempt_lifecycle_inputs(self, attempt_id: str) -> LifecycleInputs | None` (line 247; public) — The required facet set recorded for the attempt's grade application, or None.
  - `attempt_applied_at_version(self, attempt_id: str) -> str | None` (line 256; public) — The tag the attempt pipeline applied the attempt at (its application-order reservation), or None when it was ranked by an upgrade or never reserved one.
  - `insert_practice_attempt(self, attempt: Mapping[str, Any]) -> None` (line 267; public)
  - `fetch_practice_attempt(self, attempt_id: str) -> dict[str, Any] | None` (line 272; public)
  - `practice_attempt_by_submission_id(self, submission_id: str) -> dict[str, Any] | None` (line 280; public)
  - `attempt_submission_receipt(self, submission_id: str) -> dict[str, Any] | None` (line 288; public)
  - `insert_attempt_submission_receipt(self, *, submission_id: str, attempt_id: str, practice_item_id: str, result: Mapping[str, Any], clock: Clock | None=None) -> None` (line 300; public)
  - `upsert_attempt_feedback_metadata(self, *, attempt_id: str, grading_source: str, fallback_reason: str | None=None, agent_run_id: str | None=None, fatal_errors: list[str] | None=None, feedback_md: str | None=None, repair_suggestions: list[Mapping[str, Any]] | None=None, clock: Clock | None=None) -> None` (line 327; public)
  - `fetch_attempt_feedback_metadata(self, attempt_id: str) -> dict[str, Any] | None` (line 372; public) — The attempt's feedback metadata, as the causal consumers read it.
  - `raw_attempt_feedback_metadata(self, attempt_id: str) -> dict[str, Any] | None` (line 388; public) — The persisted feedback row exactly as written (no diagnosis overlay).
  - `record_feedback_shown(self, attempt_id: str, *, session_id: str | None=None, clock: Clock | None=None) -> bool` (line 398; public)
  - `attempts_with_feedback_shown_between(self, *, after: str, before: str) -> list[dict[str, Any]]` (line 422; public) — Attempts whose feedback screen was last opened inside the interval.
  - `list_recent_attempts_by_practice_item(self, practice_item_id: str, limit: int=10, *, until: str | None=None, before: tuple[str, str] | None=None, order: AttemptOrder=LEGACY_ORDER) -> list[dict[str, Any]]` (line 457; public) — The item's latest attempts, newest first.
  - `list_recent_attempts_by_learning_object(self, learning_object_id: str, limit: int=10, *, before: tuple[str, str] | None=None, order: AttemptOrder=LEGACY_ORDER) -> list[dict[str, Any]]` (line 523; public)
  - `list_recent_attempts_by_learning_objects(self, learning_object_ids: Iterable[str], *, limit: int=10, before: tuple[str, str] | None=None, order: AttemptOrder=LEGACY_ORDER) -> dict[str, list[dict[str, Any]]]` (line 535; public) — Load the latest ``limit`` attempts for each requested LO at once.
  - `list_attempts_by_learning_object(self, learning_object_id: str, *, order: AttemptOrder=LEGACY_ORDER) -> list[dict[str, Any]]` (line 602; public) — The learning object's attempts in the ledger's order (``order``): the order replay applies them in.
  - `learning_object_ids_with_attempts(self) -> list[str]` (line 619; public)
  - `list_attempt_history(self, *, order: AttemptOrder=LEGACY_ORDER) -> list[dict[str, Any]]` (line 630; public) — Every attempt (in the ledger's order, ``order``) with its posterior delta, if recorded.
  - `count_attempts_with_error_type(self, practice_item_id: str, error_type: str) -> int` (line 674; public) — Attempts on an item carrying ``error_type`` — the §12.4 promotion signal.
  - `insert_grading_evidence(self, attempt_id: str, evidence_rows: Iterable[Mapping[str, Any]]) -> None` (line 687; public)
  - `fetch_grading_evidence(self, attempt_id: str, *, include_superseded: bool=False) -> list[GradingEvidenceRecord]` (line 693; public)
  - `insert_grading_clarification(self, row: Mapping[str, Any], *, clock: Clock | None=None) -> str | None` (line 713; public) — Append one clarification request; None when the attempt already has one.
  - `grading_clarification_for_attempt(self, attempt_id: str) -> sqlite3.Row | None` (line 748; public)
  - `unanswered_grading_clarifications(self) -> list[sqlite3.Row]` (line 762; public)
  - `grading_clarifications_awaiting_regrade(self, *, limit: int | None=None) -> list[sqlite3.Row]` (line 776; public) — Clarifications whose answer landed but whose re-grade has not resolved.
  - `insert_grading_clarification_response(self, row: Mapping[str, Any], *, clock: Clock | None=None) -> str` (line 806; public)
  - `stamp_grading_clarification_outcome(self, clarification_id: str, *, outcome: str, resolved_grading_revision: int | None) -> None` (line 830; public) — Stamp the regrade result onto an already-recorded answer.
  - `attempts_pending_clarification_review(self) -> list[str]` (line 855; public) — Attempts whose grade advertises a pending clarification (Meas §3.A8).
  - `clarification_rate_counts(self) -> dict[str, int]` (line 868; public) — Counts for §3.A8's revert criterion.
  - `insert_trace_exercised_facets(self, attempt_id: str, rows: Iterable[Mapping[str, Any]], *, clock: Clock | None=None) -> int` (line 919; public) — Append A6 trace observations for one attempt; returns rows written.
  - `trace_exercised_facets(self, attempt_id: str) -> list[dict[str, Any]]` (line 969; public)
  - `all_trace_exercised_facets(self) -> dict[str, list[dict[str, Any]]]` (line 981; public) — Every A6 observation, grouped by attempt.
  - `list_grading_evidence_history(self, *, include_superseded: bool=False) -> list[GradingEvidenceRecord]` (line 997; public) — Every grading-evidence row in stable replay order.
  - `find_attempt_id_by_evidence_agent_run(self, *, practice_item_id: str, agent_run_id: str, attempt_type: str | None=None) -> str | None` (line 1019; public) — Latest attempt on an item whose grading evidence carries ``agent_run_id``.
  - `supersede_self_grade_rows(self, attempt_id: str, *, superseded_by_evidence_id: str, clock: Clock | None=None) -> int` (line 1053; public)
  - `is_score_only_exam_import(self, attempt_id: str) -> bool` (line 1073; public) — Whether the attempt is an exam import with no learner work to grade.
  - `pending_self_grade_regrade_attempts(self, limit: int | None=None) -> list[dict[str, Any]]` (line 1096; public)
  - `update_attempt_grade(self, attempt_id: str, *, rubric_score: int, correctness: float, grader_confidence: float, manual_review: bool, manual_review_reason: str | None, error_type: str | None, clock: Clock | None=None) -> bool` (line 1133; public)
  - `count_clean_attempts_since(self, learning_object_id: str, *, since: str, until: str, min_correctness: float, exclude_attempt_ids: Iterable[str]=()) -> int` (line 1173; public) — Count "clean" attempts on a learning object in ``(since, until]``.
  - `clean_attempt_ids_since(self, learning_object_id: str, *, since: str, until: str, min_correctness: float) -> list[str]` (line 1214; public) — The attempts :meth:`count_clean_attempts_since` would count.
  - `insert_attempt_surprise(self, surprise: Mapping[str, Any]) -> None` (line 1239; public)
  - `latest_attempt_surprise(self, attempt_id: str) -> dict[str, Any] | None` (line 1244; public)
  - `attempt_innovation_samples(self) -> list[dict[str, Any]]` (line 1252; public) — Per-attempt rows for the difficulty-miscalibration monitor (spec §7.4).
  - `attempt_surprise_gate_records(self, attempt_ids: Iterable[str] | None=None) -> dict[str, tuple[Any, Any, Any]]` (line 1275; public) — The follow-up gate's records on these attempts' surprise rows (every row with ``None``), as stored (``triggered_actions_json``, ``suppressed_actions_json``, ``gate_diagnostics_json``): what replay carries, since it never runs the gate.
  - `restore_attempt_surprise_gate_record(self, attempt_id: str, record: Sequence[Any]) -> bool` (line 1297; public) — Put a carried gate record back on the replayed surprise row, byte for byte.
  - `update_attempt_surprise_actions(self, attempt_id: str, *, triggered_actions: list[str] | None=None, suppressed_actions: list[str] | None=None, gate_diagnostics: Mapping[str, Any] | None=None) -> bool` (line 1310; public)
  - `record_attempt_outcome(self, *, attempt: Mapping[str, Any], evidence_rows: Iterable[Mapping[str, Any]], error_events: Iterable[Mapping[str, Any]], surprise: Mapping[str, Any], practice_item_state: PracticeItemState, mastery_state: MasteryState, facet_uncertainty_states: Iterable[Mapping[str, Any]]=(), quality_state: Mapping[str, Any] | None=None, ability_transition: Mapping[str, Any] | None=None, attempt_debug_payload: Mapping[str, Any] | None=None, item_parameter_state: ItemParameterState | None=None, lifecycle_inputs: LifecycleInputs | None=None, mastery_seed_inputs: MasterySeedInputs | None=None) -> None` (line 1340; public) — The live attempt's write.
  - `insert_regrade_evidence(self, *, attempt_id: str, new_evidence_rows: Iterable[Mapping[str, Any]], superseded_by_evidence_id: str, supersede_tiers: tuple[int, ...]=(1,), clock: Clock | None=None) -> None` (line 1419; public)
  - `attempt_debug_payload(self, attempt_id: str) -> dict[str, Any] | None` (line 1448; public)
  - `learning_outcome_labels_for_source(self, attempt_id: str) -> list[dict[str, Any]]` (line 1456; public)
  - `list_all_attempts(self) -> list[dict[str, Any]]` (line 1468; public) — Every practice attempt ordered for per-item replay (fitting jobs).
  - `attempt_count_for_learning_objects(self, learning_object_ids: list[str]) -> int` (line 1477; public)
  - `daily_qualifying_attempt_counts_for_learning_objects(self, learning_object_ids: list[str], *, days: int=14, not_before: str | None=None, clock: Clock | None=None) -> dict[date, int]` (line 1488; public) — Zero-filled, goal-scoped certification-capable attempts by local day.
  - `practice_attempt_outcomes_for_items(self, item_ids: list[str]) -> list[dict[str, Any]]` (line 1549; public) — Time-ordered attempt outcomes for a set of practice items.
  - `grading_correction_count_between(self, started_at: str, ended_at: str) -> int` (line 1582; public) — Count grading epochs after the original grade in a time window.
  - `attempt_count(self) -> int` (line 1610; public) — Every attempt ever served — the "questions served" denominator.
  - `ensure_assessment_contract_version(self, *, practice_item_id: str, contract_hash: str, contract_json: str, schema_version: int, clock: Clock | None=None) -> str` (line 1624; public) — Content-addressed assessment-contract snapshot (§5.2), idempotent.
  - `fetch_assessment_contract_version(self, version_id: str) -> dict[str, Any] | None` (line 1671; public)
  - `fetch_assessment_contract_versions(self, version_ids: Iterable[str]) -> dict[str, dict[str, Any]]` (line 1683; public) — Bulk-load content-addressed assessment contracts by id.
  - `assessment_contract_versions_for_practice_item(self, practice_item_id: str) -> list[dict[str, Any]]` (line 1704; public) — Immutable contract snapshots ever presented for one PracticeItem.
  - `append_measurement_contract_corrections(self, *, correction_set_id: str, source_practice_item_id: str, source_contract_version_ids: Iterable[str], corrected_practice_item_id: str, corrected_contract_version_id: str, consuming_projection_version: str, historical_evidence_policy: str, reason: str, correction: Mapping[str, Any] | None=None, clock: Clock | None=None) -> list[str]` (line 1725; public) — Append one immutable correction edge per historical contract version.
  - `measurement_contract_corrections(self, *, source_practice_item_id: str | None=None, correction_set_id: str | None=None) -> list[dict[str, Any]]` (line 1785; public)
  - `effective_assessment_contract_version(self, source_version_id: str, *, projection_version: str) -> dict[str, Any] | None` (line 1812; public) — Resolve the contract a named projection is authorized to consume.
  - `effective_assessment_contract_versions(self, source_version_ids: Iterable[str], *, projection_version: str) -> dict[str, dict[str, Any]]` (line 1845; public) — Bulk form of :meth:`effective_assessment_contract_version`.
  - `superseded_measurement_item_ids(self) -> set[str]` (line 1868; public) — Attempted item files superseded by an accepted correction set.
  - `list_all_assessment_contract_versions(self) -> list[dict[str, Any]]` (line 1880; public)
  - `insert_causal_cold_verification(self, *, verification_id: str, source_attempt_id: str, cold_attempt_id: str, repair_class_id: str, hypothesis_ids: Sequence[str], source_surface_family: str, cold_surface_family: str, avoided_affordances: Sequence[str], success: bool, capability_update: Mapping[str, Any], diagnosis_support_update: Mapping[str, Any], repair_effect_support: Mapping[str, Any], clock: Clock | None=None) -> dict[str, Any]` (line 1887; public)
  - `causal_cold_verification_for_attempt(self, cold_attempt_id: str) -> dict[str, Any] | None` (line 1954; public)
  - `insert_causal_cold_outcome(self, *, outcome_id: str, outcome: str, followup_task_id: str | None, remediation_episode_id: str | None, case_kind: str | None, case_ref: str | None, source_attempt_id: str | None, cold_attempt_id: str | None, repair_class_id: str | None, hypothesis_ids: Sequence[str], cold_verification_id: str | None, servable_opportunity: bool, duration_state: str | None, detail: Mapping[str, Any], store_version: str, scheduled_not_before: str | None, scheduled_expires_at: str | None, clock: Clock | None=None) -> dict[str, Any] | None` (line 1985; public)
  - `_decode_causal_cold_outcome(row: Any) -> dict[str, Any]` (line 2045; internal)
  - `causal_cold_outcome(self, outcome_id: str) -> dict[str, Any] | None` (line 2052; public)
  - `causal_cold_outcome_for_task(self, followup_task_id: str) -> dict[str, Any] | None` (line 2060; public)
  - `causal_cold_outcomes(self, *, outcome: str | None=None, remediation_episode_id: str | None=None) -> list[dict[str, Any]]` (line 2070; public)
  - `insert_coldness_receipt(self, *, receipt_id: str, lane: str, stage: str, measurement_opportunity_id: str | None=None, followup_task_id: str | None, remediation_episode_id: str | None, source_attempt_id: str | None, cold_attempt_id: str | None, cold_verification_id: str | None, dimensions: Mapping[str, Any], derived: Mapping[str, Any], telemetry_coverage: Mapping[str, Any], receipt_version: str, clock: Clock | None=None) -> dict[str, Any] | None` (line 2099; public)
  - `_decode_coldness_receipt(row: Any) -> dict[str, Any]` (line 2158; internal)
  - `coldness_receipt(self, receipt_id: str) -> dict[str, Any] | None` (line 2167; public)
  - `coldness_receipt_for_task_stage(self, followup_task_id: str, stage: str) -> dict[str, Any] | None` (line 2174; public)
  - `coldness_receipt_for_opportunity_stage(self, measurement_opportunity_id: str, stage: str) -> dict[str, Any] | None` (line 2187; public)
  - `coldness_receipts_for_task(self, followup_task_id: str) -> list[dict[str, Any]]` (line 2200; public)
  - `coldness_receipt_for_verification(self, cold_verification_id: str) -> dict[str, Any] | None` (line 2214; public)
  - `practice_attempts_between(self, *, after: str | None, before: str | None) -> list[dict[str, Any]]` (line 2224; public) — Attempts in an open interval, oldest first — the exposure-scan read.
  - `practice_attempts_for_items_before(self, practice_item_ids: Sequence[str], *, before: str) -> list[dict[str, Any]]` (line 2254; public) — Prior administrations for a bounded candidate surface family.
  - `insert_certification_cold_probe_outcome(self, *, outcome_id: str, certificate_id: str, learning_object_id: str, blueprint_id: str, recipe_id: str, certificate_receipt: Mapping[str, Any], certified_at: str | None, followup_task_id: str, scheduled_not_before: str, scheduled_expires_at: str | None, horizon_days: float, window_days: float, probe_practice_item_id: str, probe_attempt_id: str, probe_surface_group: str, excluded_surface_groups: Sequence[str], held_out_basis: str, avoided_affordances: Sequence[str], verdict: str, indeterminate_reason: str | None, success: bool | None, correctness: float | None, success_threshold: float, assisted: bool, certificate_state_at_probe: str, store_version: str, policy_version: str, certification_algorithm_version: str | None, parameters: Mapping[str, Any], grading_source: str | None=None, grading_prompt_version: str | None=None, grader_model: str | None=None, grader_provider: str | None=None, grader_provider_revision: str | None=None, grading_agent_run_id: str | None=None, clock: Clock | None=None) -> dict[str, Any] | None` (line 2289; public)
  - `certification_cold_probe_outcome_for_attempt(self, probe_attempt_id: str) -> dict[str, Any] | None` (line 2392; public)
  - `certification_cold_probe_outcomes(self) -> list[dict[str, Any]]` (line 2405; public)
  - `_insert_grading_evidence(self, connection: sqlite3.Connection, attempt_id: str, row: Mapping[str, Any]) -> None` (line 2415; internal)
  - `_insert_attempt_surprise(self, connection: sqlite3.Connection, surprise: Mapping[str, Any]) -> None` (line 2457; internal)
  - `_insert_learning_outcome_labels(self, connection: sqlite3.Connection, attempt: Mapping[str, Any], *, algorithm_version: str, max_sources: int=20) -> None` (line 2487; internal)
  - `attempted_practice_item_ids(self) -> set[str]` (line 2581; public) — Practice item ids that have at least one recorded attempt.
  - `_grading_epoch_transitions(self, rows: list[sqlite3.Row]) -> dict[str, list[dict[str, Any]]]` (line 2599; internal) — Group ordered ``grading_evidence`` rows into per-attempt epochs and return, per attempt, the ordered old→new transitions (each grading epoch after the first).
  - `regrade_epoch_transitions(self) -> list[dict[str, Any]]` (line 2645; public) — Every post-original grading epoch across all attempts, as an old→new transition with the attempt's item/LO references and the epoch time.
  - `attempt_regrade_marker(self, attempt_id: str) -> dict[str, Any] | None` (line 2668; public) — The most recent regrade (old→new score) persisted for one attempt, or ``None`` when the attempt has only its original grading epoch.

### Module constants

- `PYTHON_WHITESPACE_CODE_POINTS` ([src/learnloop/db/stores/attempts.py](../../../../../../../src/learnloop/db/stores/attempts.py), line 46)
- `_PYTHON_WHITESPACE_SQL` ([src/learnloop/db/stores/attempts.py](../../../../../../../src/learnloop/db/stores/attempts.py), line 51)
- `_EXAM_IMPORT_HAS_WORK` ([src/learnloop/db/stores/attempts.py](../../../../../../../src/learnloop/db/stores/attempts.py), line 54)

## Internal implementation anchors

- `_required_observation_scope(row: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/db/stores/attempts.py), line 87) — An A6 observation's scope, which the caller must state (Meas §3.A6).
- `_grading_evidence(row: sqlite3.Row) -> GradingEvidenceRecord` ([source](../../../../../../../src/learnloop/db/stores/attempts.py), line 99)
- `_decode_certification_cold_probe_outcome(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/attempts.py), line 131)
- `_decode_attempt_feedback_metadata(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/attempts.py), line 148)
- `_elapsed_seconds_between(start: str | None, end: str | None) -> int | None` ([source](../../../../../../../src/learnloop/db/stores/attempts.py), line 155)
- `_attempt_label_snapshot(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/attempts.py), line 163)
- `_insert_attempt_lifecycle_inputs(connection: Any, attempt_id: str, inputs: LifecycleInputs, *, recorded_at: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/attempts.py), line 223)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `GradingEvidenceRecord`, `reserve_application_sequence`; statically calls `reserve_application_sequence`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `AttemptStoreMixin`
- [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]] — imports `GradingEvidenceRecord`
- [[Reference/Modules/learnloop/ops/upgrades|learnloop.ops.upgrades]] — imports `rank_legacy_attempts`, `record_legacy_lifecycle_inputs`; statically calls `rank_legacy_attempts`, `record_legacy_lifecycle_inputs`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `GradingEvidenceRecord`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`, `utc_now_iso`; calls `SystemClock`, `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/attempt_lifecycle_inputs|learnloop.db.attempt_lifecycle_inputs]] — imports `LIFECYCLE_INPUTS_TABLE`, `LifecycleInputs`
- [[Reference/Modules/learnloop/db/attempt_order|learnloop.db.attempt_order]] — imports `APPLICATION_ORDER_TABLE`, `AttemptOrder`, `BASIS_APPLIED`, `BASIS_LEGACY_ORDER_UNKNOWN`, `LEGACY_ORDER`
- [[Reference/Modules/learnloop/db/mastery_seed_inputs|learnloop.db.mastery_seed_inputs]] — imports `MasterySeedInputs`
- [[Reference/Modules/learnloop/db/records|learnloop.db.records]] — imports `ItemParameterState`, `MasteryState`, `PracticeItemState`, `_decode_attempt`, `_decode_learning_outcome_label`, `_decode_surprise`, `_projection_id`; calls `_decode_attempt`, `_decode_learning_outcome_label`, `_decode_surprise`, `_projection_id`
- [[Reference/Modules/learnloop/db/row_serialization|learnloop.db.row_serialization]] — imports `_json`, `_loads`; calls `_json`, `_loads`
- [[Reference/Modules/learnloop/db/stores/diagnoses|learnloop.db.stores.diagnoses]] — imports `merge_causal_view_into_feedback`; calls `merge_causal_view_into_feedback`
- [[Reference/Modules/learnloop/db/stores/grade_curves|learnloop.db.stores.grade_curves]] — imports `capture_grade_curve`; calls `capture_grade_curve`
- [[Reference/Modules/learnloop/db/stores/observation_ledger|learnloop.db.stores.observation_ledger]] — imports `load_effective_assessment_contracts`; calls `load_effective_assessment_contracts`
- [[Reference/Modules/learnloop/db/stores/practice_state|learnloop.db.stores.practice_state]] — imports `insert_mastery_seed_inputs`; calls `insert_mastery_seed_inputs`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `LABEL_VERSION`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]], [[Reference/Modules/learnloop/ops/upgrades|learnloop.ops.upgrades]], [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_attempt_order.py](../../../../../../../tests/test_attempt_order.py) — direct import
  - `test_a_reservation_is_the_next_sequence_and_a_second_one_returns_it`
  - `test_ranking_legacy_attempts_fills_only_the_unbound_in_the_predecessor_order_after_every_sequence`
- [tests/test_deferred_regrade.py](../../../../../../../tests/test_deferred_regrade.py) — direct import
  - `test_the_legacy_whitespace_rule_is_pythons`
- [tests/test_p0_projection_cutover.py](../../../../../../../tests/test_p0_projection_cutover.py) — direct import
  - `test_grading_evidence_write_discipline_is_append_only_with_supersession`
- [tests/test_same_second_order.py](../../../../../../../tests/test_same_second_order.py) — direct import
  - `test_a_rolled_back_application_leaves_no_reservation_and_its_retry_takes_the_next`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/attempts.py](../../../../../../../src/learnloop/db/stores/attempts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
