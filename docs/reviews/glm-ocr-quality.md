# GLM-OCR content quality (stage `glm-ocr-quality`)

Branch `ingest/glm-ocr-quality`, worktree `learnanything-glmocr`, base `bffe086ec` (main with GLM-OCR landed, mvp-0.23).

This stage fixes the content problems found by the owner-requested live checks on 2026-10-14, when GLM-OCR read the owner's books. It covers items 1–4 under "Code changes needed" in the live report. The live report is the session's `glm-ocr-live-results.md`; its raw answers are under the gitignored `fixtures-local/glm-live-responses/`.

The work stays inside the extractor and its normaliser:

- `src/learnloop/ingest/extractors/glm_ocr.py`;
- the new `src/learnloop/ingest/extractors/glm_text_layer.py`.

It adds no migration and no successor, and it changes no Reader or sidecar code. So it composes with the parallel re-read safety stage (E1/E2: the re-read path, `handle_import`, citations and re-anchoring).

**Paid calls: none. Network: none.** The re-validation below re-reads the 39 answers the live check saved.

## What changed

1. **Estimate: 6,000 → 3,500 tokens a page** (`ESTIMATED_TOKENS_PER_PAGE`).
   - The comment cites the live receipts:
     - Axler 2,765 and Blitzstein 3,052 tokens a page; the highest 30-page window was 3,336;
     - the small PDFs 1,652 and 2,104;
     - the scan 1,376;
     - only the dense two-column paper went over, at 5,411.
   - Spending over the estimate is recorded as usage and never refused (`SpendBudget.reconcile`).
   - Axler's 404 pages now preview at 1,414,000 tokens, about $0.0424. The actual cost was $0.0335; the old estimate said $0.073.
   - Also updated:
     - the spec (`spec_source_ingestion_v2.md`);
     - the config reference line for `price_per_million_tokens`;
     - the two open items in `glm-ocr-ingest.md`, marked resolved.
2. **Normaliser** (`responses_to_ir`):
   - **(a) HTML wrappers are unwrapped** (`_unwrap_html`). This covers `<div align="center">`, `center`, `p` and `span` around a region, a wrapper with no closing tag (a caption the server misread), and a closing tag left on its own.
     - A `<` that opens no such tag stays text, for example `<P(B|C) $`.
     - No markup reaches block text or `section_path`.
   - **(b) Heading depth** (`_Headings`). The service marks every heading but the document title `##`. Depth now comes from three places, in this order:
     - the PDF outline, when a bookmark names the heading within two pages. Matching ignores numbering, case and LaTeX, so "1A `$ \mathbf{R}^{n} $` and …" matches the bookmark "R^n and C^n";
     - the heading's numbering: "2." is level 1, "2.1." level 2, "1A" level 2;
     - otherwise, one level under the last heading placed.

     The document title is the root. With an outline, numbering that would climb to or above the last bookmarked heading is a result's label, such as Axler's "1.4 example: …" under a bookmarked subsection. Such a heading nests under that subsection instead of popping it. Numbering below the bookmark is still trusted, so in Blitzstein "1.4.2" is a sibling of "1.4.1" under the bookmarked section 1.4.
   - **(c) Split numbers are joined** (`_collapse_split_number`). "1. 11 definition:" becomes "1.11 definition:".
     - This also applies to "1. 39", "3. 6 `$…$`", "1. 4.11 (Name)" and "2. 4.1. When …", but only where the number is a label. That means it is followed by a lower-case word or a kind, a colon, a parenthesis, maths, the end, or a full stop and a new sentence.
     - "1. Express …" and "6. 041SC" are unchanged.
     - It applies to Text and SectionHeader blocks.
   - **(d) Currency dollars are escaped** (`_escape_currency`), in Text, SectionHeader, Caption and Footnote blocks. Each span is judged where remark-math would pair it. A dollar before a number opens maths only when all of these hold:
     - the span it would close holds no prose word;
     - that closing dollar does not itself open something. "$18-$7" fails because a digit follows the closing dollar. "$2, ..., $n" fails because the closing dollar has a space before it and a word right after it.

     A spaced amount ("$ 18,000", which the service writes for "$18,000") needs two prose words before it is escaped, because the service pads real maths the same way ("$ 0 \in … $"). The prose test ignores `\text{…}`, `\mathrm{…}`, environment names and operator names (range, null, span, dim, …).
   - **(e) `algorithm` regions are Code only when they hold code** (`_holds_code`).
     - Code signs: R assignment, pipes or comparisons; a call on a line of its own; calls or indexing with no run of words; a fence; a leading `#` comment line.
     - Maths in dollars is never code.
     - Axler's 297 boxed definitions and results become Text. 82 of Blitzstein's 83 R listings stay Code. The 83rd is a one-line prose lead-in, which now reads as Text.
3. **Footnotes and equation numbers from the PDF's own text layer** (`glm_text_layer.py`, pypdfium2). The hosted service never returns footnote, header, footer, page-number or equation-number regions (0 in 39 answers). For each page read, pdfium's text runs are placed in the Reader's coordinates: points, top-left origin, the crop box after rotation.
   - **Footnotes.** A run is a footnote when all of these hold:
     - it is in the page's lower 40%;
     - it is inside no region;
     - it is below every region of its column;
     - it starts at that column's left edge, so a margin note is excluded;
     - it is set off from the region above by a gap, so a line the answer dropped is excluded;
     - it is not a page number, and not a running line repeated across the pages read (digits stand for any number);
     - its text is not already in the page's blocks, by letters and digits or by word pairs, so LaTeX and Unicode maths agree.

     Raised marks become superscripts ("¹ See …"). Lines join into one footnote, and a hyphen at a line end joins its word. The footnote is placed after the page's last block, under the same heading (`glm/page/N/text_layer/K`).
   - **Equation numbers.** A "(n)" that stands apart on its line becomes the display's `\tag{n}`, which `numbered_label` reads. "Stands apart" means a gap of at least half its height on both sides; "F (2)" and "M(0)" inside formulas sit 1.4–2.4 pt away. It must also:
     - lie in the display's band and right half, or beyond it;
     - be inside no other region, with no other region between it and the display (the next column);
     - be the only such number for that display, and that display the only one for it.

     A display that already carries a number is left alone, and nothing is guessed.
   - **Health flags.** `glm_ocr_footnotes_from_text_layer` and `glm_ocr_equation_numbers_from_text_layer` record recoveries. `glm_ocr_no_text_layer` marks a scan or an image, `glm_ocr_text_layer_missing_on_some_pages` a partial scan, and `glm_ocr_text_layer_unavailable` a missing pypdfium2 or a PDF pdfium can't open. These are document flags, not page flags, so a recovery or a scan never makes a "difficult page".
4. **Fixtures** (`tests/fixtures/glm_ocr/`, attribution in its README and in the test module):
   - `arxiv_2302_11517_trimmed.json` is z.ai's recorded answer for Wei Tang, Kangning Cui and Raymond H. Chan, arXiv:2302.11517v2, licensed CC BY 4.0. It is trimmed, and its kept regions are unmodified.
   - `synthetic_book_window.json` reproduces the book patterns with invented text: div wrappers, flat headings, split numbers, currency, `algorithm` boxes and R, `vision_footnote` credits, and no footnote regions.
   - No book text is in the repository.

**Cache identity.**
- `MAP_VERSION` is now 2, so `version()` ends `+map2`.
- `model_versions()` gains `text_layer` (`pdfium` or `none`), so caches re-extract.
- Paid window checkpoints do not depend on the mapping, so re-extracting re-maps the saved answers and pays nothing again.

## Fail-first

- The 28 tests written before the restart failed on the base normaliser (run with the base `src` first on the path): `-k "q1 or q2 or q3 or q4 or versions_name"` gave **28 failed**.
- Re-reading the saved answers then showed problems, and new tests pin each rule it led to:
  - 5 more currency cases;
  - 2 more R cases and 2 prose cases for `_holds_code`;
  - Blitzstein-style numbered subsections under a bookmark;
  - margin notes, dropped lines and hyphen joins;
  - partial text layers;
  - a number inside a formula or across the gutter.
- `tests/test_glm_ocr.py` now has 103 tests, all passing.

## Offline re-validation (the 39 saved answers, no network)

**Method.**
- Each document's saved windows were normalised twice:
  - "before", by main's normaliser at `bffe086ec`, loaded from an exported copy;
  - "after", by this branch's normaliser, with the PDF's text layer.
- Inputs were the copies' PDFs in `fixtures-local/` (the store files behind `glm-live-run/bytes/`), with outlines from `read_embedded_outline`.
- "Studied pages" are as in the live report: Axler 14–39 and Blitzstein 11–53, zero-based, against the recorded Marker readings in the vault copies.
- Script: the session scratchpad's `revalidate.py`. Output: `fixtures-local/glm-live-run/out/quality/revalidate.json`.

| Document | Pages / windows | Blocks before → after | Text-layer health after | Normalise time with text layer |
|---|---|---|---|---|
| arXiv 2302.11517 | 5 / 1 | 95 → 96 | footnotes, equation numbers | 0.1 s |
| Byrne scan (JPG) | 1 / 1 | 22 → 22 | `glm_ocr_no_text_layer` | 0.0 s |
| recitation1 | 2 / 1 | 16 → 18 | footnotes | 0.01 s |
| pset1 | 3 / 1 | 43 → 44 | footnotes | 0.03 s |
| Axler | 404 / 14 | 6,167 → 6,169 | footnotes | 3.3 s |
| Blitzstein | 630 / 21 | 8,412 → 8,419 | footnotes | 4.7 s |

### Markup leaks (blocks whose text, or whose `section_path`, holds an HTML wrapper tag)

| | Text before → after | Section path before → after |
|---|---|---|
| arXiv | 7 → **0** | 95 → **0** |
| pset1 | 1 → **0** | 43 → **0** |
| Axler | 25 → **0** | 6,157 → **0** |
| Blitzstein | 135 → **0** | 8,412 → **0** |

### Heading levels against the outline

| | Section-path depths before | after | Outline-matched headings before → after | Matched headings at their outline depth (one offset per book) before → after |
|---|---|---|---|---|
| arXiv (15 bookmarks) | 1: 1, 2: 16 | 1: 1, 2: 9, 3: 7 | 15 → 15 | 53% → **100%** |
| Axler (168) | 1: 14, 2: 337 | 1: 15, 2: 40, 3: 148, 4: 148 | 133 → 146 | 71% → **100%** |
| Blitzstein (152) | 1: 1, 2: 418 | 1: 1, 2: 17, 3: 135, 4: 240, 5: 26 | 146 → 146 | 91% → **100%** |

- Axler finds 13 more matches after the change: the chapter titles, which the `<div>` wrapper used to hide.
- Axler's depth-4 headings are its result labels ("1.4 example: …") nested under their subsections. Blitzstein's depth-5 headings sit under numbered subsections ("1.4.1 …"), for example "Solution:" and "FIGURE 1.3".
- Without an outline (pset1, recitation1), depth follows the numbering. Only pset1 has two headings, at depths 1 and 2.

### Numbered environments (`block_roles.numbered_label`, studied pages, against Marker's baseline)

| | Baseline (Marker) | Before (GLM-OCR) | After |
|---|---|---|---|
| Axler | 46 | 24 | **44**. Still missing: "1.46" (the server read it as a one-cell Table) and "example 1.12" (merged into another block) |
| Blitzstein | 45 | 42 | **44**. Still missing: "4.4.16", a cross-reference that Marker split as a block start |
| Whole book: Axler | — | 305 labels | 606 |
| Whole book: Blitzstein | — | 532 labels | 597 |

### Currency (Text, SectionHeader, Caption and Footnote blocks, paired the way remark-math pairs them)

| | Blocks with any unpaired dollar | Blocks pairing an amount's dollar with prose | Blocks with an unescaped, unpaired amount |
|---|---|---|---|
| Blitzstein before → after | 20 → **2** | 16 → **0** | 14 → **0** |
| Axler before → after | 0 → 2 | 0 → 0 | 0 → 0 |

- 27 Blitzstein blocks gained escapes, and every one was checked by eye.
- Axler gained none. It is a maths book, and the operator-name and environment rules keep its maths whole.
- The 2 Axler blocks with an unpaired dollar are boxed results whose maths the server left unbalanced. They now count because they are Text, not Code; their text is unchanged.
- Of Blitzstein's 2:
  - one is the server's own unbalanced maths;
  - the other is a list of amounts ending in a variable amount ("\$1, \$2, ..., $n"), where the last dollar is left alone and renders as itself.

### Footnotes and equation numbers recovered

| | Footnotes recovered (page, characters) | Equation numbers |
|---|---|---|
| arXiv | p. 0: "∗ Corresponding Author." (23) | **6 of 6**: `\tag{1}` to `\tag{6}`. Before: 0 |
| recitation1 | p. 0: the course-materials credit line (82) and the dagger note (40). The live report listed the credit line as missing | none in the PDF |
| pset1 | p. 1: the dagger note (40) | none |
| Axler | p. 24: the chapter epigraph and its attribution (175, 41). Marker also typed these as Footnote; see below | Axler numbers no displays; 0 tagged, and none wrongly |
| Blitzstein | pp. 17, 31 (the live report's footnotes 1 and 2), 190, 244, 351, 409, 520 (432, 206, 83, 278, 201, 337, 68). All start with their raised mark | none wrongly. The one set-apart "(2)" in the book is not beside a display. Before the "stands apart" rule, "F (2)" and "M(0)" inside formulas would have been tagged, so it was added |

- Blitzstein p. 47 footnote 3 is not repeated: the server kept it as a Text block.
- The arXiv p. 0 footnote sits under the left column while the right column runs lower. It is found because "below its column" is judged per column.
- Two candidates were excluded, and tests now pin both rules:
  - Axler p. 35: a margin note beside the last paragraph;
  - Axler p. 319: a body line the server dropped, directly under its region.
- Every recovered footnote box holds at least 60% of its own words in the PDF text (9 of 9 measurable).

### Geometry and reading order

| | Region blocks before → after | Same boxes | Reading order of the region blocks | Text boxes with ≥60% of own words |
|---|---|---|---|---|
| arXiv | 95 → 95 | 95/95 | identical | 70: 100% → 70: 100% |
| Byrne scan | 22 → 22 | 22/22 | identical | (image) |
| recitation1 | 16 → 16 | 16/16 | identical | 13: 100% → 13: 100% |
| pset1 | 43 → 43 | 43/43 | identical | 39: 100% → 39: 100% |
| Axler | 6,167 → 6,167 | 6,167/6,167 | identical | 3,790: 100% → 4,052: 100% (the 297 boxes, now Text, count) |
| Blitzstein | 8,412 → 8,412 | 8,412/8,412 | identical | 5,587: 100% → 5,587: 100% |

The only new blocks are the recovered footnotes, each after its page's last block. No region block was added, dropped, moved or re-boxed.

## Limits and choices

- **Axler's epigraph is typed Footnote.** The server dropped it; it sits at the foot of the chapter's opening page. Marker's reading typed it Footnote too. Keeping its words seemed better than losing them.
- **Dropped body lines are not recovered.** One Axler line (p. 319) runs on from its region with no gap. It is recognised as such and left out, never typed as a footnote, so the server's recall loss stands. Recovering such lines into their region would be a change to the region text, not done here.
- **Footnotes are plain text.** Maths in a footnote reads as the PDF's text layer has it, as on Blitzstein p. 351, where subscripts come out as plain characters. A dollar in a footnote is escaped.
- **Joining split numbers is a judgement call.** An enumerated exercise that starts "1. 5 people …" would also be joined ("1.5 people"). None occurred in the 39 answers.
- **The outline beats numbering.** Under an outline, an unbookmarked numbered heading at or above the last bookmarked level nests under it. That is right for result labels. A section heading the server misread badly enough to miss its bookmark would nest one level too deep.
- **A running footer needs two pages.** It is recognised by repeating across the pages read, so a one-page import could keep a running footer as a footnote. Page numbers are always recognised.
- **No card line for scans.** The live report suggested saying on the Library card that a scan's footnotes and equation numbers can't be recovered. This stage records it in health only (`glm_ocr_no_text_layer`), to stay inside the extractor and leave `add_source.py` to the re-read safety stage. See open questions.

## Gate

To be filled in from the final tree; see the stage report.

## Open questions

1. Should the book card's details say when a scan's footnotes and equation numbers couldn't be recovered (`glm_ocr_no_text_layer`)? Default: health only, no card line. A quiet line on every scan would be noise.
2. Should the Axler-style epigraph keep the Footnote type, or get its own type (`Epigraph`)? Default: Footnote, as Marker's reading did.

## Files

- `src/learnloop/ingest/extractors/glm_ocr.py`: the estimate; `MAP_VERSION` 2; `model_versions` gains `text_layer`; `_unwrap_html`, `_collapse_split_number`, `_escape_currency`, `_holds_code`, `_Headings`; and the text layer wired into `responses_to_ir` and `extract`.
- `src/learnloop/ingest/extractors/glm_text_layer.py` (new): pdfium text runs in the Reader's points, footnotes, equation numbers and health flags.
- `tests/test_glm_ocr.py` and `tests/fixtures/glm_ocr/` (README with attribution).
- `docs/specs/spec_source_ingestion_v2.md`, `docs/reviews/glm-ocr-ingest.md`, `docs/learnloop-architecture-vault/_scripts/db_generate_reference.py`, and the two config reference notes whose content changed (`Config - ingest.md`, `Config - schema_version.md`).
- Not committed (gitignored, third-party content): `fixtures-local/glm-live-run/out/quality/revalidate.json` and the saved answers.
