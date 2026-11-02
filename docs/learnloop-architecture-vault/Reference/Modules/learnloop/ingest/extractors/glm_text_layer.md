---
title: "learnloop.ingest.extractors.glm_text_layer"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/extractors/glm_text_layer.py"
source_paths:
  - "src/learnloop/ingest/extractors/glm_text_layer.py"
source_commit: "85f76fd12f14a0be535e01bec6f7c278be4c2016"
source_commit_timestamp: "2026-10-14T20:08:58-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ingest.extractors"
layer: "infrastructure"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
aliases:
  - "learnloop.ingest.extractors.glm_text_layer module"
  - "src/learnloop/ingest/extractors/glm_text_layer.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ingest-extractors"
---

# `learnloop.ingest.extractors.glm_text_layer`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ingest.extractors.glm_text_layer` exists within [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] to own the behavior summarized by its module contract: A PDF's own text layer, for what GLM-OCR's answers never carry.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ingest/extractors/glm_text_layer.py](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py) |
| Source lines | 682 |
| Owning package | [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `85f76fd12f14a0be535e01bec6f7c278be4c2016` |
| Commit timestamp | `2026-10-14T20:08:58-04:00` |

## Public API

- `class TextSegment(NamedTuple)` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 77) — One text run of a PDF page in the Reader's points (top-left origin).
- `class TextRun(NamedTuple)` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 87) — Segments of one line that sit together (a column's line, a number in the margin), joined into text.
- `text_layer_engine() -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 103) — What reads a PDF's text layer here: part of the extractor's identity, since it decides whether footnotes and equation numbers come back.
- `class PdfTextLayer` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 113) — ``layer(page)``: the zero-based page's text segments, None when pdfium can't read the page.
  - `__init__(self, document: Any)` (line 118; internal)
  - `__call__(self, index: int) -> list[TextSegment] | None` (line 121; internal)
  - `close(self) -> None` (line 151; public)
- `read_text_layer(raw: bytes, pages: Sequence[int]) -> tuple[PageTextLayer | None, str | None]` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 168) — The PDF's text layer on ``pages`` (zero-based), read by pdfium in a worker process; or None and the health flag saying why not (pypdfium2 missing, a PDF pdfium can't open, a worker that crashed or ran out of time).
- `class PdfiumWorkerError(RuntimeError)` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 207) — The worker could not do the pdfium work (pypdfium2 missing, a PDF pdfium can't open, a crash, a failure or a timeout).
- `pdfium_worker(task: str, raw: bytes, pages: Sequence[int], **options: Any) -> Any` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 212) — Run ``task`` on the PDF ``raw`` in a worker process: "text", each page's text segments by page; "render", each page as a PNG data URI at ``scale``.
- `text_runs(segments: Sequence[TextSegment]) -> list[TextRun]` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 317) — Segments grouped into lines, each line split into runs at wide gaps (a column gutter, a number in the margin).
- `class PageTexts` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 382) — The text segments and runs of every page read, and the running lines among them: headers and footers, short lines in the top or bottom margin that come back at the same height on another page read (digits stand for any number).
  - `__init__(self, layer: PageTextLayer, pages: Sequence[int], heights: Callable[[int], float])` (line 390; internal)
  - `segments(self, page: int) -> list[TextSegment] | None` (line 422; public)
  - `runs(self, page: int) -> list[TextRun] | None` (line 426; public)
  - `is_furniture(self, run: TextRun) -> bool` (line 430; public) — A page number, or a running line where it runs.
- `class EquationNumber(NamedTuple)` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 480) — A display's number from the text layer, and whether it lies beside the display's region rather than in it (then the recognised text can't hold it).
- `equation_numbers(segments: Sequence[TextSegment] | None, equations: dict[int, Sequence[float]], boxes: Sequence[Sequence[float] | None]) -> dict[int, EquationNumber]` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 489) — The number to tag each display region with, by region position.
- `with_equation_tag(text: str, number: EquationNumber) -> str | None` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 533) — ``text`` (a display, ``$$...$$`` or ``\[...\]``) tagged with ``number``, or None when it already carries a number or can't take one.
- `footnotes(runs: Sequence[TextRun] | None, boxes: Sequence[Sequence[float] | None], page_size: tuple[float, float], present: str, *, is_furniture: Callable[[TextRun], bool]) -> list[tuple[list[float], str]]` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 560) — Footnotes the answer lacks on one page, as (box, text) in reading order.

### Module constants

- `NO_TEXT_LAYER` ([src/learnloop/ingest/extractors/glm_text_layer.py](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 47)
- `PARTIAL_TEXT_LAYER` ([src/learnloop/ingest/extractors/glm_text_layer.py](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 48)
- `TEXT_LAYER_UNAVAILABLE` ([src/learnloop/ingest/extractors/glm_text_layer.py](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 49)
- `FOOTNOTES_RECOVERED` ([src/learnloop/ingest/extractors/glm_text_layer.py](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 50)
- `EQUATION_NUMBERS_RECOVERED` ([src/learnloop/ingest/extractors/glm_text_layer.py](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 51)
- `_FOOTNOTE_ZONE` ([src/learnloop/ingest/extractors/glm_text_layer.py](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 54)
- `_RUNNING_MARGIN` ([src/learnloop/ingest/extractors/glm_text_layer.py](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 58)
- `_RUNNING_CHARS` ([src/learnloop/ingest/extractors/glm_text_layer.py](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 59)
- `_RUNNING_HEIGHT` ([src/learnloop/ingest/extractors/glm_text_layer.py](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 60)
- `_SUPERSCRIPT` ([src/learnloop/ingest/extractors/glm_text_layer.py](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 61)
- `_MARKER` ([src/learnloop/ingest/extractors/glm_text_layer.py](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 62)
- `_SYMBOL_MARK` ([src/learnloop/ingest/extractors/glm_text_layer.py](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 63)
- `_PAGE_NUMBER` ([src/learnloop/ingest/extractors/glm_text_layer.py](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 66)
- `_EQUATION_NUMBER` ([src/learnloop/ingest/extractors/glm_text_layer.py](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 69)
- `_TRAILING_NUMBER` ([src/learnloop/ingest/extractors/glm_text_layer.py](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 72)
- `_DISPLAY_ENVIRONMENT` ([src/learnloop/ingest/extractors/glm_text_layer.py](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 73)
- `_ALNUM` ([src/learnloop/ingest/extractors/glm_text_layer.py](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 74)
- `_SPACING_ACCENT` ([src/learnloop/ingest/extractors/glm_text_layer.py](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 156)
- `_COMBINING` ([src/learnloop/ingest/extractors/glm_text_layer.py](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 157)
- `_WORKER` ([src/learnloop/ingest/extractors/glm_text_layer.py](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 201)
- `_WORKER_MIN_SECONDS` ([src/learnloop/ingest/extractors/glm_text_layer.py](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 203)
- `_WORKER_SECONDS_PER_PAGE` ([src/learnloop/ingest/extractors/glm_text_layer.py](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 204)
- `_LATEX` ([src/learnloop/ingest/extractors/glm_text_layer.py](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 638)
- `_WORDS` ([src/learnloop/ingest/extractors/glm_text_layer.py](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 639)

### Explicit exports

`__all__` declares:

- `EQUATION_NUMBERS_RECOVERED`
- `FOOTNOTES_RECOVERED`
- `NO_TEXT_LAYER`
- `PARTIAL_TEXT_LAYER`
- `EquationNumber`
- `PageTexts`
- `PdfTextLayer`
- `PdfiumWorkerError`
- `TEXT_LAYER_UNAVAILABLE`
- `TextRun`
- `TextSegment`
- `equation_numbers`
- `footnotes`
- `pdfium_worker`
- `read_text_layer`
- `text_layer_engine`
- `text_runs`
- `with_equation_tag`

## Internal implementation anchors

- `_clean(text: str) -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 160) — A run's text: pdfium's hyphenation mark (\x02) kept as a soft hyphen, spacing accents joined to their letter, whitespace collapsed.
- `_worker_main() -> None` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 240) — The worker's side: the request in ``sys.argv[1]``, the PDF on stdin, ``{"result": ...}`` or ``{"error": ...}`` on stdout.
- `_placed(left: float, bottom: float, right: float, top: float, text: str, crop: tuple[float, ...], rotation: int) -> TextSegment` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 288) — PDF user space -> the Reader's view: crop-box origin, top-left, rotated clockwise by the page's /Rotate like the page is shown.
- `_height(item: Any) -> float` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 313)
- `_run(segments: list[TextSegment]) -> TextRun` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 351)
- `_running_key(text: str) -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 438)
- `_normalised(text: str) -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 442)
- `_x_overlap(a: Any, b: Sequence[float]) -> float` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 446)
- `_inside(run: Any, box: Sequence[float], tolerance: float=1.5) -> bool` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 450) — Whether most of ``run`` lies inside ``box``.
- `_set_apart(segment: TextSegment, segments: Sequence[TextSegment]) -> bool` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 462) — Whether a "(n)" stands apart on its line, as an equation number does (flush right, set off from the display), unlike "F (2)" or "M(0)" inside a formula, whose neighbours sit a thin space away (1.4-2.4 pt in the live books, against 6.7 pt and more for a number).
- `_lead_stripped(run: TextRun) -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 634)
- `class _Seen` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 642) — The text a page's blocks already hold, to never repeat it: its letters and digits, and the pairs of consecutive words (three letters or more, LaTeX commands dropped, so "$ v_{2}, \ldots $" and "𝑣2 , …" agree).
- `_already_read(text: str, seen: _Seen) -> bool` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py), line 653)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ingest/extractors/glm_ocr|learnloop.ingest.extractors.glm_ocr]] — imports `EQUATION_NUMBERS_RECOVERED`, `FOOTNOTES_RECOVERED`, `NO_TEXT_LAYER`, `PARTIAL_TEXT_LAYER`, `PageTextLayer`, `PageTexts`, `PdfiumWorkerError`, `TextSegment`, `equation_numbers`, `footnotes`, `pdfium_worker`, `read_text_layer`, `text_layer_engine`, `with_equation_tag`; statically calls `PageTexts`, `equation_numbers`, `footnotes`, `pdfium_worker`, `read_text_layer`, `text_layer_engine`, `with_equation_tag`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `base64`, `collections`, `importlib`, `io`, `json`, `re`, `statistics`, `subprocess`, `sys`, `typing`, `unicodedata`
- Third party: `pypdfium2`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]

Static participation evidence comes from [[Reference/Modules/learnloop/ingest/extractors/glm_ocr|learnloop.ingest.extractors.glm_ocr]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_glm_ocr.py](../../../../../../../tests/test_glm_ocr.py) — direct import
  - `test_cr_f1_a_worker_that_crashes_or_hangs_is_recorded_and_the_reading_goes_on`

## Modification guidance

- Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/extractors/glm_text_layer.py](../../../../../../../src/learnloop/ingest/extractors/glm_text_layer.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
