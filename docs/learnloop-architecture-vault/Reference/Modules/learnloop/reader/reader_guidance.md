---
title: "learnloop.reader.reader_guidance"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/reader_guidance.py"
source_paths:
  - "src/learnloop/reader/reader_guidance.py"
source_commit: "6df9761722934fe9a15e17c92a3b74cb50b9425c"
source_commit_timestamp: "2026-11-03T19:25:26-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.reader_guidance module"
  - "src/learnloop/reader/reader_guidance.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.reader_guidance`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.reader_guidance` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Personalized, source-grounded guidance for the Reader.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/reader_guidance.py](../../../../../../src/learnloop/reader/reader_guidance.py) |
| Source lines | 629 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `6df9761722934fe9a15e17c92a3b74cb50b9425c` |
| Commit timestamp | `2026-11-03T19:25:26-05:00` |

## Public API

- `goal_for_item(vault: LoadedVault, learning_object: Any, item: Any) -> Any | None` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 62)
- `build_guide_plan(vault: LoadedVault, repository: Repository, *, extraction_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 206) — Build section checks and suggested passages for one extraction.
- `held_out_sections(vault_or_sets: Any, repository: Repository, extraction_id: str, section_rows: Iterable[Mapping[str, Any]]) -> set[str]` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 495) — The sections with any block in held-out material (exam protection's one held-out partition, ``content.sources.exam_material``).
- `reading_protection(vault_or_sets: Any, repository: Repository, extraction_id: str, span_ids: Iterable[str | None]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 514) — What of a reading the Reader's model actions must not touch, for its selection surfaces (reader-pdf-selection): the whole reading when it is withheld (``exam_material`` rule 4, or held out whole), else its held-out passages, with the refusal the model paths give.

### Module constants

- `_PATTERN_PHASES` ([src/learnloop/reader/reader_guidance.py](../../../../../../src/learnloop/reader/reader_guidance.py), line 38)
- `_READING_PHASES` ([src/learnloop/reader/reader_guidance.py](../../../../../../src/learnloop/reader/reader_guidance.py), line 44)

## Internal implementation anchors

- `_section_key(value: str | None) -> str` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 47)
- `_cited_text(repository: Repository, ref: SourceRef) -> str | None` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 51) — The text a span ref cites, read on the reading it names.
- `_learner_signal(repository: Repository, learning_object_id: str, *, goal_match: bool) -> tuple[float, str, str]` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 76) — Return a local ranking boost and a learner-facing, non-numeric reason.
- `_refs_for(vault: LoadedVault, item: Any, learning_object: Any) -> Iterable[SourceRef]` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 111)
- `_placement_item_id(placement: dict[str, Any], blueprint_spec: dict[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 120) — Resolve the explicitly placed surface, with a legacy blueprint fallback.
- `_placement_phase(placement: dict[str, Any]) -> tuple[str, str | None]` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 145)
- `_placement_section(placement: dict[str, Any], *, blueprint_unit_id: str, sections: list[dict[str, Any]]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 154)
- `_placement_suppressed(repository: Repository, placement_event_id: str) -> bool` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 191) — Honor the learner's durable "don't bring this back" control.
- `_pending_diagnoses(repository: Repository, sections: list[dict[str, Any]]) -> list[str]` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 268) — Attempts whose pending live diagnosis can still change a shown reason.
- `_goal_candidate(goal: Any, golden_run: Mapping[str, Any] | None, score: float) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 287)
- `_passages_by_section(vault: LoadedVault, repository: Repository, *, source_id: str, extraction_id: str, note_ids: set[str], blocks: list[Any], block_by_span: dict[str, Any], span_to_section: dict[str, str]) -> tuple[dict[str, dict[str, dict[str, Any]]], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 297) — Passages that active, source-grounded Practice Items cite, keyed by section then span.
- `_pinned_blueprint_goals(vault: LoadedVault, repository: Repository, *, source_revs: set[str], unit_ids: set[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 377) — Active goals whose golden-path run pins a blueprint to this source, by blueprint version.
- `_reviewed_placement_questions(vault: LoadedVault, repository: Repository, *, source_revs: set[str], section_rows: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 407) — One owner-reviewed question per section, from static reviewed placements (P3 §5.1 / P2 §7.6).
- `_add_auto_authored_questions(repository: Repository, *, extraction_id: str, question_by_section: dict[str, dict[str, Any]], passages_by_section: dict[str, dict[str, dict[str, Any]]], withheld_sections: set[str] | frozenset[str]=frozenset()) -> None` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 534) — Fill sections that have no owner-reviewed question with their authored quick check.
- `_goal_context(goal_candidates: list[dict[str, Any]]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 594) — The highest-scoring goal any passage or question supports (ties to the larger goal id).
- `_assembled_sections(section_rows: list[dict[str, Any]], passages_by_section: dict[str, dict[str, dict[str, Any]]], question_by_section: dict[str, dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/reader_guidance.py), line 609) — Each section with its question and its three best passages (scores stripped).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `extraction_sections`; statically calls `extraction_sections`
- [[Reference/Modules/learnloop/content/pipeline/reread|learnloop.content.pipeline.reread]] — imports `extraction_sections`; statically calls `extraction_sections`
- [[Reference/Modules/learnloop/daily_plan/reading|learnloop.daily_plan.reading]] — imports `extraction_sections`; statically calls `extraction_sections`
- [[Reference/Modules/learnloop/figures/help|learnloop.figures.help]] — imports `extraction_sections`; statically calls `extraction_sections`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `extraction_sections`; statically calls `extraction_sections`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `extraction_sections`; statically calls `extraction_sections`
- [[Reference/Modules/learnloop/reader/reader_cues|learnloop.reader.reader_cues]] — imports `held_out_sections`; statically calls `held_out_sections`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `_canonical_note_ids`, `_span_for_ref`, `extraction_sections`; statically calls `_canonical_note_ids`, `_span_for_ref`, `extraction_sections`
- [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] — imports `extraction_sections`; statically calls `extraction_sections`
- [[Reference/Modules/learnloop/reader/recap|learnloop.reader.recap]] — imports `extraction_sections`; statically calls `extraction_sections`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `extraction_sections`, `goal_for_item`; statically calls `extraction_sections`, `goal_for_item`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `extraction_sections`; statically calls `extraction_sections`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `build_guide_plan`, `extraction_sections`, `goal_for_item`, `held_out_sections`, `reading_protection`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_cue_discovery|learnloop_sidecar.handlers.reader_cue_discovery]] — imports `module`; statically calls `build_guide_plan`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_intent|learnloop_sidecar.handlers.reader_intent]] — imports `module`; statically calls `reading_protection`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `held_out_among`, `held_out_material`, `held_out_refusal`; calls `held_out_among`, `held_out_material`, `held_out_refusal`
- [[Reference/Modules/learnloop/content/sources/span_aliases|learnloop.content.sources.span_aliases]] — imports `SpanTranslator`; calls `SpanTranslator`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/section_map|learnloop.section_map]] — imports `ANCHOR_CURRENT`, `ANCHOR_MOVED`, `SPAN_LOCATOR_RE`, `anchor_for_ref`, `canonical_note_ids`, `extraction_sections`, `normalize_text`, `span_for_ref`; calls `anchor_for_ref`, `canonical_note_ids`, `extraction_sections`, `normalize_text`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `SourceRef`, `learning_object_facet_union`; calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `presented_prompt`; calls `presented_prompt`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `math`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]], [[Reference/Modules/learnloop/content/pipeline/reread|learnloop.content.pipeline.reread]], [[Reference/Modules/learnloop/daily_plan/reading|learnloop.daily_plan.reading]], [[Reference/Modules/learnloop/figures/help|learnloop.figures.help]], [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] and 10 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad_protected_readings.py](../../../../../../tests/test_ad_protected_readings.py) — direct import
  - `test_a_clean_reading_is_read_as_the_reader_and_the_incumbent_read_it`
- [tests/test_curriculum_c1_plan_follows_path.py](../../../../../../tests/test_curriculum_c1_plan_follows_path.py) — direct import
- [tests/test_daily_plan_reading.py](../../../../../../tests/test_daily_plan_reading.py) — direct import
- [tests/test_exam_protection.py](../../../../../../tests/test_exam_protection.py) — direct import
  - `test_a_reader_check_over_held_out_material_is_refused_before_any_model_call`
- [tests/test_mobile_v4_reader.py](../../../../../../tests/test_mobile_v4_reader.py) — direct import
  - `test_render_view_without_a_range_is_todays_reply_byte_for_byte`
- [tests/test_passage_links.py](../../../../../../tests/test_passage_links.py) — direct import
  - `test_with_the_judge_stubbed_to_none_no_discovered_cue_appears`
- [tests/test_reader_active_reading.py](../../../../../../tests/test_reader_active_reading.py) — direct import
- [tests/test_reader_cue_holdout.py](../../../../../../tests/test_reader_cue_holdout.py) — direct import
- [tests/test_reader_cue_value.py](../../../../../../tests/test_reader_cue_value.py) — direct import
  - `test_a_new_application_is_ordered_by_the_predictors_p_failure_on_its_passages_lo`
  - `test_a_target_seen_this_visit_ranks_after_targets_not_yet_seen_and_placement_alone_never_demotes`
- [tests/test_reader_cues.py](../../../../../../tests/test_reader_cues.py) — direct import
  - `test_a_cue_on_held_out_material_cannot_be_tapped`
  - `test_a_transcript_passage_carries_a_cue_like_any_source`
  - `test_not_relevant_withholds_the_cue_until_the_learner_undoes_it`
- [tests/test_reader_guidance.py](../../../../../../tests/test_reader_guidance.py) — direct import
  - `test_dont_bring_this_back_suppresses_the_exact_reviewed_placement`
  - `test_guide_plan_writes_nothing`
  - `test_joint_guide_plan_is_unchanged_by_the_overlay_read`
  - `test_joint_guide_plan_never_waits_on_a_shadow_diagnosis`
  - `test_legacy_placement_uses_only_its_reviewed_familiar_exemplar`
  - `test_reviewed_boundary_placement_connects_question_to_active_goal`
  - `test_split_guide_falls_back_to_the_error_type_when_the_diagnosis_failed`
  - `test_split_guide_falls_back_to_the_error_type_while_the_diagnosis_is_pending`
  - `test_split_guide_plan_names_the_pending_diagnosis_until_it_lands`
  - `test_split_guide_plan_waits_on_nothing_once_the_diagnosis_failed`
  - `test_split_guide_plan_waits_only_on_diagnoses_behind_its_passages`
  - `test_split_guide_reason_names_the_diagnosers_statement`
  - `test_timestamp_provenance_anchors_video_transcript_guidance`
  - `test_unplaced_source_item_never_becomes_a_boundary_question`
  - `test_unresolved_misunderstanding_drives_plain_language_passage_reason`
- [tests/test_reader_quick_check.py](../../../../../../tests/test_reader_quick_check.py) — direct import
  - `test_dismissed_question_suppresses_reauthoring_and_display`
  - `test_escalate_mints_practice_item_with_span_provenance`
  - `test_guide_plan_falls_back_to_authored_question`
  - `test_owner_reviewed_placement_wins_over_authored`
- [tests/test_reader_reconnect.py](../../../../../../tests/test_reader_reconnect.py) — direct import
  - `test_an_inquiry_row_never_shadows_its_sections_quick_check`
- [tests/test_reader_rw3b_fix_round4.py](../../../../../../tests/test_reader_rw3b_fix_round4.py) — direct import
  - `test_a_logged_impression_stores_the_exact_propensity`
- [tests/test_reader_rw3b_protection.py](../../../../../../tests/test_reader_rw3b_protection.py) — direct import
  - `test_every_discovered_template_and_rendered_line_is_free_of_trait_and_verdict_words`
- [tests/test_reader_rw3b_review_fixes.py](../../../../../../tests/test_reader_rw3b_review_fixes.py) — direct import
  - `test_a_tap_on_a_drawn_mark_does_not_rebuild_the_plan`
  - `test_open_shows_the_cited_answer_and_the_learners_own_words`
  - `test_the_plan_says_when_background_work_can_still_name_a_target`
- [tests/test_reader_try_first.py](../../../../../../tests/test_reader_try_first.py) — direct import
- [tests/test_reading_hardening_landing.py](../../../../../../tests/test_reading_hardening_landing.py) — direct import
  - `test_the_guide_plan_never_lists_a_check_for_a_held_out_section`
- [tests/test_required_method_round3.py](../../../../../../tests/test_required_method_round3.py) — direct import
  - `test_the_reader_quick_check_and_the_tutors_practice_tool_render_the_instruction`
- [tests/test_reread_safety.py](../../../../../../tests/test_reread_safety.py) — direct import
  - `test_a_margin_cue_marks_only_a_passage_whose_cited_words_are_there`
  - `test_the_guide_and_lo_highlights_survive_with_moved_passages_flagged`
- [tests/test_reread_safety_landing.py](../../../../../../tests/test_reread_safety_landing.py) — direct import
  - `test_a_cue_on_a_reread_resolves_the_cited_passage_and_shows_the_question_with_its_method`
- [tests/test_ux_phase1_landing.py](../../../../../../tests/test_ux_phase1_landing.py) — direct import
- [tests/test_ux_phase1_round2_review.py](../../../../../../tests/test_ux_phase1_round2_review.py) — direct import
- [tests/test_ux_phase1_usability_round1.py](../../../../../../tests/test_ux_phase1_usability_round1.py) — direct import
  - `test_u4_reading_through_a_section_moves_the_reading_step_on`

## Modification guidance

- Change reader guidance policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/reader_guidance.py](../../../../../../src/learnloop/reader/reader_guidance.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
