---
title: "learnloop.figures.labels"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/labels.py"
source_paths:
  - "src/learnloop/figures/labels.py"
source_commit: "7fd12e25ec8d644a7f73bd03a530e9a4ee9585d0"
source_commit_timestamp: "2026-11-02T19:40:18-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.figures"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.figures.labels module"
  - "src/learnloop/figures/labels.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.labels`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.labels` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: Reader RW5d: the figures' code-owned label words, and the free-text label rule (spec §9b.4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py) |
| Source lines | 320 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `7fd12e25ec8d644a7f73bd03a530e9a4ee9585d0` |
| Commit timestamp | `2026-11-02T19:40:18-05:00` |

## Public API

- `fold(text: Any) -> str` ([source](../../../../../../src/learnloop/figures/labels.py), line 130) — Text as the rule reads it: NFKC, case-folded, separators as `` · ``, single spaces.
- `label_like(text: Any) -> str | None` ([source](../../../../../../src/learnloop/figures/labels.py), line 194) — The label-like phrase ``text`` contains (folded), or None.
- `label_problems(fields: Iterable[tuple[str, Any]]) -> list[str]` ([source](../../../../../../src/learnloop/figures/labels.py), line 214) — Code's words for every field whose text reads like a check label (the repair call's problems).
- `strip_lines(text: Any) -> str` ([source](../../../../../../src/learnloop/figures/labels.py), line 227) — Stored ``text`` as it is presented (Codex review F3, Nov 1b): each label-like line replaced by :data:`LINE_WITHHELD`, so the cut is never silent; :data:`TEXT_WITHHELD` when it still reads like a label across its lines.
- `json_fields(name: str, raw: Any) -> list[tuple[str, Any]]` ([source](../../../../../../src/learnloop/figures/labels.py), line 252) — The free text of a figure answer's JSON (a spec, a sketch or a rich brief: they share these keys): what it shows and its assumptions.
- `strip_json(raw: Any) -> Any` ([source](../../../../../../src/learnloop/figures/labels.py), line 266) — ``raw`` without its label-like free text: what it shows is emptied and a label-like assumption is dropped.

### Module constants

- `CHECKED` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 71)
- `CHECKS_LEAD` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 73)
- `ILLUSTRATIVE_LABEL` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 77)
- `BOOK_CHECKED_LABEL` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 80)
- `REST_ILLUSTRATION_LABEL` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 81)
- `DERIVED_LABEL` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 82)
- `NOT_FROM_BOOKS_LABEL` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 84)
- `SKETCH_LABEL` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 86)
- `SKETCH_UNCHECKED_LABEL` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 87)
- `SKETCH_NOT_FROM_BOOKS_LABEL` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 88)
- `MANIM_LABEL` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 90)
- `MANIM_UNCHECKED_LABEL` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 91)
- `MANIM_NOT_FROM_BOOKS_LABEL` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 92)
- `MANIM_NOT_COVERED` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 94)
- `CODE_OWNED_LABELS` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 97)
- `CHECK_LABEL_WORDS` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 102)
- `CHECK_GLYPHS` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 105)
- `MIN_SEGMENT_WORDS` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 108)
- `SOURCE_CLAIM_VERBS` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 114)
- `SOURCE_NOUNS` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 116)
- `REASON_WITHHELD` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 119)
- `LINE_WITHHELD` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 122)
- `TEXT_WITHHELD` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 124)
- `_SEPARATORS` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 126)
- `_SPACES` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 127)
- `LABEL_PHRASES` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 154)
- `_PHRASE` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 155)
- `_WORD` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 156)
- `_LEARNLOOP` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 157)
- `_BADGE` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 158)
- `_NOUN` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 165)
- `_SOURCE_CLAIM` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 166)
- `_LINE_LEAD` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 174)
- `_EMPHASIS` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 175)
- `_LINK` ([src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py), line 178)

### Explicit exports

`__all__` declares:

- `BOOK_CHECKED_LABEL`
- `DERIVED_LABEL`
- `REST_ILLUSTRATION_LABEL`
- `CHECKED`
- `CHECKS_LEAD`
- `CHECK_GLYPHS`
- `CHECK_LABEL_WORDS`
- `CODE_OWNED_LABELS`
- `ILLUSTRATIVE_LABEL`
- `LABEL_PHRASES`
- `LINE_WITHHELD`
- `MANIM_LABEL`
- `MANIM_NOT_COVERED`
- `MANIM_NOT_FROM_BOOKS_LABEL`
- `MANIM_UNCHECKED_LABEL`
- `MIN_SEGMENT_WORDS`
- `NOT_FROM_BOOKS_LABEL`
- `REASON_WITHHELD`
- `SKETCH_LABEL`
- `SKETCH_NOT_FROM_BOOKS_LABEL`
- `SKETCH_UNCHECKED_LABEL`
- `SOURCE_CLAIM_VERBS`
- `SOURCE_NOUNS`
- `TEXT_WITHHELD`
- `fold`
- `json_fields`
- `label_like`
- `label_problems`
- `strip_json`
- `strip_lines`

## Internal implementation anchors

- `_label_phrases() -> tuple[str, ...]` ([source](../../../../../../src/learnloop/figures/labels.py), line 137)
- `_lines(text: Any) -> list[str]` ([source](../../../../../../src/learnloop/figures/labels.py), line 181) — Each line of ``text`` as the rule reads it, split at its original line breaks before spaces collapse, without its Markdown lead, emphasis, code spans and link targets.
- `_assumption_text(item: Any) -> Any` ([source](../../../../../../src/learnloop/figures/labels.py), line 240)
- `_object(raw: Any) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/figures/labels.py), line 244)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/manim_figure|learnloop.figures.manim_figure]] — imports `module`; statically calls `label_problems`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `module`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `module`; statically calls `json_fields`, `label_like`, `label_problems`, `strip_json`, `strip_lines`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/figures|learnloop.db.stores.figures]] — imports `VERIFIED_RW5C`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `re`, `typing`, `unicodedata`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/manim_figure|learnloop.figures.manim_figure]], [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]], [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figure_label_wording.py](../../../../../../tests/test_figure_label_wording.py) — direct import
  - `test_f1_a_source_verification_claim_is_matched_without_a_check_word_or_glyph`
  - `test_f1_remainder_a_source_claim_inside_markdown_formatting_is_matched`
  - `test_f1_remainder_a_stored_transcript_with_a_formatted_source_claim_is_presented_without_it`
  - `test_f1_remainder_ordinary_formatted_prose_is_not_matched`
  - `test_f2_a_label_lead_on_its_own_line_is_matched`
  - `test_f2_ordinary_multiline_prose_is_not_matched`
  - `test_f3_a_stored_label_like_manim_title_and_transcript_are_presented_without_that_text`
  - `test_label_like_text_is_matched`
  - `test_ordinary_prose_is_not_matched`
  - `test_problems_are_in_codes_words_and_name_the_field`
  - `test_r2_a_label_like_tier_reason_is_repaired_then_left_out_of_the_receipt`
  - `test_r2_a_rich_brief_and_reason_still_label_like_are_left_out`
  - `test_strip_json_leaves_out_only_the_label_like_text`
  - `test_the_desktop_frames_carry_the_same_label_strings`
  - `test_the_vocabulary_comes_from_the_code_owned_labels`
- [tests/test_rw5c_labels.py](../../../../../../tests/test_rw5c_labels.py) — direct import
  - `test_the_frame_and_the_python_labels_are_the_same_words`

## Modification guidance

- Make changes here when the responsibility remains labels within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/labels.py](../../../../../../src/learnloop/figures/labels.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
