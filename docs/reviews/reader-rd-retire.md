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
| Ask rail, branches, detour strip, reconnect, docked Ask and overlay | | | pending |
| Intent box, active reading | | | pending |
| The tutor that looks things up | | | pending |
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

(filled as rows close)

## 5. Product decisions asked

(none yet)
