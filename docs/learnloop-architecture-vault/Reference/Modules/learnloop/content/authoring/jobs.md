---
title: "learnloop.content.authoring.jobs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/authoring/jobs.py"
source_paths:
  - "src/learnloop/content/authoring/jobs.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.authoring"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.authoring.jobs module"
  - "src/learnloop/content/authoring/jobs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-authoring"
---

# `learnloop.content.authoring.jobs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.authoring.jobs` exists within [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] to own the behavior summarized by its module contract: The Reader and authoring job types: Reader quick checks and exercise imports, a picked source exercise, practice expansion (with adaptive difficulty's commissions), goal population, question promotion, rung variants and concept animations, with the authoring clients the runner's…

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/authoring/jobs.py](../../../../../../../src/learnloop/content/authoring/jobs.py) |
| Source lines | 1141 |
| Owning package | [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `default_animation_client(ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 33) — Resolve the animation route (default: the medium-effort profile) — any configured provider works; run_concept_animation is getattr-discovered.
- `default_video_client(ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 40) — Resolve [ai.routing] video_generation to an OpenRouter video client.
- `default_rung_variant_client(ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 64) — Resolve the rung_variant route (default: the fast low-effort profile).
- `default_promotion_analysis_client(ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 74) — Fast classification/dedup pass for a durable promotion request.
- `default_promotion_authoring_client(ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 88) — Judgment-heavy practice generation follows the configured authoring route.
- `handle_reader_quick_check(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 102) — Author one section-boundary quick check (reader producer slice).
- `handle_reader_exercise_import(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 391) — reader_exercise_import: author the learner's selected textbook exercise(s) into complete, schedulable PracticeItems.
- `handle_source_exercise_import(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 505) — source_exercise_import: a learner picked a textbook exercise proposal (canonical sources S1, §7.2).
- `ad_commission_batch_id(commission_id: str) -> str` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 552) — The one durable batch of an adaptive difficulty commission's generation (the store's name for it: a commission's expiry reads its job, Codex review F5).
- `ad_commission_skip_record(*, commission_id: Any, job_id: Any, rule: str) -> Any` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 571) — Why a commission's job generated nothing (pure): ``commission_closed`` (it landed or expired), ``view_unavailable`` (AD's held-out predicate couldn't be read) or ``guard_denied`` (AD's guard refused a read; the denial itself is in ``ad_guard_denials.jsonl``).
- `handle_practice_expansion(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 683) — practice_expansion: per-LO item generation (reader-first seeding).
- `handle_goal_population(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 846) — Generate and apply the missing practicable supply for one active goal.
- `handle_question_promotion(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 937) — Run one persisted Open-question → practice request.
- `handle_rung_variant(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 1036) — rung_variant: author one learner-requested easier/harder sibling item.
- `handle_concept_animation(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 1068) — concept_animation: author + validate + render one explainer scene.

### Module constants

- `INQUIRY_HELD_POLL_SECONDS` ([src/learnloop/content/authoring/jobs.py](../../../../../../../src/learnloop/content/authoring/jobs.py), line 225)
- `INQUIRY_HELD_MAX_POLLS` ([src/learnloop/content/authoring/jobs.py](../../../../../../../src/learnloop/content/authoring/jobs.py), line 226)
- `_ENDED_JOB_STATUSES` ([src/learnloop/content/authoring/jobs.py](../../../../../../../src/learnloop/content/authoring/jobs.py), line 228)
- `AD_MODELS_OFF_CODE` ([src/learnloop/content/authoring/jobs.py](../../../../../../../src/learnloop/content/authoring/jobs.py), line 564)
- `AD_COMMISSION_SKIP` ([src/learnloop/content/authoring/jobs.py](../../../../../../../src/learnloop/content/authoring/jobs.py), line 568)

## Internal implementation anchors

- `_reader_source_sets(vault_root: Path) -> Any` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 132) — The vault, read when a Reader request is sent (the held-out partition reads its source sets; exam protection, Codex review F3).
- `_refuse_held_out_reader_material(ctx: JobContext, extraction_id: str, span_ids: Sequence[str]) -> None` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 147) — Exam protection (2026-10-13): a Reader check over held-out material (the one held-out partition, read with the vault's source sets) is refused before any model call, and before a check authored before the mark is handed back (code ``exam_material``).
- `_section_span_ids(repository: Repository, extraction_id: str, section_id: str) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 162) — Every block of one guide section (the quick check's own derivation), or [].
- `_passage_span_ids(repository: Repository, extraction_id: str, anchors: Sequence[str]) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 172) — The anchors and every block of the passage check's view of them.
- `_paid_quick_check_client(ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 182) — The client of a paid passage check (an inquiry's or a selection's), resolved for that feature.
- `_exercise_import_client(ctx: JobContext) -> Any` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 197) — The authoring client of an exercise import, resolved for that feature (re-review F2).
- `_passage_check_spend(ctx: JobContext) -> RQC.PassageCheckSpend` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 212) — The vault's admission settings for one passage check ([reader_inquiry]).
- `_pause_while_inquiry_held(ctx: JobContext, seconds: float) -> None` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 231) — Wait between polls of a held inquiry claim (a seam for tests).
- `_inquiry_owner_ended(repo: Repository, owner: str) -> bool` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 237) — True when the claim's owner is an ingest job that has finished: it was expired, failed or cancelled after claiming, so its claim is abandoned.
- `_handle_reader_inquiry_check(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 246) — RW1a: author the reconnect line's quick check for one inquiry's root passage.
- `_handle_reader_selection_check(ctx: JobContext) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 320) — RW1b: author one active-reading question on a selection (next step, why step, assumptions, reconstruct).
- `_record_reader_import_keys(ctx: JobContext, result: dict[str, Any], *, extraction_id: str, span_ids: list[str], source_id: str | None, revision_id: str | None) -> None` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 459) — Canonical sources S1 (§7.3a): the Reader's import records its key status.
- `_verify_quietly(root: Path, repository: Repository, rows: list[dict[str, str]], trigger: str) -> None` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 493)
- `_record_commission_skip(ctx: JobContext, commission_id: str, rule: str) -> None` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 597) — Write :func:`ad_commission_skip_record` in a short transaction of its own, outside every AD operation; never raises.
- `_handle_ad_commission(ctx: JobContext, lo_ids: list[str], commission_id: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 613) — One item at an open AD commission's point, through the ordinary generation path and its gates (spec_adaptive_difficulty_v1 §6.1 "runs in the background", §7.1, §7.4).
- `class _TopicWork` ([source](../../../../../../../src/learnloop/content/authoring/jobs.py), line 781) — The topic-work rows a practice_expansion job writes for (``topic_keys`` in its payload): their checkpoint scopes, the proposals earlier waves of their sections applied, and their state as the parts land.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `AD_MODELS_OFF_CODE`, `_reader_source_sets`, `ad_commission_batch_id`; statically calls `_reader_source_sets`, `ad_commission_batch_id`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/generation|learnloop.adaptive_difficulty.generation]] — imports `contract_on`; calls `contract_on`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `ad_operation`, `is_denial`; calls `ad_operation`, `is_denial`
- [[Reference/Modules/learnloop/adaptive_difficulty/spend|learnloop.adaptive_difficulty.spend]] — imports `models_off`; calls `models_off`
- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `make_video_generation_client`; calls `make_video_generation_client`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIProviderUnavailable`, `CodexTurnTimeout`, `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `ModelCheckpoint`, `model_settings`; calls `ModelCheckpoint`, `model_settings`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `priced_by`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]] — imports `ConceptAnimationError`, `generate_concept_animation`; calls `generate_concept_animation`
- [[Reference/Modules/learnloop/content/authoring/draft_validation|learnloop.content.authoring.draft_validation]] — imports `draft_validator`, `duration_estimator`; calls `draft_validator`, `duration_estimator`
- [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] — imports `module`; calls `import_exercises`, `selected_span_ids`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `PracticeExpansionError`, `build_goal_practice_plan`, `generate_goal_practice_proposal`, `generate_post_probe_practice_proposal`, `section_questions_key`; calls `build_goal_practice_plan`, `generate_goal_practice_proposal`, `generate_post_probe_practice_proposal`, `section_questions_key`
- [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] — imports `RungVariantError`, `generate_rung_variant`; calls `generate_rung_variant`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `PRICE_SETTING`, `module`; calls `import_source_exercise`, `record_reader_import`, `verify_item_key`
- [[Reference/Modules/learnloop/content/pipeline/job_contracts|learnloop.content.pipeline.job_contracts]] — imports `IngestRunnerError`, `JobCancelled`; calls `IngestRunnerError`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `JobContext`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `PatchApplicationError`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `accept_items`; calls `accept_items`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `SourceSetsUnreadable`, `held_out_among`, `held_out_refusal`, `scope_only_among`, `surface_material`; calls `SourceSetsUnreadable`, `held_out_among`, `held_out_refusal`, `scope_only_among`, `surface_material`
- [[Reference/Modules/learnloop/content/synthesis/jobs|learnloop.content.synthesis.jobs]] — imports `_routed_task_client`; calls `_routed_task_client`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/ad_serving|learnloop.db.stores.ad_serving]] — imports `commission_batch_id`; calls `commission_batch_id`
- [[Reference/Modules/learnloop/db/stores/provenance|learnloop.db.stores.provenance]] — imports `write_decision`; calls `write_decision`
- [[Reference/Modules/learnloop/provenance|learnloop.provenance]] — imports `module`; calls `DecisionRecord`, `current_trace`, `is_code`
- [[Reference/Modules/learnloop/reader/part_read|learnloop.reader.part_read]] — imports `module`; calls `seen_text_filter`
- [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] — imports `module`; calls `author_inquiry_quick_check`, `author_quick_check`, `author_selection_question`, `extraction_sections`, `passage_check_spend`, `passage_view`, `selection_question`, `selection_view`
- [[Reference/Modules/learnloop/reader/section_generation|learnloop.reader.section_generation]] — imports `module`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `sync_vault_state`; calls `sync_vault_state`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `PromotionError`, `PromotionNoItemError`, `promote_tutor_question`; calls `promote_tutor_question`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `logging`, `pathlib`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/protection_matrix_helpers.py](../../../../../../../tests/protection_matrix_helpers.py) — direct import
- [tests/test_curriculum_c3_codex_review.py](../../../../../../../tests/test_curriculum_c3_codex_review.py) — direct import
  - `test_the_reader_s_own_import_refuses_a_syllabus_before_any_model_call`
- [tests/test_exam_protection.py](../../../../../../../tests/test_exam_protection.py) — direct import
- [tests/test_exam_protection_review.py](../../../../../../../tests/test_exam_protection_review.py) — direct import
  - `test_a_reader_import_of_a_held_out_signal_is_refused`
- [tests/test_import_split_parity.py](../../../../../../../tests/test_import_split_parity.py) — direct import
  - `test_the_reader_job_records_an_import_row_and_leaves_the_item_unchanged`
- [tests/test_job_types.py](../../../../../../../tests/test_job_types.py) — direct import
  - `test_the_job_contracts_are_one_set_of_objects_through_every_path`
- [tests/test_library_exercises.py](../../../../../../../tests/test_library_exercises.py) — direct import
  - `test_r2_contract_no_workbench_or_reader_exercise_rpc_returns_a_held_out_statement`
  - `test_r6_verify_f7_a_finished_exercise_job_read_after_its_region_is_held_out_never_delivers_it`
- [tests/test_plan_first_transport.py](../../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_rr_f2_a_feature_that_needs_its_own_price_is_not_served_by_another_features_grant`
- [tests/test_plan_first_transport_grant_scope.py](../../../../../../../tests/test_plan_first_transport_grant_scope.py) — direct import
  - `test_the_reader_imports_background_key_check_never_uses_the_grant`
- [tests/test_protection_surface_matrix.py](../../../../../../../tests/test_protection_surface_matrix.py) — direct import
  - `test_the_reader_imports_author_keeps_a_safe_neighbour`
- [tests/test_reader_active_reading.py](../../../../../../../tests/test_reader_active_reading.py) — direct import
  - `test_the_job_refuses_held_out_material_before_any_call`
  - `test_the_job_writes_the_question_once`
- [tests/test_reader_passage_check.py](../../../../../../../tests/test_reader_passage_check.py) — direct import
  - `test_a_check_held_by_a_live_job_waits_for_it_and_returns_its_question`
  - `test_a_check_held_past_the_wait_fails_retryably_and_never_completes_without_a_question`
  - `test_a_claim_left_by_a_crashed_job_is_taken_over_by_the_next_job_at_once`
  - `test_a_second_request_while_one_is_live_joins_its_job`
  - `test_a_spend_refusal_says_whether_the_price_is_missing_or_the_check_is_over_its_cap`
  - `test_the_job_fails_closed_with_a_named_reason_when_isolation_is_unavailable`
  - `test_the_job_reports_a_refusal_as_its_error_code_and_sends_nothing`
  - `test_the_vaults_spend_settings_reach_the_check`
- [tests/test_reader_reconnect.py](../../../../../../../tests/test_reader_reconnect.py) — direct import
  - `test_quick_check_job_authors_the_inquiry_row`
- [tests/test_reading_hardening_landing.py](../../../../../../../tests/test_reading_hardening_landing.py) — direct import
  - `test_the_section_check_job_still_refuses_held_out_material`
- [tests/test_remaining_decision_records.py](../../../../../../../tests/test_remaining_decision_records.py) — direct import
  - `test_a_commission_job_that_generated_nothing_says_why`
  - `test_every_b8_builder_passes_the_prose_check_with_learner_text_planted`
- [tests/test_rw1a_composition.py](../../../../../../../tests/test_rw1a_composition.py) — direct import
  - `test_the_vaults_route_effort_reaches_the_check`
- [tests/test_sidecar_animation.py](../../../../../../../tests/test_sidecar_animation.py) — direct import
  - `test_request_generates_and_status_reports_completed`
  - `test_video_renderer_request_completes_through_the_queue`
- [tests/test_source_exercise_rpcs.py](../../../../../../../tests/test_source_exercise_rpcs.py) — direct import
- [tests/test_ux_phase1_landing.py](../../../../../../../tests/test_ux_phase1_landing.py) — direct import
  - `test_a_queued_passage_check_runs_for_a_book_with_the_retired_keep_local`

## Modification guidance

- Change jobs policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/authoring/jobs.py](../../../../../../../src/learnloop/content/authoring/jobs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
