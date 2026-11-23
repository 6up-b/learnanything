# Reader workbench v2, RD3b: the companion and search in context (frontend)

The frontend half of stage RD3 of `docs/specs/spec_reader_workbench_v2.md` (§8, §9.3, §16's RD3 row). Branch
`reader/rd3b-companion-search-ui`, on the RD2 fix round's tip with main (RD3a) merged in. It calls RD3a's
contract as built (`companion.ask` / `companion.ask_job` / `companion.ask_cancel`, `companion.history`,
`search.everything` / `search.job`; `docs/reviews/reader-rd3a.md`). There is no backend change, migration, algorithm
tag, prompt change, config field or Rust change, and the phone is untouched. The owner deferred performance: the
latency acceptance numbers are recorded as information.

## 1. What landed

| Scope item | Where |
|---|---|
| The companion's geometry and state machine: the four docks, anchored summon (10 px below the anchor if it fits, else above, clamped), the nearest dock for a drop, the pill, avoid, and the transitions of `c`, `shift+c`, hand-off and hide | `F:screens/desks/companion/model.ts` (pure) |
| Questions as polled jobs: asked at once, polled through the app's one poller with the asking window as the poll's owner, honest asking / answered / failed / cancelled (kept) / interrupted states, retry, cancel, a follow-up branching from the thread's last answer about the same reading, threads kept per desk across the shell's mounts | `F:screens/desks/companion/asks.ts` |
| The `Companion` panel: grab handle, tabs `◇ tutor` / `history`, `c hide`, the context line ("following <glyph> <window>", "◎ goal in context", "earlier · <dates> ›"), the desk's thread, the selection chip, a real input (Enter asks); docks, the drawer's tab, summon from `scale(.9)`/blur 8 px at the anchor, dissolve in place, hide down out of the dock, hand-off and snap as FLIP moves, avoid, and the overview's pill | `F:screens/desks/companion/Companion.tsx`, `styles/desk.css` |
| Answers that act: claims open beside through the desk model (or focus the window that already shows the passage); "open the thread as a window"; previewed diffs with accept and "not this", ready for pads | `Companion.tsx`, `F:screens/desks/companion/DiffProposal.tsx` |
| History by day and desk (`companion.history`), with its words search, "before desks" for backfilled rows and the anchor button | `Companion.tsx` (`HistoryView`) |
| Thread windows (`ContentRef` `thread`): the whole thread the named exchange belongs to, read from the source's ask history; the window's view carries the reading | `F:screens/desks/windows/ThreadWindow.tsx`; `DeskShell.tsx` `paneBody` |
| Search in context: words at once from `search.everything`, the client's "open on this desk" group first, three rows a group until `tab`, an `off` group saying why, the meaning job polled through the poller and merged with "· by meaning", its why-not line, insert mode (`insert` prop: ↵ inserts), the rofi animation, results opened through the desk model (or focused where already open) | `F:screens/desks/search/model.ts` (pure), `F:screens/desks/search/SearchPanel.tsx` |
| Where search opens: `/`, the shelf's "/ switch". The Find verb is RD5's menu and insert mode RD4's pad menu: both call the same panel | `DeskShell.tsx`, `Shelf.tsx` |
| What a question is about: the selection in the focused window (its passages and its quote, rendered math read back as TeX), else the focused source's reading place, else the passage at the top of its window | `F:screens/desks/selection.ts`; `DeskShell.tsx` (`groundingFor`, `firstVisibleSpan`) |
| Keys: `c`, `shift+c`, `alt+c` (while typing) and `/` built (no longer waiting for this stage); the search panel is the menu scope | `keys/router.ts`; `DeskShell.tsx` (the router's `menu` flag) |
| The dock and whether it shows, remembered on the desk | `model/workspace.ts` `setCompanionDock`, `setCompanionShown` (RD0's `set_dock`, `set_companion_shown`) |
| The pill moved in step with the zoom | `overview/controller.ts` (`followers` on the zoom's targets, called with each frame's q and with null at clean-up) |
| The fixture's companion and search (a fake tutor the harness can hold open) | `F:fixtures/desks/companion.ts`, `fakeCore.ts` |

### How the companion moves

- **Docked or hidden, it never moves.** It is placed in the stage's own coordinates, outside the world, so scrolling,
  panning, reordering, gathering, pairing and switching desks leave it where it is. The dock and whether it shows are
  remembered on the desk (`set_dock`, `set_companion_shown`) and read from the desk the desks open on; after that the
  companion is app-wide and stays put across desk switches (see judgment call 3).
- **Anchored, it leaves only by a hand-off or a dissolve.** A hand-off (the view moves: the strip pans, the desk or
  focus mode changes, the overview opens; or its text scrolls away more than 250 ms after it opened; or its handle is
  dragged) is a FLIP from the rect it showed at to its dock's. A dissolve fades, blurs to 10 px and grows to 1.025 in
  place over .26 s, then it is hidden. Neither passes through the dock (frame-sampled in the harness).
- **The drawer rule.** `c` with nothing showing opens it at the cursor (the selection's rect, else the last pointer
  position over the stage; with neither, at its dock). `c` while anchored dissolves it; `c` while docked sends it to
  the drawer. `shift+c` or the tab opens it at its dock, or hands an anchored one to its dock.
- **Avoid.** When the selection lies under a docked companion it slides sideways once, the shorter way that stays on
  the stage, at most 600 px, on its own `translate` property so the FLIPs and the zoom keep `transform`.
- **The overview.** The panel, the drawer's tab and the pill stay mounted through the overview and are faded, not
  removed; the zoom's controller calls the companion with each frame's q, so the panel shrinks toward the pill's
  corner and fades as the pill fades in, and the commit changes nothing on screen (the RD2 commit-identity checks still
  pass with the companion on the stage).
- **Reduced motion.** Every move is an opacity fade of .2 s; search's animation is removed.

## 2. The poller adoption

`api/poller.ts` (RD1's one client poller: one cadence, coalesced by key, backoff, owners paused with their windows)
now carries two kinds of job:

- **the companion's questions**: `companion-ask:<request id>`, owner = the window the question was asked from. The
  shell already keeps every window's pause in step with the poller (`setOwnerPaused`), so a question asked from a
  window whose desk is left, or which is a card in the overview, is not read until that window is back.
- **search's meaning job**: `search-job:<job id>`, no owner (the panel is modal on the current desk). A newer search
  makes the older poll stale (it stops at its next answer) and the server supersedes the older job.

**Not ported: the old Reader's three job polls** (`useReaderInquiry`'s check poll, `useReadingProgress`'s authoring
poll, `ReaderScreen`'s exercise import poll). They run at 3 s, a bounded attempts loop and 2 s, each with its own
attempt counting and stall messages, and RD1's fix round already pauses them with their window. Moving them to the
poller's single 1.5 s cadence would change the old Reader's timings and its tests for no learner-visible gain while
the old Reader is on its way out (RD-retire); it did not fall out naturally.

## 3. The lifecycle and key-scope rules, and their tests

| Rule | Test |
|---|---|
| The companion follows the focused window (its context line; a question is grounded in the focused source unless a selection says otherwise) | `Companion.test.tsx` "the context line follows the focused window…"; `DeskShell.test.tsx` "Enter asks about the selection at once…" (the call's `extractionId`, `spanId`, `selectionQuote`) |
| A paused window asks nothing: its question's poll waits | `asks.test.ts` "a paused window's question is not read until it is back"; `DeskShell.test.tsx` "a question from a window whose desk is left is not read until the learner comes back" |
| Previews ask nothing: in the overview the companion is its pill and has no input; an ask is refused while the overview shows or the asking window is paused | `DeskShell.test.tsx` "the overview shows it as the pill"; the guard in `askCompanion` |
| A docked companion never moves on scroll, pan, reorder, pair, gather or desk switch | `DeskShell.test.tsx` "a docked companion never moves…"; harness "a docked companion never moves…" |
| An anchored companion leaves only by a hand-off (the view moving, its text scrolling away after 250 ms) or a dissolve, never through the dock | `DeskShell.test.tsx` "hands off to its dock when the view moves", "…when its text scrolls away, but not in its first 250 ms", "c again dissolves it where it is"; `model.test.ts` "the state machine"; harness frame samples |
| Keys: in the reading view `c` / `shift+c` / `/`; while typing a bare `c` and `/` stay in the field and `alt+c` reaches the companion; an open search panel (the menu scope) takes every key; in focus mode `c` and `/` pass through; in the overview they do nothing | `router.test.ts` "the companion's and search's keys (RD3)" (five cases); `DeskShell.test.tsx` "typing in the companion's input…", "/ opens it; while it is open its keys are its own…" |
| No collision with the shell's chords (`keymap.ts`) | `router.test.ts`'s existing shell-chord check now covers the built `c`, `shift+c`, `alt+c` and `/`; `keymap.test.ts` (it caught a ctrl+j/k pair in the first search panel, removed) |

**Fail-first evidence.** Each guard was broken by one replacement in the worktree, its test run, and the file restored
(a script under the scratch directory; `git status` clean after each):

| Broken | Test | Result |
|---|---|---|
| the search panel as the menu scope (the router's `menu` flag without it) | "/ opens it; while it is open its keys are its own" | 1 failed |
| a question's poll owned by its window (owner null) | "a question from a window whose desk is left is not read until the learner comes back" | 1 failed |
| the 250 ms guard before a scroll hands off | "an anchored companion hands off when its text scrolls away, but not in its first 250 ms" | 1 failed |
| a dissolve stays where it is (moved to the dock while leaving) | "c again dissolves it where it is" | 1 failed |
| the hand-off's view key (the desk alone, not the camera) | "an anchored companion hands off to its dock when the view moves" | 1 failed |
| the typing scope keeping a bare `c` in the companion's input (`c` bound in the typing scope) | "typing in the companion's input: a bare c stays in the field" | 1 failed |

## 4. The harness and the latency numbers

A fourth harness run, "companion" (71 checks in all), drives the real shell in headless Chromium:

| Check (deep link) | Result |
|---|---|
| `c` with a selection opens it anchored 10 px below the selection, the selection its chip (`#cur=sel`) | pass |
| the summon never passes through the dock (every frame away from it) | pass |
| `c` again dissolves it where it is: no frame moves toward the dock, and it goes | pass |
| `shift+c` opens it at its dock, 400 wide and 52 % high, 14 px in (`#cur=shiftc`) | pass |
| a docked companion never moves on scroll, pan, reorder, gather or a desk switch | pass |
| its text scrolled away, an anchored companion hands off to its dock by a FLIP, with frames between (`#cur=handoff`) | pass |
| dragged near the right edge, it snaps to the right dock (`#dock=right`) | pass |
| while an answer generates the question shows at once; released, the answer arrives through the poller with its claim | pass |
| the history tab lists exchanges by day and desk (`#hist`) | pass |
| `/` opens search: groups in order with open on this desk first; the meaning pass merges in tagged (`#spot=softmax`) | pass |
| ↑ glides the selection block; esc closes search; the shelf's "/ switch" opens it (`#switch`) | pass |
| in the overview the companion is its pill (`#ov`) | pass |
| the RD2 identity checks (entering, leaving, unvisited, focus, navigated) with the companion on the stage | 0.0069 % / 0.0089 % / 0.0078 % / 0.0000 % / 0.0089 % changed (≤ 0.1 %) |

**Latency (information; the fake tutor holding an answer open, so a job is in flight):**

- **an edit in the companion's input**: from setting the value to the frame that shows it, 16.7 ms median, 16.8 ms
  max over 20 edits (one animation frame; asked: under 50 ms);
- **a hover**: no hover card exists on the desks before pads (the pad marks' hover cards are RD4's, §10.6), so the
  hover there is now was timed: a search row under the pointer takes the selection in 4.7 ms (asked: hover cards
  under 250 ms). The pad hover cards are measured when they land.

## 5. The mockup, compared in words (served on 127.0.0.1, headless Chromium; screenshots kept in scratch only)

- **`#cur=sel`.** Mockup: a 400 px panel on `#181818` with a 1 px `#3a3a3a` border, 4 px radius and a deep shadow,
  opened under the selection, tabs `◇ tutor` / `history`, `c hide`, the "following" line with "earlier · dates ›" in
  amber, the thread in mono with the learner's bubbles amber with a 2 px left rule and the tutor's with a dotted purple
  rule, the "§ asking about “…” ✕" chip in italic book type above the "› ask about this…" input. Built: the same
  structure, colours, type and sizes, measured from the mockup's computed styles. Differences: our chip clips the quote
  at 120 characters (the mockup's two lines); our input is a real input with a disabled state that says why when there
  is no passage to ask about.
- **`#cur=handoff`, `#cur=shiftc`, `#dock=right`.** Mockup: the panel at `br` 400 × 52 % (14 px from the stage's
  bottom, 16 from the window's right), and the right dock full height. Built: the same rects (14 px insets on both
  sides of the stage), and the hand-off and snap are FLIP moves rather than the mockup's jumps.
- **`#hist`.** Mockup: the note "every exchange stays here, by day and by desk…", day headers in capitals, the desk's
  title, "› question", "◇ first sentence", where it happened and an anchor. Built: the same, plus a search field over
  the history (`companion.history`'s words query) and "before desks" for backfilled exchanges.
- **`#spot=softmax`, `#switch`.** Mockup: a 640 px panel 32 px below the top bar, an input with "⌕", group headers in
  spaced capitals, rows with the right-hand "where", the blue selection block, and a footer "↑↓ choose · ↵ insert
  beside the focus, or scroll to it if open · esc close · words now, meaning later". Built: the same geometry and
  footer; groups show three rows and "tab · n more"; an off group says why (the fixture's notes are off); the why-not of
  the meaning pass is said once in the footer. The mockup's backdrop shows no visible blur; ours follows §4.3's 2 px.
- **`#ov`.** Mockup: a 300 × 38 pill at the bottom right with the thread's title, "›" and a `c` key. Built: the same,
  faded in with the zoom.
- **`#cov`, `#selctx`.** Mockup: the docked companion over the pads with the chip. Built as `#cur=shiftc` with a
  selection; the pads it covers in the mockup are RD4's.
- **Not copied:** the mockup's static input (ours asks), its jumps between docks (ours are FLIPs), its "mock" tags and
  the action button "View sample implementation", which needs pads (the diff UI is ready).

## 6. Judgment calls (read these first)

1. **The companion is mounted on the desks only.** §8.1 asks for one panel on every screen, but RD3a's `companion.ask`
   is passage-grounded (`reader.ask`'s input) and does not wrap `ask_tutor_question` for Practice and Today (RD3a's
   deviation 5). Mounting it there now would offer a companion that cannot ask. The component takes its context and
   its calls as props, so a Practice or Today mount is a wiring step once the backend wraps those asks. The old Reader
   keeps its own Ask rail.
2. **A question is grounded in a passage:** the selection's first passage (with the whole selection's passages and
   quote), else the focused source's reported reading place, else its saved one, else the passage at the top of its
   window when asked. With no source focused and no selection, the input says how to ask and asks nothing.
3. **The dock is remembered per desk but the companion does not move on a desk switch.** §8.2 says both "remembered per
   desk" and (F17) that a docked companion never moves on a desk switch. The dock and shown state are persisted on the
   desk where they change and read from the desk the desks open on; switching desks keeps the companion where it is.
4. **`partial_md` is not streamed** (RD3a's deviation 1): while a job runs the panel says "asked" or "answering", with
   the count of streamed pieces when the transport reports them, and "stop"; the answer appears whole.
5. **The answer's diff proposals** have no source yet: `Companion` takes a `proposals` callback that RD4 fills; the
   shell passes none, so no diff shows today, and the component is tested with fixtures.
6. **The pill's click** docks the companion and leaves the overview to where it was entered from.
7. **Search rows' snippets are shown as text**, math included as its source; rendering math in search rows is left
   out (the rows stay one or two lines).
8. **Thread windows need the reading in their view.** A `thread` ref names only its root exchange; the window's view
   carries the reading it came from (from the companion or a search's thread row), else it says the thread is in the
   history.

## 7. Tests, commands and results

New tests: `companion/model.test.ts` (11), `companion/asks.test.ts` (7), `companion/Companion.test.tsx` (7: states,
history, diffs, thread exchanges), `search/model.test.ts` (4), `selection.test.ts` (3), `DeskShell.test.tsx` (+14:
summon, dissolve, dock, never-moves, hand-offs, the pill, asking through the poller, paused windows, typing scope,
search's scope, results opened or focused, esc). Edited tests: `keys/router.test.ts` (the RD3 keys are built now, and
five new scope cases), `DeskShell.test.tsx` "a chord whose feature comes later" (now `p`, since `c` is built). No
assertion was loosened.

Commands (each in its own memory-capped scope through the scratch wrapper, one test command at a time):

| Command | Result |
|---|---|
| `npm run typecheck` | exit 0 |
| `npx vitest run --maxWorkers=2` (the whole suite) | 356 files, 3956 tests passed |
| `npm run frontend:build` | built; largest output file 1.86 MB (the main bundle) |
| `cargo check --manifest-path src-tauri/Cargo.toml` | Finished `dev` profile (offline, the shared cargo cache) |
| the harness | 71 passed, 0 failed |
| `tests/test_identity_pins.py`, `test_structure_ratchets.py`, `test_effective_defaults_golden.py`, `test_cli_help_snapshot.py`, `test_kill_switches.py`, `test_sqlite_file_copies.py`, `test_reader_rd1_model_parity.py`, `test_public_tip_guards.py` | 413 passed (no pin moved, no ratchet rose, no golden moved) |
| `scripts/affected_tests.py --files <the changed src files>` | "No test file is affected" (the changed files are TypeScript and the harness script, which no Python test imports) |
| `tests/test_test_layout.py` alone / `tests/test_architecture.py` alone | 3 passed / 18 passed |
| `ruff check` / `lint-imports --no-cache` / `check_gate_partition.py` | All checks passed! / Contracts: 52 kept, 0 broken. / collected 33309: landing 33243 + arc_close 66 |
| `desktop_validate.py` | the counts moved for the nine new source files (368 files, 352 entry-reachable, 12 vitest-support, 374 ACTIVE) and two new areas are described; only the regeneration errors remain (missing notes for the new files, stale notes for the changed ones) |

No ledger row: no defect was found in existing code.

## 8. What I did not verify

- The packaged app on WebKitGTK; a real provider (only the fixture's fake tutor and vitest doubles); a real
  `search.job` meaning pass (the fixture's stands in).
- Practice and Today mounts (judgment call 1); pad hover cards and diff writes (RD4).
- Pointer gestures on a real touchpad; the companion's drag was driven by Playwright's mouse.
- The landing gate.
