# Reader: selecting and highlighting on the original PDF (stage `reader-pdf-selection`)

Branch `reader/pdf-selection`, base `main` at `37a2a7e5f` (`mvp-0.25`,
migration head 204). Owner-requested (2026-10-14): make selecting and
highlighting on the **original page view** of a PDF feel good and robust,
using the block geometry GLM-OCR and Marker now give. Specs:
`docs/specs/spec_reader_workbench_v1.md` §4.1 (the friction audit, "one
interaction model on every source kind"), §4.2 (the intent box timing),
G52/G57; `docs/specs/ux_reader_workbench_v1.md` §4.1 (entry gestures: drag,
`Ctrl`+drag boxes, `Alt`+drag sweep, `Shift`+arrows, on the PDF surface and
the extracted text alike). Single authorities kept: `checkOffer.ts` decides
check offers, `content.sources.span_aliases` resolves old spans,
`content.sources.exam_material` decides protection, the sidecar's render lock
guards pdfium (this stage renders nothing with pdfium).

## 0. Plan

1. **The friction audit of the PDF view** (§1), written before any UI change
   (spec §4.1, G52).
2. **One selection model** (`selectionModel.ts`, pure): the extraction's
   blocks in reading order, each split into words that carry their code-point
   offsets in the block's own text; word boxes from the pdf.js text content
   where the page has a text layer (aligned to the extraction's words,
   hyphenated halves joined), estimated lines inside the block's box where it
   has none (a scan read by GLM-OCR); formula, table and figure blocks are
   one unit each. Hit-testing, drags, double/triple click, `Shift`+arrows,
   the selected text (`Ctrl+C`, math as LaTeX) and the region boxes all read
   this one model.
3. **Every selection resolves to canonical anchors** through the existing
   anchor code: each node carries `start`/`end` code points and the block's
   own slice as its quote, so `annotations.translate_selection` anchors it
   exactly by construction. The extracted-text view emits the same
   `ReaderSelection` shape through the same helper.
4. **Highlights from anchors**: `reader.source_annotations` gains the open
   reading and answers, per annotation, where it lands on it through
   `span_aliases` (here / moved after a re-read / needs choosing again /
   not on this reading); the PDF draws per-line region boxes from the model,
   with hover, keyboard focus, delete and undo; the text view marks the same
   placed blocks.
5. **Protection**: `reader.pdf_view` and `reader.render_view` say which of the
   reading's passages `exam_material` holds out (the whole reading when rule 4
   holds it back), and a selection touching one offers no model action.
6. **Feel**: the selection settles 150 ms after mouse-up (no flicker on
   double/triple click), nothing takes focus, only visible pages keep a canvas
   and text layer.
7. **Tests**: vitest (model, interaction, perf) on synthetic PDFs parsed by
   the real pdf.js and on the CC BY arXiv answer's GLM geometry; Python for
   anchor resolution, placements through re-reads and protection.

No schema change, no algorithm successor (display and anchors only).

## 1. Friction audit, before (the original-PDF view, `main` at `37a2a7e5f`)

Read from the code: `apps/learnloop-tauri/src/components/PdfReaderPane.tsx`,
`screens/ReaderScreen.tsx`, `screens/reader/NotesRail.tsx`, `AskRail.tsx`,
the sidecar's `reader.pdf_view`, `reader.capture`, `reader.source_annotations`
(`learnloop_sidecar/handlers/reader.py`) and `learnloop/reader/annotations.py`.
No funnel data on PDF selections exists beyond `reader_selection` counts
(`noteSelection(..., "pdf")`).

### 1.1 How selection works today

Three gestures, three code paths, three different quote sources:

| Gesture | Code | What is selected | Quote sent |
|---|---|---|---|
| **Plain drag** | native browser selection over pdf.js's bare `TextLayer` (`PdfReaderPane.tsx:1344`); `onMouseUp` → `resolveSelection` (`:962-1051`) | the glyph spans the browser selects, in DOM (content-stream) order | the **pdf.js glyph text**, attributed per text node to the block its client rects overlap most; an `Equation` block's quote is replaced by its whole extraction LaTeX |
| **`Ctrl`+drag boxes** | marquee (`:683-941`), committed when `Ctrl` is released | words whose DOM-measured rect centre falls in a box (`resolveMarquee`, `:781`), plus any block a box covers ≥ 25 % | glyph words joined with single spaces; equations whole; a block with no glyphs (a scan) falls back to its **whole** extraction text |
| **`Alt`+drag sweep** | block sweep (`:521-681`) | whole extraction blocks between the two blocks under the pointer, in reading order | each block's extraction text verbatim |

The extraction's blocks (`reader.pdf_view`: `spanId`, `page`, `bbox` in PDF
points top-left, `blockType`, `text`) are used only to attribute glyphs to
blocks and to paint. Selection never uses the extraction's reading order
except in the `Alt` sweep.

### 1.2 How a selection becomes a span anchor today

1. The pane calls `onTextSelection({spanId, quote, nodes:[{spanId, quote}]})`;
   `ReaderScreen` stores it as the capture (`ReaderScreen.tsx:2014`), flips the
   rail to Notes (unless Ask is open) and paints the **whole** of every
   touched block amber (`selectedSpans`, `PdfReaderPane.tsx:1421-1470`).
2. An action (`highlight`, a preset, Ask, a right-click tag, exercise import)
   sends `rawSelection: {nodes}` (no offsets) to the sidecar.
3. `annotations.translate_selection` (`annotations.py:217`) looks each quote
   up in its block's text (`_locate_quote`, `:143`): exact and unique →
   whitespace-normalised → canonical maths (`math_text.locate_by_canonical`)
   → fuzzy word alignment (≥ 50 % of the quote's words, offsets snapped
   outward to whitespace) → otherwise `needs_reanchor` (the learner's text is
   kept, the raw selection stored, nothing painted).
4. The segment is persisted with `span_id`, `block_content_hash`, code-point
   offsets, the exact quote, prefix/suffix and `geometry = {page, bbox}` — the
   **whole block's** box (`_segment_from_block`, `:192`).
5. On reopen, `refreshAnnotations` (`ReaderScreen.tsx:334`) reads
   `reader.source_annotations` (every annotation of the book, on any reading)
   and paints one wash per segment from that stored block box
   (`trails`, `:746`).

### 1.3 Every way it fails

| # | Case | What happens today | Where |
|---|---|---|---|
| F1 | **Scanned page** (image only; GLM-OCR or Marker OCR boxes, no text layer) | A plain drag selects nothing. Only `Ctrl`-boxes (whole blocks, by ≥ 25 % cover) and `Alt` sweeps (whole blocks) work: no word, line or sentence can be chosen on a scan | `resolveSelection` walks text-layer nodes only; `resolveMarquee` fallback `:872` |
| F2 | **Two-column page** | Native selection follows DOM order, not reading order: a drag from the bottom of the left column to the top of the right one selects whatever the content stream put between them (often the other column's lines, running heads, figure labels). Dragging through the column gutter makes the selection jump to the end of the layer: the bare `TextLayer` has no `endOfContent` guard (that lives in pdf.js's `TextLayerBuilder`, `web/pdf_viewer.mjs`, which the pane does not use) | `:1344`; `pdf_viewer.mjs` `endOfContent` |
| F3 | **Formula** (display) | Glyphs are junk (`𝑥`, private-use codes, missing spaces); a drag that touches one glyph quotes the whole LaTeX (good) but paints the whole block and cannot be clicked to select. **Inline** maths inside a paragraph stays glyph junk in the quote; anchoring then depends on the canonical/fuzzy tiers | `:1040`; `annotations.py:181-189` |
| F4 | **Table** | Cell glyphs in content-stream order; the quote is cell soup that rarely matches the extraction's Markdown table, so anchoring goes fuzzy or `needs_reanchor`; no way to take the table whole except an `Alt` sweep | `resolveSelection` (no `Table` case) |
| F5 | **Footnotes** | The extraction reads footnotes after the page's body (GLM recovers them from the text layer and orders them after the last block, `glm_ocr.py:1445`), but a native drag from the end of a page into the next page passes over the footnote in DOM order and quotes it | DOM order |
| F6 | **Hyphenation** | `compu-` / `tation` across a line break quote as `compu- tation`; exact and normalised lookups fail, so the anchor relies on the fuzzy tier (offsets snapped outward) or fails | `_locate_quote` tiers |
| F7 | **Ligatures, spacing** | `ﬁ`, `ﬂ`, missing or doubled spaces between pdf.js items: the quote differs from the extraction; same fuzzy dependence | `:969`, `:1004` |
| F8 | **Glyphs outside every box** | A text node whose rects overlap no block is dropped silently (meant for page numbers; also drops a line a tight GLM box missed) | `:1029-1032` |
| F9 | **Selection spanning blocks** | One node per block, but each text node goes to one block by largest overlap, so a span straddling a block edge goes to the wrong block; the "primary" span is the node with the longest quote | `:1028`, `:1049` |
| F10 | **Selection spanning pages** | Works in DOM order but crosses the 14 px gap between pages, where the browser selection jumps; any running head without a block is dropped, any with a block (Marker `PageHeader`) is excluded by type | `:1020-1022` |
| F11 | **Zoom and resize** | Every zoom step re-renders the page and `replaceChildren()` empties the text layer, so a live native selection vanishes mid-read; the committed capture survives only as whole-block paint | `:1343` |
| F12 | **Selection feedback** | After mouse-up the browser highlight is the only word-level feedback; the committed capture paints **whole blocks** (`selectedSpans`), so selecting one sentence lights the whole paragraph; clicking anywhere drops the word-level feedback | `:1427-1463` |
| F13 | **Highlights are whole blocks** | A saved highlight paints the stored block box, not its words. Two highlights in one paragraph are indistinguishable | `trails`, `ReaderScreen.tsx:746` |
| F14 | **Highlights after a re-read** | `reanchor_annotation` writes `geometry: None` (`annotations.py:483`), so every carried highlight **disappears** from the PDF after a re-read; an annotation still anchored on another reading is painted by its old span id's stored box (another reading's geometry, possibly another passage), and its span id marks a block of the open reading in the text view (`annotatedSpans`) | `annotations.py:483`; `ReaderScreen.tsx:746-760` |
| F15 | **Small targets, no interaction on highlights** | Trails are `pointer-events: none`: no hover, no click, no keyboard focus; their `title` never shows; delete exists only on the rail card | `:1411` |
| F16 | **Keyboard** | No `Shift`+arrows on the PDF (no caret in a text layer); selection is mouse only. No way to select a formula by keyboard | — |
| F17 | **Copy** | `Ctrl+C` copies pdf.js glyph text: ligatures, junk maths, hard line breaks, hyphens. Nothing copies on a scan | browser default |
| F18 | **Flicker** | Every mouse-up with a non-collapsed selection commits at once: a double-click commits, then a triple-click commits again; each commit re-renders the pane and flips the rail | `onMouseUp`, `:1053` |
| F19 | **Memory on a long book** | A page's `IntersectionObserver` only ever sets `visible = true` (`:1310`); every page scrolled past keeps its canvas (≈ 17 MB at 900 px, DPR 2) and its text-layer DOM for the rest of the visit. Reading 600 pages keeps 600 canvases | `:1306-1315` |
| F20 | **Held-out material** | A selection on a held-out passage or a reading rule 4 holds back shows every model action (Ask, the four background requests, the three "remember later" presets, exercise import); the sidecar refuses only after the click (`reader_dialogue.py:611`, `reader_requests.py:392`), so the learner meets a refusal, not an absent action | `NotesRail.tsx:221-247` |
| F21 | **Right-click tag** | Tags the live selection, else the committed marquee, else the whole block under the cursor; on a scan without a marquee only whole blocks | `:1064-1115` |

### 1.4 The workflows this stage touches (spec §4.1 columns)

"Step" counts each distinct learner act. Keys against the UX key map (UX §3.5).

| Workflow (on the original PDF) | Steps | Keyboard | Waits on a model | Focus / rail moves without the learner's act | Context lost |
|---|---|---|---|---|---|
| **Highlight a sentence** | 3: drag · (rail flips to Notes) · click *highlight* | No: no keyboard selection on the PDF; *highlight* is a Tab-reachable button only | None | Rail flips to Notes on every selection | The page shows the **whole paragraph** washed, and after a re-read nothing (F13, F14) |
| **Ask about a selection and get back to reading** | 4-5: drag · click the *ask* tab · type · `Ctrl+↵` · read | Selection mouse only; the rest by key since RW1a | The tutor answer | Rail flips to Notes first | Quote is glyph text (F3, F6, F7); on a scan only whole blocks (F1) |
| **Capture "test me later"** | 3: drag · (rail flips) · click *test me later* | Selection mouse only | None (queued) | Rail flips | On held-out material the action is offered, then refused (F20) |
| **Select a formula or table** | 2+: `Alt`+drag over it · (rail flips); a plain click does nothing | No | None | Rail flips | A table's plain-drag quote rarely anchors (F4) |
| **Copy a passage with maths** | 2: drag · `Ctrl+C` | Copy key only | None | — | Glyph junk instead of LaTeX (F17) |
| **Remove a highlight** | 3: open Notes · find the card · *delete* | Tab to the card's button | None | — | No way from the page; no undo |

## 2. Design (after)

*(written with the code; see below)*
