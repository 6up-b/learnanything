---
title: "learnloop.tutor.promotions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/tutor/promotions.py"
source_paths:
  - "src/learnloop/tutor/promotions.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.tutor"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Tutor and Teach-Back Workflow"
aliases:
  - "learnloop.tutor.promotions module"
  - "src/learnloop/tutor/promotions.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-tutor"
---

# `learnloop.tutor.promotions`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.tutor.promotions` exists within [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] to own the behavior summarized by its module contract: Promote a socratic tutor question into practice / a gap need (spec_tutor_promotion.md §3).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/tutor/promotions.py](../../../../../../src/learnloop/tutor/promotions.py) |
| Source lines | 1180 |
| Owning package | [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `request_promotion_analysis(client: OperationClient, context: PromotionAnalysisContext) -> PromotionAnalysis` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 51) — Run the feature-owned tutor-promotion analysis operation.
- `class PromotionError(ValueError)` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 67)
- `class PromotionNoItemError(PromotionError)` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 71) — The authoring turn completed but proposed no practice item.
- `promotion_target_ids(vault: LoadedVault, repository: Repository, event: dict[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 75) — Deterministic LO choices available to a question promotion.
- `promote_tutor_question(root: Path, client: Any, *, event_id: str, intent: str, subject_id: str | None=None, learning_object_id: str | None=None, authoring_client: Any | None=None, authoring_client_factory: Callable[[], Any] | None=None, progress: Callable[[str], None] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 181) — Promote one answered tutor turn (spec_tutor_promotion.md §3).
- `reconcile_accepted_question_promotion_patch(repository: Repository, patch_id: str, *, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 377) — Make accepted reviewed items consume their original promotion request.
- `reconcile_rejected_question_promotion_patch(repository: Repository, patch_id: str, *, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 432) — Expose a fully rejected practice proposal as a retryable request failure.
- `reconcile_reset_question_promotion_patch(repository: Repository, patch_id: str, *, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 468) — Restore the awaiting-review request state after undoing a rejection.

### Module constants

- `_TUTOR_PROMOTED_TAG` ([src/learnloop/tutor/promotions.py](../../../../../../src/learnloop/tutor/promotions.py), line 47)
- `_TRANSFER_NATURES` ([src/learnloop/tutor/promotions.py](../../../../../../src/learnloop/tutor/promotions.py), line 48)

## Internal implementation anchors

- `_reader_anchor(event: dict[str, Any]) -> tuple[str, str] | None` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 118)
- `_suggestion_note(vault: LoadedVault, event: dict[str, Any]) -> str` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 132) — Name a recorded nearest-LO suggestion (Slice 2 T6), labelled as one.
- `_reader_target_ids(vault: LoadedVault, repository: Repository, event: dict[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 152)
- `_reader_source_refs(vault: LoadedVault, repository: Repository, event: dict[str, Any], origin_lo: LearningObject | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 158)
- `_run_promotion_analysis(client: Any, vault: LoadedVault, origin_lo: LearningObject | None, thread: list[dict[str, Any]], intent: str, *, subject_id: str | None=None) -> PromotionAnalysis` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 502) — Step-0 structured extraction; degrades to an empty analysis when unavailable.
- `_promote_existing_item(root: Path, repository: Repository, vault: LoadedVault, *, event: dict[str, Any], intent: str, analysis: PromotionAnalysis, attributed: list[str], origin_lo: LearningObject | None, existing_item_id: str, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 553) — Dedup route: schedule the existing item; gap intent still writes the claim (§3 Step 0).
- `_promote_practice(root: Path, repository: Repository, vault: LoadedVault, client: Any, *, event: dict[str, Any], analysis: PromotionAnalysis, attributed: list[str], origin_lo: LearningObject | None, saved_note_id: str, reader_source_refs: list[dict[str, Any]] | None, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 599) — Practice route: author a practice item, enforcing routing in code (§3 Steps 2-3).
- `_promote_gap(root: Path, repository: Repository, vault: LoadedVault, client: Any, *, event: dict[str, Any], analysis: PromotionAnalysis, attributed: list[str], origin_lo: LearningObject, saved_note_id: str, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 711) — Gap route: self-report claim + intervention need + inline diagnostic gen (§3 Step 2.5).
- `_write_gap_claim(repository: Repository, vault: LoadedVault, origin_lo: LearningObject, attributed: list[str], *, event_id: str, clock: Clock | None) -> str` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 778) — G2 self-report: a low ``tutor_gap_declaration`` claim scoped to the LO / facet.
- `_gap_claim_key(event_id: str) -> str` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 852) — The idempotency suffix of a gap claim's id: the question event it came from.
- `_file_gap_need(repository: Repository, *, origin_lo: LearningObject, attributed: list[str], analysis: PromotionAnalysis, event: dict[str, Any], clock: Clock | None) -> str` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 858) — G3 instrument authoring: file a ``tutor_gap_declaration`` intervention need.
- `_thread_from_event(event: dict[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 900) — The promoted turn as a one-item thread for the need's steering context.
- `_record_promotion_decision_features(repository: Repository, vault: LoadedVault, *, event: dict[str, Any], origin_lo: LearningObject | None, analysis: PromotionAnalysis, attributed: list[str], intent: str, outcome: str, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 912) — Log the promotion training signal (§3 Step 4 / §0 fitting contract).
- `_origin_mastery(repository: Repository, origin_lo: LearningObject | None) -> tuple[float | None, float | None]` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 972)
- `_recommended_difficulty_band(vault: LoadedVault, mastery_mean: float | None) -> tuple[float, float]` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 984) — Mode-ladder difficulty band (§3 Step 2.6) — reuses the expansion planner math.
- `_promotion_instructions(vault: LoadedVault, repository: Repository, origin_lo: LearningObject | None, analysis: PromotionAnalysis, attributed: list[str], event: dict[str, Any]) -> str` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 1007) — TUTOR_PROMOTION_PROMPT + the PROMOTION_CONTEXT payload (thread, origin, band).
- `_promotion_source_refs(vault: LoadedVault, saved_note_id: str, origin_lo: LearningObject | None, *, additional_refs: list[dict[str, Any]] | None=None) -> tuple[list[dict[str, Any]], bool]` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 1052) — Grounding note + authoritative source material.
- `_promotion_subjects(vault: LoadedVault, origin_lo: LearningObject | None, saved_note_id: str) -> list[str] | None` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 1090)
- `_created_entities(repository: Repository, patch_id: str) -> tuple[str | None, str | None, bool, bool]` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 1101) — (created_practice_item_id, created_learning_object_id, auto_applied, has_lo_create).
- `_origin_facet_vocabulary(vault: LoadedVault, origin_lo: LearningObject) -> list[str]` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 1125)
- `_origin_existing_items(vault: LoadedVault, origin_lo: LearningObject) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 1136)
- `_concept_neighbors(vault: LoadedVault, origin_lo: LearningObject) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/promotions.py), line 1153)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `reconcile_accepted_question_promotion_patch`, `reconcile_rejected_question_promotion_patch`; statically calls `reconcile_accepted_question_promotion_patch`, `reconcile_rejected_question_promotion_patch`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `PromotionError`, `PromotionNoItemError`, `promote_tutor_question`; statically calls `promote_tutor_question`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]] — imports `PromotionNoItemError`, `promote_tutor_question`; statically calls `promote_tutor_question`
- [[Reference/Modules/learnloop/tutor/question_queue|learnloop.tutor.question_queue]] — imports `promotion_target_ids`; statically calls `promotion_target_ids`
- [[Reference/Modules/learnloop_sidecar/handlers/proposals|learnloop_sidecar.handlers.proposals]] — imports `reconcile_accepted_question_promotion_patch`, `reconcile_rejected_question_promotion_patch`, `reconcile_reset_question_promotion_patch`; statically calls `reconcile_accepted_question_promotion_patch`, `reconcile_rejected_question_promotion_patch`, `reconcile_reset_question_promotion_patch`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `OperationClient`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/authoring/authoring_gates|learnloop.content.authoring.authoring_gates]] — imports `build_instrument_gates`; calls `build_instrument_gates`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `PracticeExpansionError`, `ability_logit`, `generate_diagnostic_practice_proposal`, `success_band_difficulty`; calls `ability_logit`, `generate_diagnostic_practice_proposal`, `success_band_difficulty`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `generate_authoring_proposal`; calls `generate_authoring_proposal`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `claim_fixes_live`, `display_mastery`, `reanchor_mastery_from_claim`; calls `claim_fixes_live`, `display_mastery`, `reanchor_mastery_from_claim`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `learning_objects_for_span`, `source_refs_for_span`; calls `learning_objects_for_span`, `source_refs_for_span`
- [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]] — imports `PromotionAnalysis`, `PromotionAnalysisContext`, `TUTOR_PROMOTION_PROMPT`, `promotion_analysis_prompt`; calls `PromotionAnalysis`, `PromotionAnalysisContext`, `promotion_analysis_prompt`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `_thread`, `build_tutor_qa_note`, `delivered_answer_md`; calls `_thread`, `build_tutor_qa_note`, `delivered_answer_md`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LearningObject`, `LoadedVault`, `learning_object_facet_union`; calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `vault_repository`; calls `vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Tutor and Teach-Back Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]], [[Reference/Modules/learnloop/tutor/question_queue|learnloop.tutor.question_queue]], [[Reference/Modules/learnloop_sidecar/handlers/proposals|learnloop_sidecar.handlers.proposals]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/lp_claim_fixes_review_helpers.py](../../../../../../tests/lp_claim_fixes_review_helpers.py) — direct import
- [tests/test_difficulty_band_guards.py](../../../../../../tests/test_difficulty_band_guards.py) — direct import
  - `test_promotion_band_is_floored_like_the_expansion_planner`
  - `test_promotion_band_unchanged_at_ordinary_mastery`
- [tests/test_lp_claim_fixes.py](../../../../../../tests/test_lp_claim_fixes.py) — direct import
- [tests/test_source_retrieval_tutor.py](../../../../../../tests/test_source_retrieval_tutor.py) — direct import
  - `test_a_reader_question_records_the_suggestion_and_promotion_names_it`
- [tests/test_structured_transport_parity.py](../../../../../../tests/test_structured_transport_parity.py) — direct import
- [tests/test_tutor_promotion_service.py](../../../../../../tests/test_tutor_promotion_service.py) — direct import
  - `test_accepting_reviewed_promotion_makes_original_request_schedulable`
  - `test_attach_to_existing_with_grounding_auto_applies`
  - `test_dedup_short_circuit_gap_writes_claim_no_need`
  - `test_dedup_short_circuit_practice`
  - `test_gap_inline_diagnostic_generation_when_available`
  - `test_gap_need_dedup_links_existing_need`
  - `test_gap_route_transfer_nature_biases_intent`
  - `test_gap_route_writes_claim_need_and_diagnostic_pending`
  - `test_grounding_fallback_forces_review`
  - `test_idempotent_returns_existing_row`
  - `test_library_gap_rejected`
  - `test_new_lo_batch_forced_review`
  - `test_practice_promotion_with_no_authored_item_fails_instead_of_claiming_review`
  - `test_reader_promotion_honors_persisted_learning_object_target`
  - `test_reader_promotion_uses_subject_facet_vocabulary_without_origin_item`
  - `test_rejecting_and_resetting_review_updates_promotion_request_state`

## Modification guidance

- Change promotions policy here when tutor owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/tutor/promotions.py](../../../../../../src/learnloop/tutor/promotions.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
