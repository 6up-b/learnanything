# GLM-OCR content quality: Codex review and fixes

Stage `glm-ocr-quality`, branch `ingest/glm-ocr-quality`, worktree `learnanything-glmocr`. The review covered `bffe086ec..2b608bf1d` (codex job `20261014-193449-Rnpqoy`). The fixes are in `85f76fd12`.

**Paid calls: none. Network: none.** Every check below ran on fakes, on synthetic PDFs, or on the 39 answers the live check saved under the gitignored `fixtures-local/`.

## Findings

Each finding was reproduced first, with a failing test on `2b608bf1d`, and then fixed.

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F1 | High | Text-layer extraction can race Reader rendering inside PDFium | fixed | `85f76fd12` | `test_cr_f1_extraction_never_enters_pdfium_in_this_process_while_the_reader_renders`, `test_cr_f1_a_worker_that_crashes_or_hangs_is_recorded_and_the_reading_goes_on` |
| F2 | Medium | Split-number joining corrupts ordinary numbered lists | fixed | `85f76fd12` | `test_cr_f2_list_items_keep_their_numbers_without_the_documents_numbering_behind_them`, `test_q2c_split_numbering_is_collapsed_where_it_is_a_label` (rewritten) |
| F3 | Medium | Currency still consumes adjacent math delimiters | fixed | `85f76fd12` | `test_cr_f3_currency_never_takes_the_opening_dollar_of_maths_beside_it` |
| F4 | Medium | A stripped bookmark match overrides an exact numbered match | fixed | `85f76fd12` | `test_cr_f4_an_exact_bookmark_beats_one_that_matches_only_without_its_numbering` |
| F5 | Medium | A trailing function argument prevents equation-number recovery | fixed | `85f76fd12` | `test_cr_f5_a_formulas_own_brackets_never_stop_an_equation_number_from_coming_back` |
| F6 | Medium | Repeated body text silently truncates recovered footnotes | fixed | `85f76fd12` | `test_cr_f6_a_footnote_line_that_the_body_repeats_elsewhere_is_kept` |

None was rejected.

### Reproductions on `2b608bf1d`

- **F1.** The test runs `extract()` on a thread named `learnloop-ingest-drain` while the test's own thread keeps rendering page 0 through `reader/span_view._local_pdf_page_render`. The whole pytest process died with `Fatal Python error: Segmentation fault`, inside pypdfium2's `document.get_page`, called from `span_view.py:212`. No Python handler could contain it. The second F1 test failed because the worker it exercises did not exist yet.
- **F2.** `"1. 5 people arrive."` became `"1.5 people arrive."`, and `"2. 3 is prime"` became `"2.3 is prime"`. This happened in a chapter-3 list, where nothing numbers 1.5 or 2.3.
- **F3.** `"$5 ($x$ each)"` came back unchanged, so remark-math paired `$5 ($` as maths.
- **F4.** Under the outline entries `1 Matrices` (level 1) and `1.1 Matrices` (level 2) on one page, a body block's `section_path` was `['1.1 Matrices']`. The chapter was missing.
- **F5.** `$$y = f(0)$$` stayed untagged, although the PDF had a unique `(3)` beside it.
- **F6.** The two-line footnote came back as `¹ A note on tallies that runs on.` alone. Its continuation, "See Chapter 2 for the proof.", was dropped because page 0's body says the same sentence.

### Fixes

- **F1: pdfium runs in a worker process.** pypdfium2's documentation says "PDFium is inherently not thread-safe". The Reader renders with pdfium in the sidecar's process, and an import runs on the ingest drain's thread. So the import no longer enters pdfium in its own process.
  - `glm_text_layer.pdfium_worker` starts `sys.executable -P -c …`. It inherits the environment, so the sidecar's `PYTHONPATH` still applies; `-P` only drops the working directory.
  - It sends the file on stdin and reads JSON back. It has two tasks: `"text"` returns each page's text segments, and `"render"` returns the PNG pages a self-hosted GLM-OCR server is shown.
  - `read_text_layer(raw, pages)` replaces the in-process `open_text_layer`. `_render_pages` uses the same worker.
  - If the worker exits non-zero, crashes or sends no answer, the reading records `glm_ocr_text_layer_unavailable` and carries on. The test makes the worker call `os.abort()` for a crash and sleep for a timeout. A local render failure raises `GlmOcrExtractionError`, which falls back under `auto` as before.
  - The timeout is the larger of 120 s and 1 s a page. Measured under load average 13–17, Axler's 404 pages took 2.99 s and Blitzstein's 630 pages took 4.02 s.
  - The concurrency test now passes, five runs out of five. In it, the Reader is the only code that enters pdfium in the test process, and the worker still recovers the footnote.
- **F2: a split number needs evidence** (`_join_split_labels`). It is judged across the whole document in reading order. A split number is joined only in either of these cases:
  - an environment word follows it ("1. 11 definition:");
  - the document's own numbering vouches for it. All three of these must hold:
    - the label read just before it numbers the same way and at most 3 lower ("1.37 example" then "1. 39"; the section "1.4" or the label "1.4.10" then "1. 4.11 (…)");
    - the next label that is not a heading is not at or below it. Headings are left out of this check because a section's own counter ("7.1.2 Continuous") runs apart from its labels;
    - no neighbour opens the item before or after it ("2. " beside "1. 5 …").

  Anything else stays as read, including a number on its own. On the saved answers, 162 of Axler's 163 weak splits and all 65 of Blitzstein's are vouched for. The step of 3 is the largest gap seen in either book.

  The synthetic fixture's "1. 39" and "1. 4.11 (…)" are now "1. 5" and "1. 6 (…)". Each comes after the label "1.4", as a real book's sequence would. The multi-level case moved to unit tests.
- **F3: currency beside maths** (`_is_amount`). A would-be closing dollar now counts as opening something else in two more cases:
  - it follows an opening bracket and opens a complete maths span ("$5 ($x$ each)", "$5 ($ x $ each)"). Maths never ends on "(";
  - it opens another amount, spaced or not, with prose between ("$ 5 and $ 10"). The second dollar of such a pair is escaped even when nothing closes it.

  These stay maths: `$x$`, `$5x$`, `$\$5$`, `$(1+y)$`, and padded maths followed by a number (`$ 2 \leq j $ 10 times`).
- **F4: exact bookmarks first** (`_Headings._outline_level`). A bookmark whose whole title matches the heading, numbering included, beats one that matches only after the numbering is stripped. Page distance decides next, then outline order. The two-pages rule and the fallback without an outline (numbering, then one level under the last heading placed) are unchanged.
- **F5: a formula's own brackets** (`EquationNumber`, `with_equation_tag`). `equation_numbers` now also reports whether the number lies beside the display's region or inside it. A display counts as carrying its number in only two cases:
  - it has a `\tag`;
  - its recognised text ends with that very number while the number lies inside its region, so the recognition read it.

  So `f(0)` takes `\tag{3}`. The test also covers `f(5)` with an external `(5)` beside it, which is tagged too. `a = b \quad (4)`, whose `(4)` is inside its region, is left alone.
- **F6: running lines by position** (`PageTexts`). A running line must meet all of these:
  - it is at most 100 characters;
  - it sits in the top or bottom 12% of the page;
  - it comes back within 2 pt of the same height on another page read.

  `is_furniture` takes the run, not just its text. Body occurrences never count. A bare number ("33.", an exercise's number in Blitzstein's margin) now matches the page-number pattern. The old repeated-text rule had caught two of those, and they must stay out of footnotes. Axler's running footer at 98% of the page height is still recognised on all 341 pages where it was before.

## Re-validation on the 39 saved answers

Each document was normalised by `2b608bf1d` and by the fixed tree, with the PDF's text layer. Both used the same saved windows, sizes and outlines. Every block's type, text, `section_path`, box and id was compared.

| Document | Blocks before → after | Blocks that differ | Blocks with a numbered label | Footnote blocks | `\tag`s | Health flags |
|---|---|---|---|---|---|---|
| arXiv 2302.11517 | 96 → 96 | 0 | 13 → 13 | 1 → 1 | 6 → 6 | identical |
| Byrne scan (JPG) | 22 → 22 | 0 | — | — | — | identical |
| recitation1 | 18 → 18 | 0 | 0 → 0 | 2 → 2 | 0 | identical |
| pset1 | 44 → 44 | 0 | 0 → 0 | 1 → 1 | 0 | identical |
| Axler | 6,169 → 6,169 | 1 | 610 → 609 | 24 → 24 | 0 | identical |
| Blitzstein | 8,419 → 8,419 | 0 | 601 → 601 | 9 → 9 | 0 | identical |

The footnote counts include the service's own `vision_footnote` blocks.

The one difference is on Axler p. 245. The service read result 7.9 twice: once as a heading, "7.9 matrix of T* …", and once as the body, "7. 9 matrix of T* …". The body's previous label is that same 7.9, so it is not "a little lower", and the body stays split. The heading keeps the label, so a reference to 7.9 still resolves. The studied pages (Axler 14–39, Blitzstein 11–53) are unchanged, so the recorded 44 of 46 and 44 of 45 numbered environments stand.

## The review's focus

1. **Split numbers.** The rule now needs an environment word or the book's own numbering (F2). The adversarial cases are tested, each with what keeps it as read:
   - a list in another chapter: no numbering vouches for it;
   - a list between "1.4" and "1.5": the next label is at its number;
   - a list between "1.4" and "1.9": the item "2. …" sits beside it;
   - a lone "1. 5 people arrive." with no label around: nothing vouches for it.
2. **Currency and inline maths.** Fixed for brackets and spaced pairs (F3). Every earlier case still holds (`test_q2d`, 18 cases), and so do `$x$`, `$5x$` and `$\$5$`.
3. **Heading depth.** Exact bookmarks now win (F4). The within-two-pages window and the no-outline fallback are unchanged and still pass `test_q2b`.
4. **Text-layer recovery.** These are unchanged and still tested:
   - the never-repeat check (`_already_read`);
   - footnote placement after the page's last block, under its heading;
   - the single-candidate `\tag` rule.

   F5 and F6 fix the two defects found. Scans and a missing pypdfium2 are recorded as before, and a failed worker is now recorded as `glm_ocr_text_layer_unavailable` (F1).
5. **Cache invalidation.** `MAP_VERSION` stays 2:
   - main (`4108e1ccd`) is still at map1, and map2 has never left this branch, so these fixes share it;
   - `model_versions()["text_layer"]` is unchanged (`pdfium` or `none`);
   - `_checkpoint_key` is untouched. It keys on the file, the pages, the backend and the models, never the mapping, so saved paid windows are reused and nothing is billed again. `test_r2_f5_paid_windows_are_kept…` and `test_r3_f13_…` pass.
6. **No third-party book text.** All 6-word sequences the stage adds were compared with every 6-word sequence of the saved Axler, Blitzstein, pset1 and recitation1 answers, 304,237 in all. "Adds" means the diff from `bffe086ec`, these fixes included.
   - There were 15 matches. All are markup or formula fragments: HTML table tags, `\left( \begin{array}{c c} … \end{array} \right)`, and the formula "P(B|C) and P(A|C^c) < P(B|C^c)" in `test_q2a`'s stray-"<" case.
   - No prose matched. The new test strings are invented.
   - The arXiv fixture remains CC BY 4.0 with attribution.

## Open questions

1. **Card line for scans.** Should the book card say when a scan's footnotes couldn't be recovered? I recommend keeping the accepted default: health only (`glm_ocr_no_text_layer`), with no card line, for three reasons:
   - a line on every scan's card would be noise, against the frictionless-defaults direction (glass box on demand);
   - `add_source.py` belongs to the re-read safety stage, which is in review in parallel;
   - a worker failure (F1) is likewise health-only, as `glm_ocr_text_layer_unavailable`.

   If the owner wants the line, it is one quiet detail keyed on the flag, for the re-read safety stage or a UX stage.
2. **Epigraph typed Footnote.** I recommend keeping the accepted default. Marker's reading also types it Footnote. An `Epigraph` type would add an IR block type, which is outside the extractor.
3. **Follow-up outside this stage.** Marker runs in the sidecar's process (`PdfConverter`), and its PDF text extraction also uses pdfium. So a Marker import can race Reader rendering the same way F1 did. This predates this stage and lies outside the GLM-OCR extractor. The same worker pattern, or one shared pdfium lock with the Reader, would close it.

## Gate

Final tree: code at `85f76fd12`. No network: `uv` ran `--offline`, and `uv run --no-sync` keeps the pypdfium2 that `uv pip install` added.

| Step | Result |
|---|---|
| `uv sync --offline --extra dev --extra mobile`, then `uv pip install --offline pypdfium2` | done (pypdfium2 5.14.0) |
| `uv run --no-sync lint-imports --no-cache` | **17 kept, 0 broken** |
| `tests/test_glm_ocr.py` | **110 passed** (103 before, plus 7 review tests); `test_mobile_allowlist.py` together with it: 230 passed |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto` | **11,008 passed**, 0 failed, 0 skipped (669.8 s). That is the 11,001 recorded before plus the 7 review tests. |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -m durability` | **100 passed**, 10,908 deselected (124.0 s) |
| `db_generate_reference.py` then `db_validate_reference.py` | `errors: []`. The one note whose content changed, the moved `glm_ocr.py` line citation in `Config - schema_version.md`, is committed. Provenance-only churn is left for the landing, as before. |
| Frontend, `src-tauri`, schema | unchanged: no npm, cargo or migration steps |

## Files

- `src/learnloop/ingest/extractors/glm_text_layer.py`: changes for F1 (`pdfium_worker`, `read_text_layer` and `_worker_main`), F5 (`EquationNumber`, `with_equation_tag`) and F6 (`PageTexts` running lines, bare numbers).
- `src/learnloop/ingest/extractors/glm_ocr.py`: changes for F1 (`_render_pages` through the worker, `extract`), F2 (`_join_split_labels`, a pre-pass in `responses_to_ir`), F3 (`_is_amount`) and F4 (`_title_keys`, `_Headings._outline_level`).
- `tests/test_glm_ocr.py`, plus `tests/fixtures/glm_ocr/synthetic_book_window.json` and its README (renumbered split labels).
- `docs/specs/spec_source_ingestion_v2.md` and `docs/reviews/glm-ocr-quality.md`, amended where these rules changed.
- `docs/learnloop-architecture-vault/Reference/Configuration/Fields/Config - schema_version.md`, for the moved line citation.
