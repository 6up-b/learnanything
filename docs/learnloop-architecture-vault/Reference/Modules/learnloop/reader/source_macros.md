---
title: "learnloop.reader.source_macros"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/source_macros.py"
source_paths:
  - "src/learnloop/reader/source_macros.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.source_macros module"
  - "src/learnloop/reader/source_macros.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.source_macros`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.source_macros` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: A source's own TeX macros, read from its stored original for the page's renderers.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/source_macros.py](../../../../../../src/learnloop/reader/source_macros.py) |
| Source lines | 303 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `parse_tex_macros(text: str) -> dict[str, str]` ([source](../../../../../../src/learnloop/reader/source_macros.py), line 63) — The macro table the definitions in ``text`` make, as KaTeX's ``macros`` option takes it (``{"\\vvec": "{\\mathbf v}"}``).
- `macros_from_original(raw: bytes) -> dict[str, str]` ([source](../../../../../../src/learnloop/reader/source_macros.py), line 220) — The macro table of one original's bytes: an HTML page's text, or a text file's own (Markdown or TeX); nothing for a PDF, an image, audio or anything else binary.
- `source_math_macros(vault_root: Path, revision: dict[str, Any] | None) -> dict[str, str]` ([source](../../../../../../src/learnloop/reader/source_macros.py), line 247) — The macros of a revision's stored original, or ``{}`` when it has none or the original is not in the vault's store.
- `extraction_math_macros(vault: Any, repository: Any, extraction_id: str | None) -> dict[str, str]` ([source](../../../../../../src/learnloop/reader/source_macros.py), line 258) — The macros of the source an extraction was read from (see :func:`source_math_macros`), or ``{}`` while anything of that source is protected.

### Module constants

- `LOG` ([src/learnloop/reader/source_macros.py](../../../../../../src/learnloop/reader/source_macros.py), line 35)
- `MAX_MACROS` ([src/learnloop/reader/source_macros.py](../../../../../../src/learnloop/reader/source_macros.py), line 39)
- `MAX_NAME_LENGTH` ([src/learnloop/reader/source_macros.py](../../../../../../src/learnloop/reader/source_macros.py), line 41)
- `MAX_BODY_LENGTH` ([src/learnloop/reader/source_macros.py](../../../../../../src/learnloop/reader/source_macros.py), line 43)
- `MAX_TOTAL_BODY` ([src/learnloop/reader/source_macros.py](../../../../../../src/learnloop/reader/source_macros.py), line 45)
- `MAX_ORIGINAL_BYTES` ([src/learnloop/reader/source_macros.py](../../../../../../src/learnloop/reader/source_macros.py), line 47)
- `_DEFINER` ([src/learnloop/reader/source_macros.py](../../../../../../src/learnloop/reader/source_macros.py), line 49)
- `_NAME` ([src/learnloop/reader/source_macros.py](../../../../../../src/learnloop/reader/source_macros.py), line 50)
- `_FORBIDDEN_IN_BODY` ([src/learnloop/reader/source_macros.py](../../../../../../src/learnloop/reader/source_macros.py), line 54)
- `_LOOKS_HTML` ([src/learnloop/reader/source_macros.py](../../../../../../src/learnloop/reader/source_macros.py), line 60)

### Explicit exports

`__all__` declares:

- `MAX_BODY_LENGTH`
- `MAX_MACROS`
- `MAX_NAME_LENGTH`
- `MAX_TOTAL_BODY`
- `extraction_math_macros`
- `macros_from_original`
- `parse_tex_macros`
- `source_math_macros`

## Internal implementation anchors

- `_skip_space(text: str, at: int) -> int` ([source](../../../../../../src/learnloop/reader/source_macros.py), line 91)
- `_read_name(text: str, at: int) -> tuple[str, int] | None` ([source](../../../../../../src/learnloop/reader/source_macros.py), line 97) — ``\name`` or ``{\name}`` at ``at``: the letters and the index after it.
- `_read_group(text: str, at: int) -> tuple[str, int] | None` ([source](../../../../../../src/learnloop/reader/source_macros.py), line 116) — A balanced ``{...}`` at ``at`` (escaped braces do not count): its inside and the index after it.
- `_read_newcommand(text: str, at: int) -> tuple[str, str, int] | None` ([source](../../../../../../src/learnloop/reader/source_macros.py), line 140)
- `_read_def(text: str, at: int) -> tuple[str, str, int] | None` ([source](../../../../../../src/learnloop/reader/source_macros.py), line 167)
- `_highest_parameter(body: str) -> int` ([source](../../../../../../src/learnloop/reader/source_macros.py), line 189)
- `class _VisibleAndHiddenText(HTMLParser)` ([source](../../../../../../src/learnloop/reader/source_macros.py), line 194) — The page's text, hidden elements included (that is where the definitions live), with entities decoded (``\newcommand{\amp}{&amp;}`` is ``&`` to TeX).
- `_cached_macros(path: str, digest: str) -> tuple[tuple[str, str], ...]` ([source](../../../../../../src/learnloop/reader/source_macros.py), line 238)
- `_anything_protected(vault: Any, repository: Any, revision: dict[str, Any]) -> bool` ([source](../../../../../../src/learnloop/reader/source_macros.py), line 274) — Whether exam material (rules 1-4, the held-out partition included: the predicate the phone's ``phone_withheld`` and the Reader's section withholding read) covers any reading of this source, or of the same original under another source, wholly or in part.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `extraction_math_macros`; statically calls `extraction_math_macros`
- [[Reference/Modules/learnloop_sidecar/handlers/side_by_side|learnloop_sidecar.handlers.side_by_side]] — imports `extraction_math_macros`; statically calls `extraction_math_macros`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `exam_material`; calls `exam_material`
- [[Reference/Modules/learnloop/ingest/originals|learnloop.ingest.originals]] — imports `PDF_MAGIC`, `stored_original_path`; calls `stored_original_path`

### Platform and third-party dependencies

- Standard library: `__future__`, `functools`, `html`, `logging`, `pathlib`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]], [[Reference/Modules/learnloop_sidecar/handlers/side_by_side|learnloop_sidecar.handlers.side_by_side]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ux2_macros_protection.py](../../../../../../tests/test_ux2_macros_protection.py) — direct import
  - `test_ux2_an_unreadable_protection_predicate_sends_no_macros`
- [tests/test_ux2_source_macros.py](../../../../../../tests/test_ux2_source_macros.py) — direct import
  - `test_ux2_a_body_that_could_define_include_or_reach_out_is_dropped`
  - `test_ux2_a_recursive_macro_is_kept_as_text_and_left_to_katexs_expansion_limit`
  - `test_ux2_a_source_added_before_reads_its_macros_from_the_stored_original_without_a_new_reading`
  - `test_ux2_an_oversized_table_is_cut_at_the_bounds`
  - `test_ux2_only_plain_definitions_are_read`
  - `test_ux2_scripts_and_binaries_give_no_macros`
  - `test_ux2_the_sample_is_stored_as_before_and_its_reading_carries_the_pages_macros`

## Modification guidance

- Change source macros policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/source_macros.py](../../../../../../src/learnloop/reader/source_macros.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
