# UX fix stage 2: math and empty-goal copy

Stage 2 of the UX journey audit's fix stages (`ux-journey-audit.md` §10, row 2): defects UX-2 (a source's own TeX macros) and UX-8 (the goal report on an empty goal). UX-10 waits for the owner's ruling and is not here. Branch `ux/stage2-math-and-empty-goal`, from `c496806d7d` (stages 1, 3 and 4). Judged against `ux-journey-audit-criteria.md`. No schema change, no migration, no algorithm tag, no config key, no prompt change.

| Defect | Commit | What |
|---|---|---|
| UX-8 | `e9760113ee` | The goal report says what is true before anything is checked |
| UX-2 | `ce57db2c97` | The Reader's reply carries the source's own TeX macros (sidecar) |
| UX-2 | `5367e7d896` | The source's macros reach KaTeX; snippets show no raw TeX (desktop and phone) |
| UX-8 | `9eb8309b65` | The empty goal's comment names no audit id |
| UX-2 | `da7a7683f5` | `mathMacros` is absent when a source defines none (keeps every other reply byte for byte) |
| UX-2 | `e15d8bc5ee` | Six switch-off Reader snapshots take the whole-formula clip |
| UX-2 | `09dae4d917` | No macro table while anything of the source is protected (the coordinator's review) |

This record and the ledger rows are the last commit.

## UX-2: a source's own TeX macros

**What the learner saw** (student-1 #132, #147; beginner-1 #61, #106; retainer-1 #19, #61; phone-2 #37). The sample chapter (`samples/understanding-linear-algebra-symmetric-matrices-and-variance.html`) writes `\vvec`, `\uvec`, `\real`, `\twovec`, `\amp` in its formulas. In the Reader they showed as red raw commands, `\real` as ℜ, the Ask chip showed "(\lambda = \…", and Today's thread line showed "Suppose that \(\uvec\) is an eigenvector of \(B\) with asso…".

### The map: from the page to each renderer

**Where the definitions are.** In the page's HTML, a hidden element, `<div id="latex-macros" class="hidden-content process-math" style="display:none">`, holds one `\( … \)` with 62 definitions: 61 `\newcommand` and one `\renewcommand` (of `\row`, to the same body), so 61 names. (The audit's "64" counted the string "newcommand" in the file; the other two name MathJax's `newcommand` package in its configuration script.) Three bodies are HTML entities in the source (`\newcommand{\amp}{&amp;}`, `\lt`, `\gt`), which MathJax reads decoded. The MathJax configuration itself defines no macros (`tex.macros` is absent); `\definecolor{fillinmathshade}` sits beside them.

**What each stage keeps.**

| Stage | Code | Keeps the formulas | Keeps the definitions |
|---|---|---|---|
| Fetch and store the original | `content/pipeline/add_source.py` → `ingest/originals.py` `store_original_bytes` | the whole page, byte for byte, in `canonical-sources/raw/sha256-…` under the revision's `asset_hash` | yes |
| Extraction (HTML) | `content/pipeline/jobs.py` `default_extract` → `_html_to_markdown` (trafilatura, `output_format="markdown"`) → `ingest/extractors` `markdown_to_ir` (`extractor="html"`, version 2) | inline `\(…\)` yes; display math mostly not (see "Found on the way") | **no**: trafilatura drops `display:none` content, so the macro element never reaches the markdown |
| Stored blocks | `source_document_blocks.text`, `content_hash` (sha256 of the text); the extraction run's request and result hashes | `\vvec` etc. as written | no |
| Render view | `reader/source_render_views.py`: per block the sanitized text as `markdown`, `katex_nodes: []`, and a `content_hash` over the blocks' hashes; stored in `source_render_views` | yes | no |
| Sidecar reply | `reader.render_view` (desktop, and the phone through the host's allowlist with `sectionId`), `reader.side_by_side_section` (the second pane) | yes | **now yes**: `mathMacros` beside the blocks (below) |

**What each renderer does with a block's math.**

| Surface | Renderer | Before | After |
|---|---|---|---|
| Desktop Reader text (`ReaderScreen.tsx` block list) | `MarkdownMath` (react-markdown, remark-math, rehype-katex with no options, `throwOnError` then KaTeX's error fallback) | `\vvec` undefined: raw command in KaTeX's error colour; `\real` KaTeX's built-in ℜ | the book's macros (provider over the whole Reader) |
| Desktop Ask chip "ASKING ABOUT …" (`AskRail.tsx`) | `MarkdownMath` over `clip(text, 150/300)` | macros as above, and a cut inside a formula left a dangling `\(` shown as text | macros, and `clipMath` never cuts inside a formula |
| Desktop "FOLLOW-UP TO" passage (`AskRail.tsx`) | plain text `clip` | raw TeX | `MarkdownMath` over `clipMath` |
| Desktop side-by-side pane (`SideBySidePane.tsx`) | `MarkdownMath` | as above | the other book's own macros (its own provider, never the open book's) |
| Desktop Reader model text: tutor answers, quick checks, guide questions, Library answers | `MarkdownMath` | red where the model copied `\vvec` | the open book's macros (they are under the Reader's provider) |
| Desktop citation labels: Ask overlay `§`/`❯`, Reader answer "source:", Library "cites:" | plain text of the sidecar's `passage_label` (first 60 characters) | raw TeX | `plainMathLine`: each formula as readable words |
| Today's "Pick up a thread" (`todayPlan.ts` `questionThread`, `problemThread`) | plain text (`oneLine`, and the citation label) | raw TeX | `plainMathLine` |
| Phone Reader (`apps/learnloop-mobile/src/read/ReaderScreen.tsx`) | `PhoneMarkdown` = the desktop's `MarkdownMath` | as desktop | the section reply's `mathMacros` |
| Practice, feedback, lessons, the practice exam, the phone's practice (model-written text) | `MarkdownMath` | red where the model copied a book's macro | unchanged (no provider there; see the follow-up) |
| The terminal app | text | raw TeX | unchanged (not in this stage) |

### The design, and why

Option (a) of the brief, with the macros read at request time rather than written at ingest: `learnloop/reader/source_macros.py` reads the revision's stored original (`stored_original_path`, by `asset_hash`), takes the page's text with hidden elements included and scripts and styles left out (entities decoded), parses the definitions (`parse_tex_macros`), and caches the table per stored file (`lru_cache`, keyed by the path and the content hash its name commits to). `reader.render_view` and `reader.side_by_side_section` add it as `mathMacros`, only when the source defines at least one macro: every other reading's reply stays byte for byte what it was (`tests/test_mobile_v4_reader.py::test_render_view_without_a_range_is_todays_reply_byte_for_byte` pins that, and caught the first version, which sent an empty table). On the frontends, `render/mathMacros.tsx` is a React context (`MathMacrosProvider`, `useMathMacros`); `MarkdownMath` passes the table to rehype-katex as KaTeX's `macros` option when one is provided, and keeps its module-level plugin list (rehype-katex with no options) when none is.

Why this design:

- **Nothing stored or hashed changes.** Block text, block `content_hash`, the render view's `content_hash`, spans and the extraction's hashes are what they were (pinned in `tests/test_ux2_source_macros.py`), and nothing sent to a model changes. Option (b), expanding the macros into the stored text, would change every one of them.
- **Capturing the table at ingest would need somewhere to put it.** There is no source-level field for it without a schema change (or a write into a JSON column that feeds an identity), and it would leave already-ingested sources without it. Reading the original the vault already keeps gives new and old sources the same path, with no migration.
- **A provider, not a prop.** `MarkdownMath` has dozens of call sites; the macros belong to whichever source's math a screen shows, which is exactly a subtree (the Reader, the second pane, the phone Reader). The context is in its own module because about forty Reader tests mock `../render/MarkdownMath` with only that export.
- **A copy of the table per rendered value.** KaTeX writes a formula's `\gdef` into the `macros` object it is given; each `MarkdownMath` value gets a fresh copy, so one formula's definition cannot reach the next render or the source's table (tested).
- **The book-math check is untouched.** `pageMathSegments.ts` and `markdownPipeline.ts` (what `sketch-engine/markdown` bundles and `katex_tree.MARKDOWN_SHA256` pins) are not edited. The check still reads a segment without the source's macros, so a segment that uses one stays unreadable there and gets no "checked" label (it fails closed).

**Snippets.** `render/mathSnippet.ts`: `clipMath(text, max)` cuts between formulas (a formula the cut would split is left out, or kept whole when it starts the snippet and fits in twice the room; an unclosed opener before the cut is dropped). `plainMathLine(markdown)` turns a line that is text, never rendered, into readable words: Greek letters and common symbols as characters, `\frac{a}{b}` as a/b, styling commands dropped, an unclosed formula's rest included, and any other command as its bare name. The rendered snippets (the Ask chip) render their math with the book's macros; the plain ones (Today's threads, citation labels) never show a backslash command. A plain line has no macro table, so `\uvec` reads "uvec" there (judgment call 2).

### Sources already in a library

They get their macros the first time they are opened after this change, with nothing to run: the table is read from the stored original, lazily, model-free, and cached for the process. No re-read, no migration. A revision whose original is not in the store (a pre-store revision whose file was never backfilled) opens exactly as before: no `mathMacros` in the reply (tested). Nothing is backfilled from `original_uri` on this read path: it writes into the vault and a local file may have changed since.

### Protected sources: no table at all

The table is read from the whole original, and where each definition sits in the page is not mapped to spans. So a definition in a withheld part (a past paper's solutions, a held-out unit, an exam unit on a marked reading: `\newcommand{\ans}{x = 3}`) would reach a view of any other part, on the desktop and on the phone. `extraction_math_macros` (`learnloop/reader/source_macros.py`, `_anything_protected`) therefore asks the existing predicate, `exam_material(vault, repository)` from `content/sources/exam_material.py` (rules 1 to 4 with the held-out partition: the one `phone_withheld` in `reader/phone_media.py` reads for the phone's reader views and pages), and sends no `mathMacros` when its material covers any reading of the source, or of the same original under another source, wholly or in part (`Material.touched`), or when it raises (unreadable source sets included). Both `reader.render_view` (desktop and phone) and `reader.side_by_side_section` go through it. The predicate is asked only when the original has definitions.

**What a protected source's Reader shows:** its formulas as before this stage, with a source macro as a red raw command (and `\real` as ℜ), in every part, including the parts that are not protected. That is the fail-closed state: nothing of the protected part can reach the screen through the table. Carrying macros for the unprotected parts of a protected source would need each definition's position in the page mapped to the spans it sits in (so a definition inside a protected part is dropped and the others kept); that is not built.

### Safety limits (the page is untrusted)

- Only `\newcommand`, `\renewcommand`, `\providecommand` (starred too) and `\def` are read. `\def` only with plain parameters `#1#2…` in order (a delimited parameter is skipped); `\newcommand` with `[n]`, 0 to 9; one with an optional argument's default (`[n][default]`) is skipped (KaTeX's table cannot say it); a body that uses more parameters than declared is skipped.
- Names are letters only, at most 40 (`MAX_NAME_LENGTH`); at most 256 macros per source (`MAX_MACROS`); a body at most 2,000 characters (`MAX_BODY_LENGTH`), all bodies together at most 64,000 (`MAX_TOTAL_BODY`); an original over 16 MB, a PDF, or anything with a NUL in its first 4 KB is not scanned. An unclosed body stops at the body bound, never scanning the rest of the page.
- A body naming any of `\def \gdef \edef \xdef \let \futurelet \global \long \outer \newcommand \renewcommand \providecommand \input \include \includeonly \InputIfFileExists \openin \openout \read \readline \write \immediate \special \catcode \lccode \uccode \sfcode \mathcode \delcode \csname \endcsname \expandafter \noexpand \afterassignment \href \url \includegraphics \htmlClass \htmlId \htmlStyle \htmlData` is dropped whole.
- Scripts and styles are not read: a definition quoted in a script's string is the script's.
- A body is never expanded or evaluated in Python; it reaches KaTeX only as a string macro. KaTeX's own `maxExpand` (1000) and `trust: false` stay as they are. A recursive macro is an error in the one formula that uses it; a table that expands past the limit fails in that formula, not the page (both tested on the frontend; the parser keeps a recursive body as text and returns at once, tested in Python).

### Model-written text that uses a source's macro

Models read the stored block text, which holds `\vvec`, and may copy it. Today and after:

| Where it shows | Before | After |
|---|---|---|
| In the Reader: tutor answers, quick-check questions and answers, guide questions, Library answers | red raw commands | rendered with the open book's macros |
| Practice and feedback screens, Teacher lessons, the practice exam, the phone's practice | red raw commands | unchanged |

**Follow-up (not in this stage).** Either the practice, feedback and lesson views carry their source's `mathMacros` (a read-side field on those replies, the same helper, no prompt change), or the writing prompts carry the source's definitions so the model writes plain TeX (a prompt change: identity pins move under the playbook). The first keeps every prompt as it is and is the smaller step.

### Found on the way (not fixed: each would change stored text)

- **Display math is mostly dropped at extraction.** The page has 34 `displaymath` elements; the extracted markdown has 3 equation environments (measured with the production `_html_to_markdown`). trafilatura does not keep most of PreTeXt's display math, so "We have" is followed by nothing. A fix changes the extraction and every block hash after it: a separate defect for the ledger.
- **A book that redefines a KaTeX built-in.** `\real` is ℝ in this book and ℜ to KaTeX. The book-math check reads segments without the source's macros, so for an allowlisted command a book redefined, the page and the check could read different symbols. No such case is known (`\real` is not in the check's allowlist, so its segments are unreadable there); a guard would be the check refusing a segment that uses a name in the source's table. Noted for whoever next touches `figures/book_math.py`.

## UX-8: the goal report on an empty goal

**What the learner saw** (student-1 #128; beginner-1 #84, `beginner-1-0084-empty-goal-report.png`). Under the goal card's *details*: "BEHIND", "0 certified · 0 examined · 0 untouched", "0 attempts · 0/0 facets examined · 0 certified", "all facets certified — hold the line until the due date." (beginner-1's goal is open-ended), and "practice at-risk facets ↵", which answered "Nothing for this goal is ready to practise yet."

**Where it is composed.** In the desktop, not the sidecar: `components/GoalBanner.tsx`. `buildPaceSentence` says "all facets certified — hold the line until the due date." whenever `attemptsRemaining === 0`, which a goal with nothing in scope (`total` 0) also has; `statusOf(attainment)` says BEHIND for a null attainment. The phone and the terminal app show no goal report.

**What it says now.** `emptyGoalSentence(goal)` picks the state from the report the banner already has; nothing computed or stored changes. A goal is "not yet checked" when the report has the dual-axis counts and `examinedCount` and `certifiedCount` are both 0. In that state the standing reads NOT STARTED (neutral colour), the all-zero coverage and count rows (which say "certified" and "facets") are not shown, the sentence below replaces the pace sentence, and the practice action is offered only when there is something to practise. The pace sentence used for the forecast claim (`claimText`) is still computed as before and is only presented when there is remaining work to project, which this state never has.

| State | The data that tells it | The sentence | The action offered |
|---|---|---|---|
| No answers, no due date, nothing from the books in the goal (beginner-1 #84) | `examinedCount` 0, `certifiedCount` 0, `pace.attemptsLogged` 0, `total` 0, `dueAt` null | Nothing has been checked for this goal yet. None of the topics in your books is part of it so far: add or read a book that covers it, and its questions will count here. | none (nothing to practise); "+ new goal" stays |
| No answers, a due date (student-1 #128) | as above with `dueAt` 22 days ahead | the same, then "It is due in 22 days." ("It is due today." / "tomorrow." / "Its due date passed N days ago.") | none when `total` is 0 |
| Topics in the goal, no answers yet | `total` > 0, `attemptsLogged` 0 | Nothing has been checked for this goal yet. Answer its questions on your own and this report will start to fill in. (plus the date sentence) | **practise for this goal ↵** (the same `onPracticeAtRisk`) when `practicableItemCount` is above 0 or unknown |
| Answers, but nothing checked | `attemptsLogged` > 0 (3 here), `examinedCount` 0 | You have answered 3 questions, but none has checked this goal's topics yet. This goal's questions, answered on your own, are what count here. (plus the date sentence; with `total` 0, the "None of the topics in your books…" sentence instead) | as the row above |
| Everything examined and certified (unchanged) | `examinedCount` = `certifiedCount` = `total` > 0, `attemptsRemaining` 0 | all facets certified — hold the line until the due date. | practice at-risk facets ↵ |
| Anything checked, or an older sidecar without `examinedCount` | otherwise | unchanged | unchanged |

The new words avoid "facet" and "certified" (the deny-list's plain words are topic and "on your own"); each new sentence passes `findJargon` in the test. The rest of the banner (the at-risk list's "facets need work", the forecast link, the exam line, the unchanged certified sentence) keeps its words: stage 8's jargon sweep extends the deny-list to the goal report.

## Judgment calls

1. **Read at request time, not captured at ingest.** The brief's option (a) says "captured at ingest as source-level data". There is no place for it without a schema change, and the original the vault already keeps holds it; reading it lazily serves old and new sources alike. If the owner wants the table stored, it is one helper call at ingest plus a column (a migration).
2. **A plain snippet names a macro it cannot render.** Today's thread lines and citation labels are text with no macro table, so `\uvec` reads "uvec". Rendering them would need the cited source's table on Today (a field on `list_question_queue`'s citation, or a sidecar-written plain label, which changes `passage_label` and what the tutor prompt carries). The brief allows clean text; this is the smallest step.
3. **The whole Reader is under the book's macros,** model text included (tutor answers, quick checks). A Library answer quoting another book is drawn with the open book's table; a passage of another book that redefines one of its names would show the open book's meaning. The side-by-side pane, which shows another book's text, has its own table.
4. **UX-8: NOT STARTED with a date too.** The brief requires no BEHIND without a date. With a date and nothing checked, the attainment is unknown ("predicted recall —"), not low, so BEHIND is replaced there as well and the sentence says how long is left.
5. **UX-8: "practise for this goal ↵" in place of "practice at-risk facets ↵"** when topics and questions exist but nothing is checked: the same action, without "at-risk" (which claims a check) or "facets". Hidden when there are no topics, or the goal's practicable count is 0.
6. **UX-8: the all-zero coverage rows are hidden in the empty state,** because they say "certified" and "facets" and carry nothing the sentence does not.

## Tests, each written first and seen failing

| Test | Fail-first evidence (before the fix) | After |
|---|---|---|
| `apps/learnloop-tauri/src/components/GoalBanner.emptyGoal.test.tsx` (5 tests, UX-8) | 5 failed: "expected '…' not to match /hold the line/" (no answers, both date cases), "not to match /certified/i" (topics in scope; answers but nothing checked), "Unable to find an element by: [data-testid="goal-status"]" (the unchanged certified state: its only failure is the new test id) | 5 passed |
| `tests/test_ux2_source_macros.py::test_ux2_the_sample_is_stored_as_before_and_its_reading_carries_the_pages_macros` | `KeyError: 'mathMacros'` after its pins of the stored blocks passed | passed |
| `tests/test_ux2_source_macros.py::test_ux2_a_source_added_before_reads_its_macros_from_the_stored_original_without_a_new_reading` | `KeyError: 'mathMacros'` | passed |
| `tests/test_ux2_source_macros.py::test_ux2_the_second_pane_gets_its_own_books_macros` | `KeyError: 'mathMacros'` (handler at its stage-start version) | passed (now on a book with no held-out unit) |
| `tests/test_ux2_macros_protection.py::test_ux2_a_source_with_a_held_out_part_sends_no_macros_with_any_view` (desktop whole reading and section u1, phone section u1, original defines `\ans` = "x = 3") | before `09dae4d917`: "AssertionError: {'extractionId': 'ext1'} / assert 'mathMacros' not in {…}" | passed |
| `tests/test_ux2_macros_protection.py::test_ux2_an_unreadable_protection_predicate_sends_no_macros` | "AttributeError: … source_macros … has no attribute 'exam_material'" (the predicate was not asked) | passed |
| `tests/test_ux2_macros_protection.py::test_ux2_the_second_pane_of_a_book_with_a_held_out_unit_gets_no_macros` | "assert 'mathMacros' not in {'blocks': …, 'extractionId': 'ext_lay', …}" | passed |
| `tests/test_ux2_macros_protection.py::test_ux2_an_unprotected_source_sends_its_macros_on_the_desktop_and_the_phone` | passed before and after (the control) | passed |
| `tests/test_ux2_source_macros.py` parser tests (`only_plain_definitions_are_read`, 11 cases of `a_body_that_could_define_include_or_reach_out_is_dropped`, `a_recursive_macro_is_kept_as_text…`, `an_oversized_table_is_cut_at_the_bounds`, `scripts_and_binaries_give_no_macros`) | collection error: `ModuleNotFoundError: No module named 'learnloop.reader.source_macros'` (run with the module moved aside) | passed (17 + 1 in the file) |
| `apps/learnloop-tauri/src/render/sourceMacros.test.tsx` (9 tests: the renderer with the book's macros, `\amp`, no macros unchanged, a recursive macro, a table past `maxExpand`, `\gdef` isolation, the clipped chip, the plain line, Today's thread) | first: "Cannot find module './mathSnippet'"; then, with the snippet module and before `MarkdownMath` and `todayPlan.ts` were changed, 7 failed: "expected '<p>Let <span class="katex">…' not to match /katex-error\|mathcolor="#cc0000"/", "Target cannot be null or undefined" (no error span for the recursive and the expanding table: the macros were not passed), the thread line "Received: Suppose that \(\uvec\) is an eigenvector of \(B\) with asso…" | 9 passed |
| `apps/learnloop-tauri/src/screens/ReaderScreen.sourceMacros.test.tsx` (2 tests: the real Reader screen with the real renderer) | with `ReaderScreen.tsx` at its stage-start version: "expected '<div style=…' not to match /katex-error\|mathcolor="#cc0000"/"; the older-sidecar case passed (it pins the old behaviour) | 2 passed |
| `apps/learnloop-mobile/src/read/sourceMacros.test.tsx` (2 tests: the phone Reader through the fake host) | with the phone's `ReaderScreen.tsx` at its stage-start version: "expected '<div class="block" data-span="b0">…' not to match /katex-error\|mathcolor="#cc0000"/"; the older-reply case passed | 2 passed |

The Python pins were taken from the production path (`add_source` of the sample, `html` extraction, stored blocks, `reader.render_view`) before any backend change: 59 blocks, sha256 over the blocks' "span id, content hash" lines `f03ceb9f…69202`, block `s5`'s content hash `sha256:57f99b7f…6b09d`, the render view's `contentHash` `sha256:4d153455…fcbd`, extractor `html` version 2. The extraction run's request and result hashes key on the revision's id, which is new at each import, so they are not pinned (a first draft pinned them and failed on that, before any change).

## Pins and goldens

No identity pin or golden moved: `tests/test_identity_pins.py`, `tests/test_cli_help_snapshot.py` and `tests/test_effective_defaults_golden.py` pass unchanged (results below). The phone's request contract (`apps/learnloop-mobile/contract/reader.render_view.json`) is unchanged: `mathMacros` is optional, read when present, and the contract lists only the fields the phone needs on every reply.

Snapshots that did move, deliberately (`e15d8bc5ee`): six "switched off, byte-identical to the base" Reader snapshots (`intentSwitchOff`, `libraryAskSwitchOff`, `readingPathsSwitchOff`, `recapSwitchOff`, `tutorSwitchOff`, `workbench/switchOff`; 18 snapshot entries). In every changed line the only differences are the Ask chip's clip, from `eigenvectors $(1,1)/\s…` (cut inside a formula) to `eigenvectors…`, and, in `tutorSwitchOff`, the FOLLOW-UP TO passage now rendered through `MarkdownMath` in a `div` instead of plain text in a `span` (checked line by line).

## What was run

Every Python run: `systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=1G <wrapper> uv run --no-sync pytest -q -n 1 -p no:cacheprovider <files>`; node in a 5G scope with `--maxWorkers=4`.

| Command | Result |
|---|---|
| `pytest tests/test_ux2_source_macros.py tests/test_mobile_v4_reader.py` (final code) | 38 passed |
| `scripts/affected_tests.py --files src/learnloop/reader/source_macros.py src/learnloop_sidecar/handlers/reader.py src/learnloop_sidecar/handlers/side_by_side.py` | 585 files: over 150, so the 138 whose names contain extract, ingest, html, source, block, reader, goal, report or deliverable were run, in four chunks of at most 40 |
| chunk 1 (first run) | 1 failed, 766 passed, 1 skipped: `test_mobile_v4_reader.py::test_render_view_without_a_range_is_todays_reply_byte_for_byte` (the empty `mathMacros`; fixed in `da7a7683f5`) |
| chunks 2, 3, 4 | 806 passed; 598 passed; 218 passed |
| chunk 1 again, after `da7a7683f5` | 767 passed, 1 skipped |
| the 8 files of chunks 2 to 4 that call `render_view` or `side_by_side_section`, again after `da7a7683f5` | 138 passed |
| `tests/test_identity_pins.py` | 342 passed |
| `tests/test_cli_help_snapshot.py` | 26 passed |
| `tests/test_effective_defaults_golden.py` | 3 passed |
| `tests/test_structure_ratchets.py` | 3 passed |
| `tests/test_test_layout.py` (alone) | 3 passed |
| `tests/test_architecture.py` (alone) | 18 passed |
| `ruff check` | All checks passed! |
| `lint-imports --no-cache` | Contracts: 43 kept, 0 broken. |
| desktop `npm run typecheck` / phone `npm run typecheck` | exit 0 / exit 0 |
| desktop `npx vitest run --maxWorkers=4` | 294 files, 2973 tests passed (first run: 12 failed in the six switch-off snapshot files, updated in `e15d8bc5ee`) |
| phone `npx vitest run --maxWorkers=4` | 33 files, 373 tests passed |
| desktop `npm run frontend:build` | built (exit 0) |

After `09dae4d917` (the protection gate; Python only, no frontend change):

| Command | Result |
|---|---|
| `pytest tests/test_ux2_macros_protection.py tests/test_ux2_source_macros.py` before the gate | 3 failed, 19 passed |
| the same after the gate | 22 passed |
| `pytest tests/test_ux2_macros_protection.py tests/test_ux2_source_macros.py tests/test_mobile_v4_reader.py` | 42 passed |
| `pytest` the render_view and side-by-side files (`test_reader_ca6_side_by_side`, `test_reader_pdf_selection`, `test_reader_source_identity_guard`, `test_rw5c_block_policy`, `test_sidecar_reader`, `test_sidecar_reader_p3`, `test_sidecar_reader_p3_slice2`, `test_sidecar_reader_pdf_view`) | 138 passed |
| `tests/test_identity_pins.py` | 342 passed |
| `ruff check` | All checks passed! |
| `lint-imports --no-cache` | Contracts: 43 kept, 0 broken. |

## What a re-walk should check

- **student-1 #18 to #132 (desktop, the sample as a web page).** Open the chapter in the Reader: `\vvec`, `\uvec`, `\xvec` bold, `\real^n` as ℝⁿ, `\twovec` and the `\amp` matrices drawn, no red commands. Select "Suppose that u is an eigenvector of B…" and press ask: the ASKING ABOUT chip shows rendered math and never "(\lambda = \…".
- **student-1 #147 (Today).** "Pick up a thread" shows the passage without `\(`; expect "Suppose that uvec is an eigenvector of B with asso…" (judgment call 2).
- **student-1 #128 and beginner-1 #84 (goal details).** NOT STARTED, no BEHIND, no "certified", one plain sentence, no "practice at-risk facets"; student-1's says "It is due in N days."
- **retainer-1 #19 and #61.** The Reader's math as above; the side-by-side pane, if opened on another book, uses that book's notation.
- **phone-2 #37.** The phone Reader's section of the sample draws the same symbols with no red commands. The phone must be served by a desktop with this branch (an older sidecar sends no `mathMacros`; the phone then renders as before).
- **A source with an exam or held-out part** (student-1's past paper, if it defines macros): its formulas still show raw source commands in every part, by design ("Protected sources" above).
- **Any persona that practises from the sample.** Questions or feedback that copy `\vvec` still show it red outside the Reader (the follow-up).

## Not verified here

- No app, browser, host or walk was run: the screens were checked through vitest (jsdom) and the sidecar through its handlers.
- The phone through the real host (`learnloop_mobile`): the field is added by the same handler the host calls, and the phone's test uses the fake host.
- A source in a real owner vault, and HTML from sources other than PreTeXt (MathJax configurations with `tex.macros` are not read; a page defining macros only there gets none).
- The cost of the first open of a very large HTML original (the scan is linear and cached; not measured beyond the sample, where the whole Python test file runs in about 6 s).
