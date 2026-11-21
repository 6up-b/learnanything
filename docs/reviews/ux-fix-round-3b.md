# UX fixes: broken controls, third round (group B)

The defects the third wave of persona walks found in the Reader and the Library (`ux-journey-audit-3.md` §5.1, §5.3, F45, F47), and four wording rows. Ledger ids UX-50, UX-51, UX-54 to UX-57, and UX-30, UX-32, UX-44c, UX-52b (`refactor-bug-ledger.md`, "From the UX journey audit's walks"). Group A (Today, practice, the session end) is `ux-fix-round-3a.md`. Branch `ux/broken-controls-3b` from group A's tip (main `91ca1ea28d` plus the audit's third part and group A), one commit per defect; the wording rows one commit per screen. Desktop unless said; the phone for UX-52b and wherever it says the same line through shared code. Three small sidecar changes, each said under its defect (UX-54, UX-57, and the card's words for UX-30).

| Defect | Sev | Commit | What |
|---|---|---|---|
| UX-50 | S2 | `5eb451a556` | Words written in the Notes box after a highlight are saved on it ("save note", or leaving the box) |
| UX-51 | S3 | `2ac0c28678` | Words typed only to find an action are not kept as a highlight's note; the list says which |
| UX-56 | S3 | `e4fb678dd3` | Ask's source chips name a section in words, a one-section reading by its title |
| UX-55 | S3 | `3c43285492` | A control scrolled into the rail lands clear of the rail's sticky tab bar |
| UX-57 | S3 | `c0a3fb55c3`, `48155752eb` | The same file added from another place opens the book already there (sidecar: a content-hash lookup); the second commit fixes a test whose "second book" was the first book's bytes |
| UX-54 | S3 | `a373728294` | A book whose getting ready waits behind another's work says which (sidecar: a fact on the status line) |
| UX-44c | words | `a961fb8482` | The full list says when a waiting question comes back; a done plan counts only what can be asked |
| UX-52b | words | `8482d9a942` | The phone's Today says no "Nothing planned" above a book's questions offered |
| UX-30, UX-32 | words | `bb9efa49e6` | The book card says what its build does (sidecar words), and its details name the whole-book press for what it does |

This record and the ledger cells are the last commit. No new non-test TypeScript file: `desktop_validate.py`'s counts do not move.

## UX-50 (S2): a note typed after "note" is never saved

**What the person saw** (retainer-3 #24-28, #69-70). After "note" from the selection box's list, the Notes rail showed "✓ saved · choose another action or select another passage" above an empty note box; the person typed their thought there ("Equal counts do not mean equal chances…") and moved on, unsure it was kept ("saved was showing before I typed"). The vault's third highlight has no note.

**Cause.** `screens/reader/NotesRail.tsx`: the note box's only sender is the "highlight" button (`captureHighlight`, `ReaderScreen.tsx`), which is disabled and reads "highlighted ✓" once the selection's actions hold "highlight"; "✓ saved" shows whenever the selection has any action, whatever is in the box. The "note" action (`reader_intent.py`: effect `highlight` with `note: true`) with no words in the selection box makes a highlight with an empty note, so after it nothing could send the box.

**What they see now.** Once the selection is highlighted (from the rail's button, the box's "highlight" or "note", Enter's routing):
- the box's placeholder reads **"add a note to this highlight…"** (or **"add to your note on this highlight…"** once it has one);
- with words in the box, the button reads **save note**, and **"✓ saved"** is not shown; leaving the box (blur) with words in it saves them the same way;
- once saved, the box empties, the card shows **your note: “…”** and "✓ saved · choose another action or select another passage" again; more words are added to the note (a blank line between), never replacing it.

The save is the existing note edit (`reader.edit_annotation`, the path the Notes list's "edit" uses) on the highlight this selection made; offline (the labelled demo) it updates the local highlight, as the offline capture does. Before the passage is highlighted nothing changed: the words go with "highlight" as before. After a mark that is not a highlight ("mark confusing"), "✓ saved" hides while the box has words, and "highlight" still sends them. A second save while one is on its way is refused (a ref), so blur followed by a click on "save note" saves once. What a highlight or a note is and how it is stored are unchanged.

**Test** (`screens/reader/highlightNote.test.tsx`, new; the real Reader on fake RPCs), fail first: 4 failed, 1 passed (its plain-words control):
- `after 'note' from the box's list: the words typed in the Notes box are saved by 'save note', and 'saved' never shows above unsaved words` (failed: `expected <span …> to be null`, the "✓ saved" line above the typed words);
- `leaving the box with words in it saves them, once` (failed: `expected "spy" to be called 1 times, but got 0 times`, no edit sent);
- `a note written before highlighting goes with the highlight as before; more words later are added to it` (failed: `Unable to find an element with the text: your note: “first thought”`);
- `after a mark that is not a highlight, words in the box are not called saved: 'highlight' still sends them` (failed as the first).

## UX-51 (S3): words typed to find an action become the note

**What the person saw** (retainer-3 #15-20). With the list open (Tab), the person typed "highlight" into the box ("Maybe typing highlight will narrow the choices") and clicked "highlight"; the highlight was saved with the note "highlight".

**Cause.** `screens/reader/useIntentBox.ts` `pick` hands the box's words to the action, and `ReaderScreen.tsx` `runIntentIn` passes them to `captureHighlight(text, …)` (and `invokePreset`) as the learner's note. The list does not filter by the words (it never did; not changed here).

**How the box tells them apart now.** For a highlight, a note or a mark (the list's actions no model reads: `model: false`), the words are kept as the note unless they **only name an action**: the start of an action's or a group's name in the list ("highl", "highlight", "note", "Mark", "confusing", trailing punctuation ignored), or a whole name followed by "this", "it" or "that" ("highlight this"). Anything more ("the gaps matter", "highlight because the gaps matter") is the note, as before. The same rule holds for the list's pick and for Enter's routing. Actions a model reads keep the words exactly as before (nothing sent to a model changes). `intentPalette.ts` `onlyNamesAnAction`.

**What the screen says.** While the list is open with words in the box, under it: **“highlight” only finds an action: it isn't kept as a note.**, or **A highlight or a note keeps your words as its note.** The box's "ⓘ where this goes" now reads: "Used to pick the action you meant. If it becomes a question or a note, it's kept like one; an action's name typed only to find it is not kept."

**Tests** (`screens/reader/intentNoteWords.test.tsx`, new), fail first (as first written in one file with UX-50's, then split into its own before the commit; the same test bodies): 4 failed, 1 passed (plain words):
- `typing 'highlight' and picking highlight from the list saves no note, and the list says why` (failed: `Unable to find an element with the text: “highlight” only finds an action: it isn't kept as a note.`);
- `the start of an action's name, or the name with 'this', is not a note either; the Enter route keeps the same rule` (failed: `expected { … } to match object { learnerText: '' }`: "Highlight this" was the note);
- `words that are more than an action's name are the note, as before` (failed on the list's new line; its `learnerText` part is a control);
- `the rule, on the palette's own names` (failed: `onlyNamesAnAction is not a function`).

**Snapshot moved, deliberately:** `screens/reader/__snapshots__/libraryAskSwitchOff.test.tsx.snap`, one entry ("reader after a selection and Tab"): only the "where this goes" tooltip's text (`title`) changed, checked word by word.

## UX-56 (S3): Ask's source chips show a slug or "root"

**What the person saw** (retainer-3 #46). "§ source: Wikipedia Elevator Paradox · modeling-the-elevator-problem" and "§ source: Understanding Linear Algebra Symmetric Matrices And Variance · root".

**Cause.** A cited passage's label is built in the sidecar as "<title> · <section>" (`source_retrieval/reader_tutor.py` `_span`, `source_retrieval/tutor.py` `span_context`), the section being the reading's unit label: a web page's slug, or "root" for a reading that is one section. It is what the tutor is given. `screens/reader/ReaderAskBranches.tsx` printed it as it came (UX-24's `sectionWords` covered Contents, the path and side by side, not the chips).

**What they see now.** `readerShared.ts` `citationWords(label)`: the part after the last " · " goes through `sectionWords` ("Modeling the elevator problem", "(intro)" as "Introduction"); "root" (or an empty section) is dropped, so the chip names the reading by its title: "§ source: Wikipedia Elevator Paradox · Modeling the elevator problem", "§ source: Understanding Linear Algebra Symmetric Matrices And Variance". A book's own section names ("Axler · 5.C Eigenspaces") are unchanged. Applied to the same labels in the Reader's Ask chips (all three branches), the library answer's "cites:" line (`LibraryAnswer.tsx`) and the practice Ask panel's chips (`components/AskOverlay.tsx`), which print the same field. The label sent to the tutor and stored is unchanged.

**Tests** (`screens/reader/citationWords.test.tsx`, new), fail first: both failed (`Unable to find an accessible element with the role "button" and name "source: Wikipedia Elevator Paradox · Modeling the elevator problem"`; `citationWords is not a function`).

## UX-55 (S3): the first click on a control just scrolled into the rail lands on something covering it

**What the person saw.** student-3 #72-74 and expert-2 #33-35: after "ask follow-up", typing into the follow-up box failed ("Something else is covering that spot"); the second try worked. firstq-2 #28-33: "Done with this section" could not be clicked twice, then worked after scrolling the rail up.

**Cause, from the layout code and the walks' screenshots.** The rail (`ReaderScreen.tsx`, the `ll-scroll` box with `padding: 18px 20px`) has a sticky tab bar as its first child (`position: sticky; top: -18px`, about 52 px tall), stuck over the rail's first ~52 px. `components/scrollWithin.ts` `scrollIntoViewWithin` placed a target's top at the scroller's top edge for `block: "start"`, and for `"nearest"` when the target was above the view: exactly under the bar. Ask's follow-up composer sits above the thread the learner scrolled to, so `AskRail.tsx`'s `scrollIntoViewWithin(composer, { block: "nearest" })` put it under the tabs: expert-2's step-34 screenshot shows only the composer's lower edge below the tab bar. The harness's WebDriver click does not scroll an element whose centre is already inside the window, so it hit the bar.

**What changed.** `scrollIntoViewWithin` measures the scroller's own sticky children (a sticky child's offset counts from inside the scroller's padding: cover = padding + `top` + height; likewise `bottom`) and places the target in the part they leave clear: `start` below the top bar, `end` above a bottom bar, `center` centred in the clear part, `nearest` treating a target under a bar as out of view. A sticky child that holds the target covers nothing of it. Every Reader caller gets it (the rail's Ask, Guide quick-check card and path card; the reading pane, whose side-by-side header and undo/PDF-offer bars are sticky too).

**What jsdom could and could not show.** jsdom lays nothing out: the tests place the rail, its bar and the composer by hand, reading the rail's real styles (its 18 px padding, the bar's `top: -18px`) from the rendered Reader. Reproduced: the follow-up composer brought into view landed at the rail's top (200) under the bar (to 252). Not reproducible in jsdom: whether the click reaches the control (no hit-testing); the firstq-2 "Done with this section" case, which no code scrolled (the person had scrolled the rail down to the quick check, leaving Done just above the clear part, under the bar; its screenshot shows no Done on screen, so a person would scroll up for it; the harness's click found it under the bar). Part 2's student-2 #70 and project-1 #41 were not re-read.

**Tests**, fail first with `scrollWithin.ts` at its base version: 5 failed, 8 passed:
- `components/scrollWithin.test.ts` (5 added): `start and nearest put a target clear of a sticky bar at the scroller's top, never under it`, `nearest moves a target that is in the scroller's view but under its sticky bar`, `center centres the target in the part of the scroller the bar leaves clear`, `end and nearest keep a target above a sticky bar at the scroller's bottom` (each failed: the scroll put the target at the edge, `expected [] to have a length of 1` for the one under the bar), `a target inside the sticky bar itself is not pushed below it` (control, passed on both).
- `screens/reader/railStickyClear.test.tsx` (new): `ask follow-up brings the follow-up box below the rail's tab bar, where a click reaches it (student-3 #73, expert-2 #34)` (failed: `expected 200 to be greater than or equal to 252`).

## UX-57 (S3): the same file from another place becomes a silent second copy

**What the person saw** (retainer-3 #6, #48). Adding an article already in the library, from another folder, made a second card; Today then asked an OK for "… and 2 more".

**Cause.** `content/pipeline/add_source.py` `add_source` answers `existing` ("Already in your library — opened where you left off.") only when `source_artifact_by_uri(category, path)` finds the same path; `register_source_revision` keys a source by its canonical path, so other bytes-identical paths made a new source.

**The sidecar change (the smallest that recognises it).** For a local file, before registering, `add_source` hashes the bytes with the hash the sources already carry (`ingest.hashing.asset_hash`, stored as `source_revisions.asset_hash`, indexed) and looks for a source with a revision of that hash through a new store read, `source_revisions_by_asset_hash` (`db/stores/source_documents.py`, oldest first). The first such source that has a reading or an import on its way (the same condition the same-path answer uses) is answered exactly as the same path is: `status: "existing"`, its id, current revision and title, the same message, nothing registered or queued. No schema change, nothing merged, deleted or written. A link (fetched later, bytes unknown at Add) is not covered.

**Where a library already holds two copies.** Both stay as they are, with their cards and their own progress; adding the file again from a third place opens the first-added copy, with "Already in your library — opened where you left off."; nothing tells the learner the two cards are one file (a merge would move progress and notes: not done here).

**Tests** (`tests/test_add_source_same_content.py`, new), fail first: 3 failed, 1 passed: `test_the_same_file_from_another_folder_opens_the_book_already_there`, `test_the_same_file_under_another_name_is_recognised_too`, `test_two_copies_already_in_the_library_stay_and_a_third_add_opens_the_first` (each: `assert ('added', …, None) == ('existing', …, 'Already in your library — opened where you left off.')`); `test_a_different_file_is_still_a_new_book` is the control.

**Inputs changed, assertions not:** two existing tests added the same bytes under two names to get two books, which is now one book: `tests/test_ux_phase1_add_source.py` `test_several_files_become_several_books_and_the_first_opens` (its second file gets its own text, in `c0a3fb55c3`) and `tests/test_first_questions_today.py` `test_the_duration_is_this_librarys_own_measured_one` (found by the wider run; its second book gets a closing line of its own and `_book` a `text` argument, in `48155752eb`).

## UX-54 (S3): a second source waits silently behind another book's build

**What the person saw** (student-3 #27, #92; the vault: the past exam's import `queued` from 1:09 to the walk's end). The past exam's card said "◐ Getting this PDF ready" for seven and a half minutes; its import is about a second's work.

**Cause.** `db/stores/ingest_queue.py` `claim_next_ingest_job` runs one job at a time (no claim while any job is `running` with a live heartbeat, unless the caller names compatible types), ordered by batch priority, then batch age; the chapter's build (an older batch) keeps the worker, and the exam's import stays `queued`. The card's line (`add_source.py` `_source_status_line`) said "Getting this PDF ready" for a queued import as for a running one.

**The sidecar change (the smallest fact).** `_waiting_turn_line`: while a source's latest import is `queued` and a job of another batch is `running`, the card's line is **Waiting its turn behind “<that book's title>”** (tone `working`, no action) and carries `waiting_behind: "<title>"` (`waitingBehind` on the card, `SourceStatusLineDto`). The title is the running job's source's learner title (`payload.source_id`, its result's, or `auto_build.source_id`); with no source to name (nothing running, or a job with no book), the line is unchanged. The same holds for a link still being fetched (the shelf's pending line). The key is present only then, so every other line keeps its bytes. Read-only: `active_ingest_jobs` (existing). The queue's order and concurrency are unchanged.

**Today** (`app/todayCause.ts`): the `on_the_way` cause gains `behind` (the book Today names waits) and `queued` (books waiting behind the one Today names):
- the waiting book named: **“Past Exam” is waiting its turn behind “Symmetric Matrices and Variance”. LearnLoop gets one book ready at a time. Keep reading meanwhile.**
- the book at work named: "Getting “Symmetric Matrices and Variance” ready for questions · 1 of 2 steps done. **“Past Exam” is waiting its turn behind it.** Questions come as you finish sections. Keep reading meanwhile." (two: "“A” and “B” are waiting their turn behind it.")
The phone says the same through the shared `causeSentence`.

**What letting a cheap import go ahead would take** (not done, as the brief rules): the import is the vault-writing lane's job like the build's model steps, so it cannot simply run beside them. Either the claim lets a short, write-light job type (the import, the planner) be claimed while a model step is in its call (`compatible_running_job_types` exists for this shape, but the model steps write the vault on landing, so the writes would need the same lease discipline), or a model step gives the lane up while it waits on the model and re-claims to land (a job state between `running` and `queued`). Either changes the queue's single-writer lease (one vault-writing job at a time); it is the ledger row's stage 2.

**Tests:**
- `tests/test_status_line_waiting_turn.py` (new), fail first: 2 failed, 1 passed: `test_an_import_queued_behind_another_books_running_work_names_that_book` (failed: `assert 'Getting this PDF ready' == 'Waiting its turn behind “Symmetric Matrices”'`), `test_a_link_still_being_fetched_names_the_book_it_waits_behind` (failed: `'Getting this article ready'`); `test_nothing_else_running_keeps_the_line_as_it_was` is the control (the line's exact dict).
- `screens/today/TodayPlace.test.tsx` › "a book whose getting ready waits its turn behind another's says so (UX-54)", fail first: 2 failed, 1 passed (`Unable to find an element with the text: “Past Exam” is waiting its turn behind “Symmetric Matrices and Variance”`; `expected '◐ Getting “Symmetric Matrices and Var…' to contain '“Past Exam” is waiting its turn behin…'`; "no book waiting: the line is as it was" the control).

## UX-44c (words): "coming back later today" for every waiting question, and "more for today" counting them

**What the person saw** (firstq-9 #85). "All six questions are coming back later today, even the ones I got right"; a done plan said "The plan stopped here, but there's more for today if you'd like it." over rows only waiting to come back.

**Cause.** `app/todayPlan.ts` `fullListWhy` said "coming back later today" for every row whose `dueStatus` is `later`, with no due time (never answered) or one days on (answered right); `TodayPlace.tsx` `moreLeft` counted every row on the list.

**What they see now.** The full list's "why" for a later row, from its own due time: **not answered yet** (no due time), **coming back later today** (later the same day), **comes back tomorrow**, **comes back in N days** (by calendar day), and "time to bring it back" once the time has passed. A done plan says "there's more for today" (and offers "Open today's list") only for rows that can be asked now: the list's rows less those waiting to come back (`waitingOnList`, the rule Today's offer already uses); with only waiting rows it says "Nothing else is needed today."

**Tests**, fail first: 5 failed, 1 passed:
- `app/todayPlan.test.ts` › "the full list's words for a question that waits (UX-44c)": 3 tests (failed: `expected 'coming back later today' to be 'not answered yet'`, `… 'comes back tomorrow'`, `… 'time to bring it back'`).
- `screens/today/TodayPlace.test.tsx` › "the full list's words and a done plan's count tell waiting rows apart (UX-44c)": `a done plan whose list holds only questions waiting to come back does not say there's more for today (firstq-9 #85)` (failed: `Unable to find an element by: [data-testid="today-finished"]`), `the full list says when an answered question comes back, and a question never answered as one` (failed: `expected 'Topic 1coming back later today' to match /comes back in 9 days/`); `a question never answered still counts as more for today…` the control.

**Assertion changed:** `app/todayPlan.test.ts` › "says why in a few words…": `fullListWhy(item({ dueStatus: "later" }))` (no due time) expected "coming back later today"; it now expects "not answered yet". That assertion pinned the defect's words.

## UX-52b (words): the phone's "Nothing planned for today." above an offer

**Cause.** `apps/learnloop-mobile/src/today/PlanToday.tsx` has its own heading: "Nothing planned for today." whenever the empty day has a cause line, including the shared offer "3 questions from … are ready."

**What they see now.** As on the desktop (group A's UX-52): while the cause offers a book's questions (`questions_ready`, `questions_ready_with_section_work`), the finished empty day shows no heading, only the offer's sentence; an open plan with nothing in it says no "Nothing planned for today." either. Every other heading is unchanged (the writing line keeps "Nothing planned for today."). The phone's one action stays Keep going.

**Tests** (`apps/learnloop-mobile/src/today/Today.plan.test.tsx` › "the phone's own Today heading agrees with the desktop (UX-52b)…"), fail first: 3 failed (`expected 'Nothing planned for today.' not to match /Nothing planned/`, twice, and the open plan's), 1 control passed ("nothing offered (the writing line): the heading stays").

## UX-30, UX-32 (words): the card promised question writing its build does not do

**What the person saw.** UX-30: "◐ Writing questions for this article" for the whole of student-3's build (#92), which writes topics and question plans and no question to practise; after the section's questions were written and answered, "Questions for this article come up as you read" (firstq-10 #84). UX-32: "Build questions for the whole article at once" (firstq-1 #52-54, firstq-8 #58), which writes no question either.

**Cause.** The card's line is the sidecar's (`add_source.py` `_source_status_line`); the details' label is the desktop's (`components/BookCard.tsx`).

**The sidecar change (words only).** The card's lines now say what happens:

| State | Before | Now |
|---|---|---|
| a build under way | Writing questions for Ch. 1–2 | **Getting Ch. 1–2 ready for questions** (what Today says) |
| a build under way, a measured time | Questions for Ch. 1–2 in about 5 min | **Getting Ch. 1–2 ready for questions in about 5 min** |
| built | Questions for Ch. 1–2 come up as you read | **Questions for Ch. 1–2 are written as you finish sections** |
| built, no AI | … come up as you read once an AI is connected | **… are written as you finish sections once an AI is connected** |

And the details' press: **Get the whole article ready for questions at once** (book, paper, PDF: its noun). What it does is unchanged; when nothing is left its notice is UX-31's ("All of this article is ready for questions. Each section's questions are written when you finish it."), and when it starts a build the card's line now says "Getting … ready for questions", so no notice was added. The CLI's `sources build-preview --whole-book` help names it the same way (`tests/cli_surface.json` carries no help text). Nothing else changes: no fact, key, action or behaviour.

**Tests and assertions changed.** The tests that assert these words now assert the new ones (18 Python assertions in `test_apply_recovery.py`, `test_first_questions_today.py`, `test_section_done_before_build.py`, `test_ux_phase1_add_source.py`, `test_ux_phase1_usability_round1.py`, `test_ux_phase1_usability_round2.py`, `test_ux_phase1_review_fixes.py`, `test_ux_phase1_auto_build.py`; one of them, `test_f3_rereview_a_link_planner_that_dies_after_queuing_its_build_is_found`, checked `startswith("Writing questions for")` and now checks that the line starts "Getting " and says " ready for questions", since its phrase is a link's title). Edited first, they failed on the base: **15 failed, 151 passed** (8 files). The press's label: `components/BookShelf.test.tsx` (2) and `screens/LibraryPlace.wholeBook.test.tsx` (2) query the new label (failed first: 4 failed, `Unable to find … name "Get the whole article ready for questions at once"`); their fixtures' line texts, and the deny-list's list of every card line, carry the new words. Other desktop and phone fixtures that echo an old line text as data (`FeedbackScreen.plan.test.tsx`, the phone's `Today.plan.test.tsx`) are left as they are: they test no sidecar words.

## Plain words

`copy/denyList.test.tsx` gains "the broken controls 3b sentence: %s" over every sentence this round adds: UX-50's box words, UX-51's two list lines and the tooltip, UX-56's chips, UX-54's card line and Today's three sentences, UX-44c's four "why"s; its list of every card line carries UX-30's words. Each new component test also checks its lines with `findJargon`.

## Sidecar changes

- UX-57: `add_source` looks up the file's content hash (`source_revisions_by_asset_hash`, a new read in `db/stores/source_documents.py`) and answers an existing source; read-only, no schema.
- UX-54: the status line's `waiting_behind` fact and its words for a queued import; read-only, key absent otherwise.
- UX-30: the card's build and built lines' words; and the CLI preview's help text.

No schema, migration, algorithm tag, config key or prompt change; nothing sent to a model changes (UX-51's rule leaves the words of every action a model reads as they were; UX-56 changes only what is shown). The one write this round adds is UX-50's note, on the existing note edit.

## What I ran

All through the scratch wrapper (`env -i`, empty `HOME`, `CODEX_HOME` and config dir, the shared uv and npm caches), npm and vitest in a `systemd-run --user --scope` of 5G, pytest from script files in a 3G scope at `-n 1`, one test command at a time.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile --extra tui`, `uv pip install --offline pypdfium2==5.14.0` | done |
| `npm ci` (desktop, then phone) | exit 0 (esbuild's install script blocked by allowScripts, as before) |
| fail-first and passing runs per defect | as under each defect |
| desktop `src/screens/reader` + `ReaderScreen*` (after UX-50) | 131 files: 1517 passed, 4 failed (UX-51's tests, not yet fixed) |
| desktop `src/copy`, `src/screens/reader`, `ReaderScreen*` (after UX-51) | 1 failed (the `libraryAskSwitchOff` snapshot, updated deliberately), 1763 passed |
| desktop `AskOverlay*`, `screens/reader`, `ReaderScreen*`, `Practice*`, `Feedback*` (after UX-56) | 173 files, 1906 passed |
| desktop `src/components`, `screens/reader`, `ReaderScreen*` (after UX-55) | 189 files, 1902 passed |
| desktop `src/screens/today`, `todayCause.test.ts`, `src/copy` (after UX-54) | 15 files, 458 passed |
| desktop `src/app`, `src/screens/today`, `src/copy` (after UX-44c) | 48 files, 794 passed |
| phone `src/today` (after UX-52b) | 3 files, 58 passed |
| desktop `LibraryPlace*`, `BookShelf.test.tsx`, `BookCard*`, `src/copy` (after UX-30/32) | 8 files, 291 passed |
| desktop `npm run typecheck` | exit 0 |
| desktop `npx vitest run --maxWorkers=4` (whole suite) | Test Files 1 failed, 318 passed (319); Tests 1 failed, 3343 passed: `FeedbackScreen.refusals.test.tsx` (a `findBy` timing out under the whole run's load; no file of this round is involved); then that file alone three times: 1 passed each |
| desktop `npm run frontend:build` | exit 0, "✓ built in 2.83s" |
| phone `npm run typecheck` | exit 0 |
| phone `npx vitest run --maxWorkers=4` (whole suite) | Test Files 42 passed (42), Tests 432 passed (432) |
| phone `npm run build` | exit 0, "✓ built in 854ms" |
| pytest: every test file that calls `add_source` (23) + `test_quick_add.py`, `test_sidecar_quick_add.py`, `test_ingest_queue_store.py` (after UX-57) | 832 passed |
| pytest: the files using the add helpers not in that set (15, `test_ux_phase1_first_run.py` among them) | 223 passed |
| pytest: `test_first_questions_arrive.py`, `test_first_questions_today.py`, `test_section_done_before_build.py`, `test_empty_first_build.py` | 1 failed, 73 passed (the duration test's two identical books: fixed by `48155752eb`), then `test_first_questions_today.py` 32 passed |
| pytest: `test_status_line_waiting_turn.py`, `test_mobile_allowlist.py`, `test_ux_phase1_add_source.py`, `test_ux_phase1_usability_round1.py`, `…round2.py`, `test_ux_phase1_finish.py`, `test_ux_phase1_review_fixes.py`, `test_ingest_queue_store.py`, `test_add_source_same_content.py` (after UX-54) | 424 passed |
| pytest: the 8 files whose words UX-30 changed | before the words: 15 failed, 151 passed; after: 1 failed (the `startswith` assertion, corrected as said), then 166 passed |
| `scripts/affected_tests.py --files` the three changed Python sources | 1,337 files, so a name filter: add_source, quick_add, source_library, status_line, ingest_queue, highlight, notes, reader_ask, ux_phase1, first_questions, section_done, empty_first_build, source_documents, cli_sources, build_preview, apply_recovery (29 files, one chunk, `-m "not arc_close"`, at the tip): 383 passed |
| `tests/test_identity_pins.py` after every source commit (and with the ratchets after UX-57, UX-54, UX-30/32) | 345 passed each time; with `test_structure_ratchets.py` 348 passed: no pin moved, no number rose |
| at the tip: `test_identity_pins.py`, `test_structure_ratchets.py`, `test_effective_defaults_golden.py`, `test_cli_help_snapshot.py`, `test_kill_switches.py`, `test_sqlite_file_copies.py` | 386 passed |
| `tests/test_test_layout.py` (alone) | 3 passed |
| `tests/test_architecture.py` (alone) | 18 passed |
| `tests/test_mobile_allowlist.py` | 332 passed |
| `ruff check` | All checks passed! |
| `lint-imports --no-cache` | Contracts: 43 kept, 0 broken. |
| `scripts/check_gate_partition.py` | collected 32027: landing 31962 + arc_close 65 |
| `desktop_validate.py` | no count drift; it reports the stale Reference notes of the changed modules (the landing regenerates them) |

## What a walk must check

1. **UX-50** (retainer-3 #21-28, #69-70). Select a passage, Tab, pick "note" (or "highlight"); open Notes: the box says "add a note to this highlight…"; type a thought: "✓ saved" disappears and the button reads **save note**; press it (or click elsewhere): "your note: “…”" in the card and "✓ saved" back; the Notes list shows the note on that highlight; reopen the book: it is still there. Type more and save: the note grows.
2. **UX-51** (retainer-3 #15-20). Select, Tab, type "highlight" into the box: under the list "“highlight” only finds an action: it isn't kept as a note."; pick highlight: the highlight has no note. Type "the gaps matter" and pick note: the line reads "A highlight or a note keeps your words as its note."; the note is "the gaps matter". Hover "ⓘ where this goes": the new sentence.
3. **UX-56** (retainer-3 #46). Ask about the elevator article with another book in the library: the chips read "§ source: Wikipedia Elevator Paradox · Modeling the elevator problem" and, for a one-section reading, its title alone; no slug, no "root".
4. **UX-55** (student-3 #72-74, expert-2 #33-35; WebKitGTK). In Ask, scroll the rail down to a thread, press "ask follow-up": the follow-up box is fully visible below the GUIDE/ASK/NOTES bar, and the first keystroke or click lands in it. In the Guide, a quick check brought into view ("A quick check on this section is ready") lands below the bar. Also firstq-2 #26-33: after "compare", note whether "Done with this section" is on screen; if it is under the tab bar (not brought there by LearnLoop), that is the person's scroll, not this fix's case.
5. **UX-57** (retainer-3 #6, #48). Add a file already in the library from another folder (or a renamed copy): "Already in your library — opened where you left off.", the book opens, no second card, Today asks no OK "and 2 more". A library that already has two copies: both cards stay; Add opens the first.
6. **UX-54** (student-3 #27, #92). Add a chapter, then while its build runs add a past exam PDF: the exam's card reads "◐ Waiting its turn behind “<chapter>”" (not "Getting this PDF ready"), and Today says "“<exam>” is waiting its turn behind “<chapter>”. LearnLoop gets one book ready at a time. …" or, naming the chapter, "“<exam>” is waiting its turn behind it."; once the exam's import starts, its card reads "Getting this PDF ready" again.
7. **UX-44c** (firstq-9 #84-85). After answering two questions right, open the full list (l): answered rows read "comes back in N days" (or tomorrow, later today), never-answered rows "not answered yet"; a done plan with only answered rows left says "Nothing else is needed today.", not "there's more for today".
8. **UX-52b** (a phone walk on the first evening, as firstq-10 #58 on the desktop). With a book's questions written and the plan empty: no "Nothing planned for today." above "N questions from … are ready".
9. **UX-30, UX-32** (student-3 #92, firstq-10 #84, firstq-1 #52-54). The card reads "◐ Getting this article ready for questions" during the build (with "in about N min" once this library has measured one), then "Questions for this article are written as you finish sections"; details offer "Get the whole article ready for questions at once". Note whether a person still expects questions from that press.

## Not verified

- No app, browser, server or model ran; every screen state is from vitest on fake RPCs, every sidecar state from pytest on fixture libraries. WebKitGTK layout, hit-testing and the real timing are not seen: UX-55's fix is checked against a hand-placed layout that uses the rail's real styles, not a rendered one.
- UX-50: the note is added to (a blank line between), never replaced from this box; the Notes list's own "edit" still replaces. Offline (the demo) the note is local only, as the offline capture is.
- UX-51: one-letter notes that start an action's name ("a") are taken as finding words. The list still does not narrow as the learner types (the walk's expectation; not this defect).
- UX-56: "root" is dropped wherever it is the label's last part; a page whose part before its first heading is labelled "root" now shows its title alone.
- UX-57: only local files (a link's bytes are not known at Add); a source with that content that has neither a reading nor an import on its way (a failed import) is not matched, and the file is added as before.
- UX-54: only the import (a source's first step, and a link's fetch) says it waits; a build queued behind another book's build still says "Getting … ready for questions" (true, but not why it does not move). A running job whose book has no title, or a stale running job, gives no waiting line.
- UX-44c: the days are counted in the machine's local calendar.
- The desktop's whole run failed once on `FeedbackScreen.refusals.test.tsx` (a `findByPlaceholderText` timing out); it passed three times alone. Not filed: seen once, under load, in a file this round does not touch.
- The vault references are not regenerated (the landing does); the vault's `Reference/Desktop` notes for the changed modules are stale until then.
