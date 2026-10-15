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

Commits: `0adf0253c` (this audit), `b1087be0a` (the pure model, the
sidecar's placements and protection), `4073fbd50` (the pane, highlights,
undo, protection in the rails), `b9899fbe6` (what the real-UI look found),
`bc9f915ab` (this record; placements read block hashes without loading the
reading), `e2108f0c3` (after the 2026-10-15 restart: `reader.pdf_view` loads
the IR only when the original is stored; with none, protection's span ids
come from the narrow block-hash query, in reading order, so the wire is
unchanged), and the commit that records the gate.

### 2.1 One selection model

`apps/learnloop-tauri/src/components/pdfSelection/`:

| File | What it is |
|---|---|
| `tokens.ts` | A block's units: maximal runs of non-space characters, an inline formula (`$…$`, `\(…\)`) one unit with the run it touches; NFKC comparison keys (ligatures fold); UTF-16 ↔ code points |
| `geometry.ts` | Where a block's units sit on its page, in PDF points (top-left, the extraction's box space, zoom-free): from the page's text content when it has one (glyph words split by Helvetica advance widths, grouped into lines, aligned to the extraction's tokens by key with a short lookahead; a word hyphenated at a line end joined to its other half; units with no glyph laid over the glyph runs between matched neighbours); estimated lines inside the block's box when it has none (a scan read by GLM-OCR or OCR'd by Marker); one region (the block's box) for a formula, table or figure |
| `model.ts` | `SelectionModel`: the extraction's selectable blocks in reading order (furniture and empty blocks left out, but their boxes kept so a running head's glyphs never land in a paragraph). Hit-testing (a figure with no text selects nothing, never its caption), word/line moves, `selectionNodes` (one exact slice per block, code-point offsets), `selectionText` (clean copy: one space for the extraction's line breaks, maths as LaTeX, a paragraph running on over a page or column break joined), `anchorRange` (an anchor's words), `rangeRects` (one box per line per block), `marqueeRanges`, and `exactNode` (the extracted-text view's node in the same shape) |
| `usePdfSelection.ts` | The interaction: plain drag (rAF-throttled, auto-scroll at the edges, across columns, blocks and pages), click (caret on text; a formula, table or figure whole), double click (word), triple click (passage), Shift+click, Shift+←/→ (word), Shift+↑/↓ (line, keeping the column), Shift+Home/End, Ctrl+drag boxes (released Ctrl selects their union), Alt+drag (whole passages), Esc, Ctrl+C. A selection settles **150 ms** after the mouse is released or the last key (spec §4.2) and only then reaches the Reader; nothing in it moves focus except the learner's own click on a page |
| `highlights.ts` | Highlights from placements: `here`/`moved` drawn on their words, `flagged` as a dashed outline on the passage that took their place, `elsewhere` not drawn; hit-testing; plain-word labels |
| `PdfSelectionLayer.tsx` | One page's paint (selection, caret, highlights, boxes being drawn), a keyboard stop per highlight (`role="button"`, an accessible name with its kind, quote, state and note; Enter opens it, Delete removes it), and the open highlight's chip (*open note*, *remove*). Static: nothing animates |

`PdfReaderPane.tsx` turns the browser's own selection off over the pages
(the pdf.js text layer stays, transparent and inert, for find and screen
readers), builds the model from `reader.pdf_view`'s blocks, gives it each
page's text content as the page is drawn (the same content the text layer is
drawn from), and mounts a layer only on pages near the view. A page more than
1200 px from the view gives back its canvas pixels and its text-layer DOM
(F19); its size stays, so nothing moves. Per-page box arrays keep their
identity when unchanged, so a drag frame redraws only the pages it changes.

**The text view shares the model's shape.** Its own selection stays native
(it is real text), but `collectSelectionNodes` sends each block's part
through `exactNode`: when the quote is found once in the block's text, the
node carries the exact slice and code-point offsets the PDF view would send.
Both views anchor, restore (the return stack) and paint a capture the same
way; the PDF view paints a text-view capture word by word when its offsets
are known, else its whole passage.

### 2.2 From a selection to anchors (unchanged authority)

Each node is `{spanId, quote, start, end}` with `quote ==
block.text[start:end]` in code points, so `annotations.translate_selection`
anchors it exactly on its first branch, without the whitespace, canonical
maths or fuzzy tiers (F3, F6, F7 no longer reach them from the PDF). The
sidecar stays the authority: offsets that no longer name the quote are
relocated by the quote or fail visibly (`test_a_node_whose_offsets_drifted…`).
A cross-language contract file (`fixtures/selection_contract.json`, written by
`arxiv.test.ts`, anchored by `tests/test_reader_pdf_selection.py`) pins twelve
selections — two columns, a hyphenated word, a page break with its footnote,
a formula, a table, inline maths, letters outside the BMP on a scan, and five
on the arXiv answer's GLM geometry — to exact anchors with the same offsets.
Ask, the palette, checks, citations, notes, the tag menu and exercise import
all send `selectionNodes(selection)`, so they receive these nodes unchanged.

### 2.3 Highlights from anchors, through span_aliases

`reader.source_annotations` takes the open reading (`extractionId`) and adds a
`placement` to each head (`annotations.annotation_placements`, read-only):

* made on this reading, its blocks unchanged → `here`;
* made on this reading by a re-read's carry-over (`reanchored`) → `moved`
  ("moved here when the book was read again", on the page and on the card);
* made on another reading → resolved through `SpanTranslator` (span_aliases,
  the one alias authority): the same text → `moved`, drawn on its words;
* its words changed (an alias to changed text, a re-anchor below confidence,
  a segment whose block hash no longer matches) → `flagged` at the passage
  that took its place, never drawn as text;
* nothing on this reading → `elsewhere` (rail only).

The PDF draws a placement from the model's word boxes, never from stored
screen or page coordinates, so it follows zoom, resize, reload and re-reads
(F13, F14). `geometry_json` stays in the database for history but nothing
paints from it. A capture made a moment ago is drawn at once from its own
offsets until the sidecar's placement arrives.

### 2.4 Remove and undo

From the page: click a highlight (or Tab to its stop) → *remove* or Delete.
From the rail: *delete* as before. Either way the Reader offers **undo** for
ten seconds (a quiet line at the foot of the reading column, and Ctrl+Z
outside text fields). Undo is `reader.restore_annotation`: a `disposition`
event with `{"undo": "delete_intent", "event_id": …}` that withdraws the
latest delete intent; the listing shows an annotation when the latest of its
delete intents and undos is an undo. Deletion stays a tombstone event and so
does its undo: anchor, versions and history are untouched. **No schema
change**: `disposition` was already an allowed event type and no annotation
event used it; no migration number is taken.

### 2.5 Protection (exam_material decides)

`reader.pdf_view` and `reader.render_view` carry `protection`
(`reader_guidance.reading_protection`): the whole reading when rule 4 holds it
back or it is held out whole, else its held-out passages, with the refusal the
model paths give — the same held-out partition Ask, background requests,
remember-later synthesis and exercise import refuse. A selection touching any
of it offers no model action (`selectionProtected`): Notes hides exercise
import, the four background requests and the three remember-later presets and
says why in the sidecar's words ("You can still highlight it, mark it and keep
notes."); Ask shows the same line instead of its composer. Highlight, the two
local marks and notes stay. `checkOffer.ts` is untouched (no check offer
changes), the render lock is untouched (nothing here renders with pdfium).

### 2.6 RPC and wire changes

| RPC | Change | Mobile |
|---|---|---|
| `reader.restore_annotation` | new (undo of a delete) | pinned desktop-only (`READER_PDF_SELECTION_RPCS`) |
| `reader.source_annotations` | optional `extractionId` → `placement` per head; without it, unchanged | pinned (extended) |
| `reader.pdf_view`, `reader.render_view` | `protection` | pinned (extended) |

Tauri: one passthrough (`reader_restore_annotation`); `cargo check` clean.

## 3. Friction audit, after (the original-PDF view)

### 3.1 The failures of §1.3

| # | Case | Now |
|---|---|---|
| F1 | Scanned page | Words, lines and passages select on a scan: estimated inside the layout boxes (GLM-OCR or Marker OCR). Approximate placement, exact text (the extraction's). |
| F2 | Two columns | Reading order, not the content stream; a drag through the gutter keeps its head on the nearest line |
| F3 | Formulas | Display formula: one click selects it, its LaTeX the text. Inline maths: one unit, quoted as LaTeX, drawn over its glyphs |
| F4 | Tables | One click selects the table, its Markdown the text |
| F5 | Footnotes | Read after the body, as the extraction reads them |
| F6 | Hyphenation | Both halves select the whole word; it copies and anchors whole |
| F7 | Ligatures, spacing | The quote is the extraction's own slice; NFKC keys align glyphs to it |
| F8 | Glyphs outside every box | By design still left out (page numbers, a line no box holds): only the extraction's text can anchor. Box tolerance (2 pt across, 30 % of a line down) keeps a tight GLM box's edge words |
| F9 | Spanning blocks | One exact node per block in reading order; the primary span is the node with the most text |
| F10 | Spanning pages | Reading order across the page break, the pointer snapped to the nearest page across the gap; running heads and footers excluded |
| F11 | Zoom, resize | The selection and highlights live in PDF points: they follow zoom and resize exactly (checked at 115 % in jsdom and 130 % in Chromium) |
| F12 | Feedback | Live, word by word, per line; the active passage's frame steps back under a selection |
| F13 | Highlights are whole blocks | Drawn on their words, one box per line |
| F14 | After a re-read | Placed through span_aliases: drawn and labelled when moved, outlined when their words changed, never painted on another passage |
| F15 | No interaction | Hover lights it; a click opens its chip (open note, remove); Tab reaches each, Enter opens, Delete removes; undo |
| F16 | Keyboard | Shift+arrows by word and line, Shift+Home/End, from a click's caret or the top of the view; a formula is one step |
| F17 | Copy | The extraction's clean text, maths as LaTeX, works on scans |
| F18 | Flicker | Settles 150 ms after the mouse or the last key; a double then triple click hands over one selection |
| F19 | Memory | Pages far from the view release their canvas and text layer |
| F20 | Held-out material | No model action offered, with the reason |
| F21 | Right-click | On the selection: its exact nodes; elsewhere in a passage (scans too): the passage |

### 3.2 The workflows (spec §4.1 columns)

| Workflow (on the original PDF) | Steps | Keyboard | Waits on a model | Focus / rail moves without the learner's act | Context lost |
|---|---|---|---|---|---|
| **Highlight a sentence** | 3: drag · (rail flips to Notes) · *highlight* | Yes: click once, Shift+arrows, Tab to *highlight* | None | Rail flips to Notes (unchanged; RW2's intent box takes this over behind `reader_intent`) | None: its words, kept through zoom, reload and re-reads |
| **Ask about a selection and get back to reading** | 4–5: drag · *ask* tab · type · Ctrl+↵ · read | Yes (selection by Shift+arrows) | The tutor answer | Rail flips to Notes first (unchanged) | None: the quote is the extraction's text, LaTeX for maths, words on scans |
| **Capture "test me later"** | 3: drag · (rail flips) · *test me later* | Yes | None (queued) | Rail flips | On held-out material it is not offered, and the rail says why |
| **Select a formula or table** | 1: click it | Shift+arrows reach it as one unit | None | Rail flips | None: LaTeX / Markdown |
| **Copy a passage with maths** | 2: drag · Ctrl+C | Yes | None | — | None |
| **Remove a highlight** | 2: click it · *remove* (or Tab to it · Delete) | Yes | None | — | None: undo for ten seconds (button or Ctrl+Z) |

The friction this phase adds: none of the six gained a step; two lost one
(select a formula, remove a highlight), and every selection is now reachable
from the keyboard. The rail still flips to Notes on a selection: that is the intent box's
job (spec §4.2, `reader_intent`), not this stage's.

## 4. Tests

| Where | What |
|---|---|
| `pdfSelection/model.test.ts` (20, node) | The model on synthetic PDFs parsed by the real pdf.js: furniture and page numbers out; Helvetica advance widths; snapping; the hyphenated word; two columns with the footnote drawn between them; page break; display formula, table, inline maths; scan by estimate; code points outside the BMP; word/line moves; anchors to boxes; restore from nodes; marquee; `exactNode`; highlight placement; the recorded text content (`fixtures/synthetic_text_content.json`) is what pdf.js reads |
| `pdfSelection/arxiv.test.ts` (6, node) | GLM-OCR geometry of the CC BY arXiv answer (no text layer): words inside boxes, two columns, the loss formula and the results table whole, a figure selects nothing, a page break past a figure; writes the selection contract |
| `pdfSelection/perf.test.ts` (1, node) | A **600-page** synthetic PDF parsed by pdf.js (half of it scanned): model build, a page's words placed, 2,720 drag frames, the hand-over of a 300-page selection |
| `PdfReaderPane.selection.test.tsx` (17, jsdom) | The pane driven like a learner: columns, page break, formula click, scan drag, double→triple click (one hand-over), Shift+arrows with the read-out, Shift+arrows and Shift+click after a click elsewhere, Ctrl+C, right-click, a click keeps the capture and Esc clears it, a restored capture never moves focus; highlights here/moved/flagged with their labels, zoom, chip, remove, Delete on a stop, a drag starting on a highlight; page release and redraw; **600 pages**: drag commits against a full redraw |
| `ReaderScreen.pdfSelection.test.tsx` (5, jsdom) | The Reader: exact nodes reach `reader.capture`; highlights from placements (here, moved, flagged, elsewhere); held-out and rule-4 protection in Notes and Ask; remove and undo (button, Ctrl+Z, the offer ends) |
| `tests/test_reader_pdf_selection.py` (25) | The contract anchors exactly (12); drifted offsets relocate; capture → placement round trip; placements before and after a re-read, with and without aliases; never-anchored and changed-block cases; protection on both views and for rule 4; remove → undo → listed again with the same placement, history `create, delete_intent, disposition`; delete after undo |
| `tests/test_mobile_allowlist.py` | `reader.restore_annotation` and the three extended RPCs pinned desktop-only |

Measured (this machine, under other stages' load):

* model, 600 pages / 5,000 blocks: build 1.7 ms; a page's words placed 0.30 ms
  mean (p95 0.48, max 3.3); a drag frame (hit-test + three pages' boxes)
  0.016 ms mean, p95 0.024 ms, max 1.0 ms; the hand-over of a 300-page
  selection 117 ms (once, 150 ms after release);
* the pane, 600 pages with three drawn, jsdom: a drag frame's React commit
  3.7 ms mean, p95 5.0 ms, against 21.3 ms for a zoom step that redraws
  every page (the test asserts the ratio, which load does not change).

## 5. A real-UI look (usability harness, fake AI, no paid call)

Instance *a* (brand-new user) of the scratchpad harness, on the synthetic book
(`buildPdf(SYNTHETIC_PAGES)`, invented text) added through the app; a second,
completed reading with GLM-like boxes was then written into that scratch vault
(the app had read it with pypdf, which has no geometry; Marker is not
installed and GLM-OCR is paid). Driven in headless Chromium over CDP:

* a drag from the left column's last word to the right column's first words:
  two word-level boxes, the rail's capture `[1] "quietly." [2] "Right column
  begins"`, and Ctrl+C gave `quietly.\n\nRight column begins`;
* a click on the display formula: Ctrl+C gave `$$\nx^{2} + y^{2} = 1\n$$`;
* a drag on the scanned page selected its words (`A scanned page has no text
  layer at all, …`);
* *highlight*, reload, the Reader again: the highlight is drawn on its two
  lines from its placement; a click opens its chip; Delete removes it, the
  undo line shows; Ctrl+Z brings it back;
* at 130 % the selection and the highlight sit on their words.

It found four things, fixed in `b9899fbe6` (with a test for the first):
Shift+arrows after a click extended the kept capture instead of starting at
the click; the capture card named the raw span id ("selected · s2", now "1
passage"); a keyboard focus drew the browser's heavy outline round the whole
pane (now a quiet dashed ring, only for keyboard focus); and the active
passage's frame washed the paragraph a word selection sat in. The harness's
command table was regenerated from this branch's `commands.rs` (its 13 Oct
copy is kept beside it).

## 6. Gate

Run 2026-10-15 after a Claude Code restart, on the final tree `e2108f0c3`
(branch `reader/pdf-selection`, base `37a2a7e5f`, main not merged in).
Python 3.12.14, SQLite 3.53.1, Node 26.11.1, npm 12.2.0, cargo 1.99.0.
`TMPDIR` = the worktree's `fixtures-local/tmp`. No paid call and no vault
touched.

| Lane | Command | Result |
|---|---|---|
| Install | `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| Import contracts | `uv run lint-imports --no-cache` | **22 kept, 0 broken** |
| Full suite | `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto` | **11858 passed**, 0 failed, 0 skipped (16 warnings), 12:57 |
| Durability | `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -m durability` | **106 passed**, 11752 deselected, 1:52 |
| Targeted (no lock) | `tests/test_reader_pdf_selection.py`, `test_mobile_allowlist.py`, `test_coordinated_migrations.py` | 173 passed; with `test_sidecar_reader_pdf_view.py` and the two UX Phase 1 pdf_view files after `e2108f0c3`: 187 passed |
| Frontend | `npm install`; `npm run typecheck`; `npm test`; `npm run frontend:build` | typecheck clean; vitest **648 passed in 89 files**; build ok (Vite's usual chunk-size notice) |
| Tauri | `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` | ok |
| DB references | — | not run: no schema change (head stays 204 on this base; no migration number taken) |

`e2108f0c3` changed Python only, after the frontend and cargo lanes ran; the
frontend tree they checked is the final one. The perf test's hand-over of a
300-page selection measured 216 ms in this run under the other stages' load
(117 ms in §4); it happens once, 150 ms after release, and the test asserts
the drag-frame budget, not the hand-over.

Not in this gate, noted: the generated desktop reference
(`_scripts/desktop_validate.py`, last regenerated 2026-09-23) already refuses
sources from `main`: with this branch's two test-only helpers
(`pdfSelection/testing/*.ts`) left out, its activation audit still stops at
`src/copy/denyList.ts` (UX Phase 1, 2026-10-13), and `src/testNodeShims.d.ts`
(also 2026-10-13, test-only) has no rule either. The module reference
(`module_validate.py`) passes.

## 7. Open questions (each with the default this branch takes)

1. **Highlights in the extracted-text view stay passage-level** (now from the
   same placements, so a moved or changed highlight no longer marks another
   passage). Drawing them word by word there needs offsets mapped into the
   rendered Markdown and KaTeX. *Default: passage-level there, word-level on
   the original.*
2. **A click keeps the capture** (as the extracted text always did), so
   reading on never loses what was selected; Esc, *clear*, bare Alt or a new
   selection replace it. *Default: keep.* The owner may prefer a browser's
   click-to-deselect.
3. **The rail still flips to Notes on a selection** — the intent box's job
   behind `reader_intent` (RW2), not this stage's. *Default: unchanged.*
4. **Estimated word positions on scans** come from the box's size (lines of
   about 1.2 em); GLM-OCR gives block boxes, not lines. If a later GLM or
   Marker answer records line or word boxes, `geometry.ts` should take them.
   *Default: estimate, honestly approximate; the text is always exact.*
5. **Undo as a `disposition` event** avoids a migration. A dedicated
   `restore` event type would need migration 206 (the events table's CHECK).
   *Default: no schema change.*
6. **Triple click selects the passage**, not the line (Shift+Home/End
   reach a line's ends). *Default: passage.*
7. **Text-only readings (pypdf) still have no selection on the original**
   (no boxes to anchor to); the learner selects on the extracted text, as
   before. *Default: unchanged.*
8. **The desktop reference generator needs a rule for test-only sources**
   (`testNodeShims.d.ts` on `main`, `pdfSelection/testing/*.ts` here) and
   main's unreached `copy/denyList.ts` classified, before its next
   regeneration. *Default: left to that regeneration; nothing here changes
   the generator.*
