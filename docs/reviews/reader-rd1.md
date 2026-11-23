# Reader workbench v2, RD1: the desk shell with adapters

Stage RD1 of `docs/specs/spec_reader_workbench_v2.md` (§16). Branch `reader/rd1-desk-shell`, from main `54be27df69`
(migration head 264, latest algorithm tag mvp-0.66). Frontend only, apart from one parity test and the vault
generator's area descriptions: no migration, no algorithm tag, no config field, no RPC, no Rust, no model call, nothing
on the phone. The owner deferred performance on 2026-11-23, so the lifecycle contract is built as correctness and no
frame budget is gated (§3.6's budgets wait for the performance revisit).

## 1. What landed, per item

| Brief item | Where |
|---|---|
| `DeskShell`, the window lifecycle contract (§3.6) | `F:screens/desks/DeskShell.tsx`, `lifecycle.tsx`, `keys/listeners.ts` |
| The key router, the resolved key matrix (§5.4), the bare-Alt tap/hold rule, modifiers from key events (§5.5) | `F:screens/desks/keys/router.ts`; `F:screens/reader/bareAlt.ts` gains the 400 ms threshold |
| The one central poller | `F:api/poller.ts` (see deviation 4) |
| Source and video windows as scoped instances of the Reader's source pane | `F:screens/desks/windows/SourceWindow.tsx` over `ReaderScreen`'s new windowed mode (see deviation 1) |
| Per-instance media identity (`event.source`), the existing bug fixed | `F:screens/reader/YouTubeWatchPanel.tsx`; ledger RD1-1 |
| Panel windows: Guide rail, reading-path card, library pane, notes rail, compare view (§21.1) | `F:screens/desks/windows/PanelWindow.tsx` |
| Slots and pairs, slivers, soft crop, open beside without duplicates, close and undo, move, desks, focus mode, footer dots and hints, which-key, the shelf | `DeskShell.tsx`, `Shelf.tsx`, `geometry.ts`, `model/workspace.ts` |
| Persistence through `desk.state`/`desk.apply` with `client_id` + `seq` and conflict handling | `F:screens/desks/outbox.ts` (in memory, behind `OutboxStore`) |
| First-run desks | `DeskShell.tsx` `firstRun` (see deviation 6) |
| Design tokens as CSS variables, fonts local | `F:styles/desk.css` (see deviation 7) |
| The synthetic workspace fixture (§18.3) | `F:fixtures/desks/` (`sources.ts`, `workspace.ts`, `fakeCore.ts`, `harness.tsx`, `opParity.json`) |
| The real-webview harness | `apps/learnloop-tauri/vite.desks.config.mjs`, `desk-harness.html`, `scripts/desk_harness/run.py` |
| The old Reader stays reachable | The Reader place keeps the old Reader by default; its header has "desks ▸", the desks' top bar has "old Reader", and the choice is remembered on this machine (`app/shell.ts` `rememberedReaderSurface`) |

### How the pieces fit

- **The workspace model** (`model/workspace.ts`) is pure and mirrors the server's `desk.apply` op for op
  (`src/learnloop/desks/workspace.py`), including the active-pane rule of the server's layout write. Each intent
  (`openBeside`, `closeWindow`, `undoClose`, `moveFocused`, `moveWindowTo`, `pairFocused`, `unpairFocused`,
  `focusAlong`, `focusPane`, `createDesk`, `renameDesk`, `setView`, `swapInView`) returns the next workspace and the
  ops that persist it, each op stamped with the version its desk will have when it lands (every applied op adds one,
  as on the server; a transfer names both versions). One script, `fixtures/desks/opParity.json` (eighteen ops over two
  desks, with a refusal and a stale head), runs through the sidecar (`tests/test_reader_rd1_model_parity.py`) and
  through the client model behind the harness's version-checking server (`fixtures/desks/opParity.test.ts`): both
  give its results and final state.
- **The outbox** (`outbox.ts`) numbers batches per client from the server's head (`desk.state`'s `serverSeq`; the
  client id is kept per vault on the machine), sends them oldest first one flush at a time, drops a batch on its
  receipt, keeps it when the sidecar is unreachable, and on a conflict or a refused number drops what was queued
  after it and lets the shell read `desk.state` again (§3.5: moves and pairs take the server's state).
- **The listener router** (`keys/listeners.ts`) installs one real listener per event type and phase, however many
  windows there are. Each window registers through its hub (`lifecycle.tsx` `ListenerHub`); input events (keys,
  pointer, mouse, clipboard, selection, wheel) go to the active window only, a pointer press makes the window under it
  active before it is handed on, other events go to every window that is not paused, and the shell's own handling
  (the key router, the bare-Alt tracker) runs first and can take an event from every window. Outside the desks the
  hub is the real window (`DIRECT_HUB`), so the old Reader and every other screen behave as before.
- **The Reader's listeners** in the hooks a source window mounts (`useBareAltClear`, `useReaderCues`, `useIntentBox`,
  `useReaderInquiry`, `useReaderRecap`, `useReaderWorkbench`, `useReadingProgress`, `useCueImpressions`,
  `useSideBySide`, `PdfReaderPane`, `WrapUpPanel`, `YouTubeWatchPanel`, `LibraryPane`, `ReaderWorkingPosture`,
  `ComparePointTable`, and `ReaderScreen`'s own) now register through the hub. The two key-listener scans
  (`app/keymap.test.ts`, `app/shellChrome.test.ts`) read the hub's registrations as well as direct ones, so their
  guards still cover these listeners.

## 2. The key matrix as built

The router resolves one key event against the open scopes, highest first (§5.4): notebook, check, menu, typing,
arrange, pen, overview, focus, reading. RD1 opens only typing (an input, textarea, contenteditable, select, or a part
marked `data-desk-typing`), focus mode and the reading view; the other scopes' rules are in the matrix and tested,
for the stages that open them. A chord whose feature is not built is not taken: the key goes on to the window and the
shell as before, and which-key does not list it.

| Chord | Action | Scopes | Built |
|---|---|---|---|
| `alt+h` / `alt+l` | focus the window left / right | typing, focus, reading | yes |
| `alt+j` / `alt+k` | the pane below / above in a pair, then the desk below / above | typing, reading | yes |
| `alt+[` / `alt+]` | move the focused window one slot | typing, overview, reading | yes |
| `alt+shift+j/k` | window to another desk | overview | RD2 |
| `alt+↵` | focus mode (true full screen) on / off | typing, focus, reading | yes |
| `alt+w` | close (undo on the shelf for 9 s) | focus, reading | yes |
| `alt+g` / `alt+shift+g` | gather / to a new desk | reading | RD2 |
| `alt+o`, `o` | overview | overview, focus, reading | RD2 |
| `alt+,` / `alt+.` | share a slot / own slot | typing, reading | yes |
| `alt+n`, `alt+a`, `alt+d` | new pad, arrange pads, sketch block | reading | RD4 |
| `alt+;` | insert ▶ timestamp | reading | RD10 |
| `alt+p` | pen mode | pen, reading | RD8a |
| `alt+c` | the companion while typing | typing | RD3 |
| `space` | play or pause the focused video (anything else: the key scrolls as before) | reading | yes |
| `c`, `shift+c`, `/` | companion here, at its dock; search | reading | RD3 |
| `.`, the menu key, `n`, `b` | the menu, a margin note, the first promoted action | reading (`b` also overview) | RD5 |
| `ctrl+tab` / `ctrl+shift+tab` | next / previous pad | reading | RD4 |
| `p` | your path | reading | RD6 |
| `u` | follow along | reading | RD10 |
| `x` | swap the two windows in view | reading | yes |
| `=` (`+`), `-`, `0` | document zoom in, out, 100 % (0.6–2.2 in steps of 0.1; a per-window `set_view`, CSS zoom) | focus | yes |
| `esc` | leave focus mode | focus | yes |

The bare-Alt rule: a tap under 400 ms with nothing else pressed is the old capture-clearing tap (the active window's
`useBareAltClear` hears its release); a hold of 400 ms shows which-key, and its release reaches no window and never
clears. A key, a pointer press or the window losing focus while Alt is down spoils the press. Alt and Ctrl are
tracked from key events, cleared on blur and ORed with the event's flags. No desk chord collides with a shell chord
(`Alt+S` stays Settings; arranging pads is `alt+a`), checked against `shellBindings` of both shells.

## 3. The lifecycle contract and its tests

| Rule (§3.6) | Built as | Tests |
|---|---|---|
| States active, visible, offscreen, hidden, preview | `lifecycle.tsx` `windowState`: the desk's focus is active; other panes of slots in view are visible; the rest of the desk is offscreen (all but the focus, in focus mode); other desks are hidden; a card is preview | `DeskShell.test.tsx` (each state on screen, desk switch, focus mode); harness |
| Only the active window owns input, the selection and the capture target; listeners through the router | `keys/listeners.ts`; the Reader's listeners through the hub | `listeners.test.ts` (one real listener for four windows; keys to the active window only; a press activates first; paused windows hear nothing else; phases; interception; stopImmediatePropagation); `DeskShell.test.tsx` "only the active window hears keys; a hidden desk's window hears none" |
| Offscreen and hidden windows pause effects, timers, polling and media | the Reader's three job polls skip while paused (`useReaderInquiry`, `useReadingProgress`'s authoring poll, `ReaderScreen`'s import poll); the player is sent `pauseVideo`; `.paused` windows get `content-visibility: auto` with an intrinsic size and paused animations; hidden desks stay mounted (inert) once visited, never mounted before | `YouTubeWatchPanel.instance.test.tsx` "is paused when its window goes offscreen, and not before"; harness "a hidden desk's player is paused" |
| Previews and programmatic moves generate no reading activity | a reading visit opens only while active or visible (`useReaderVisit`); scrolling or playback counts as reading only then (`useReadingProgress`); margin-mark impressions only then (`useCueImpressions`); moves and pairs never scroll content, and a restore or jump never counted as reading before either | `SourceWindow.lifecycle.test.tsx` (a preview logs nothing; active opens a visit, hidden closes it, offscreen opens none); harness preview check with an active control |
| Media identity per instance | `event.source === iframe.contentWindow` | `YouTubeWatchPanel.instance.test.tsx` (two players; a message no player's frame sent); harness "two players each keep their own clock" through real iframes |
| One central poller | `api/poller.ts`: one cadence, coalesced by job key, backoff 1/2/4… ticks on failure, owners paused with their windows (the shell keeps each window's pause in step) | `poller.test.ts` |

**Fail-first evidence** (each guard broken by one line in the worktree, the test run, the file restored; `git status`
clean after each):

| Broken | Test | Result |
|---|---|---|
| the `event.source` check absent (the landed code) | `YouTubeWatchPanel.instance.test.tsx` | 2 failed: "expected 'watch modebbbb1:15…' to contain '0:00'", "expected 'watch modecccc1:31…' to contain '0:00'" |
| the router handing input to every window | `listeners.test.ts`, `DeskShell.test.tsx` | 3 failed |
| the visit's activity gate | `SourceWindow.lifecycle.test.tsx` | 2 failed |
| the bare-Alt hold threshold | `bareAlt.test.ts` | 1 failed |
| the player's pause on leaving the view | `YouTubeWatchPanel.instance.test.tsx` | 1 failed |
| a which-key release handed to the window | `DeskShell.test.tsx` | 1 failed (after the test was made to record key-ups; the first version passed with the break, so it was strengthened) |
| the typing scope ignored | `DeskShell.test.tsx` | 1 failed |
| the margin-mark impression gate in `useCueImpressions` | `ReaderScreen.discoveredCues.test.tsx` "impressions: a source window offscreen on a desk sends none" | 1 failed ("expected "spy" to not be called at all, but actually been called 1 times") |

## 4. The harness and its blind spots

`scripts/desk_harness/run.py` serves the page built by `vite.desks.config.mjs` on 127.0.0.1 and drives it in
headless Playwright Chromium (Playwright fetched by `uv run --with playwright==1.65.2`; not a project dependency). The
page is the real `DeskShell` and real windows (the real `ReaderScreen` in each source window) over the browser mode's
shims, with `@tauri-apps/api/core` answered from the synthetic workspace (`fixtures/desks/fakeCore.ts`, every call
recorded). YouTube is never contacted: its embed URL is answered by a local stub player that reports a time of its own
and records the commands it gets; every other outside request is refused. Its 28 checks:

- windows render; every window fills its slot's height (the slot is the stage height less 16 px and the pane body
  reaches the slot's bottom); two windows in view with the book active; one sliver for the off-screen neighbour;
- which-key on an Alt hold, hidden on release;
- `alt+l` ×3 moves the focus to the guide panel (#focus=3), whose body hosts the book's rail; slivers both sides;
- `alt+]` moves the focused window one slot (#move);
- opening the book again opens no second window and focuses the existing one;
- the first player shows its own time; `space` plays the focused video;
- switching to the attention desk hides the first desk's windows (#desk=1) and pauses its player; two players keep
  their own clocks;
- focus mode is the whole viewport (#zoom=after); `=` zooms to 110 %; leaving restores every window's rect within 1 px;
- `alt+,` stacks two windows top and bottom with equal heights; a third is refused with the toast; `alt+.` undoes it;
- `alt+w` closes and the shelf's undo reopens;
- the outbox's batches are numbered 1..n from one client, and the server's slots equal the screen's;
- no error reached the shell's error line;
- a preview logs no reading activity and no progress, while the same window active opens a visit.

**Blind spots.** It runs Chromium, not WebKit: the Playwright WebKit build is not installed here, and the packaged
WebKitGTK app was not run (the RD-spike's ground). The fonts are the app's own (bundled), so the harness renders the
designed faces. No screenshot comparison with a tolerance: the checks are geometry
and state (the zoom engine's screenshot invariant is RD2's). The stub player is not YouTube: real embedding, error 153
and playback in the packaged origin are unverified. The fake sidecar answers the Reader's reads from fixtures, so the
windows' Reader features that need other RPCs (Ask, figures, notes, quick checks) show their refused or empty states
in the harness.

## 5. The mockup, compared in words

The mockup (served on 127.0.0.1, headless Chromium, 1600×960) was opened at the four deep links. In headless
Chromium `#focus=3` and `#move` rendered the plain first view (the focus and order unchanged), so their comparison is
against the mockup driven by its own keys (`alt+l` ×3, `alt+]`), which run the code those links call.

**`#desk=1` (the second desk).** Mockup: the attention desk's video window focused (a poster with ▶, a scrub track and
"▶ m:ss / duration", the transcript on paper with a timestamp gutter, the current cue amber), the paper beside it on
paper with Source Serif text, the companion floating at bottom right; the shelf lists the desk's windows ("§ PAPER ·
IN VIEW", "› NOTES · IN VIEW", "▶ VIDEO · same idea"…) with minimap bars and "where" lines, and below them TODAY ·
RUNNING PAD and CARRIED; the footer has hints left, dots right and "hold alt for navi hints". The build: the attention
tab active, its video window active and the paper visible beside it, both on paper; shelf rows with glyph, kind, state
word, title, a reading-progress bar and the section as the "where" line; the same footer. **Differences, and why:** no
companion (RD3); no "· same idea" state, minimap ticks or question dots (they need the union read and LO coverage; the
shelf shows reading progress only); no running pad or carried questions (RD4); the video window is the Reader's watch
panel as it is (a "watch mode" header, the player above the transcript at this width, no poster-first frame or scrub
track: §7.4's player is not part of RD1's extraction); the paper renders in Literata, not Source Serif 4 (§7.3's paper
typography needs the source kind the window does not yet distinguish); the top bar has no goal, overview, path, tour or
pen chips (RD6, RD2, RD8a; `mock` chips are never built).

**`#focus=3` (focus the fourth window).** Mockup: the camera slides so the fourth column and the third are in view,
the focused column ringed amber, slivers at both stage edges with a vertical short name, the shelf's row marked
"· FOCUS". Columns are 638 px at this stage width. The build: the same camera rule (the least movement that brings
the focus in view, the strip's ends clamped), the focus ringed, two slivers with glyph and vertical title, the shelf
row marked focus, the partly visible neighbour softly cropped. **Differences:** slots are 643 px, not 638: the build
makes the right margin equal the left (34 px each); the mockup's formula left 44 px on the right. The fourth window in
the fixture is the Guide panel hosting the book's v1 rail, where the mockup has a paper (the fixture's arrangement
differs; the rail is §21.1's adapter).

**`#move` (`alt+]`).** Mockup: the focused column swaps with its right neighbour, which slides over in .45 s, and the
viewport follows; the shelf order changes. The build: the same, persisted as one `move_window` op. **Difference:** the
build moves windows by animating each window's `left`, not by translating the world: a transformed ancestor would
become the containing block of the Reader's `position: fixed` menus and cards inside a window (deviation 3).

**`#zoom=after` (focus mode).** Mockup: the focused column stays half width (756 px at x 34; the known defect, §4.4),
the top bar fades to 45 %, the badge "alt+↵ or esc to leave · = − to zoom". The build: true full screen (the window
fills the whole 1600×960 viewport; the top bar, shelf and footer collapse to nothing), the content at its reading
measure centred (900 px for a video, 980 for a book), and the badge with the zoom percentage. **Differences:** full
screen per owner decision 11 instead of the mockup's half width; the window's own header stays visible in focus mode
(the mockup's does too).

**Which-key** (not a deep link, compared too): the mockup's panel has four groups (move, windows, pads, media) with
every key; the build's panel has the same frame and groups but lists only what works in RD1 (move, windows, media),
since a listed key that does nothing would mislead.

## 6. Deviations from the spec, with reasons

1. **Source windows host `ReaderScreen` in a windowed mode instead of a moved-out `SourceWindow` body.** The spec has
   `SourceWindow.tsx` "extracted from ReaderScreen's source pane together with its hooks… it does not fork them". The
   source pane's state is shared with the rail, side by side, the intent box, inquiry and capture across 4,700 lines;
   moving it out in one stage would rewrite most of the 60-odd ReaderScreen test files' subject. The windowed mode keeps
   one implementation (no fork) and every existing Reader test runs against it unchanged: `ReaderScreen` gains a
   `windowed` prop that hides its header, key bar and library list, renders its rail into the desk's panel window bound
   to the book (or nowhere), and portals its fixed-position menus out of the window. The move of the code itself
   belongs with RD-retire, when the old Reader place goes. `VideoWindow.tsx` is the same host for a video source (the
   Reader's watch surface), so there is one window module, not two.
2. **The Guide and Notes panels show the rail of the book's own window.** The rail's state (the guide plan, quick
   checks, captures, notes) lives in that `ReaderScreen` instance, so the panel window is the place it renders, not a
   second instance. The panel's kind picks the tab it opens on; the rail keeps its Ask tab (the v1 tutor) until the
   companion lands. With no window of that book on the desk the panel says so; two panels for one book show one rail,
   and the other offers "show it here".
3. **Windows move by `left`/`top`, not a world transform; `content-visibility` only while paused.** A transform on the
   world or a window, or `content-visibility: auto` on a visible window, makes that element the containing block of
   every `position: fixed` descendant, which would misplace the Reader's tag menu, note picker, intent box and figure
   cards. The camera's .55 s and the window move's .45 s are kept as the transitions on `left` and `top`. RD2's zoom
   engine freezes content during its transforms, which is where transforms belong.
4. **The central poller is built, and the Reader's existing three job polls keep their own timers, paused with their
   window.** Their tests drive those intervals directly (`ReaderScreen.review.test.tsx` captures the `setInterval`
   callbacks); moving them onto one cadence is a behaviour change to those waits, best ported with RD3's
   `companion.ask_job`, the poller's first new user. Until then the contract's "pauses polling" holds through the
   pause gate on each.
5. **The outbox is in memory** (the brief's instruction): `OutboxStore` is the interface the RD-spike's durable store
   implements; until then an op queued but not acknowledged is lost if the app closes, and a sidecar that cannot be
   reached shows "couldn't save the desk just now · it is kept here until it can be".
6. **First run is one desk.** §5.1 asks an existing user's first open to build one desk per recently read source set,
   grouped by reading sessions; no read lists recent reading sessions to the client, so RD1 builds one desk named "new
   desk · <short name>" holding the book the learner read last (the shell's remembered book), or an empty desk with
   "open a source beside". No running pad is created (pads have no UI until RD4). The grouping needs a sidecar read of
   recent reading sessions, which no RPC offers; proposed as a follow-up with RD4, where the running pads arrive.
7. **Fonts ship as npm dependencies** (the orchestrator's decision after the first report): the Fontsource variable
   packages `@fontsource-variable/inter` 5.3.0, `literata` 5.3.0 (with italics), `source-serif-4` 5.3.1 (with
   italics), `jetbrains-mono` 5.3.0 and `caveat` 5.3.0, pinned exactly, all **SIL Open Font License 1.1**. DeskShell
   imports them, so Vite copies their WOFF2 files into the built app (about 1.5 MB of WOFF2 in all, the largest built
   file still the 1.86 MB main bundle, under the public-tip guard's 5 MB; no font file is committed); the tokens name
   the variable families first; nothing is fetched from a font service, and the CSP's `font-src 'self'` covers them.
   `LICENSES.txt` names each font, its licence and its copyright line. The harness checks the five families load and
   that no request leaves the page but the stubbed player's. Source and video windows read on paper by remapping the
   Reader's palette variables inside the window and setting the book's prose in the book font.
8. **The old Reader stays the default of the Reader place**, with links both ways remembered on this machine. The
   desks have no companion (Ask lives in the panel's rail) or pads yet, so making them the default now would take the
   daily Reader's Ask one click further away; the parity matrix (§21.1) is what lets the default flip. The plan-reading
   entry (the Reader opened from Today's plan with its banner) always opens the old Reader.
9. **Batches are one per change**, not coalesced: each committed change is enqueued as its own batch with the next
   `seq`; a burst is sent after 250 ms idle, still in order.
10. **Overview and miniatures are RD2**: the "overview-preview" test is a card in the `preview` state (the harness's
    `?preview=` page and `SourceWindow.lifecycle.test.tsx`).
11. **A window that fails to render fails alone** (an error boundary per pane). Found by the harness: the reading-path
    card threw on a malformed fixture reply and took the whole desk down before the boundary.

## 7. Tests, commands and results

New test files: `screens/desks/model/workspace.test.ts`, `geometry.test.ts`, `outbox.test.ts`, `keys/router.test.ts`,
`keys/listeners.test.ts`, `DeskShell.test.tsx`, `windows/SourceWindow.lifecycle.test.tsx`, `api/poller.test.ts`,
`screens/reader/YouTubeWatchPanel.instance.test.tsx`, `fixtures/desks/fakeCore.test.ts`, `harness.test.tsx`,
`opParity.test.ts`, `tests/test_reader_rd1_model_parity.py`. Edited: `screens/reader/bareAlt.test.ts` (the hold rule),
`app/shell.test.ts` (the remembered Reader), `app/keymap.test.ts` and `app/shellChrome.test.ts` (their scans also read
the hub's `listen("window", "keydown", …)` registrations; nothing they assert was loosened, they see more listeners),
`ReaderScreen.followsLearner.test.tsx` and `ReaderScreen.checkOffer.test.tsx` (their fake widget messages now come from
the player's frame, as the real widget's do; the behaviour they test is unchanged).

Every pytest run went through the scratch wrapper in a `systemd-run --user --scope -p MemoryMax=3G -p MemorySwapMax=1G`
scope as `uv run --no-sync pytest -q -n 1 -p no:cacheprovider -m "not arc_close" <files>`; every npm and cargo run
through the wrapper (the shared npm and cargo caches) in a 5G scope.

| Command | Result |
|---|---|
| `npm ci` | done (no dependency added) |
| `npm run typecheck` (`tsc --noEmit`) | exit 0, no errors |
| `npx vitest run --maxWorkers=2 src/app src/screens/desks src/fixtures src/api src/screens/ReaderScreen src/screens/reader src/components/PdfReaderPane` (every touched area) | 192 files, 2095 tests passed (one earlier run of the same set: 1 failed, `SketchFigure.test.tsx`'s timing flake under load, ledger RD1-2; it passes alone, 19 of 19) |
| `cargo check --offline --manifest-path src-tauri/Cargo.toml` (no Rust changed) | Finished `dev` profile |
| `npx vite build --config vite.desks.config.mjs`, then `uv run --no-project --with playwright==1.65.2 python scripts/desk_harness/run.py` | 28 passed, 0 failed |
| `scripts/affected_tests.py --files <the 62 changed files>` | 11 test files; run: 352 passed |
| `tests/test_reader_rd1_model_parity.py` | 1 passed |
| `tests/test_identity_pins.py`, `test_structure_ratchets.py`, `test_effective_defaults_golden.py`, `test_cli_help_snapshot.py`, `test_kill_switches.py`, `test_sqlite_file_copies.py`, `test_public_tip_guards.py` | 412 passed |
| `tests/test_test_layout.py` alone / `tests/test_architecture.py` alone | 3 passed / 18 passed |
| `uv run ruff check` | All checks passed! |
| `uv run lint-imports --no-cache` | Contracts: 52 kept, 0 broken. |
| `uv run python scripts/check_gate_partition.py` | collected 33170: landing 33104 + arc_close 66 |
| `docs/learnloop-architecture-vault/_scripts/desktop_validate.py` | only the regeneration errors remain (missing notes for the fifteen new files, stale notes of the changed ones, the reproducibility diff); the three counts now read 352 files, 337 entry-reachable + 11 vitest-support, 358 ACTIVE |

Pins and goldens: no identity pin, effective default, CLI snapshot or structure ratchet moved. `desktop_validate.py`'s
three counts moved (above) and `desktop_generate.py` describes the five new areas. Ledger: RD1-1 (fixed), RD1-2
(open, with RD0-11).

## 8. What I did not verify

- The packaged app on WebKitGTK (the RD-spike's), Playwright WebKit (not installed), and the laptop.
- Real YouTube embedding and playback (the harness's player is a local stub).
- The desks against a real sidecar and vault (the harness answers from fixtures; the parity test checks the model
  against the sidecar's ops directly).
- Any performance budget (deferred by the owner).
- The landing gate, the whole Python suite and `npm run frontend:build` (not run here, per the brief); the vault's
  generated references (the landing regenerates them; `desktop_validate.py` reports only the missing and stale notes
  of the new and changed files).

## 9. After the orchestrator's first read: fonts, the impression gate, and main merged

The orchestrator accepted judgment calls 1–6 and asked for three changes. **Fonts** now ship (deviation 7, rewritten:
Fontsource variable packages, SIL OFL 1.1, named in `LICENSES.txt`). **The margin-mark impression gate** now has a
fail-first test (§3's table). **Main** (`f7becdf2ea`: mvp-0.67, migration 265) merged without conflict. Nothing on main
touched the frontend, the desks or their dependencies.

| Command (after the merge) | Result |
|---|---|
| `npm run typecheck` | exit 0 |
| `npm run frontend:build` | built; largest output file 1.86 MB (the main bundle), fonts about 1.5 MB of WOFF2 in all |
| vitest over app, desks, fixtures, api, ReaderScreen, reader, PdfReaderPane | 192 files, 2096 tests passed |
| the harness (before the merge, with the fonts; nothing it builds changed in the merge) | 30 passed, 0 failed |
| `tests/test_reader_rd1_model_parity.py`, `test_identity_pins.py`, `test_structure_ratchets.py`, `test_public_tip_guards.py` | 375 passed |
| `tests/test_architecture.py` alone / `tests/test_test_layout.py` alone | 18 passed / 3 passed |
| `ruff check` / `lint-imports --no-cache` / `check_gate_partition.py` | All checks passed! / Contracts: 52 kept, 0 broken. / collected 33251: landing 33185 + arc_close 66 |
| `desktop_validate.py` | no count drift; only the regeneration errors (missing notes for the new files, stale notes for the changed ones, the reproducibility diff) |

## 10. Fix round: the adversarial review's twelve findings

The review found one blocker and eleven majors. All twelve were defects; each is fixed with a fail-first test, and
each has a ledger row (RD1-3 to RD1-14, finding 1 to finding 12 in order). The fix round builds on RD2 (the overview),
so the windows' markup, the zoom plan and the controller changed with finding 2.

| # | Finding | Fail-first test (failed before, passes after) | Fix |
|---|---|---|---|
| 1 (RD1-3) | Empty compare poisons the save queue | `DeskShell.test.tsx` "compare with nothing typed opens the library pane…" (got `{ kind: 'compare', query: undefined }`); `outbox.test.ts` "a request refused for good is rejected, never retried…" | Empty compare opens the library pane. The outbox classes `validation_error` and `stale_sidecar_schema` as permanent: the batch is dropped once and the later batches move up one number (the server consumed none for a refused request); the store says "that change couldn't be saved, and was undone" and reconciles. Any other error is a transport failure and is retried |
| 2 (RD1-4) | Pairing and focus mode remount the Reader | `DeskShell.test.tsx` "a draft survives pairing, unpairing and focus mode, and its window mounts once" (a different input element after pairing); the harness's "pairing and unpairing remount neither window" (no marks left against the old shell) | One element per window, keyed by the window id and rendered in id order (reordering slots moves no element, so no iframe reloads); a pair is two windows placed at their panes (square where they meet, the divider between). The focus-mode measure wrapper is always there and only restyled; a focused pane's partner stays mounted, hidden. The zoom plan moves one item per window (a pair's card split top and bottom) and the rings per slot |
| 3 (RD1-5) | A conflict deletes unrelated intent | `outbox.test.ts` "a conflict keeps the batches queued after it, for the store to rebase" | The new desk store (`store.ts`) keeps the queued batches as intent. On a conflict or a rejection it waits for any batch on its way, reads `desk.state`, re-applies every queued op on it through the model (`restampOp` stamps the versions it now expects), requeues what applies from the server's head and counts what does not; the shell says "the desk changed elsewhere · N changes couldn't be kept". New commits made while the state is on its way are rebased too, and no flush runs while reconciling. `store.test.ts` covers the rebase, the report and the commit during the read |
| 4 (RD1-6) | Hidden windows keep real DOM input | `DeskShell.test.tsx` "switching desks moves the focus out of the old desk's input…", "moving the activation… takes the focus with it"; the harness's "a field on a desk left behind takes no typing" (`zz` arrived in the hidden field against the old shell) | A paused window's content carries `inert` (no focus, typing, tab stop, clicks or iframe focus); a visible inactive window stays clickable. When the active window changes, focus held in a window that is no longer active (an iframe included) moves to the new active window (`tabIndex=-1`); focus in the shell's own chrome stays where it is |
| 5 (RD1-7) | Unmount leaves an old writer alive | `DeskShell.test.tsx` "leaving the desks before a change is sent and coming back keeps one numbering" (seqs 1, 2 from one client), "a reading place still waiting to be saved survives leaving the desks"; `store.test.ts` "a second load reads the server's state again…" | One store per vault and transport (`deskStoreFor`), outside the shell, owning the outbox and the flush timer. The shell's own timers (the entering fade) end with it; a pending view save is handed to the store at unmount; a load after coming back rereads the server and rebases what is queued; a load that lands after unmount changes nothing |
| 6 (RD1-8) | Hidden and preview windows start work and poll | `pausedProducers.test.tsx` "an offscreen source starts no cue discovery until it is on screen" (called once while offscreen), "a library job is not read while its window is hidden…" (43 reads while hidden, against at most 4); `ReadingPathCard.test.tsx` "a hidden panel does not read the path while it is judged…" | `useWhenLive()` (in `lifecycle.tsx`): a wait that resolves at once while the window is live, else when it next is. Every job reader and timed re-read awaits it before each request, so a job in flight keeps its id and is read on after; interval loops stop while paused. Inventory below |
| 7 (RD1-9) | A hidden Reader's menu stays over the new desk | `SourceWindow.lifecycle.test.tsx` "a tag menu portaled over the desks closes when its window stops being the active one" | The tag menu and the note picker close when the window's state is not active, and render only while it is; back on its desk the menu does not reappear |
| 8 (RD1-10) | The Reader's scopes are bypassed | `DeskShell.test.tsx` "an intent box open over a selection takes the typed key: x reaches it and swaps nothing", "an open menu in focus mode takes esc…"; `scopeClaims.test.tsx` (the intent box claims typing while armed; an open Wrap up claims the menu scope) | `useScopeClaim(scope, open)` through the window scope; the shell keeps each window's claims, and the router resolves the active window's typing, menu and check claims before the desk's reading and focus bindings. Claimed: the intent box (typing, while armed over a selection or open), the tag menu and note picker, the ask find box and Wrap up (menu). No hosted Reader surface owns non-text keys as a check card today (the quick checks answer in text fields, already the typing scope); the check claim is there for RD4's check card |
| 9 (RD1-11) | An Alt chord can clear the capture | `DeskShell.test.tsx` "an Alt chord the shell takes never reaches the Reader as a bare-Alt tap; a real tap still clears" | The shell's Alt tracker sees every key while Alt is down, so it is the authority: an Alt release goes on to a window only for a confirmed tap; a hold (which-key) or a chord keeps it |
| 10 (RD1-12) | The rail inherits the source's input ownership | `SourceWindow.lifecycle.test.tsx` "the rail in a panel window lives in that panel's window scope…" (read `w1`, the source) | The rail host carries the panel window's lifecycle, hub and claims; the portaled rail is wrapped in that window scope, so Wrap up's esc, the rail's listeners and its pausing go by the panel |
| 11 (RD1-13) | Undo after a rejected close duplicates a window | `workspace.test.ts` "refuses to reopen a window that is open, even with a stale closed entry for it"; `DeskShell.test.tsx` "an undo offer for a close the server refused goes away"; `store.test.ts` "undo after a rejected close" | The model refuses `reopen_window` for an open window (`window_open`, as RD0) and `undoClose` offers nothing then; reconciling keeps a closed entry only for a window not open on the server; the shelf's undo offer names its window and holds only while that window is closed. `opParity.json` gains a batch: reopening an open window, then closing and reopening one, then reopening it twice (TS and Python agree) |
| 12 (RD1-14) | Unshown recaps recorded as shown | `SourceWindow.recap.test.tsx`: a preview, an active window with no rail panel, a hidden rail panel (each recorded `recap_shown` once) | The card counts as shown only where the rail is rendered and its window is not paused: on a desk, a rail host whose panel is active or visible; outside the desks, the Reader itself |

### The producer and timer inventory (finding 6)

Every `setTimeout`, `setInterval` and sleep loop in the hosted Reader (the Reader's screens, its hooks, the PDF pane,
figures, and the workbench hosted in its working posture), with what each does while its window is paused.

| Where | What | Paused |
|---|---|---|
| `useCueDiscovery` | discovery started per open; its job reads; the plan re-read while targets are pending | waits (`useWhenLive`): no start, no read; the same job read on |
| `useLibraryAsk` | each stage's job loop (ask, notes, compare, tutor, scope) | waits before each read; the same job |
| `useLibraryExercises` | candidate and fallback job loops | waits before each read; the same job |
| `figures/useFigures` | figure job loop, recheck job loop, the rich-figure re-read | waits before each read; the same job |
| `guidePlan` `useGuideDiagnosisRefresh` | plan re-read while diagnoses are pending | waits |
| `useReaderRecap` | recap and Wrap up narrative re-reads | waits |
| `ReadingPathCard` | re-read while judging; refresh after progress | waits (a refresh asked while paused runs once back) |
| `DeliverableSliceCard` | re-read while pending; refresh | waits |
| `useReaderRequests` | request status poll | waits |
| `useActiveReading` | active question status read | waits |
| `ReaderNotes` `usePathNotes` | path-notes linking re-read | waits |
| `workbench/useWorkbenchHelp`, `workbench/RouteExample` | help and example job loops | waits before each read; the same job |
| `PreparingView` | library readiness check (interval) | stops; restarts on return |
| `workbench/useWorkbenchSession` | import-binding refresh (interval) | stops; restarts on return |
| `workbench/Workbench` | "saved · n min ago" clock (interval) | stops; catches up at once on return |
| `figures/FigureInline` | a parameter's play animation (interval) | stops where it is |
| `useReaderInquiry` check poll, `useReadingProgress` authoring poll, `ReaderScreen` exercise import poll | job polls | already skipped while paused (RD1) |
| `useReaderVisit`, `useReadingProgress` scroll and playback, `useCueImpressions` | reading activity and impressions | already gated to active or visible (RD1) |
| `useIntentBox` show timer, speculation timer, routing settle | after a selection or typing in the box | not gated: only the active window has a selection or the box's focus, and the settle is bounded by the contract's few seconds |
| `useReadingProgress` progress save debounce and seen-count report | writes what the learner read | not gated: they carry what an active or visible window already recorded; pausing them could lose it |
| `workbench/useWorkbenchSession` edit debounce and save retry | saves the learner's steps | not gated, for the same reason |
| `useReaderCues` focus retry, `useReaderInquiry` and `AskRail` find-box focus, `ReaderScreen` undo-removed, focus and jump timers, `PdfReaderPane` find debounce, pending-target settle and font wait | one-shot UI timers after a learner action | not gated: each fires once, within a second, after something done in the active window |

### Other changes and judgment calls

- **Outside the desks nothing changes.** `useWhenLive` never waits, `useScopeClaim` claims nothing, and the rail and
  overlays behave as before when the Reader is not windowed (the Reader's own suites pass unchanged).
- **The store is in memory**, as the outbox was (the accepted memory-only limitation). It lives as long as the page,
  one per vault and transport; the app's transport is a module constant, so leaving and re-entering the desks finds it.
- **A refused request consumes no number.** The server checks params before it takes a sequence, so the batches after
  a rejected one are renumbered from its number; a conflict's reply does consume its number, and the rebased batches
  start after the server's head for this client.
- **The undo offer** keeps the window id it offers; the offer disappears as soon as reconciling shows the window open.
- **Pairs look as before** within a few pixels: each pane is its own box with square inner corners and the 6 px divider
  between; the old shared box and its `.desk-pane + .desk-pane` border are gone.

### Harness

Two checks added (51 in all): "a field on a desk left behind takes no typing; the focus follows the active window"
(a field put into the active window's body, alt+j, two letters typed) and "pairing and unpairing remount neither
window" (a mark put into each window's content before alt+, survives alt+, and alt+.). "The server's slots equal the
screen's" now reads each window's slot and pane from its own element. Run against the RD2 shell (with this round's
Reader and controller), both new checks failed: the field read `zz` with the focus still in the old window and nothing
inert, and no mark survived. The other failures of that mixed build came from pairing the old shell with the new rail
host and controller, not from the old shell alone.

### Commands and results
