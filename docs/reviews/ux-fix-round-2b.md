# UX fixes: broken controls, second round (group B)

Stage 3 of the UX journey audit's second part (`ux-journey-audit-2.md` §8, row 3), group B: the defects the second wave of walks found in the Reader, on the phone and in math rendering. Ledger ids UX-15, UX-23 to UX-26 (`refactor-bug-ledger.md`, "From the UX journey audit's walks"). Group A (Today, lessons, the workbench) is `ux-fix-round-2a.md`. Branch `ux/broken-controls-2b` from group A's `ux/broken-controls-2` at `38bc245f58`, one commit per defect. Judged against `ux-journey-audit-criteria.md`. Frontend only: no sidecar change. UX-26 came after the first report, on the owner's ruling; its commit carries its record section and ledger cell.

| Defect | Sev | Commit | What |
|---|---|---|---|
| UX-15 | S2 | `74b6a4e882` | A Reader scroll moves its own pane, never the shell |
| UX-23 | S3 | `123d438cd8` | The phone's feedback says a review reason in words, never its code |
| UX-24 | S3 | `972a0169c6` | A web page's sections are named in words, not by their slugs |
| UX-25 | S3 | `d636f4bbe3` | A kept display environment is drawn as display math |
| UX-26 | S3 | the UX-26 commit | A selection's quote takes each formula once, as its TeX (the owner's ruling, option a) |
| words | | `42af32415e` | The deny-list checks every sentence this round adds |

This record and the ledger cells were the last commit of the first report; UX-26's commit, on the owner's ruling, adds its section and cell.

## UX-15 (S2): the Reader scrolled the whole window

**What the person saw.** student-2 #79-88: after "ask follow-up" and a sent follow-up, the app's top bar and the place tabs had left the window; "Today" could not be found (#83), and scrolling and Escape did not bring them back (#85-87; screenshot `0087`: the whole application moved up, black below its last line). expert-1 #38-41: the same after an answer arrived. notes-1 #92-95: after "show me the passage".

**Cause.** Sixteen `scrollIntoView` calls in the Reader and the panes it opens (`screens/ReaderScreen.tsx` 4: the side-by-side follow-along, a passage jump, two side-pane passages; `screens/reader/AskRail.tsx` the follow-up composer, then `focus()`; `useReaderInquiry.ts` 2: a new answer's card, an opened thread; `useReadingProgress.ts` 3: a quick check's card, a jump to a passage, the resume at the saved place; `useSidePane.ts`, `ReadingPathCard.tsx`, and `components/PdfReaderPane.tsx` 4). The browser's `scrollIntoView` (and `focus()` without `preventScroll`) scrolls every scrolling box between the element and the window, and a box with `overflow: hidden` is one: `html`, `body`, `#root` (index.html and `styles/app.css`) and `.terminal-frame` all were. Once one of them was scrolled, nothing the learner can do scrolls a hidden box back. No `scrollTo` on an ancestor was found (the four `scrollTo`/`scrollTop` writes in the Reader target the pane's own scroller).

**What they see now.** Every Reader and PDF-pane call goes through `components/scrollWithin.ts` `scrollIntoViewWithin(element, { block, behavior })`: it scrolls only the ancestors the learner can scroll (overflow `auto`, `scroll`), by the amount the alignment asks (start, center, end, nearest, clamped; the PDF pane's `scroll-margin-top` kept), outer boxes measured for where the inner moves leave the element, and never a hidden box, `body` or the document. The follow-up composer is focused with `preventScroll` after it is brought into view. And `html`, `body`, `#root` and `.terminal-frame` now clip their overflow (`overflow: clip` after `overflow: hidden`, so a browser without `clip` keeps `hidden`; the frame gains `min-width: 0; min-height: 0`, since a clipped flex item would otherwise keep its content's minimum size): a clipped box cannot be scrolled by any request, so another screen's native call (Ingest, Proposals, the classic Today, the SQLite browser still use one) cannot move the shell either. The top bar and the place tabs stay where they are.

**What jsdom can and cannot show.** jsdom lays nothing out and has no `scrollIntoView`. The Reader tests model the one rule that matters (a browser's `scrollIntoView` or `focus()` may move every ancestor whose overflow is not visible, and the window) and check which boxes a Reader request can move: before the fix the shell's hidden frame and the document were among them; after, only the Reader's own scroll panes. Whether the app's WebKitGTK honours `overflow: clip` on the shell (WebKit has it since Safari 16; the version the app runs on was not checked; without it `hidden` stays, and the Reader's own calls no longer reach the shell anyway), and the move itself, are for the real window.

**New file:** `components/scrollWithin.ts`, so `desktop_validate.py`'s three counts move: 332 to 333 TypeScript files, 321 to 322 entry-reachable, 338 to 339 ACTIVE (comment lines added there). Its Reference note is the landing's regeneration (the validator reports it missing until then; nothing else).

**Tests.**
- `screens/reader/scrollStaysInReader.test.tsx` (new), fail-first: all 4 failed. `opening at the reading place scrolls the Reader's text, and nothing around it`, `a follow-up brings its question box into view inside the rail, never the shell (student-2 #83-88)`, `the answer to a follow-up is brought into view inside the rail, never the shell` (each: `expected [ … ] to not include <div data-testid="shell" …>`); `no module of the Reader asks the browser to scroll an element into view itself` (listed the 16 call sites). Re-checked with `AskRail.tsx` and `PdfReaderPane.tsx` put back at their base versions: the follow-up test and the guard failed again (the guard listing those 5 calls).
- `styles/shellClip.test.ts` (new), 2 tests, both failed with `app.css` and `index.html` at their base versions (`expected ' width: 100%; height: 100%; margin: 0…' to match /overflow:\s*clip/`).
- `components/scrollWithin.test.ts` (new), 7 tests of the helper with boxes placed by hand (start, center, end, nearest, a hidden box and the document never moved, nothing to scroll, nested scrollers, the scroll margin, the clamp). Written after the helper, so its only fail-first is the module's absence.

**Assertions moved, not changed:** six tests read the native call and now read the helper's, with the same assertions on which element was brought into view and how (`vi.mock` of `scrollWithin`): `readingPathsReader.test.tsx` (Orient's "what matters here?" scrolls), `figureProvenanceReader.test.tsx` (the passage scrolled to), `ReaderScreen.followsLearner.test.tsx` (#4, the new answer at `block: "start"`), `ReaderScreen.recapReview.test.tsx` (F5, the inquiry in view), `PdfReaderPane.scroll.test.tsx` and `PdfReaderPane.marks.test.tsx` (the recorded `block:span` strings). Each failed after the change and before the port (6 tests).

## UX-23 (S3): the phone printed a raw review code

**What the person saw.** phone-3 #10: under the score, "valid_alternative_unverified" (the faked models raised it; the print is real).

**Cause.** `apps/learnloop-mobile/src/practice/FeedbackScreen.tsx` rendered `feedback.manualReviewReason` as text. That field is the attempt's `manual_review_reason`, a code. The codes the sidecar writes: `valid_alternative_unverified` (PF-c, `attempts/grading_support.py`), `provisional_pending_clarification`, `grade_held_for_review`, `grade_contract_unrecorded` (replay), `codex_manual_review`, `low_grader_confidence`, `low_self_confidence`, `blank_answer`, and five that carry ids after a colon: `unknown_target_evidence_family:`, `unknown_target_criterion:`, `unanchored_diagnosis_facet:`, `attribution_scope:`, `unknown_error_type:` (`attempts/grading.py`, `attempts/attempts.py`). The desktop's feedback (the simple surface) says something for four of them and nothing for the rest; its classic screen prints "manual review recommended: <code>" for those, which is no word to reuse. No other code is printed on the phone's feedback (the router's "details" sheet is the glass box on demand).

**What they see now.** The desktop's own sentences moved into `app/practiceFeedback.ts` (`HELD_GRADE_LINE`, `PROVISIONAL_GRADE_LINE`, `UNASSESSED_ROUTE_LINE`; `FeedbackSurface` and the classic `FeedbackScreen` render the same text as before), beside `REVIEW_REASON_CODES` and `reviewReasonLine(reason)`; the phone imports them through `@desktop`.

| Code | The phone shows (dim, under the score) |
|---|---|
| `valid_alternative_unverified` | your answer checks out by a different route · criteria that route did not exercise are not assessed (no credit, no lost points) |
| `provisional_pending_clarification` | This grade may change after one question. (the clarifying question is below, as before) |
| `grade_held_for_review`, `grade_contract_unrecorded` | The grader couldn't check the way you answered, so this answer doesn't count either way until it's reviewed. |
| the nine others, with or without ids | nothing (as the desktop's feedback) |
| any code not in the list | nothing, never the code |

A criterion a different route never used (`assessed: false`) reads "(not assessed (a different route))" (the desktop's `NOT_ASSESSED_LABEL`) in place of "(0/1)", which contradicted the line above it.

**Tests** (`apps/learnloop-mobile/src/practice/Feedback.reviewReason.test.tsx`, new, through the fake host), fail-first: 15 failed, 1 control passed. One test per code (13, each with ids after a colon where the sidecar writes them: `expected '…3 / 4valid_alternat…' not to contain 'valid_alternative_unverified'`, and so on), `a code the phone doesn't know shows nothing, not itself`, `a criterion a different route didn't use says so, as on the desktop, instead of a lost point` (`expected <span class="dim"></span> to be null`: the "(0/1)" was there); `no reason, no line` is the control. Each line also passes `findJargon`.

**Found on the way:** the phone shows a held grade's score; the desktop never does. Not this defect's (no code is printed): UX-28, open.

## UX-24 (S3): sections named by their HTML ids

**What the person saw.** retainer-2 #16: the Guide's reading path and Contents listed "(intro)", "modeling-the-elevator-problem", "more-than-one-elevator", "the-real-world-case", "references", "external-links"; "Next: read (intro)". #45: the button "side by side with Wikipedia Elevator Paradox modeling-the-elevator-problem" and the pane's "§ … · modeling-the-elevator-problem".

**Where the label comes from, and why it is an id.** Not the page's HTML ids (Wikipedia's are `Modeling_the_elevator_problem`): our own slug of the heading. `content/pipeline/jobs.py` `default_extract` → `_html_to_markdown` (trafilatura) gives `## Modeling the elevator problem`; `ingest/extractors/normalizers.py` `markdown_to_ir` drops the heading line, keeps only `_slug(heading)` in each block's `section_path`, and `_units_from_level2` makes that slug the unit's `label` (and "(intro)" the part before the first `##`). `section_map.extraction_sections` passes `unit.label` to the guide plan; the reading path, side by side, find-section and the phone's section list all carry it. The stored extraction holds no heading text anywhere (the walk's vault, read from a copy: `source_document_units.label` is the slug, the blocks start after the heading), only the stored original page does. So, as the brief rules for this case: no stored text changed; the slug is shown as words, and the proper fix is filed under UX-11's re-read.

**What they see now.** `screens/reader/readerShared.ts` `sectionWords(label)`: a label that is a slug (lowercase words and digits joined by hyphens) reads as words with the first letter capital ("Modeling the elevator problem", "External links", "References"), "(intro)" reads "Introduction", and anything else (a book's "7.1 Symmetric matrices", "§5.A", "Section 3", "Mixtures") is left as it is. Used where a section's name is shown: the Guide's Contents and section card and its two section sentences, the reading path's sections and its "Next: read …" line (the sidecar's sentence, with the next section's stored label replaced by its words), the Reader's header and § line, the detour labels, side by side (the crumb button, the pane's header, its previous and next), the compare buttons, find-section's and also-in-books' hits and peek, a deliverable's section marker, and on the phone the section list, the header and the plan banner. What is sent or matched on keeps the stored label (the "where else is this explained" query, the section objects passed on).

**Tests.**
- `screens/reader/sectionWords.test.tsx` (new), fail-first: all 5 failed: the slug and the book-title tests (`sectionWords is not a function`), the Guide (`Unable to find an element with the text: Introduction`), the reading path (`Unable to find role="button" and name "Modeling the elevator problem"`), side by side (`expected 'side by side with Wikipedia Elevator …' to be …`).
- `apps/learnloop-mobile/src/read/sectionWords.test.tsx` (new), fail-first: `expected [ '(intro)', …(3) ] to deeply equal [ 'Introduction', …(3) ]`.

**Filed under UX-11** (its re-read): keeping each heading's own words as its section's title, and dropping the page furniture the extraction keeps at a section's start (Wikipedia's "[edit]" opens every section's first paragraph). Both change extracted text. A read-time route exists, as UX-2's macros did it: read the headings from the stored original and map slug to heading text; not taken, because the brief limits this case to the stored extraction.

## UX-25 (S3): kept display equations shown as raw TeX

**What the person saw.** student-2 #65, retainer-2 #38-44, project-1, expert-1: the extraction's few kept display equations printed as `\begin{equation*} A = QDQ^{-1} = QDQ^T. \end{equation*}`.

**Cause.** The sample's three kept equations are blocks whose whole text is a bare environment, in no `$$`. `render/MarkdownMath.tsx` passes the block through `normalizeMathDelimiters` (which rewrites `\[ \]` and `\( \)` only) and remark-math, which knows only `$` and `$$`, so the environment stayed text.

**What they see now.** `MarkdownMath` first puts each bare display environment KaTeX draws (`equation`, `align`, `gather`, `alignat`, starred or not) in `$$` on lines of its own, as the page's own `\[ … \]` already are, skipping code (fences and inline), escaped dollars and math already delimited (`$$…$$`, `$…$`, `\[…\]`, `\(…\)`: an environment inside is that formula's own). One never closed, or one KaTeX cannot draw (`multline`, `displaymath`), stays as written rather than becoming an error. The source's macros apply (`\dtil`, `\uvec` in the sample). The phone draws its Reader with the same `MarkdownMath`, so it gets the same. In a paragraph the equation is drawn on its own line between the words.

**The book-math check is untouched** (`markdownPipeline.ts`, `pageMathSegments.ts`, `figures/book_math.py`, the bundle): it still finds no equation in such a block (its Python side returns none for text with no `$`, `\[` or `\(`), so such a block is never labelled "checked". The check places a label by the segment's offsets in the block's text, never by the page's count of math elements, and the corpus already pins page-only math (a struck-through equation, a `math` fence).

**Tests.**
- `render/displayEnvironments.test.tsx` (new, the real renderer), fail-first: 7 failed, 2 passed (the controls: an environment KaTeX cannot draw or never closed stays text; the check finds no equation in the three kept blocks). The three kept environments of the sample (`expected +0 to be 1`, no `katex-display`), the macros (`expected '<p>\begin{equation*}\nV = \frac 1N\su…' to contain '<mi mathvariant="bold">d</mi>'`), in a paragraph, the other environments, and already-delimited math. Two inputs were corrected after that first run, before the fix: a one-line `$$\begin{equation*} … \end{equation*}$$` (remark-math reads one-line `$$` as inline math, so it is no display today either, and stays untouched) became the same on lines of its own, and the `equation` case lost an `&` (invalid there).
- `apps/learnloop-mobile/src/read/displayEnvironments.test.tsx` (new, the phone Reader through the fake host): written after the fix; run with `MarkdownMath.tsx` at its base version it failed (`expected +0 to be 2`), with the fix it passes.

## UX-26 (S3): a selection's quote takes each formula once, as its TeX

**What the person saw.** student-2 #87: Ask's "§ from the book" quote of the passage showed each formula twice (the rendered formula's text layers, e.g. "matrix Q Q").

**Where the quote is built.** `screens/ReaderScreen.tsx` `onMouseUp`: `quote = getSelection().toString()`, whitespace squeezed. A KaTeX formula is a MathML copy (with its TeX in an `<annotation>`) beside an HTML copy, and the selection's text holds them all. That string is `selection.quote`; `useReaderInquiry.ts` `ask` sends it as `reader_ask`'s `selectionQuote`, which the tutor reads (`reader_dialogue.py` `selection_quote_md`) and the exchange stores; the composer's "ASKING ABOUT" chip shows it, and "§ from the book" shows the stored `selectionQuoteMd`. So the quote the learner sees and the quote sent are one string. This stage first stopped there (the fix changes what is sent); the owner ruled for option (a): the chip, the stored exchange and what the tutor reads are the same clean string, and no prompt template changes.

**Both forms**, for the sample's sentence "… into a matrix \(Q\) produces an orthogonal matrix, which means that \(Q^T = Q^{-1}\text{.}\) We then have" (jsdom with the real renderer; the walk's Chrome gave the two visible layers, jsdom also includes the annotation's TeX):

| | The text |
|---|---|
| Before (jsdom) | `… into a matrix QQQ produces an orthogonal matrix, which means that QT=Q−1.Q^T = Q^{-1}\text{.}QT=Q−1. We then have` |
| Before (the walk, Chrome) | each formula as its MathML and its HTML text, as the audit quotes it: "matrix 𝑄 Q", "Q T =Q −1" |
| Now | `… into a matrix $Q$ produces an orthogonal matrix, which means that $Q^T = Q^{-1}\text{.}$ We then have` (a display formula as `$$…$$`) |

**The function.** `render/mathSnippet.ts` `selectionQuote(range, asSelected)`: it walks the text nodes the range touches; a text node inside a formula (`.katex`, or KaTeX's `.katex-error`) stands for its whole formula, taken once: the TeX is read from the formula's own `<annotation encoding="application/x-tex">` (the source KaTeX was given, after the page's `\(…\)` to `$…$` rewrite, so the book's own macros stay as written, `\vvec`), written `$…$`, or `$$…$$` when the formula is inside `.katex-display` (a `.katex-error` gives its own text, which is its source). So a selection that starts or ends inside a formula takes it whole. Text outside formulas is taken as selected (cut at the range's ends), with a line break between blocks, and the result's whitespace squeezed to single spaces. A selection that touches no formula returns `asSelected` unchanged, so every quote without math is byte for byte what it was.

**Where it is used.** Wherever a selection becomes a quote for Ask:
- the desktop Reader's selection (`ReaderScreen.tsx` `onMouseUp`): `selection.quote`, so the "ASKING ABOUT" chip, `reader_ask`'s `selectionQuote`, the stored exchange, and the other places that read `selection.quote` (the intent box's question, "make your own practice"'s stem, the Library compose box, an exercise import's shown quote) all get the clean form;
- side by side's second pane (`SideBySidePane.tsx` `selectionIn`), whose quote its Ask sends;
- the phone's selection sheet (`apps/learnloop-mobile/src/read/ReaderScreen.tsx` `readSelection`): it had the same defect (`toString().trim()` over the same renderer); the sheet shows, Ask sends and Copy copies the clean form.

**Notes and highlights: not changed.** A highlight or note anchors through its `rawSelection.nodes`, whose per-block `quote` the sidecar finds the passage by (`reader/annotations.py` `_locate_quote`: exact, canonical, then a word alignment; the stored anchor's `exact_quote` is then the block's own text). Those words stay the words as selected: on the desktop `collectSelectionNodes` and the right-click tag are untouched, side by side's fallback node keeps the text as selected, and the phone's Save sends `anchorQuote` (the words as selected) where the two differ. A highlight's shown quote after saving is the sidecar's anchored text, as before.

**Old exchanges.** No migration, no rewrite. An exchange saved before keeps its stored quote and comes back from history as it was stored: "§ from the book" draws a quote with `MarkdownMath` only when it holds a `$` (a quote taken the new way, with a formula); a quote with no `$` (every quote saved before, which holds the formulas' layers as text) is the stored text in the same blockquote as before, so an old exchange still shows "matrix QQQ …" exactly as it did. A quote from before that held a literal dollar (the book's own text) would now be drawn as Markdown; no such case is known.

**Identity and prompts.** No template changed; only the learner's selection is read correctly. `tests/test_identity_pins.py`, `tests/test_retired_config_identities.py` and the tutor and Reader ask files (`test_reader_dialogue.py`, `test_reader_tutor_offers.py`, `test_reader_tutor_retrieval.py`, `test_reader_tutor_switch_off.py`, `test_sidecar_tutor_qa.py`, `test_tutor_qa.py`): 450 passed, nothing moved.

**Tests**, written first:
- `render/selectionQuote.test.tsx` (new, the real renderer): `the walk's passage: inline math in a sentence`, `a selection that starts or ends inside a formula takes the formula whole`, `display math is quoted as $$…$$`, `a selection with no math is the selection's text, byte for byte`. All 4 failed first (`selectionQuote is not a function`).
- `screens/reader/askQuoteMath.test.tsx` (new, the real Reader and renderer): `UX-26: asking about a passage with a formula sends the passage with the formula once, as its TeX` failed first (`expected 'A real symmetric matrix A=A⊤A = A^\to…' to be 'A real symmetric matrix $A = A^\top$ …'`; the test's first run failed on its own selector and was corrected before this). Its last three assertions ("§ from the book" draws the formula once, with no dollar sign) were added with the "§ from the book" change. Controls that passed before and after: `UX-26: a highlight of the same selection anchors with the words it always did` (`readerCapture`'s `rawSelection.nodes` are the block's selected text, every layer included) and `UX-26: an exchange saved before the fix is shown as it was stored`.
- `apps/learnloop-mobile/src/read/selectionQuote.test.tsx` (new, through the fake host): the sheet shows, Ask sends, and Save anchors with the words as selected. Run with the phone's `ReaderScreen.tsx` and `SelectionSheet.tsx` at their base versions it failed (`expected '§ orthonormal vectors into a matrix Q…' to be '§ orthonormal vectors into a matrix $…'`); with the fix it passes. (Its selection was narrowed to the passage's paragraph before that run: the block also holds a "View the page" button.)

**Snapshot moved, deliberately:** `screens/reader/__snapshots__/tutorSwitchOff.test.tsx.snap`, one entry ("ask rail after an answer lands"): that test's selection quote is the block's raw markdown (it mocks the renderer, so the quote holds `$A = A^\top$`), so its "§ from the book" is now drawn through `MarkdownMath` (`<blockquote class="md-tight"><div>…</div>`); the text is the same, checked character by character.

## Plain words

`copy/denyList.test.tsx` gains "the broken controls 2b sentence: %s" over every review line a feedback can now show and the section names as the Reader says them. Each new component test also checks its lines with `findJargon`.

## Sidecar change

None. No schema, migration, algorithm tag, config key, stored text, block hash or prompt change. What is sent to a model changes in one place, on the owner's ruling: the selection quote Ask sends (UX-26) now holds each formula once, as its TeX; no template changes. The phone's service worker and caching and the book-math check bundle are untouched.

## What a walk must check

- **student-2 #79-88 (UX-15), in the WebKitGTK window.** In the Reader on the Ask tab, open a thread, "ask follow-up", send one: the composer and then the answer come into view inside the rail; the top bar and the place tabs stay; "Today" is clickable. **expert-1 #38-41:** the same when an answer lands. **notes-1 #90-95:** "show me the passage", then Today and "← Library" are where they were. Also open a book at a saved place, jump from the Guide's Contents, use side by side's follow along, and the PDF view's find: the panes move, the window never does.
- **phone-3 #8-10 (UX-23).** Submit an answer whose grade carries a review reason: no code under the score; for a different route the sentence above, for the nine others nothing. A criterion the route did not use reads "(not assessed (a different route))".
- **retainer-2 #16 and #43-45 (UX-24).** The elevator article's Guide: Contents, the reading path and "Next: read Introduction · about 1 min of reading" name the sections in words; "side by side with Wikipedia Elevator Paradox Modeling the elevator problem" and the pane's header likewise. A PDF book's sections are named as before. The phone's section list (phone-2 or phone-3 on the article) likewise.
- **student-2 #65, retainer-2 #38-44, project-1, expert-1 (UX-25).** The sample chapter's "A = QDQ^{-1} = QDQ^T." and the two variance equations drawn as display math, with bold vectors, no backslashes. The phone's Reader on the same section.
- **student-2 #79-87 (UX-26).** Select a passage with formulas ("…into a matrix Q produces…, which means that Q^T = Q^{-1}") and ask: the "ASKING ABOUT" chip and the answer's "§ from the book" show each formula once, drawn; select from the middle of a formula: it is quoted whole. An exchange saved before shows its old quote unchanged. Highlight the same passage: it lands on the passage as before. On the phone (phone-2 or phone-3, the sample): the selection sheet's quote, likewise.

## What was run

Every command through the scratch wrapper (`env -i`, isolated HOME, CODEX_HOME, config dir), node in a 5G scope, Python in a 3G scope at `-n 1`, one at a time.

| Command | Result |
|---|---|
| `npm ci` (desktop, then phone) | exit 0 (esbuild's install script blocked by allowScripts, as before) |
| `npx vitest run --maxWorkers=4 <files>` per defect, fail-first and passing | as above, per defect |
| the 77 desktop test files that mention `scrollIntoView` or `scrollTo` (after UX-15, before porting) | 6 failed, 633 passed; after the port: the 6 files 63 passed |
| the 35 desktop test files on feedback (after UX-23) | 331 passed |
| desktop `src/screens/reader`, `ReaderScreen*`, `PdfReaderPane*`, `screens/workbench` (after UX-24) | 143 files, 1639 passed |
| desktop `src/render`, `src/screens/reader/figures` (after UX-25; the book-math parity lane included) | 24 files, 615 passed |
| desktop `npm run typecheck` | exit 0 |
| desktop `npx vitest run --maxWorkers=4` (whole suite) | Test Files 310 passed (310), Tests 3106 passed (3106) |
| desktop `npm run frontend:build` | exit 0, "✓ built in 2.95s" (the usual chunk-size notice) |
| phone `npm run typecheck` | exit 0 |
| phone `npx vitest run --maxWorkers=4` (whole suite) | Test Files 40 passed (40), Tests 408 passed (408) |
| phone `npm run build` | exit 0, "✓ built in 1.02s" |
| `docs/learnloop-architecture-vault/_scripts/desktop_validate.py` | no count drift; reports the new file's missing Reference note and the stale notes (the landing regenerates) |
| `pytest tests/test_identity_pins.py` after each of the four defect commits | 342 passed, each time |
| `scripts/affected_tests.py --files <the changed non-test files>` | 6 files |
| `pytest` those 6 (`test_causal_repair_sidecar_rpcs`, `test_desktop_activation_audit`, `test_mobile_https`, `test_mobile_rpc`, `test_rw5c_block_policy`, `test_ux_walk_harness`) | 194 passed, 1 skipped |
| `pytest tests/test_identity_pins.py tests/test_structure_ratchets.py tests/test_effective_defaults_golden.py tests/test_cli_help_snapshot.py tests/test_kill_switches.py tests/test_sqlite_file_copies.py` | 383 passed |
| `pytest tests/test_test_layout.py` (alone) | 3 passed |
| `pytest tests/test_architecture.py` (alone) | 18 passed |
| `ruff check` | All checks passed! |
| `lint-imports --no-cache` | Contracts: 43 kept, 0 broken. |
| `scripts/check_gate_partition.py` | collected 31709: landing 31644 + arc_close 65 (exit 0) |

For UX-26 (after the owner's ruling), the same way:

| Command | Result |
|---|---|
| `npx vitest run` the new UX-26 files, fail-first and passing | as in its section |
| desktop `src/screens/reader` | 1 failed (the `tutorSwitchOff` snapshot, updated deliberately), 1499 passed; then 4 passed in that file |
| desktop `npm run typecheck` | exit 0 |
| desktop `npx vitest run --maxWorkers=4` (whole suite) | Test Files 312 passed (312), Tests 3113 passed (3113) |
| desktop `npm run frontend:build` | exit 0, "✓ built in 2.81s" |
| phone `npm run typecheck` | exit 0 |
| phone `npx vitest run --maxWorkers=4` (whole suite) | Test Files 41 passed (41), Tests 409 passed (409) |
| phone `npm run build` | exit 0, "✓ built in 821ms" |
| `pytest tests/test_identity_pins.py tests/test_retired_config_identities.py tests/test_reader_dialogue.py tests/test_reader_tutor_offers.py tests/test_reader_tutor_retrieval.py tests/test_reader_tutor_switch_off.py tests/test_sidecar_tutor_qa.py tests/test_tutor_qa.py` | 450 passed |
| `scripts/affected_tests.py --files <the five changed source files>` | `tests/test_rw5c_block_policy.py`: 39 passed |
| `pytest tests/test_structure_ratchets.py tests/test_desktop_activation_audit.py` | 7 passed |

## Not verified here

- Nothing was walked or launched: no app, browser or server. UX-15's move and `overflow: clip` in WebKitGTK are for the real window; jsdom checks which boxes a request may move, under a model of the browser's rule.
- Other screens still call the native `scrollIntoView` (Ingest, Proposals, the classic Today, the ingest activity list, the SQLite browser). The shell's clip keeps the shell in place for them; a hidden box inside those screens could still shift. Not walked as broken.
- `sectionWords` reads "root" (the part of a page before its first level-1 heading, when it has several) as "Root"; no walk showed one. A real heading that is one lowercase word or a hyphenated lowercase phrase is capitalised and loses its hyphens.
- The "where else is this explained" search still sends a web page's section slug as its query (unchanged on purpose: it is sent).
- UX-25 in table cells, lists and quotes was not tried; the walks' equations are blocks of their own.
- The walk evidence was read (step logs, observations, copies of two walks' databases in the scratch directory, read only); nothing of it is in tracked files.
