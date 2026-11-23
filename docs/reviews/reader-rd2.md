# Reader workbench v2, RD2: the overview and gestures

Stage RD2 of `docs/specs/spec_reader_workbench_v2.md` (§16). Branch `reader/rd2-overview`, from main `6d6815aa2e`
(RD1 landed). The change is frontend only, plus the harness script and the vault generator's descriptions and counts.
There is no migration, no algorithm tag, no config field, no RPC, no Rust change and no model call. The companion,
search, ingest screens and the phone are untouched. The owner deferred performance, so no frame budget is gated: the
harness records a frame-time trace as information, and §3.6's correctness rules (transform and opacity only, frozen
geometry, no inherited custom property changed during animation, no insertion during frames) are checked.

## 1. What landed

| Scope item | Where |
|---|---|
| The zoom engine (§6.3): geometry split, log-scale camera, the frame function, chase and spring, release rule, wheel classification, end latch, ctrl+drag progress | `F:screens/desks/overview/engine.ts` (pure) |
| One rAF writer, frozen geometry, the commit | `F:screens/desks/overview/controller.ts`; `DeskShell.tsx` (`planZoom`, `beginEnter`, `beginLeave`, the commit in `onEndRef`) |
| The commit-identity invariant | exact geometry in `engine.test.ts`; harness screenshots both ways under a documented tolerance |
| Cards with thumbnails and live miniatures (paused, invalidated on change) | `overview/Card.tsx`, `overview/miniature.ts`; the miniatures are built in `DeskShell.tsx` when idle |
| Curved links | `overview/links.ts` (relations, curves, gather order), `Card.tsx` `LinkLayer` |
| Overview keyboard and drag | `keys/router.ts` (the overview's bindings), `DeskShell.tsx` (`moveOverviewSelection`, card drag, background pan) |
| Gather, gather to a new desk, ungather | `DeskShell.tsx` `gather`; `model/workspace.ts` `reorderSlots`, `moveToDesk` |
| The wheel router and background-only ctrl+drag (§5.5, D14 on its default) | `DeskShell.tsx` (one capture wheel listener on the shelf and stage; stage pointer handlers) |
| The HUD | `.desk-hud` (bottom centre), written by the wheel and the drag |
| The laptop rail | RD1's rail (44 px, ☰ overlay at 260 px), now checked in the harness at 1280×800 |
| Reduced motion | the zoom becomes a .25 s crossfade (`desk-fadeswap`); `reducedMotion` prop for tests, else the system setting |
| Previews log nothing | in the overview every window's lifecycle state is `preview` (paused, no visit, no progress); miniatures are inert clones with no listeners |

### How the zoom works

- **Coordinates.** All desks' windows sit in one world element. In the reading view the world's transform is the
  identity, and each slot is laid out (`left/top/width/height`, as in RD1) where it shows on the stage. In the
  overview, slots are laid out at their card rects in the overview's own layout (rows at 0.75 of the stage height,
  330 apart, cards at least 760 wide after the links' 170 px gutter) under the camera `translate(x, y) scale(0.34)`.
- **A zoom.** When a zoom begins, both rect sets and both cameras are computed once (`planZoom`). Each frame the writer
  sets the world's camera (scale in log space; `q` is the linear fraction of the scale change). It morphs each slot's
  box from its laid-out rect by `translate + scale`, counter-scales the content, fades the content over
  q ∈ [.45, .85] while the card face fades in, recedes unrelated cards to `1 − .62q`, fades the links and labels over
  q ∈ [.6, 1] and the slivers by `1 − 3q`, and fades the focus edge over the first third. All of this is written
  straight onto the elements; React lays nothing out during a zoom.
- **Rings.** The selection's ring (3k amber with a 7k halo) and the related cards' cyan rings are sibling elements
  laid out at the cards' rects, morphed with their boxes and faded in with q. A box-shadow on a box that scales
  unevenly would come out uneven.
- **The commit.** At rest, one commit (`flushSync`, then the writer's clean-up in the same task) lays out the view the
  zoom ended on. While a zoom leaves the overview, the desk it lands on already carries its soft crop and slivers.
  Transitions on the windows stay off for two frames after leaving, so `left/top` never animate the commit. A key or a
  pointer press during a zoom settles it at once. A cancel lays out nothing.
- **Content during the zoom.** Only windows on screen when the zoom begins keep their content through it (`live`). The
  rest show their card face. In the overview the content is hidden and its size stays the reading size.

## 2. The invariant and its checks

**Exact geometry** (`overview/engine.test.ts`): the last frame entering has each window's transformed box equal to
its card rect within 0.5 px, with the camera equal to the overview's. Leaving, the last frame is the reading layout
under the identity camera. The first frame entering moves nothing. The writer (`controller.test.ts`) ends on the
goal's exact frame (box transform equal to the card rect to 1e-6).

**Screenshots** (harness). The harness drives p through the shell's debug handle, takes a screenshot at the last frame
and another just after the commit, and compares the stage area. A pixel counts as changed when a channel differs by
more than 24. The documented tolerance is **0.1 % of the stage's pixels**, set from the measured rasterisation noise:

- entering: **0.0069 %** changed (0.0008 % on an earlier run);
- leaving: **0.0090 %** changed.

The tolerance was 0.5 % while the rings were box-shadows on the morphing boxes. At that tolerance entering measured
0.22–0.41 %, which is how the uneven-shadow problem was found and fixed.

**Correctness of the frames** (harness, MutationObserver over a zoom's frames at p = .1 … .9): the frames changed
only `transform`, `opacity` and `box-shadow` (the focus edge). They inserted no element and touched no custom
property.

## 3. Keys as built (additions to RD1's matrix)

| Chord | Scope | Action |
|---|---|---|
| `alt+o`, `o`, the top bar's "o overview" | reading, focus, overview | zoom out, or back to where it was |
| `h j k l`, arrows, `alt+h/j/k/l` | overview | move the selection (left and right in a desk; up and down to the next desk's card nearest by x-centre); the camera follows over .2 s, 48 px inside (74 from the top) |
| `↵` / click a card | overview | open the selected card (zoom into it on its desk) |
| `alt+↵` | overview | open it in focus mode |
| `esc` | overview | back to the desk and focus the overview was entered from |
| `b` | overview | relations on or off (rings, links, receding) |
| `g` held | overview | gather preview: dashed cyan ghosts where the linked cards would go |
| `alt+[` / `alt+]` | overview | move the selected card along its desk |
| `alt+shift+j/k` | overview | move the selected card to the desk below or above |
| `alt+g` / `alt+shift+g` | reading | gather / gather to a new desk ("gathered · <short name>"; a placeholder sliver "→ moved to …" for 6 s); `alt+g` again or the footer's `↺ ungather` undoes |
| drag a card more than 8 px / drag the background | overview | move the card (row and index by drop point) / pan |
| wheel | overview: pans; reading: plain scroll stays the window's | see §5.5 |
| alt + horizontal swipe, shift + wheel | reading | pan the strip; snap after 120 ms idle to the nearest window's left edge, which takes the focus |
| alt + vertical scroll, ctrl + scroll, pinch | reading and overview | zoom: touch chases (420 px is the whole zoom), pinch `p += dy/108`, a notch runs the whole eased zoom (a notch the other way turns it round); at an end the stream is latched for 150 ms |
| ctrl + drag on the stage background | reading | scrub the zoom (320 px is the whole zoom); inside a window's content ctrl+drag stays the box selection |

`b` in the reading view stays RD5's promoted action (not built). The overview passes no reading-view key.

## 4. Tests

New: `overview/engine.test.ts` (18), `overview/controller.test.ts` (7, including miniatures), `overview/links.test.ts`
(5). `DeskShell.test.tsx` gains the overview (zoom out and back with every window a preview; selection moves and `↵`
opening on another desk; reduced motion; `alt+shift+j`; `b`; `g` ghosts; a key settling a zoom), gather and ungather,
gather to a new desk, the alt + swipe pan and snap, and the alt + wheel zoom. `keys/router.test.ts` gains the
overview's scope and records that nothing waits on RD2 any more.

**Fail-first** (each guard broken by one line in the worktree, its tests run, the file restored):

| Broken | Test | Result |
|---|---|---|
| the camera interpolated linearly instead of in log space | `engine.test.ts` | 2 failed |
| the morph measured from the wrong box (`a` instead of the laid-out base) | `engine.test.ts`, `controller.test.ts` | 1 failed |
| windows not previews in the overview | `DeskShell.test.tsx` | 1 failed |
| a key during a zoom not settling it | `DeskShell.test.tsx` | 1 failed |
| the end latch's same-direction swallow removed | `engine.test.ts` | 1 failed (after strengthening: the first version passed with the break, because the "already at the end" rule also swallowed) |
| a miniature keeping its window's mark | `controller.test.ts` | 1 failed |
| RD1's `content-visibility` selector restored | harness | 1 failed ("visible" for all eight paused bodies), ledger RD2-1 |

**Harness** (`scripts/desk_harness/run.py`, now `--with pillow==11.3.0` too): 49 checks, all passing. RD1's 30 are
kept; the two-player check now reads the clocks from the DOM's text, because a paused window's content is no longer
rendered. The overview run adds:

- alt+o into the overview, every window a preview, esc back;
- the identity screenshots both ways, the frames' writes, no insertion;
- navigation in view on 18 key presses;
- nothing logged while panning the overview;
- the four ways back (esc, o, alt+o, ↵, and a click) restoring the reading layout within 1 px;
- the frame trace;
- alt + notch out and back, ctrl+drag with the HUD, paused content not rendered, the alt + swipe pan and snap, a card
  dragged onto another desk;
- the laptop rail, and no error.

**Frame trace (information only):** one alt+o zoom took 20 frames, median 16.7 ms, p95 16.7 ms, max 16.7 ms. This is
headless Chromium on this desktop, not WebKitGTK or the packaged app.

## 5. The mockup, compared in words (served on 127.0.0.1, headless Chromium)

**`#ov` (the overview).**
- *Mockup:* every desk is a row of cards under an uppercase label. A card shows its picture first: a page image for
  books, the pad's tab list for scratchpads, a poster with time and a caption line for videos. Under the picture sit
  the glyph and name, a minimap bar with ticks, and up to two chips. The selection has an amber ring with a halo, its
  related cards cyan rings. Curved links with labels ("same idea", "markers point here") run between them, unrelated
  cards recede, and the companion sits as a corner pill.
- *Build:* the same rows, labels, picture-first cards (a live miniature of each opened window: the book's page, the
  video's watch panel with its player as a ▶ placeholder, the Guide rail), the name, the reading-progress bar, the
  selection ring and halo, cyan rings, curved labelled links and receding.
- *Differences, and why:*
  - no chips, no ticks and no "same idea" links: they need the union read and LO coverage, which the desks do not read
    yet. The build's relations are "opened beside", a book and its panels ("its panel", "its book"), and "same book"
    on another desk;
  - no pdf.js page bitmap or YouTube poster: the fixture has neither, and the live miniature serves every kind;
  - no companion pill (RD3);
  - a desk never opened shows "not opened yet" (its windows are not mounted until visited);
  - relations show for the selection, not for a hovered card.

**`#ovn=far`, `#ovn=down` (navigation).** The mockup pans the camera so a far selection stays inside the edges, and
moves to the card below with the camera following (world y moved up). The build uses the same rule (48 px, 74 from the
top, rounded away from zero so the margin always holds). The harness checks it on 18 key paths.

**`#scrub=0.5` (mid-zoom).** The mockup's frame at p = .5: camera scale √0.34 ≈ 0.583, columns half-morphed, content
fading with the card faces partly in, the companion still docked. The build's frame function gives the same scale and
q at p = .5 (unit-tested), with the same fades.

**`#ovg` (gather preview).** In headless Chromium the link rendered the plain overview (its ghosts need `g` held).
The build draws dashed cyan ghosts at the places the linked cards would take while `g` is held (tested).

**`#selftest`, `#selftest2` (the mockup's self-tests).** Its round trip logged entering and leaving the overview with
the companion's positions; its second test checked navigation in view. The build keeps both as harness checks (the
four ways back within 1 px; navigation in view) and as component tests. The companion part waits for RD3.

**`#lap=1`, `#lap=open` (laptop).** At 1280×800 the mockup folds the shelf to a rail and its ☰ overlays the strip at
about 260 px. The build does the same (44 px rail, 260 px overlay, checked). The mockup's top bar also drops chips the
build does not have.

## 6. Deviations, with reasons

1. **Windows are laid out by `left/top` at rest, and transformed only during a zoom and in the overview**, as in RD1:
   a transformed ancestor would misplace the Reader's fixed-position menus in the reading view. The world's transform
   is the identity at rest in the reading view.
2. **Chips, ticks and weight-1 links are not drawn** (union read and coverage are not read by the desks); the relations
   built are explicit ones and "same book".
3. **Thumbnails are live miniatures for every kind** (no pdf.js bitmap, no poster). A miniature is a static clone of
   the window's pane: built when idle after the overview opens, rebuilt when its window changed, inert, with frames as
   placeholders.
4. **Panning the strip by alt + swipe writes the camera through React state** (a re-render per wheel event). This is a
   performance question the owner deferred; it is correct.
5. **Gather to a new desk names the desk after the focus's title** ("gathered · <short name>"), not its main LO, since
   the desks have no LO data yet.
6. **A desk never visited shows its cards without content**; its windows mount when it is first visited, as in RD1.
7. **The shelf stays the current desk's in the overview**; a row's click opens its window and leaves the overview, as
   §5.6 says.

## 7. Commands and results

Each pytest run used `-n 1 -m "not arc_close"`, through the scratch wrapper, in a 3G scope; npm and cargo ran in a 5G
scope.

| Command | Result |
|---|---|
| `npm run typecheck` | exit 0 |
| `npx vitest run --maxWorkers=2 src/app src/screens/desks src/fixtures src/api src/screens/ReaderScreen src/screens/reader src/components/PdfReaderPane` | 196 files, 2184 tests passed |
| `npm run frontend:build` | built |
| `cargo check --offline` (no Rust changed) | Finished `dev` profile |
| the harness | 49 passed, 0 failed |
| `scripts/affected_tests.py --files <the 19 changed files>` | 5 test files: 196 passed |
| identity pins, structure ratchets, effective defaults, CLI snapshot, kill switches, sqlite copies, public tip guards | 412 passed |
| `tests/test_test_layout.py` alone / `tests/test_architecture.py` alone | 3 passed / 18 passed |
| `ruff check` / `lint-imports --no-cache` / `check_gate_partition.py` | All checks passed! / Contracts: 52 kept, 0 broken. / collected 33276: landing 33210 + arc_close 66 |
| `desktop_validate.py` | no count drift (358 files, 343 entry-reachable + 11 vitest-support, 364 ACTIVE); only the regeneration errors the landing clears |

No identity pin, golden, effective default or CLI snapshot moved. Ledger: RD2-1 (fixed).

## 8. Not verified

- WebKitGTK and the packaged app (Chromium only; the Playwright WebKit build is not installed), the laptop's touchpad,
  real pinch (synthetic wheel events only), and real YouTube.
- Any frame budget (deferred); the trace is headless and information only.
- The overview against a real sidecar and a large workspace (the fixture has 3 desks and 9 windows).
- The landing gate and the whole suite.
