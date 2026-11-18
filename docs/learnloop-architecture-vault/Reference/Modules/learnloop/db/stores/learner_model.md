---
title: "learnloop.db.stores.learner_model"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/learner_model.py"
source_paths:
  - "src/learnloop/db/stores/learner_model.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.stores.learner_model module"
  - "src/learnloop/db/stores/learner_model.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.learner_model`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.learner_model` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Learner-model evidence, misconceptions and intervention needs.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/learner_model.py](../../../../../../../src/learnloop/db/stores/learner_model.py) |
| Source lines | 1857 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class ActiveErrorEvent` ([source](../../../../../../../src/learnloop/db/stores/learner_model.py), line 27)
- `class MisconceptionRecord` ([source](../../../../../../../src/learnloop/db/stores/learner_model.py), line 42) — A normalized, content-bearing belief scoped to a learning object.
- `class ItemMisconceptionDiscrimination` ([source](../../../../../../../src/learnloop/db/stores/learner_model.py), line 80) — Estimated discrimination of an item's keyed fatal error vs a misconception.
  - `sensitivity_mean(self) -> float` (line 101; public)
  - `specificity_mean(self) -> float` (line 105; public)
  - `sensitivity_lb(self, q: float=0.25) -> float` (line 108; public)
  - `specificity_lb(self, q: float=0.25) -> float` (line 111; public)
  - `youden_j(self) -> float` (line 115; public) — Discrimination power J = E[sens] + E[spec] - 1.
  - `youden_j_lb(self, q: float=0.25) -> float` (line 119; public) — Conservative J from the sensitivity/specificity lower bounds.
- `class LearnerModelStoreMixin` ([source](../../../../../../../src/learnloop/db/stores/learner_model.py), line 206)
  - `active_error_events(self) -> list[ActiveErrorEvent]` (line 208; public)
  - `active_errors_by_learning_object(self, learning_object_id: str) -> list[ActiveErrorEvent]` (line 215; public) — The LO's active error events exactly as stored (no diagnosis overlay).
  - `active_errors_by_learning_object_overlaid(self, learning_object_id: str) -> list[ActiveErrorEvent]` (line 227; public) — The LO's active error events as the diagnosis overlay shows them.
  - `active_error_events_overlaid(self) -> list[ActiveErrorEvent]` (line 257; public) — Every active error event as the diagnosis overlay shows it.
  - `_active_error_rows(self, learning_object_id: str) -> list[sqlite3.Row]` (line 285; internal)
  - `error_events_for_attempt(self, attempt_id: str) -> list[dict[str, Any]]` (line 296; public) — The attempt's error events, as the causal consumers read them.
  - `raw_error_events_for_attempt(self, attempt_id: str) -> list[dict[str, Any]]` (line 316; public) — The persisted error-event rows exactly as written (no overlay).
  - `all_error_events_by_attempt(self) -> dict[str, list[dict[str, Any]]]` (line 330; public) — Decode the complete error-event ledger in one ordered scan.
  - `attempt_ids_for_misconception(self, misconception_id: str, *, event_ids: Sequence[str]=(), limit: int=5) -> list[str]` (line 358; public) — Attempt ids whose error events minted/fed this misconception, newest first.
  - `insert_error_event(self, event: Mapping[str, Any]) -> None` (line 395; public)
  - `set_error_event_misconception(self, event_id: str, misconception_id: str | None, *, clock: Clock | None=None) -> bool` (line 400; public) — Link (or unlink) an error event to a normalized registry belief.
  - `insert_misconception(self, *, learning_object_id: str, statement: str, id: str | None=None, concept_id: str | None=None, signature: str | None=None, facet_ids: Iterable[str] | None=None, severity: float=0.0, status: str='active', source_error_event_ids: Iterable[str] | None=None, mechanism: str | None=None, operation: str | None=None, target_facet: str | None=None, confused_with_facet: str | None=None, trigger_conditions: Iterable[str] | None=None, expected_signatures: Iterable[str] | None=None, first_divergence: Iterable[str] | None=None, non_applicable_controls: Iterable[str] | None=None, promotion_reason: str | None=None, correction_statement: str | None=None, correction_source_span_ids: Iterable[str] | None=None, provenance: Any=None, correction_provenance: Any=None, provenance_writer: str='misconception', clock: Clock | None=None) -> str` (line 420; public) — Insert a registry belief.
  - `misconception(self, misconception_id: str) -> MisconceptionRecord | None` (line 516; public)
  - `misconceptions_for_learning_object(self, learning_object_id: str, statuses: Iterable[str]=('active', 'resolving')) -> list[MisconceptionRecord]` (line 534; public)
  - `misconceptions_for_concepts(self, concept_ids: Iterable[str], statuses: Iterable[str]=('active', 'resolving')) -> list[MisconceptionRecord]` (line 566; public)
  - `update_misconception(self, misconception_id: str, *, statement: str | None=None, signature: str | None=None, facet_ids: Iterable[str] | None=None, severity: float | None=None, status: str | None=None, append_source_error_event_ids: Iterable[str] | None=None, correction_statement: str | None=None, correction_source_span_ids: Iterable[str] | None=None, transition_source: str='repository', statement_provenance: Any=None, correction_provenance: Any=None, clock: Clock | None=None) -> MisconceptionRecord | None` (line 602; public)
  - `misconception_transition_events(self, misconception_id: str) -> list[dict[str, Any]]` (line 708; public)
  - `insert_misconception_candidate(self, *, learning_object_id: str, statement: str, statement_normalized: str, id: str | None=None, concept_id: str | None=None, signature: str | None=None, mechanism: str | None=None, operation: str | None=None, target_facet: str | None=None, confused_with_facet: str | None=None, facet_ids: Iterable[str] | None=None, source_error_event_ids: Iterable[str] | None=None, surface_families: Iterable[str] | None=None, item_ids: Iterable[str] | None=None, occurrence_count: int=1, severity: float=0.0, provenance: Any=None, provenance_writer: str='misconception_candidate', clock: Clock | None=None) -> str` (line 719; public) — Insert a holding-pen candidate.
  - `misconception_candidate_by_id(self, candidate_id: str) -> dict[str, Any] | None` (line 785; public)
  - `upsert_item_misconception_discrimination(self, row: ItemMisconceptionDiscrimination, *, clock: Clock | None=None) -> None` (line 807; public)
  - `discrimination_row(self, practice_item_id: str, misconception_id: str) -> ItemMisconceptionDiscrimination | None` (line 849; public)
  - `resolve_error_event(self, event_id: str, *, clock: Clock | None=None) -> bool` (line 862; public)
  - `pending_gap_need_for_facets(self, facet_ids: Iterable[str]) -> dict[str, Any] | None` (line 876; public) — A pending tutor-gap need already targeting any of ``facet_ids``.
  - `append_attempt_diagnosis_receipt(self, attempt_id: str, receipt: Mapping[str, Any]) -> dict[str, Any]` (line 901; public) — Append one immutable P1 decision snapshot to the attempt payload.
  - `recent_surprise_signals(self, *, limit: int=200, exclude_attempt_id: str | None=None) -> list[dict[str, Any]]` (line 970; public) — Most recent attempt_surprise signal rows for quantile-threshold resolution (newest first).
  - `upsert_intervention_need(self, need: Mapping[str, Any]) -> str` (line 998; public)
  - `pending_intervention_needs(self, learning_object_id: str | None=None) -> list[dict[str, Any]]` (line 1074; public)
  - `intervention_need(self, need_id: str) -> dict[str, Any] | None` (line 1091; public)
  - `update_intervention_need_diagnostic_focus(self, need_id: str, diagnostic_focus: dict[str, Any] | None, *, clock: Clock | None=None) -> bool` (line 1099; public) — Replace a need's diagnostic_focus snapshot in place (spec §6 reopen).
  - `intervention_need_for_attempt(self, attempt_id: str) -> dict[str, Any] | None` (line 1125; public)
  - `update_intervention_need_status(self, need_id: str, *, status: str, blocked_reason: str | None=None, clock: Clock | None=None) -> bool` (line 1138; public)
  - `append_intervention_need_target_facets(self, need_id: str, facets: list[str], *, clock: Clock | None=None) -> bool` (line 1163; public) — Union extra facets into an existing need's target_facets in place.
  - `intervention_needs_for_diagnostic_proposal(self, patch_id: str) -> list[dict[str, Any]]` (line 1195; public)
  - `upsert_state_belief(self, *, scope_type: str, scope_id: str, belief_key: str, mean: float, variance: float, evidence_count: int, algorithm_version: str, subject: str | None=None, last_surprise: float | None=None, last_evidence_at: str | None=None, stale_after_days: int | None=None, clock: Clock | None=None) -> str` (line 1209; public) — Insert or update a `learner_state_beliefs` row.
  - `state_beliefs(self, *, subject: str | None=None, scope_type: str | None=None, scope_id: str | None=None, belief_key: str | None=None) -> list[dict[str, Any]]` (line 1294; public)
  - `all_scheduler_slates(self) -> list[dict[str, Any]]` (line 1321; public) — Every scheduler slate in chronological order (for shadow reports).
  - `misconception_transition_counts_between(self, started_at: str, ended_at: str) -> dict[str, int]` (line 1330; public)
  - `insert_hypothesis_event(self, *, event_type: str, claim_class: str, claim_type: str, claim_ref: str, claim_version: str, producer_version: str, surface: str, temperature: str, presentation_id: str | None=None, visible_at: str | None=None, suppression_reason: str | None=None, response_payload: Mapping[str, Any] | None=None, session_id: str | None=None, visit_id: str | None=None, claim_text: str | None=None, belief_kind: str | None=None, belief_id: str | None=None, surfaced_to_learner: bool=False, id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` (line 1353; public)
  - `hypothesis_event(self, event_id: str) -> dict[str, Any] | None` (line 1420; public)
  - `find_hypothesis_presentation(self, *, claim_ref: str, claim_version: str, surface: str, session_id: str | None, visit_id: str | None) -> dict[str, Any] | None` (line 1427; public)
  - `mark_hypothesis_visible(self, presentation_id: str, visible_at: str, *, claim_text: str | None=None, belief_kind: str | None=None, belief_id: str | None=None) -> dict[str, Any] | None` (line 1451; public) — Patch actual viewport exposure onto a debounced presentation.
  - `soliciting_hypothesis_count(self, *, session_id: str | None=None, visit_id: str | None=None) -> int` (line 1497; public)
  - `cold_hypothesis_count_for_visit(self, visit_id: str) -> int` (line 1516; public)
  - `last_hypothesis_response_at(self, claim_ref: str, claim_version: str) -> str | None` (line 1528; public)
  - `list_hypothesis_events(self) -> list[dict[str, Any]]` (line 1541; public)
  - `purge_hypothesis_events(self) -> int` (line 1548; public)
  - `record_surfaced_belief_presentation(self, *, id: str, belief_kind: str, belief_id: str, claim_text: str, surface: str, claim_class: str='diagnosis', claim_type: str='misconception', claim_version: str='surfaced-1', producer_version: str='surfaced_beliefs', clock: Clock | None=None) -> str` (line 1558; public) — Record a belief shown on a surface that does NOT dispatch claims.
  - `insert_misconception_disposition(self, *, misconception_id: str, disposition: str, reason: str, replacement_misconception_id: str | None=None, id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` (line 1621; public) — Append one demotion/supersession to the append-only lifecycle stream.
  - `misconception_dispositions(self, misconception_id: str | None=None) -> list[dict[str, Any]]` (line 1668; public)
  - `surfaced_beliefs(self) -> list[dict[str, Any]]` (line 1690; public) — Distinct beliefs the learner was actually SHOWN (migration 132).
  - `surfaced_belief_withdrawals(self) -> list[dict[str, Any]]` (line 1721; public) — The A6 join: dispositions on beliefs the learner was actually SHOWN.
  - `_insert_error_event(self, connection: sqlite3.Connection, event: Mapping[str, Any]) -> None` (line 1797; internal)
  - `golden_path_runs_all(self) -> list[dict[str, Any]]` (line 1824; public)
  - `discrimination_profile_match_rows(self, *, since: str | None=None) -> list[dict[str, Any]]` (line 1831; public) — Every recorded A5 judgement, oldest first.
  - `diagnostic_augmentation_receipt_rows(self) -> list[dict[str, Any]]` (line 1849; public)

## Internal implementation anchors

- `_active_error(row: sqlite3.Row | Mapping[str, Any]) -> ActiveErrorEvent` ([source](../../../../../../../src/learnloop/db/stores/learner_model.py), line 124) — An :class:`ActiveErrorEvent` from a stored row or a decoded (overlaid) one.
- `_decode_hypothesis_event(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/learner_model.py), line 141)
- `_decode_misconception(row: sqlite3.Row) -> MisconceptionRecord` ([source](../../../../../../../src/learnloop/db/stores/learner_model.py), line 147)
- `_row_opt(row: sqlite3.Row, key: str) -> Any` ([source](../../../../../../../src/learnloop/db/stores/learner_model.py), line 179) — Row value for ``key`` or ``None`` when the column is absent.
- `_decode_discrimination(row: sqlite3.Row) -> ItemMisconceptionDiscrimination` ([source](../../../../../../../src/learnloop/db/stores/learner_model.py), line 191)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `ActiveErrorEvent`
- [[Reference/Modules/learnloop/attempts/surprise|learnloop.attempts.surprise]] — imports `ActiveErrorEvent`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `MisconceptionRecord`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `LearnerModelStoreMixin`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_gate|learnloop.diagnosis.diagnostic_gate]] — imports `ItemMisconceptionDiscrimination`, `MisconceptionRecord`; statically calls `ItemMisconceptionDiscrimination`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `MisconceptionRecord`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `MisconceptionRecord`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `ActiveErrorEvent`, `ItemMisconceptionDiscrimination`, `MisconceptionRecord`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `ActiveErrorEvent`
- [[Reference/Modules/learnloop/scheduling/selection_rewards|learnloop.scheduling.selection_rewards]] — imports `ActiveErrorEvent`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/records|learnloop.db.records]] — imports `_decode_error_event`, `_decode_intervention_need`, `_decode_misconception_candidate`, `_decode_scheduler_slate`; calls `_decode_error_event`, `_decode_intervention_need`, `_decode_misconception_candidate`, `_decode_scheduler_slate`
- [[Reference/Modules/learnloop/db/row_serialization|learnloop.db.row_serialization]] — imports `_json`, `_loads`; calls `_json`, `_loads`
- [[Reference/Modules/learnloop/db/stores/diagnoses|learnloop.db.stores.diagnoses]] — imports `merge_causal_view_into_events`; calls `merge_causal_view_into_events`
- [[Reference/Modules/learnloop/db/stores/grading|learnloop.db.stores.grading]] — imports `_decode_diagnostic_augmentation_receipt`; calls `_decode_diagnostic_augmentation_receipt`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/numeric|learnloop.numeric]] — imports `beta_mean`, `beta_quantile`; calls `beta_mean`, `beta_quantile`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/surprise|learnloop.attempts.surprise]], [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]], [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/diagnosis/diagnostic_gate|learnloop.diagnosis.diagnostic_gate]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_cold_start_revision.py](../../../../../../../tests/test_cold_start_revision.py) — direct import
  - `test_scheduler_excludes_assessment_side_errors`
- [tests/test_diagnostic_gate.py](../../../../../../../tests/test_diagnostic_gate.py) — direct import
- [tests/test_misconception_registry.py](../../../../../../../tests/test_misconception_registry.py) — direct import
- [tests/test_misconception_routing.py](../../../../../../../tests/test_misconception_routing.py) — direct import
  - `test_active_mc_with_discriminator_queues_it`
- [tests/test_repositories.py](../../../../../../../tests/test_repositories.py) — direct import
  - `test_item_misconception_discrimination_upsert_and_math`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/learner_model.py](../../../../../../../src/learnloop/db/stores/learner_model.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
