---
title: "learnloop.figures.katex_tree"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/katex_tree.py"
source_paths:
  - "src/learnloop/figures/katex_tree.py"
source_commit: "a126b6bea5b3498d0ed30d949340f2ccc9a35ff6"
source_commit_timestamp: "2026-11-02T22:44:18-05:00"
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
  - "learnloop.figures.katex_tree module"
  - "src/learnloop/figures/katex_tree.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.katex_tree`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.katex_tree` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: KaTeX's own parse tree of a book's equation (spec_reader_rw5c_checked_labels_v1 §5.3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/katex_tree.py](../../../../../../src/learnloop/figures/katex_tree.py) |
| Source lines | 153 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `a126b6bea5b3498d0ed30d949340f2ccc9a35ff6` |
| Commit timestamp | `2026-11-02T22:44:18-05:00` |

## Public API

- `class TreeRefused(Exception)` ([source](../../../../../../src/learnloop/figures/katex_tree.py), line 72) — No tree, and why as the reader's closed key: ``not_rendered`` (KaTeX refuses; the page shows an error), ``macro_definition``, ``too_long`` (over a cap) or ``engine_unavailable`` (no engine here).
  - `__init__(self, reason: str) -> None` (line 76; internal)
- `class Trees` ([source](../../../../../../src/learnloop/figures/katex_tree.py), line 81) — One loaded engine for one check (not thread-safe, as :class:`.sketch_engine.SketchEngine`).
  - `__init__(self, *, path: Path=KATEX_ENGINE_PATH, expected: str=KATEX_ENGINE_SHA256, source: Path=KATEX_PATH, source_sha256: str=KATEX_SHA256) -> None` (line 85; internal)
  - `_open(self) -> Any` (line 91; internal)
  - `parse(self, tex: str, *, display: bool=False) -> list[dict[str, Any]]` (line 113; public) — KaTeX's tree of ``tex`` under the page's settings, or :class:`TreeRefused`.
  - `close(self) -> None` (line 133; public)
  - `__enter__(self) -> 'Trees'` (line 138; internal)
  - `__exit__(self, *_exc: Any) -> None` (line 141; internal)

### Module constants

- `_ENGINE_DIR` ([src/learnloop/figures/katex_tree.py](../../../../../../src/learnloop/figures/katex_tree.py), line 35)
- `KATEX_ENGINE_PATH` ([src/learnloop/figures/katex_tree.py](../../../../../../src/learnloop/figures/katex_tree.py), line 37)
- `KATEX_ENGINE_SHA256` ([src/learnloop/figures/katex_tree.py](../../../../../../src/learnloop/figures/katex_tree.py), line 38)
- `KATEX_PATH` ([src/learnloop/figures/katex_tree.py](../../../../../../src/learnloop/figures/katex_tree.py), line 41)
- `KATEX_VERSION` ([src/learnloop/figures/katex_tree.py](../../../../../../src/learnloop/figures/katex_tree.py), line 42)
- `KATEX_SHA256` ([src/learnloop/figures/katex_tree.py](../../../../../../src/learnloop/figures/katex_tree.py), line 43)
- `_PROGRAM` ([src/learnloop/figures/katex_tree.py](../../../../../../src/learnloop/figures/katex_tree.py), line 48)

### Explicit exports

`__all__` declares:

- `KATEX_ENGINE_PATH`
- `KATEX_ENGINE_SHA256`
- `KATEX_PATH`
- `KATEX_SHA256`
- `KATEX_VERSION`
- `TreeRefused`
- `Trees`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/book_math|learnloop.figures.book_math]] — imports `module`; statically calls `Trees`
- [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]] — imports `module`; statically calls `Trees`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/figures/sketch_engine|learnloop.figures.sketch_engine]] — imports `module`; calls `SketchEngine`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `json`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/book_math|learnloop.figures.book_math]], [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/katex_meaning.py](../../../../../../tests/katex_meaning.py) — direct import
- [tests/test_rw5c_book_math.py](../../../../../../tests/test_rw5c_book_math.py) — direct import
  - `test_caps_and_a_seeded_fuzz_never_raise_outside_the_reasons`
- [tests/test_rw5c_katex_tree.py](../../../../../../tests/test_rw5c_katex_tree.py) — direct import
  - `test_a_changed_katex_file_is_unreadable`
  - `test_a_definition_never_reaches_another_parse_in_one_engine`
  - `test_a_katex_bump_moves_the_reader_version_and_needs_a_certification_bump`
  - `test_a_missing_engine_is_unreadable_never_a_fallback`
  - `test_a_segment_nested_past_every_cap_is_unreadable_not_a_crash`
  - `test_a_segment_over_the_work_cap_is_unreadable_and_the_engine_still_reads`
  - `test_a_wrong_engine_digest_is_unreadable`
  - `test_display_mode_does_not_change_a_readable_tree`
  - `test_the_engine_variant_is_pinned_and_differs_from_the_sketch_engine_by_one_define`
  - `test_the_left_hand_side_is_refused_when_alone_it_would_not_be_the_left_of_the_parse`
  - `test_the_variant_runs_under_the_sketch_engines_caps`
  - `test_the_vendored_file_is_byte_for_byte_the_installed_package_when_installed`
  - `test_the_vendored_file_is_text_with_its_licence_beside_it`
  - `test_the_vendored_katex_is_the_one_the_reader_locks`
  - `test_whatever_reads_from_token_soup_means_what_katex_renders`
  - `test_whatever_reads_means_what_katex_renders`
- [tests/test_rw5c_labels.py](../../../../../../tests/test_rw5c_labels.py) — direct import
  - `test_every_other_code_owned_label_template_renders_in_katex`
  - `test_the_plain_writer_parses_back_to_the_same_value_and_the_tex_writer_means_it_in_katex`
- [tests/test_rw5c_recheck.py](../../../../../../tests/test_rw5c_recheck.py) — direct import
  - `test_reading_a_figure_never_opens_the_katex_engine`
- [tests/test_rw5c_source_check.py](../../../../../../tests/test_rw5c_source_check.py) — direct import
  - `test_with_no_engine_a_book_equation_is_unreadable_and_the_sandbox_is_not_asked`

## Modification guidance

- Make changes here when the responsibility remains katex tree within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/katex_tree.py](../../../../../../src/learnloop/figures/katex_tree.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
