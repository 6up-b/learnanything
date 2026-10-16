# Original-PDF selection: Codex review fixes

Branch `reader/pdf-selection`, worktree `learnanything-ux-impl`. Codex
reviewed the stage at `43bb85a10` (`37a2a7e5f..reader/pdf-selection`, job
`20261015-175114-j8GLEH`) and returned seven findings: six Medium and one
Low. All seven are fixed and none was rejected. The fixes are recorded in
the stage's design record (`docs/reviews/reader-pdf-selection.md`, commit
`10562d526`). No model, Decider or embedding call was made and no money was
spent. No migration was added, no table changed and no migration number was
taken: the undo still uses the `disposition` event type the annotation
events already allowed.

The fix step was interrupted three times by Claude Code restarts (caused by
a full `/tmp`, which the owner has since cleared). The fixes were committed
before the last restart. The reproductions and the gate below were run after
it, on the final tree.

Owner decisions in force (2026-10-12):

- the spec defaults are accepted;
- Codex on the subscription may run every paid LLM role without a
  physical-request bound;
- the Decider is `perplexity/pplx-decider-v1.1-27b` on OpenRouter;
- frictionless defaults: honest labels, generous defaults, and live changes
  behind kill switches.

## Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Word hit-testing assumes every font is Helvetica | Fixed | `e2916ff0e` | `pdfSelection/fonts.test.ts` (11 tests: Courier, Times-Roman and Type3 coordinates worked out by hand from the PDF's own numbers; "a click inside a word selects that word … (the review's x = 102 in Courier)", "and from the text content while the operator list is not read yet"); `PdfReaderPane.selection.test.tsx` › "words where the page paints them (Codex review F1)" |
| F2 | Medium | Clearing a protected selection re-enables Ask | Fixed | `01b8cd17f` | `ReaderScreen.pdfSelection.test.tsx` › "the Ask, held back by what it would send (Codex review F2)": "no composer after a selection is cleared", "no composer when it opens on a passage with no selection", "a held-out active passage offers no composer; another passage does" |
| F3 | Medium | Undo can withdraw a different, concurrent deletion | Fixed | `01b8cd17f` | `tests/test_reader_pdf_selection.py::test_an_undo_withdraws_only_the_delete_it_names_never_a_concurrent_one`, `::test_a_restore_racing_a_second_delete_leaves_it_hidden`, `::test_an_undo_must_name_a_delete_of_that_annotation`, `::test_a_second_delete_after_an_undo_hides_it_again` (now with a retry); `ReaderScreen.pdfSelection.test.tsx` › "an undo while another delete of it stands does not draw it back" |
| F4 | Medium | Undo can paint another book's annotation on the current book | Fixed | `01b8cd17f` | `ReaderScreen.pdfSelection.test.tsx` › "a removal's undo belongs to its book and its delete": "Ctrl+Z in another book opened within the undo's time does nothing there", "a delete that answers after another book opened leaves that book's list and offers no undo" |
| F5 | Medium | Continuing pages of a highlight have no usable controls | Fixed | `e2916ff0e` | `PdfReaderPane.selection.test.tsx` › "a highlight running over a page break (Codex review F5)": "a click on its part on the next page opens its chip there, above that part", "each page it is drawn on has its keyboard stop: Tab reaches the part in view, Enter and Delete act on it" |
| F6 | Medium | Escape does not cancel an ongoing drag | Fixed | `e2916ff0e` | `PdfReaderPane.selection.test.tsx` › "Esc and Shift+Home/End (Codex review F6, F7)": "Esc in the middle of a drag ends it: the release selects nothing, after a frame was drawn or before", "Esc in the middle of an Alt sweep ends it, wherever the keyboard is" |
| F7 | Low | The first Shift+Home/End ignores the line boundary | Fixed | `e2916ff0e` | `PdfReaderPane.selection.test.tsx` › "from a click on a word, the first Shift+Home selects to the line's start and Shift+End to its end" |

### What each fix does

- **F1.** Once a page is drawn, its words are placed from the page's
  operator list (`operatorWords` in `pdfSelection/geometry.ts`). Each glyph
  gets its own advance in its own font, with `Tc`, `Tw`, `Tz`, `Ts`, `Tm`,
  leading and form XObjects applied, and annotations left out. The list is
  read once per page. Until it is read, the text content's runs are split by
  their font family's widths (Helvetica, Times-Roman or monospace). That is
  exact for the standard fonts and an estimate for an embedded one, never
  Helvetica's widths for every font. A page leaving the view also releases
  what pdf.js read to draw it (`page.cleanup()`).
- **F2.** `groundingProtected` with `askGroundingSpans` (`readerShared.ts`)
  checks what an Ask would send now, in the order `useReaderInquiry`'s
  `submitAsk` grounds it: an inherited thread's passage, else the selection,
  else the active passage. A reading that rule 4 holds back hides the Ask
  composer whether or not anything is selected. `AskRail` shows the
  protection line in place of the composer in both cases.
- **F3.** `reader.restore_annotation` now takes `deleteEventId`, the
  `eventId` that `reader.delete_intent_annotation` returned.
  `Repository.withdraw_annotation_delete` checks that this event is a delete
  of that annotation and appends the undo naming it, both in one `BEGIN
  IMMEDIATE` transaction. The listing hides an annotation while any of its
  deletes stands, meaning a delete that no undo names. An undo therefore
  never withdraws a delete written meanwhile, and a retry changes nothing. A
  missing `deleteEventId`, or one naming anything other than a delete of
  that annotation, is a `validation_error`. The answer carries `listed`, and
  the Reader draws the highlight again only when `listed` is true.
- **F4.** The undo offer records its delete event, source and extraction.
  `resetSourceState` ends the offer and bumps a source epoch. An annotation
  read, delete or undo that answers after another book opened never touches
  the new book's list. Undo runs only on the reading the highlight was
  removed from.
- **F5.** A highlight now has a keyboard stop on every page it is drawn on.
  A stop on a later page is labelled "continued from the page before". A
  click on any part, or focus on any stop, opens the chip above that part,
  on that page.
- **F6.** Esc during a plain drag or an Alt sweep ends the gesture,
  wherever the keyboard focus is. It clears the press, the pending animation
  frame and the auto-scroll, so the release selects nothing. This works
  before the first drag frame too. Esc already cleared a Ctrl box drag
  before this fix.
- **F7.** The special case for the first key from a caret, which takes the
  word under the caret first, now applies only to Shift+Left and
  Shift+Right. Shift+Home and Shift+End go through `moveHead()` at once.

### Reproductions on the original code

The new tests were run against the code at `43bb85a10`, the commit Codex
reviewed:

- **Python:** `src/` and `migrations/` were extracted with `git archive` into
  the scratchpad and put first on `PYTHONPATH`, with pytest's `pythonpath`
  cleared.
- **Frontend:** `apps/learnloop-tauri` was extracted the same way, with the
  worktree's `node_modules` linked in. Only the new and changed test files
  and test helpers were copied over (`syntheticPdf.ts` and its recorded
  text-content fixture, which gained Courier, Times-Roman and Type3 support).
  Every implementation file stayed as it was at `43bb85a10`.

| Finding | Test | On `43bb85a10` |
|---|---|---|
| F1 | ad hoc copy of the review's case (Courier 10 pt `iiiiiiiiii WWWWWWWWWW end` at x = 72, the text content only, the old `setPageText` signature) | a click at x = 102 selected `WWWWWWWWWW`, not `iiiiiiiiii` |
| F1 | `fonts.test.ts` › "monospace and serif runs are split exactly for the standard fonts" | a word's edge was 36.0 pt off (the Helvetica split of a Courier run) |
| F1 | the other ten `fonts.test.ts` tests and the pane's F1 test | fail on API the fix added (`operatorWords`, `hasPageGlyphs`, the pane reading the operator list), so they do not reproduce F1 on their own |
| F2 | the three Ask tests | no protection line in the Ask rail (`[data-ask-protected]` missing) after the selection was cleared, on a passage opened with no selection, and on a held-out active passage |
| F3 | `test_an_undo_withdraws_only_the_delete_it_names_never_a_concurrent_one` | after D1, D2 and an undo naming D1, the annotation was listed (`['01M5…'] == []` failed at its first assertion, before any new API is called) |
| F3 | ad hoc race on the old API (a second delete lands between the old restore's read of the pending delete and its write) | the annotation was listed again: the undo of the first delete withdrew the second |
| F3 | the Reader's "an undo while another delete of it stands does not draw it back" | the undo was sent without the delete's id (`{ annotationId }` only), so the sidecar could not tell which delete it withdraws |
| F4 | the two book-change tests | the undo offer (`role="status"`) was still shown in the other book |
| F5 | the two page-break tests | no chip and no keyboard stop on the highlight's second page |
| F6 | the drag and Alt-sweep Esc tests | the release after Esc committed a selection (two nodes; the sweep's selection callback was called) |
| F7 | the Shift+Home/End test | the first Shift+Home selected only `fox`, not `The quick brown fox` |

Altogether, 25 of the 45 tests in the three frontend files failed on
`43bb85a10`. The remaining 20 are earlier tests, and they passed. Four of
the Python tests failed: three on the new `delete_event_id` keyword, and one
at its first assertion as described above.

### Notes on the review's other points

- **"Claims that don't hold."** Each one maps to a finding above (F1, F2,
  F4, F5, F6/F7). The design record's wording was corrected along with each
  fix (`10562d526`).
- **RW5a figure-region selection** (spec conformance row). This is not a
  finding of this stage. `ux_reader_workbench_v1.md` §11 assigns region
  selection on a figure to RW5a (explorable figures, §4.7), and this stage
  does not build that phase. A figure with no text still selects nothing and
  never its caption, as the design record states.
- **Cross-source parity: no new transcript fixture.** Not a finding. The
  extracted-text view keeps the browser's native selection and its
  passage-level highlights, as the design record says.
  `SelectionModel.exactNode` gives that view's nodes the same shape. No
  transcript surface changed.
- **Intent box and active-reading actions.** These are deferred to their
  workbench stages, as the review notes. Nothing here changes them.

## Gate

The gate was run on 2026-10-15, after the last restart, on the final fix
tree `10562d526` plus this record (`e2abcec51`, docs only). That tree is on branch
`reader/pdf-selection`, on base `37a2a7e5f`, and main was not merged in.
Versions: Python 3.12.14, SQLite 3.53.1, Node 26.11.1, npm 12.2.0, cargo
1.99.0. `TMPDIR` was the worktree's `fixtures-local/tmp`. No paid call was
made and no vault was touched.

| Lane | Command | Result |
|---|---|---|
| Install | `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| Import contracts | `uv run lint-imports --no-cache` | **22 kept, 0 broken** |
| Targeted (no lock) | `tests/test_reader_pdf_selection.py`, `test_mobile_allowlist.py`, `test_coordinated_migrations.py` | **176 passed** |
| Full suite | `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto` | **11860 passed, 1 failed** (16 warnings), 15:00. The failure was `test_chatgpt_plan_provider.py::test_the_deadline_shuts_a_stalled_stream`, a timing test under the machine's load: the stream broke on a `TimeoutError` before the deadline's own error. Rerun alone it passed **3 of 3** times. This stage does not touch the ChatGPT plan provider. |
| Durability | `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -m durability` | **106 passed**, 11755 deselected, 1:56 |
| Frontend | `npm install`; `npm run typecheck`; `npm test`; `npm run frontend:build` | typecheck clean; build ok (Vite's usual chunk-size notice). Vitest: **671 passed in 90 files**. A first run alongside the full suite timed out one test at 5 s (`ReaderScreen.inquiry.test.tsx`, the detour-strip test). That file passed 10 of 10 twice alone, and the whole of vitest passed on the rerun. |
| Tauri | `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` | ok (`src-tauri` is unchanged since the reviewed commit; the `reader_restore_annotation` passthrough forwards its input as it is, `deleteEventId` included) |
| DB references | none | not run: no schema change (head stays 204 on this base) |

Compared with the stage's own gate at `e2108f0c3` (11858 passed, vitest
648), the Python count adds the three new F3 tests (11858 + 3 = 11861 =
11860 + 1). Vitest adds the 23 new frontend tests (648 + 23 = 671).
