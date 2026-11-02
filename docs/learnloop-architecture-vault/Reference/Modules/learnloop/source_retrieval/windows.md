---
title: "learnloop.source_retrieval.windows"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/windows.py"
source_paths:
  - "src/learnloop/source_retrieval/windows.py"
source_commit: "e1e10f69b9ad6f40b364fe4f79097caa108bcdd4"
source_commit_timestamp: "2026-10-24T20:18:30-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.source_retrieval.windows module"
  - "src/learnloop/source_retrieval/windows.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.windows`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.windows` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Contextual windows over production blocks (spec_local_contextual_retrieval_v1 §4.1, §4.3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/windows.py](../../../../../../src/learnloop/source_retrieval/windows.py) |
| Source lines | 312 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e1e10f69b9ad6f40b364fe4f79097caa108bcdd4` |
| Commit timestamp | `2026-10-24T20:18:30-04:00` |

## Public API

- `token_estimate(text: str | None) -> int` ([source](../../../../../../src/learnloop/source_retrieval/windows.py), line 67) — UTF-8 bytes / 3, rounded up (E0's packing estimate; the worker measures).
- `class Member` ([source](../../../../../../src/learnloop/source_retrieval/windows.py), line 74) — One block, or one part of a split block, inside a window.
  - `tokens(self) -> int` (line 83; public)
- `class Window` ([source](../../../../../../src/learnloop/source_retrieval/windows.py), line 88)
  - `chunks(self) -> list[str]` (line 96; public)
  - `span_ids(self) -> list[str]` (line 100; public)
  - `digest(self) -> str` (line 104; public)
- `window_key(space_id: str, window: Window, span_id: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/windows.py), line 115) — The vector key of ``span_id``'s vector in ``window`` (§4.2): the space, the extraction, the whole window (members, texts, offsets, policy class) and the target block.
- `policy_classes(vault: LoadedVault, repository: Repository, keys: Iterable[tuple[str, str]]) -> dict[tuple[str, str], str]` ([source](../../../../../../src/learnloop/source_retrieval/windows.py), line 123) — Each block's policy class (``teaching`` unless withheld), by the production predicates: ``exam_exclusions`` for exam and held-out material, ``model_reader_withheld`` for solutions and the assessment lane.
- `build_windows(extraction_id: str, blocks: Sequence[tuple[str, str, tuple[str, ...], str]], variant: str) -> list[Window]` ([source](../../../../../../src/learnloop/source_retrieval/windows.py), line 178) — Windows of one extraction from ``(span_id, recipe text, section path, policy class)`` in document order.
- `permitted_titles(extraction_id: str, titles: Mapping[str, str], headers: Mapping[str, str], classes: Mapping[tuple[str, str], str]) -> dict[str, str]` ([source](../../../../../../src/learnloop/source_retrieval/windows.py), line 226) — ``titles`` with every header whose block is not ``teaching`` (or that no current block anchors) replaced by ``WITHHELD_HEADING`` (Codex review F1).
- `extraction_windows(vault: LoadedVault, repository: Repository, extraction_id: str, variant: str, *, classes: Mapping[tuple[str, str], str] | None=None) -> list[Window]` ([source](../../../../../../src/learnloop/source_retrieval/windows.py), line 239) — The windows of one extraction's embeddable blocks under the current policy (withheld headings redacted from every section path).
- `windows_by_extraction(vault: LoadedVault, repository: Repository, extraction_ids: Sequence[str], variants: Sequence[str]=VARIANTS) -> dict[tuple[str, str], list[Window]]` ([source](../../../../../../src/learnloop/source_retrieval/windows.py), line 259) — ``{(extraction_id, variant): windows}`` under the current policy (one policy read).
- `expected_keys(space_id: str, windows: Sequence[Window]) -> dict[str, list[tuple[str, int]]]` ([source](../../../../../../src/learnloop/source_retrieval/windows.py), line 272) — ``{span_id: [(vector key, tokens)]}``: one key per (window, block); a split block has one key per part (all must exist), weighted by its tokens.
- `mean_vector(parts: Sequence[Sequence[float]], weights: Sequence[int]) -> list[float]` ([source](../../../../../../src/learnloop/source_retrieval/windows.py), line 283) — The token-weighted mean of a split block's part vectors (``split_mean``).

### Module constants

- `WINDOW_RULE` ([src/learnloop/source_retrieval/windows.py](../../../../../../src/learnloop/source_retrieval/windows.py), line 51)
- `WINDOW_TOKENS` ([src/learnloop/source_retrieval/windows.py](../../../../../../src/learnloop/source_retrieval/windows.py), line 53)
- `CHUNK_MARKER_TOKENS` ([src/learnloop/source_retrieval/windows.py](../../../../../../src/learnloop/source_retrieval/windows.py), line 54)
- `MAX_DOCUMENT_TOKENS` ([src/learnloop/source_retrieval/windows.py](../../../../../../src/learnloop/source_retrieval/windows.py), line 57)
- `PART_TOKENS` ([src/learnloop/source_retrieval/windows.py](../../../../../../src/learnloop/source_retrieval/windows.py), line 60)
- `WITHHELD_HEADING` ([src/learnloop/source_retrieval/windows.py](../../../../../../src/learnloop/source_retrieval/windows.py), line 62)
- `VARIANTS` ([src/learnloop/source_retrieval/windows.py](../../../../../../src/learnloop/source_retrieval/windows.py), line 63)
- `POLICY_CLASSES` ([src/learnloop/source_retrieval/windows.py](../../../../../../src/learnloop/source_retrieval/windows.py), line 64)

### Explicit exports

`__all__` declares:

- `CHUNK_MARKER_TOKENS`
- `MAX_DOCUMENT_TOKENS`
- `Member`
- `PART_TOKENS`
- `POLICY_CLASSES`
- `VARIANTS`
- `WITHHELD_HEADING`
- `WINDOW_RULE`
- `WINDOW_TOKENS`
- `Window`
- `build_windows`
- `expected_keys`
- `extraction_windows`
- `mean_vector`
- `permitted_titles`
- `policy_classes`
- `token_estimate`
- `window_key`
- `windows_by_extraction`

## Internal implementation anchors

- `_sha(value: Any) -> str` ([source](../../../../../../src/learnloop/source_retrieval/windows.py), line 111)
- `_split(span_id: str, text: str) -> list[Member]` ([source](../../../../../../src/learnloop/source_retrieval/windows.py), line 145) — Consecutive character parts, each at most ``PART_TOKENS`` estimated tokens: the longest prefix within the bound, cut back to its last whitespace when it has one (the next part starts at that whitespace), else cut hard, so an unbroken input (CJK, a long formula) still holds the b…
- `_header_spans(blocks: Sequence[Any]) -> dict[str, str]` ([source](../../../../../../src/learnloop/source_retrieval/windows.py), line 219) — ``{extractor block id: span id}`` of the extraction's section headers.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]] — imports `WINDOW_RULE`, `Window`, `expected_keys`, `extraction_windows`, `mean_vector`, `window_key`; statically calls `expected_keys`, `extraction_windows`, `mean_vector`, `window_key`
- [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]] — imports `WINDOW_RULE`, `Window`, `expected_keys`, `extraction_windows`, `token_estimate`, `window_key`, `windows_by_extraction`; statically calls `expected_keys`, `extraction_windows`, `token_estimate`, `window_key`, `windows_by_extraction`
- [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]] — imports `expected_keys`, `mean_vector`, `windows_by_extraction`; statically calls `expected_keys`, `mean_vector`, `windows_by_extraction`
- [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]] — imports `windows_by_extraction`; statically calls `windows_by_extraction`
- [[Reference/Modules/learnloop/source_retrieval/spaces|learnloop.source_retrieval.spaces]] — imports `expected_keys`, `mean_vector`, `windows_by_extraction`; statically calls `expected_keys`, `mean_vector`, `windows_by_extraction`
- [[Reference/Modules/learnloop/source_retrieval/student_data|learnloop.source_retrieval.student_data]] — imports `extraction_windows`, `token_estimate`; statically calls `extraction_windows`, `token_estimate`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `extraction_blocks`, `section_header_titles`; calls `extraction_blocks`, `section_header_titles`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `exam_exclusions`, `model_reader_withheld`; calls `exam_exclusions`, `model_reader_withheld`
- [[Reference/Modules/learnloop/source_retrieval/recipes|learnloop.source_retrieval.recipes]] — imports `embeddable`, `section_path`, `source_block_text`; calls `embeddable`, `section_path`, `source_block_text`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `hashlib`, `json`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]], [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]], [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]], [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]], [[Reference/Modules/learnloop/source_retrieval/spaces|learnloop.source_retrieval.spaces]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_local_index.py](../../../../../../tests/test_local_index.py) — direct import
  - `test_the_moved_pins_equal_e1s`
- [tests/test_query_student.py](../../../../../../tests/test_query_student.py) — direct import
  - `test_training_candidates_hold_training_families_only_and_no_bank_tainted_window`
- [tests/test_source_windows.py](../../../../../../tests/test_source_windows.py) — direct import
  - `test_a_new_exam_mark_changes_the_affected_windows_keys_only`
  - `test_a_withheld_heading_never_reaches_a_teaching_descendant_and_marking_it_changes_its_keys`
  - `test_an_oversized_block_is_split_by_offsets_and_averaged_by_tokens`
  - `test_every_window_holds_the_bound_cjk_and_unbroken_text_included`
  - `test_grouped_windows_respect_sections_policy_and_the_token_bound`
- [tests/test_voyage_fallback.py](../../../../../../tests/test_voyage_fallback.py) — direct import
  - `test_the_backfill_is_capped_receipted_and_window_keyed`

## Modification guidance

- Make changes here when the responsibility remains windows within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/windows.py](../../../../../../src/learnloop/source_retrieval/windows.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
