---
title: "learnloop.content.authoring.exercise_authoring"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/authoring/exercise_authoring.py"
source_paths:
  - "src/learnloop/content/authoring/exercise_authoring.py"
source_commit: "9b98bccfa9bc08339fe3103643d0d6fc6fd459a6"
source_commit_timestamp: "2026-11-01T14:48:10-05:00"
source_worktree_state: "clean"
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
  - "learnloop.content.authoring.exercise_authoring module"
  - "src/learnloop/content/authoring/exercise_authoring.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-authoring"
---

# `learnloop.content.authoring.exercise_authoring`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.authoring.exercise_authoring` exists within [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] to own the behavior summarized by its module contract: Reader exercise import: selected textbook exercises become real PracticeItems.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/authoring/exercise_authoring.py](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py) |
| Source lines | 963 |
| Owning package | [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `9b98bccfa9bc08339fe3103643d0d6fc6fd459a6` |
| Commit timestamp | `2026-11-01T14:48:10-05:00` |

## Public API

- `class ExerciseAuthoringError(ValueError)` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 106) — Domain error for the reader exercise-import producer.
- `request_exercise_authoring(client: StructuredTransport, context: ExerciseAuthoringContext, *, admit: Callable[[str, type[ExerciseAuthoring]], AbstractContextManager[Any]] | None=None) -> ExerciseAuthoring` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 110) — Author selected exercises through the shared transport.
- `class AuthoredDraft` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 447) — One authored exercise, validated and ready to write (nothing written yet).
- `class AuthoredBatch` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 461) — ``author_exercises``' result: drafts plus today's skipped/warnings report.
- `author_exercises(root: Path, repository: Repository, client: Any, *, extraction_id: str, raw_selection: Mapping[str, Any], render_view_id: str | None=None, source_id: str | None=None, revision_id: str | None=None, learning_object_hint: str | None=None, clock: Clock | None=None, book_solution: Mapping[str, Any] | None=None, admit: Callable[[str, type[ExerciseAuthoring]], AbstractContextManager[Any]] | None=None, method_judge: Any=None, method_judge_owner: tuple[str, str] | None=None) -> AuthoredBatch` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 473) — Author the selected exercise(s) into validated drafts.
- `write_draft(root: Path, repository: Repository, draft: AuthoredDraft, *, extraction_id: str, clock: Clock | None=None, mechanism: str='reader_exercise_import', extra_payload: Mapping[str, Any] | None=None) -> str` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 876) — Write one draft as a vault item and mark it with ``learner_item_authored``.
- `write_exercises(root: Path, repository: Repository, batch: AuthoredBatch, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 913) — Write every draft of ``batch`` (the Reader import's write step).
- `import_exercises(root: Path, repository: Repository, client: Any, *, extraction_id: str, raw_selection: Mapping[str, Any], render_view_id: str | None=None, source_id: str | None=None, revision_id: str | None=None, learning_object_hint: str | None=None, clock: Clock | None=None, method_judge: Any=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 933) — Author the learner's selected exercise(s) into schedulable PracticeItems.

### Module constants

- `MAX_CONTEXT_BLOCKS` ([src/learnloop/content/authoring/exercise_authoring.py](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 76)
- `MAX_CONTEXT_CHARS` ([src/learnloop/content/authoring/exercise_authoring.py](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 77)
- `MAX_CATALOG_OBJECTS` ([src/learnloop/content/authoring/exercise_authoring.py](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 78)
- `MAX_HINTS` ([src/learnloop/content/authoring/exercise_authoring.py](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 79)
- `_DEFAULT_RUBRIC` ([src/learnloop/content/authoring/exercise_authoring.py](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 81)
- `READER_IMPORT_OWNER_KIND` ([src/learnloop/content/authoring/exercise_authoring.py](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 94)
- `STIMULUS` ([src/learnloop/content/authoring/exercise_authoring.py](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 250)
- `_SOLUTION_FIGURE_ROLES` ([src/learnloop/content/authoring/exercise_authoring.py](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 253)
- `_CLAIM_STRENGTH` ([src/learnloop/content/authoring/exercise_authoring.py](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 259)

## Internal implementation anchors

- `_configured_method_judge(vault: LoadedVault) -> Any` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 97) — The one-time statement judge from configuration, resolved on first use.
- `_normalize(text: str) -> str` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 148)
- `_clamp01(value: Any) -> float | None` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 152)
- `_anchor_range(selection_text: str, statement: str) -> tuple[int, int] | None` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 158) — Where the model's echoed statement sits in the learner's selection, as a verbatim slice (whitespace-tolerant, same idea as annotation quote relocation); None for a paraphrase.
- `_anchor_statement(selection_text: str, statement: str) -> str | None` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 173) — Re-anchor the model's echoed statement as a verbatim slice of the learner's selection.
- `_owned_spans(part_ranges: Sequence[tuple[str, int, int]] | None, ranges: Sequence[tuple[int, int] | None], index: int, *, span_ids: Sequence[str]=(), text_length: int | None=None) -> set[str]` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 181) — Reader CA1 (Codex re-review F9, final verify F9; Astra batch review, owner 2026-10-26): the blocks one item is printed from, when they are its alone.
- `_item_refs(source_refs: Sequence[Mapping[str, Any]], span_ids: Sequence[str], *, owned: set[str], figures: Mapping[str, tuple[str, str | None]] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 223) — One item's copy of the selection's refs.
- `_claimed_roles(entry: ExerciseAuthoredItem) -> dict[str, str]` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 262) — The author's role per figure span for one item.
- `_answer_figures(entries: Sequence[ExerciseAuthoredItem]) -> set[str]` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 275) — Every figure some claim of some item calls an ``answer`` or ``worked`` (Sol verify 1: read from every claim, never from one resolved role per item), so it is no item's stimulus.
- `_figure_roles(claimed: Mapping[str, str], figures: Mapping[str, str | None], statement: str, *, claimed_elsewhere: set[str]) -> dict[str, tuple[str, str | None]]` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 284) — Reader CA1 (the Astra redesign): each selected figure's role for one item, (role, why a stimulus claim was refused).
- `_context_blocks(ir: Any, span_ids: list[str]) -> list[dict[str, str]]` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 316) — The covered blocks plus one neighbor on each side, in document order.
- `_catalog(vault: LoadedVault, hint: str | None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 345) — The bounded LO catalog the model maps into: id, title, summary, and the canonical facet vocabulary each object exposes.
- `_validated_rubric(payload: Any) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 376) — Admit the model rubric only when the arithmetic holds (points sum to a positive integer, unique non-empty criteria); otherwise the caller falls back to the plain correctness rubric.
- `_normalized_weights(raw: Mapping[str, float], facets: list[str], canonical: Any) -> dict[str, float]` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 408) — Normalize only facet links the author actually asserted.
- `_uniform_criterion_smear(criterion_weights: Mapping[str, Mapping[str, float]]) -> bool` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 429) — Whether multiple criteria received the same multi-facet distribution.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `AuthoredDraft`, `ExerciseAuthoringError`, `author_exercises`, `write_draft`; statically calls `AuthoredDraft`, `ExerciseAuthoringError`, `author_exercises`, `write_draft`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `module`; statically calls `import_exercises`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIOutputTruncated`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `StructuredTransport`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/authoring/ai_contracts|learnloop.content.authoring.ai_contracts]] — imports `ExerciseAuthoredItem`, `ExerciseAuthoring`, `ExerciseAuthoringContext`, `FIGURE_ROLE_INSTRUCTIONS`, `exercise_authoring_prompt`; calls `ExerciseAuthoringContext`, `exercise_authoring_prompt`
- [[Reference/Modules/learnloop/content/proposals/method_statement_judge|learnloop.content.proposals.method_statement_judge]] — imports `LazyStatementJudge`, `resolve_statement_judge`, `source_judge`; calls `LazyStatementJudge`, `resolve_statement_judge`, `source_judge`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `SCOPE_ONLY_REFUSAL`, `reference_keys`, `scope_only_among`; calls `reference_keys`, `scope_only_among`
- [[Reference/Modules/learnloop/content/sources/math_text|learnloop.content.sources.math_text]] — imports `contains_unicode_math`, `unicode_math_to_latex`; calls `contains_unicode_math`, `unicode_math_to_latex`
- [[Reference/Modules/learnloop/curriculum/depth_rungs|learnloop.curriculum.depth_rungs]] — imports `TASK_FEATURE_SCHEMA_SLUG`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ingest/block_roles|learnloop.ingest.block_roles]] — imports `FIGURE_ANSWER_ROLES`, `FIGURE_REJECTED_ANOTHER_ANSWER`, `FIGURE_REJECTED_NUMBER_MISMATCH`, `figure_numbers`; calls `figure_numbers`
- [[Reference/Modules/learnloop/ingest/ir|learnloop.ingest.ir]] — imports `is_figure_block`, `selection_region`; calls `is_figure_block`, `selection_region`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `BLOCK_SPAN_V1`, `format_block_span`; calls `format_block_span`
- [[Reference/Modules/learnloop/reader/annotations|learnloop.reader.annotations]] — imports `translate_selection`; calls `translate_selection`
- [[Reference/Modules/learnloop/substrate/activity_patterns|learnloop.substrate.activity_patterns]] — imports `LEGACY_UNMAPPED`, `ensure_builtin_task_feature_schema`, `ensure_capability_alias_registry`, `map_capability`, `validate_task_features`; calls `ensure_builtin_task_feature_schema`, `ensure_capability_alias_registry`, `map_capability`, `validate_task_features`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `learning_object_facet_union`; calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `learning_object_method_targets`, `method_targets`, `normalize_required_method`; calls `learning_object_method_targets`, `method_targets`, `normalize_required_method`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `upsert_practice_item`; calls `upsert_practice_item`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `json`, `pathlib`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_curriculum_c3_codex_review.py](../../../../../../../tests/test_curriculum_c3_codex_review.py) — direct import
  - `test_the_one_write_refuses_a_syllabus_draft`
- [tests/test_exercise_authoring.py](../../../../../../../tests/test_exercise_authoring.py) — direct import
  - `test_edited_capture_quote_becomes_the_exercise_surface`
  - `test_import_dedupes_identical_prompt_on_second_run`
  - `test_selection_level_edited_text_overrides_combined_surface`
  - `test_unresolvable_selection_raises`
- [tests/test_import_split_parity.py](../../../../../../../tests/test_import_split_parity.py) — direct import
  - `test_author_then_write_writes_what_import_exercises_writes`
- [tests/test_openrouter_client.py](../../../../../../../tests/test_openrouter_client.py) — direct import
  - `test_openrouter_supports_exercise_authoring`
- [tests/test_reader_ca1_astra_codex_review.py](../../../../../../../tests/test_reader_ca1_astra_codex_review.py) — direct import
- [tests/test_reader_ca1_astra_fixes.py](../../../../../../../tests/test_reader_ca1_astra_fixes.py) — direct import
  - `test_a_selection_level_edit_of_the_whole_passage_never_crops_the_solution`
- [tests/test_reader_ca1_astra_redesign.py](../../../../../../../tests/test_reader_ca1_astra_redesign.py) — direct import
  - `test_a_duplicate_answer_claim_is_never_lost`
  - `test_a_sibling_never_owns_a_figure_one_item_calls_its_answer_among_duplicates`
  - `test_a_split_never_gives_one_item_a_figure_another_calls_its_answer`
  - `test_every_rejection_reason_the_validator_emits_is_classified`
  - `test_figure_roles_are_validated_never_widened`
  - `test_two_claims_for_one_figure_resolve_away_from_stimulus`
- [tests/test_reader_ca1_astra_rereview.py](../../../../../../../tests/test_reader_ca1_astra_rereview.py) — direct import
- [tests/test_reader_ca1_codex_review.py](../../../../../../../tests/test_reader_ca1_codex_review.py) — direct import
  - `test_a_split_over_disjoint_and_shared_blocks_withholds_only_the_sharing_items_crop`
  - `test_a_split_with_an_unanchored_sibling_owns_nothing`
  - `test_two_exercises_split_from_one_block_get_no_free_crop_and_keep_the_page`
- [tests/test_reader_ca1_unicode_containment.py](../../../../../../../tests/test_reader_ca1_unicode_containment.py) — direct import
- [tests/test_required_method_authority.py](../../../../../../../tests/test_required_method_authority.py) — direct import
- [tests/test_required_method_items.py](../../../../../../../tests/test_required_method_items.py) — direct import
  - `test_an_imported_exercise_keeps_a_required_method_only_by_its_one_time_judgment`
- [tests/test_structured_transport_parity.py](../../../../../../../tests/test_structured_transport_parity.py) — direct import

## Modification guidance

- Change exercise authoring policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/authoring/exercise_authoring.py](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
