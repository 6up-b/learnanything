---
title: "learnloop.ingest.extractors.web_page"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/extractors/web_page.py"
source_paths:
  - "src/learnloop/ingest/extractors/web_page.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ingest.extractors"
layer: "infrastructure"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
aliases:
  - "learnloop.ingest.extractors.web_page module"
  - "src/learnloop/ingest/extractors/web_page.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ingest-extractors"
---

# `learnloop.ingest.extractors.web_page`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ingest.extractors.web_page` exists within [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] to own the behavior summarized by its module contract: A web page read into Markdown (extractor ``html``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ingest/extractors/web_page.py](../../../../../../../src/learnloop/ingest/extractors/web_page.py) |
| Source lines | 255 |
| Owning package | [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `readable_markdown(raw_html: Any) -> str | None` ([source](../../../../../../../src/learnloop/ingest/extractors/web_page.py), line 50) — Version 2: trafilatura's readable body as Markdown.
- `page_markdown(raw_html: str) -> str | None` ([source](../../../../../../../src/learnloop/ingest/extractors/web_page.py), line 61) — Version 3: the page's readable body as Markdown, its display math, headings and lists kept.
- `prepare_page(tree: Any, *, old_text: str) -> None` ([source](../../../../../../../src/learnloop/ingest/extractors/web_page.py), line 75) — The changes version 3 makes to a parsed page before trafilatura reads it, in order.
- `display_formulas(markdown: str) -> list[str]` ([source](../../../../../../../src/learnloop/ingest/extractors/web_page.py), line 198) — The display formulas of version-3 Markdown, in order: bare display environments, ``\[ \]`` and ``$$ $$``.

### Module constants

- `WEB_PAGE_EXTRACTOR_VERSION` ([src/learnloop/ingest/extractors/web_page.py](../../../../../../../src/learnloop/ingest/extractors/web_page.py), line 23)
- `OLD_WEB_PAGE_EXTRACTOR_VERSION` ([src/learnloop/ingest/extractors/web_page.py](../../../../../../../src/learnloop/ingest/extractors/web_page.py), line 24)
- `PAGE_FURNITURE` ([src/learnloop/ingest/extractors/web_page.py](../../../../../../../src/learnloop/ingest/extractors/web_page.py), line 27)
- `_HIDDEN_XPATH` ([src/learnloop/ingest/extractors/web_page.py](../../../../../../../src/learnloop/ingest/extractors/web_page.py), line 35)
- `_HIDDEN_MATCH_MIN` ([src/learnloop/ingest/extractors/web_page.py](../../../../../../../src/learnloop/ingest/extractors/web_page.py), line 42)
- `_TEX` ([src/learnloop/ingest/extractors/web_page.py](../../../../../../../src/learnloop/ingest/extractors/web_page.py), line 44)
- `_DISPLAY_ENVIRONMENT` ([src/learnloop/ingest/extractors/web_page.py](../../../../../../../src/learnloop/ingest/extractors/web_page.py), line 47)

### Explicit exports

`__all__` declares:

- `OLD_WEB_PAGE_EXTRACTOR_VERSION`
- `PAGE_FURNITURE`
- `WEB_PAGE_EXTRACTOR_VERSION`
- `display_formulas`
- `page_markdown`
- `prepare_page`
- `readable_markdown`

## Internal implementation anchors

- `_mediawiki_formulas_as_tex(tree: Any) -> None` ([source](../../../../../../../src/learnloop/ingest/extractors/web_page.py), line 85) — A MediaWiki formula shows as an image whose TeX is also in a hidden MathML copy: its TeX, as math.
- `_hidden_parts_as_before(tree: Any, old_text: str) -> None` ([source](../../../../../../../src/learnloop/ingest/extractors/web_page.py), line 97) — A hidden or collapsed part reaches the text only where version 2 let it: version 3 reads more of some pages than version 2 did, and a solution a page hides behind a disclosure must not start reaching the text that way.
- `_drop_furniture(tree: Any) -> None` ([source](../../../../../../../src/learnloop/ingest/extractors/web_page.py), line 116)
- `_math_as_tex(tree: Any) -> None` ([source](../../../../../../../src/learnloop/ingest/extractors/web_page.py), line 122) — MathML with its TeX (a TeX annotation, else ``alttext``) and MathJax's ``math/tex`` scripts, as TeX.
- `_articles_as_parts(tree: Any) -> None` ([source](../../../../../../../src/learnloop/ingest/extractors/web_page.py), line 137) — When the page's first ``<article>`` holds under half of its main text, the articles are parts of the page (a book's activities and exercises), not the page: they are read as the page's other blocks are.
- `_tidy(markdown: str, headings: set[str]) -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/web_page.py), line 153) — Two marks of trafilatura's Markdown writer: a heading written at the end of the line before it (after emphasis that closes a paragraph) is put on its own line, when its words are a heading of the page; a list item whose text starts in a child element is written "-" alone on a li…
- `_displays_apart(lines: list[str]) -> list[str]` ([source](../../../../../../../src/learnloop/ingest/extractors/web_page.py), line 175) — A display environment trafilatura wrote on the lines after a paragraph's last words (or before the next paragraph's first) is set apart by a blank line, so it is a block of its own as the page shows it.
- `_annotation(element: Any) -> str | None` ([source](../../../../../../../src/learnloop/ingest/extractors/web_page.py), line 206)
- `_delimited(tex: str, display: bool) -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/web_page.py), line 213)
- `_replace_with_text(element: Any, text: str) -> None` ([source](../../../../../../../src/learnloop/ingest/extractors/web_page.py), line 217) — Put ``text`` where ``element`` was, its tail kept.
- `_remove(element: Any) -> None` ([source](../../../../../../../src/learnloop/ingest/extractors/web_page.py), line 232) — Remove ``element`` and everything in it, keeping its tail (the text after it belongs to its parent).
- `_squeeze(text: str) -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/web_page.py), line 239)
- `_letters(text: str) -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/web_page.py), line 243)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `WEB_PAGE_EXTRACTOR_VERSION`, `page_markdown`; statically calls `page_markdown`
- [[Reference/Modules/learnloop/content/pipeline/reread|learnloop.content.pipeline.reread]] — imports `OLD_WEB_PAGE_EXTRACTOR_VERSION`, `display_formulas`, `page_markdown`; statically calls `display_formulas`, `page_markdown`
- [[Reference/Modules/learnloop_sidecar/handlers/first_run|learnloop_sidecar.handlers.first_run]] — imports `OLD_WEB_PAGE_EXTRACTOR_VERSION`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `re`, `typing`
- Third party: `trafilatura`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/content/pipeline/reread|learnloop.content.pipeline.reread]], [[Reference/Modules/learnloop_sidecar/handlers/first_run|learnloop_sidecar.handlers.first_run]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ux11_html_extraction.py](../../../../../../../tests/test_ux11_html_extraction.py) — direct import
  - `test_ux11_mathml_and_script_math_reach_the_text_as_tex`

## Modification guidance

- Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/extractors/web_page.py](../../../../../../../src/learnloop/ingest/extractors/web_page.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
