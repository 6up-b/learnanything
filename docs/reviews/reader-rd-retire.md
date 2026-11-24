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
| Notes rail | | | pending |
| Margin cues, alt+↓/↑ | Margin marks in each source window, keys unchanged (the Reader's cue hooks through the window's listener hub); new: with no Guide panel on screen the window keeps the Guide footer's marks controls itself, the density at the foot of its reading and what a mark changed (set aside, fewer marks, off for the book) held at the window's foot with its undo | `windows/SourceWindow.cues.test.tsx`: two book windows each draw their own marks, Alt+↓/↑ move between the active window's marks only and follow the active window; not relevant… undone in its window; fewer marks and off for this book undone in the window, the density control at the foot of the reading, the other book untouched. The old screen's cue suites still pass (impressions from an offscreen window: `ReaderScreen.discoveredCues.test.tsx`, windowed) | **Built and demonstrated.** Before: a change made from a mark on a desk had no undo and no way back but Settings (the receipts and density lived in the Guide rail's footer). Fail-first: the two undo cases failed before the build. The harness fixture has no cues, so this is proven in jsdom only |
| Library ask, compare, keep, roles | | | pending |
| Exercises from my sources | | | pending |
| Figures and Show me | | | pending |
| Last time here, wrap up, digest | | | pending |
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

(none yet)

## reader/rd-retire-parity-b

| §21.1 row | Replacement on the workbench | Test (real bodies unless noted) | Verdict |
|---|---|---|---|
| Workbench (RW2a–d) | Problem pads (§15.2). A problem a book window opens (work through this, an exercise, a check, a resume, back from feedback) is handed to the desk: a pad of kind `problem` bound to its workbench session (`create_pad` with `workbenchSessionId`, or the loaded pad of that session) joins the desk's stack and comes into view, and the window goes back to reading instead of showing the working posture over the book. The pad hosts the workbench itself (`screens/workbench/Workbench`, unchanged): steps saved to `workbench_steps`, the help ladder, the check, I'm stuck, Submit (the shell's hand-off to feedback with the way back to the problem's passage), Leave for now and Abandon, the book in its own window ("show in the book"). Set aside or abandoned, the pad keeps a way back (resume / reopen); submitted, it shows the problem read-only. `screens/desks/problem/` (`ProblemPad`, `problemPads`); `ReaderWindowing.onWorkOnPad`, `SourceWindow`, `DeskShell` (`workOnPad`, `problems` on the pads host), `PadStackWindow` (the problem pad's case) | `problem/ProblemPad.desk.test.tsx`: work through this on a selection opens `workbench.open` and a problem pad in the stack with the workbench, and no posture in the book's window; on the pad a step saves, the help ladder opens (`workbench.suggest_help`) and the check runs (`workbench.check`), Submit sends `workbench.submit` and hands the result to feedback with the problem's card and passage, and the pad shows it submitted; Leave for now keeps the pad, and resume reopens the same session. The old screen's workbench suites still pass | **Built and demonstrated.** Before: on a desk the problem opened as the old working posture inside the book's window. Fail-first: all three cases failed with the hand-over unwired. Not built: finding an earlier problem pad that is not loaded (a second open of the same session in a fresh desk view makes a second pad for it); RD8a's ink ladder on problem pads stays stopped, as recorded there |
| Figures and Show me (RW5a–d) | §13.1. Source insets stay in the book's window (the Reader's figures, unchanged). Show me (the menu's verb on a passage, a cue, a highlight or a pad line) now puts its figure in the companion's answer: "◇ Show me · a figure for <source> p.<page>", the live widget itself (the Reader's `FigureInline`, open, predictions recorded as the Reader's), **view source** (the figure's source, display tier, no kernel), **move to scratchpad** (the `figure` block in the running pad of the desk it was asked on, as before) and **not useful** (removed, and logged as the salience-only reader event `figure_not_useful`), with the footer "it is help, not a check"; the companion is summoned docked if it was hidden. **Shared parameters**: every instance of one figure shares its parameters for the app's run (`reader/figures/sharedParams.ts`), so dragging one moves the others. `companion/companionFigures.tsx`; `Companion`'s `figures` slot; `DeskShell` (`showFigure` in the menu's context, `landFigureBlock`); `menu/verbs.ts`; `reader_inquiry.CLIENT_ACTION_EVENTS` (+`figure_not_useful`) | `companion/Companion.showMe.test.tsx` (real desk): the figure in the companion, named for its source and page, live (sliders), with the footer, and nothing written to a pad by itself; view source shows its source; move to scratchpad writes the figure block in the running pad and the figure leaves the companion; not useful removes it and `reader.log_activity` records `figure_not_useful`. `reader/figures/sharedParams.test.tsx`: two instances of one figure move together, another figure keeps its own values. `DeskShell.menu.test.tsx`'s Show me case now finds the figure in the companion and moves it to the running pad of the desk it was asked on, with another desk shown. Backend: `tests/test_figures_rpc.py::test_the_client_records_a_companion_figure_set_aside_as_not_useful` | **Built and demonstrated.** Before: Show me only landed a figure line in the running pad (no live widget anywhere on the desk, no view source, no not useful), and two instances of a figure kept separate values. Fail-first: the three companion cases with Show me routed to the pad, the shared-parameter case with per-instance state, and the backend case (the event was refused). **View source and the notebook frame:** no figure carries a notebook today (`FigureViewDto` has none, and nothing exports a figure to marimo), so view source shows the figure's own source (its spec, or a sketch's program) in place, display tier; a figure-notebook window (§13.1) needs that export, which is not built. Visual: the reference set shows no companion figure (`#figopen`, `#figsrc` were not applied in the plain variant; in the goal variant they applied with the companion on its thread; `#figmove` threw in the page); only the pad's `◇ fig` gutter mark (`pad_mark_fig`, `#figmark`) is comparable, and it is unchanged here |

Notes on these two rows (reader/rd-retire-parity-b):

- **Harness.** The `showme` run (`scripts/desk_harness/run.py --only showme`, 7 checks) drives Show me from the menu
  on a book passage in headless Chromium: the figure in the companion, live (sliders and a plot), its buttons and
  footer, JetBrains Mono, nothing clipped sideways, nothing in a pad until moved, view source, and move to
  scratchpad writing the running pad's figure block. The fake sidecar answers a figure build with a fixture figure
  (`fixtures/desks/figures.ts`, a project-authored spec from the figure golden corpus). The problem pad has no
  harness run: the fake sidecar has no workbench service, so RW2 on the pad is demonstrated in jsdom with the real
  desks only.
- **Visual stages.** `visual_reference.py --stage rd3`: `findings rd3: 7 (colour 1, geometry 4, missing 2)`;
  `--stage rd4`: `findings rd4: 19 (geometry 1, missing 15, type 3)`, the same counts as the last full run on this
  reference set. No captured state shows a companion figure or a problem pad.
