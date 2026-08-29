---
title: "learnloop.content.authoring.exercise_authoring"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/authoring/exercise_authoring.py"
source_paths:
  - "src/learnloop/content/authoring/exercise_authoring.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
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
| Source lines | 588 |
| Owning package | [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ExerciseAuthoringError(ValueError)` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 75) — Domain error for the reader exercise-import producer.
- `request_exercise_authoring(client: StructuredTransport, context: ExerciseAuthoringContext) -> ExerciseAuthoring` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 79) — Author selected exercises through the shared transport.
- `import_exercises(root: Path, repository: Repository, client: Any, *, extraction_id: str, raw_selection: Mapping[str, Any], render_view_id: str | None=None, source_id: str | None=None, revision_id: str | None=None, learning_object_hint: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 241) — Author the learner's selected exercise(s) into schedulable PracticeItems.

### Module constants

- `MAX_CONTEXT_BLOCKS` ([src/learnloop/content/authoring/exercise_authoring.py](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 58)
- `MAX_CONTEXT_CHARS` ([src/learnloop/content/authoring/exercise_authoring.py](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 59)
- `MAX_CATALOG_OBJECTS` ([src/learnloop/content/authoring/exercise_authoring.py](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 60)
- `MAX_HINTS` ([src/learnloop/content/authoring/exercise_authoring.py](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 61)
- `_DEFAULT_RUBRIC` ([src/learnloop/content/authoring/exercise_authoring.py](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 63)

## Internal implementation anchors

- `_normalize(text: str) -> str` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 92)
- `_clamp01(value: Any) -> float | None` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 96)
- `_anchor_statement(selection_text: str, statement: str) -> str | None` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 102) — Re-anchor the model's echoed statement as a verbatim slice of the learner's selection (whitespace-tolerant, same idea as annotation quote relocation).
- `_context_blocks(ir: Any, span_ids: list[str]) -> list[dict[str, str]]` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 117) — The covered blocks plus one neighbor on each side, in document order.
- `_catalog(vault: LoadedVault, hint: str | None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 146) — The bounded LO catalog the model maps into: id, title, summary, and the canonical facet vocabulary each object exposes.
- `_validated_rubric(payload: Any) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 171) — Admit the model rubric only when the arithmetic holds (points sum to a positive integer, unique non-empty criteria); otherwise the caller falls back to the plain correctness rubric.
- `_normalized_weights(raw: Mapping[str, float], facets: list[str], canonical: Any) -> dict[str, float]` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 203) — Normalize only facet links the author actually asserted.
- `_uniform_criterion_smear(criterion_weights: Mapping[str, Mapping[str, float]]) -> bool` ([source](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py), line 224) — Whether multiple criteria received the same multi-facet distribution.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `module`; statically calls `import_exercises`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `StructuredTransport`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/authoring/ai_contracts|learnloop.content.authoring.ai_contracts]] — imports `ExerciseAuthoring`, `ExerciseAuthoringContext`, `exercise_authoring_prompt`; calls `ExerciseAuthoringContext`, `exercise_authoring_prompt`
- [[Reference/Modules/learnloop/content/sources/math_text|learnloop.content.sources.math_text]] — imports `contains_unicode_math`, `unicode_math_to_latex`; calls `contains_unicode_math`, `unicode_math_to_latex`
- [[Reference/Modules/learnloop/curriculum/depth_rungs|learnloop.curriculum.depth_rungs]] — imports `TASK_FEATURE_SCHEMA_SLUG`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `BLOCK_SPAN_V1`, `format_block_span`; calls `format_block_span`
- [[Reference/Modules/learnloop/reader/annotations|learnloop.reader.annotations]] — imports `translate_selection`; calls `translate_selection`
- [[Reference/Modules/learnloop/substrate/activity_patterns|learnloop.substrate.activity_patterns]] — imports `LEGACY_UNMAPPED`, `ensure_builtin_task_feature_schema`, `ensure_capability_alias_registry`, `map_capability`, `validate_task_features`; calls `ensure_builtin_task_feature_schema`, `ensure_capability_alias_registry`, `map_capability`, `validate_task_features`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `learning_object_facet_union`; calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `upsert_practice_item`; calls `upsert_practice_item`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `pathlib`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_exercise_authoring.py](../../../../../../../tests/test_exercise_authoring.py) — direct import
  - `test_edited_capture_quote_becomes_the_exercise_surface`
  - `test_import_dedupes_identical_prompt_on_second_run`
  - `test_selection_level_edited_text_overrides_combined_surface`
  - `test_unresolvable_selection_raises`
- [tests/test_openrouter_client.py](../../../../../../../tests/test_openrouter_client.py) — direct import
  - `test_openrouter_supports_exercise_authoring`
- [tests/test_structured_transport_parity.py](../../../../../../../tests/test_structured_transport_parity.py) — direct import

## Modification guidance

- Change exercise authoring policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/authoring/exercise_authoring.py](../../../../../../../src/learnloop/content/authoring/exercise_authoring.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
