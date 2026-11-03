---
title: "learnloop.figures.help"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/help.py"
source_paths:
  - "src/learnloop/figures/help.py"
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
  - "learnloop.figures.help module"
  - "src/learnloop/figures/help.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.help`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.help` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: Reader RW5d P3: figures as a help kind inside attempts (spec_reader_show_me_figures_v1 §6.4, §11.2-§11.4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/help.py](../../../../../../src/learnloop/figures/help.py) |
| Source lines | 461 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `7fd12e25ec8d644a7f73bd03a530e9a4ee9585d0` |
| Commit timestamp | `2026-11-02T19:40:18-05:00` |

## Public API

- `enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/figures/help.py), line 67) — ``figures.help_kind_enabled`` (under ``figures.enabled`` and ``show_me_enabled``).
- `format_value(value: Any, form: str='number') -> str` ([source](../../../../../../src/learnloop/figures/help.py), line 140) — A number as the desktop's figure panels show it (``FigurePanels.tsx`` ``formatValue``, operation for operation): a percent to one decimal, a very large or small number in exponent form with three decimals, else five significant digits.
- `reveal_text(row: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/figures/help.py), line 203) — A stored figure's words (:func:`_words`: what it demonstrates, its assumptions, labels, annotations, prompts; a sketch's drawn strings) and a grammar figure's displayed values at the defaults as formatted (§11.2 row 2): the text the overlap check reads.
- `chain_root(connection: Any, figure_id: str) -> str` ([source](../../../../../../src/learnloop/figures/help.py), line 233) — The first version of ``figure_id``'s "not right?" chain (itself when it supersedes nothing); a rich figure's quick version is its root too.
- `open_assist_for(connection: Any, figure_id: str) -> str | None` ([source](../../../../../../src/learnloop/figures/help.py), line 252) — The figure row of the open attempt a prediction on ``figure_id`` is made under (Codex review F7, spec §11.2 "linked to the assist row"), or None: the newest figure row attached to no attempt yet, requested after its item's last attempt, whose figure is in the same chain (a "not…
- `figure_keys(repository: Repository, row: Mapping[str, Any]) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/figures/help.py), line 277) — Every ``(extraction_id, span_id)`` a figure is placed at or built from: its anchor, its region and crop, the passages around it, its retrieved passages and (a goal-only figure) where it was asked.
- `qualifying_figure(vault: Any, repository: Repository, item: Any, *, exclude_roots: Sequence[str]=()) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/figures/help.py), line 383) — The newest shown figure the chooser may offer for ``item`` as ``explore_figure`` (§11.4), or None: its place in the books treats the item's learning object; none of the passages it was placed at or built from is the item's own (``item_exclusions``: its exercise, solution or work…
- `offer_view(row: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/help.py), line 439) — What the chooser's served line carries (§11.4: one line that opens the figure).

### Module constants

- `FIGURE_LEVEL` ([src/learnloop/figures/help.py](../../../../../../src/learnloop/figures/help.py), line 45)
- `EXPLORE_FIGURE` ([src/learnloop/figures/help.py](../../../../../../src/learnloop/figures/help.py), line 47)
- `QUALIFYING_SCAN` ([src/learnloop/figures/help.py](../../../../../../src/learnloop/figures/help.py), line 51)
- `COST_LINES` ([src/learnloop/figures/help.py](../../../../../../src/learnloop/figures/help.py), line 53)
- `TAKE_STEP_BANNER` ([src/learnloop/figures/help.py](../../../../../../src/learnloop/figures/help.py), line 59)
- `EXPLORE_LABEL` ([src/learnloop/figures/help.py](../../../../../../src/learnloop/figures/help.py), line 61)
- `_TREATS` ([src/learnloop/figures/help.py](../../../../../../src/learnloop/figures/help.py), line 64)
- `_TEXT_KEYS` ([src/learnloop/figures/help.py](../../../../../../src/learnloop/figures/help.py), line 82)
- `_LITERAL` ([src/learnloop/figures/help.py](../../../../../../src/learnloop/figures/help.py), line 86)

### Explicit exports

`__all__` declares:

- `COST_LINES`
- `EXPLORE_FIGURE`
- `EXPLORE_LABEL`
- `FIGURE_LEVEL`
- `QUALIFYING_SCAN`
- `TAKE_STEP_BANNER`
- `chain_root`
- `enabled`
- `figure_keys`
- `format_value`
- `open_assist_for`
- `offer_view`
- `qualifying_figure`
- `reveal_text`

## Internal implementation anchors

- `_literals(code: str) -> Iterable[str]` ([source](../../../../../../src/learnloop/figures/help.py), line 89)
- `_words(value: Any, *, keyed: bool=False) -> Iterable[str]` ([source](../../../../../../src/learnloop/figures/help.py), line 96) — The text values of a figure's JSON: every string under a text key (:data:`_TEXT_KEYS`), however deep; a sketch's program contributes its string literals.
- `_round_half_up(value: float, places: int) -> Any` ([source](../../../../../../src/learnloop/figures/help.py), line 115) — ``value`` (its exact binary value) rounded to ``places`` decimals, ties away from zero: JavaScript's ``toFixed``/``toPrecision`` rule.
- `_js_number(value: float) -> str` ([source](../../../../../../src/learnloop/figures/help.py), line 124) — JavaScript's ``String(number)`` for a finite number in the formatter's plain range (shortest round-trip digits, no trailing ``.0``).
- `_readouts(spec_json: str) -> list[str]` ([source](../../../../../../src/learnloop/figures/help.py), line 175) — A grammar figure's displayed values at the defaults, as the panels format them (:func:`format_value`): readouts, shaded areas (the value and its bounds), a bar chart's highlighted mass, a linear map's determinant.
- `_grammar_version() -> str` ([source](../../../../../../src/learnloop/figures/help.py), line 223)
- `_placed_keys(repository: Repository, row: Mapping[str, Any]) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/figures/help.py), line 297) — Where a figure sits in the books: its anchor (and region), or its retrieved passages and the reading positions it was asked at.
- `class _SectionTopics` ([source](../../../../../../src/learnloop/figures/help.py), line 315) — The learning objects a passage's section treats: its provenance links and (curriculum C0a) its coverage rows that say the section is about the object, the learner's corrections standing over the judge.
- `_covered(repository: Repository, extraction_id: str, section_id: str) -> set[str]` ([source](../../../../../../src/learnloop/figures/help.py), line 359) — Coverage's learning objects for a section: the newest learner row per object stands (``is_about`` counts, ``not_about``/``none`` removes), else a judge row that says the section treats it.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/teacher/visuals|learnloop.teacher.visuals]] — imports `reveal_text`; statically calls `reveal_text`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `COST_LINES`, `FIGURE_LEVEL`, `TAKE_STEP_BANNER`, `chain_root`, `figure_keys`, `open_assist_for`, `reveal_text`; statically calls `chain_root`, `figure_keys`, `open_assist_for`, `reveal_text`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `module`, `reveal_text`; statically calls `chain_root`, `offer_view`, `qualifying_figure`, `reveal_text`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/figures|learnloop.db.stores.figures]] — imports `module`; calls `has_tables`, `shown_figures`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `figure_home_keys`, `help_kind_enabled`; calls `figure_home_keys`, `help_kind_enabled`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `module`; calls `advanced_off_row`, `drawable_now`, `rich_row`, `row_withheld`, `show_me_enabled`, `show_me_row`, `sketch_off_row`, `source_rejected`
- [[Reference/Modules/learnloop/figures/spec|learnloop.figures.spec]] — imports `module`; calls `evaluate_figure`, `parse_spec`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `extraction_sections`; calls `extraction_sections`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `learning_objects_for_section`; calls `learning_objects_for_section`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `item_exclusions`; calls `item_exclusions`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `span_leaks_expected`; calls `span_leaks_expected`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `decimal`, `json`, `math`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/teacher/visuals|learnloop.teacher.visuals]], [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]], [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figures_help.py](../../../../../../tests/test_figures_help.py) — direct import
  - `test_a_figure_built_from_the_items_own_blocks_never_qualifies`
  - `test_the_reveal_text_reads_every_model_written_string_and_the_readouts`
- [tests/test_figures_help_codex_review.py](../../../../../../tests/test_figures_help_codex_review.py) — direct import
  - `test_f2_a_grammar_figures_shaded_area_is_read_as_shown`
  - `test_f2_numbers_are_formatted_as_the_desktop_panels_format_them`
  - `test_s0_f13_an_undisplayed_string_in_a_scene_is_not_reveal_text`

## Modification guidance

- Make changes here when the responsibility remains help within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/help.py](../../../../../../src/learnloop/figures/help.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
