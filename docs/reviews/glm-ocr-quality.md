# GLM-OCR content quality (stage `glm-ocr-quality`)

Branch `ingest/glm-ocr-quality`, worktree `learnanything-glmocr`, base `bffe086ec` (main with GLM-OCR landed, mvp-0.23).

*Landed on main at `mvp-0.24` (merge `2d8a30125`; see "Landing onto main" below). The extractor landed unchanged. One existing retry test was made immune to the text-layer worker's wait. Re-read safety will need two of its tests updated for the 3,500-token estimate when it lands.*

This stage fixes the content problems found by the owner-requested live checks on 2026-10-14, when GLM-OCR read the owner's books. It covers items 1–4 under "Code changes needed" in the live report. The live report is the session's `glm-ocr-live-results.md`; its raw answers are under the gitignored `fixtures-local/glm-live-responses/`.

The work stays inside the extractor and its normaliser:

- `src/learnloop/ingest/extractors/glm_ocr.py`;
- the new `src/learnloop/ingest/extractors/glm_text_layer.py`.

It adds no migration and no successor, and it changes no Reader or sidecar code. So it composes with the parallel re-read safety stage (E1/E2: the re-read path, `handle_import`, citations and re-anchoring).

**Paid calls: none. Network: none.** The re-validation below re-reads the 39 answers the live check saved.

> **Amended by the Codex review** (`docs/reviews/glm-ocr-quality-codex-review.md`): split numbers need evidence (2c), currency beside maths (2d), exact bookmarks first (2b), running lines by position, equation numbers beside a formula's own brackets, and pdfium in a worker process (3). The rules below are as amended; the measurements are as first recorded, and the review re-ran them.

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
   - **(c) Split numbers are joined** (`_join_split_labels`). "1. 11 definition:" becomes "1.11 definition:".
     - Only the shapes a label takes: the number is followed by a lower-case word or a kind, a colon, a parenthesis, maths, the end, or a full stop and a new sentence.
     - A list's items take the same shapes ("1. 5 people arrive.", "2. 3 is prime"), so the number is joined only when something vouches for it: an environment word after it, or the document's own numbering. That means the label read just before it numbers the same way and at most 3 lower ("1.37 example" then "1. 39"; the section "1.4" or the label "1.4.10" then "1. 4.11 (Name)"), the next label that is not a heading is not at or below it, and no neighbour opens the item before or after it ("2. " beside "1. 5 …").
     - An enumerated item ("1. Write …"), a course code ("6. 012XY") and a list's item are unchanged.
     - It applies to Text and SectionHeader blocks, judged across the whole document in reading order.
   - **(d) Currency dollars are escaped** (`_escape_currency`), in Text, SectionHeader, Caption and Footnote blocks. Each span is judged where remark-math would pair it. A dollar before a number opens maths only when all of these hold:
     - the span it would close holds no prose word;
     - that closing dollar does not itself open something. "$18-$7" fails because a digit follows the closing dollar. "$2, ..., $n" fails because the closing dollar has a space before it and a word right after it. "$5 ($x$ each)" fails because the closing dollar follows a bracket and opens whole maths. "$ 5 and $ 10" fails because the closing dollar opens another amount with prose between.

     Otherwise a spaced amount ("$ 18,000", which the service writes for "$18,000") needs two prose words before it is escaped, because the service pads real maths the same way ("$ 0 \in … $"). The prose test ignores `\text{…}`, `\mathrm{…}`, environment names and operator names (range, null, span, dim, …).
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
     - it is not a page number or a bare number ("33.", an exercise's number in the margin), and not a running line: a line of at most 100 characters in the top or bottom 12% of the page that comes back within 2 pt of the same height on another page read (digits stand for any number). The same words in a page's body never make a footnote line running;
     - its text is not already in the page's blocks, by letters and digits or by word pairs, so LaTeX and Unicode maths agree.

     Raised marks become superscripts ("¹ See …"). Lines join into one footnote, and a hyphen at a line end joins its word. The footnote is placed after the page's last block, under the same heading (`glm/page/N/text_layer/K`).
   - **Equation numbers.** A "(n)" that stands apart on its line becomes the display's `\tag{n}`, which `numbered_label` reads. "Stands apart" means a gap of at least half its height on both sides; "F (2)" and "M(0)" inside formulas sit 1.4–2.4 pt away. It must also:
     - lie in the display's band and right half, or beyond it;
     - be inside no other region, with no other region between it and the display (the next column);
     - be the only such number for that display, and that display the only one for it.

     A display that already carries its number is left alone: a `\tag`, or recognised text ending with that very number while the number lies inside the display's region. A formula's own brackets ("f(0)") never stop the tag, and nothing is guessed.
   - **Health flags.** `glm_ocr_footnotes_from_text_layer` and `glm_ocr_equation_numbers_from_text_layer` record recoveries. `glm_ocr_no_text_layer` marks a scan or an image, `glm_ocr_text_layer_missing_on_some_pages` a partial scan, and `glm_ocr_text_layer_unavailable` a missing pypdfium2, a PDF pdfium can't open, or a pdfium worker that failed.
   - **pdfium runs in a worker process.** pdfium is not thread-safe and the Reader renders with it in the sidecar's process, so the text layer (and a local server's page images) is read by a worker of its own; a crash or a timeout stays there. These are document flags, not page flags, so a recovery or a scan never makes a "difficult page".
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
- **Joining split numbers needs evidence.** A list's item ("1. 5 people …") stays as read unless the label before it numbers 1.2–1.4, nothing at or below 1.5 follows, and no item "2. …" sits beside it. A label whose neighbours went unread (more than 3 apart) stays split; one Axler result read twice (heading and body, both "7.9") keeps its label on the heading only.
- **The outline beats numbering.** Under an outline, an unbookmarked numbered heading at or above the last bookmarked level nests under it. That is right for result labels. A section heading the server misread badly enough to miss its bookmark would nest one level too deep.
- **A running footer needs two pages.** It is recognised by coming back at the same height in the margin across the pages read, so a one-page import could keep a running footer as a footnote. Page numbers are always recognised.
- **No card line for scans.** The live report suggested saying on the Library card that a scan's footnotes and equation numbers can't be recovered. This stage records it in health only (`glm_ocr_no_text_layer`), to stay inside the extractor and leave `add_source.py` to the re-read safety stage. See open questions.

## Gate (final tree; code at `347ba844a`; no network, `--offline`)

| Step | Result |
|---|---|
| `uv sync --offline --extra dev --extra mobile`, then `uv pip install --offline pypdfium2` | done (pypdfium2 5.14.0) |
| `uv run --no-sync lint-imports --no-cache` | **17 kept, 0 broken** |
| `tests/test_glm_ocr.py` | **103 passed** |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto` | **11,001 passed**, 0 failed, 0 skipped (903.9 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -m durability` | **100 passed** (10,901 deselected; 110.4 s) |
| `db_generate_reference.py` then `db_validate_reference.py` | `errors: []`. The two config notes whose content changed are committed: the estimate in `Config - ingest.md` and a moved line citation in `Config - schema_version.md`. The provenance-only churn on the other notes is left for the landing. |
| Frontend, `src-tauri`, schema | unchanged: no npm, cargo or migration steps |

`uv run` is given `--no-sync` so the gate keeps the pypdfium2 that `uv pip install` added; a plain `uv run` would sync it away. Re-running the offline re-validation on the committed tree reproduced every recorded number.

## Open questions

1. Should the book card's details say when a scan's footnotes and equation numbers couldn't be recovered (`glm_ocr_no_text_layer`)? Default: health only, no card line. A quiet line on every scan would be noise.
2. Should the Axler-style epigraph keep the Footnote type, or get its own type (`Epigraph`)? Default: Footnote, as Marker's reading did.

## Files

- `src/learnloop/ingest/extractors/glm_ocr.py`: the estimate; `MAP_VERSION` 2; `model_versions` gains `text_layer`; `_unwrap_html`, `_collapse_split_number`, `_escape_currency`, `_holds_code`, `_Headings`; and the text layer wired into `responses_to_ir` and `extract`.
- `src/learnloop/ingest/extractors/glm_text_layer.py` (new): pdfium text runs in the Reader's points (read in a worker process), footnotes, equation numbers and health flags.
- `tests/test_glm_ocr.py` and `tests/fixtures/glm_ocr/` (README with attribution).
- `docs/specs/spec_source_ingestion_v2.md`, `docs/reviews/glm-ocr-ingest.md`, `docs/learnloop-architecture-vault/_scripts/db_generate_reference.py`, and the two config reference notes whose content changed (`Config - ingest.md`, `Config - schema_version.md`).
- Not committed (gitignored, third-party content): `fixtures-local/glm-live-run/out/quality/revalidate.json` and the saved answers.

## Landing onto main

**Branch:** `merge/glmq-onto-main` (worktree `learnanything-merge2`), from main `a9356f986`: `mvp-0.24` LATEST, migration head 202, sixteen defaults snapshots. Since this branch's base `bffe086ec`, main has landed router R2b + R2c, plan determinism and the storage and sync spec.

- Merge `2d8a30125` is a real `--no-ff` merge of `ingest/glm-ocr-quality` (`8be2fdd8f`, unchanged; the Codex re-review was clean).
- Then `4152afcc5`, a test fix (see "The flake").
- Then this record.

Not pushed. Owner-directed, 2026-10-15, single phase.

**Paid calls:** none ($0.00); no network, no key read. **Migration:** none (head 202 is main's). **Successor:** none. **`apps/`:** unchanged, so no frontend gate and no `cargo check`.

| Commit | What |
|---|---|
| `2d8a30125` | the merge: the regenerated references and the Pipeline Map line |
| `4152afcc5` | the retry test records only the retry loop's own waits |
| (this commit) | this section |

### Conflicts and compositions

| File | Resolution |
|---|---|
| `Config - ingest.md`, `Config - schema_version.md` (the only conflicts, both generated) | Taken from main, then regenerated with the rest of `Reference/`. 373 notes changed: provenance, plus the branch's two content lines (the 3,500-token estimate under `price_per_million_tokens`, and the `glm_ocr.py:292` citation under `schema_version`). |
| Auto-merged, both sides kept | `_scripts/db_generate_reference.py`: the branch's estimate wording beside main's `plan.deterministic_staged_plans` override |
| This side only | `glm_ocr.py`, `glm_text_layer.py`, `tests/test_glm_ocr.py`, `tests/fixtures/glm_ocr/`, `spec_source_ingestion_v2.md`, `glm-ocr-ingest.md` and the two review records. Since `bffe086ec`, main has changed none of them, and nothing under `src/learnloop/ingest/`, `content/` or `reader/`. |

- **The code is the branch's.** `git diff 8be2fdd8f 4152afcc5` is empty for `src/learnloop/ingest/`, `tests/fixtures/glm_ocr/` and the spec, and `tests/test_glm_ocr.py` differs only by the fix below. `git diff a9356f986 4152afcc5 -- src` touches only the two extractor files.
- **R2b + R2c and plan determinism.** They share no code with this branch. Neither reads an extraction, and the extractor reads no plan, router or config state that they added.
- **Defaults.** The merge changes no config: `git diff a9356f986 4152afcc5 -- src/learnloop/config` is empty. So the sixteen `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries are main's and were not recomputed. A fresh process (`python -B`) confirms all sixteen against `defaults_fingerprint_for_version`.
- **References.**
  - `db_generate_reference.py`: schema head 202, 321 table notes.
  - `db_validate_reference.py` reports `errors: []`, with the prose counts unchanged. `Configuration.md` and `Database.md` still read 854 leaves in 50 sections, since no leaf was added or removed.
- **CLI help.** `test_cli_help_snapshot.py` passes unchanged.
- **Pipeline Map** (`Maps/LearnLoop Pipeline Map.md`). One line after the extraction paragraph:
  - the normaliser's repairs (HTML wrappers, heading depth from bookmarks or numbering, split numbers joined only with evidence, currency, `algorithm` regions);
  - the text layer read in a pdfium worker process, for footnotes and equation numbers;
  - the health flags, and the cache identity (`MAP_VERSION` 2, `text_layer`).

  `validate_vault.py` passed: 1,105 notes.
- **Re-read safety** (`fix/reread-safety` `9f1023b49`, in review, not on main).
  - A dry merge with this tip (`git merge-tree --write-tree`; no ref changed, no checkout) conflicts only in the 373 generated notes. `test_glm_ocr.py` auto-merges: its status-line assertions gain pages and cost.
  - On that tree, exported to `fixtures-local/` and run with its own `src` first on the path, `test_glm_ocr.py` and `test_reread_safety.py` give **164 passed, 2 failed**. Both failures pin the old 6,000-token estimate:
    - `test_the_z_ai_ok_line_names_pages_and_cost_for_a_404_page_book` expects "404 pages, about $0.07". It is now about $0.04: 404 × 3,500 tokens × $0.03 per million = $0.042.
    - `test_the_reread_confirmation_shows_pages_and_cost_when_z_ai_reads_it` expects `26 * 6000 * 0.03 / 1_000_000` (0.00468). It is now 0.00273.
  - Re-read safety's landing must update those two expectations. Computing them from `glm_ocr.ESTIMATED_TOKENS_PER_PAGE` would stop them pinning the number again. Nothing else on that branch reads the estimate.

### The flake

Every run below is a separate `pytest` process on the merge, with `TMPDIR` in this worktree's `fixtures-local/tmp`. Other worktrees' suites were running, so the machine was loaded.

| Run | Result |
|---|---|
| the two worker-process tests alone (`test_cr_f1_extraction_never_enters_pdfium_in_this_process_while_the_reader_renders`, `test_cr_f1_a_worker_that_crashes_or_hangs_is_recorded_and_the_reading_goes_on`), 25 runs, load 18–37 | **25 of 25 passed** |
| `tests/test_glm_ocr.py` under `-n 8` at `2d8a30125`, 10 runs, load 30–46 | **7 of 10 failed**, each on `test_429_and_5xx_retry_with_their_own_admission_and_receipt` |
| the same with the fix (`4152afcc5`), 20 runs, load 13–24 | **20 of 20 passed** (110 tests each) |

**The worker-process tests did not flake.** The test that did, `test_429_and_5xx_retry_with_their_own_admission_and_receipt`, came with GLM-OCR and is on main.

- **Symptom.** `sleeps` held `[3.0, 2.0]` and then 207 to 2,149 more entries, starting `0.001`.
- **Cause.** The test replaces `time.sleep` for the whole process and asserts every call. (The file's autouse fixture already makes `time.sleep` a no-op; this test records the calls instead.) Since this branch, `extract` reads the text layer in a worker process. `subprocess.run`'s wait polls with `time.sleep` (0.001, 0.002, … up to 0.05 s) when the worker has answered and closed its pipes but not yet exited, which a loaded machine makes common.
- **Main is not exposed.** Its `extract` never starts a process.
- **Reproduction.** A worker that waits 0.3 s after answering fails the test every time, with 708,726 extra entries. It ran as a scratch test, since deleted.
- **The fix** (`4152afcc5`, test only). The recorder keeps only the calls made from `glm_ocr`'s own code, and the assertion `[3.0, 2.0]` is unchanged. With it, the reproduction passes.
- **Left as is.** Under the file's no-op `sleep`, every worker wait in this file spins rather than sleeps. That costs CPU in tests only and never fails.

The full suite and the durability lane each passed on their first run, so neither needed a rerun.

### Gate

Run in this worktree with `TMPDIR=<worktree>/fixtures-local/tmp`.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` · `uv pip install pypdfium2` | ok. The sync removed pypdfium2 and the install restored 5.14.0; a plain `uv run` (an inexact sync) keeps it. |
| `uv run lint-imports --no-cache` | **17 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto`, at `2d8a30125` | **11,153 passed**, 0 failed, 48 warnings (16 min 27 s). That is main's 11,110 plus the branch's 43 more GLM-OCR tests (67 → 110). |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability -n auto`, at `4152afcc5` | **100 passed**, 0 failed (31 s, after about 16 minutes waiting for the lock) |
| Targeted, before the merge commit | **468 passed** across `test_glm_ocr.py`, CLI help, PDF extraction and extractor selection, the Reader's PDF and span views, the `mvp-0.23` and `mvp-0.24` upgrades, and the 19 ingest and source-ingestion files. **52 passed** across config, plan determinism and the vault template. |
| `tests/test_glm_ocr.py` after the fix | 20 of 20 runs under `-n 8` passed (see "The flake") |
| Frontend, `cargo check` | not run: nothing under `apps/` changed |

### Parity

The parity copies are in `fixtures-local/glmq-parity`. They are backup-API copies (`learnloop.db.copies.copy_tree_with_databases`) of this worktree's tracked `fixtures/linear_algebra` and `fixtures/probability` (`mvp-0.8`): one pristine copy each, then one copy per side and per check. Each copy was migrated by its own code (`migration_coordinator.migrate_vault`, 47 migrations to 202):

- **main `a9356f986`**, exported with `git archive` (`src`, `tests`, `migrations`) and placed first on `PYTHONPATH`. The migration printed the archive's `learnloop/__init__.py`, and the export's `glm_ocr` has `MAP_VERSION` 1 and no `glm_text_layer`.
- **the merge's own code.**

On each copy, `learnloop rebuild --shadow --json` and `learnloop doctor --json` ran with `LEARNLOOP_CONFIG_DIR` an empty directory. The outputs were compared after setting aside ULIDs, timestamps, ids, hashes and paths.

| Fixture | Version | Shadow (facet / mastery / schedule) | Doctor issues / errors | Differences, main vs merge |
|---|---|---|---|---:|
| linear algebra | `mvp-0.8` (own) | 22 / 6 / 47 | 106 / 1 | **0** (shadow and doctor) |
| probability | `mvp-0.8` (own) | 2 / 1 / 1 | 134 / 49 (46 `criterion:unknown_dependency`) | **0** |
| linear algebra | `mvp-0.24` | 0 / 0 / 0 | 56 / 1 | **0** |
| probability | `mvp-0.24` | 0 / 0 / 0 | 98 / 49 (46) | **0** |

**How the `mvp-0.24` copies were made.** Each side's own code ran `learnloop upgrade --to mvp-0.9`, then `--to mvp-0.24` (the chain's advisory-guard notes printed). Then `learnloop rebuild-derived-state` ran twice, to its fixed point. The upgrade printed the same notes on both sides. The `mvp-0.8` rows are the fixtures' existing drift. It is the same on both sides, and the same as at the plan-determinism landing.

**No GLM-OCR reading in the owner's data.**
- Linear algebra's extraction runs are Marker (`1.10.2+map2`, 2) and YouTube (2).
- Probability's are Marker (`1.10.2+map3`, 3) and HTML (1).
- No run, model version or health record names GLM-OCR.

So the changed code reads none of the owner's data. Replay never reads an extraction's normaliser, and 0 replay differences is what extraction-only work should give.

**Every run left its copy alone.** `live_database.unchanged` is true on every shadow, and each copy's `state.sqlite` hash is the same before and after its shadow and doctor. Doctor exits 1 on both sides, as on main. The tracked fixtures were only copied: their hashes are unchanged and `git status fixtures/` is clean.

### Safety

- No paid call, no subscription call, no network. No key, credential, `.env` or `settings.env` file was read, nor `~/.config/learnloop/`.
- The main checkout was not touched, and its working vaults were never opened. This worktree's tracked `linear_algebra` and `probability` were opened only by the backup API, and `arxiv_v2` not at all.
- Nothing was pushed, rebased or stashed. `ingest/glm-ocr-quality`, its worktree `learnanything-glmocr` and `fix/reread-safety` were not modified. The dry merge wrote objects only; no ref changed.
- Nothing from `fixtures-local/` is committed.

### Open questions for the owner (defaults applied)

1. **A card line when a scan's footnotes and equation numbers can't be recovered** (open question 1 above; the Codex review's 1). **Default applied: health only.** `glm_ocr_no_text_layer` (and `glm_ocr_text_layer_unavailable` for a worker failure) is recorded in extraction health, with no line on the Library card. A quiet line on every scan's card would be noise against the frictionless defaults. If the owner wants one, it is a single detail keyed on the flag, for the re-read safety stage (which owns `add_source.py`) or a UX stage.
2. **The epigraph's type** (open question 2; the review's 2). **Default applied: it stays typed `Footnote`.** Axler's chapter epigraph is recovered from the text layer as a Footnote, as Marker's reading typed it. An `Epigraph` type would add an IR block type, which is outside the extractor.
3. **Follow-up: Marker can race the Reader the same way** (the review's open question 3). Marker runs in the sidecar's own process (`PdfConverter`), and its PDF text extraction also uses pdfium. So a Marker import on the ingest drain's thread can enter pdfium while the Reader renders, which is the segmentation fault F1 fixed for GLM-OCR. It predates this stage and lies outside the GLM-OCR extractor, so it is not fixed here. **Default: a follow-up stage**, with one of two fixes:
   - the same worker pattern (`glm_text_layer.pdfium_worker`: pdfium in a process of its own) for Marker's conversion;
   - one process-wide pdfium lock, shared by the Reader's renderer and every pdfium caller left in the sidecar's process.
