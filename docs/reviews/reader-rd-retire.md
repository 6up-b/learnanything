# Reader workbench v2, RD-retire: the parity table

Stage RD-retire of `docs/specs/spec_reader_workbench_v2.md` (§16's RD-retire row, D12, §21.1). Phase 1 (this branch,
`reader/rd-retire-parity`) makes every parity row true and demonstrated on the workbench with real production bodies.
It deletes nothing and retires no config switch: the extraction of the shared source out of `ReaderScreen.tsx` and
the deletions are phase 2, after inline checks (RD7) and after this table is complete.

The table started from a read-only audit of the parity matrix against main; each row was checked again against this
branch before any work on it.

## 1. How a row is demonstrated

- **Real bodies.** A row's test mounts the desks with no pane stand-in: `fixtures/desks/realDesk.tsx` renders
  `DeskShell` itself, so a source window is the real `SourceWindow` and the Reader's source pane inside it, and every
  read and write goes through the app's api client to a fake sidecar (the harness's `fakeCore.ts`, with a test's own
  answers on top). The only other stand-in is the original-PDF pane, because pdf.js cannot load in jsdom; it keeps
  the props the Reader gives it, as the old screen's PDF tests do.
- **Where it is visible**, the desk harness (`scripts/desk_harness/run.py`) runs the same path in headless Chromium,
  with real layout: gestures that need geometry (a ctrl+drag marquee) are proven there.
- **Fail first.** A row that needed a build has a test that failed before it.
- A row the spec deliberately dropped says so with the spec line instead of a build.

## 2. The parity table

| §21.1 row | Replacement on the workbench | Test (real bodies unless noted) | Verdict |
|---|---|---|---|
| Source pane: render view, PDF pane, selection (drag, ctrl+drag, alt+drag), capture, health flags | The Reader's source pane in each source window (§7.1), unchanged; on a desk its capture runs from the intent box over a selection (highlight, note, the presets) and the menu's Note in margin and Append | `windows/SourceWindow.desk.test.tsx`: text selection captured with exact nodes and offsets and drawn at once; PDF selection sent as the pane sent it and drawn from its placement; held-out material offers no model action; a removed highlight's undo by button and Ctrl+Z in its window; a failed block's health line and its way to the original. Harness `intent` run: ctrl+drag boxes over a book window's text commit one selection there, with no desk zoom | **Demonstrated.** Alt+drag is the PDF pane's own paragraph gesture (`usePdfSelection`), mounted unchanged and covered by the pane's tests; the harness has no PDF to drag on. See §3 for two notes (plain highlight with the intent switch off; ranged windows) |
| Guide rail: cues, reading-path card, deliverable slice | Margin marks with their density and undo (Margin cues), the quick checks (Quick checks), the recap and Wrap up (Last time here); with a goal, the band and path view (RD6). The rest of the Guide is **the reading's guide** in the window: on a desk with no goal and no Guide panel on screen, `p` (and "what matters here?") opens the Guide's own component at the window's top: the section in view with how far through it the learner is and what to do near its break (finish the section, the next one, the check coming up), where questions come from, finding the section in other books and the other books' lines, the reading's path (or a deliverable's slice for the book in its place), the contents and the passages worth a second look; its recap and marks' controls are the window's own there, and its checks show at its top instead of under their sections while it is open | `windows/SourceWindow.guide.test.tsx` (real desk): the section's card with its position bar, where questions come from, the contents, and "find this section in my other books" asking `reader.correspondents`; a deliverable's slice in the path's place (`curriculum.guide_slice`). `windows/SourceWindow.path.test.tsx` and `.intent.test.tsx` for the path in it; harness `intent` run for `p` | **Built and demonstrated.** Before: those lines had no home without a Guide panel. Fail-first: the guide's section card, contents and find were absent from the window's path view before |
| Ask rail, branches, detour strip, reconnect, docked Ask and overlay | The companion (§8) asks; its answers now act on the book's window as the Ask rail's did: a claim of a reading already open peeks there (`openClaim` → the window's inquiry), a companion follow-up joins the window's detours with its parent, walking back (Alt+← or a crumb) shows the inline reconnect under where the learner was, and its "still unclear" asks again in the companion as a branch of that question (`askElsewhere`; `CompanionAsks.ask` takes a named parent). The palette's "Ask the tutor about this" summons the companion while the desks are the Reader (`askRequest`) | `windows/SourceWindow.inquiry.test.tsx`: a claim peeks with the strip and Alt+← back (the restore names the origin passage); a follow-up's branch crumbs, the reconnect inline under the origin and its "yes" naming the root; "still unclear" with words asked in the companion with `parentExchangeId` the root; the palette's Ask summons and never dismisses. The old screen's inquiry suites still pass. Harness `intent` run: a claim of the open book peeks in its window, the strip in the desk's dark tokens (new: the window's lines above its sheet took the paper's ink on the window's dark, unreadable), and alt+← walks back | **Built and demonstrated.** Before: a claim jumped with no way back, a companion follow-up left the window's strip empty, no reconnect ever showed on a desk, and the palette's Ask did nothing there. Fail-first: the first three cases and the palette case failed before the build. RD3b's choice stands: Practice and Today keep their own Ask hosts (`docs/reviews/reader-rd3b.md`) |
| Intent box, active reading | The intent box inside each source window (unchanged); every routed action now has a destination on a desk with no Guide or Notes panel: an ask goes to the companion, asked at once on the selection in the routed answer mode (`CompanionAskInput.answerMode`; an empty Enter opens it on the selection); the active-reading card (and "another way") shows in the window under the last passage it is about, on the text and on the original PDF (an inline note), and its fold follows it; "what matters here?" opens the desk's path (the goal's path view, else the reading's own path in the window: see Reading paths); figures, captures and the presets were already in the window | `windows/SourceWindow.intent.test.tsx`: the routed ask reaches `companion.ask` (no `reader.ask`) with the selection and `help_me_reason`; the next-step question's card under its passage, before the next, and closed; "what matters here?" opens the reading's path in the window. Harness `intent` run: with the box shown, c, / and typing keep their meanings | **Built and demonstrated.** Before: a routed ask opened the Ask tab of a rail the desk hides (nothing visible, and `reader.ask` was sent), the active-reading card lived only in the Notes rail's header, and "what matters here?" switched a hidden rail to its Guide. Fail-first: all three cases failed before the build |
| The tutor that looks things up | `companion.ask` runs the Reader's retrieval unchanged (it inherits `ReaderAskInput`); the companion now carries RW1c's controls: under an answer that looked things up, the abstention line, the verbatim excerpt "from your books" (opening its passage, a peek where it is open), the bridge to the learner's work, and "another way" / "that didn't help…", which ask again as a branch of that answer with `retrievalIntent` alternative / remediate; the personalized chip in its input, sent with every ask while retrieval is on (the vault's default until switched). The window's routed asks and reconnect branches send it too | `companion/Companion.tutor.test.tsx` (real desk): excerpt, bridge and its passage opened as a peek; another way and that didn't help with their intents and parents; abstention; the chip sent and switched; with retrieval off no chip, no controls and nothing extra sent. Backend: `tests/test_reader_rd3a_companion_ask.py` (the companion answers with the Reader ask's reply) and the RW1c suites through the shared core | **Built and demonstrated.** Before: the companion showed only the answer's words and claims, so an answer that looked things up lost its excerpt, bridge and abstention line, and there was no way to ask another way, to say it didn't help, or to switch personalization. Fail-first: four cases failed with the controls withheld (the off-switch case passes both ways, as it should) |
| Workbench (RW2) | See below | See below | **Built and demonstrated on `reader/rd-retire-parity-b`; its row, tests and notes are in that branch's section below (merged here).** |
| Notes rail | Margin notes (§7.1): with no Notes panel on screen, a passage carrying the learner's annotations shows "›" in its margin (30 px left of the text, drawn by CSS so a selection never quotes it); it opens a card under the passage with each annotation's kind, anchor state and words, to edit, delete (the window's undo) or, when the book was read again, re-anchor to this version or to a selection (the Notes rail's card, extracted as `AnnotationCard` and shared). A PDF highlight opened, or a window a search result opened for a note (its `annotationId` in the window's view), opens that card being edited. A capture made from the menu (Note in margin, an append's highlight) is read again by the windows showing its reading, so its mark shows at once. What this knows opens the passage, where the mark is | `windows/SourceWindow.notes.test.tsx`: the mark and edit; delete and undo; re-anchor; a PDF highlight's card; a window opened for a note; a note written with `n` shows its mark at once and opens. Harness `intent` run: the `n` note's mark is CSS-drawn and 30 px left of the text, and its card holds the words with edit and delete | **Built and demonstrated.** Before: edit, delete and re-anchor lived only in the Notes rail; a PDF highlight opened into a hidden rail; a search result for a note opened its passage but not the note; a menu note did not show in the window until it was reopened. Fail-first: the first four cases failed before the build, and the last two each failed with their piece withheld. The fixture sidecar now places a capture on its selection's passages, as the sidecar does |
| Margin cues, alt+↓/↑ | Margin marks in each source window, keys unchanged (the Reader's cue hooks through the window's listener hub); new: with no Guide panel on screen the window keeps the Guide footer's marks controls itself, the density at the foot of its reading and what a mark changed (set aside, fewer marks, off for the book) held at the window's foot with its undo | `windows/SourceWindow.cues.test.tsx`: two book windows each draw their own marks, Alt+↓/↑ move between the active window's marks only and follow the active window; not relevant… undone in its window; fewer marks and off for this book undone in the window, the density control at the foot of the reading, the other book untouched. The old screen's cue suites still pass (impressions from an offscreen window: `ReaderScreen.discoveredCues.test.tsx`, windowed) | **Built and demonstrated.** Before: a change made from a mark on a desk had no undo and no way back but Settings (the receipts and density lived in the Guide rail's footer). Fail-first: the two undo cases failed before the build. The harness fixture has no cues, so this is proven in jsdom only |
| Library ask, compare, keep, roles | See below | See below | **Built and demonstrated on `reader/rd-retire-parity-c`; its row, tests and notes are in that branch's section below (merged here).** |
| Exercises from my sources | See below | See below | **Built and demonstrated on `reader/rd-retire-parity-c`; its row, tests and notes are in that branch's section below (merged here).** |
| Figures and Show me | See below | See below | **Built and demonstrated on `reader/rd-retire-parity-b`; its row, tests and notes are in that branch's section below (merged here).** |
| Last time here, wrap up, digest | With no Guide on screen, the recap card shows in the source window on return, held at the window's top while open (wherever the window opened in the book) and at the top of the reading once folded, recorded as shown once and only there; `w` opens the session's Wrap up in the window; closing the desk's day (the drain, `alt+shift+q`) shows today's pads first, then each reading's Wrap up (with its digest and follow-ups) named by its book (`DrainPanel` gains a slot after the pads; each window puts its own Wrap up there, with its chips, undo and restore). The leave-the-Reader offer outside the desks is unchanged | `windows/SourceWindow.wrapup.test.tsx` (real desk): the card above the reading, recorded once; `w` opens Wrap up in the window (`wrap_up_opened`); the drain shows the pads first, then the Wrap up, its "resolve" calling `reader.set_inquiry_status`. `windows/SourceWindow.recap.test.tsx` changed with the behaviour: no panel, or a hidden one, shows the card in the window, recorded once; a visible panel shows it in the panel, still once; a preview records nothing. Harness `intent` run (`?recap=1`): the card at the top of the book's window, recorded once; the drain's Wrap up after the pads, named by its book | **Built and demonstrated.** Before: recap and Wrap up lived only in the Guide's header, so a desk with no Guide panel showed neither, and the drain had no Wrap up. Fail-first: the three desk cases failed before the build. Skimming still mutes the card, but a desk has no way to choose skimming (§5) |
| Cold follow-ups | Inline checks (RD7) | `tests/test_reader_rd7b_cold_followup_parity.py`; `screens/desks/checks/deskChecks.test.tsx`; the harness's `checks` run | proven on `reader/rd7b-inline-checks-ui` (section below) |
| Reading paths | With a goal band, the goal's path view (§12.5, RD6; unchanged). With none, the book's own path (RW7a) in its window: `p` opens it in the focused book window (it used to do nothing without a goal) and "what matters here?" opens it in the window asked from, held at the window's top with the recap card (one sticky block), closed with esc or "close". It is the Guide's own path card and deliverable slot (`GuidePathSlot` with `ReadingPathCard`): the depth asked once and changed there (stored, `reader.reading_path_set_depth`), "read it anyway" / "skip it" stored (`reader.reading_path_override`), and the exercise worth trying opened as a problem on its verbatim words. Each opening reads the path again | `windows/SourceWindow.path.test.tsx` (real desk, no goal): `p` opens it, the depth asked and stored, the path shown, esc closes; "read it anyway" stored and "Try it" opening the problem (`workbench.open` on the exercise's words). `windows/SourceWindow.intent.test.tsx`: "what matters here?" opens it in the window. Goal desks: `goal/GoalDesk.test.tsx`, `goal/components.test.tsx` (unchanged). Harness `intent` run: `p` opens it in view at the window's top, and esc closes it | **Built and demonstrated.** Before: a desk with no goal had no path but the Path panel adapter, which the Path panel row removes in phase 2 and which passed no exercise action; `p` did nothing. Fail-first: both cases failed before the build. The Path panel window still opens when reading paths are off and a panel is asked for; it goes in phase 2 |
| Side by side | See below | See below | **Built and demonstrated on `reader/rd-retire-parity-c`; its row, tests and notes are in that branch's section below (merged here).** |
| Watch panel | Video windows (§7.4) wrap `SourceWindow`; the Reader's synchronized watch panel inside | `tests/test_sidecar_reader.py::test_watch_plan_returns_video_id_for_youtube_source`; `reader/YouTubeWatchPanel.instance.test.tsx` (each frame takes only its own time messages); harness `desks` run (two players' frames checked) | **Demonstrated** (by the audit; unchanged here) |
| Quick checks, authored questions | The section-end offer and the PDF's section break were already in the window; now the checks themselves are too: with no Guide on screen, each section's quick check or authored question shows in the window under its section (after its opening for a question placed before it, else after its end; on the original PDF as an inline note), with its whole round: think it through, record or compare, the controls (too easy, bad moment, ask differently…), what to do with the idea, and "Done with this check", after which what it showed stays folded where it was. It is the Guide's own check list, extracted as `QuickChecks` and shared, so one rule offers checks in both. The learner's own question ("write my own question") is asked in §5 | `windows/SourceWindow.checks.test.tsx` (real desk): a placed question in its section, presented, answered (`reader.present_question`, `reader.submit_question`), closed with what it showed kept and the section marked; an authored question answered and compared with the source (`reader.authored_question_action`). The Guide's own suites still pass (`reader/sectionEndRound.test.tsx`, `checkControls`, `sectionDone`). Harness `intent` run (`?checks=1`): the check shows in the book's window, in its section | **Built and demonstrated**, with the learner's own question from Make it practice's "write it myself" (the orchestrator's default, §5). Before: the window offered "quick check →", but the check opened in a Guide the desk hides. Fail-first: the first case failed before the build |
| Lesson entry from the Reader | Lesson windows (§11.1) | `lesson/deskLessons.test.tsx` (a selection's lesson lands in the desk's stack); `DeskShell.menu.test.tsx` (Teach me opens a tab of the desk's stack); harness `lesson` run | **Demonstrated** (by the audit; unchanged here) |
| Reader config switches | Each audited individually | The audit table (phase 2's landing carries it, with the config dispositions) | phase 2 |

## 3. Notes on rows

- **Plain highlight with the intent switch off.** On a desk the intent box is a selection's capture door. With
  `reader_intent.enabled` off (default on) a selection falls back to the Notes rail's capture composer, which a window
  shows only beside a Notes panel; the menu's Note in margin and Append still capture, but a plain highlight with no
  words needs the box. Recorded, not built: the switch is on by default and the menu keeps capture reachable.
- **Ranged windows (§7.1).** The desk model stores a window's range (`content_ref.py`), and `SourceWindow` opens the
  whole reading at the range's start. That is a §7.1 layout gap of RD1's, not a v1 behaviour the old Reader had, so it
  is outside the parity matrix; recorded for the coordinator.

## 4. Entry points that still open the old Reader

The desks gained the targeted open the audit found missing: `DeskShell`'s `openRequest` (the app's `readerOpenSeq`
with its book, passage, reading and search words) opens or focuses the book at the passage on the desk in view, or
opens the desks' search, once per request however often the desks mount again (`windows/SourceWindow.entry.test.tsx`:
a book opens beside and focused, and is not opened again on a remount; a book already open is focused at the
passage; "Look in my library" opens search with its words). A passage found on an earlier reading of the book opens
the book at the learner's place and says so, never as a passage of the reading it has now; a book still being
prepared says so and stays in the Library.

Routed to the workbench on this branch, while the desks are the Reader:

| Entry | Now |
|---|---|
| The palette's "Ask the tutor about this" while reading | Summons the desks' companion (`askRequest`) |
| Library shelf, Today's book choices, Add a file, Continue | The book opens or is focused on the desk in view (`openRequest`) |
| Today's threads and citations (with the reading translation) | The book at the cited passage on the desk in view; an earlier reading's passage opens the book and says so |
| Feedback's "Back to where you studied this", printed-page restoration | The book at the restored passage on the desk in view |
| A lesson's "Look in my library" | The desks' search, prefilled once |
| Restore on startup | The workspace as it was, the remembered book focused |
| Today's plan reading (`reader/rd-retire-loose-ends`) | The plan's book opened (or focused) at its section on the desk in view, under the plan's banner; back to the plan ends the block as before |
| Check me, an exercise pick, a deferred session start, workbench submit, feedback and back, unfinished problems (`reader/rd-retire-loose-ends`) | Proven from the app: the return into side by side and Today's resume onto its pad, end to end (that branch's section) |

Still listed, each waiting on its row, another worker's row or phase 2:

| Entry | Why it stays |
|---|---|
| The Reader place's default surface, the two surface-switch buttons, the desks' "old Reader" | Phase 2's cutover. The default stays the old screen and the switches stay until the old screen is deleted: they are the way back while phase 2 extracts the shared source out of it, and flipping the default first would leave the desks with no way out to a screen phase 2 still edits (re-checked on `reader/rd-retire-loose-ends`) |
| Saved panel windows (Guide, Notes, Path, Library) | They open no old screen: a saved panel is a desk window (`panel` content) whose Guide and Notes are the book window's own Reader rail, shown through the window's rail host, and whose Path and Library are the desks' own panels. What phase 2 owes them is the identity translation when the rail adapters leave `ReaderScreen` with the shared source (re-checked on `reader/rd-retire-loose-ends`) |
| A book still being prepared (reading the original before extraction ends) | Cannot be routed yet: a desk window's source content names its reading (`SourceRef.extraction_id`, required in `desks/content_ref.py`), and a book being prepared has none; the original file's view is the old screen's preparing view (its PDF pane over the original). A window for it needs a content kind for an original, a server validator change, so the desks keep it in the Library with the line that says so (re-checked on `reader/rd-retire-loose-ends`) |
| Phone Read tab and `#/read/...` | Kept: the phone keeps its own Reader (§13.3) |

## 5. Product decisions asked

Both are built as the orchestrator's defaults; the owner may change either, and the alternatives stay recorded.

- **Skim, read closely, mark for later on a desk** (the audit's §5, no parity row). The old screen's header offers the
  mode; skimming mutes the recap card, section prompts, cues and dose offers, and tells the app to hold the
  leave-time offer. **Default built: (a)**, the choice in each window's source bar beside the view switch ("I want to"
  · skim quickly / read closely / mark for later), per window, stored where the old screen stored it
  (`reader.set_mode`, by reading), with the same effects inside that window. Alternatives kept: (b) one choice per
  desk, in the desk's top bar; (c) drop skimming on the desks (the desk's own geometry is the learner's "skim").
  Wired on `reader/rd-retire-loose-ends`: the app's leave-time offer hears the book being read on the desks being
  skimmed (that branch's section). Tests: `windows/SourceWindow.mode.test.tsx`, `app/App.desks.test.tsx`.
- **The learner's own question on a desk** (row "Quick checks, authored questions"). The old screen's Notes rail
  offers "write my own question" from a selection (`reader.author_qa`, with the wording coach). **Default built: (a)**,
  Make it practice's sheet offers "write it myself" beside the model's draft, opening the Reader's own question card
  (the Notes rail's, extracted as `AuthoringCard`) under the passage in its window; nothing is drafted then.
  Alternatives kept: (b) the card opened from the intent box's palette (a client-side action); (c) the pad path,
  Append the passage, then Make it practice on its line (`author_practice_item`, the pad's item, not the passage's).
  Tests: `windows/SourceWindow.ownQuestion.test.tsx` (real desk), `menu/verbs.test.ts`.

## `reader/rd-retire-parity-c`: library ask and Compare, exercises from my sources, side by side

Three rows, each checked again against this branch first. Tests mount the real desks (`fixtures/desks/realDesk.tsx`);
each failed on the code before its build.

| §21.1 row | Replacement on the workbench | Test (real bodies) | Verdict |
|---|---|---|---|
| Library ask, compare, keep, roles | The Compare (and library) window mounts the library pane with what the Reader gave it: Keep and the learner's take (`CompareKeepContext`, `NotesContext`, from the Reader's own `useKeptComparisons` and `useNoteMarks`), "practice this ▸" handed to the shell as a learner pick in the asked book at the asked passage (that book's window opens or takes the focus, as the library page opened it), and the textbook exercise rows. A keep or a take made in any window announces itself, and every reading's ⇄ and › marks read again (`announceKeptChange`, `announceNotesChange`), so a book open beside shows the mark at once. Library ask stays reachable unanchored from the opener's "ask across the library" and anchored from the Compare verb | `windows/CompareWindow.desk.test.tsx`: an anchored ask and each hit's role (a model's proposed role labelled as the model's); pins compared by point, kept, the book beside showing ⇄ with no reload; a practice pick with its book, passage and reading, the book's window focused | **Demonstrated** (roles were already shown; keep, practice and exercises built) |
| Exercises from my sources | Exercise rows in the book window's library answer (the Reader's `ProposalExercises`, unchanged): candidate discovery and the fallback as before; "use this one" and "open in the book" for an exercise in another book open that book in a window beside (`ReaderWindowing.onOpenBeside`), never in place of the window's own book, and the shell's queued exercise opens in that book's window only (a window opens the problem of its own book) | `windows/SourceWindow.exercises.test.tsx`: the rows listed in the window; "use this one" here hands over the exercise with its source and opens nothing; in another book it opens that book beside and the queued exercise opens there alone (`workbench_open` once, with the exercise's own passage); "open in the book" opens it beside | **Demonstrated** |
| Side by side | Two windows in view, or a pair (§5.2), as the spec says; the nested second pane is not rebuilt. Ctrl+\ (the first correspondent) and the lists' "side by side" open the other book in a window paired with the book (`openPaired`: one slot, two panes; beside it when the slot is full; an open book is focused where it is), recorded as `side_by_side_opened` as the pane recorded it. The desk hosts what the pane did between the two (`desks/sideBySide/pairs.ts`): follow along (on by default; the other window moves once per section crossing to its book's first judged correspondent, a search hit never moves it, none says "stays put", the moved window never answers back; `follow_along_moved` recorded), Ctrl+Shift+L for the pair, F6 to the other window. Every crossing takes a ticket: an answer for an earlier
crossing moves nothing once a newer crossing, a toggle, or the learner's own hand on the window it would move
(a scroll, a click, a touch: `ReaderWindowing.onTouched`) has come since. Second-pane targeting needs nothing: each window's selection, capture, checks and asks are its own book's. Each window keeps its own place and anchors | `windows/SourceWindow.sideBySide.test.tsx`: Ctrl+\ opens the correspondent paired with the book, no pane inside the book's window; scrolling the book into a new section moves its pair once and the move asks nothing back; a late answer moves nothing after the learner scrolled the other window, nor after a newer crossing; Ctrl+Shift+L stops following, F6 moves the focus each way; a highlight in the paired window is that book's. Harness `pairs` run (headless Chromium, real layout, `?pairs=1` on the backprop desk): the pair in one slot with two equal panes at the correspondent's section, the learner's scroll across a section moving the other window once and asking nothing back, Ctrl+Shift+L stopping it, F6 each way. Visual stage `pairs` against the reference's `desk=1` | **Demonstrated** (see the notes) |

Notes on these rows:
- **Side by side: what changed by design.** The pane's crumb (`↩ … › side by side with …`) and walking off it to close
  have no counterpart: both windows stay on the desk, each with its own place, and closing one is closing a window.
  The narrow window's peek sheet is not needed: a pair stacks top and bottom at any width. "The last-touched pane is
  never moved" holds: a window moved by following never leads from that move, and a window the learner touched since
  a crossing is never moved by that crossing's answer.
- **The pair against the mockup.** The reference holds no state with two windows in one slot (its "stack" keeps two
  in one slot as tabs), so the visual stage `pairs` compares the desks' pair against `desk=1`, the reference's state
  with two reading windows in view, for colours, tokens and type only (geometry off: a pair stacks top and bottom by
  §5.2). `findings pairs: 1 (colour 1)`: at laptop size the first passage measured in the paired window is its
  section heading (the jump opens the window at the section, so the heading is first in view; amber, as the reading's
  headings are), where the reference's first passage is prose. Every other colour, token and type matches.
- **The way back after a check opened from the second book** (CA6b's `besideTrail`, through the shell's practice and
  feedback screens) waits on phase 2's targeted open, like every app-level return to a passage (the audit's §4).
- `ReaderWindowing` gained `onOpenBeside`, `onOpenPair`, `onSection` and `onPairKey` (additive; the old screen passes
  none and behaves as before).

## reader/rd-retire-parity-b

| §21.1 row | Replacement on the workbench | Test (real bodies unless noted) | Verdict |
|---|---|---|---|
| Workbench (RW2a–d) | Problem pads (§15.2). A problem a book window opens (work through this, an exercise, a check, a resume, back from feedback) is handed to the desk: a pad of kind `problem` bound to its workbench session (`create_pad` with `workbenchSessionId`, or the loaded pad of that session) joins the desk's stack and comes into view, and the window goes back to reading instead of showing the working posture over the book. The pad hosts the workbench itself (`screens/workbench/Workbench`, unchanged): steps saved to `workbench_steps`, the help ladder, the check, I'm stuck, Submit (the shell's hand-off to feedback with the way back to the problem's passage), Leave for now and Abandon, the book in its own window ("show in the book"). Set aside or abandoned, the pad keeps a way back (resume / reopen); submitted, it shows the problem read-only. `screens/desks/problem/` (`ProblemPad`, `problemPads`); `ReaderWindowing.onWorkOnPad`, `SourceWindow`, `DeskShell` (`workOnPad`, `problems` on the pads host), `PadStackWindow` (the problem pad's case) | `problem/ProblemPad.desk.test.tsx`: work through this on a selection opens `workbench.open` and a problem pad in the stack with the workbench, and no posture in the book's window; on the pad a step saves, the help ladder opens (`workbench.suggest_help`) and the check runs (`workbench.check`), Submit sends `workbench.submit` and hands the result to feedback with the problem's card and passage, and the pad shows it submitted; Leave for now keeps the pad, and resume reopens the same session. The old screen's workbench suites still pass | **Built and demonstrated.** Before: on a desk the problem opened as the old working posture inside the book's window. Fail-first: all three cases failed with the hand-over unwired. **One pad per problem** (follow-up): the pads store has no read by session (`pad.list` neither filters nor indexes by `workbench_session_id`), so the pad's id is derived from its session (`problemPadId`) and read from the server before one is made; a second open of the same session, in a fresh desk view with the pad not loaded, finds the first pad. **Two desks**: a stack that already holds the pad, on any desk, is where it is shown, that desk becoming the current one, with a line saying so; a pad in no stack joins this desk's. Tests: "opening the same problem again in a fresh desk view, its pad not loaded, finds that pad" and "opened from another desk, the problem is shown on the desk its pad lives on" (both failed before: two pads, and the second desk's stack took it). The workbench sits on the pad as a card in the app's own theme (on the paper its text read light on light). RD8a's ink ladder on problem pads stays stopped, as recorded there |
| Figures and Show me (RW5a–d) | §13.1. Source insets stay in the book's window (the Reader's figures, unchanged). Show me (the menu's verb on a passage, a cue, a highlight or a pad line) now puts its figure in the companion's answer: "◇ Show me · a figure for <source> p.<page>", the live widget itself (the Reader's `FigureInline`, open, predictions recorded as the Reader's), **view source** (the figure's source, display tier, no kernel), **move to scratchpad** (the `figure` block in the running pad of the desk it was asked on, as before) and **not useful** (removed, and logged as the salience-only reader event `figure_not_useful`), with the footer "it is help, not a check"; the companion is summoned docked if it was hidden. **Shared parameters**: every instance of one figure shares its parameters for the app's run (`reader/figures/sharedParams.ts`), so dragging one moves the others. `companion/companionFigures.tsx`; `Companion`'s `figures` slot; `DeskShell` (`showFigure` in the menu's context, `landFigureBlock`); `menu/verbs.ts`; `reader_inquiry.CLIENT_ACTION_EVENTS` (+`figure_not_useful`) | `companion/Companion.showMe.test.tsx` (real desk): the figure in the companion, named for its source and page, live (sliders), with the footer, and nothing written to a pad by itself; view source shows its source; move to scratchpad writes the figure block in the running pad and the figure leaves the companion; not useful removes it and `reader.log_activity` records `figure_not_useful`. `reader/figures/sharedParams.test.tsx`: two instances of one figure move together, another figure keeps its own values. `DeskShell.menu.test.tsx`'s Show me case now finds the figure in the companion and moves it to the running pad of the desk it was asked on, with another desk shown. Backend: `tests/test_figures_rpc.py::test_the_client_records_a_companion_figure_set_aside_as_not_useful` | **Built and demonstrated.** Before: Show me only landed a figure line in the running pad (no live widget anywhere on the desk, no view source, no not useful), and two instances of a figure kept separate values. Fail-first: the three companion cases with Show me routed to the pad, the shared-parameter case with per-instance state, and the backend case (the event was refused). **View source and the notebook frame:** no figure carries a notebook today (`FigureViewDto` has none, and nothing exports a figure to marimo), so view source shows the figure's own source (its spec, or a sketch's program) in place, display tier; a figure-notebook window (§13.1) needs that export, which is not built. Visual: the reference set shows no companion figure (`#figopen`, `#figsrc` were not applied in the plain variant; in the goal variant they applied with the companion on its thread; `#figmove` threw in the page); only the pad's `◇ fig` gutter mark (`pad_mark_fig`, `#figmark`) is comparable, and it is unchanged here |

Notes on these two rows (reader/rd-retire-parity-b):

- **Harness.** The `showme` run (`scripts/desk_harness/run.py --only showme`, 7 checks) drives Show me from the menu
  on a book passage in headless Chromium: the figure in the companion, live (sliders and a plot), its buttons and
  footer, JetBrains Mono, nothing clipped sideways, nothing in a pad until moved, view source, and move to
  scratchpad writing the running pad's figure block. The fake sidecar answers a figure build with a fixture figure
  (`fixtures/desks/figures.ts`, a project-authored spec from the figure golden corpus). The `problem` run
  (`?problem=1`, 4 checks) drives RW2 on a problem pad with a minimal fake workbench service
  (`fixtures/desks/workbench.ts`: one session, steps saved, a help suggestion pending, a submit recording an
  attempt): work through this on a selection opens the problem pad in the stack with the workbench and nothing over
  the book, a typed step is saved, the help ladder opens, and Submit hands the attempt to feedback with the pad
  showing it submitted.
- **Visual stages.** `visual_reference.py --stage rd3`: `findings rd3: 7 (colour 1, geometry 4, missing 2)`;
  `--stage rd4`: `findings rd4: 19 (geometry 1, missing 15, type 3)`, the same counts as the last full run on this
  reference set. No captured state shows a companion figure or a problem pad.

## reader/rd7b-inline-checks-ui

| Old Reader surface | On the desks | Proof |
|---|---|---|
| Cold follow-ups (RW6b) (§21.1, "Unchanged (commitments), and hosted inline (§12.6)") | Unchanged: a follow-up is a `test_me_later` commitment, served by Today as before (the RW6b tests still pass). Hosted inline: a due follow-up shows its closed marker before its host passage and opens on the desks through `check.begin_inline`, on the item Today would serve, cold; RW6b's serve-time gate holds it on both surfaces, because the inline opening serves only what the serving view's `servable` allows. | `tests/test_reader_rd7b_cold_followup_parity.py`: a due cold follow-up opens inline, cold, on Today's item; under the gate (an exposure since its valuation) Today holds it and the inline opening refuses with `nothing_to_serve`. The desks' side (marker, check now, card, veils) is in `screens/desks/checks/deskChecks.test.tsx` and the harness's `checks` run. |

## reader/rd-retire-loose-ends

The phase-1 record's paths not proven or not wired from the app, closed before the old Reader can go. The proofs mount
the whole `App` with the real desks: `fixtures/desks/realApp.tsx` (the app's helper beside `realDesk.tsx`) gives a
fake sidecar for one app: its vault, an empty Today, its desks and pads on a fixture server of its own. Every book,
reading and Reader read goes through the app's api client to the desks' fixture. Each app's desk writes reach only its
own server: an earlier app's desk store, kept per vault while the module lives as the app keeps it, may still be
sending its outbox. Only the practice and feedback screens are stand-ins (their back and "back to the book" are the
app's own ways back), and the leave-time offer shows only whether the app mounted it. Tests: `app/App.desks.test.tsx`
(9).

| Path | Before | Now | Proof |
|---|---|---|---|
| Back from a check begun in the paired (second) book of a side-by-side pair | The desks came back focused at the passage in the paired window, but no longer a pair. The desks' pairs (following, F6, the way back) were the mount's, and the Reader place unmounts for the check. In the webview the paper also came back where following had left it, not at the passage: its Reader, placing itself once it opened (a saved place, its reading history), undid the jump the desks made | The pairs are the vault's while the app runs (`keptPairsFor`; a move an earlier mount still waited for is dropped). The window the app's open request focuses opens at the passage | App: check from the paper's margin mark, practice, back: the paper focused at the passage, in the book's slot, F6 to the book and back (failed before: F6 stayed). Harness `pairs` run: leave the desks and come back with the way back to the paper's passage: the pair as it was, the paper focused, its passage in view, F6 (failed before: the passage out of view) |
| Back from a problem begun in the paired book (workbench on) | Not proven | Unchanged code (the pair fix above) | App: the check is worked on the desk's problem pad, Submit to feedback, then "back to the book": the paper focused at the passage, the pad showing it submitted, still a pair; and feedback's back (the problem): the same, the problem read-only on its pad, never a posture over the paper |
| Today's resume of an unfinished problem | The desk side tested, the app's wiring not | Unchanged code: proven | App: Today's "resume ▸" opens the desks, the book's window takes the resume, and the problem is open on its pad (one pad, bound to its session); with the pad living on another desk, that desk becomes the one in view and the pad is never shown, nor stacked, on the learner's desk |
| An exercise used from a book window with no session yet | Not proven | Unchanged code: proven | App: "use this one" starts one session (the simple shell's implicit start) and the exercise is worked on the desk's problem pad |
| The leave-time offer while skimming on a desk | Heard the old screen only | Each book window reports its reading's skimming to the desks (`SourceWindow.onSkimming`, the Reader's own `onSkimmingChange`). The desks report the book being read (the focused book window, else the book window focused last) to the app (`DeskShell.onSkimmingChange`) | App: skimming the focused book, then leaving for Today: no offer; read closely: the offer (failed before: offered while skimming); another window skimmed while the book read is read closely: the offer |
| Today's plan reading | Mounted the old screen whatever the surface | On the desks: the plan's book opened (or focused) at its section on the desk in view, under the plan's banner. Lessons and the palette's ask go to the desks while the plan's reading is shown. The plan's visit initiator (RO0 row 4) is named for its reading (`setNextReaderVisitInitiator("plan", extractionId)`), so on the desks only the plan's book's visit takes it, not the first window to start one | App: Today's ↵ on a plan whose step is a reading: the banner, the paper opened beside the book and focused at the section, back to the plan sends `plan_reading_ended` (`left_reader`) and the banner goes (failed before: the old screen). `screens/reader/activity.initiator.test.ts` (failed before: any visit took it) |

**Judgment calls**
- **The book being read** is the focused book window, else the one focused last. The old screen had one book, and the
  offer followed it; on a desk another window's skimming does not hold the offer.
- **Pairs kept for the app's run, not stored.** The desks' state has no pair; a slot of two windows is not always a
  pair (the learner can share a slot), so a pair is not derived from the layout. After an app restart the two windows
  are still in their slot, without following.
- **A problem's way back.** Feedback's back (the problem) and "back to the book" both focus the book's window at the
  passage: the problem is on its pad in view, read-only after a submit. The old screen showed the problem over the
  book; on the desks the pad is where it lives.

**Phase 2's**: the surface default and switches, and the saved panels' identities (rows above). The preparing view
needs a content kind for an original first. The phone keeps its own Reader.

## Phase 2, step 1: the scoped source extracted (`reader/rd-retire-extraction`)

A move, no deletion: the standalone screen and a source window both mount the same extracted source, so step 2 can
delete the standalone shell alone.

### What moved where

| Before | After | Lines |
|---|---|---|
| `screens/ReaderScreen.tsx`, the whole `ReaderScreen` function and every module-level definition | `screens/desks/source/ScopedSource.tsx`: the function as `ScopedSource`, the module's helpers, `RailScope` (the live portal stays) and `SIDE_PATH_COPY` | 5,359 → 4,884 (4,880 at the move; 4 more with RDX-1's fix) |
| The seven exported contracts (`ReaderOpenSource`, `ReaderWindowing`, `WindowInquiry`, `ReaderLens`, `PenSurface`, `ReaderCheckMeRequest`, `ReaderExerciseRequest`) | `screens/desks/source/types.ts`, with `StandaloneShell` and its four contexts | 216 |
| The standalone-only branches: the opening view and the list of books with its search, shelf, reader-off and demo views; the old header; the collapsed rail's handle; the key bar | `screens/ReaderScreen.tsx`: four functions (`unopened`, `header`, `collapsedRail`, `keyBar`) the source calls through its one new prop, `standalone`; `ReaderScreen` mounts `ScopedSource` with them | 332 |

`SourceWindow` mounts `ScopedSource` (no `standalone`), and every type importer (`App.tsx`, `DeskShell.tsx`,
`CheckCard.tsx`, `GoalLayer.tsx`, `goal/marks.tsx`, `PenLayer.tsx`, `video/followLens.ts` and two tests) reads
`screens/desks/source/types`. The only change to a moved statement: `READER_MODE_OPTIONS` is exported, because the old
header reads it. Each standalone function takes exactly the source's locals it read (24, 16, 9 and 10 names), typed in
`types.ts`.

**Not split (and why).** No hook moved out of the source. The standalone-only state stays in it until step 2 deletes it
with the screen: the list's search (its query, depth, results, busy and error state and the effect that runs it), the
offline demo, `backToLibrary`, the `shelf`, `initialLibrarySearch`, `onOpenLibrary` and `onOpenDesks` props, and the
collapsed rail's preference with its `\` key. These read and write the source's own state (`render`, `sidecarDown`,
`openSource`, the inquiry), so taking them out would change which component owns a hook; the four functions read them
through their contexts instead. `railCollapsed` is also read by shared code (the recap's visibility, the cue layout
key), so step 2 keeps it at its window value (never collapsed) rather than deleting it outright.

### The proof

- `scripts/rd_retire/check.mjs` (TypeScript's compiler API, run against the original file): every module-level
  definition (28) is the same AST, comments and layout aside, in `ScopedSource.tsx` or `types.ts`; the function is the
  same (3,426 printed lines) but for its name, the `standalone` prop and the four calls; each of the 11,604 names in it
  resolves to the same declaration as before (an import's target module and name, a module definition, or the same
  local, by its declaration's order); each standalone function is the original branch's text with each of its names
  resolving as before (555, 208, 34 and 34 names), and each call passes exactly the names its function reads, each the
  local it read before. The check fails on a changed literal in the source and on a renamed context name in a slot
  (both tried). `scripts/rd_retire/generate.mjs` made the move (it rewrites the three files from the original: a record,
  not a tool to run again).
- Every `screens/ReaderScreen.*.test.tsx` (23 files) passes unchanged against the standalone screen, as do the 64 other
  test files that mount it; every real-desk test passes against the window.
- The tests about the shared source are ported to mount `ScopedSource` (`screens/desks/source/ScopedSource.*.test.tsx`,
  22 files, 154 cases, made by `scripts/rd_retire/port_tests.mjs`; `cuesSwitchOff`'s snapshot is the original's, byte for
  byte, run with `CI=true` so nothing new was written). The 28 cases that reach the source only through the standalone
  branches are left out of the copies and kept in the originals: 13 leave the book by "← Library"; 9 use the list of
  books (its search box 4, opening a book from it 2, the opening view, the shelf and the reader-off notice 1 each); 5
  read or set the header's "I want to" (4) or read its re-read note (1); 1 reads the key bar's wrap up. Each is named in
  its copy's header and in `scripts/rd_retire/standalone_only_cases.json`.
- Source-path guards read the moved file: the capture-listener pin (`app/shellChrome.test.ts`), the classic gate's
  evidence for the palette's ask (`app/classicIsBase.test.ts`) and the block policy's page check
  (`tests/test_rw5c_block_policy.py`).
- Typecheck; the whole vitest suite; every desk harness run (206 passed); the visual stages: every state's numbers are
  the last run's (pairs 1, rd1 36, rd2 21, rd3 7, rd4 19, rd5 2, rd6 7, rd7 30, rd8 3, rd9 4). The one state whose pixel
  share moved (`s11=lift` at laptop size, 25.9% or 48.9%) takes either value from run to run on the tree before the move
  as well; built before and after the move, its two runs in the same mode are pixel-identical.
- `desktop_validate` counts recomputed with the generator: 434 TypeScript files, 409 entry-reachable, 21 vitest-support,
  440 active; `screens/desks/source` has its area line.
- Found on the way: RDX-1 in the ledger (a hosted rail showed the Guide's name for a render in a Notes window), fixed in
  its own commit after the move.

### What step 2 deletes, in order

1. Port the 28 left-out cases to a source window's own controls (leaving a book is closing or switching its window;
   search hits come through the desk's search or the Library panel; "I want to" is the window's source bar; wrap up is
   the window's `w`), and port the 64 other standalone-mount test files the same way (or retire the ones that test only
   the old frame), as the 23 originals were ported here.
2. The app-to-desk hand-offs (the audit's §4, order 3): every entry that opens the standalone screen opens a desk, and a
   stored desk's panel windows of the old kinds are mapped on restore (below).
3. Remove `App.tsx`'s lazy `ReaderScreen` and its two mounts, `app/shell.ts`'s Reader surface switch, `DeskShell`'s
   `onLeave` back to the old surface, then `screens/ReaderScreen.tsx` itself.
4. In `ScopedSource`: the `standalone` prop and its four calls (each `null` without it), the standalone-only state
   listed above, and the props only the screen passes; in `types.ts`, `StandaloneShell` and its four contexts. Then
   `screens/reader/readerKeys.ts` and `searchBasis.ts` (their last caller is the old key bar and list) and the original
   `screens/ReaderScreen.*.test.tsx` (the ported copies keep their cases).
5. Later, with the rows that move the Guide, Notes, Ask, checks and recap out of the portal: `railHost` and `RailScope`.

### What still blocks deletion

- **The surface default and switches**: the app's Reader place still defaults to and can switch back to the standalone
  screen (the surface choice and the desks' way back); the owner's default and the switch's removal come first.
- **Saved panels' identities**: stored desks hold panel windows of kind `guide`, `path`, `library` and `notes` (and a
  separate `compare`); each must be mapped to its new home on restore, keeping its book, place, focus and a saved
  Compare's anchor, and tried on an already-populated workspace.
- **The preparing view's content kind**: a book still being prepared opens on its original in the standalone screen
  (`PreparingView`, the shared branch above the window's own opening line); a desk has no content kind for an original
  yet, so a source window cannot name or restore that view.

## Phase 2, step 2: the deletion (`reader/rd-retire-extraction`)

The old standalone Reader screen is gone: the desks are the Reader's only surface. Each part is its own commit(s), in
the brief's order. `origin/main` was merged first (the goal lens's chapter reason in batch 5's voice: "A chapter you
accepted here is about …" and "A chapter you accepted links this section to …"; the nouns branch will meet the same
conflict when it lands).

### A1. Saved panels' identities (`screens/desks/model/restore.ts`)

The orchestrator's calls: a saved `library` panel keeps its kind (no change to `CompareRef`, any stored shape or RPC
contract), and `guide` and `notes` panels keep their live kinds until the rail leaves the portal. `restoreContent` is
a pure function from a stored content reference (any shape) to what it restores as, tested over every kind the
content reference has had, the fixture workspace's windows and damaged or unknown shapes (`model/restore.test.ts`,
29 cases):

| Stored | Restores as |
|---|---|
| `source`, `video`, `pad`, `lesson`, `thread`, `compare`, `figure_notebook`, `preparing` | itself |
| `panel: guide`, `panel: notes` | itself (the hosts of the book window's rail until it leaves the portal) |
| `panel: library` | itself (the Compare window's body; stored shape unchanged) |
| `panel: path` with a reading | the book's window with its path open: the book's window already on that desk (the panel closes, the window takes the focus if the panel had it), else the book's window opened in the panel's place; the reading's source is asked of the reading (`sourceOfExtraction`) |
| `panel: path` with no reading | kept, shown inert, named in a toast ("a reading path with no book") |
| a `source` or `video` that lost its reading or its source | the book's window again |
| an unknown kind (or an unknown panel) naming a source or a reading | the book's window (a book being prepared when only its source is named) |
| an unknown kind naming nothing, no content, not an object | kept, shown inert ("This window (a whiteboard window) can't open here…"), named in one toast for the load |

The desks apply it once per load, before the shell reports ready (`DeskShell.restoreSaved`), through
`replaceWindow` (model/workspace.ts: the new window opens right after the old one, which closes; the focus follows;
the replaced window is not offered back by "undo close"). No path panel is opened any more: `p`, "what matters
here?" and the opener's "Reading path" row open the path in the book's window; with no path for the book the desks
say so. A path panel that arrives from another device mid-session says the path is in the book's window and is
restored on the next load. The fixture workspace's path panel is a Notes panel now (`fx_w_notes`).

Tests (real desks, `windows/PreparingWindow.desk.test.tsx`): a stored path panel with the book on the desk closes and
the book's window shows its path; with no window of its book, the book's window opens in its place with its path
open; an unknown kind naming a source restores as that book's window, and one naming nothing is kept, inert and
named in the toast. Each failed before the build (the panel kept, nothing restored).

### A2. A window for a book still being prepared

`desk_windows.kind` gains `'preparing'` (migration 272, `272_reader_workbench_preparing_windows.sql`, a
temp-then-rename rebuild as 266's; the head fixture holds it, its README section names it): `PreparingRef` names the
source alone (`{"kind": "preparing", "source_id"}`), since a book being prepared has no reading. The previous plan
named only the content reference; the table's CHECK needed the migration as well. Backend test:
`tests/test_reader_rd_retire_migration.py` (the head fixture holds 272 in rollback mode; the rebuild keeps every row
and changes only `desk_windows`, matching the head; a preparing reference round-trips through `desk.apply`, and one
naming no source or also a reading is refused).

On the desks a book still being prepared opens in a window of its own (the app's open request, the opener, first
run): the Reader's `PreparingView` (the original's pages, the progress line, a stopped book's action and retry),
lazily loaded, with no "← Library" (closing the window is the way out). When it is ready (the view's own poll, or a
ready card at restore), the book's window replaces it in its place, focused, at the page the learner had reached in
the original (the hand-over's position, `SourceWindow.handoff` → `ReaderOpenSource.handoff`). The library's copy of
the card is replaced by the ready one first: a window that mounts in the store's commit, before the library state
updates, reads the ready card (`readyCards`), or it would reopen the preparing view. Test: the same file, "a book
still being prepared opens in a window of its own, with its original and its progress, and becomes the book's window
when ready" (asked again, the same window is focused; ready, the stored window is the book's source window).

### A3. The desks are the only Reader surface

- `App.tsx` mounts no `ReaderScreen`: the Reader place and the plan's reading are the desks, or "Open a library to
  read in it." with no library open. Every route that opened the old Reader sets the book (or search words) and a new
  open request for the desks: Today's threads and citations, the Library shelf, Continue reading, Add, the startup
  restore, a check's or a problem's return, feedback's "Back to where you studied this" (fixed, RDX-2), a goal's
  plan reading, a lesson's "Look in my library", the palette's Ask (the companion). The desks' own deep links are
  their open requests (`SourceWindow.entry.test.tsx`, `App.desks.test.tsx`).
- The surface switch: `app/shell.ts`'s per-machine `learnloop.reader.surface` (remembered/remember functions and
  their test) is gone, and `DeskShell`'s `onLeave` and "old Reader" button with it. It was never a `learnloop.toml`
  field, so `RETIRED_FIELDS` has nothing to carry and the identity pins and the effective-defaults golden are
  unchanged (both run green). A machine whose storage still says `"reader"` gets the desks
  (`App.desks.test.tsx`, "is the desks even where an older version remembered the old Reader for this machine").
- The app heard the old screen's open book (`onSourceChange`); the desks now report the book being read
  (`DeskShell.onReadingChange`: the focused book window, else the one focused last, else the first on the desk in
  view, or none). The app remembers it per library (closing the last book window forgets it), offers it as Continue
  reading, holds its notices while one is open, and reopens the Reader on a check's book when it is another. Until the
  desks first report, the book restored at startup stands for it (RDX-3).
- **The Reader config switches, audited** (spec §21.1's last row). Every switch the old screen read is read by the
  scoped source a window mounts (`reader_inquiry.enabled` → `inquiryEnabled`, `tutor_qa.reader_enabled` →
  `readerEnabled` and the sidecar's `_require_reader`, `workbench.enabled`, the cue and recap switches, `reader_intent`,
  `reading_paths`, `library_ask`, `side_by_side`, `reader_tutor`), or by the sidecar; the standalone branches read
  no switch of their own. So none is retired: each is kept, as the spec says when something else reads it.
- The app's own tests (11 files) mount a stand-in for the desks (`fixtures/deskShellStub.tsx`): what the app asks of
  them (the open request, the ask count, the workbench's resume, the hand-offs) is on its element, and it reports as
  the desks do. Retired: three assertions on the old screen's `besideTrail` (App.today, the CA6b cases), covered by
  `App.desks.test.tsx` "back from a check begun in the paired book … still a pair", and fixRound4's `data-title`
  (the open request carries no title: the desks read it from the library).

### A4. What only the standalone branches offered

| Standalone offer | On the workbench |
|---|---|
| The list of books and its search | The desks' opener (`+ open beside`) lists every book; the desks' search (`[data-desk-search]`) searches them; ask across the library and Compare are the Compare window (`CompareWindow.desk.test.tsx`, `CompareWindow.bare.test.tsx`: the old library page with no book open is a Compare window with none, keep and reopen, the take band, a practice pick, both exercise actions) |
| The shelf with no book open | The Library place's shelf, one key away; the desks' shelf lists the desk's windows |
| "← Library" | Closing the window (`alt+w`, ✕); the Library place (Alt+2) |
| "desks ▸" | Gone by design (no second surface) |
| The header's "I want to" | The source bar's "I want to" (per window; it was already there) |
| The header's re-read note | **Built**: the source bar says "This book was read again: you're near …" (`[data-reread-note]`) |
| The header's quick-checks toggle | **Built**: the source bar's "quick checks on/off" (the same per-device preference). It had no workbench home: a learner who turned checks off in the old Reader could not turn them back on |
| The header's progress bar and section name | The window's title bar names the section in view; the percent through is **dropped**: display only, the scroll position shows it |
| The header's line "Select a passage to ask about it…" | **Dropped**: instructional copy; the desks' footer hints and the intent box carry the same |
| The key bar | The desks' footer hints and which-key; wrap up is the window's `w` (`SourceWindow.wrapup.test.tsx`); `x` still opens "also in your books" |
| The collapsed rail's handle and `\` | **Dropped**: a window's rail lives in its panel window and is never collapsed (`railCollapsed` pinned at `false`) |
| The offline demo chapter | **Dropped**: it showed only while the sidecar was down, and its captures were never kept; the desks need a library, and the app says when the sidecar is unreachable |
| The reader-off view | **Built**: the desks say once, with the setting, when `tutor_qa.reader_enabled` is off (`[data-desk-reader-off]`; `App.desks.test.tsx`) |
| A book still being prepared | A2's window |
| "Back to Today" at a book's last section (`onOpenToday`) | **Dropped**: only the old screen passed it; Today is one key away (Alt+1) |
| The palette's Ask into the Ask rail (`askRequest`), and its wait in the working posture | The palette summons the desks' companion (`SourceWindow.inquiry.test.tsx`); a problem is worked on its pad, so nothing waits |
| A search hit's relevance signal (`reader.retrieval_open` with the search's receipt) | **Dropped, for the orchestrator**: only the list's search sent it. It records only while a new embedding space is on (`embedding.local` or `.fallback`, both off by default), so by default nothing was recorded. The desks' search (`search_everything`) carries no receipt; giving it one is a backend follow-up if the opt-in experiment needs the opened signal |

Each drop is display or default-off; none loses something a learner did or stored.

### B. The tests

- **64 standalone-mount files.** 41 component tests mounted `ReaderScreen` directly: they mount `ScopedSource`
  (same props); 265 of their 306 cases passed unchanged. 11 app tests mounted a stand-in of the screen: they mount
  the desks' stand-in (A3). The rest named the file in a path guard or a comment: the classic-is-base evidence
  (`app/classicIsBase.test.ts`), the capture-listener pin, and three lints that read the Reader's sources as text
  (`attentionBudget`, `voices`, `scrollStaysInReader`). **Found:** those three lints still read the thin
  `ReaderScreen.tsx` after step 1 and so missed the moved source; they read `ScopedSource.tsx` now, and pass.
- **The switch-off snapshot tests** ("byte-identical with the switch off": intent, reading paths, recap, tutor,
  workbench, library ask): their snapshots held the old header and key bar. Rewritten, and
  `scripts/rd_retire/snapshot_frames.mjs` showed every entry equal to the old one once the old header and key bar
  and the new source bar are taken out (24 entries, plus library ask's); nothing else moved.
- **The 41 cases that reached the frame** at first: 6 passed once the source bar carried "I want to" and the re-read
  note, 12 with the snapshots rewritten (above); of the other 23, ported in place (a key retried until it acts instead of waiting on the key
  bar's offer, the rail opened with `\` after Esc, the source bar's "I want to"; 16, four renamed), moved to the real
  desks (`CompareWindow.bare.test.tsx`, 5), or retired (2: "Shift+Enter in the library search is today's Enter with
  library_ask / reader_inquiry off": the list's search box is gone; the switch stays pinned by the palette rows). The
  covering test is named at each site.
- **The 28 left-out cases** (`standalone_only_cases.json`): 18 ported to the step-1 copies (leaving a book is closing
  its window, `cleanup()`; another book or a search hit is a new mount with a reading, as a window mounts it; "I want
  to" and the re-read note are the source bar's), 1 moved to the real desks (`SourceWindow.retired.test.tsx`: a book
  window still opening names its book in one line and then shows its reading), 9 retired: "← Library goes to the
  Library…", "the Reader's own book list offers no demo chapter…", "with no book open, the Reader shows the Library's
  own shelf", "a lesson's Look in my library opens the library search…" (covered by `SourceWindow.entry`'s "Look in my
  library opens the desks' search"), "F7: the newest count of a book left behind is still sent when the Reader
  closes" (leaving and closing are one step now; covered by the ported F7 retry case and the copy's F3 resend),
  "lists a book that is not ready yet on the picker" (covered by `PreparingWindow.desk`'s first case and the copy's
  preparing case), "still says so when the reader really is off" (covered by `App.desks`' reader-off case), "opening
  another book from its library card leaves a way back" (covered by `SourceWindow.exercises`' open beside and
  `DeskShell.test`'s opened-beside relation), "opening a search hit sends the result's receipt…" (the dropped signal,
  A4). Each copy's header says where each case went.
- **`ReaderScreen.parity.test.tsx`**, which step 1 did not copy, is `ScopedSource.parity.test.tsx` now (the
  transcript and notes inquiry, the restart rule, `[`/`]`); its `\` collapse half is retired with the collapse.
- **Retired whole**: the 23 `ReaderScreen.*.test.tsx` originals and their snapshot (their cases are in the copies);
  `readerKeys.test.ts` and `searchBasis.test.ts` (their modules were the old key bar's and list's alone);
  `paletteAsk.test.tsx` and `paletteAskPostures.test.tsx` (the palette's ask into the screen's Ask rail and its wait
  in the working posture: the screen-only `askRequest` is deleted; the palette summons the companion, covered by
  `SourceWindow.inquiry.test.tsx` "the palette's Ask … summons and never dismisses").

### C. The deletion

Deleted: `screens/ReaderScreen.tsx` (332 lines), App's lazy `ReaderScreen` and both mounts, `app/shell.ts`'s surface
switch, `DeskShell`'s `onLeave`; in `ScopedSource.tsx` the `standalone` prop and its four calls, the list's search state
and effect, the offline demo (`offline` pinned `false`), `backToLibrary`, the library page's practice pick, the
palette's `askRequest` path, the screen-only props (`onSourceChange`, `onOpenLibrary`, `onOpenToday`, `shelf`,
`askRequest`, `initialLibrarySearch`, `onOpenDesks`), the rail collapse and its preference (`railCollapsed` pinned
`false`); `types.ts`'s `StandaloneShell` and its four contexts; `screens/reader/readerKeys.ts`, `searchBasis.ts`; the
path panel's `PathPanel`. `railHost` and `RailScope` stay. Lines: `ScopedSource.tsx` 4,884 → 4,740 (with the source
bar's additions), `types.ts` 216 → 133; the deletion commit removes about 7,800 lines, almost all of it the 23
original test files.

Kept for a later step, recorded: the scoped source's non-windowed branches (the nested second pane of side by side,
the rail's own layout, `offline`'s dead conditions) are reached only by its tests now; they go with the rows that move
the Guide, Notes, Ask, checks and recap out of the portal. `scripts/rd_retire/check.mjs` and `generate.mjs` are step
1's record and read files that no longer exist.

### Proof

- `npm run typecheck` clean; the whole vitest suite after A and B: 448 files, 4,694 tests passed; after C: 422 files,
  4,500 tests passed (the 23 originals, the two palette-ask files and the two retired modules' tests gone; the parity
  copy added); `cargo check` clean.
- Desk harness (`vite build --config vite.desks.config.mjs`, then `uv run --no-project --with playwright==1.65.2
  --with pillow==11.3.0 python scripts/desk_harness/run.py`): 207 passed, 0 failed after A and again after C, on a
  quiet machine. **A flake, not this branch's:** three runs while the vault generators ran beside them stopped the
  `checks` run at "show it anyway" (`Page.click` timed out: the cost dialog, placed from the companion's pill in
  `checks/VeilLayer.tsx`, lay below the 960 px viewport); the same run with the pre-deletion source failed the same
  way, and every quiet run passes (22 of 22). For the checks worker: the dialog is not kept inside the viewport.
- Python: `tests/test_reader_rd_retire_migration.py`, `test_migrations.py`, the RD0 and RD4 migration tests,
  `test_reader_rd1_model_parity.py`, `test_reader_rd0_protocol.py`, `test_identity_pins.py`,
  `test_effective_defaults_golden.py`, `test_tracked_fixture_databases.py`, `test_public_tip_guards.py`, the guards
  that read frontend paths (`test_rw5c_block_policy.py`, `test_reading_hardening_2_fixes.py`), `test_table_roles.py`:
  green; ruff clean; lint-imports 55 kept, 0 broken.
- Generated references regenerated after the last code commit (`_scripts/generate_all.py`, no uncommitted input);
  `desktop_validate` counts recomputed: 433 TypeScript files, ACTIVE 439 (406 entry-reachable, 23 vitest-support:
  `fixtures/deskShellStub.tsx` and `fixtures/readerRenderView.ts`, which only tests read now); the four validators
  pass.
- **Not run here:** the visual-reference comparison (`visual_reference.py`) needs the private reference directory;
  the orchestrator runs it.

### Bugs found (ledger)

- RDX-2: feedback's "Back to where you studied this" opened nothing on the desks after any earlier open request.
- RDX-3: Continue reading after a restart on another place opened the Library, not the remembered book.

### The gate round: merged with the RD7 fix round and main

At the coordinator's request, before the gate: `reader/rd7-fix-frontend` at `475a29f5d1` merged (batch 5's per-verb
protection fix, main at `1293ec6f96`, the RD7 fix round's allowlist hold and the app's check gate), then `origin/main`
(the workbench superset, landed; only generated notes differed).

- **Migration 272.** The fix round's `271_reader_workbench_inline_checks_fix.sql` lands first, so this branch's is
  `272_reader_workbench_preparing_windows.sql` (temp table `desk_windows__272`; every mention renamed). 271 touches
  `check_administrations`, `check_veil_sets` and the video chapters' guard, not `desk_windows` (checked), so the rebuild
  carries 262's definition as it stands. The head fixture was upgraded again from the merged 271 head in its own commit
  (`[272]` applied only, rollback mode, no companions, `integrity_check` ok, `foreign_key_check` empty, `desk_windows`
  alone redefined, 7,909,376 bytes) with its README section.
- **After the merge.** App's `onDesks` is the Reader place with a library (no surface); "back to the check" no longer
  chooses a surface; the check gate's test leaves the desks by Today's key only (the desks' "old Reader" button is
  gone, and the button sat in the header's safe tool group, so the hold needs no change for it).
- **This branch's surfaces under an open check** (the fix round's hold is an allowlist: what is not marked safe is
  held):
  - a preparing window: `WINDOW_VEIL_DECISIONS.preparing = "whole"` (its original's pages carry the book's words but no
    passage the server can judge; only a source's and a video's own text can show);
  - the source bar's re-read note and quick-checks toggle, and an inert window of an unknown kind: held by default with
    the window's body, deliberately (nothing marks them safe);
  - the reader-off note: on the safe list deliberately (one fixed line about a setting, no study material);
  - the book being read (`onReadingChange`): not told to the app while a check holds the desks, since the windows' heads
    show neutral titles then, and told once the check is answered or set aside (`screens/desks/readingReport.test.tsx`,
    which fails without the hold).
- **The veil walk with a preparing window.** The harness fixture's `?preparing=1` puts a book still being prepared in
  the library and its preparing window on the softmax desk; the `veilsweep` run opens with it and adds its progress line
  to the phrases it looks for: at every point of the walk nothing of it shows, and the walk checks the window is held
  whole (body veiled, its status line inert).
- The desks' stand-in in the app's tests keeps its open book across a remount, as the desks do (the check gate can
  mount the Reader place again; "closing a book forgets it" relied on it).

**Proof on the merged tree** (`9f375c2cf6`, then the main merge, which changed generated notes only): typecheck clean;
the whole vitest suite 427 files, 4,531 tests passed; `cargo check` clean; every harness run on a fresh `vite build`:
234 passed, 0 failed (veilsweep 26 of 26 with the preparing window); Python (migrations incl. 270, 271 and 272,
tracked fixtures, upgrades, table roles, identity pins, effective-defaults golden, structure ratchets, architecture,
test layout, desktop RPC contract, mobile allowlist, the nouns scan, the RD7 files, the RD0/RD1/RD4 desk tests, public
tip guards, the frontend-path guards): 1,465 passed; ruff clean; lint-imports 55 kept, 0 broken;
`check_gate_partition.py`: 34,595 collected (landing 34,529 + arc_close 66). References regenerated after the last
code commit; the four validators below.
