# Reader workbench v2, RD4b: the scratchpads (frontend)

The frontend half of stage RD4 of `docs/specs/spec_reader_workbench_v2.md` (§10, §13.4, §16's RD4 row). Branch
`reader/rd4b-pads-ui`, on the RD3b tip with RD4a's branch (the pads backend) merged in. It calls RD4a's contract as
built (`pad.get`, `pad.apply`, `pad.submit_block`, `pad.proposals`, `proposal.label`, `pad.drain`, `carried.carry`,
`carried.list`, `carried.mark`; `docs/reviews/reader-rd4a.md`). There is no backend change, migration, algorithm tag,
prompt change, config field or Rust change; nothing of pen and ink (RD8a) or marimo cells (RD9b); the phone is
untouched.

## 1. What landed

| Scope item | Where |
|---|---|
| The client pad model: pads, blocks and anchors mirroring `pad.apply` op for op (versions, heads, anchor heads, tombstones, lift out), fractional position keys, re-stamping a queued op on newer pads after a conflict | `F:screens/desks/pads/model.ts` (pure) |
| Pad writes through the per-vault store: client-minted ids, expected heads, one sequence shared with desk batches, a pad read on demand, conflicts reconciled as desks are (re-read, rebase what still applies, report what was lost) | `screens/desks/store.ts`, `screens/desks/outbox.ts` |
| Sticky tabs: top `i·30`, bottom `(n−1−i)·30`, paper at least the viewport less the tabs, the active pad crossing the upper third, the merge amount over 56 px, the three grades (flat, order, distance) and fillets at opacity m; written per tab each scroll frame | `F:screens/desks/pads/stickyTabs.ts` (pure), `F:screens/desks/pads/PadStackWindow.tsx`, `styles/desk.css` |
| The running pad: dated headings ("SUN 22 NOV", "… · TODAY"), the jot line; named and problem pads; provenance per block (learner, source, tutor, LearnLoop) with the gutter marks | `PadStackWindow.tsx` |
| The live editor: `LiveMarkdownEditor` in place, the hint, ↵ keeps and opens the next block, shift+↵ a line break, ↑/↓ at the ends move between editable blocks, ⌫ on an empty block removes it, esc restores (and takes back a line opened and never written), blur keeps; a quote never opens | `PadStackWindow.tsx` |
| Hover cards from the gutter marks (source, tutor, figure, proposal): 160 ms open, 220 ms hide, tap toggles, esc closes; proposals read when a pad is shown and after a write, labelled `opened`, `not_this`, `dismiss`, or `ignored` (a card closed with nothing chosen) | `PadStackWindow.tsx` |
| Two-way links: a quote's back-link opens its passage beside; a passage linked from a block shows ✎ beside it, which scrolls the pad to the block and flashes it 1.8 s; a source piece inserted from the menu is linked in the same write | `PadStackWindow.tsx`, `F:screens/desks/pads/PassageMarks.tsx` |
| Lift out (a stub "→ lifted to …" and the block's own pad in the stack) and `alt+n` (a new named pad in this stack, or beside the focus away from one) | `PadStackWindow.tsx`, `model/workspace.ts` `openStackBeside`, `DeskShell.tsx` |
| Arrange (`alt+a`) and split (two or three pads one above the other, with dividers) | `F:screens/desks/pads/PadOverlays.tsx` (`ArrangeOverlay`), `PadStackWindow.tsx` |
| The pad menu (right-click, or `.` on the hovered line): Ask, Find, Show me, Make it practice, Carry, Teach me, Submit this block as…, mute suggestions; INSERT BELOW: sketch cell, "marimo cell · arrives with notebooks" (disabled), the source pieces in view, "a piece of another source…" (search in insert mode) | `PadOverlays.tsx` (`PadMenu`) |
| Sketch blocks with every tool (pen with pressure, line, arrow, box, text, eraser), a 20 px grid, growing 60 px near the bottom | `F:screens/desks/pads/SketchCanvas.tsx` |
| Submitting a block (attempt or teach-back) with the visible "submitted · attempt, <date>" / "submitted · teach-back" tag | `PadOverlays.tsx` (`SubmitSheet`), `store.ts` `noteSubmission` |
| Carried questions: the `? carry` chip on a question line, the pad menu's Carry, the drain's carry; the shelf's CARRIED (at most the attention limit, "since <date>", how many more); the quiet ◌ beside the passage it was carried from, logged `surfaced` once, with fruitful / not now / let it go | `DeskShell.tsx`, `Shelf.tsx`, `PassageMarks.tsx` |
| The drain (`alt+shift+q`): "Closing “<desk>”", each of today's pads with its first and last line, `Nk` keep, `Nl` leave, `Nc` carry the last line when it is a question | `F:screens/desks/pads/DrainPanel.tsx` |
| The companion's answers propose "Add this to your pad" into the desk's running pad; accept writes a `tutor_quote` block (provenance tutor, the day it was asked) | `DeskShell.tsx` (`answerProposals`), `companion/DiffProposal.tsx` |
| ⓘ "where your words go", and a quote-only pad saying nothing on it is read as your words; every block carries whether it is read as the learner's words | `PadStackWindow.tsx` |
| Display math in every container (pad blocks, hover cards, the companion's bubbles, thread windows) fitted to its column (scale ≥ 0.75) or given a horizontal scroller with a visible bar and its full height; room above and below; re-measured after fonts load, on resize and when KaTeX output lands | `F:screens/desks/fitMath.tsx`, `styles/desk.css` |
| Keys: `alt+n`, `alt+a`, `alt+d`, `ctrl+tab` / `ctrl+shift+tab`, `.` and the menu key (on a pad line), `alt+shift+q` (new) built; `alt+j/k` go through a stack's pads (or split panes) before the next desk | `keys/router.ts`, `DeskShell.tsx` |
| Fixtures: the pads (a running pad over two days, a named pad), the display-math pad, a carried question, a proposal, the drain, and a companion answer with display math | `F:fixtures/desks/pads.ts`, `fixtures/desks/workspace.ts`, `fakeCore.ts`, `companion.ts`, `harness.tsx` |

### Lifecycle and keys

- A paused pad window (hidden desk, offscreen, a preview card) reads no pad and no proposal and writes nothing: the
  jot line, the editor, lift out and sketching all refuse while paused. Back on screen it reads them.
- The editor claims the typing scope while it is open; its frame takes the focus in the frame between ↵ and the new
  box mounting, so letters typed at once never reach the desk's bare keys. The pad menu, the arrange overlay and the
  submit sheet claim the menu scope; the drain is a menu scope at the shell. Their keys go through the window's
  listener hub; the pad menu closes when its window stops being active. The drain and the overlays ignore modified
  keys (without that, `alt+l` in the drain was read as `l`, leave; found and fixed before landing).

## 2. Judgment calls (please confirm)

1. **A stack's pads beyond its own entries live in the window's view.** No desk op changes a stack window's entries
   (RD0 and RD4a have `open_window` with a stack, nothing after). A new pad (`alt+n` inside a stack) and a lifted
   block's pad are added through `set_view` as `view.addedPads`, which the stack shows after its own entries. The pad
   itself is stored and kept either way. Options: (a) keep this; (b) a backend `set_stack` (or `add_to_stack`) desk
   op, after which the client moves `addedPads` into it; (c) open a new stack window for every new pad. I took (a)
   because it needs no backend change; (b) is the clean answer.
2. **Where a submission goes.** A block in a problem pad answers that pad's item (the open problem whose session
   the pad names); a check cell answers its item; a block linked to a passage can be a teach-back of the idea the
   passage teaches (`request_teach_back` with the learning object the passage union names). The attempt is recorded
   in the shell's practice session; with none open the sheet says "start a practice session first" and sends
   nothing. The block's words are flushed and the current head is submitted.
3. **Make it practice needs a passage.** `author_practice_item` needs a learning object, so the row shows only on a
   block linked to a passage, and the sheet asks for the question and what a right answer says.
4. **Show me writes a `figure` block.** The pad menu's Show me runs the Reader's figure build (`figure.request`,
   origin `show_me`, read until done) and, when a figure is shown, writes a `figure` block below the line naming
   it. There is no figure surface on the desks yet (§13.1); the block's card says what it is.
5. **The sketch cell's letter.** §9.2 gives the sketch cell row `k`, and §5.4's matrix gives an open menu `j`/`k` to
   move. Moving wins: the row shows no letter and is chosen with ↑↓ ↵ (or `alt+d` from the pad). Options: keep, or a
   different letter for the row.
6. **`.` and the menu key are built for pad lines only.** They were waiting for RD5 (the menus). On a hovered pad
   line they open the pad menu now; elsewhere they do nothing, as before, and go on to the window.
7. **Display math is `$$` on lines of its own.** The app's markdown pipeline reads a one-line `$$…$$` as inline
   math, so §13.4's fitting applies to display blocks (the tutor's, the Reader's `\[…\]`, and `$$` on their own
   lines in a pad). A learner's one-line `$$…$$` renders inline and is not fitted. Options: keep, or make a one-line
   `$$…$$` on its own paragraph a display block in the pipeline (an app-wide change).
8. **A source's macros in pad quotes (§13.4 rule 4) are not applied.** A quote block does not carry its source's
   macros, and reading them needs the source's render. Options: (a) the append path (RD5) stores the macros the
   quote uses in its payload; (b) the pad window reads each quoted source's macros once and caches them.
9. **Problem pads show as pads of kind `problem`** ("a problem · <date>" on the tab, submit answers its item) when a
   stack holds one; there is no new entry point that opens a workbench session's pad on a desk.
10. **Proposals on blocks that have their own mark** (a quote's §, the tutor's ◇) are not shown as a second mark;
    the proposal mark takes an empty gutter only.

## 3. The mockup, compared in words

Compared side by side in headless Chromium against the mockup's deep links (screenshots kept in scratch only and
deleted). The mockup's book text was not copied anywhere.

- **#tabs=distance,pad=2,padf=0.4.** Same structure: cream tabs with dark borders stacked top and bottom, the open
  tab white and merged into the paper, distance-graded margins so tabs far from the open one are narrower, and
  fillets flaring the open tab's bottom corners into the paper. The mockup's tab meta reads "beside the Guide ·
  today"; ours reads "running · today" (where a pad sits beside is not stored).
- **#tabs=order.** The order grade's 9 px per index is built; the grade is read from the window's view.
- **#s11=run.** Same: dated amber headings with a rule, Literata prose on #fdfdfc, the gutter's §/◇/fig marks, the
  quote's amber back-link chip, the tutor's dotted rule and mono text, the green submitted tag, the jot line.
- **#s11=lift.** Same stub sentence and a new tab; our "lift out" button shows on hover at the block's right.
- **#s11=sketchqk.** Same tool row and grid; ours draws in the canvas's own units (the column may scale it).
- **#s12=info.** Same text; the mockup puts "ⓘ yours" in the window's title bar, ours on a thin row at the top of
  the pad window (the title bar is the shell's).
- **#s12=submitted.** Same tag and colour.
- **#s11=menu.** The mockup's menu shown is the source passage's (with promoted rows and "Append to …"), which is
  RD5's. Ours is the pad line's: the fixed verbs, then INSERT BELOW THIS LINE, as §9.2 lists them.
- **#append.** The mockup's frame is the passage menu's append, RD5's verb. The pad side is built: a source piece
  inserted from the pad menu lands below the line, linked to its passage; the companion's answer lands at the end
  of the running pad.
- **#markback / #backlink.** Same: an amber ✎ chip at the passage's right edge; a click scrolls the pad to the block
  and flashes it; the quote's back-link opens the passage.
- **#s11=arrange.** Same: over the pad window, ARRANGE in amber, cards with ●/○, the title and the pad's first line,
  the key line at the foot.
- **#s11=split.** Same: pads one above the other with a divider; ours titles each pane with the pad's title.
- **#figmark.** The mockup's figure marker on a passage is §13.1's (not this stage); a `figure` block in a pad has
  its `◇ fig` gutter card.

## 4. Display math (§13.4, an owner rule)

- **Rules built.** `.desk-math .katex-display` has `.45em` top and `.55em` bottom padding and `overflow: visible`, so
  nothing between an equation and its window's scroller clips it; pad blocks, cards and companion items have no
  fixed height or overflow. A wide equation is scaled through `.katex`'s font size (so its height follows) down to
  0.75; below that it scrolls horizontally with a 6 px bar drawn by `::-webkit-scrollbar` (always shown and given
  room in WebKitGTK and Chromium; a standard `scrollbar-width` would switch those styles off) and extra room above
  and below, because a scroller's box clips vertically. Measured on render, after `document.fonts.ready`, on
  resize and when KaTeX output lands.
- **The real-webview fixture** (`desk-harness.html?latex=1`): fractions of sums, an aligned derivation, a matrix,
  `\left( \right)` with tall content and a wide equation, in a learner block, a quote, a tutor quote and a check cell,
  in pad windows 640, 430 and 300 px wide, and in a hover card; and the same math in the companion's answer on the
  desks page. Each equation's ink (the union of the client rects of KaTeX's `.vlist` and `.mord` spans) is compared
  with the visible rect of its nearest clipping ancestor below the window's scroller: at least 3 px above and 5 px
  below; a wide equation is scaled at least 0.75 or sits in a horizontal scroller whose bar takes room. Again after a
  resize. Fail-first: with the fitting switched off, five of the fixture's checks fail.
- Playwright hides scrollbars in headless Chromium; the pads and display-math runs launch Chromium with scrollbars
  drawn, as the app's webview draws them.

## 5. Tests

- vitest: `pads/model.test.ts`, `pads/stickyTabs.test.ts`, `pads/PadStackWindow.test.tsx` (provenance, a quote-only
  pad emitting nothing, the editor's keys and its typing scope, a paused window reading and writing nothing, lift out,
  the pad menu, submitting, proposals and their labels, a linked source piece), `pads/SketchCanvas.test.tsx`,
  `fitMath.test.tsx`, `store.test.ts` (pads in the store), `DeskShell.test.tsx` (alt+n beside, the drain and its
  keys, CARRIED on the shelf, the carried ◌ and its marks, the companion's proposal into the running pad),
  `keys/router.test.ts` (the pad keys built).
- Fail-first: a paused window's write guard and read guards (each removed, the lifecycle test fails); the sketch's
  pointer units (removed, three tests fail); the flush chain (below); the fitting (above).
- The harness's pads run checks the RD4 deep links' equivalents (§3), the § row's hover fade, the editor writing
  through `pad.apply`, the carried ◌ logged once, the drain, and the companion's math.

## 6. Bugs

- **RD4b-1** (ledger): concurrent flushes sent a batch queued after a conflict before the store had reconciled, so a
  second conflict was reported for one edit. Flushes are chained one at a time. Fail-first: without the chain the
  pad reconcile test sees two conflict notices.
- Found and fixed before landing, in this stage's own code: `alt+l` with the drain open was read as `l` (leave); a
  sketch drawn in a scaled canvas landed away from the pen; passage marks wrote `left`/`top` during a zoom's frames.

## 7. Not verified

- WebKit (WebKitGTK, the packaged app's engine): the harness runs Chromium only. The `::-webkit-scrollbar` bar and
  the fillet gradients were not seen in WebKit.
- The desktop app was not launched; the sidecar's pad calls were exercised through the fixture core only.
- Show me end to end (the figure build is the Reader's; the fixture answers with no figure).
- Pen pressure on a real pen.
