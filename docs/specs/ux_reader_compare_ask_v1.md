# Reader: comparing sources, skimming across books, and Ask, revised — experience design (v1)

**Status:** owner decisions recorded 2026-10-25 (§15: every recommended answer adopted except Q3, which keeps today's rule). Aligned the same day with the companion curriculum spec at `5facf66b9`. It revises three parts of `docs/specs/ux_reader_workbench_v1.md` (the *UX doc* below): §4.5 (ask your library, compare, keep), W9–W10 (the comparing posture and the compare table), and Ask wherever it appears (§4.2, §4.9, §5.12, W13). It adds two things the UX doc lacks: skimming and jumping across corresponding sections of the learner's books, and the problem as printed for imported problems. The UX doc still governs everything this document doesn't name. The workbench spec (`docs/specs/spec_reader_workbench_v1.md`, *spec* below) wins on behaviour, data and gates, and this document on presentation, as before.

**Changes no data contract by itself.** Where the design needs a contract changed, §12 says so, with the spec or code it touches. A few changes are requests to specs that other stages own: the bug-fix stage on `fix/owner-capture-1025`, the sources spec (`spec_source_practice_and_probes_v1.md`, `compare_sources`), and the companion spec `docs/specs/spec_deliverable_curriculum_v1.md` (branch `docs/deliverable-curriculum`, commit `5facf66b9`). The companion spec owns the **section correspondence index**: its backbone table `section_coverage` (one judged row per section × LO; two sections correspond when both cover the same LO) and the read API `reader.correspondents`. It owns that data and how it is computed. This document owns how it is presented (§6), and §12.3 records what the presentation reads from it and the little it still asks for.

**The owner's notes (2026-10-25), which this document answers:**
1. "make it easier to compare sources in learnloop within the reader ux, with natural language querying available to the user. revise also the specific reader table for ux" → §4 and §5.
2. "for syntopic reading should we have the ability to skim through multiple sources and jump to sections that correlate with the other source?" (yes) → §6.
3. "learnloop ask needs a ux overhaull and should reset hints if the question is reattempted instead of reusing the same hints/questions that were asked last time this question was served" → §7.
4. "learnloop ask doesnt work in Work in Steps mode when doing a question" → §7.6. The bug-fix stage on `fix/owner-capture-1025` is restoring the behaviour now: Ask in steps mode, the help style ignored when hints exist, hints and Ask not reset on a reattempt, and a stale scheduler offer on submit. This document assumes those behaviours are fixed. §11 marks which contracts belong to that stage (**B**) and which are new work (**N**).
5. "for any textbook problem that was OCR'd allow the option to see the original textbook screenshot/section" → §8.

**Inputs, read for this document:**
- The UX doc in full, including §3–§7, §4.5, §4.6, §4.9, §4.10, §5.11 and §6.1, and wireframes W1–W16.
- The spec's §4 (inquiry, the intent box, RW1c's tutor), §5 (the workbench and §5.4's evidence table), §7.3 (RW4a), §7.8 (RW4d), §3.4 item 15 (the relation mapping) and D46.
- `spec_adaptive_hints_v1.md`: §4.1–4.2 (one service, kinds, levels, the learner's picks), §4.5 (the chooser, the help style) and §4.8 (what the learner sees).
- `ux_learnloop_v1.md`: §0, §4.2–4.3 (three layers, placement rules, one disclosure pattern), §7.3–7.4 (the Reader shell, practice).
- The sources spec §9.4 (`compare_sources`), the image drop-in spec, and P3 §11.
- The code on `main` at `fa2eb72f8`, audited for this document (§3).

**Citation convention.** *UX §4.5* is the UX doc; *spec §7.3* is the workbench spec; *hints §4.2* is the adaptive-hints spec; *shell §4.2* is `ux_learnloop_v1.md`; *sources §9.4* is the sources spec; *curriculum* is the companion spec. Phase tags in brackets, such as **[CA2]**, name this document's phases (§13). `FE` is `apps/learnloop-tauri/src`; `SC` is `src/learnloop_sidecar/handlers`.

**Who this is for.** The same one person as the UX doc: the owner, reading mathematics and probability from several textbooks at once, on the desktop app and sometimes on the phone. They own several books on the same subject on purpose: in the linear algebra vault, more than one treatment of eigenvalues, each with a different route. Comparing those routes is a reason the library exists.

---

## 0. The design on one page

Ten moves:

1. **One way to compare, four doors.** Selecting a passage and asking *how do my other books treat this?*, typing *how do Axler and Strang treat eigenvalues* into the ask box, pressing the tutor's *how do your books treat this?*, and *compare* in a library answer all build the same comparison request and land on the same table (§4). None of them needs passages pinned first. Pinning stays as the precise route.
2. **Natural language names the books.** "Axler and Strang" becomes two source chips and "eigenvalues" the topic, shown before anything runs as *comparing Axler · Strang · on eigenvalues · change*. The learner's words are read by a model, never parsed by rules (§4.3).
3. **The table reads across, not down.** One row per point and one column per source, so a row answers *what does each book say about this?* (§5). Each cell is the book's own words first, with LearnLoop's one-line reading under it. Each row carries an agreement chip in plain words: *the same claim · different assumptions · different notation · they disagree · unclear*. A last column holds the learner's own take. The three voices never share a cell.
4. **Perspectives are rows.** *A geometric view* typed above the table becomes a row. A book that has none says *not here*, and a row no book fills says *not found in your library* (§5.4).
5. **A quiet "also in your books".** While reading a section, the Guide shows one dim line naming the learner's other books that treat it, such as *also in Strang §6.1, Axler §5.B ▸*. It names books, never counts them, and it never enters the text column. `Space` peeks a section, `↵` jumps there, and `Alt+←` comes back (§6).
6. **Side by side, following along.** Two books in two panes, and the second follows the first section by section. It moves only when the leading pane crosses into a new section, and never the pane the learner last touched (§6.4).
7. **One Ask, everywhere.** The Reader's rail, the practice screen and the workbench, Work in Steps included, use one Ask component with one set of states, keys and voices (§7). On the practice screen it docks beside the answer instead of covering it. In the workbench it asks about the focused step and answers under that step.
8. **A fresh thread every attempt.** Each attempt at an item starts with an empty Ask and an empty hint list. Earlier threads stay browsable under *earlier on this question*, dated, read-only and never shown as current. They are absent during a check on your own (§7.3).
9. **One ladder, two doors.** A hint is help LearnLoop picks for your work. Ask is help in your own words. Both land in one help record for the attempt, are measured on the same five-rung ladder, and cost the same. Ask never hands over worked help without the ladder's take step. The help style is visible on the panel and changes what both serve (§7.4–7.5).
10. **The problem as printed.** Any problem imported from a page (Marker, GLM-OCR) or a photo shows *▸ as printed* under the stem, an inline crop of just that problem from the page, plus *original page ↗*. During a check on your own both are hidden, because they locate the exercise (D46). They come back with feedback (§8).

---

## 1. Principles, as tests

These add to the UX doc's U1–U14, which all still hold. Each ends in a test that can fail.

| # | Principle | Test (fails if…) |
|---|---|---|
| **C1** | **One comparison, whatever the door.** The learner's way in changes only what is pre-filled. | …two doors produce different RPCs or payload shapes for the same scope and question, or land on different table components. …any door requires pinning before a comparison can run. |
| **C2** | **Across, not down.** A row is one point, read across every book. | …a comparison computed with the v2 contract (§12.2) renders source-per-row by default. …a cell holds a model line with no verified quote and isn't labelled *not addressed here*. |
| **C3** | **Differences are the content; agreement is labelled, not merged.** | …any row, header or chip says "summary", "consensus" or "overall". …a chip shows a relation the comparison didn't return. …a "same claim" row collapses its cells into one. |
| **C4** | **Names, not counts, for things to read.** The learner sees which books, not how many. | …the *also in your books* line, a row or a chip shows a number of sources, sections or matches. (The comparison's header keeps the source names; when they don't fit it ends *and others ▸*, and those names are one key away.) |
| **C5** | **Navigation is quiet.** Correspondence helps the learner move; it never asks for attention. | …*also in your books* appears in the text column, animates, takes focus, or appears on a section the index has nothing for. …in side by side, the pane the learner last scrolled, clicked or selected in moves on its own. …follow-along moves the other pane while the learner is mid-section in the leading pane. |
| **C6** | **Every attempt starts clean.** | …a new serve of an item shows a hint, an Ask exchange or a help footer from an earlier serve as current. …an earlier serve's exchanges enter the model context of a later attempt. |
| **C7** | **The help style is visible and it works.** | …any host's Ask or hint panel hides the style. …under *let me struggle* the fallback serves the same kind and level it serves under *guide me* on the same state (bug-fix B2). …an Ask answer doesn't say which mode it was written in. |
| **C8** | **Help is one ledger.** Every hint, check and question taken on an attempt is listed in one place, in order, each with its cost. | …a question that counted as a hint is missing from the attempt's help footer. …two help surfaces on one attempt show different totals. |
| **C9** | **Ask is never blocked and never a back door.** | …Ask is hidden or refused in Work in Steps, on a cold check, or in the Reader's working posture. …Ask shows worked help (level 4–5) without the take step. …during a cold check, a question is sent without its consequence shown in the box first. |
| **C10** | **The book is the reference for its own problems.** | …a problem imported from a page or a photo lacks *as printed* outside a cold check. …*as printed* shows anything beyond the problem's own blocks (no neighbouring exercise, solution or worked example). …*as printed* or *original page* shows during a cold check. |

---

## 2. The felt experience

The owner is in the linear algebra vault, in Strang's chapter on eigenvalues. Each moment says what happens, what the learner feels, and what LearnLoop deliberately doesn't do.

**Moment 1 — noticing the other books.** Under the section bar in the Guide sits one dim line: *also in Axler §5.A, Lay §5.1 ▸*. Nothing else changed. They keep reading.
- *Does not:* put a mark in the text, say "2 other sources", or pulse.

**Moment 2 — a peek.** At the characteristic polynomial, they wonder how Axler gets eigenvalues without determinants. `x` focuses the line, and `↓` reaches *Axler §5.A Invariant subspaces · introduces it*, under the LO *eigenvalues of a linear map*. `Space` shows that section in the right side. The crumb strip reads `↩ Strang §6.1 ¶4 › peek Axler §5.A`. `Esc` closes the peek, and they are back at ¶4.
- *Feels:* the other book was one key away and didn't cost them their place.

**Moment 3 — side by side.** They want to read both. `Ctrl+\`: Strang on the left, Axler on the right, and the rail folds to its gutter. As they scroll Strang into §6.2, Axler moves to its section covering the same LO, once, at the boundary. When they start scrolling Axler, it leads instead, and Strang follows.
- *Does not:* jitter line by line, or move the pane they are reading.

**Moment 4 — asking across books in their own words.** `Ctrl+Shift+F`, then they type *how do Axler and Strang show eigenvalues exist?* The box shows *comparing Axler · Strang · on: why eigenvalues exist · change* for a second, and the table opens beside the book. Its rows are *existence argument*, *what's assumed about the field*, *role of the determinant*. Each row has Axler's words and Strang's words, with a dim LearnLoop line under each. The chips read *different assumptions* on the first row and *they disagree* on the third: one book builds on the determinant, the other avoids it.
- *Feels:* the books talking to each other, with their differences kept.
- *Does not:* write an essay, crown one book's route, or say "3 rows".

**Moment 5 — your take, in its own column.** On the determinant row, `t`: they type *Axler's route generalizes; Strang's computes*. It sits in the *› you* column, in their voice. `k` keeps the comparison, and both passages get `⇄`.

**Moment 6 — a problem as printed.** Monday's plan serves Exercise 6.1.12, imported through GLM-OCR. Under the stem: *▸ as printed (Strang p.297)*. They open it to check a subscript the transcription made ambiguous. The crop shows just the exercise. *original page ↗* would show the whole page; its label says *counts as a hint* because they haven't submitted yet. They don't need it.

**Moment 7 — stuck in steps, asking in their own words.** They switch to *Work in steps*. On step 3 they press `?`: *why can I assume λ is real here?* The answer lands under step 3: *◇ model · your question · about step 3 · helping you reason*, with the book first (*§ Strang §6.4: "…"*). The help footer reads *help used: a question (counts as a hint)*.
- *Does not:* say "Ask isn't available while working", or open a modal over their steps.

**Moment 8 — a reattempt.** Two weeks later the plan serves 6.1.12 again, as ordinary practice. Ask is empty, and so is the hint list. At the Ask panel's foot sits a dim line: *earlier on this question ▸*. They leave it closed and work it fresh.
- *Does not:* show last time's hints as if they were today's, or feed them to the model.

**Moment 9 — a check on your own.** A cold check from another book. `?` opens Ask with the placeholder *ask in your words — a question about the maths makes it practice with help ◌; asking what the question means doesn't*. They ask what a symbol in the stem means. The answer is labelled *a clarification · still on your own*, and the banner doesn't change. They solve it alone. *As printed* is hidden, and so is *earlier on this question*. After feedback, both appear, with *Exercise 4.22 · p.214 · original page ↗*.

---

## 3. What is there today (code truth, `main` at `fa2eb72f8`)

| Area | Today | Where |
|---|---|---|
| **Compare: entry** | In the comparing posture, pin at least two passages from at least two sources, then *compare pinned (N)*; otherwise *pin passages from two places to compare them*. The tutor's *how do your books treat this?* runs `compare_sources` on press. `reader.library_compare` refuses fewer than two pins. | `FE/screens/reader/LibraryAnswer.tsx:498-504`, `useLibraryAsk.ts:281-285`; `TutorOffers.tsx:65, :429-431`; `src/learnloop/source_retrieval/library_ask.py:1102-1155` |
| **Compare: natural language** | The ask box's text is search text over every source. No source names are recognized: "Axler and Strang" is just more query. `LibraryAskInput` has no source filter. | `SC/library_ask.py:354-363`; `source_retrieval/compare.py:156-479` |
| **Compare: the table** | `CompareTable`: one row per source, **stacked**, each with three labelled cells underneath: *contributes · assumes · differs from the others*. Not W10's grid. A relation only decides which cell a line goes in (`different_assumptions` → *assumes*, every other relation → *differs*). The table shows no relation chips. | `LibraryAnswer.tsx:158-244`; `library_ask.py:1050-1099`; `TutorOffers.tsx:252-301` |
| **Compare: relations and keep** | Below the table, `CompareKeep` shows a band, *how LearnLoop reads the relations*, with one line per pair (`A ⇄ B · different assumptions`), then *your take (optional)* with an *about* select over pairs, then *keep comparison ⇄ / remove*. Fine labels: *the same claim*, *different assumptions*, *different notation*, *complementary*, *they disagree*, *unclear*. The model never produces `complementary`. | `CompareKeep.tsx:47-54, :81-112, :183-239`; `kept_comparisons.py:97-104` |
| **Compare: the model's output** | Per source, its contributions, each with a perspective and a verified quote. Per pair, a relation, a statement and two quotes. Plus missing perspectives, *also discussed in*, unverified sources and dropped pins. **There is no per-point alignment**, so the comparison has no rows a "row per claim" layout could use as is. | `compare.py:71, :91-131` |
| **Compare: perspectives** | Free text, comma-separated, beside *compare pinned*. At most 4 kept. They come back as *perspectives: …* and *not found in your library: …* lines. | `LibraryAnswer.tsx:190-198, :485-497`; `kept_comparisons.py:110` |
| **Compare: narrow widths** | `LibraryPane` is half the window, at least 480 px, and leaves at least 360 px for the book. It does **not** stack below 1,040 px, although UX §3.1 says the comparing posture should. Its width isn't re-clamped when the window is resized. | `LibraryPane.tsx`; `screens/workbench/splitWidth.ts:6-20` |
| **Compare: keys** | Inside the answer only: `↑↓` move, `Space` peek, `p` pin, `o` open, `c` compare pinned, `Ctrl+↵` ask the tutor about pinned. | `LibraryAnswer.tsx:323-366` |
| **Cross-source sections** | **No correspondence data exists on `main`.** Nearest: LO and facet teaching links (`entity_source_links`, `build_cross_source_spans`), used for *where else is this explained*; stored comparisons are per question, not per section. The curriculum spec (`5facf66b9`) specifies `section_coverage` and `reader.correspondents` (its phase C0, or C0a alone); not built yet. | `content/authoring/practice_leakage.py:271`; `library_ask.py:408-427` |
| **Return stack** | Shipped (RW1a): entries *origin · branch · peek · citation · source*, `Alt+←/→`, the detour strip. | `returnStack.ts`; `useReaderInquiry.ts:404-434, :545-551`; `DetourStrip.tsx` |
| **Ask: practice** | `AskOverlay`, **a modal** shared by the practice, feedback, library and reader contexts. The practice thread and its question budget are keyed by **(item, session)**, with no attempt key, so a second serve of an item in the same session shows the old thread and sends it to the model as history. Pills: *counted as hint*. Footer: *tutor answers are logged · never reveals the answer*. | `FE/components/AskOverlay.tsx`; `src/learnloop/tutor/tutor_qa.py:291-298, :1497-1530`; `SC/tutor_qa.py:532-575` |
| **Ask: Work in Steps** | **No Ask.** The `?` handler returns early in steps mode, and the Ask button lives in the answer-box branch that steps mode replaces. The key bar still advertises *? ask*. The palette's Ask opens the practice overlay with the hidden answer box's progress and no steps. In the Reader's working posture, Ask waits: *"Ask the tutor is beside the book. Leave for now (your steps are kept) and Ask opens."* `ask_tutor_question` has no workbench field; the Reader path has `workbench_session_id`. | `PracticeScreen.tsx:841, :850, :2070, :2086`; `ReaderWorkingPosture.tsx:16`; `SC/reader.py:111` |
| **Ask: Reader** | The rail's Ask tab: grounding cards (*asking about your selection*), a *mode* select (answer directly · help me reason · ask me first, set per source by `reader_set_answer_mode`), *personalized ●*, `Ctrl+↵` sends. Answers come book first (`TutorAnswer`), with offers that are fetched early and shown on press (`TutorOffers`). | `AskRail.tsx:124-226`; `TutorAnswer.tsx`; `TutorOffers.tsx` |
| **Hints: practice** | The adaptive hint panel (`HintPanel.tsx`) resets on (item, session) on the client; the server counts per `submission_id`. The draft checkpoint restores `submissionId` and `hintsUsed`, so reopening an item after a steps submit restores both and fails as a stale offer (bug-fix B4). The help style lives in Settings and the panel's `⋯` menu, **not on the screen**. | `useAdaptiveHints.ts:139-154`; `SC/hints.py:178-181`; `hints/state.py:40-66`; `PracticeScreen.tsx:238, :320, :374, :521` |
| **Hints: workbench** | The ladder, *check my work*, per-problem help style (`HelpStyleControl`), restored on reopen by `workbench_help_state`. Help is on only once the session is bound to an item. | `screens/workbench/*`; `SC/workbench_help.py` |
| **Help style** | One stored preference, `[hints] help_style`. It reaches the hint state, the writer prompt and the chooser prompt, but not the deterministic fallback (bug-fix B2). Ask doesn't read it: the Reader has its own answer mode, and practice Ask has none. | `hints/writer.py:256`; `hints/chooser.py:97` |
| **Cold checks** | DL2's banner and the ladder's take header are in place for Hint. **Ask isn't gated by the take step**: its only warning is *substantive questions count as hints*, and the server doesn't check cold status on `ask_tutor_question`. "Substantive" is the tutor model's own `question_type` on each answer: `prerequisite`, `mechanism` and `strategy` count (`HINT_EQUIVALENT_TYPES`); `clarification`, `verification` and `other` don't. A Reader Ask bound to a cold workbench session counts **whatever its type** (`tutor_qa.py:855-867`), so the two cold paths disagree today. `cold_retry` follow-ups say *"No hints on this one: it's a check on your own."*, which withholds hints, against UX U11 and P3 §11. The item header hides locators (D46, `locators_hidden`). | `src/learnloop/intent/checks.py:44-62, :155`; `PracticeScreen.tsx:935-963, :1496-1515, :1536-1541` |
| **Original page** | **No *original page ↗* on any practice item** (none in the frontend). PDF blocks from Marker, pypdf, Datalab and GLM-OCR keep `page` and `bbox_json`. Imported textbook exercises keep `canonical_exercise.span_ids`, but the DTO carries no page or box. A crop RPC exists, `reader.block_original_region` (a PNG data URL of a block, or a sub-box of it), **with no UI caller**. `OpenInSource` renders a page with a box highlighted, opened from provenance and citations, never from practice or feedback. A phone photo becomes a hand-written card; the item keeps no link back to the photo. The image drop-in path is only specced. | `migrations/032_source_layer.sql:70-77`; `ingest/extractors/glm_ocr.py:20-27, :738`; `vault/models.py:735-749`; `FE/api/dto.ts:2411-2422`; `SC/reader.py:666-674`; `reader/span_view.py:257-370`; `capture/inbox.py:100-160, :234` |
| **The bug-fix stage** | `fix/owner-capture-1025` has one commit: fail-first tests for B4 (a steps submit releases the draft; a stale offer still grades, unattributed). Its docstring names B3 (Ask belongs to the current attempt) and B2 (the help style changes the fallback). | `tests/test_owner_capture_1025.py` on that branch |

---

## 4. Compare from anywhere **[CA3]**

### 4.1 One request, four doors

Every door builds one **comparison request**:

| Field | What it is | Who fills it |
|---|---|---|
| question | the learner's words, or the selection's sentence | the learner, or the door |
| anchor | the passage the comparison is about (a selection, the open section) | the door, when there is one |
| sources | the books to compare, when the learner named or chose them | the scope reading (§4.3), the side-by-side pane, *+ add a book* |
| pins | exact passages the learner pinned | the library answer (optional) |
| perspectives | views the learner asked for | the refine box (§5.4) |

The server still derives the policy from the call's context (sources §5.2). A request can narrow the scope and never widen it (C1, §11 K12).

| Door | What the learner does | Pre-filled | Lands |
|---|---|---|---|
| **The selection verb** | Selects a passage, then the palette's *how do my other books treat this?* (Transfer group), or types it in the intent box | anchor = the selection; question = the selection's sentence, or the typed words; sources = every other book, or the other pane's book in side by side | The comparing posture: the table, with the anchor's book as the first column, headed *your passage* |
| **The ask box** | `Ctrl+Shift+F` (or *Ask* on the library page), then types a comparison: *how do Axler and Strang treat eigenvalues* | question, sources and topic from the scope reading (§4.3) | The table, if the words ask for a comparison; otherwise today's sources-first library answer (UX §4.5) |
| **The tutor's offer** | Presses *how do your books treat this?* under an answer (exists, RW1c / RW4d) | question = the tutor's request; anchor = the answer's cited passage | The same table |
| **A library answer** | *compare these books ▸* (new: all the books in the answer, no pins), or pins and *compare pinned* (exists) | sources = the answer's books; pins when pinned | The same table |

**Palette change.** Today's palette has two neighbouring verbs: *where else is this explained?* (a library ask) and *how do my sources treat this? (compare)*. They stay two verbs, because they answer different questions. *Where else* lists passages; *how do my other books treat this?* compares. The second moves from Understand to **Transfer**, beside *where else*, and takes the owner's wording. The intent box's router (`reader_intent`) already lists *compare sources* among its actions; its label follows.

**No pins needed.** A selection-started comparison is the anchor plus discovery: `compare_sources` already considers every source in scope (sources §9.4 step 2). The Reader's RPC refuses fewer than two pins today; §12.2 asks it to accept the anchor alone.

### 4.2 What the learner sees while it runs

- **The routed line**, in the intent box or the ask box: *→ comparing · Axler · Strang · on eigenvalues · change*. *change* reopens the box with the text kept. It is the intent box's pattern (UX §4.1), with the sources as chips.
- **Pending,** in the comparing posture: the table frame appears **at once**, with source columns named as soon as the scope is known. Cells fill in two stages, each with a pending line in its own words: *◐ finding each book's passages…* while retrieval and verification run, then *◐ lining the books up…* while the comparison model writes. The excerpts appear as soon as they are verified, before the rows exist. They show in a provisional *by book* layout, which then reflows into rows once (no animation; under reduced motion it just appears).
- **Landed:** the table (§5). It takes no focus, and the posture's tab shows a static `•` if the learner was elsewhere (UX §4.0).
- **Failed, unreachable, capped, plan down, switched off:** UX §4.0's states, in place of the rows. The question and the chosen books are kept. **Plan down** follows T1: one line, *ChatGPT plan isn't answering right now · use OpenRouter for this comparison? ▸*. This is redesign D: the offer is the grant, keyed by the origin RPC method (`reader.library_compare`), and it is offered only because the learner pressed something.

### 4.3 Naming books in natural language

**What the learner types** is free: *how do Axler and Strang treat eigenvalues*, *compare the spectral theorem in my two books*, *does Lay do this differently from the lecture notes?*

**What reads it.** A model, never a rule: one typed Decider choice (a new task, `compare_scope`, routed by T1's rules) over the vault's book list (titles, authors, short names). It returns:
1. whether the words ask for a comparison (otherwise it is a library ask, today's behaviour);
2. which books were named (a multi-select over the list, possibly none);
3. the topic, as a query with the book names removed.

A named book the list can't match comes back as *"Hoffman" isn't in your library* in the routed line; nothing is guessed. With no books named, every book with a match is compared, as `compare_sources` does today.

**What the learner sees before it runs:** *comparing Axler · Strang · on: eigenvalues · change*. Each chip has an `×`, and *+ add a book* opens a short picker of the library's books (type-ahead; `↵` adds). The comparison starts at once. The chips are visible so *change* is honest, not to ask for a confirmation (UX: no "are you sure?").

**Speculation:** none. The ask box routes on `↵` only. It is a pressed action, so background work stays quiet (T1), and the routing call is paid for only when the learner asks.

**Unavailable Decider:** the routed line reads *comparing all your books · on: "how do Axler and Strang treat eigenvalues" · choose books ▸*, and the comparison runs over every book with a match. The learner's words are the query, so nothing is lost.

### 4.4 Comparing inside the comparison

The question that started a comparison is rarely the last one:
- **Refine** (`/` in the table): *what do you want to see? a geometric view, an application, just the proofs…*. Perspectives become rows (§5.4). A request that changes the scope (*add Lay*, *only Axler and Lay*) changes the chips instead. The same `compare_scope` reading decides which is which. The table re-runs as one comparison, and the earlier version stays one key away (*previous ▸*), since a comparison is never paid for twice (sources §9.4 step 7).
- **Ask the tutor about this comparison** (`Ctrl+↵`, exists as *ask the tutor about these*): citations limited to the compared passages, and it says so.
- **Practice this** (exists): `find_practice` on the comparison's question.

---

## 5. The comparison table, redesigned **[CA4]**

### 5.1 The shape

- **A column per source**, in the order the scope reading or the anchor gives (the anchor's book first, headed *your passage*; otherwise verified relevance, sources §9.4 step 4). The column header holds the book's short name and the section locator: *§ Strang §6.1 p.289*.
- **A row per point.** A point is one thing the books can be compared on: *the definition*, *why eigenvalues exist*, *what's assumed about the field*, *the role of the determinant*, *a worked example*. The comparison model names the points and labels them in LearnLoop's voice (`◇`). The row header shows the label, with *◇ LearnLoop's point* the first time per table, then only `◇`.
- **A cell** is the book's verified words first, `§ "…"` (at most two lines, expandable with *more*), then LearnLoop's one-line reading of what the book does on this point, in the model voice, dim, `◇ builds the polynomial first`. A book that has nothing verified on a point shows *— not addressed here*, never a paraphrase. A book whose passage wasn't checked shows *possible match, not checked ▸* (sources §9.4 step 2).
- **The agreement chip**, at the end of each row header, in the model voice: one of the comparison's own relation labels, in the shipped plain words.

  | Relation (`compare_sources`) | Chip | Shown when |
  |---|---|---|
  | `equivalent` | *the same claim* | every compared pair on the row returned it |
  | `different_assumptions` | *different assumptions* | at least one pair returned it |
  | `different_notation` | *different notation* | at least one pair returned it |
  | `disagreement` | *they disagree* | at least one pair returned it |
  | `unclear` | *unclear* | at least one pair returned it |
  | (only one book addresses the point) | *only in Axler* | the other cells are *not addressed here* |

  **Only the relations that exist.** The five model relations above are exactly `compare_sources`' `RELATIONS` (`source_retrieval/compare.py:71`), and v2 keeps that set unchanged (§12.2). *Only in Axler* is not a relation: it is how the table shows a row where only one book has a verified cell. `complementary` is **not** a chip. The comparison model never emits it; it exists only in RW4d's mapping table (`kept_comparisons.py:97-104`, and `CompareKeep.tsx`'s fine labels), where it maps to `refines`. How two books complement each other is already visible as their different cells on the same row, and as rows only one book fills. Adding `complementary` as a model relation would be a `source_compare` prompt and schema change, and this design doesn't ask for it.

  A row shows every label its pairs returned, in the table's order above, never a summary of them. With more than two books, focusing the chip opens the pairs: *Axler ⇄ Strang · different assumptions · "…" / "…"* (the pair's statement and both quotes; RW4d's band, moved onto its row). The chip has words and no colour coding. *They disagree* gets the same treatment as every other label: books disagreeing is the content, not an alarm (U6, C3).
- **The learner's column**, last, headed *› you*: each row's *your take* in the learner's voice, empty until written. `t` on a row opens a one-line box there, with *ⓘ where this goes* (UX §4.10's comparison wording). A take not tied to a row goes in the table's foot (*about the whole comparison*). This replaces today's *about* select: the row is the *about*.
- **The table's header:** *COMPARE · Axler · Strang · on: why eigenvalues exist · differences kept · each line quotes its own book*, then *perspectives* (the refine box), *by point · by book* (the layout toggle, §5.6), *keep ⇄* and *esc back*.
- **The table's foot:** *also discussed in: Lay §5.1 ▸* (uncompared books, one key to add each), *left out: …* (dropped pins, with reasons), and *ask the tutor about this comparison · practice this*.

The three voices never share a box. Column cells are the books (`§`, solid rule), with LearnLoop's gloss under a dotted rule. Row headers and chips are LearnLoop's (`◇`, dotted rule, purple label). The last column is the learner's (`›`, amber solid rule). This holds in greyscale and for a screen reader (U7).

### 5.2 Keep, remove, and coming back

- **Keep** (`k`, or *keep ⇄*) keeps the whole comparison as RW4d does today (proposals in the source-object layer, `⇄` margin marks on each compared passage). The receipt line is unchanged: *kept as proposals · nothing changes your map until you review them*.
- **Hide a row** (`-` on the row header): the row folds to one dim line, *hidden: the role of the determinant · show*, and isn't kept. It is the learner's edit, before or after keeping (after keeping, it supersedes that row's proposals, never deletes them).
- **Remove** (*remove* in the header, after a keep): supersedes the kept proposals, as today.
- **Reopening** from a `⇄` mark, or from *you compared these on 3 Oct · reopen ⇄* on a later library answer, shows the kept table with no model call. Hidden rows stay hidden.

### 5.3 Old comparisons

Comparisons stored before the v2 contract (§12.2) have no points. They open in the *by book* layout (§5.6), with today's three cells and the relations band, and no label says they are old. *Compare again by point ▸* re-runs under v2 when the learner wants rows. It is one paid call, named before it runs (*runs one comparison*). Nothing re-runs on its own.

### 5.4 Perspectives as rows

- The refine box takes the learner's words (*a geometric view*, *an application to differential equations*). Each requested perspective becomes a row headed by the learner's words in the learner's voice (*› a geometric view*), since the learner asked for it, with each book's cell beneath, as for any other point.
- A book without that perspective shows *— not here*. A row no book fills reads *a geometric view · not found in your library*, and *where else is this explained? ▸* offers a library ask (it may find a passage the comparison's scope left out).
- Today's bound of four perspectives on a keep is a stored-size bound. The refine box doesn't show it unless it is reached: *four views is the most a comparison keeps · remove one to add this*. It is labelled a `keep` guardrail in §12.2.

### 5.5 Keyboard first

The table is an ARIA `grid` with a roving focus. Focus starts on the first row header, never on a cell's text. The keys are checked against the comparing posture's existing keys (`Space`, `p`, `o`, `c`, `Ctrl+↵`) and keep their meanings.

| Key | Does |
|---|---|
| `↑` `↓` `←` `→` | move between cells; `Home` / `End` reach the row's first and last cells |
| `Space` | peek this cell's passage in the source pane (with a crumb) |
| `o` | open this book at this passage (left pane, with a crumb) |
| `↵` | expand a cell's quote, or open a row chip's pairs |
| `t` | your take on this row |
| `-` | hide or show this row |
| `/` | refine (views or books) |
| `+` | add a book (picker) |
| `v` | switch *by point* / *by book* |
| `k` | keep the comparison (and *remove* after a keep, from the header) |
| `Ctrl+↵` | ask the tutor about this comparison |
| `Esc` | back (peek, then box, then posture, as UX §3.2) |

**Screen reader.** Column headers name the book and locator; row headers name the point. A cell reads as *"Strang, on why eigenvalues exist. From the book, section 6.1: … LearnLoop's reading: builds the polynomial first."* A chip reads as *"LearnLoop's reading of how they relate: different assumptions."* *Not addressed here* is spoken, not left as an empty cell. The grid announces nothing while filling, then one polite *"Comparison ready: 4 points"*. That is a count of rows in a finished table, not of waiting things; if the owner prefers names, *"Comparison ready"* (§15 Q7).

### 5.6 Narrow widths, and *by book*

- **Wide enough for the grid** (the comparing posture at its remembered width). The point column is sticky. When the columns don't fit at a readable cell width, the grid scrolls sideways **inside its frame**, never the page, with the next book's name peeking at the edge. The readable cell width is a layout bound, labelled in the CSS, not a learned constant.
- **Narrow** (below the 1,040 px breakpoint the app already uses, or a pane too narrow for two columns). The comparing posture **stacks**, as UX §3.1 already asks and the code doesn't do yet. The table becomes **cards by point**: one card per row, its label and chips on top, then each book's cell under the book's name, and *› you* at the card's foot. `↑↓` move between cards and `←→` between the books inside a card. The grid's keys keep their meanings.
- **By book** (`v`, remembered per device) is the transposed view: one card per book, with that book's cell on every point. It reads like today's table, so a learner who reads one book at a time keeps that view. It is also the only layout for v1 comparisons (§5.3).
- **Resizing** re-clamps the pane (today's width is computed once at mount).

### 5.7 The phone

v1 has no Reader on the phone and no new phone RPC (spec D20, UX §7.6). This design proposes one read-only phone view for later, behind the owner's trigger (**[CA7]**, §15 Q11): **kept comparisons, by point**. On the phone page, a kept comparison opens as the narrow cards of §5.6: the point, the chips, each book's words and LearnLoop's line, and *› you*. *Your take* can be added there, because it is learner text in the learner's voice. Nothing that costs money runs on the phone: no new comparison, no tutor, no refine. It needs one read RPC on the mobile allowlist (`reader.kept_comparison_view`, desktop-only today) and one write (`reader.library_compare_keep` with a take only). Both are owner decisions under the mobile spec.

---

## 6. Skim and jump across your books **[CA5, CA6]**

### 6.1 What it is for

The owner's question: while reading a section, see and reach the sections of other books that treat the same thing, and read two of them together. This is navigation, not a cue. It doesn't say anything about the learner, so it never uses the evidence vocabulary and never counts against the margin-mark density (UX §4.4). It is still something LearnLoop shows unasked, so it obeys every rule of the attention budget: static, out of the text column, switchable from the element itself (§6.5).

### 6.2 *Also in your books*, in the Guide **[CA5]**

**The data is the curriculum spec's** (`spec_deliverable_curriculum_v1.md` §6, commit `5facf66b9`). Its backbone is `section_coverage`, one judged row per (section, LO). Two sections in two books **correspond when their coverage names the same LO** with a treatment other than `not_about` (the *section correspondence index* in this document is that join). The read API is `reader.correspondents(extraction_id, section_id)`. Per LO and per other source, it returns the sections with their `treatment`, roles, notation line, any relation the learner kept, and a `jump` locator, ordered by treatment (`introduces` and `develops` first) and then by retrieval rank. It makes no model call. This section designs only how that answer looks.

- **Where:** in the Guide rail, directly under the section progress line, one dim line: *also in Axler §5.A, Lay §5.1 ▸*. If the names don't fit one line it ends *and others ▸*, still names and never a number (C4). The line appears only when `reader.correspondents` returns judged coverage for the section. Unchecked search hits never put it on screen by themselves (below). Nothing appears when there is nothing (no ghost line, no "none found").
- **Expanded** (`x` from the reading posture, or a click): grouped by LO, because a correspondence *is* a shared LO, in the API's order:

  ```
  also in your books
  eigenvalues of a linear map
    Axler  §5.A Invariant subspaces     introduces it                     ▸
    Lay    §5.1 Eigenvectors…           develops it · uses row vectors    ▸
  the characteristic polynomial
    Lay    §5.2 The characteristic eq.  develops it · you compared these: different notation  ▸
  space peek · ↵ go there · s side by side · c compare · ⋯ not about this
  ```

  - **The LO heading** is the LO's title, the learner's map vocabulary.
  - **Each line** has the book, then the section's own number and title (`§`, the book's words), then its **treatment** in plain words: `introduces` → *introduces it*, `develops` → *develops it*, `applies` → *uses it*, `mentions` → *mentions it*.
  - **The notation line** (`notation_md`, *uses row vectors*) is the coverage judge's words, so it shows in LearnLoop's voice (`◇` when focused).
  - **A kept relation** shows as *you compared these: different notation*, the learner's own record.
  - **Read sections** carry *read* when the learner has read them (a reading fact, never `●`).
  - **No line carries a model-written pair relation.** The index has none: pair relations stay on demand in `compare_sources` (`c`).
  - **One section under several shared LOs** shows once, under its first LO in the API's order, with *also: the characteristic polynomial* on focus.
- **Keys:** `↑↓` move, `Space` peek, `↵` go there, `s` side by side, `c` compare (pins both sections' passages into `compare_sources`, as the curriculum spec's §6.4 says, and opens §5's table), `Esc` folds it back to one line. `x` joins the Reader's single keys (`w`, `[`, `]`, `\`): it is off while the intent box shows or a text field has focus, and CA5 checks it against the PDF surface's and `LiveMarkdownEditor`'s bindings.
- **Corrections** (curriculum §6.5), in each line's `⋯`: *not about this* (one key; the line goes, with *undo*) and *also about…* (a one-line box: *this is really about orthogonal projection*). The curriculum spec resolves and records them as `learner` rows. *ⓘ where this goes* reads *"Tells LearnLoop which sections treat what, so these lines get better. It isn't read for gaps in your understanding — and never grades you."*
- **Off switch on the element:** the block's `⋯` has *hide for this book · hide everywhere* (U13). Hidden leaves nothing behind. Settings brings it back.
- **Skim mode:** shown. Skim mutes what LearnLoop says about the learner and the text (marks, reconnects, quick checks). This line is a table of contents, and skimming across books is exactly what it serves (§15 Q8).

**A section with no coverage yet** (the curriculum spec builds coverage on demand, per deliverable, plus an owner-run `learnloop curriculum cover`). Here `reader.correspondents` returns live `search_spans` hits per source, labelled unchecked, with no model call and no write. Those hits never appear on their own. The Guide's footer has a pressed action, *find this section in my other books ▸* **[CA5a]**, which calls the same API and lists the hits in the same layout. They are grouped by book instead of by LO, and each line reads *found by search, not checked*, without a treatment. *Not about this* works on them too (it is a correction like any other). The action isn't shown for a section that already has its one-line entry.

### 6.3 Peek and jump

- **Peek** (`Space`): the section opens in the right side, as a library hit's peek does today (UX §4.5), scrolled to the API's `jump` locator with the first blocks outlined. The detour strip gains `› peek Axler §5.A`. `Esc` closes it and returns focus to the line it came from.
- **Go there** (`↵`): the left pane navigates to the `jump` locator. The return stack records a `source` entry with the origin passage, the strip shows `↩ Strang §6.1 ¶4 › Axler §5.A`, and `Alt+←` returns to ¶4 with its selection. Arriving shows nothing extra: no reconnect line, because the learner didn't leave a question behind.
- **From the other side:** correspondence is a join on the LO, so it is symmetric. After a jump, the new section's *also in your books* lists the origin section, so going back and forth by meaning doesn't depend on `Alt+←`.
- **A plan's reading block:** jumping to another book during a plan's reading block keeps the plan banner (shell §7.3). The banner's *Back to today's plan* is unchanged, and the plan's section is the stack's root.

### 6.4 Side by side **[CA6]**

- **Entry:** `s` on a corresponding section, `Ctrl+\` from reading (it opens the first correspondent in the API's order), or *read side by side* in a peek's header. It is a variant of the comparing posture, so it pushes a crumb: `↩ Strang §6.1 › side by side with Axler §5.A`.
- **Layout:** two source panes, each with its own small header (*§ Strang · §6.1* / *§ Axler · §5.A* plus *✕*). The rail folds to its 28 px gutter (`\` reopens it as an overlay at the right). The two panes together are the source area, so U2's "source ≥ 60%" holds. The split is resizable and remembered per device. `F6` moves focus between the panes. `Ctrl+\` or `Esc` closes the second pane, and the first returns to its full width at the same position.
- **Follow along** (default on, §15 Q14). It has a toggle in the second pane's header, *follow along ●*, and a key, proposed as `Ctrl+Shift+L` and checked for clashes.
  - **The leading pane** is the one the learner last scrolled, clicked or selected in. The other pane follows.
  - **The following pane moves only when the leading pane crosses into a new section.** It moves to the first of the follower book's correspondents for that section (`reader.correspondents`, the API's order), at its `jump` locator, once, with no animation (instant under reduced motion). Mid-section scrolling in the leader moves nothing. That is C5's test. Only judged coverage moves a pane, never an unchecked search hit.
  - **Section level only.** The index pairs sections, not paragraphs, so there is no paragraph alignment and no gutter glyph in v1. Line-level sync would jitter anyway, and the books' paragraphs don't correspond one to one. Paragraph anchors would be the curriculum spec's to add, and its deferral list holds the related *precomputed section × section relation index*.
  - **With no correspondent** for the new section in the follower's book, the follower stays where it is. Its header reads *no matching section here · stays put*, dim, until the learner moves it.
- **Everything else works in both panes.** Selecting in either pane shows the intent box (UX §4.1). *How do my other books treat this?* on a selection in one pane names the other pane's book as the source (§4.1). Margin marks follow the density setting per pane, as if each pane were the reader alone. Notes and highlights go to their own book.
- **Narrow windows** (below 1,040 px): side by side isn't offered. `s` and `Ctrl+\` peek instead, in the sheet UX §3.1 uses, with one dim line, *side by side needs a wider window*.

### 6.5 The attention budget, extended

UX §4.12's table gains two entries in *allowed, quietly, and only these*:
- the Guide's one-line *also in your books*, static, only when judged coverage exists for the section;
- in side by side, which the learner opened, the following pane's move at a section crossing.

What this design never does, in addition to UX §4.12's list:
- **a correspondence mark in the text column** (§15 Q9);
- **a count of matching sections or books**;
- **unchecked search hits shown unasked**;
- **an offer to compare, or a correspondence line, while the learner is in the working posture** (the Guide is folded into the workbench's `⋯` there anyway);
- **any correspondence that points into exam material.** The curriculum spec reads coverage and correspondents only through `exam_withheld`, `reading_held_back` and `spans_withheld` (its §9, gate G-C1), and the presentation adds nothing that could bypass them. A section in an exam source is never listed, peeked or paired. Exam questions are never taught.

**Records:** peeks, jumps and side-by-side sessions are `reader_action_invoked` events with `event` = `corresponding_section_peeked`, `corresponding_section_opened`, `side_by_side_opened`, or `follow_along_moved` (salience only, spec §4.3). The detour return rate (UX §9.2) covers jumps with no new measure.

---

## 7. Ask, overhauled **[CA2; bug-fix stage first]**

### 7.1 One component, three hosts

There is one **Ask panel**: a thread, a box, a context line, the help style, and the states of UX §4.0. It appears in three hosts and behaves the same in each.

| Host | Where the panel sits | What changes from today |
|---|---|---|
| **The Reader** | The rail's Ask tab, as today | The *mode* select becomes the help style (§7.4). `↵` sends (`Ctrl+↵` still works). Threads keep RW1a's tree, statuses and reconnect. Reader inquiries are durable threads about a passage, not attempts, so §7.3's per-attempt rule doesn't apply to them. |
| **The practice screen** (answer box) | **Docked**: a column at the right of the question and answer box, 360 px, resizable, remembered. Below 1,040 px it becomes a sheet over the lower half, with the stem pinned above. | Replaces `AskOverlay`'s modal for practice and feedback, so the question and the draft stay visible while asking. The library and capture contexts keep the overlay until a later phase moves them (§13). |
| **The workbench** (Reader working posture, and Work in Steps on the practice screen) | **Inline, under the focused step**, like a hint (§7.6). The whole-problem box sits at the foot of the steps. The attempt's thread opens from the footer's *help so far ▸* in the help column. | Ask exists. The working posture no longer says *"Ask the tutor is beside the book. Leave for now…"*. |

**The panel's parts, top to bottom:**
1. **The context line**: what the answer will see, in words, each part a chip with `×` for this question only: *about › Exercise 6.1.12 · your draft · § Strang §6.1 (open)*; in the workbench, *about › step 3 · your steps 1–4 · the last check*; in the Reader, *about › your selection in §6.1 ¶4 · this thread*. *ⓘ what's sent* opens the plain list (shell §4.3's *details ▸*). Removing *your draft* sends the question without it. The chips are the context, not filters on retrieval: the server still derives policy and retrieval from the call (sources §5.2).
2. **The help style**: *help style: balanced ▾* (§7.4).
3. **The thread**: this attempt's exchanges in order, each an exchange as in UX §4.2: *›* the question, then the answer in book-first order (§7.8). It is empty at the start of every attempt (§7.3).
4. **The box**: *ask in your words* (on a cold check, §7.7's placeholder), `↵` sends, `Shift+↵` new line, `$math$` renders. Under it, one dim line says the cost before sending: on an item, *a question about the maths counts as a hint · asking what the question means doesn't*. That is the existing rule, said plainly: the tutor model's `question_type` on its answer, where `prerequisite`, `mechanism` and `strategy` count and `clarification`, `verification` and `other` don't (`HINT_EQUIVALENT_TYPES`). After the answer lands, its label says which it was: *counts as a hint* or *a clarification · free*. It never says *N left*. The question budget is a money bound, and it shows only as UX §4.0's capped state.
5. **The foot**: *earlier on this question ▸* when there are earlier threads and no cold check (§7.3).

**Keys, the same in every host:** `?` (outside a text field) opens the panel with the box focused. In the workbench, `?` asks about the focused step. `↵` sends, and `Esc` closes the panel, returning focus to where it was. In the Reader, `?` with a selection keeps focusing the intent box (UX §3.5), so asking about a selection still goes through the box.

### 7.2 What the answer is about, in the workbench and in practice

- **Practice (answer box):** the question, the learner's current draft (read from the checkpoint at send), the attempt's earlier help (hints and exchanges in order), the item's LOs. It is the practice-context tutor of hints §4.1's H4, which reads the draft.
- **Workbench (steps):** the steps with their numbers, the focused step, the last check's verdicts, the book's visibility, and the attempt's earlier help. A question about a step is answered about that step, and the answer quotes it in the learner's voice (U3).
- **Feedback:** the attempt just submitted, as today (keyed by attempt).

### 7.3 A fresh thread every attempt

- **The rule (C6):** on an item, an Ask thread belongs to **one attempt-in-progress**, keyed by the attempt's submission id, the same key the hint service already counts by (`SC/hints.py:178-181`). A new serve of the item has a new submission id. It opens with an empty thread, an empty hint list and an empty help footer (bug-fix B3, with B4's checkpoint release). Feedback Ask stays keyed by attempt id. Reader inquiries are unchanged (they aren't attempts).
- **Earlier threads are browsable and never current.** *earlier on this question ▸* opens a list by date. Each entry gives its date and how that attempt ended, in the evidence vocabulary: *Tue 14 Oct · solved with help ◌*, *Sat 4 Oct · on your own ●*, *Thu 2 Oct · left unfinished*. Opening one shows its exchanges read-only, under a dim header: *from your attempt on 14 Oct — not part of this one*. Hints that attempt took show the same way, under their own label. No earlier thread's text enters the model context of a later attempt (§11 K6). What carries over is what the learner model already knows: the facet's history, read by the hint chooser and the tutor as state, never as text to repeat.
- **Its cost, before Submit.** Rereading last time's help is help, so *earlier on this question* says what opening it costs before it opens: *earlier on this question ▸ · opening one counts as a hint*. It is recorded as one hint-equivalent (`hints_used` += 1), the same rule as the book left open (spec §5.4). After Submit it is free, and the feedback screen offers it plainly (*your earlier attempts ▸*). The owner decided this rule on 2026-10-25 (§15 Q2).
- **During a check on your own:** absent, both the link and any hint carried from before (U11: a cold check shows nothing from before). After feedback it appears.
- **What "reattempt" means.** Every new serve of the item counts: the plan serving it again, *practice this* choosing it, a guided redo, a resumed Work-in-Steps session's **next** attempt. Resuming the **same** unfinished workbench session is not a reattempt. Its steps and help are the same attempt, so they come back (UX §5.3, `workbench_help_state`), with its thread.
- **Carried hints** between the answer box and steps (`carriedHints`, today's *hints-carried* banner) stay: they are the same attempt moving between two answer surfaces.

### 7.4 The help style, visible and effective

- **Visible on every help surface:** the Ask panel's header, the practice hint panel's header (today it is only in the `⋯` menu and Settings), and the workbench header (exists). It is one control, *help style: let me struggle · balanced · guide me*, one stored preference (`hints.help_style`). The workbench header still overrides it for one problem (spec D31), and says so: *for this problem*.
- **It changes what both doors serve:**
  - **Hints:** the chooser and the writer already read it, and the fallback will (bug-fix B2).
  - **Ask:** the style **is** the answer mode, one vocabulary instead of two:

    | Help style | Ask answers by… | Label on the answer | The Reader's old mode |
    |---|---|---|---|
    | *let me struggle* | asking you first: a question back, or the smallest pointer | *asking you first* | `ask_me_first` |
    | *balanced* | helping you reason: the idea and the next question | *helping you reason* | `help_me_reason` |
    | *guide me* | answering directly, inside leak control | *answering directly* | `answer_directly` |

    The Reader's per-source mode select (`reader_set_answer_mode`) retires into this control (§15 Q5). For one question, *change* under the box picks another mode (*answer directly this time*), and the answer's label says which mode it used.
- **The style never blocks anything.** Every rung and every mode stays available (U4, U10).

### 7.5 Ask and hints: one ladder, two doors

**Decided (§15 Q1, 2026-10-25): one help record and one ladder, with two ways in.**
- **Two doors.** *Hint* (`Ctrl+H`, the ladder in the workbench) is help LearnLoop chooses for your work. *Ask* (`?`) is help in your own words. Both stay, because the learner sometimes knows what they need and sometimes doesn't.
- **One record.** Every check, hint, question and answer taken on the attempt lands in the attempt's **help footer**, in order and each with its cost: *help used: a check · a question (counts as a hint) · a hint (L3)*. The help column (workbench) and the docked panel (practice) list the same items. The server counts them as it already does: hints and checks at levels 1–3 add to `hints_used`, worked help sets `primed`, and hint-equivalent questions fold in at Submit (`tutor_qa.py:1166-1186`). §11 K8–K9 pin that one surface never shows a different total from another.
- **One ladder.** The five rungs measure how much of the solution the help does (spec §5.4), whichever door it came through:
  - A **strategy question** (*how do I go on?*, *what should I try?*) is answered by the hint service as a hint of a chosen kind (hints §4.1, H4). It lands where a hint lands, labelled *◇ model · the next step · answering your question*, and counts as that hint.
  - A **question about the idea** (*why is a polynomial's root an eigenvalue?*) is answered by the tutor in book-first order (§7.8). It counts as a hint when the tutor's `question_type` says it is substantive (a prerequisite or a mechanism), as today. A **clarification** (*what does this symbol mean?*) or a verification is free. The box said so before it was sent (§7.1), and the answer's label says which it was.
  - **Who decides is always a model, with a receipt.** The tutor's `question_type` is its judgment, written on the question event with the answer's model and prompt version. Recognizing a strategy question to hand to the hint service is H4's (hints §4.1). Where that needs a judgment before answering, it is a model's typed choice logged in `judgment_ledger`, never a word list. If the CA2 agent finds a receipt lacks model or prompt version, it adds them to the event payload (no migration).
  - **A request for the answer** (*just show me*, *what's the final matrix?*) is never served as worked help on the spot. The answer is the ladder's take step, inline in the thread: *That's worked help ◌ — ↵ work a piece of it for me · show me the worked answer · or ask something smaller*. Taking it is the ladder's rung 4 or 5, recorded as such. Leak control applies to every Ask answer at levels 1–3, as for hints (hints §4.6).
- **Why not two ladders.** Two ladders would put two totals on one attempt and let the learner reach worked help through whichever door is less guarded. The owner's "hints and Ask reset together" is easier to keep with one record.

### 7.6 Ask in Work in Steps

The bug-fix stage makes Ask work in steps mode: `?` outside a text field, the palette and the key bar all reach it, and it sees the steps. This document designs what the learner sees once that works.

- **`?` on a focused step** (not while typing in it) opens a one-line box **under that step**, where a hint would sit, with the context line *about › step 3 · your steps 1–4*. `↵` sends. The answer lands under the step:

  ```
  3 › λ is a root of det(A − λI) = 0
      › why can I assume λ is real here?
      ◇ model · your question · about step 3 · helping you reason · counts as a hint
      § from the book · Strang §6.4: "…"
      ┊ For a symmetric matrix the book shows every root is real; your A is symmetric,
      ┊ so your step stands. Does your step 4 use that?
      ┊ ask follow-up · this doesn't connect to my work… · show in the book ▸
  ```

- **A question about the whole problem** goes in the box at the foot of the steps, *ask about this problem*, and its answer lands in the help column's thread.
- **Hints and Ask share the step.** An answer and a hint under the same step stay in the order they were taken. *This doesn't connect to my work…* works on an answer as on a hint: the next answer moves, shrinks, keeps the learner's route or their symbols (UX §5.7).
- **The Reader's working posture:** the same. Asking about a step no longer means leaving the problem. Asking about a passage of the book beside it is *?* in the book pane with a selection (the intent box), and the answer lands in the help column, labelled *about the book: Strang §6.4 ¶2*, so the rail never has to come back.
- **The key bar** advertises *? ask about this step* in steps mode, and only when it works.

### 7.7 Cold checks: never blocked, honest about the change

- **Ask is always reachable** (U11, P3 §11, C9). On a check on your own, opening the panel shows nothing from before: no earlier threads and no carried hints. The box's placeholder reads *ask in your words — a question about the maths makes this practice with help ◌; asking what the question means doesn't*.
- **Today's rule decides what converts** (owner decision, §15 Q3). Only a **substantive** question makes a check on your own practice with help. Substantive means the existing classification: the tutor model's `question_type` on its answer is `prerequisite`, `mechanism` or `strategy` (`HINT_EQUIVALENT_TYPES`). A **clarification** (what a symbol or a word in the stem means), a verification (*am I right?*, which the tutor deflects) or anything `other` leaves the check as it was. The judgment is the model's, written on the question event with its model and prompt version as its receipt (§7.5), never a hand list of words.
  - **After a substantive question,** it is recorded as a hint-equivalent (the existing fold). The banner changes from *A check on your own…* to *Practice with help ◌ — you asked about the maths*, the answer's label says *counts as help*, and the attempt's record line says the same at Submit.
  - **After a clarification,** the answer is labelled *a clarification · still on your own* and the banner doesn't change.
  - **A clarification's answer is still checked for leaks.** If its text overlaps the key, the existing reveal row (`tutor_answer`, with its overlap) is written as for any tutor answer, and the reveal-aware rules apply exactly as they do today. The classification only decides the hint count; it never hides a reveal.
  - **The Reader's bound cold Ask follows the same rule.** Today it counts whatever its type (`tutor_qa.py:855-867`), so one rule now covers both cold paths. The CA2 agent checks whether this changes an existing attempt's classification (§13's successor ruling).
- **The Hint door** keeps DL2's take header (*"Taking any help makes this attempt practice with help, not a check on your own."*). Any hint converts the check: a hint is help by construction. The Ask door's placeholder states its own rule in the same plain words.
- **`cold_retry` and certification probes** today say *"No hints on this one: it's a check on your own."* and withhold hints. That contradicts U11. This design replaces it with the same take step as every other cold check (§15 Q4). Taking help converts the attempt, so the measurement stays honest and nothing is withheld.
- **Diagnostic blocks** keep today's refusal of the tutor until the block ends (hints §4.8). The panel says so in one line: *Ask opens after this short set · your question is kept*, and it keeps a typed question for then.
- **After feedback,** Ask works as on any feedback screen, and *earlier on this question* appears.

### 7.8 Where answers cite sources

- **Book first, on every host** (UX §4.2's order, now everywhere, not only in the Reader): *§ from your books* (a verified excerpt, when one answers directly), then *◇ LearnLoop's explanation* with citation chips, then *◇ connecting it to your work* (when the learner has work or an open question on this; it quotes it). When nothing verified is kept: *Your books don't cover this directly — this is LearnLoop's model's explanation*.
- **Citation chips** are `§` buttons naming book and locator, *§ Strang §6.4 p.312*. `Space` or a click peeks the passage (in the Reader's source pane; on the practice screen, in a sheet over the panel, the page rendered as `OpenInSource` does). The peek pushes a crumb in the Reader and returns focus on `Esc`.
- **Policy decides what can be cited**, derived on the server (sources §5.2). During practice it is `assisted_practice`: the item's own solution, its exercise block and the passages the answer-overlap filter catches are never cited. A cited passage overlapping the key writes the existing reveal row (`source_review`), as today.
- **Exam material** is never cited, excerpted or retrieved for teaching (A8).

### 7.9 States

UX §4.0's seven states, in the thread, with the learner's question kept in every one. T1's plan-down line is the same as §4.2's: *ChatGPT plan isn't answering right now · use OpenRouter for this question? ▸*, keyed by the origin RPC method, and offered because the learner pressed send. A switched-off Ask (`reader_tutor` off, or the practice tutor switch) removes the door and its key-bar entry entirely (U13).

---

## 8. The problem as printed **[CA1]**

### 8.1 Where *original page ↗* goes

The UX doc already promises *original page ↗* in the workbench header (UX §5.1) and after a cold check's feedback (UX §4.6, §4.9). The code renders it nowhere for practice items (§3). This phase puts it, and the inline crop, everywhere a problem that came from a page is shown:

| Surface | Before Submit (not a cold check) | During a check on your own | After feedback |
|---|---|---|---|
| Practice screen header | *From Strang · Exercise 6.1.12 · p.297 · original page ↗* and *▸ as printed* under the stem | *from Strang · verbatim* only (D46): no number, page, link or crop | the full locator, *original page ↗* and *▸ as printed* |
| Work in Steps / the Reader workbench header | *WORKING · Exercise 6.1.12 · from the book, verbatim · original page ↗* (hidden while the book is hidden, UX §5.1), *▸ as printed* under the stem | as the practice screen | as the practice screen |
| Feedback | the header gains the locator and both controls; *compare methods* (RW2c) shows the book's solution as text and, when it came from a page, *▸ the solution as printed* | — | — |
| Reader exercise candidates (RW4b) | *open in the book ↗* (exists) plus *▸ as printed* | — | — |
| The phone | none in v1 (§8.5) | none | none in v1 |

### 8.2 *As printed*: the inline crop

- **What it shows:** the item's own blocks, cropped from the page, through the existing `reader.block_original_region`. For an exercise, that is its `canonical_exercise.span_ids` resolved to blocks with their `page` and `bbox`. One crop per page, in reading order, when the exercise crosses a page. The crop is the union of the exercise's own boxes, with no neighbouring exercise, solution, hint section or worked example (C10). Any padding is a rendering margin inside the union of those boxes, not a constant that reaches into another block.
- **What it looks like:** collapsed by default to one line under the stem, *▸ as printed (Strang p.297)*, remembered open or closed per device. Expanded, the image sits at the stem's width, with a thin `§` rule, the book's voice: the page is the book's. Its alt text is the transcribed stem, so a screen reader hears the same problem. `+` / `−` zoom inside the frame. The image is never re-run through OCR in the UI.
- **Why it's there** (the owner's case): OCR and transcription make mistakes in subscripts, signs and figures. *As printed* lets the learner check the problem against the book without leaving it. If they differ, the existing *this question is wrong* (practice `⋯`) gains a first option, *the transcription doesn't match the page*. It carries the learner's optional text and records what it does today.
- **Cost:** none. The crop is the problem itself, not help (§11 K15). It records no exposure, because it shows only the stem the learner already has.

### 8.3 *Original page ↗*

- Opens the whole page in `OpenInSource`'s page view, with the exercise's boxes outlined, and *open in the Reader ↗* from there.
- **Before Submit** it is a source opening during practice (spec §5.4), so it records the exposure. It costs what the book left open costs, one hint-equivalent, and the label says so first: *original page ↗ · counts as a hint* (§15 Q12). After Submit, it is free and unlabelled.

### 8.4 Per import path

| Path | *As printed* shows | Status of the data |
|---|---|---|
| PDF via Marker, pypdf or Datalab | the exercise's blocks, cropped | page and bbox per block exist (`032_source_layer.sql:70-77`). The item DTO must carry them (§12.4) |
| PDF via GLM-OCR (scans) | the same; this is the owner's main case | the same; GLM's boxes are mapped to PDF points (`glm_ocr.py:20-27`) |
| A textbook exercise imported from a selection (RW4b, RW2a) | the same, from its spans | spans exist; region selections (`ReaderSelection.region`) should also store their sub-box, so a crop drawn by the learner is the crop shown (§12.4) |
| A phone photo (the capture inbox, written into a card) | *▸ your photo*, the stored photo, whole | the photo is in the originals store; the item has no link back today (the link is one-way, capture → result). §12.4 asks for the reverse lookup |
| An image drop-in (specced, not built) | *▸ your photo*, the reviewed crop when the spec's crop step exists | per that spec: the photo is the item's provenance |
| Pasted text, a web page | nothing (no page exists); the source link, as today | — |

### 8.5 The cold rule, and figures

- **Hidden during a check on your own**, both *as printed* and *original page*, because a printed exercise number, a running head or a page number locates the exercise and its solution (D46, spec G61). They appear with the rest of the header after feedback.
- **Figures the problem needs.** Some problems are unanswerable without their figure (*the graph shown*). When the item was imported with a figure block it depends on (an attached `figure` block, or the drop-in spec's `diagram_present`), the figure is part of the stimulus, so it shows during a cold check too: **figure-only**, cropped to the figure block, with no caption, number or page, under the label *the figure, as printed* (§15 Q10). The stem stays the transcription.
- **The phone:** v1 shows neither (no new phone RPC, D20). Showing the crop after feedback on the phone needs `reader.block_original_region` on the allowlist, which is an owner decision (**[CA7]**).

---

## 9. Wireframes

Widths are indicative. `◐` marks pending; `▓` marks a selection.

**X1 — The selection verb and the routed line.** **[CA3]**

```
│    ▓▓ The eigenvalues of A are the roots of its characteristic polynomial. ▓▓            │
│    ┌──────────────────────────────────────────────────────────────┐                       │
│    │ › how do my other books do this?                              │                       │
│    │ → comparing · your passage · Axler · Lay · on: eigenvalues    │  change               │
│    └──────────────────────────────────────────────────────────────┘                       │

    Tab instead:  TRANSFER  where else is this explained? · how do my other books treat this? ·
                            connect it · why it matters
```

**X2 — The ask box, reading named books.** **[CA3]**

```
┌ ASK YOUR LIBRARY ──────────────────────────────────────────────────────────────────────┐
│ › how do Axler and Strang treat eigenvalues                                            │
│ → comparing  [Axler ×] [Strang ×]  + add a book    on: eigenvalues            change   │
│ ◐ finding each book's passages…                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
    unmatched:  → comparing [Axler ×] · "Hoffman" isn't in your library · + add a book
```

**X3 — The table, by point (wide).** **[CA4]**

```
┌ COMPARE · Axler · Strang · on: why eigenvalues exist · differences kept · each line quotes its own book ┐
│ perspectives: [ a geometric view            ]      by point ● · by book ○      keep ⇄      esc back    │
├──────────────────────────────┬──────────────────────────┬──────────────────────────┬───────────────────┤
│ ◇ point                      │ § Axler §5.A p.133       │ § Strang §6.1 p.289      │ › you             │
├──────────────────────────────┼──────────────────────────┼──────────────────────────┼───────────────────┤
│ ◇ existence argument         │ § "…"                    │ § "…"                    │                   │
│   different assumptions      │ ┊ ◇ polynomial in A,     │ ┊ ◇ roots of det(A−λI)   │                   │
│                              │ ┊   no determinant       │                          │                   │
├──────────────────────────────┼──────────────────────────┼──────────────────────────┼───────────────────┤
│ ◇ what's assumed of the field│ § "…"                    │ — not addressed here     │                   │
│   only in Axler              │ ┊ ◇ needs ℂ explicitly   │                          │                   │
├──────────────────────────────┼──────────────────────────┼──────────────────────────┼───────────────────┤
│ ◇ role of the determinant    │ § "…"                    │ § "…"                    │ › Axler's route   │
│   they disagree              │ ┊ ◇ avoided until ch.10  │ ┊ ◇ the main tool        │   generalizes;    │
│                              │                          │                          │   Strang computes │
├──────────────────────────────┼──────────────────────────┼──────────────────────────┼───────────────────┤
│ › a geometric view           │ — not here               │ § "…"                    │                   │
│   only in Strang             │                          │ ┊ ◇ directions A only    │                   │
│                              │                          │ ┊   stretches            │                   │
├──────────────────────────────┴──────────────────────────┴──────────────────────────┴───────────────────┤
│ also discussed in: Lay §5.1 ▸ (+ to add)                                                               │
│ ^↵ ask the tutor about this comparison (answers only from these passages) · practice this ▸            │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ←↑↓→ cells  space peek  o open  ↵ expand  t your take  - hide row  / refine  + book  v layout  k keep   │
```

**X4 — A chip's pairs, with three books.** **[CA4]**

```
│ ◇ role of the determinant    ▾ how LearnLoop reads the relations (AI-written)                      │
│   they disagree · different notation                                                              │
│     Axler ⇄ Strang · they disagree · ◇ one avoids it, one builds on it  § "…" / § "…"             │
│     Strang ⇄ Lay   · different notation · ◇ same step, χ(λ) vs p(λ)     § "…" / § "…"             │
│     Axler ⇄ Lay    · they disagree · ◇ …                                 § "…" / § "…"             │
```

**X5 — Narrow: cards by point.** **[CA4]**

```
┌ COMPARE · Axler · Strang ─────────── by point ┐
│ ◇ role of the determinant                     │
│   they disagree                               │
│ § Axler §5.A                                  │
│   "…"                                         │
│   ◇ avoided until ch.10                       │
│ § Strang §6.1                                 │
│   "…"                                         │
│   ◇ the main tool                             │
│ › you: Axler's route generalizes; Strang…     │
│ ───────────────────────────────────────────── │
│ ↑↓ points  ←→ books  t take  k keep  esc      │
└───────────────────────────────────────────────┘
```

**X6 — The phone: a kept comparison (proposed, CA7).**

```
┌──────────────────────────────┐
│ kept · 3 Oct                 │
│ Axler · Strang               │
│ on: why eigenvalues exist    │
│ ──────────────────────────── │
│ role of the determinant      │
│ they disagree                │
│ Axler §5.A                   │
│ "…"                          │
│ LearnLoop: avoided until     │
│ ch.10                        │
│ Strang §6.1                  │
│ "…"                          │
│ LearnLoop: the main tool     │
│ you: Axler's route…          │
│ [ add your take ]            │
│ ◂ previous point · next ▸    │
└──────────────────────────────┘
```

**X7 — *Also in your books*, collapsed and open.** **[CA5]**

```
│ GUIDE    ask    notes                    │
│ section · 6.1 ━━━━━━━━━──────            │
│ also in Axler §5.A, Lay §5.1 ▸           │   (dim; static; only with judged coverage)
│ ──────────────────────────────────────── │
│ your path · learn to use it   …          │

    after x:
│ also in your books                    ⋯ │
│ eigenvalues of a linear map              │
│  Axler §5.A Invariant subspaces          │
│        introduces it                 ▸  │
│  Lay   §5.1 Eigenvectors and…            │
│        develops it · read            ▸  │
│        ◇ uses row vectors               │
│ the characteristic polynomial            │
│  Lay   §5.2 The characteristic eq.       │
│        develops it · you compared    ▸  │
│        these: different notation         │
│ space peek · ↵ go · s side · c compare  │

    no coverage yet (pressed: find this section in my other books ▸):
│  Axler §5.A Invariant subspaces          │
│        found by search, not checked  ▸  │
```

**X8 — Peek, then the way back.** **[CA5]**

```
┌ READER  ← library  Strang · ch.6                                                         ┐
│ ↩ §6.1 ¶4  ›  peek Axler §5.A                                              alt+← back    │
├──────────────────────────────────────────────────┬───────────────────────────────────────┤
│ (Strang §6.1, ¶4 outlined)                       │ PEEK · § Axler §5.A Invariant subsp.  │
│                                                  │ ┃ (the section's first blocks)        │
│                                                  │ read side by side (s) · go there (↵)  │
│                                                  │ compare with §6.1 (c) · esc close     │
```

**X9 — Side by side, following along.** **[CA6]**

```
┌ READER · side by side                                                                                ┐
│ ↩ Strang §6.1  ›  side by side with Axler §5.A                                       alt+← back      │
├───────────────────────────────────────────────┬─┬───────────────────────────────────────────────┬────┤
│ § Strang · §6.2 Diagonalizing           ✕ lead│ │ § Axler · §5.C  follow along ● (^⇧L)       ✕ │ ⋮  │
│                                               │ │                                               │    │
│   6.2 Diagonalizing a matrix …                │ │   5.C Eigenspaces and diagonal matrices …     │    │
│   …                                           │ │   …                                           │    │
│                                               │ │                                               │    │
├───────────────────────────────────────────────┴─┴───────────────────────────────────────────────┴────┤
│ F6 other pane  ^⇧L follow along  select ask·act  ^\ close side by side  \ rail                        │

    the follower moves only when the leader crosses into a new section (to its first correspondent)
    no correspondent for the new section:   § Axler · §5.C · no matching section here · stays put
```

**X10 — Ask on the practice screen, docked, at the start of a reattempt.** **[CA2]**

```
┌ PRACTICE · Today's plan                                           linear algebra  ⋯ ┐
├───────────────────────────────────────────────────────┬────────────────────────────┤
│ From Strang · Exercise 6.1.12 · p.297 · original page ↗│ ASK                    esc │
│ · counts as a hint                                     │ about › Ex 6.1.12 ×        │
│ Find the eigenvalues of …                              │         your draft ×       │
│ ▸ as printed (Strang p.297)                            │ help style: balanced ▾     │
│ ┌────────────────────────────────────────────────────┐ │ ────────────────────────── │
│ │ write what you can — $math$ works                   │ │ (nothing asked yet on     │
│ └────────────────────────────────────────────────────┘ │  this attempt)             │
│ [ Submit ^↵ ]  Hint ^h · I'm stuck · Ask ? · Skip       │ ┌────────────────────────┐ │
│ help used: nothing yet                                 │ │ ask in your words       │ │
│                                                        │ └────────────────────────┘ │
│                                                        │ a question about the maths │
│                                                        │ counts as a hint           │
│                                                        │ earlier on this question ▸ │
│                                                        │ · opening one counts as a  │
│                                                        │   hint                     │
├───────────────────────────────────────────────────────┴────────────────────────────┤
│ ^↵ submit  ^h hint  ? ask  ^d stuck  esc today                                     │
```

**X11 — Ask in Work in Steps, under a step.** **[CA2]**

```
┌ WORKING · Exercise 6.1.12 · from the book, verbatim · original page ↗   help: struggle ·[balanced]· guide ┐
│ Problem  § "Find the eigenvalues of …"                     ▸ as printed (Strang p.297)                     │
│ Your work                                                                       saved · just now          │
│  1 › det(A − λI) = 0                                                             ≈ model's reading         │
│  2 › (2 − λ)(3 − λ) − 2 = 0                                                      ✓ checked                 │
│  3 › λ is real because …                                                         · not checked             │
│      ┌ about › step 3 · your steps 1–3 ──────────────────────────────────────┐                             │
│      │ › why can I assume λ is real here?                                   ↵ │                             │
│      └ a question about the maths counts as a hint · what the question means doesn't ┘                      │
│  4 › _                                                                                                     │
│ ^k check my work (a hint)  ^h help  ? ask about this step  ^d I'm stuck                       ^↵ submit   │
│ help used: a question (counts as a hint)                             help so far ▸   esc leave · ⋯        │
```

**X12 — Ask during a check on your own, then after feedback.** **[CA2; DL2]**

```
┌ PRACTICE · check · on your own · about 6 min                                                         ┐
│ ┃ A check on your own. Help is still here — using it makes this practice with help.                 │
│ from Lay · verbatim                                                                                   │
│ …                                                                                                     │
│                                                   ┌ ASK ─────────────────────────────────────────────┐ │
│                                                   │ about › this check · your draft                  │ │
│                                                   │ ┌──────────────────────────────────────────────┐ │ │
│                                                   │ │ ask in your words — a question about the      │ │ │
│                                                   │ │ maths makes this practice with help ◌; asking │ │ │
│                                                   │ │ what the question means doesn't               │ │ │
│                                                   │ └──────────────────────────────────────────────┘ │ │
│                                                   │ esc keep it on my own                            │ │
│                                                   └──────────────────────────────────────────────────┘ │

    after a question about the maths:   ┃ Practice with help ◌ — you asked about the maths
    after a clarification:              ◇ model · a clarification · still on your own   (banner unchanged)
    after feedback:  Exercise 4.22 · Lay p.214 · original page ↗ · ▸ as printed · why this check ▸
                     earlier on this question ▸
```

**X13 — The problem as printed.** **[CA1]**

```
│ From Strang · Exercise 6.1.12 · p.297 · original page ↗ · counts as a hint                  │
│ Find the eigenvalues of the matrix …   (the transcription)                                  │
│ ▾ as printed (Strang p.297)                                                     − +        │
│ ┃ ┌──────────────────────────────────────────────────────────────────────────────────┐     │
│ ┃ │  (crop of the exercise's own blocks from the page image; nothing around them)    │     │
│ ┃ └──────────────────────────────────────────────────────────────────────────────────┘     │
│   doesn't match the page? ⋯ → the transcription doesn't match the page                      │

    cold check:  from Strang · verbatim            (no locator, no crop, no link)
    cold check, figure needed:  ▸ the figure, as printed   (figure block only, no caption)
    photo item:  ▸ your photo (4 Oct)
```

**X14 — Waiting and failure, in place.** **[all]**

```
│ ◐ finding each book's passages… then lining them up                         cancel  │  compare, pending
│ ◇ Couldn't line the books up. Their passages are below — try again ↵                 │  compare, failed (excerpts kept)
│ ◇ ChatGPT plan isn't answering right now · use OpenRouter for this comparison? ▸    │  plan down (T1, redesign D)
│ ◇ Today's comparison budget is used. The passages are still here ▸                  │  capped
│ › why can I assume λ is real here?                                                   │
│ ◐ looking in your books… then writing                                        cancel  │  ask, pending
│ ◇ Couldn't reach LearnLoop's model. Your question is kept — try again ↵              │  ask, unreachable
│ ◐ cropping the page…                                                                 │  as printed, pending
│ the page image isn't available for this book · the transcription is above            │  as printed, no original
```

---

## 10. What changes against today

| Area | Today (`main` at `fa2eb72f8`) | With this design | Phase |
|---|---|---|---|
| Starting a comparison | Pin passages from at least two books, then *compare pinned* | Four doors, no pins needed: the selection verb, the ask box in natural language, the tutor's offer, *compare these books* in an answer. Pins remain | CA3 |
| Naming books | Not possible; names are search text | *comparing Axler · Strang · on eigenvalues*, read by the `compare_scope` Decider task, with chips, `×` and *+ add a book* | CA3 |
| Table orientation | One stacked row per source; *contributes · assumes · differs* | Row per point, column per book; *by book* as a toggle and as the layout for v1 comparisons | CA4 |
| Relations | A separate band under the table; in the table they only pick a cell | Chips on each row in plain words; pairs on focus; the band moves into the rows | CA4 |
| Your take | A box under the table with an *about* select | A *› you* column, one take per row, plus a table-level take | CA4 |
| Perspectives | Comma list; *perspectives:* / *not found* lines | Each one a row in the learner's words; *not here* per book; *not found in your library* per row | CA4 |
| Refining | Re-ask in the box | `/`: views or books, in words; *previous ▸* keeps the earlier table | CA3, CA4 |
| Narrow widths | No stacking below 1,040 px; width fixed at mount | Stacks, then cards by point; re-clamps on resize | CA4 |
| Table keys | `↑↓` hits, `Space`, `p`, `o`, `c`, `Ctrl+↵` | A full grid map (§5.5); the old keys keep their meanings | CA4 |
| Phone | No comparisons | Proposed: kept comparisons by point, read-only plus *your take* | CA7 (owner trigger) |
| Cross-book sections | Nothing | *Also in your books* in the Guide; peek, go there, compare | CA5 (index), CA5a (fallback) |
| Reading two books | One source pane; peeks only | Side by side with follow along | CA6 |
| Practice Ask | A modal overlay over the question | A docked panel; the question and draft stay visible | CA2 |
| Ask in Work in Steps | Absent; the key bar advertises it anyway | Ask about the focused step, inline under it; a whole-problem box | Bug-fix (works) → CA2 (presentation) |
| Ask in the Reader's working posture | *"Leave for now… and Ask opens"* | Ask about a step inline; about the book through a selection | CA2 |
| Thread per attempt | Practice thread per (item, session): reattempts reuse it | Per submission id; earlier threads under *earlier on this question*, read-only, dated, never in context | Bug-fix (reset) → CA2 (browse) |
| Hints on reattempt | Restored from the checkpoint; stale offer on submit | Empty on a new serve; checkpoint released; stale offer still grades | Bug-fix |
| Help style | Settings and the hint `⋯` menu; the Reader has a separate mode select; the fallback ignores the style | Visible on every help panel; drives hints and Ask's mode; one vocabulary | Bug-fix (fallback) → CA2 (visible, Ask mode) |
| Ask and hints | Separate panels, separate counts on screen | One help record and one ladder, two doors; requests for the answer go through the take step | CA2 |
| Cold checks and Ask | Ask's cold consequence isn't said before sending; practice counts only substantive questions while the Reader's bound cold Ask counts every question | One rule on both paths (owner, Q3): substantive questions convert and clarifications don't, judged by the tutor's `question_type` with its receipt; the placeholder says so before sending, and the answer's label and the banner say what happened | CA2 (§15 Q3) |
| `cold_retry` "No hints on this one" | Hints withheld | The same take step as every cold check | CA2 (§15 Q4) |
| Citations | Reader: book first; practice overlay: a "sources:" chip row | Book first on every host; `§` chips peek in place | CA2 |
| Original page | Not rendered for any practice item; crop RPC unused | *Original page ↗* and *▸ as printed* on practice, workbench, feedback and candidates; hidden during a cold check; figure-only exception | CA1 |
| Photo items | No link back to the photo | *▸ your photo* | CA1 |
| Transcription errors | *this question is wrong* | Plus *the transcription doesn't match the page* | CA1 |

---

## 11. Behaviour contracts the code must honour

**B** = the bug-fix stage on `fix/owner-capture-1025` (in flight; this design assumes it lands first). **N** = new work in this document's phases. Each contract names its test's home.

| # | Contract | Owner | Test |
|---|---|---|---|
| **K1** | **Ask works in Work in Steps** on the practice screen: `?` outside a text field, the palette and the key bar reach it, and the request carries the workbench session (steps, focused step, last check). The key bar never advertises an Ask that doesn't work. | **B** | vitest on PracticeScreen steps mode; sidecar test that the request binds the session |
| **K2** | **The help style changes the fallback:** under *let me struggle* and *guide me* on the same state, the deterministic fallback serves different kinds or levels as hints §4.5 describes. | **B** (B2) | `test_owner_capture_1025.py` |
| **K3** | **An attempt starts clean:** a new serve of an item (new submission id) shows no hint, Ask exchange or help footer from an earlier serve, and none of them enters its model context. | **B** (B3) | sidecar + vitest |
| **K4** | **A steps submit releases the answer box's checkpoint,** and a stale or consumed scheduler offer never fails a submit: the attempt is graded, unattributed (`scheduler_candidate_id` NULL). | **B** (B4) | `test_owner_capture_1025.py` (fail-first tests exist) |
| **K5** | **The thread key** on every item host is the attempt's submission id (practice answer box, Work in Steps, a Reader workbench session bound to an item); feedback stays per attempt id; Reader inquiries are unchanged. ~~The question budget is a money bound per day, and its window doesn't reset per serve.~~ **Owner decisions 2026-10-26:** the practice question budget stays **per attempt** (owner capture B3's rule): each attempt gets its own `max_questions_practice`, counted over its thread, on a **metered** route; the **subscription** route (the ChatGPT plan) stays **unlimited** (no request bound, Codex review F8's rule). | **N** (CA2), building on K3 | sidecar |
| **K6** | **Earlier threads are read-only and never current:** listed by date with the attempt's outcome; absent during a cold check; opening one before Submit records `hints_used` += 1, said first; free after Submit. | **N** (CA2; Q2) | sidecar (count) + vitest (absence when cold) |
| **K7** | **One Ask contract for practice and the workbench:** the practice Ask RPC accepts `submission_id` and `workbench_session_id`; the server derives policy (`assisted_practice`, `cold_attempt`); no client-sent policy or count is trusted. | **N** (CA2) | sidecar, extending `test_reader_find_sources_callers.py`'s pattern |
| **K8** | **One help record:** the attempt's help footer on every host lists every check, hint, question and worked help taken, in order; its count of hint-equivalents equals what Submit records. | **N** (CA2) | sidecar (fold) + vitest (footer) |
| **K9** | **Ask never serves worked help without the take step:** an Ask answer at levels 1–3 passes the hint service's leak control; a request for the answer returns the rung 4/5 take step, recorded as that rung only if taken. | **N** (CA2) | sidecar |
| **K10** | **Cold: Ask is never blocked, and only substantive questions convert** (owner, Q3). The box states the rule before sending. A question whose tutor `question_type` is `prerequisite`, `mechanism` or `strategy` makes the attempt practice with help (the existing hint-equivalent fold). A `clarification`, `verification` or `other` question leaves it on your own, and its answer is labelled so. The classification is the model's, with its receipt (model and prompt version) on the question event. The Reader's bound cold Ask follows the same rule. Leak overlap still writes its reveal row whatever the type. Earlier threads and carried hints are absent. Diagnostic blocks keep today's refusal, with the question kept. | **N** (CA2; Q3) | sidecar + vitest. *If the agent finds this changes an attempt's classification beyond the existing hint-equivalent mapping, stop: it becomes a successor (the next free `mvp-0.N`) under the algorithm-change playbook.* |
| **K11** | **Book first on every host:** a verified `§` excerpt when one answers, then `◇`, then the bridge; "your books don't cover this directly" when none is kept; exam material never cited. | **N** (CA2) | vitest (order), sidecar (policy) |
| **K12** | **One comparison request:** every door issues the same RPC with the same payload shape; a selection-started comparison needs no pins; named sources only narrow the scope; the server derives the policy; exam material is withheld (unchanged). | **N** (CA3) | sidecar + vitest (door parity) |
| **K13** | **No merged answer, and cells are quoted or empty:** every cell's quote is verified in code (sources §9.4, unchanged); a cell without one reads *not addressed here*; chips are exactly the relations the comparison returned for the row's pairs. | **N** (CA4) | sidecar (v2 schema has no consensus field) + vitest |
| **K14** | **Correspondence is quiet:** never in the text column, no count, static, absent when empty; a jump pushes a return-stack entry; follow-along moves only the following pane, only at a section crossing, never the last-touched pane; never lists an exam-material section. | **N** (CA5, CA6) | vitest (focus, no animation per G54–G58, leader rule) |
| **K15** | **The problem as printed:** the crop shows only the item's own blocks; hidden during a cold check except the figure-only rule (Q10); *original page* before Submit records exposure and costs what its label said; nothing after Submit. | **N** (CA1) | sidecar (block set, cold refusal) + vitest |
| **K16** | **The UX doc's gates extend to every new component:** no focus move on a result landing, no animation, a voice label on every model text, `--dim` not `--faint` for meaning-bearing copy (spec G54–G58). | **N** (every phase) | the existing lint and vitest gates |

---

## 12. Data, and requests to other specs

### 12.1 To the bug-fix stage (`fix/owner-capture-1025`)

K1–K4, as that stage's own tests define them. Two notes so the presentation can build on them without rework:
- key the practice Ask thread and its stored transcript by the same submission id the hint service counts by (K5 depends on it);
- keep the earlier serves' exchanges stored (they become *earlier on this question*), just not current.

### 12.2 To the Reader and sources specs (comparisons)

- **`reader.library_compare` accepts an anchor without pins** (zero or one pin plus discovery), and **named sources** (`source_ids`, which only narrow the scope; refused if they would widen it, as `policy` is). `compare_sources` gains the same optional `source_ids` (sources §9.4). Exam material stays withheld.
- **A v2 comparison output** (`source_compare.v2`, the same route and one call): a list of **points**, each with a short label, and per source a cell `{quote, line, span_key}` or `not_addressed`; per point, its pairs' relations with statements and quotes, drawn from the **unchanged** `RELATIONS` set (`equivalent`, `different_assumptions`, `different_notation`, `disagreement`, `unclear`; no `complementary`); requested perspectives as points labelled by the learner's words. Quote verification is unchanged. Stored in `source_comparisons.comparison_json` (no migration); v1 rows keep rendering by book (§5.3). `CompareKeep` maps a kept v2 row to the same proposals as today (RW4d's mapping, spec §3.4 item 15), one claim per cell, with the row's label in `content_json`.
- **The four-view bound** (`MAX_PERSPECTIVES`) is a stored-size bound and is labelled a `keep` guardrail in config, not a learned constant.
- **A Decider task, `compare_scope`** (T1 plan-first; a typed choice over the vault's book list, never a chat fallback). Unavailable means "all books, the words as the query" (§4.3). It writes ledger verdicts like `reader_intent` (`decider`, then `learner_card` on *change*), so its error is measurable without a chore.

### 12.3 The companion spec: what the presentation reads from the section correspondence index

The curriculum spec (`spec_deliverable_curriculum_v1.md` §6, commit `5facf66b9`) defines the data and its read API. This document adds nothing to them and reads them as follows:

| The presentation needs | The curriculum spec provides | Used in |
|---|---|---|
| A section's corresponding sections in the learner's other books | `reader.correspondents(extraction_id, section_id)`: per LO, per other source, the sections whose `section_coverage` names the same LO with a treatment other than `not_about` | §6.2's list, grouped by LO |
| How each one treats the shared LO, in plain words | `treatment`: `introduces` · `develops` · `applies` · `mentions` | the line's *introduces it · develops it · uses it · mentions it* |
| An order, with no score on screen | ordered by treatment (`introduces`, `develops` first), then retrieval rank | the list's order; side by side's follower target |
| A short, labelled model note | `notation_md` (the judge's one line), plus `roles_json` | the `◇` notation line; roles in the peek header |
| The learner's own record of a relation | the kept relation, if any (RW4d) | *you compared these: different notation* |
| Where to land | the `jump` locator | peek, go there, side by side |
| Sections with no coverage yet | live `search_spans` hits per source, labelled unchecked, with no model call and no write | CA5a's pressed *find this section in my other books* only (§6.2) |
| Corrections | *not about this* and *also about…* rows (`learner`, curriculum §6.5) | each line's `⋯` |
| Exam and reading protection | reads only through `exam_withheld`, `reading_held_back`, `spans_withheld` (curriculum §9, G-C1) | every surface in §6 |
| Freshness | a changed `state_key` writes new rows, and old rows are no longer read (curriculum §6.1) | nothing stale is shown |

**What the index deliberately doesn't have,** and how this design copes:
- **No pair relation between two sections.** The curriculum spec keeps pair relations on demand in `compare_sources` and in RW4d's keeps. So §6 shows no model-written pair relation, and `c` runs the comparison.
- **No paragraph-level anchors.** Side by side follows at section level only (§6.4).

**Two small requests remain, both on presentation-facing details and neither a new table:**
1. `reader.correspondents` returns the section's own number and title (or ids the client can resolve without a second round trip), so a line can quote the book's heading.
2. It returns, per section, whether it is the same section the call was made from under another extraction of the same source, so a re-extracted book never lists itself.

The names this document uses: *section correspondence index* for the `section_coverage` join, *also in your books* for the Guide line, *side by side* and *follow along* for the paired view.

### 12.4 Items and import paths (original page)

- **The practice item DTO** carries, for an item with `canonical_exercise` (or another span-backed origin), the page and bbox of each of its blocks, plus the figure blocks it depends on. When `locators_hidden` is set, the server sends none of them except the figure-only crop (Q10), so a cold check can't leak them through the DTO.
- **`reader.block_original_region`** gains a multi-block form (one crop per page for a list of blocks), or the caller composes it. It is a read; no model call.
- **Region selections** (`ReaderSelection.region`) store their sub-box on the imported exercise, so a learner-drawn crop is the crop shown.
- **Photo items:** the item can find its capture photo, through a reverse lookup over `capture_routes.result_refs_json` or an indexed column if the phase needs one (that phase's migration, if any).
- **Image drop-in** (when built): the photo is the item's provenance per that spec; *your photo* shows it.

---

## 13. Phases, smallest valuable first

| Phase | What ships | Depends on | Size | Migration |
|---|---|---|---|---|
| **CA0 — the bug-fix stage** (in flight) | K1–K4: Ask in steps works, the help style changes the fallback, attempts start clean, the steps submit releases the checkpoint, and a stale offer grades | — | (that stage's) | (that stage's) |
| **CA1 — the problem as printed** (**first slice**) | *Original page ↗* and *▸ as printed* on practice, Work in Steps, the Reader workbench, feedback and exercise candidates; the cold rule and the figure-only exception; *the transcription doesn't match the page*; *your photo* for capture-photo items | the existing crop RPC and block geometry | **S** | none expected (the photo lookup may want an index) |
| **CA2 — one Ask** | The Ask panel in three hosts (the docked practice panel; inline per step in the workbench; the rail restyled); context chips; the help style visible on every help panel and driving Ask's mode; *earlier on this question*; one help record; the take step for worked help; Ask on cold checks with the take step; book first on every host. Library and capture contexts keep the overlay | CA0 | **M** | possibly a submission-id column on stored tutor exchanges, if they don't already carry one in their payload (K5) |
| **CA3 — compare from anywhere** | The selection verb; *compare these books*; the ask box with `compare_scope`; chips, *+ add a book*; refine (`/`) for books; one request for every door (anchor without pins, named sources) | — | **S–M** | none |
| **CA4 — the table by point** | `source_compare.v2`; the grid, chips, *› you* column, perspectives as rows, hide row, keyboard map, narrow cards, *by book*, v1 rendering, resize re-clamp | CA3 (shares the request) | **M** | none (JSON in `source_comparisons`) |
| **CA5a — find this section in my other books** | The pressed action in the Guide's footer over `reader.correspondents`' unchecked search hits, by book, *found by search, not checked*; peek, go there, compare; *not about this* | the curriculum spec's C0a (`reader.correspondents`; its search fallback needs no coverage) | **S** | none here |
| **CA5 — also in your books** | The one-line Guide entry and its list grouped by LO from judged `section_coverage`; treatment words, notation line, kept relation, *read*; corrections; the off switch | the curriculum spec's C0a, with coverage built for the LOs in question (a deliverable, or `learnloop curriculum cover`) | **S** on top of C0a | none here |
| **CA6 — side by side** | Two panes; follow along at section level from `reader.correspondents` (judged coverage only); narrow fallback to peek | CA5 | **M** | none |
| **CA7 — the phone** (owner trigger) | Kept comparisons by point, read-only plus *your take*; *as printed* after feedback | owner decisions on the allowlist (mobile spec) | **S** | none |

**Why CA1 first:** it answers one of the owner's notes on its own, uses data and an RPC that already exist, changes no evidence semantics outside one stated rule (the page before Submit, Q12), and is useful on every OCR'd problem from the first day. CA2 waits for the bug-fix stage, so it builds on fixed behaviour rather than around it. CA3 is the cheapest way to make comparing easier, and it doesn't wait for the v2 table. CA5a and CA5 wait on the curriculum spec's C0a (`section_coverage` and `reader.correspondents`; that spec's Q15 recommends C0a first when this spec is ready to build). CA5a is usable the day C0a lands, because its search fallback needs no coverage.

**Successor ruling.** None of these changes scoring, scheduling or projections, with two places to check. K6's "opening an earlier thread counts as a hint" maps onto the existing `hints_used` field with its existing meaning (spec §5.4). K10 keeps practice's existing rule, but it changes the Reader's bound cold Ask, which counts every question today, to count only substantive ones (`tutor_qa.py:855-867`). If the CA2 agent finds that either changes an existing attempt's classification in a way the field doesn't already express, it stops and makes it a successor (the next free `mvp-0.N`), following `docs/algorithm-change-playbook.md`.

*As built (CA2, branch `reader/ca2-one-ask`, `docs/reviews/reader-ca2-one-ask.md`):* the ruling found two changes of
classification, so they ship as one successor, `mvp-0.34` (one constant after RW7b's `mvp-0.32`), behind
`ask.cold_help_converts`: K10's Reader cold Ask (a clarification no longer converts a check on your own) and Q4's take
step on a cold follow-up (submit admits a hinted attempt as practice with help, which never answers the cold
measurement). K6 maps onto `hints_used` with its existing meaning and needs none. After the Codex review
(`docs/reviews/reader-ca2-one-ask-codex-review.md`): K9's leak control and take step are built (an Ask answer that
would give the answer away is withheld and offers rungs 4/5 through the host's ladder); H4's strategy routing is
not built yet (H4's checkpoint), nor the separate bridge voice of K11 or a dollar envelope for a metered tutor route.
After the re-review: a withheld answer's text is never stored (the row keeps its take step and a digest), so no
read, note, promotion or queue can show it; an earlier attempt's help opened on the answer box moves onto the
workbench when the draft moves into steps (its carried hints); and a question a workbench binds counts in the
item's window whatever its practice session, as a bound Reader question does (`hint_window.workbench_bound`).

*As built (CA5a, branch `reader/ca5a-find-section`, `docs/reviews/reader-ca5a-find-section.md`):* the Guide
footer's *find this section in my other books ▸* runs a quiet read first (`search_fallback` off) and shows only
when no coverage has been judged and the section is not protected. Pressed, it lists the unchecked hits by book.
Peek renders in the rail through the library peek's span read, go there is the library hit's source detour, and
compare is the library compare path (an ask anchored on the section, both passages pinned, the organizer's notes
left to be asked for). *Not about this* is C0a's correction once per LO of the open section, with undo. The
detour-strip crumb for a peek and §6.5's salience events are deferred to CA5. The new `[reader.correspondence]`
section is the switch, and the prompt contract carries it only while `curriculum.enabled` is on too.

**Kill switches,** following the house pattern (off restores today exactly): `reader_compare.scope_enabled` (CA3: named books and the selection verb's no-pin run), `reader_compare.by_point` (CA4: off renders by book), `reader.correspondence.enabled` (CA5/CA5a; the curriculum spec's `curriculum.enabled` gates the data), `reader.side_by_side.enabled` (CA6), `ask.panel_enabled` (CA2: off restores the overlay and today's Reader rail), `practice.as_printed.enabled` (CA1).

---

## 14. Evaluating it at n = 1

No new table; the measures read existing events and rows (spec §4.3, §5.7, §7.5).

| After | Owner does | Looks at |
|---|---|---|
| CA1 | Practise OCR'd problems as usual | *As printed* opened per OCR'd item; *the transcription doesn't match the page* reports (each is a transcription defect worth fixing); *original page* opened before vs after Submit |
| CA2 | Two weeks of normal practice, some in steps | Asks per attempt by host; questions answered as hints vs about the idea; take steps shown vs taken for worked help; *earlier on this question* opened before vs after Submit; cold checks converted by Ask vs by Hint, and cold questions classified as clarifications (each with its `question_type` receipt, so a misclassified one can be found); help-style changes and the mix of kinds under each style |
| CA3–CA4 | Compare when curious | Comparisons by door; named-book readings corrected with *change* (the `compare_scope` error rate); rows hidden; takes written; keeps; *by book* chosen |
| CA5–CA6 | A week reading across two books | Peeks and jumps per reading hour and their **return rate** (UX §9.2); side-by-side minutes; follow-along moves the learner undid by scrolling back (a sign the pairing was wrong); *not about this* and *also about…* corrections, which the curriculum spec counts as the coverage judge's error rate |

**Questions for the week's end** (added to UX §9.4's checklist):
1. When you wondered how another book did something, could you get there in one or two keys?
2. Did the table make each book's position on each point clear without reading every cell?
3. Did *also in your books* ever feel like noise?
4. In side by side, did the other book ever move when you didn't want it to?
5. On a reattempt, did Ask and hints start fresh? Did you miss last time's help, and was it easy to find?
6. Did the help style visibly change what you got?
7. Did *as printed* ever catch a transcription mistake?

---

## 15. Decisions (owner, 2026-10-25)

The owner adopted every recommended answer except Q3's, which was decided against the recommendation: today's rule stands. Each row gives the decision. The recommendation is kept only where it differed.

| # | Question | Decision |
|---|---|---|
| **Q1** | Ask and hints: one ladder or two? | **DECIDED 2026-10-25, as recommended.** **One help record and one ladder, two doors** (§7.5). Strategy questions are served as hints; requests for the answer go through the take step; one footer. |
| **Q2** | Opening an earlier attempt's thread before Submit: free, or a hint? | **DECIDED 2026-10-25, as recommended.** **One hint-equivalent, said first; free after Submit; absent during a cold check.** Rereading last time's help is help, and the book-open rule already counts that way. |
| **Q3** | During a check on your own, does every sent question make it practice with help, or only questions the server classifies as substantive (today)? | **DECIDED 2026-10-25, against the recommendation: today's rule.** Only substantive questions convert. *Substantive* is the existing rule: the tutor model's `question_type` is `prerequisite`, `mechanism` or `strategy`. Clarifying questions (what a symbol or word means), verification and `other` leave the check on your own. Where Ask needs a judgment to classify, it is the model's, logged as a receipt (the question event with model and prompt version; a `judgment_ledger` row where a judgment comes before the answer), never a hand list. The placeholder states the rule before sending, the answer's label says which it was, and the Reader's bound cold Ask follows the same rule (§7.7, K10). *(The recommendation had been: every sent question converts.)* |
| **Q4** | `cold_retry` and certification probes withhold hints (*No hints on this one*). Keep that, or use the take step? | **DECIDED 2026-10-25, as recommended.** **The take step,** as for every cold check: help is never withheld (U11, P3 §11), and taking it converts the attempt, so the measurement stays honest. |
| **Q5** | Retire the Reader's per-source answer-mode select in favour of the help style? | **DECIDED 2026-10-25, as recommended.** **Yes:** one vocabulary, one stored preference, plus *change* for one question. A learner who wants one source always answered directly can use the workbench-style per-problem override, extended to a per-source override if it is missed (revisit after CA2's two weeks). |
| **Q6** | The practice screen's Ask: docked panel or modal overlay? | **DECIDED 2026-10-25, as recommended.** **Docked,** so the question and draft stay in view (U3: anchor on the learner's work). Below 1,040 px, a sheet with the stem pinned. |
| **Q7** | The screen reader's "Comparison ready: 4 points": a count of rows in a finished table. Keep it, or say only "Comparison ready"? | **DECIDED 2026-10-25, as recommended.** **Keep it.** It is a fact about the finished table, not a count of waiting things (shell rule 10), and it tells a screen-reader user how long the table is. |
| **Q8** | *Also in your books* in skim mode? | **DECIDED 2026-10-25, as recommended.** **Shown.** It is navigation, and skimming across books is what it serves. Skim still mutes everything LearnLoop says about the learner or the text. |
| **Q9** | A margin mark beside paragraphs that have a correspondence? | **DECIDED 2026-10-25, as recommended.** **No.** It would double the margin's load for little gain over the Guide line. The index pairs sections, not paragraphs (§12.3), so v1 has no paragraph-level pairing anywhere. Revisit if the owner finds the Guide line too far from the text. |
| **Q10** | During a cold check, show a figure the problem uses as input, cropped figure-only? | **DECIDED 2026-10-25, as recommended.** **Yes,** with no caption, number or page. Without it the problem is unanswerable, and a figure crop doesn't locate the exercise the way a number or page does (D46's purpose). |
| **Q11** | Kept comparisons on the phone (read-only plus *your take*)? | **DECIDED 2026-10-25, as recommended.** **Later, on the owner's trigger,** when the phone page is used most days. It needs two allowlist entries (§5.7). |
| **Q12** | *Original page* before Submit: a hint, or free? | **DECIDED 2026-10-25, as recommended.** **One hint-equivalent, labelled first.** The page shows neighbouring material (other exercises, a worked example, sometimes a solution), the same as the book left open. *As printed* (the problem's own blocks) stays free. |
| **Q13** | Named books in the ask box: compare only those, or those plus every other match? | **DECIDED 2026-10-25, as recommended.** **Only the named books,** with the others found by retrieval listed under *also discussed in* (one key to add). Naming books is the learner narrowing on purpose. |
| **Q14** | Follow along: on by default in side by side? | **DECIDED 2026-10-25, as recommended.** **On,** section-level only, with the last-touched pane leading. The owner asked to jump between corresponding sections; following at boundaries is that jump, made for them. One toggle turns it off for the session. |
| **Q15** | Should *how do my other books treat this?* replace *where else is this explained?* | **DECIDED 2026-10-25, as recommended.** **No, keep both.** *Where else* finds passages (cheap, sources first); *how do my other books treat this?* compares them (one model call). They answer different questions, and both sit in Transfer. |

---

## 16. Anti-patterns this design refuses

| Refused | Instead |
|---|---|
| **Pin-before-compare**: making the learner collect passages before they can ask the question | One request from any door; pins are optional (§4) |
| **Keyword parsing of book names** ("and", "vs" rules) | A model reads the words and shows its reading as chips, with *change* (§4.3) |
| **A grid of model prose**: cells that summarize instead of quoting | The book's words first in every cell; *not addressed here* when there are none (§5.1) |
| **A "consensus" row, or a winner** | Chips name relations; differences are the content (C3) |
| **"3 other books cover this"** | Names, not counts (C4) |
| **Line-by-line scroll sync** that jitters and fights the reader | Section-level follow along, last-touched pane leads (§6.4) |
| **A modal Ask over the learner's work** | Docked, or inline under the step (§7.1) |
| **Last attempt's hints served as today's** | A fresh record per attempt, earlier ones browsable and labelled (§7.3) |
| **A back door to the answer through Ask** | Requests for the answer go through the take step (§7.5) |
| **"Ask isn't available here"** | Ask everywhere, cold included, with its consequence said first (C9) |
| **A hidden help style** | Visible on every help panel, and it changes what's served (§7.4) |
| **An OCR'd problem with no way to see the page** | *As printed*, and *original page* (§8) |
| **Leaking the exercise's location during a cold check** | Both hidden until feedback; figure-only when the figure is the problem (§8.5) |

---

*Related:* `docs/specs/ux_reader_workbench_v1.md` (§3–§7, W1–W16) · `docs/specs/spec_reader_workbench_v1.md` (§4, §5, §7.3, §7.8, D42, D46) · `docs/specs/spec_adaptive_hints_v1.md` (§4.1–4.8) · `docs/specs/ux_learnloop_v1.md` (§4.2–4.3, §7.3–7.4) · `docs/specs/spec_source_practice_and_probes_v1.md` (§5.2, §9.4) · `docs/specs/spec_image_dropin_ingest.md` · `docs/specs/spec_p3_reader_integration.md` (§11) · `docs/specs/spec_deliverable_curriculum_v1.md` (branch `docs/deliverable-curriculum`, the section correspondence index) · branch `fix/owner-capture-1025` (B2–B4)
