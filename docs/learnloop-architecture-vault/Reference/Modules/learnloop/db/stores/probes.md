---
title: "learnloop.db.stores.probes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/probes.py"
source_paths:
  - "src/learnloop/db/stores/probes.py"
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
  - "learnloop.db.stores.probes module"
  - "src/learnloop/db/stores/probes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.probes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.probes` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Diagnostic probe episodes, instruments and evaluation.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/probes.py](../../../../../../../src/learnloop/db/stores/probes.py) |
| Source lines | 2168 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class ProbeEpisodeRecord` ([source](../../../../../../../src/learnloop/db/stores/probes.py), line 27) — One first-class diagnostic episode (probe redesign spec §5.1).
- `class ProbeStateSegmentRecord` ([source](../../../../../../../src/learnloop/db/stores/probes.py), line 55) — A learner-state segment boundary event (probe redesign spec §5.1).
- `class ProbeFamilyTemplateRecord` ([source](../../../../../../../src/learnloop/db/stores/probes.py), line 68)
- `class ProbeInstrumentCardRecord` ([source](../../../../../../../src/learnloop/db/stores/probes.py), line 79)
- `class ProbeItemFamilyLinkRecord` ([source](../../../../../../../src/learnloop/db/stores/probes.py), line 93)
- `class ProbeGenerationNeedRecord` ([source](../../../../../../../src/learnloop/db/stores/probes.py), line 105)
- `class ProbeCalibrationSessionRecord` ([source](../../../../../../../src/learnloop/db/stores/probes.py), line 117) — A learner-initiated calibration session (probe redesign spec §5.9).
- `class ProbeStoreMixin` ([source](../../../../../../../src/learnloop/db/stores/probes.py), line 273)
  - `probe_state(self, learning_object_id: str) -> ProbeStateRecord | None` (line 275; public)
  - `upsert_probe_state(self, *, learning_object_id: str, status: str, algorithm_version: str, probe_phase_id: str | None=None, hypothesis_set_id: str | None=None, probe_attempts_completed: int=0, probe_attempts_target: int=3, families_converged: list[str] | None=None, entered_at: str | None=None, completed_at: str | None=None, clock: Clock | None=None) -> None` (line 283; public)
  - `insert_hypothesis_set(self, *, learning_object_id: str, probe_phase_id: str | None, hypotheses: list[Mapping[str, Any]], prior: Mapping[str, float], algorithm_version: str, prior_basis: str | None=None, clock: Clock | None=None) -> str` (line 337; public)
  - `fetch_hypothesis_set(self, hypothesis_set_id: str) -> dict[str, Any] | None` (line 373; public)
  - `insert_probe_episode(self, *, learning_object_id: str, status: str, trigger: str, hypothesis_set_id: str | None, active_state_segment_id: str | None, algorithm_version: str, target_decision: Mapping[str, Any] | None=None, origin: str | None=None, required_facets: list[str] | None=None, minimum_independent_observations: int=2, maximum_observations: int=4, entered_at: str | None=None, episode_id: str | None=None, target_contract_version_id: str | None=None, target_support_hash: str | None=None, calibration_model_id: str | None=None, calibration_model_hash: str | None=None, probe_mapping_version: str | None=None, clock: Clock | None=None) -> str` (line 383; public)
  - `probe_episode(self, episode_id: str) -> ProbeEpisodeRecord | None` (line 448; public)
  - `open_probe_episode(self, learning_object_id: str) -> ProbeEpisodeRecord | None` (line 455; public) — The single open (`pending_items` / `in_progress`) episode for an LO, if any.
  - `open_probe_episodes(self) -> dict[str, ProbeEpisodeRecord]` (line 470; public)
  - `probe_episodes_for_learning_object(self, learning_object_id: str) -> list[ProbeEpisodeRecord]` (line 477; public)
  - `update_probe_episode_status(self, episode_id: str, *, status: str, completion_reason: str | None=None, completed_at: str | None=None, active_state_segment_id: str | None=None, completion_posterior_json: str | None=None, completion_detail_json: str | None=None, clock: Clock | None=None) -> None` (line 485; public)
  - `latest_completed_probe_episode(self, learning_object_id: str) -> dict[str, Any] | None` (line 525; public) — Latest complete episode's conclusion for entry-rung selection: completion_reason plus the argmax of the persisted completion posterior.
  - `open_state_segment(self, *, learning_object_id: str, probe_episode_id: str | None, reason: str, opened_by_attempt_id: str | None=None, clock: Clock | None=None) -> str` (line 553; public) — Mint the next state segment for an LO and persist its opening event.
  - `state_segments_for_learning_object(self, learning_object_id: str) -> list[ProbeStateSegmentRecord]` (line 597; public)
  - `insert_probe_presentation(self, *, probe_episode_id: str, practice_item_id: str, state_segment_id: str, scheduler_candidate_id: str | None=None, probe_family_template_id: str | None=None, probe_family_template_version: int | None=None, instrument_card_id: str | None=None, instrument_card_version: int | None=None, instrument_card_snapshot: Mapping[str, Any] | None=None, target_hypothesis_pairs: list[list[str]] | None=None, target_facets: list[str] | None=None, posterior_at_selection: Mapping[str, float] | None=None, entropy_at_selection: float | None=None, expected_information_gain: float | None=None, selection_policy_version: str | None=None, selection_components: Mapping[str, Any] | None=None, expires_at: str | None=None, clock: Clock | None=None) -> str` (line 607; public)
  - `probe_presentation(self, presentation_id: str) -> ProbePresentationRecord | None` (line 659; public)
  - `probe_presentations_for_episode(self, probe_episode_id: str) -> list[ProbePresentationRecord]` (line 666; public)
  - `active_probe_presentation(self, probe_episode_id: str, practice_item_id: str | None=None) -> ProbePresentationRecord | None` (line 674; public) — The most recent committed-but-unconsumed presentation for an episode.
  - `active_probe_presentation_for_item(self, practice_item_id: str) -> ProbePresentationRecord | None` (line 695; public) — The latest committed-but-unconsumed diagnostic presentation of an item, in any episode (Reader CA1: the item is being measured on your own, so nothing may locate it).
  - `mark_probe_presentation_served(self, presentation_id: str, *, clock: Clock | None=None) -> None` (line 711; public)
  - `consume_probe_presentation(self, presentation_id: str, *, clock: Clock | None=None) -> bool` (line 724; public) — Atomically move a presentation to `submitted`; False if not consumable.
  - `end_probe_presentation(self, presentation_id: str, *, end_reason: str, clock: Clock | None=None) -> None` (line 740; public)
  - `insert_probe_observation(self, *, attempt_id: str, posterior_before: Mapping[str, float], posterior_after: Mapping[str, float], entropy_before: float, entropy_after: float, realized_information_gain: float, independent_evidence_discount: float | None=None, contamination: Mapping[str, Any] | None=None, grader_channel: Mapping[str, Any] | None=None, updates_belief: bool=True, eligible_for_completion: bool=False, features: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` (line 757; public)
  - `qualifying_probe_observation_count(self) -> int` (line 807; public) — Qualifying diagnostic observations across the whole vault (§5.9 time-to-first-ordinary-practice ceiling), held ones excluded (review F3).
  - `qualifying_probe_observation_attempt_ids(self, session_id: str | None=None) -> list[str]` (line 825; public) — The attempts of the observations :meth:`qualifying_probe_observation_count` (vault-wide) or ``qualifying_probe_observation_count_for_session`` (``session_id``) count, as recorded (held ones excluded): what a tag-aware reader (``probe_episodes.effective_qualifying_total``) reads…
  - `ordinary_practice_attempt_count(self) -> int` (line 843; public) — Attempts recorded outside the diagnostic/exam channels (§5.9): the signal that ordinary practice has started in this vault.
  - `probe_observation_for_attempt(self, attempt_id: str) -> ProbeObservationRecord | None` (line 857; public) — One observation AS RECORDED (its receipt): existence checks and the grader-agreement regrade check read it.
  - `list_probe_episodes(self, *, statuses: tuple[str, ...] | None=None) -> list[ProbeEpisodeRecord]` (line 868; public) — All episodes, oldest first, optionally filtered by status.
  - `upsert_probe_family_template(self, *, family_id: str, version: int, status: str, template: Mapping[str, Any], schema_hash: str, clock: Clock | None=None) -> None` (line 884; public)
  - `probe_family_template(self, family_id: str, version: int) -> ProbeFamilyTemplateRecord | None` (line 907; public)
  - `latest_probe_family_template(self, family_id: str, *, statuses: tuple[str, ...]=('provisional', 'trusted')) -> ProbeFamilyTemplateRecord | None` (line 915; public)
  - `update_probe_family_template_status(self, family_id: str, version: int, *, status: str, clock: Clock | None=None) -> None` (line 930; public) — Lifecycle transition for one family version (§9.7, Checkpoint 4.7).
  - `all_probe_family_templates(self) -> list[ProbeFamilyTemplateRecord]` (line 949; public)
  - `insert_probe_family_lifecycle_event(self, *, probe_family_template_id: str, probe_family_template_version: int, from_status: str, to_status: str, reason: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` (line 956; public)
  - `probe_family_lifecycle_events(self, probe_family_template_id: str, probe_family_template_version: int | None=None) -> list[dict[str, Any]]` (line 989; public)
  - `insert_probe_instrument_card(self, *, card_id: str, version: int, probe_family_template_id: str, probe_family_template_version: int, learning_object_id: str, hypothesis_scope: list[str], card: Mapping[str, Any], compiled_likelihood_hash: str, clock: Clock | None=None) -> None` (line 1009; public)
  - `probe_instrument_card(self, card_id: str, version: int) -> ProbeInstrumentCardRecord | None` (line 1047; public)
  - `probe_instrument_cards_for_learning_object(self, learning_object_id: str) -> list[ProbeInstrumentCardRecord]` (line 1055; public)
  - `link_probe_item_family(self, *, practice_item_id: str, instrument_card_id: str, instrument_card_version: int, generator_id: str | None=None, generator_version: str | None=None, generation_seed: str | None=None, instance_metadata: Mapping[str, Any] | None=None, clock: Clock | None=None) -> None` (line 1069; public)
  - `probe_item_family_links(self, practice_item_id: str) -> list[ProbeItemFamilyLinkRecord]` (line 1105; public)
  - `probe_items_for_card(self, instrument_card_id: str, instrument_card_version: int) -> list[str]` (line 1113; public)
  - `upsert_probe_family_calibration(self, *, probe_family_template_id: str, probe_family_template_version: int, evidence_source: str, parameter_posterior: Mapping[str, Any], sample_size: int, effective_sample_size: float | None=None, generator_version: str | None=None, grader_version: str | None=None, clock: Clock | None=None) -> None` (line 1125; public)
  - `probe_family_calibration(self, probe_family_template_id: str, probe_family_template_version: int, *, evidence_source: str, generator_version: str | None=None, grader_version: str | None=None) -> dict[str, Any] | None` (line 1190; public)
  - `probe_family_calibrations_for_family(self, probe_family_template_id: str, probe_family_template_version: int) -> list[dict[str, Any]]` (line 1222; public) — Every calibration row for one family version, all evidence sources.
  - `upsert_probe_item_calibration(self, *, practice_item_id: str, probe_family_template_id: str, probe_family_template_version: int, evidence_source: str, parameter_posterior: Mapping[str, Any], sample_size: int, effective_sample_size: float | None=None, grader_version: str | None=None, clock: Clock | None=None) -> None` (line 1243; public) — Item-instance residual layer under the family posterior (§9.7).
  - `probe_item_calibration(self, practice_item_id: str, probe_family_template_id: str, probe_family_template_version: int, *, evidence_source: str, grader_version: str | None=None) -> dict[str, Any] | None` (line 1310; public)
  - `insert_probe_regrade_check(self, *, attempt_id: str, probe_family_template_id: str, probe_family_template_version: int, original_outcome: str, regrade_outcome: str, grader_version: str | None=None, clock: Clock | None=None) -> str` (line 1344; public)
  - `probe_regrade_checks(self, probe_family_template_id: str | None=None, probe_family_template_version: int | None=None) -> list[dict[str, Any]]` (line 1380; public)
  - `upsert_probe_generation_need(self, *, probe_episode_id: str, learning_object_id: str, target_key: str, missing_capability: str, clock: Clock | None=None) -> str` (line 1403; public) — Create one deduplicated pending generation need per episode target.
  - `probe_generation_needs(self, *, learning_object_id: str | None=None, probe_episode_id: str | None=None, status: str | None=None) -> list[ProbeGenerationNeedRecord]` (line 1436; public)
  - `resolve_probe_generation_need(self, need_id: str, *, status: str='resolved', clock: Clock | None=None) -> None` (line 1461; public)
  - `upsert_diagnostic_surface_generation_need(self, *, learning_object_id: str, consumed_practice_item_id: str, target_key: str, missing_capability: str='diagnostic_probe_surface', facet_ids: list[str] | None=None, misconception_ids: list[str] | None=None, clock: Clock | None=None) -> str` (line 1474; public) — Record one deduplicated replacement need per consumed diagnostic surface.
  - `diagnostic_surface_generation_needs(self, *, learning_object_id: str | None=None, status: str | None=None) -> list[dict[str, Any]]` (line 1527; public)
  - `resolve_diagnostic_surface_generation_need(self, need_id: str, *, status: str='resolved', clock: Clock | None=None) -> None` (line 1564; public)
  - `update_probe_item_family_metadata(self, *, practice_item_id: str, instrument_card_id: str, instrument_card_version: int, instance_metadata: Mapping[str, Any]) -> None` (line 1575; public)
  - `probe_instance_ids_with_review_status(self, review_status: str) -> set[str]` (line 1594; public)
  - `insert_probe_calibration_session(self, *, session_id: str, learning_object_ids: list[str], planned_episode_ids: list[str], time_budget_minutes: int, goal_id: str | None=None, clock: Clock | None=None) -> str` (line 1607; public)
  - `probe_calibration_session(self, calibration_id: str) -> ProbeCalibrationSessionRecord | None` (line 1644; public)
  - `active_probe_calibration_session(self, session_id: str) -> ProbeCalibrationSessionRecord | None` (line 1651; public)
  - `end_probe_calibration_session(self, calibration_id: str, *, status: str, clock: Clock | None=None) -> None` (line 1659; public)
  - `list_all_probe_presentations(self) -> list[dict[str, Any]]` (line 1674; public)
  - `list_all_probe_instrument_cards(self) -> list[dict[str, Any]]` (line 1681; public)
  - `ensure_diagnostic_pack(self, *, pack_slug: str, blueprint_version_id: str, content_hash: str, clock: Clock | None=None) -> dict[str, Any]` (line 1693; public) — Register/return the stable diagnostic pack row.
  - `register_diagnostic_pack_card(self, *, pack_id: str, card_slug: str, coverage_json: str, content_hash: str, instrument_ref: str | None=None, clock: Clock | None=None) -> str` (line 1737; public) — Register a candidate diagnostic-purpose card.
  - `set_diagnostic_pack_card_admission(self, *, pack_id: str, card_slug: str, admission_status: str, detail_json: str | None=None, author: str='owner', clock: Clock | None=None) -> None` (line 1772; public)
  - `transition_diagnostic_pack(self, *, pack_id: str, status: str, kind: str, detail_json: str | None=None, author: str='owner', clock: Clock | None=None) -> None` (line 1800; public)
  - `diagnostic_pack(self, pack_id: str) -> dict[str, Any] | None` (line 1826; public)
  - `diagnostic_packs_for_blueprint(self, blueprint_version_id: str) -> list[dict[str, Any]]` (line 1833; public)
  - `diagnostic_pack_cards_for(self, pack_id: str) -> list[dict[str, Any]]` (line 1841; public)
  - `diagnostic_pack_events_for(self, pack_id: str) -> list[dict[str, Any]]` (line 1849; public)
  - `pin_diagnostic_pack(self, *, run_id: str, pack_id: str, goal_contract_version_id: str, visible_cap: int, probe_episode_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` (line 1857; public) — Pin exactly one reviewed pack to a run at diagnostic entry (§5.2).
  - `diagnostic_pack_pin_for_run(self, run_id: str) -> dict[str, Any] | None` (line 1894; public)
  - `insert_persona_realism_run(self, values: Mapping[str, Any], *, clock: Clock | None=None) -> str` (line 1903; public) — Append one blinded B2 matcher result.
  - `persona_realism_run_rows(self, *, generator_family: str | None=None, persona_source: str | None=None, persona_corpus_hash: str | None=None) -> list[dict[str, Any]]` (line 1954; public)
  - `latest_persona_realism_run(self, *, generator_family: str | None=None, persona_source: str | None=None, persona_corpus_hash: str | None=None) -> dict[str, Any] | None` (line 1984; public)
  - `real_attempt_trace_rows(self, *, limit: int=500) -> list[dict[str, Any]]` (line 1998; public) — Recent non-empty real learner traces for B2, newest first.
  - `insert_diagnostic_eval_run(self, values: Mapping[str, Any], *, clock: Clock | None=None) -> str` (line 2022; public)
  - `insert_diagnostic_eval_case(self, values: Mapping[str, Any], *, clock: Clock | None=None) -> str` (line 2063; public)
  - `diagnostic_eval_run_rows(self) -> list[dict[str, Any]]` (line 2132; public)
  - `diagnostic_eval_case_rows(self, *, run_id: str | None=None, licensed_only: bool=False) -> list[dict[str, Any]]` (line 2142; public)

## Internal implementation anchors

- `_decode_persona_realism_run(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/probes.py), line 133)
- `_decode_diagnostic_eval_run(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/probes.py), line 139)
- `_decode_diagnostic_eval_case(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/probes.py), line 147)
- `_probe_episode_record(row: sqlite3.Row) -> ProbeEpisodeRecord` ([source](../../../../../../../src/learnloop/db/stores/probes.py), line 167)
- `_probe_state_segment_record(row: sqlite3.Row) -> ProbeStateSegmentRecord` ([source](../../../../../../../src/learnloop/db/stores/probes.py), line 192)
- `_probe_family_template_record(row: sqlite3.Row) -> ProbeFamilyTemplateRecord` ([source](../../../../../../../src/learnloop/db/stores/probes.py), line 204)
- `_probe_instrument_card_record(row: sqlite3.Row) -> ProbeInstrumentCardRecord` ([source](../../../../../../../src/learnloop/db/stores/probes.py), line 216)
- `_probe_item_family_link_record(row: sqlite3.Row) -> ProbeItemFamilyLinkRecord` ([source](../../../../../../../src/learnloop/db/stores/probes.py), line 231)
- `_probe_generation_need_record(row: sqlite3.Row) -> ProbeGenerationNeedRecord` ([source](../../../../../../../src/learnloop/db/stores/probes.py), line 244)
- `_probe_calibration_session_record(row: sqlite3.Row) -> ProbeCalibrationSessionRecord` ([source](../../../../../../../src/learnloop/db/stores/probes.py), line 257)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ProbeStoreMixin`
- [[Reference/Modules/learnloop/diagnosis/calibration_sessions|learnloop.diagnosis.calibration_sessions]] — imports `ProbeCalibrationSessionRecord`
- [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]] — imports `ProbeEpisodeRecord`
- [[Reference/Modules/learnloop/diagnosis/probe_completion|learnloop.diagnosis.probe_completion]] — imports `ProbeEpisodeRecord`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `ProbeEpisodeRecord`
- [[Reference/Modules/learnloop/diagnosis/probe_evidence|learnloop.diagnosis.probe_evidence]] — imports `ProbeEpisodeRecord`
- [[Reference/Modules/learnloop/diagnosis/probe_hard_stops|learnloop.diagnosis.probe_hard_stops]] — imports `ProbeEpisodeRecord`
- [[Reference/Modules/learnloop/diagnosis/probe_presentations|learnloop.diagnosis.probe_presentations]] — imports `ProbeEpisodeRecord`
- [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]] — imports `ProbeCalibrationSessionRecord`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/records|learnloop.db.records]] — imports `ProbeObservationRecord`, `ProbePresentationRecord`, `ProbeStateRecord`, `_decode_hypothesis_set`, `_insert_probe_presentation_row`, `_probe_observation_record`, `_probe_presentation_record`, `_probe_state_record`; calls `_decode_hypothesis_set`, `_insert_probe_presentation_row`, `_probe_observation_record`, `_probe_presentation_record`, `_probe_state_record`
- [[Reference/Modules/learnloop/db/row_serialization|learnloop.db.row_serialization]] — imports `_json`, `_loads`; calls `_json`, `_loads`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_for_review_attempts`; calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/diagnosis/calibration_sessions|learnloop.diagnosis.calibration_sessions]], [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]], [[Reference/Modules/learnloop/diagnosis/probe_completion|learnloop.diagnosis.probe_completion]], [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] and 4 more.

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

1. Modify [src/learnloop/db/stores/probes.py](../../../../../../../src/learnloop/db/stores/probes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
