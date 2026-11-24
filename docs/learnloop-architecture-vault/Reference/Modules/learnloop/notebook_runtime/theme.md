---
title: "learnloop.notebook_runtime.theme"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/notebook_runtime/theme.py"
source_paths:
  - "src/learnloop/notebook_runtime/theme.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.notebook_runtime"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.notebook_runtime.theme module"
  - "src/learnloop/notebook_runtime/theme.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-notebook-runtime"
---

# `learnloop.notebook_runtime.theme`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.notebook_runtime.theme` exists within [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] to own the behavior summarized by its module contract: The paper theme every notebook frame is served with (spec_reader_workbench_v2 §11.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/notebook_runtime/theme.py](../../../../../../src/learnloop/notebook_runtime/theme.py) |
| Source lines | 127 |
| Owning package | [[Reference/Modules/learnloop/notebook_runtime/_package|learnloop.notebook_runtime]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `font_packages_dir() -> Path` ([source](../../../../../../src/learnloop/notebook_runtime/theme.py), line 48)
- `font_file(name: str) -> Path | None` ([source](../../../../../../src/learnloop/notebook_runtime/theme.py), line 55) — The served font ``name``'s file, or None when it is not a theme font or not installed.
- `theme_css(base_url: str) -> str` ([source](../../../../../../src/learnloop/notebook_runtime/theme.py), line 65)

### Module constants

- `PAGE` ([src/learnloop/notebook_runtime/theme.py](../../../../../../src/learnloop/notebook_runtime/theme.py), line 25)
- `SURFACE` ([src/learnloop/notebook_runtime/theme.py](../../../../../../src/learnloop/notebook_runtime/theme.py), line 26)
- `INK` ([src/learnloop/notebook_runtime/theme.py](../../../../../../src/learnloop/notebook_runtime/theme.py), line 27)
- `INK_SOFT` ([src/learnloop/notebook_runtime/theme.py](../../../../../../src/learnloop/notebook_runtime/theme.py), line 28)
- `RULE` ([src/learnloop/notebook_runtime/theme.py](../../../../../../src/learnloop/notebook_runtime/theme.py), line 29)
- `FRAME_RULE` ([src/learnloop/notebook_runtime/theme.py](../../../../../../src/learnloop/notebook_runtime/theme.py), line 30)
- `PURPLE` ([src/learnloop/notebook_runtime/theme.py](../../../../../../src/learnloop/notebook_runtime/theme.py), line 31)
- `PROSE_SIZE_PX` ([src/learnloop/notebook_runtime/theme.py](../../../../../../src/learnloop/notebook_runtime/theme.py), line 35)
- `PROSE_LINE_PX` ([src/learnloop/notebook_runtime/theme.py](../../../../../../src/learnloop/notebook_runtime/theme.py), line 36)
- `FONT_FILES` ([src/learnloop/notebook_runtime/theme.py](../../../../../../src/learnloop/notebook_runtime/theme.py), line 39)
- `FONT_PACKAGES_ENV` ([src/learnloop/notebook_runtime/theme.py](../../../../../../src/learnloop/notebook_runtime/theme.py), line 45)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/notebook_runtime/proxy|learnloop.notebook_runtime.proxy]] — imports `module`; statically calls `font_file`, `theme_css`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `os`, `pathlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/notebook_runtime/proxy|learnloop.notebook_runtime.proxy]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_notebook_runtime.py](../../../../../../tests/test_notebook_runtime.py) — direct import
  - `test_the_paper_theme_sets_variables_and_serves_its_faces_from_the_frames_origin`

## Modification guidance

- Make changes here when the responsibility remains theme within learnloop.notebook_runtime; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/notebook_runtime/theme.py](../../../../../../src/learnloop/notebook_runtime/theme.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
