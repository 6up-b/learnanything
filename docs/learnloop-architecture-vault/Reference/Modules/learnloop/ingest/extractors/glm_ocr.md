---
title: "learnloop.ingest.extractors.glm_ocr"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/extractors/glm_ocr.py"
source_paths:
  - "src/learnloop/ingest/extractors/glm_ocr.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ingest.extractors"
layer: "infrastructure"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
aliases:
  - "learnloop.ingest.extractors.glm_ocr module"
  - "src/learnloop/ingest/extractors/glm_ocr.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ingest-extractors"
---

# `learnloop.ingest.extractors.glm_ocr`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ingest.extractors.glm_ocr` exists within [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] to own the behavior summarized by its module contract: GLM-OCR's complete layout-and-recognition pipeline as a DocumentExtractor.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py) |
| Source lines | 1537 |
| Owning package | [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class GlmOcrExtractionError(RuntimeError)` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 127) — GLM-OCR could not read the document (transport, provider or shape).
- `class GlmOcrConsentRequired(GlmOcrExtractionError)` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 131) — A hosted run was attempted without the whole-file OK.
- `glm_api_key(config: dict | None=None) -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 138) — The z.ai key from the environment the app loaded (shell, vault .env, machine settings.env): the configured variable first, then the aliases.
- `is_loopback_url(url: str) -> bool` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 150)
- `local_available(config: dict | None=None) -> bool` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 164) — Whether the self-hosted server accepts connections: a TCP connect only, no upload and no inference.
- `selected_backend(config: dict | None=None, *, local_only: bool=False, probe: bool=True) -> str | None` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 185) — Which GLM-OCR backend can run now, or None.
- `estimate(pages: int | None, config: dict | None=None, *, backend: str='api') -> dict[str, Any]` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 211) — A planning estimate for previews: pages x ESTIMATED_TOKENS_PER_PAGE at the configured price (local runs cost nothing).
- `class GlmOcrDocumentExtractor` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 278)
  - `__init__(self, *, config: dict[str, Any] | None=None, backend: str | None=None)` (line 281; internal)
  - `version(self) -> str` (line 296; public)
  - `model_versions(self) -> dict[str, str]` (line 299; public)
  - `leaves_this_computer(self) -> bool` (line 305; public) — Whether reading sends the document off this computer: always for z.ai, and for a self-hosted server not on a loopback address.
  - `extract(self, raw_bytes: bytes, context: ExtractionContext) -> DocumentIR` (line 311; public)
  - `_window(self, raw: bytes, mime: str, reader: Any, pages: list[int], *, total_pages: int, context: ExtractionContext, asset: str | None=None) -> list[tuple[dict, list[int]]]` (line 359; internal)
  - `_answer(self, payload: dict, pages: list[int], context: ExtractionContext) -> dict` (line 404; internal) — One window's answer, read before the next window is paid for: a layout LearnLoop can't read stops the run here, not after the book.
  - `_checkpoint_key(self, asset: str, pages: list[int]) -> str` (line 412; internal)
  - `_endpoint(self) -> str` (line 419; internal)
  - `_request(self, payload: dict, page_count: int, *, interrupt=None) -> dict` (line 430; internal)
  - `_record_usage(self, receipt: dict, result: dict, page_count: int) -> None` (line 512; internal)
- `is_glm_document(raw: bytes) -> bool` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 554)
- `is_image_document(raw: bytes) -> bool` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 562)
- `responses_to_ir(results: list[tuple[dict, list[int]]], *, sizes: list[tuple[float, float]], outline: list[dict], version: str, text_layer: PageTextLayer | None=None) -> DocumentIR` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 1348) — Map GLM-OCR responses (each with the zero-based pages it covers) to the IR.

### Module constants

- `EXTRACTOR_NAME` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 93)
- `API_URL` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 94)
- `LOCAL_URL` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 95)
- `PDF_LIMIT` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 97)
- `IMAGE_LIMIT` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 98)
- `MAX_PAGES_PER_REQUEST` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 99)
- `ESTIMATED_TOKENS_PER_PAGE` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 107)
- `LOCAL_RENDER_SCALE` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 109)
- `MAP_VERSION` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 117)
- `LAYOUT_MODEL` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 118)
- `RECOGNITION_MODEL` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 119)
- `UNAVAILABLE_MESSAGE` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 120)
- `CONSENT_MESSAGE` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 121)
- `KEY_ENV_ALIASES` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 122)
- `_MAX_ATTEMPTS` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 123)
- `_MAX_RETRY_AFTER_SECONDS` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 124)
- `_PROBES` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 160)
- `_PROBE_TTL_SECONDS` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 161)
- `_TITLE_LEVELS` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 807)
- `_BLOCK_TYPES` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 809)
- `_MARKDOWN_HEADING` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 820)
- `_MARKDOWN_IMAGE` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 821)
- `_WRAPPER_TAGS` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 856)
- `_WRAPPER_OPEN` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 857)
- `_WRAPPER_CLOSE_END` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 861)
- `_ENVIRONMENT_WORDS` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 883)
- `_SPLIT_LABEL` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 890)
- `_KIND_AFTER` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 894)
- `_ENUMERATOR` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 896)
- `_LABEL_STEP` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 899)
- `_TEXT_COMMANDS` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 963)
- `_LATEX_COMMAND` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 967)
- `_SPAN_WORD` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 968)
- `_MATHS_WORDS` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 969)
- `_PROSE_SHORT` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 974)
- `_AMOUNT` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 992)
- `_MATHS_MARK` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 1088)
- `_CODE_TOKENS` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 1089)
- `_CODE_CALL` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 1090)
- `_PROSE_PAIR` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 1091)
- `_CODE_LINES` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 1092)
- `_TITLE_PREFIX` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 1127)
- `_TITLE_MARKUP` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 1132)
- `_NON_ALNUM` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 1133)
- `_STRAY_LT` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 1256)
- `_LABEL_TYPES` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 1344)
- `_PROSE_TYPES` ([src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 1345)

### Explicit exports

`__all__` declares:

- `API_URL`
- `CONSENT_MESSAGE`
- `ESTIMATED_TOKENS_PER_PAGE`
- `GlmOcrConsentRequired`
- `GlmOcrDocumentExtractor`
- `GlmOcrExtractionError`
- `LOCAL_URL`
- `MAP_VERSION`
- `TextSegment`
- `UNAVAILABLE_MESSAGE`
- `estimate`
- `glm_api_key`
- `is_glm_document`
- `is_image_document`
- `is_loopback_url`
- `local_available`
- `responses_to_ir`
- `selected_backend`

## Internal implementation anchors

- `class _NoRedirect(HTTPRedirectHandler)` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 231)
- `_open(request: Request, timeout: float)` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 237)
- `_provider_error(exc: HTTPError, secret: str) -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 241) — The provider's own error code/message, short and without the key.
- `_retry_after(exc: HTTPError, attempt: int) -> float` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 265)
- `_mime(raw: bytes) -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 544)
- `_data_uri(mime: str, raw: bytes) -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 566)
- `_pdf_pages(raw: bytes) -> tuple[Any, list[tuple[float, float]]]` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 570) — The reader and each page's displayed size in PDF points (crop box, width and height swapped for a quarter-turn rotation): the space the Reader's PDF view (pdfium's page size) draws block boxes in.
- `_image_size(raw: bytes) -> tuple[float, float]` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 594)
- `_pdf_subset(reader: Any, pages: list[int]) -> bytes` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 604)
- `_render_pages(raw: bytes, pages: list[int]) -> list[str]` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 618) — PNG data URIs of the selected pages for the self-hosted server, rendered in a pdfium worker process (pdfium is not thread-safe, and the Reader renders with it in this one).
- `_layout_value(result: dict) -> Any` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 643)
- `_is_region(value: Any) -> bool` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 660)
- `_page_regions(result: dict, count: int, page_ids: list[int] | None=None) -> tuple[list[list[dict]], str]` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 664) — Per-page region lists for one request's ``count`` pages, and the name of the response shape seen (kept in extraction health).
- `_saved_window_reader(pages: list[int])` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 716) — Read a saved window answer back: one this mapping can no longer read is a stale checkpoint (``ValueError``), discarded and asked for again.
- `_validated(result: dict, pages: list[int]) -> None` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 732) — Raise unless ``result`` holds a readable layout for exactly ``pages``.
- `_page_dimensions(result: dict) -> list[dict]` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 745)
- `_bbox(region: dict, target: tuple[float, float], page: dict) -> list[float] | None` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 750) — Region box -> PDF points (or image pixels), top-left origin.
- `_positive(value: Any) -> float | None` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 796)
- `_labels(region: dict) -> tuple[str, str]` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 824)
- `_block_type_and_heading(region: dict, text: str) -> tuple[str, int | None, str]` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 830) — (IR block type, heading level as the answer marks it or None, text) for one region's unwrapped text.
- `_unwrap_html(text: str) -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 864) — The text inside the HTML wrappers the hosted service puts around titles and captions (``<div align="center">...</div>``, on every doc_title and figure_title seen).
- `_number(text: str) -> tuple[int, ...]` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 902)
- `_join_split_labels(blocks: list[tuple[str, str]]) -> list[str]` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 906) — The texts of the Text and SectionHeader blocks, (type, text) in reading order, with each label's number the recognition model split ("1.
- `_prose_words(span: str) -> int` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 977) — How many ordinary words a would-be inline maths span holds ("1, one worth", "5 and pays", "10 if "): words outside \text{...} and environment names, other than the usual operator names.
- `_closing_dollars(text: str, start: int, size: int) -> int | None` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 995) — Where the run of ``size`` unescaped dollars closing the maths opened before ``start`` begins, or None.
- `_is_amount(text: str, end: int, closer: int | None, spaced: bool, paired: bool) -> bool` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 1020) — Whether the dollar ending at ``end``, before a number, is an amount rather than maths it would open, closed at ``closer`` (None: nothing closes it).
- `_escape_currency(text: str) -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 1041) — Escape the dollars of amounts ("$1000", "$5 and $10", "$ 18,000") so remark-math never pairs them as maths, and keep real maths, padded or not ("$ \infty $", "$10^{100}$", "$1/(j^2 + k)$", "$2^{n}$", "$ 2 \leq j $").
- `_holds_code(text: str) -> bool` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 1101) — Whether an ``algorithm`` region holds code (Blitzstein's R) rather than a boxed definition or result ("1.6 notation: ...").
- `_title_keys(title: str) -> tuple[str, str]` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 1136) — A heading's or bookmark's text for matching: letters and digits only, with and without its numbering ("2.1.
- `_numbering_depth(title: str) -> int | None` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 1144) — How deep a heading's own numbering puts it: "2." 1, "2.1." 2, "2.1.1" 3, "1A" 2, "A.1" 2, "Chapter 3" 1; None when unnumbered.
- `class _Headings` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 1161) — Each heading's depth, since the service marks every heading but the document title "##": the PDF's outline when a bookmark names it (within two pages), else its numbering ("2.1." under "2."), else one level under the last heading so placed.
- `_equation_text(text: str) -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 1229)
- `_table_cells(cells: Any) -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 1238) — The older flat shape's table cells, as HTML for the Markdown converter.
- `class _TableParser(HTMLParser)` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 1263)
- `_table_markdown(text: str) -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 1299) — HTML tables -> GFM: the Reader renders GFM tables but never raw HTML.
- `_region_order(region: dict) -> tuple[int, int]` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 1336)
- `_heading_units(headings: list[dict[str, Any]], blocks: list[DocumentBlock]) -> list[DocumentUnit]` ([source](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py), line 1486) — Units at detected headings, split by block (several headings can share a page); the text before the first heading belongs to the first unit.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/acquisition_preview|learnloop.content.pipeline.acquisition_preview]] — imports `CONSENT_MESSAGE`, `estimate`, `selected_backend`; statically calls `estimate`, `selected_backend`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `selected_backend`; statically calls `selected_backend`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `UNAVAILABLE_MESSAGE`, `estimate`, `is_image_document`, `selected_backend`; statically calls `estimate`, `is_image_document`, `selected_backend`
- [[Reference/Modules/learnloop/content/pipeline/reread|learnloop.content.pipeline.reread]] — imports `LOCAL_URL`, `estimate`, `is_loopback_url`; statically calls `estimate`, `is_loopback_url`
- [[Reference/Modules/learnloop/content/sources/pdf_extraction|learnloop.content.sources.pdf_extraction]] — imports `CONSENT_MESSAGE`, `GlmOcrConsentRequired`, `GlmOcrExtractionError`, `UNAVAILABLE_MESSAGE`, `selected_backend`; statically calls `selected_backend`
- [[Reference/Modules/learnloop/ingest/extractors/__init__|learnloop.ingest.extractors]] — imports `EXTRACTOR_NAME`, `GlmOcrConsentRequired`, `GlmOcrDocumentExtractor`, `GlmOcrExtractionError`, `UNAVAILABLE_MESSAGE`, `is_image_document`, `selected_backend`; statically calls `GlmOcrDocumentExtractor`, `is_image_document`, `selected_backend`
- [[Reference/Modules/learnloop_sidecar/handlers/first_run|learnloop_sidecar.handlers.first_run]] — imports `selected_backend`; statically calls `selected_backend`
- [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]] — imports `glm_api_key`, `selected_backend`; statically calls `glm_api_key`, `selected_backend`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `ModelCheckpoint`, `model_call`; calls `ModelCheckpoint`, `model_call`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`; calls `SpendBudget`, `SpendCaps`, `SpendEstimate`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `GlmOcrConfig`; calls `GlmOcrConfig`
- [[Reference/Modules/learnloop/ingest/block_roles|learnloop.ingest.block_roles]] — imports `classify_block_role`, `numbered_label`; calls `classify_block_role`, `numbered_label`
- [[Reference/Modules/learnloop/ingest/extractors/base|learnloop.ingest.extractors.base]] — imports `ExtractionContext`, `units_from_toc_entries`; calls `units_from_toc_entries`
- [[Reference/Modules/learnloop/ingest/extractors/glm_text_layer|learnloop.ingest.extractors.glm_text_layer]] — imports `EQUATION_NUMBERS_RECOVERED`, `FOOTNOTES_RECOVERED`, `NO_TEXT_LAYER`, `PARTIAL_TEXT_LAYER`, `PageTextLayer`, `PageTexts`, `PdfiumWorkerError`, `TextSegment`, `equation_numbers`, `footnotes`, `pdfium_worker`, `read_text_layer`, `text_layer_engine`, `with_equation_tag`; calls `PageTexts`, `equation_numbers`, `footnotes`, `pdfium_worker`, `read_text_layer`, `text_layer_engine`, `with_equation_tag`
- [[Reference/Modules/learnloop/ingest/extractors/pypdf|learnloop.ingest.extractors.pypdf]] — imports `read_embedded_outline`; calls `read_embedded_outline`
- [[Reference/Modules/learnloop/ingest/hashing|learnloop.ingest.hashing]] — imports `semantic_hash`; calls `semantic_hash`
- [[Reference/Modules/learnloop/ingest/ir|learnloop.ingest.ir]] — imports `DocumentBlock`, `DocumentIR`, `DocumentUnit`, `IR_SCHEMA_VERSION`, `PageHealth`; calls `DocumentIR`, `DocumentUnit`, `PageHealth`

### Platform and third-party dependencies

- Standard library: `__future__`, `base64`, `hashlib`, `html`, `http`, `io`, `ipaddress`, `json`, `math`, `os`, `re`, `socket`, `time`, `types`, `typing`, `urllib`, `uuid`
- Third party: `PIL`, `pypdf`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/acquisition_preview|learnloop.content.pipeline.acquisition_preview]], [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/content/pipeline/reread|learnloop.content.pipeline.reread]], [[Reference/Modules/learnloop/content/sources/pdf_extraction|learnloop.content.sources.pdf_extraction]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ad_ingest_fakes.py](../../../../../../../tests/ad_ingest_fakes.py) — direct import
- [tests/identity_pins_helpers.py](../../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/test_glm_ocr.py](../../../../../../../tests/test_glm_ocr.py) — direct import
  - `test_429_and_5xx_retry_with_their_own_admission_and_receipt`
  - `test_a_whole_short_pdf_goes_as_one_data_uri_with_its_page_range_and_bearer_key`
  - `test_an_unanswering_local_server_is_not_selected`
  - `test_auto_falls_back_on_a_glm_failure_but_never_past_a_refusal`
  - `test_cr_f1_a_worker_that_crashes_or_hangs_is_recorded_and_the_reading_goes_on`
  - `test_cr_f1_extraction_never_enters_pdfium_in_this_process_while_the_reader_renders`
  - `test_cr_f3_currency_never_takes_the_opening_dollar_of_maths_beside_it`
  - `test_cr_f4_an_exact_bookmark_beats_one_that_matches_only_without_its_numbering`
  - `test_cr_f5_a_formulas_own_brackets_never_stop_an_equation_number_from_coming_back`
  - `test_cr_f6_a_footnote_line_that_the_body_repeats_elsewhere_is_kept`
  - `test_errors_name_the_provider_reason_but_never_the_key`
  - `test_heading_units_split_by_block_and_nest_by_level`
  - `test_html_tables_become_gfm_with_spans_escaped_pipes_and_untouched_maths`
  - `test_images_are_sent_whole_and_capped_at_10_mb`
  - `test_incomplete_or_unreadable_layouts_fail_rather_than_read_as_empty`
  - `test_local_runs_only_when_chosen_and_answering_and_a_local_only_reading_never_uploads`
  - `test_missing_usage_is_charged_at_the_labelled_estimate`
  - `test_older_and_variant_shapes_normalise_too`
  - `test_q1_the_estimate_is_3500_tokens_a_page_from_the_live_receipts`
  - `test_q2a_html_wrappers_never_reach_block_text_or_section_paths`
  - `test_q2b_heading_depth_comes_from_the_outline_else_the_numbering`
  - `test_q2b_numbered_subsections_under_a_bookmark_are_siblings_and_bookmarks_match_through_latex`
  - `test_q2c_split_numbering_is_collapsed_where_it_is_a_label`
  - `test_q2d_currency_dollars_are_escaped_and_real_maths_is_kept`
  - `test_q2e_algorithm_regions_are_code_only_when_they_hold_code`
  - `test_q3_a_footnote_under_the_left_column_is_found_though_the_right_column_runs_lower`
  - `test_q3_a_number_inside_a_formula_or_across_the_gutter_is_not_an_equation_number`
  - `test_q3_equation_numbers_are_never_guessed_or_doubled`
  - `test_q3_margin_notes_and_lines_the_answer_dropped_are_not_footnotes_and_hyphens_join`
  - `test_q3_scans_and_images_record_that_nothing_could_be_recovered`
  - `test_q3_some_pages_without_a_text_layer_are_recorded_as_such`
  - `test_q3_text_layer_boxes_follow_the_rotated_crop_box_the_reader_draws_in`
  - `test_q4_the_recorded_arxiv_answer_reads_cleanly`
  - `test_r2_f1_a_local_repair_never_goes_to_a_glm_server_on_another_computer`
  - `test_r2_f5_a_timeout_is_tried_once_more_and_the_default_wait_is_the_sdks`
  - `test_r2_f5_a_window_glm_ocr_answered_wrongly_stops_before_the_next_is_paid`
  - `test_r2_f5_paid_windows_are_kept_so_trying_again_pays_only_for_the_rest`
  - `test_r2_f6_a_cut_off_answer_or_an_unrenderable_page_falls_back_under_auto`
  - `test_r2_f8_page_sizes_come_from_data_info_before_a_regions_own_size`
  - `test_raw_base64_the_zhipu_endpoint_and_an_oversize_window_splits`
  - `test_redirects_are_refused_so_the_key_and_file_never_follow_them`
  - `test_regions_map_to_blocks_in_reading_order_with_roles_text_and_point_boxes`
  - `test_spend_refusals_send_nothing_and_no_ok_sends_nothing`
  - `test_the_configured_key_variable_comes_first_then_the_aliases`
  - `test_the_daily_gate_prices_glm_receipts_and_local_runs_cost_nothing`
  - `test_the_endpoint_must_be_https_and_plain`
  - `test_the_local_backend_reads_an_image_as_one_page`
  - `test_the_local_backend_renders_pdf_pages_for_a_real_http_server`
  - `test_the_preview_estimates_pages_and_names_the_upload`
  - `test_the_self_hosted_shapes_one_unit_per_image_and_0_to_1000_boxes`
  - `test_versions_name_backend_models_and_mapping_so_caches_re_extract`
- [tests/test_reader_pdf_selection.py](../../../../../../../tests/test_reader_pdf_selection.py) — direct import
- [tests/test_reread_safety.py](../../../../../../../tests/test_reread_safety.py) — direct import
  - `test_a_glm_reread_of_a_sliced_book_sends_only_its_pages`
- [tests/test_reread_safety_landing.py](../../../../../../../tests/test_reread_safety_landing.py) — direct import
  - `test_a_glm_reread_uploads_pages_of_the_stored_original_not_the_pointer`
- [tests/test_rw5c_block_policy.py](../../../../../../../tests/test_rw5c_block_policy.py) — direct import
  - `test_every_type_an_extractor_writes_is_classified`

## Modification guidance

- Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/extractors/glm_ocr.py](../../../../../../../src/learnloop/ingest/extractors/glm_ocr.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
