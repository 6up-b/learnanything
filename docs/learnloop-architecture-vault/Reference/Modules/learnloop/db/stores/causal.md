---
title: "learnloop.db.stores.causal"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/causal.py"
source_paths:
  - "src/learnloop/db/stores/causal.py"
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
  - "learnloop.db.stores.causal module"
  - "src/learnloop/db/stores/causal.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.causal`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.causal` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Causal hypotheses, evidence and probe decisions.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/causal.py](../../../../../../../src/learnloop/db/stores/causal.py) |
| Source lines | 2841 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class CausalStoreMixin` ([source](../../../../../../../src/learnloop/db/stores/causal.py), line 124)
  - `latest_causal_hypothesis_for_episode(self, episode_key: str) -> dict[str, Any] | None` (line 128; public)
  - `append_causal_hypothesis(self, *, episode_key: str, attempt_id: str, learning_object_id: str, cause_scope: str, statement: str, statement_normalized: str, error_event_id: str | None=None, mechanism: str | None=None, operation: str | None=None, target_ref: Mapping[str, Any] | None=None, applicability: Mapping[str, Any] | None=None, postdictive_claims: Sequence[Mapping[str, Any]]=(), evidence: Mapping[str, Any] | None=None, repair_class_id: str | None=None, repair_class_basis: str | None=None, repair_class_unresolved_reason: str | None=None, status: str='candidate', generation_agent_run_id: str | None=None, model: str | None=None, hypothesis_id: str | None=None, provenance: Any=None, provenance_writer: str='causal_hypothesis', clock: Clock | None=None, replayed_from: Sequence[str] | None=None) -> dict[str, Any]` (line 143; public) — Append a changed hypothesis version, or return the identical head.
  - `causal_hypothesis_versions(self, episode_key: str) -> list[dict[str, Any]]` (line 308; public) — Every version of one episode, oldest first.
  - `causal_hypothesis(self, hypothesis_id: str) -> dict[str, Any] | None` (line 318; public)
  - `causal_hypotheses_for_attempt(self, attempt_id: str, *, latest_only: bool=True) -> list[dict[str, Any]]` (line 326; public)
  - `all_causal_hypotheses(self, *, latest_only: bool=True) -> list[dict[str, Any]]` (line 354; public) — Return causal-hypothesis rows across episodes in stable order.
  - `causal_hypotheses_with_statement(self, statement_normalized: str, *, statuses: Sequence[str]=('candidate', 'validated'), cause_scope: str | None='learner_state') -> list[dict[str, Any]]` (line 386; public) — Episode heads, vault-wide, of one exact statement class (Slice 2 T1).
  - `causal_hypotheses_with_operations(self, *, latest_only: bool=True, require_operation: bool=True) -> list[dict[str, Any]]` (line 424; public) — Hypothesis heads for taxonomy minting.
  - `insert_missing_vocabulary_notes(self, notes: Sequence[Mapping[str, Any]], *, clock: Clock | None=None) -> int` (line 460; public) — Append missing-vocabulary notes (migration 134, Aug A5).
  - `missing_vocabulary_notes(self, *, source: str | None=None, learning_object_id: str | None=None, limit: int | None=None) -> list[dict[str, Any]]` (line 518; public)
  - `record_causal_repair_class_definitions(self, definitions: Sequence[Mapping[str, Any]], *, clock: Clock | None=None) -> int` (line 554; public) — Persist repair-class definitions durably (migration 133, Aug A2).
  - `causal_repair_class_definitions(self, repair_class_ids: Sequence[str] | None=None) -> dict[str, dict[str, Any]]` (line 603; public) — Durable repair-class definitions keyed by ``repair_class_id``.
  - `retired_causal_mechanism_taxonomy_versions(self) -> dict[str, dict[str, Any]]` (line 630; public) — Taxonomy versions withdrawn from new receipts, keyed by version id.
  - `retire_causal_mechanism_taxonomy_version(self, taxonomy_version_id: str, *, reason: str, clock: Clock | None=None) -> bool` (line 642; public) — Withdraw a taxonomy version from NEW receipts (migration 133).
  - `insert_causal_mechanism_taxonomy_version(self, *, taxonomy_version_id: str, algorithm: str, min_cluster_size: int, source_head_hash: str, status: str, taxonomy: Mapping[str, Any], assignments: Sequence[Mapping[str, str]], clock: Clock | None=None) -> dict[str, Any]` (line 671; public) — Insert an immutable taxonomy snapshot and its hypothesis assignments.
  - `causal_mechanism_taxonomy_version(self, taxonomy_version_id: str, *, include_assignments: bool=False) -> dict[str, Any] | None` (line 752; public)
  - `latest_active_causal_mechanism_taxonomy(self) -> dict[str, Any] | None` (line 784; public) — The taxonomy a NEW receipt may adopt.
  - `causal_mechanism_assignment(self, taxonomy_version_id: str, hypothesis_id: str) -> str | None` (line 813; public)
  - `insert_causal_blind_prediction_bundle(self, *, bundle_id: str, hypothesis_id: str, hypothesis_version: int, practice_item_id: str, input_hash: str, predictions: Mapping[str, Any], model_revision: str, outcome_schema_version: str, blind_input_contract_version: str | None=None, generation_agent_run_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` (line 831; public) — Insert one content-addressed, observation-blind prediction bundle.
  - `causal_blind_prediction_bundle(self, bundle_id: str) -> dict[str, Any] | None` (line 879; public)
  - `causal_blind_prediction_bundles(self, *, practice_item_id: str | None=None, hypothesis_ids: Iterable[str] | None=None) -> list[dict[str, Any]]` (line 900; public)
  - `insert_probe_manipulation_audit(self, *, audit_id: str, source_kind: str, source_item_id: str, candidate_item_id: str, contract: Mapping[str, Any], structural_diff: Mapping[str, Any], adversarial_review: Mapping[str, Any] | None, status: str, generation_agent_run_id: str | None=None, reviewer_agent_run_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` (line 938; public)
  - `probe_manipulation_audit(self, audit_id: str) -> dict[str, Any] | None` (line 987; public)
  - `insert_causal_probe_candidate(self, *, candidate_id: str, factor_id: str, practice_item_id: str, hypothesis_set_id: str, manipulation_audit_id: str, measurement_contract: Mapping[str, Any], blind_bundle_ids: Sequence[str], discrimination: Mapping[str, Any] | None=None, blind_input_contract_version: str | None=None, status: str='candidate', clock: Clock | None=None) -> dict[str, Any]` (line 1002; public)
  - `causal_probe_candidate(self, candidate_id: str) -> dict[str, Any] | None` (line 1071; public)
  - `update_causal_probe_candidate(self, candidate_id: str, *, status: str, discrimination: Mapping[str, Any] | None=None, reviewer: str | None=None, review_reason: str | None=None, clock: Clock | None=None) -> dict[str, Any] | None` (line 1093; public)
  - `causal_probe_candidate_events(self, candidate_id: str) -> list[dict[str, Any]]` (line 1165; public)
  - `record_causal_activity_classification(self, *, attempt_id: str, contamination_class: str, near_clone: bool=False, closes_pre_intervention_segment: bool | None=None, eligible_for_fsrs: bool | None=None, eligible_for_certification: bool | None=None, near_clone_basis: str | None=None, source: str='unknown', detail: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` (line 1179; public) — Append one classification event; NEVER raises on a conflict (§4.2).
  - `causal_activity_classification_events(self, attempt_id: str) -> list[dict[str, Any]]` (line 1279; public)
  - `causal_activity_classification(self, attempt_id: str) -> dict[str, Any] | None` (line 1296; public) — The current classification, DERIVED from the event log (§4.2).
  - `all_causal_activity_classifications(self) -> dict[str, dict[str, Any]]` (line 1312; public) — Resolve every attempt's current activity policy in one DB read.
  - `insert_causal_discriminating_observation(self, *, observation_id: str, factor_id: str, presentation_id: str, hypothesis_set_id: str, outcome: str, classified_as: Sequence[str], supports_open_set: bool, feature_source: str, observed_features: Mapping[str, Any], declared_keys_observed: bool, admitted: bool, admission_reason: str, support_scores: Mapping[str, Any], resolved_factor: bool, detail: Mapping[str, Any], decision_policy_version: str, formula_version: str, blind_bundle_ids: Sequence[str]=(), attempt_id: str | None=None, probe_attempt_id: str | None=None, candidate_id: str | None=None, support_authority: str | None=None, channel: str | None=None, admissible_as_independent: bool | None=None, inadmissibility_reason: str | None=None, contaminating_reveal_event_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` (line 1340; public) — Append one discriminating-observation receipt (idempotent on id).
  - `causal_discriminating_observation(self, observation_id: str) -> dict[str, Any] | None` (line 1435; public)
  - `causal_discriminating_observations(self, *, factor_id: str | None=None, attempt_id: str | None=None, presentation_id: str | None=None, admitted_only: bool=False, probe_channel_only: bool=False) -> list[dict[str, Any]]` (line 1449; public) — Observation receipts, oldest first.
  - `set_unresolved_cause_hypothesis_refs(self, factor_id: str, refs: Sequence[Mapping[str, Any]], *, clock: Clock | None=None) -> None` (line 1495; public) — Replace P0 duplicated candidate prose with P1 hypothesis references.
  - `insert_unresolved_cause_factor(self, *, attempt_id: str, candidate_causes: Any, algorithm_version: str, observation_id: str | None=None, status: str='open', clock: Clock | None=None) -> str` (line 1517; public)
  - `refresh_open_unresolved_cause_candidates(self, observation_id: str, candidate_causes: Any, *, clock: Clock | None=None) -> bool` (line 1554; public) — Replace an OPEN factor's candidate set when it differs (Slice 1 M2).
  - `open_unresolved_cause_observation_ids(self) -> set[str]` (line 1581; public)
  - `open_unresolved_cause_factor_attempts(self) -> dict[str, str]` (line 1591; public) — Each open observation-keyed factor's attempt id, by observation id.
  - `unresolved_cause_observation_ids(self) -> set[str]` (line 1603; public) — Observation ids the projection sync must NOT (re-)insert a factor for.
  - `unresolved_cause_factors_for_attempt(self, attempt_id: str, *, status: str='open') -> list[dict[str, Any]]` (line 1627; public) — Open unresolved-cause factors for an attempt (the §9.6 diagnostic card).
  - `_presented_causal_candidates(self, candidates: Sequence[Any]) -> list[dict[str, Any]]` (line 1693; internal) — Hydrate P1 refs for presentation without duplicating stored claims.
  - `open_unresolved_cause_factors(self, *, learning_object_id: str | None=None) -> list[dict[str, Any]]` (line 1744; public) — Open positional-ambiguity factors, optionally one learning object.
  - `unresolved_cause_factors(self, *, status: str | None='open') -> list[dict[str, Any]]` (line 1793; public) — Vault-wide unresolved-cause factors (readiness reads; EVSI-2).
  - `unresolved_cause_factor(self, factor_id: str) -> dict[str, Any] | None` (line 1819; public)
  - `resolve_unresolved_cause_factor(self, factor_id: str, *, resolution_observation_ids: Iterable[str], clock: Clock | None=None) -> bool` (line 1846; public)
  - `insert_causal_attribution_report(self, *, factor_id: str, attempt_id: str, response: str, candidate_index: int | None, payload: Mapping[str, Any] | None=None, report_id: str | None=None, clock: Clock | None=None) -> str` (line 1871; public)
  - `retire_unresolved_cause_factor(self, observation_id: str, *, clock: Clock | None=None) -> None` (line 1904; public)
  - `close_unresolved_cause_factor(self, factor_id: str, *, status: str, resolution_kind: str, resolution_detail: Mapping[str, Any] | None=None, clock: Clock | None=None) -> bool` (line 1921; public) — Close an OPEN factor with an explicit evidence label.
  - `causal_attribution_reports_for_factor(self, factor_id: str) -> list[dict[str, Any]]` (line 1962; public) — Learner self-reports on one factor's diagnostic card, oldest first.
  - `primed_attempt_exists_for_learning_object(self, learning_object_id: str, *, since: str) -> bool` (line 1978; public) — Any primed attempt on the learning object at/after ``since``.
  - `insert_causal_probe_decision_receipt(self, *, factor_id: str, decision: str, reason: str, repair_status: str, decision_policy_version: str, formula_version: str, inputs: Mapping[str, Any], parameters: Mapping[str, Any], hypothesis_ids: Sequence[str]=(), repair_class_ids: Sequence[str]=(), blind_bundle_ids: Sequence[str]=(), machine_check_ids: Sequence[str]=(), learning_object_id: str | None=None, attempt_id: str | None=None, misconception_id: str | None=None, candidate_id: str | None=None, clock: Clock | None=None, once: bool=False) -> dict[str, Any]` (line 2009; public) — Append one probe decision.
  - `_decode_causal_probe_decision_receipt(self, row: sqlite3.Row) -> dict[str, Any]` (line 2112; internal)
  - `causal_probe_decision_receipt(self, receipt_id: str) -> dict[str, Any] | None` (line 2130; public)
  - `causal_probe_decision_receipts(self, *, factor_id: str | None=None, decision: str | None=None, limit: int=200) -> list[dict[str, Any]]` (line 2142; public)
  - `_decode_causal_shadow_selection_receipt(self, row: sqlite3.Row) -> dict[str, Any]` (line 2179; internal)
  - `causal_shadow_selection_receipt(self, receipt_id: str) -> dict[str, Any] | None` (line 2194; public)
  - `causal_shadow_selection_receipts(self, *, factor_id: str | None=None, limit: int=500) -> list[dict[str, Any]]` (line 2206; public)
  - `median_attempt_latency_seconds(self) -> tuple[float | None, int]` (line 2232; public) — Pooled median of captured attempt latencies + the sample count.
  - `record_causal_probe_preference(self, *, scope: str, scope_ref: str, preference: str, source: str, session_id: str | None=None, expires_at: str | None=None, detail: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` (line 2260; public) — Persist one learner probe preference ("Not now" and friends).
  - `causal_probe_preference(self, *, factor_id: str | None=None, learning_object_id: str | None=None, session_id: str | None=None, at: str | None=None) -> dict[str, Any] | None` (line 2307; public) — The newest applicable, unexpired preference across the given scopes.
  - `enqueue_causal_machine_check(self, *, check_id: str, kind: str, payload: Mapping[str, Any], source: str, learning_object_id: str | None=None, factor_id: str | None=None, attempt_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` (line 2353; public) — Queue one machine-side obligation, idempotently.
  - `causal_machine_check(self, check_id: str) -> dict[str, Any] | None` (line 2407; public)
  - `causal_machine_checks(self, *, status: str | None='pending', learning_object_id: str | None=None, factor_id: str | None=None) -> list[dict[str, Any]]` (line 2419; public)
  - `close_causal_machine_check(self, check_id: str, *, status: str, resolution: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any] | None` (line 2455; public)
  - `causal_probe_candidates_for_factor(self, factor_id: str, *, statuses: Sequence[str] | None=None) -> list[dict[str, Any]]` (line 2485; public) — Probe candidates minted for one unresolved-cause factor.
  - `insert_diagnosis_adjudication(self, *, values: Mapping[str, Any], adjudication_id: str | None=None, clock: Clock | None=None) -> str` (line 2524; public) — Append one immutable verdict on a diagnosis (A4).
  - `diagnosis_adjudication(self, adjudication_id: str) -> dict[str, Any] | None` (line 2584; public)
  - `diagnosis_adjudications_for_attempt(self, attempt_id: str) -> list[dict[str, Any]]` (line 2594; public) — The whole supersession chain for one attempt, oldest first.
  - `active_diagnosis_adjudication(self, attempt_id: str) -> dict[str, Any] | None` (line 2610; public) — The head of the chain: the row nothing else supersedes.
  - `adjudicated_attempt_ids(self) -> set[str]` (line 2631; public) — Attempts already carrying a verdict — the queue's exclusion set.
  - `list_diagnosis_adjudications(self, *, active_only: bool=True, attempt_ids: Sequence[str] | None=None, verdicts: Sequence[str] | None=None, grading_prompt_version: str | None=None, grader_model: str | None=None, queue_reasons: Sequence[str] | None=None, limit: int | None=None) -> list[dict[str, Any]]` (line 2640; public) — Scoreboard/eval read.
  - `insert_contrast_pair_serving(self, *, pair_key: str, practice_item_id: str, counterpart_item_id: str, serve_position: int, randomization_seed: str, randomization_value: float, separated: bool, adjacency_basis: str, session_id: str | None=None, id: str | None=None, clock: Clock | None=None) -> str | None` (line 2698; public) — Record which member of an A4 pair this session's queue offered first.
  - `contrast_pair_serving_rows(self, *, since: str | None=None, pair_key: str | None=None) -> list[dict[str, Any]]` (line 2747; public)
  - `insert_error_hunt_outcome(self, *, attempt_id: str, practice_item_id: str, clean_solution: bool, planted_total: int, planted_repaired: int, planted_flagged_not_repaired: int, planted_missed: int, false_positive_reports: int, misconception_candidate_id: str | None=None, facet_failure_suppressed: bool=False, grading_prompt_version: str | None=None, id: str | None=None, clock: Clock | None=None) -> str | None` (line 2770; public) — Record one A3 attempt's outcome; ``None`` when the attempt already has one.
  - `error_hunt_outcome_rows(self, *, since: str | None=None) -> list[dict[str, Any]]` (line 2819; public)
  - `error_hunt_outcome(self, attempt_id: str) -> dict[str, Any] | None` (line 2835; public)

### Module constants

- `OBSERVATION_CHANNEL_BLIND_PROBE` ([src/learnloop/db/stores/causal.py](../../../../../../../src/learnloop/db/stores/causal.py), line 24)

## Internal implementation anchors

- `_decode_diagnosis_adjudication(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/causal.py), line 27)
- `_resolve_causal_activity_classification(attempt_id: str, events: Sequence[Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/causal.py), line 37) — Fold one decoded activity-event history through the policy authority.
- `_decode_causal_activity_event(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/causal.py), line 75)
- `_decode_causal_discriminating_observation(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/causal.py), line 89)
- `_decode_causal_mechanism_taxonomy(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/causal.py), line 116)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `CausalStoreMixin`
- [[Reference/Modules/learnloop/diagnosis/causal_discrimination|learnloop.diagnosis.causal_discrimination]] — imports `OBSERVATION_CHANNEL_BLIND_PROBE`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/causal_activity_policy|learnloop.causal_activity_policy]] — imports `CAUSAL_ACTIVITY_POLICY_VERSION`, `CONTAMINATION_PRECEDENCE`, `policy_for_class`; calls `policy_for_class`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/records|learnloop.db.records]] — imports `_decode_causal_hypothesis`; calls `_decode_causal_hypothesis`
- [[Reference/Modules/learnloop/db/row_serialization|learnloop.db.row_serialization]] — imports `_json`, `_loads`; calls `_json`, `_loads`
- [[Reference/Modules/learnloop/db/stores/write_provenance|learnloop.db.stores.write_provenance]] — imports `closure`, `record_text_write`, `stored_record`; calls `closure`, `record_text_write`, `stored_record`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/diagnosis/causal_discrimination|learnloop.diagnosis.causal_discrimination]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/ad1_codex_rereview_fixes_helpers.py](../../../../../../../tests/ad1_codex_rereview_fixes_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad1_reading_opportunities_helpers.py](../../../../../../../tests/ad1_reading_opportunities_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad23_contract_helpers.py](../../../../../../../tests/ad23_contract_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad23_fakes.py](../../../../../../../tests/ad23_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad23_fix_r8_helpers.py](../../../../../../../tests/ad23_fix_r8_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad2_serving_helpers.py](../../../../../../../tests/ad2_serving_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad_ingest_fakes.py](../../../../../../../tests/ad_ingest_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad_projection_helpers.py](../../../../../../../tests/ad_projection_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/apply_write_ahead_helpers.py](../../../../../../../tests/apply_write_ahead_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/approach_map_fakes.py](../../../../../../../tests/approach_map_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/assumed_known_helpers.py](../../../../../../../tests/assumed_known_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/canonical_facet_helpers.py](../../../../../../../tests/canonical_facet_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/causal.py](../../../../../../../src/learnloop/db/stores/causal.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
