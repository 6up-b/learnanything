---
title: "learnloop.attempts.salience_firewall"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/salience_firewall.py"
source_paths:
  - "src/learnloop/attempts/salience_firewall.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempts.salience_firewall module"
  - "src/learnloop/attempts/salience_firewall.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.salience_firewall`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.salience_firewall` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: Reading-signal / salience firewall (spec_p3_reader_integration §8.2, §15.4; design §C).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py) |
| Source lines | 378 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class SalienceEvidenceRejected(ValueError)` ([source](../../../../../../src/learnloop/attempts/salience_firewall.py), line 127) — Raised when a salience-only signal is fed into an evidence/belief API.
- `salience_payload(payload: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/salience_firewall.py), line 131) — Stamp ``authority_class='salience_only'`` onto a reader/reading event payload.
- `is_salience_only(obj: Any) -> bool` ([source](../../../../../../src/learnloop/attempts/salience_firewall.py), line 165)
- `reject_salience(obj: Any, *, context: str='evidence_ingestion') -> None` ([source](../../../../../../src/learnloop/attempts/salience_firewall.py), line 169) — Hard reject: raise if ``obj`` carries salience-only authority.
- `proposal_priority_signal(events: list[Mapping[str, Any]]) -> dict[str, float]` ([source](../../../../../../src/learnloop/attempts/salience_firewall.py), line 181) — The ONE allowed downstream of salience (§8.2): reorder PROPOSAL priority only.
- `salience_projection_v1(events: list[Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/salience_firewall.py), line 206) — Versioned salience projector v1 (§8.2, design B step 9).
- `learning_opportunity_events(rows: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/attempts/salience_firewall.py), line 342) — The confirmed exception's only path (A12, §5.11): learning opportunities, never evidence.

### Module constants

- `SALIENCE_ONLY` ([src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py), line 75)
- `DWELL_SEGMENT_MAX` ([src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py), line 79)
- `READING_EVENT_KINDS` ([src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py), line 84)
- `SALIENCE_PROJECTIONS` ([src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py), line 115)
- `SALIENCE_PROJECTOR_VERSION` ([src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py), line 196)
- `_DEPTH_SUGGEST_HIGHLIGHT_WEIGHT` ([src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py), line 201)
- `_DEPTH_SUGGEST_QUESTION_WEIGHT` ([src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py), line 202)
- `_DEPTH_SUGGEST_REVISIT_WEIGHT` ([src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py), line 203)
- `SELF_CHECK_SUBKINDS` ([src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py), line 284)
- `LESSON_SUBKINDS` ([src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py), line 287)
- `LEARNING_OPPORTUNITY_SOURCES` ([src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py), line 292)
- `READING_OPPORTUNITY_KINDS` ([src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py), line 308)
- `LEARNING_OPPORTUNITY_KINDS` ([src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py), line 311)
- `LEARNING_OPPORTUNITY_FIELDS` ([src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py), line 314)
- `_ALLOWED` ([src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py), line 318)

## Internal implementation anchors

- `_extract_authority_class(obj: Any) -> str | None` ([source](../../../../../../src/learnloop/attempts/salience_firewall.py), line 139) — Best-effort recovery of an authority class from a dict, an event row, or an object carrying a payload/metadata/draft.
- `_doses(value: Any) -> dict[str, float]` ([source](../../../../../../src/learnloop/attempts/salience_firewall.py), line 321)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]] — imports `LEARNING_OPPORTUNITY_KINDS`, `LEARNING_OPPORTUNITY_SOURCES`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `learning_opportunity_events`; statically calls `learning_opportunity_events`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `reject_salience`; statically calls `reject_salience`
- [[Reference/Modules/learnloop/reader/reader_authoring|learnloop.reader.reader_authoring]] — imports `salience_payload`; statically calls `salience_payload`
- [[Reference/Modules/learnloop/reader/reader_capture|learnloop.reader.reader_capture]] — imports `salience_payload`; statically calls `salience_payload`
- [[Reference/Modules/learnloop/reader/reader_cues|learnloop.reader.reader_cues]] — imports `salience_payload`; statically calls `salience_payload`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `salience_payload`; statically calls `salience_payload`
- [[Reference/Modules/learnloop/reader/reader_inquiry|learnloop.reader.reader_inquiry]] — imports `salience_payload`; statically calls `salience_payload`
- [[Reference/Modules/learnloop/reader/reader_restoration|learnloop.reader.reader_restoration]] — imports `salience_payload`; statically calls `salience_payload`
- [[Reference/Modules/learnloop/reader/recap|learnloop.reader.recap]] — imports `salience_payload`; statically calls `salience_payload`
- [[Reference/Modules/learnloop/reader/workbench|learnloop.reader.workbench]] — imports `salience_payload`; statically calls `salience_payload`
- [[Reference/Modules/learnloop/remote/telemetry|learnloop.remote.telemetry]] — imports `salience_payload`; statically calls `salience_payload`
- [[Reference/Modules/learnloop/source_retrieval/kept_comparisons|learnloop.source_retrieval.kept_comparisons]] — imports `salience_payload`; statically calls `salience_payload`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `salience_payload`; statically calls `salience_payload`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `READING_EVENT_KINDS`, `SALIENCE_ONLY`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `salience_payload`; statically calls `salience_payload`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_intent|learnloop_sidecar.handlers.reader_intent]] — imports `salience_payload`; statically calls `salience_payload`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/reading_sources|learnloop.reading_sources]] — imports `IN_PASSAGE_STYLES`, `TUTOR_ANSWER_MODES`, `UNKNOWN_ANSWER_MODE`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]], [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]], [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/reader/reader_authoring|learnloop.reader.reader_authoring]], [[Reference/Modules/learnloop/reader/reader_capture|learnloop.reader.reader_capture]] and 12 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad3_reading.py](../../../../../../tests/test_ad3_reading.py) — direct import
  - `test_a_question_counts_once_and_no_verdict_reaches_evidence`
  - `test_reading_raises_prediction_never_evidence`
- [tests/test_compare_sources_keep.py](../../../../../../tests/test_compare_sources_keep.py) — direct import
  - `test_every_rw4d_event_is_salience_only`
- [tests/test_figure_rich_rpc.py](../../../../../../tests/test_figure_rich_rpc.py) — direct import
  - `test_rich_build_cancelled_is_a_salience_only_event_without_words`
- [tests/test_figures_prefetch.py](../../../../../../tests/test_figures_prefetch.py) — direct import
  - `test_outcomes_close_once_at_the_structural_horizon`
- [tests/test_figures_prefetch_review_fixes.py](../../../../../../tests/test_figures_prefetch_review_fixes.py) — direct import
  - `test_f9_an_open_after_the_horizon_is_not_an_outcome`
- [tests/test_figures_rpc.py](../../../../../../tests/test_figures_rpc.py) — direct import
  - `test_server_events_are_salience_only`
- [tests/test_figures_show_me.py](../../../../../../tests/test_figures_show_me.py) — direct import
  - `test_show_me_requested_is_a_salience_only_event_without_the_words`
- [tests/test_followups_batch7_prefetch_capped_resume.py](../../../../../../tests/test_followups_batch7_prefetch_capped_resume.py) — direct import
- [tests/test_followups_batch7_prefetch_link_served.py](../../../../../../tests/test_followups_batch7_prefetch_link_served.py) — direct import
- [tests/test_library_ask.py](../../../../../../tests/test_library_ask.py) — direct import
  - `test_every_rw4a_event_is_salience_only_refused_as_evidence_and_never_client_recorded`
- [tests/test_library_exercises.py](../../../../../../tests/test_library_exercises.py) — direct import
  - `test_the_learner_pick_is_owed_durably_across_a_restart_and_acknowledged_only_after_delivery`
- [tests/test_mcp_tools.py](../../../../../../tests/test_mcp_tools.py) — direct import
  - `test_every_call_is_recorded_with_its_origin_and_is_never_evidence`
- [tests/test_p3_journeys.py](../../../../../../tests/test_p3_journeys.py) — direct import
  - `test_arc_and_salience_heads_rebuild_deterministically`
- [tests/test_reader_active_reading.py](../../../../../../tests/test_reader_active_reading.py) — direct import
  - `test_the_active_reading_events_are_salience_only`
- [tests/test_reader_activity.py](../../../../../../tests/test_reader_activity.py) — direct import
  - `test_every_client_event_is_salience_only_and_never_evidence`
  - `test_every_server_event_is_salience_only_and_never_evidence`
  - `test_the_vocabulary_is_the_spec_list_plus_the_funnels_rows`
- [tests/test_reader_authoring.py](../../../../../../tests/test_reader_authoring.py) — direct import
  - `test_coach_response_is_corpus_only_salience`
- [tests/test_reader_ca2_astra_handoff.py](../../../../../../tests/test_reader_ca2_astra_handoff.py) — direct import
  - `test_the_handoff_is_recorded_once_and_salience_only`
- [tests/test_reader_ca6_side_by_side.py](../../../../../../tests/test_reader_ca6_side_by_side.py) — direct import
  - `test_each_ca6_event_is_salience_only_keeps_ids_and_drops_words`
- [tests/test_reader_cues.py](../../../../../../tests/test_reader_cues.py) — direct import
  - `test_every_server_cue_event_is_salience_only`
  - `test_taps_are_salience_only_events_and_learner_card_verdicts`
- [tests/test_reader_dialogue.py](../../../../../../tests/test_reader_dialogue.py) — direct import
  - `test_real_reader_writes_carry_the_salience_firewall_stamp`
- [tests/test_reader_reconstruct.py](../../../../../../tests/test_reader_reconstruct.py) — direct import
  - `test_every_rw1b_event_is_salience_only_refused_as_evidence_and_never_client_recorded`
- [tests/test_reader_restoration.py](../../../../../../tests/test_reader_restoration.py) — direct import
  - `test_restoration_records_salience_exposure_and_cannot_be_evidence`
- [tests/test_reader_try_first.py](../../../../../../tests/test_reader_try_first.py) — direct import
  - `test_pressing_try_first_is_a_learner_pick_that_opens_the_next_step_at_that_line`
- [tests/test_reader_tutor_offers.py](../../../../../../tests/test_reader_tutor_offers.py) — direct import
  - `test_a_press_is_a_salience_only_reader_event_counted_by_the_report`
- [tests/test_reader_workbench_rw2a.py](../../../../../../tests/test_reader_workbench_rw2a.py) — direct import
  - `test_every_workbench_event_is_salience_only`
- [tests/test_salience_firewall.py](../../../../../../tests/test_salience_firewall.py) — direct import
  - `test_apply_attempt_chokepoint_rejects_salience`
  - `test_carve_out_allowlist_is_the_sweeps_list_and_the_only_typed_value_is_the_verdict`
  - `test_firewall_carve_out_admits_only_listed_kinds`
  - `test_highlights_may_reorder_proposals_only`
  - `test_non_salience_input_is_not_rejected`
  - `test_reject_salience_hard_rejects_every_reading_signal`
  - `test_rw3b_cue_events_are_salience_only_server_events_the_client_cannot_record`
  - `test_salience_payload_always_stamps_authority_class`
  - `test_salience_projection_dwell_is_bounded`
  - `test_salience_projection_v1_is_salience_only_and_rejected_as_evidence`
- [tests/test_te3a_lesson_opportunity.py](../../../../../../tests/test_te3a_lesson_opportunity.py) — direct import
  - `test_the_firewall_admits_exactly_the_lesson_subkinds_and_they_stay_salience_only`
  - `test_the_prior_is_centred_and_spread_on_ro4s_placeholder_with_ads_shape`
- [tests/test_workbench_hint_service.py](../../../../../../tests/test_workbench_hint_service.py) — direct import
  - `test_help_events_are_salience_only`

## Modification guidance

- Change salience firewall policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
