---
title: "learnloop.pads.ink_render"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/pads/ink_render.py"
source_paths:
  - "src/learnloop/pads/ink_render.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.pads"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.pads.ink_render module"
  - "src/learnloop/pads/ink_render.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-pads"
---

# `learnloop.pads.ink_render`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.pads.ink_render` exists within [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] to own the behavior summarized by its module contract: Strokes to an image, on the server, deterministically (spec §10.10: ``ink.transcribe`` renders the strokes and sends the image).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/pads/ink_render.py](../../../../../../src/learnloop/pads/ink_render.py) |
| Source lines | 83 |
| Owning package | [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class InkTooLarge(ValueError)` ([source](../../../../../../src/learnloop/pads/ink_render.py), line 31) — The strokes span more than an image may hold.
- `pen_width_px(device_pixel_ratio: float) -> int` ([source](../../../../../../src/learnloop/pads/ink_render.py), line 35)
- `canvas(strokes: list[dict[str, Any]], device_pixel_ratio: float) -> tuple[int, int, float, float, int]` ([source](../../../../../../src/learnloop/pads/ink_render.py), line 39) — ``(width, height, min_x, min_y, margin)`` in device pixels for these strokes.
- `render_png(strokes: list[dict[str, Any]], *, device_pixel_ratio: float, paper: tuple[int, int, int]=PAD_PAPER) -> bytes` ([source](../../../../../../src/learnloop/pads/ink_render.py), line 50) — The strokes (each ``{points: [[x, y, ...], ...]}``, CSS pixels) as a PNG.

### Module constants

- `PEN` ([src/learnloop/pads/ink_render.py](../../../../../../src/learnloop/pads/ink_render.py), line 24)
- `PEN_WIDTH_CSS_PX` ([src/learnloop/pads/ink_render.py](../../../../../../src/learnloop/pads/ink_render.py), line 25)
- `PAD_PAPER` ([src/learnloop/pads/ink_render.py](../../../../../../src/learnloop/pads/ink_render.py), line 26)
- `SOURCE_PAPER` ([src/learnloop/pads/ink_render.py](../../../../../../src/learnloop/pads/ink_render.py), line 27)
- `MEDIA_TYPE` ([src/learnloop/pads/ink_render.py](../../../../../../src/learnloop/pads/ink_render.py), line 28)

### Explicit exports

`__all__` declares:

- `InkTooLarge`
- `MEDIA_TYPE`
- `PAD_PAPER`
- `PEN`
- `PEN_WIDTH_CSS_PX`
- `SOURCE_PAPER`
- `canvas`
- `pen_width_px`
- `render_png`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/pads/ink_transcribe|learnloop.pads.ink_transcribe]] — imports `module`; statically calls `render_png`
- [[Reference/Modules/learnloop_sidecar/handlers/ink|learnloop_sidecar.handlers.ink]] — imports `InkTooLarge`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `MAX_IMAGE_BYTES`

### Platform and third-party dependencies

- Standard library: `__future__`, `io`, `math`, `typing`
- Third party: `PIL`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/pads/ink_transcribe|learnloop.pads.ink_transcribe]], [[Reference/Modules/learnloop_sidecar/handlers/ink|learnloop_sidecar.handlers.ink]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rd8a_render.py](../../../../../../tests/test_reader_rd8a_render.py) — direct import
  - `test_nothing_is_drawn_past_the_canvas_limit_or_sent_past_the_image_limit`
  - `test_the_canvas_is_the_strokes_box_plus_one_pen_width_each_side`
  - `test_the_pen_is_the_specs_on_the_paper_it_was_drawn_on`
  - `test_the_same_strokes_give_the_same_bytes`
- [tests/test_reader_rd8a_transcribe.py](../../../../../../tests/test_reader_rd8a_transcribe.py) — direct import
  - `test_the_render_digest_and_the_prompt_are_stable`

## Modification guidance

- Make changes here when the responsibility remains ink render within learnloop.pads; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/pads/ink_render.py](../../../../../../src/learnloop/pads/ink_render.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
