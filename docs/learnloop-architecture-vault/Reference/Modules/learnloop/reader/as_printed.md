---
title: "learnloop.reader.as_printed"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/as_printed.py"
source_paths:
  - "src/learnloop/reader/as_printed.py"
source_commit: "5c6a0834ffb27d10a00b5936cb8f407285014482"
source_commit_timestamp: "2026-10-27T07:02:20-04:00"
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
  - "learnloop.reader.as_printed module"
  - "src/learnloop/reader/as_printed.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.as_printed`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.as_printed` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Reader CA1: the problem as printed (ux_reader_compare_ask_v1 §8; K15, C10).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/as_printed.py](../../../../../../src/learnloop/reader/as_printed.py) |
| Source lines | 930 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `5c6a0834ffb27d10a00b5936cb8f407285014482` |
| Commit timestamp | `2026-10-27T07:02:20-04:00` |

## Public API

- `class CropBox` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 136) — One crop: one retained region (a block's box, or its selected sub-box) on one page.
- `crop_boxes(own: Sequence[DocumentBlock], regions: Mapping[str, tuple[int, Box]] | None=None) -> tuple[list[CropBox], list[str]]` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 165) — The crops of ``own`` (the problem's blocks), one per block in reading order, and the span ids that crop nothing (no page or no box).
- `shows_unsafe(retained: Sequence[DocumentBlock], on_pages: Sequence[DocumentBlock], unsafe: Collection[str], regions: Mapping[str, tuple[int, Box]] | None=None) -> bool` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 206) — Whether a retained display area (a crop: a retained block's box, or its selected sub-box) overlaps unsafe content (Sol verify ruling, 2026-10-27): the box of a block in ``unsafe`` that is not retained (a book-solution span, a solution role, a heading-led solution, a figure ``fig…
- `page_label(pdf_path: Any, page: int | None) -> str | None` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 245) — The printed page label when the PDF carries page labels, else the page's position in the file (one-based); None without a page.
- `class PrintedOrigin` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 257) — Where an item's print is: its blocks on one extraction (§8.4).
  - `located_by(self) -> tuple[str, ...]` (line 282; public)
  - `stimulus(self) -> tuple[str, ...]` (line 286; public) — The blocks a check on your own may crop figures from.
- `region_for(value: Mapping[str, Any] | None, span_ids: Sequence[str]) -> dict[str, tuple[int, Box]]` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 296) — A selection's ``region`` as :func:`crop_boxes` takes it (``ingest.ir.selection_region``).
- `printed_origin(repository: Any, item: Any, *, roles: RoleReader | None=None) -> PrintedOrigin | None` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 710) — The item's print, or None (pasted text, a generated card, a photo card).
- `printed_crops(repository: Any, *, extraction_id: str, span_ids: Sequence[str], render: bool, figure_only: bool=False, regions: Mapping[str, tuple[int, Box]] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 733) — The crops of these blocks (the multi-block form of ``reader.block_original_region``).
- `item_as_printed(repository: Any, item: Any, *, enabled: bool, cold: bool, render: bool, source_title: str | None=None, photo: Mapping[str, Any] | None=None, origin: PrintedOrigin | None=None, roles: RoleReader | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 855) — The practice view of ``item`` as printed (K15).

### Module constants

- `KIND_PAGE` ([src/learnloop/reader/as_printed.py](../../../../../../src/learnloop/reader/as_printed.py), line 121)
- `KIND_FIGURE` ([src/learnloop/reader/as_printed.py](../../../../../../src/learnloop/reader/as_printed.py), line 122)
- `KIND_PHOTO` ([src/learnloop/reader/as_printed.py](../../../../../../src/learnloop/reader/as_printed.py), line 123)
- `KIND_NONE` ([src/learnloop/reader/as_printed.py](../../../../../../src/learnloop/reader/as_printed.py), line 124)
- `FIGURE_LABEL` ([src/learnloop/reader/as_printed.py](../../../../../../src/learnloop/reader/as_printed.py), line 126)
- `PHOTO_LABEL` ([src/learnloop/reader/as_printed.py](../../../../../../src/learnloop/reader/as_printed.py), line 127)
- `NO_ORIGINAL` ([src/learnloop/reader/as_printed.py](../../../../../../src/learnloop/reader/as_printed.py), line 128)
- `NO_CROP` ([src/learnloop/reader/as_printed.py](../../../../../../src/learnloop/reader/as_printed.py), line 130)
- `_ANSWER_HEADING` ([src/learnloop/reader/as_printed.py](../../../../../../src/learnloop/reader/as_printed.py), line 405)
- `_PART_BREAK` ([src/learnloop/reader/as_printed.py](../../../../../../src/learnloop/reader/as_printed.py), line 412)
- `_LABEL_WORDS` ([src/learnloop/reader/as_printed.py](../../../../../../src/learnloop/reader/as_printed.py), line 512)
- `_NUMBERED_ONLY` ([src/learnloop/reader/as_printed.py](../../../../../../src/learnloop/reader/as_printed.py), line 514)
- `_LABEL_TOKEN` ([src/learnloop/reader/as_printed.py](../../../../../../src/learnloop/reader/as_printed.py), line 515)
- `_ROMAN` ([src/learnloop/reader/as_printed.py](../../../../../../src/learnloop/reader/as_printed.py), line 520)
- `_DASHES` ([src/learnloop/reader/as_printed.py](../../../../../../src/learnloop/reader/as_printed.py), line 521)

### Explicit exports

`__all__` declares:

- `FIGURE_LABEL`
- `KIND_FIGURE`
- `KIND_NONE`
- `KIND_PAGE`
- `KIND_PHOTO`
- `NO_CROP`
- `NO_ORIGINAL`
- `PHOTO_LABEL`
- `CropBox`
- `PrintedOrigin`
- `crop_boxes`
- `item_as_printed`
- `page_label`
- `printed_crops`
- `printed_origin`
- `region_for`

## Internal implementation anchors

- `_box(block: DocumentBlock) -> Box | None` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 144)
- `_overlap(a: Box, b: Box) -> Box | None` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 159)
- `_outside(outer: Box, inner: Box) -> list[Box]` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 197) — ``outer`` less ``inner`` (inside it), as at most four rectangles.
- `_pdf_path(repository: Any, extraction_id: str) -> Any` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 236)
- `_region(value: Any) -> tuple[int, Box] | None` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 292)
- `_ref_field(ref: Any, name: str) -> Any` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 302)
- `_block_refs(item: Any) -> list[tuple[str, str, Any]]` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 312) — The item's ``block_span_v1`` source refs: (extraction, span, ref).
- `_selection_origin(repository: Any, item: Any) -> PrintedOrigin | None` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 327) — A Reader selection import (``reader.import_exercise``, the workbench's "work through this"): marked by its ``learner_item_authored`` event (the origin alone is shared with AI proposals over sources), its blocks named by its ``block_span_v1`` source refs, else by its import rows.
- `_canonical_origin(item: Any) -> PrintedOrigin` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 382) — A ``canonical_exercise``: the sources service's exercise region names its blocks.
- `_tokens(text: str | None) -> list[str]` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 415)
- `_joined(tokens: list[str]) -> tuple[str, list[int]]` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 419) — The words run together without spaces, and where each word starts in that run (with its end): word boundaries, where a placement may begin or end.
- `_words(tokens: list[str], offsets: list[int], start: int, end: int) -> str` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 430) — The words between two boundaries of :func:`_joined`.
- `_occurrences(haystack: str, needle: str) -> list[int]` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 436)
- `class _Placement` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 445) — Where the statement places a block: the block's words before and after the statement's text in it, and the part of the statement it prints (``start``, ``end``: positions in the statement's words run together without spaces).
- `_placement(block_text: str, statement: str) -> _Placement | None` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 457) — Where the statement places a block, or None when nothing does (they share no run of words: the block is not the statement's, or the learner reworded it).
- `_covers(parts: Sequence[_Placement], statement: str) -> bool` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 497) — Whether the placed parts print the whole statement between them (Codex re-review F3: never a partial print).
- `_label_token(token: str) -> str | None` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 524) — ``"label"`` for a word a label may hold, ``"kind"`` for a kind that is one only with a number after it ("No.", "Q."), ``"number"`` for a number, else None.
- `_is_label(text: str) -> bool` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 551) — Whether words before a statement in its block are affirmatively a label or heading (Codex re-review of the Astra fixes, F1): an exercise's kind and number, an enumerator, a section mark, nothing else.
- `_contained(block_text: str, statement: str) -> tuple[bool, _Placement | None]` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 564) — Whether a text block lies inside the statement (rule 2 of the module docstring), and the part of the statement it prints.
- `_import_forms(block_text: str) -> list[str]` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 583) — The block's text, and the text an import made of it when it carries Unicode math (CA1 landing finding): ``exercise_authoring`` passes each part through ``unicode_math_to_latex`` ("exist ∈ such that" becomes "exist $\in$ such that"), so a verbatim statement holds that form.
- `_answer_heading(text: str | None) -> str | None` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 597) — ``"solution"`` or ``"proof"`` when a heading of that kind starts the text's first line (:data:`_ANSWER_HEADING`), else None.
- `_runs_into_solution(text: str | None) -> bool` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 606) — Whether a solution or proof heading starts any part of a block's text.
- `_solution_span_ids(connection: Any, item_id: str, extraction_id: str) -> set[str]` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 612) — The book-solution blocks the item's import checks found (each import row's ``verification``: ``book_solution``, ``solution_search``).
- `_problem_only(repository: Any, item: Any, origin: PrintedOrigin, *, roles: RoleReader | None=None) -> PrintedOrigin` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 629) — The origin narrowed to the problem (module docstring, "Only the problem, never the solution" and "Figures by role"): ``span_ids`` the free crop (empty: ``NO_CROP``), ``figure_span_ids`` the figures a check on your own shows, ``page_span_ids`` the original page's outline, none of…
- `_overlaps_unsafe(repository: Any, origin: PrintedOrigin) -> bool` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 787) — Whether the free crop would overlap unsafe content (:func:`shows_unsafe`); a read that fails says yes (fail closed: ``NO_CROP``, the page offered).
- `_label(label: str | None) -> str | None` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 803) — CA1 polish: an exercise label with no text is no label (the header then names the book and page only, no empty part).
- `_none(reason: str, *, cold: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 811)
- `_page_only(repository: Any, origin: PrintedOrigin) -> tuple[int, str, list[str]] | None` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 815) — F5: the first page of the problem's blocks and its blocks there, when no crop can be made but the page is known (a pypdf extraction keeps a page and no box); None without a page.
- `_page_without_crop(repository: Any, origin: PrintedOrigin, *, source_title: str | None, cold: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/as_printed.py), line 828) — F5 and re-review F9: no crop can be made (no box, or the problem's own blocks are not known), but a known page of a readable original is still the book's page: offered (with its cost, where it opens), and the crop says honestly that it can't be made.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/as_printed|learnloop_sidecar.handlers.as_printed]] — imports `item_as_printed`, `printed_origin`; statically calls `item_as_printed`, `printed_origin`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `printed_crops`, `region_for`; statically calls `printed_crops`, `region_for`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/math_text|learnloop.content.sources.math_text]] — imports `contains_unicode_math`, `unicode_math_to_latex`; calls `contains_unicode_math`, `unicode_math_to_latex`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `imports_for_item`, `is_reader_import`; calls `imports_for_item`, `is_reader_import`
- [[Reference/Modules/learnloop/ingest/block_roles|learnloop.ingest.block_roles]] — imports `figure_is_unsafe`; calls `figure_is_unsafe`
- [[Reference/Modules/learnloop/ingest/ir|learnloop.ingest.ir]] — imports `DocumentBlock`, `is_figure_block`, `page_region`, `selection_region`; calls `is_figure_block`, `page_region`, `selection_region`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `parse_block_span`; calls `parse_block_span`
- [[Reference/Modules/learnloop/reader/span_view|learnloop.reader.span_view]] — imports `module`; calls `_local_pdf_crops`, `_local_pdf_page_label`, `_original_pdf_for`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `logging`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/as_printed|learnloop_sidecar.handlers.as_printed]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_ca1_as_printed.py](../../../../../../tests/test_reader_ca1_as_printed.py) — direct import
  - `test_a_block_without_a_page_or_a_box_crops_nothing`
  - `test_during_a_check_on_your_own_only_the_figure_shows_and_nothing_locates_it`
  - `test_each_of_the_problems_blocks_is_its_own_crop_in_reading_order`
  - `test_the_crops_from_the_page_hold_only_the_problems_own_ink`
  - `test_the_view_function_without_a_canonical_exercise_or_photo`
  - `test_without_the_original_the_geometry_is_kept_and_nothing_is_drawn`
- [tests/test_reader_ca1_astra_codex_review.py](../../../../../../tests/test_reader_ca1_astra_codex_review.py) — direct import
  - `test_a_check_on_your_own_still_shows_the_figure_the_statement_names`
- [tests/test_reader_ca1_astra_fixes.py](../../../../../../tests/test_reader_ca1_astra_fixes.py) — direct import
  - `test_a_block_holding_the_stem_and_its_solution_gives_no_crop_and_keeps_the_page`
  - `test_a_block_whose_text_beside_the_stem_gives_the_answer_away_gives_no_crop`
  - `test_a_paraphrased_single_statement_owns_nothing_and_offers_only_the_charged_page`
  - `test_a_selection_level_edit_of_the_whole_passage_never_crops_the_solution`
  - `test_a_split_selection_still_crops_each_items_own_block`
- [tests/test_reader_ca1_astra_redesign.py](../../../../../../tests/test_reader_ca1_astra_redesign.py) — direct import
  - `test_a_solution_lead_is_a_heading_not_a_word_starting_a_sentence`
  - `test_and_outside_a_check_the_rule_withholds_the_free_crop`
  - `test_f2_a_required_input_graph_is_shown_in_a_check_on_your_own`
  - `test_f6_crop_boxes_returns_one_crop_per_retained_region`
- [tests/test_reader_ca1_astra_rereview.py](../../../../../../tests/test_reader_ca1_astra_rereview.py) — direct import
  - `test_a_placement_starts_and_ends_where_words_do`
  - `test_labels_and_headings_are_labels`
  - `test_other_words_before_the_statement_are_not_labels`
- [tests/test_reader_ca1_codex_review.py](../../../../../../tests/test_reader_ca1_codex_review.py) — direct import
  - `test_a_crop_is_exactly_its_blocks_box`
  - `test_a_figure_only_crop_never_takes_in_the_stem_beside_it`
  - `test_a_neighbour_reaching_into_the_gap_is_in_no_crop_though_its_centre_is_outside`
  - `test_a_page_known_without_a_box_offers_the_original_page_and_no_substitute_crop`
  - `test_a_split_over_disjoint_and_shared_blocks_withholds_only_the_sharing_items_crop`
  - `test_a_split_whose_ownership_cannot_be_read_offers_only_the_charged_page`
  - `test_a_split_with_an_unanchored_sibling_owns_nothing`
  - `test_a_split_written_before_ownership_was_kept_withholds_the_free_crop`
  - `test_a_split_written_with_no_import_rows_withholds_the_free_crop`
  - `test_adjacent_blocks_stay_two_crops`
  - `test_an_import_written_before_ownership_was_kept_shows_only_the_page`
  - `test_two_exercises_split_from_one_block_get_no_free_crop_and_keep_the_page`
- [tests/test_reader_ca1_unicode_containment.py](../../../../../../tests/test_reader_ca1_unicode_containment.py) — direct import
  - `test_containment_reads_the_converted_form_and_nothing_more`

## Modification guidance

- Change as printed policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/as_printed.py](../../../../../../src/learnloop/reader/as_printed.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
