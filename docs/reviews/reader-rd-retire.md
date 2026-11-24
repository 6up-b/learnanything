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
| Guide rail: cues, reading-path card, deliverable slice | | | pending |
| Ask rail, branches, detour strip, reconnect, docked Ask and overlay | The companion (§8) asks; its answers now act on the book's window as the Ask rail's did: a claim of a reading already open peeks there (`openClaim` → the window's inquiry), a companion follow-up joins the window's detours with its parent, walking back (Alt+← or a crumb) shows the inline reconnect under where the learner was, and its "still unclear" asks again in the companion as a branch of that question (`askElsewhere`; `CompanionAsks.ask` takes a named parent). The palette's "Ask the tutor about this" summons the companion while the desks are the Reader (`askRequest`) | `windows/SourceWindow.inquiry.test.tsx`: a claim peeks with the strip and Alt+← back (the restore names the origin passage); a follow-up's branch crumbs, the reconnect inline under the origin and its "yes" naming the root; "still unclear" with words asked in the companion with `parentExchangeId` the root; the palette's Ask summons and never dismisses. The old screen's inquiry suites still pass. Harness `intent` run: a claim of the open book peeks in its window, the strip in the desk's dark tokens (new: the window's lines above its sheet took the paper's ink on the window's dark, unreadable), and alt+← walks back | **Built and demonstrated.** Before: a claim jumped with no way back, a companion follow-up left the window's strip empty, no reconnect ever showed on a desk, and the palette's Ask did nothing there. Fail-first: the first three cases and the palette case failed before the build. RD3b's choice stands: Practice and Today keep their own Ask hosts (`docs/reviews/reader-rd3b.md`) |
| Intent box, active reading | The intent box inside each source window (unchanged); every routed action now has a destination on a desk with no Guide or Notes panel: an ask goes to the companion, asked at once on the selection in the routed answer mode (`CompanionAskInput.answerMode`; an empty Enter opens it on the selection); the active-reading card (and "another way") shows in the window under the last passage it is about, on the text and on the original PDF (an inline note), and its fold follows it; "what matters here?" opens the desk's path (the goal's path view, else the reading's path beside); figures, captures and the presets were already in the window | `windows/SourceWindow.intent.test.tsx`: the routed ask reaches `companion.ask` (no `reader.ask`) with the selection and `help_me_reason`; the next-step question's card under its passage, before the next, and closed; "what matters here?" opens a Reading path window. Harness `intent` run: with the box shown, c, / and typing keep their meanings | **Built and demonstrated.** Before: a routed ask opened the Ask tab of a rail the desk hides (nothing visible, and `reader.ask` was sent), the active-reading card lived only in the Notes rail's header, and "what matters here?" switched a hidden rail to its Guide. Fail-first: all three cases failed before the build |
| The tutor that looks things up | `companion.ask` runs the Reader's retrieval unchanged (it inherits `ReaderAskInput`); the companion now carries RW1c's controls: under an answer that looked things up, the abstention line, the verbatim excerpt "from your books" (opening its passage, a peek where it is open), the bridge to the learner's work, and "another way" / "that didn't help…", which ask again as a branch of that answer with `retrievalIntent` alternative / remediate; the personalized chip in its input, sent with every ask while retrieval is on (the vault's default until switched). The window's routed asks and reconnect branches send it too | `companion/Companion.tutor.test.tsx` (real desk): excerpt, bridge and its passage opened as a peek; another way and that didn't help with their intents and parents; abstention; the chip sent and switched; with retrieval off no chip, no controls and nothing extra sent. Backend: `tests/test_reader_rd3a_companion_ask.py` (the companion answers with the Reader ask's reply) and the RW1c suites through the shared core | **Built and demonstrated.** Before: the companion showed only the answer's words and claims, so an answer that looked things up lost its excerpt, bridge and abstention line, and there was no way to ask another way, to say it didn't help, or to switch personalization. Fail-first: four cases failed with the controls withheld (the off-switch case passes both ways, as it should) |
| Workbench (RW2) | | | pending |
| Notes rail | Margin notes (§7.1): with no Notes panel on screen, a passage carrying the learner's annotations shows "›" in its margin (30 px left of the text, drawn by CSS so a selection never quotes it); it opens a card under the passage with each annotation's kind, anchor state and words, to edit, delete (the window's undo) or, when the book was read again, re-anchor to this version or to a selection (the Notes rail's card, extracted as `AnnotationCard` and shared). A PDF highlight opened, or a window a search result opened for a note (its `annotationId` in the window's view), opens that card being edited. A capture made from the menu (Note in margin, an append's highlight) is read again by the windows showing its reading, so its mark shows at once. What this knows opens the passage, where the mark is | `windows/SourceWindow.notes.test.tsx`: the mark and edit; delete and undo; re-anchor; a PDF highlight's card; a window opened for a note; a note written with `n` shows its mark at once and opens. Harness `intent` run: the `n` note's mark is CSS-drawn and 30 px left of the text, and its card holds the words with edit and delete | **Built and demonstrated.** Before: edit, delete and re-anchor lived only in the Notes rail; a PDF highlight opened into a hidden rail; a search result for a note opened its passage but not the note; a menu note did not show in the window until it was reopened. Fail-first: the first four cases failed before the build, and the last two each failed with their piece withheld. The fixture sidecar now places a capture on its selection's passages, as the sidecar does |
| Margin cues, alt+↓/↑ | Margin marks in each source window, keys unchanged (the Reader's cue hooks through the window's listener hub); new: with no Guide panel on screen the window keeps the Guide footer's marks controls itself, the density at the foot of its reading and what a mark changed (set aside, fewer marks, off for the book) held at the window's foot with its undo | `windows/SourceWindow.cues.test.tsx`: two book windows each draw their own marks, Alt+↓/↑ move between the active window's marks only and follow the active window; not relevant… undone in its window; fewer marks and off for this book undone in the window, the density control at the foot of the reading, the other book untouched. The old screen's cue suites still pass (impressions from an offscreen window: `ReaderScreen.discoveredCues.test.tsx`, windowed) | **Built and demonstrated.** Before: a change made from a mark on a desk had no undo and no way back but Settings (the receipts and density lived in the Guide rail's footer). Fail-first: the two undo cases failed before the build. The harness fixture has no cues, so this is proven in jsdom only |
| Library ask, compare, keep, roles | | | pending |
| Exercises from my sources | | | pending |
| Figures and Show me | | | pending |
| Last time here, wrap up, digest | With no Guide on screen, the recap card shows in the source window on return, held at the window's top while open (wherever the window opened in the book) and at the top of the reading once folded, recorded as shown once and only there; `w` opens the session's Wrap up in the window; closing the desk's day (the drain, `alt+shift+q`) shows today's pads first, then each reading's Wrap up (with its digest and follow-ups) named by its book (`DrainPanel` gains a slot after the pads; each window puts its own Wrap up there, with its chips, undo and restore). The leave-the-Reader offer outside the desks is unchanged | `windows/SourceWindow.wrapup.test.tsx` (real desk): the card above the reading, recorded once; `w` opens Wrap up in the window (`wrap_up_opened`); the drain shows the pads first, then the Wrap up, its "resolve" calling `reader.set_inquiry_status`. `windows/SourceWindow.recap.test.tsx` changed with the behaviour: no panel, or a hidden one, shows the card in the window, recorded once; a visible panel shows it in the panel, still once; a preview records nothing. Harness `intent` run (`?recap=1`): the card at the top of the book's window, recorded once; the drain's Wrap up after the pads, named by its book | **Built and demonstrated.** Before: recap and Wrap up lived only in the Guide's header, so a desk with no Guide panel showed neither, and the drain had no Wrap up. Fail-first: the three desk cases failed before the build. Skimming still mutes the card, but a desk has no way to choose skimming (§5) |
| Cold follow-ups | Inline checks (RD7, another worker) | | not this branch's: RD7 closes it |
| Reading paths | | | pending |
| Side by side | | | pending |
| Watch panel | Video windows (§7.4) wrap `SourceWindow`; the Reader's synchronized watch panel inside | `tests/test_sidecar_reader.py::test_watch_plan_returns_video_id_for_youtube_source`; `reader/YouTubeWatchPanel.instance.test.tsx` (each frame takes only its own time messages); harness `desks` run (two players' frames checked) | **Demonstrated** (by the audit; unchanged here) |
| Quick checks, authored questions | | | pending |
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

Routed to the workbench on this branch:

- **The palette's "Ask the tutor about this" while reading** (`app/App.tsx`): on the desks it now summons their
  companion (`DeskShell` `askRequest`), with or without a book in a window; on the old screen it is unchanged.

Still listed (each waits on its row or on phase 2's targeted open):

(filled as rows close)

## 5. Product decisions asked

- **Skim, read closely, mark for later on a desk** (the audit's §5, no parity row). The old screen's header offers the
  mode; skimming mutes the recap card, section prompts, cues and dose offers, and tells the app to hold the
  leave-time offer. A source window has no header and so no way to choose it: on a desk every reading is "read
  closely". Options: (a) the choice in the window's source bar beside the view switch, per window; (b) one choice per
  desk, in the desk's top bar; (c) drop skimming on the desks (the desk's own geometry is the learner's "skim"),
  keeping it on the phone and the old screen until it goes. Recommended: (a), since the mode is per reading today and
  the bar already exists. Not built until chosen.
