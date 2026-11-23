# Reader workbench v2, RD5b: the context-aware right-click (frontend)

The frontend half of stage RD5 of `docs/specs/spec_reader_workbench_v2.md` (§0 item 7, §4.4, §9, §10.6, §16's RD5
row). Branch `reader/rd5b-menus-ui`, on the RD4 frontend fix round's tip with RD5a's branch (the menus backend) and
the visual reference merged in. It calls RD5a's contract as built (`passage.promoted`, its job and cancel,
`passage.knows`, `proposal.label` with `proposalKind: "promoted_row"`; `docs/reviews/reader-rd5a.md`) and the
existing entries its verb table names. There is no backend change, migration, algorithm tag, prompt change, config
field, kill switch or Rust change, and no model call.

## 1. What landed

| Scope item | Where |
|---|---|
| One menu, one listener | `screens/desks/menu/` (`model.ts` what was right-clicked, the verbs per kind, placement; `ContextMenu.tsx` the menu; `verbs.ts` each verb's call; `KnowsPanel.tsx` What this knows). DeskShell catches `contextmenu` once, in the stage's capture phase, and stops it there, so the Reader's tag menu and a cue's menu inside a window never open beside it (§4.4's "opens twice") |
| The objects | a passage (`[data-span-id]`), a transcript cue (`[data-transcript-span]`, with its time from a new `data-t`), a highlight or margin note (`data-annotation-id`/`-kind`, put on a marked passage by the Reader and on each card in its notes rail, the card naming its passage), a window header (`.desk-pane-head`), a pad line (`[data-pad] [data-block]`, handed to its stack's handle so the rows stay the pad's) |
| `.` and the ContextMenu key | the key router's `menu` action: the pad menu on a hovered pad line, else the menu on the hovered object, else on the focused window's first visible passage (or its header). An open menu claims the `menu` scope, so a second `.` does nothing |
| The split layout | the header (`<kind> · “<46 characters>”`), then up to four promoted rows in their own block with their reasons, then the fixed verbs of that kind in their fixed order and letters, What this knows after a rule in the design aid's green |
| Promoted rows | cheap rows from `passage.promoted` at once; with `pendingJob`, the job is polled on the one poller under the menu's window (a paused window's poll waits) and its rows replace the cheap ones when done; closing the menu before then calls `passage.promoted_cancel`. `checked: false` reads "found by search, not checked". A parent's new object for the same calls neither asks again nor cancels the job |
| Labels | `proposal.label` with `proposalKind: "promoted_row"`, `proposalId` the row's `rowId`: `opened` when a row is run, `dismiss` (×) and `not_this` (shown on the selected or hovered row); a dismissed row leaves the open menu at once, and the server leaves it out on that object afterwards |
| The pad menu | the same component: its rows (§9.2) map onto the menu's sections, `INSERT BELOW THIS LINE` (or `AT THE END OF THIS PAD`), marimo's one disabled row, mute; it gains Note in margin (a `note` block with `payload.parent_block_id`) and What this knows, and its promoted rows come from `passage.promoted` on the pad line. Show me is offered only on a line with a passage. PadStackWindow's own `onContextMenu` is gone |
| Teach me's window | `lesson.turn {action: "open", entry: "reader_selection", selection}` then `open_window {kind: "lesson", lessonId}`; the desks' pane body gains a `lesson` case rendering the Teacher's `LessonScreen` (resume) |
| Carried layout: TODAY · RUNNING PAD | the shelf's lower part, above CARRIED: the heading, `open`, and the running pad's last three blocks of today, each marked (`◇ fig`, `§`, `◇`, `›`); `open` focuses the stack and scrolls it to the running pad (VR-29) |
| Carried layout: "Scratchpads ⓘ yours" | a pad stack's title bar: "Scratchpads", the circled ⓘ opening "where your words go" under it, "yours" as its place (RD5b-1) |

### The verbs and their server entries

| Verb | Kinds | Call |
|---|---|---|
| Ask (`a`) | passage, cue, highlight, note, pad line | the companion summoned at the object with its words as the chip (`companion.ask` when asked; a pad line's names its block) |
| Note in margin (`n`) | passage, cue, pad line | a small sheet for the words, then `reader.capture` action `annotate` with the passage's (or selection's) nodes; on a pad line, a `note` block under it |
| Append to (`w`) | passage, cue, highlight | the remembered pad of this desk (else its running pad); the submenu lists the desk's pads with ✓ on the current one and "+ a new pad" (`create_pad` + `add_to_stack`). Writes `insert_block` `source_quote` and `link_anchor` with the passage's highlight (`reader.capture` `highlight` when it has none) in one batch |
| Carry (`c`) | passage, cue, highlight, note, pad line | `carried.carry` with the passage as its anchor |
| Open beside (`b`) | passage, cue, highlight | the first promoted `correspondent`, `next_step` or `elsewhere` row's place; else `reader.correspondents` (search fallback) on the passage's section, saying "found by search, not checked" when it is |
| Find in my sources (`/`) | all but window | search in context on the words |
| Compare (`=`) | passage, cue, highlight | opens a Compare window on the words (`{kind: "compare", query}`) |
| Show me (`v`) | passage, cue, highlight, pad line | `figure.request` origin `selection`, the build polled under the window; a shown figure lands as a `figure` block in the desk's running pad; none shown, nothing lands and it says so |
| Make it practice (`p`) | passage, cue, pad line | after a review sheet: `reader.import_exercise` when What this knows reads the passage as an exercise, else `reader.author_section_question` on its section; from a pad line, the item form prefilled (no server draft) |
| Teach me this (`t`) | passage, cue, highlight, pad line | `lesson.turn` open, then the lesson window |
| Submit this block as… (`s`) | pad line | the pad's submit sheet |
| New desk from these, Gather linked sources, Share a slot, Own slot | window | the desks' own moves on that window (gather to a new desk, gather, pair, unpair) |
| What this knows (`i`) | all | `passage.knows`: per place, grouped (questions, pads, highlights and notes, what LearnLoop read in your words, carried, linked passages, figures, written questions, a due check as a fact only), each with its anchor quality, "may need re-anchoring" for an alias that does |

## 2. Judgment calls (please confirm)

1. **Verbs per spec, not the mockup's three.** The mockup's selection and highlight menus show Ask, Note in margin
   and Append only; §9.1 and RD5a's verb table give each object kind its full set. The spec wins, so the menu is
   taller than the mockup's (about 460-480 px against 300); it scrolls within the viewport when it must.
2. **Show me's destination for a passage** is the desk's running pad (a `figure` block), with a toast. The
   companion's figure surface (§13.1) is not built; when it is, the destination moves there.
3. **Compare** opens the existing Compare window on the selection's words; the comparison itself runs when the
   learner asks there (no compare is started from the menu).
4. **Note in margin** writes through `reader.capture` action `annotate` (the client's existing capture call):
   `reader.create_annotation` is not exposed to the client, and no backend change was needed.
5. **Make it practice** asks before anything joins the queue (one small sheet), then imports or drafts.
6. **A highlight is the marked passage.** The Reader marks highlights per passage, not per word, so a right-click
   anywhere on a highlighted passage opens "your highlight"'s menu (its verbs, not a plain passage's). A margin
   note's card in the notes rail opens "your margin note".
7. **The Append target is remembered per desk in this viewer's browser storage** (a per-viewer convenience; the
   running pad when nothing is remembered or the remembered pad left the desk).
8. **The notebook seam (§11.3).** The pad menu's rows are plain data handed to the one menu (`MenuRow` with
   sections), so a notebook frame's "the lesson" menu can hand its rows in the same way; nothing of it is built.
9. **`#s11=menu` moved to the visual reference's rd5 stage.** The mockup's link is a selection's menu over the book
   (RD5's surface), so it is compared against a selection's menu now; the pad line's menu renders the same
   component and is covered by vitest and the harness's pads run.

## 3. The mockup, compared (measured)

Through the shared private reference set and `scripts/desk_harness/visual_reference.py --stage rd5` (new states
`#s11=menu`, `#menu=cue`, `#menuhl`; regions `pad_menu`, `pad_menu_row`, `pad_menu_head`, `auto:div.pro`,
`auto:span.why` now point at the one menu), both viewports. Tolerance: geometry within 2 px (§4.3 and the reference
doc), colours and type exact.

- **Matching, measured:** the frame (`#181818`, 1 px `#3a3a3a`, radius 4, shadow `0 18px 50px #00000099`, padding 5,
  360 wide, 12 px JetBrains Mono, text `#eeeeee`); the header (10 px `#a8a8b8`, padding 4/9/6, 23 px); a verb row
  (padding 5/9, radius 2, line height 16.8, 26.8 px; the grid of 18 px glyph, label, key, gap 7); the selected row
  (`#241d12`, an inset 2 px `#e3a063` rule, text `#d8d8e0`, its reason `#a8a8b8`, its key amber); a reason (11 px,
  15.4 line, `#b3b3c0`); the promoted block (`#141414`, 1 px `#2a2a2a`, radius 2, padding 2/0, 5 px below it); the
  rule (`rgba(255,255,255,.08)`, 3/6 margin); keys 10.5 px `#8b8b9d`; the submenu 260 wide, 4 px right of its row
  and 6 px above it. Placement: 2 px down and right of the pointer, moved in to stay 10 px inside the right and
  bottom edges and below the 44 px top bar (the harness checks the pointer offset in Chromium).
- **Differences left, each explained:** the frame's height (judgment 1); in `#s11=menu` the first reason's colour
  is `#a8a8b8` here and `#b3b3c0` in the mockup, because the mockup's link has its Append row selected and ours
  selects the first row (both colours match per state); the token rows (absent mockup variables) are the visual
  reference's own finding, not this menu's.
- **The carried layouts:** `shelf_lower_head` now matches in `plain` (the TODAY heading: 10 px, weight 500, 1 px
  letter spacing, uppercase, `#8b8b9d`); in `#s12=info` the ⓘ button matches (`#8b8b9d`, 1 px `#3a3a3a`, circled).
  The pad window head's colours, the popover's text, size and shadow, and the carried item's style are VR-2, VR-37
  and the CARRIED rows of the visual reference (another worker's).
- **Fixed by this menu, for the other worker's ledger:** VR-40 (the pad menu's 340 px frame, `#d8d8e0` text, the
  heading's 10.5 px over a rule) no longer holds: the pad menu is the one menu, measured as above.

## 4. Tests

- vitest: `menu/model.test.ts` (verbs per kind and unique letters, the header, the server's object, the cap and
  dismissed rows, "found by search, not checked", placement and the submenu's, every object read from the DOM);
  `menu/ContextMenu.test.tsx` (cheap rows then judged rows by the poller, the job cancelled on close, labels per row
  and a dismissed row gone, keys j/k/↑↓/↵/esc/letters with the disabled row skipped, chords left alone, the Append
  submenu, the section order, a parent's new object not restarting the request); `menu/verbs.test.ts` (each verb's
  call and arguments, a failed call said, a promoted row's place); `menu/KnowsPanel.test.tsx`;
  `DeskShell.menu.test.tsx` (one menu on a passage and the window's own menu shut, promoted rows differ by passage,
  a dismissed row labelled, a window header's menu, `.` through the key router, Teach me's window, Append's batch,
  the menu kept across the desks' re-renders, TODAY · RUNNING PAD, "Scratchpads ⓘ yours"); `PadStackWindow.test.tsx`
  opens the pad menu through the shell's listener as the desks do.
- Fail-first: the stage's listener removed (six DeskShell menu tests fail) and its `stopPropagation` removed (the
  one-menu test fails, the window's own menu opens); TODAY and the title reverted (both tests fail); a new promoted
  object per render (the re-render test fails: four requests).
- The harness's new `menus` run: one menu on a passage at the pointer in the mockup's face and colours, the judged
  row by the job saying "found by search, not checked", the verbs after the promoted block, **promoted rows differ
  by passage**, a menu closed early cancels its job, a window header's menu, `.` on the hover. The fixture core
  answers `passage.promoted` (a row per passage, a judged job on its second read), its job and cancel, and
  `passage.knows`.

## 5. Bugs

- **RD5b-1** (ledger): the pad stack's title and ⓘ placement (the layout carried from RD4).
- **RD5b-2** (ledger): the DeskShell suite's pads fake answered `passage.union_range` without `spans`; six unhandled
  rejections made vitest exit 1 on that suite, on RD4's frontend fix round's tip as well.
- **VR-29** (ledger, fixed): the shelf's TODAY · RUNNING PAD.
- Found and fixed before landing, in this stage's own code: the source menu's promoted calls were a new object on
  every render of the desks, which restarted the request and cancelled the judged job while the menu stayed open.

## 6. Not verified

- WebKit (the packaged app's engine): the harness runs Chromium only.
- The desktop app was not launched; the sidecar's calls ran through the fixture core and vitest fakes only.
- Teach me's lesson window beyond the open (the fixture has no Teacher); Show me end to end (no figure in the
  fixture); Open beside against a real `reader.correspondents`; Note in margin against the real capture.
- A highlight saved in the fixture's book: there is none, so `#menuhl` is compared on a passage's menu (the same
  frame, rows and type).

## Fix round (frontend)

The adversarial review of RD5 (Codex Astra, 2026-11-23; 2 blockers, 15 major, 6 minor) read main at batch 1. This
is the half whose fixes are in `apps/learnloop-tauri`, on the second integration batch's tip; every finding was
checked against that code first. The two blockers (protected material reaching rows, proposals and the judged job)
and the other Python findings are the backend half's. Ledger RD5-30 to RD5-46.

| Review finding | Outcome |
|---|---|
| Major: a menu closed before `passage.promoted` answered never cancelled its job | Fixed, RD5-30 |
| Major: menu A's late rows overwrote B's, and B's Open beside opened A's correspondent | Fixed, RD5-31 (the rows are told by the open menu only) |
| Major: a selection across passages quoted the whole run in every node; Append linked one passage | Fixed, RD5-33 (per-passage slices, every passage linked, the capture's placement read) |
| Major: a selection inside a highlight was dropped | Fixed, RD5-34 |
| Major: Make it practice on an exercise admits items behind a yes/no, with no review of the draft | **Stopped, options below** |
| Major: the pad's practice sheet authored twice on a double press | Fixed on the client, RD5-41 (one save at a time); the retry identity across a lost reply needs the backend's key |
| Major: a window header named no passage | Fixed, RD5-35 (the passage in view; a window with none offers its moves only) |
| Major: promoted actions half wired, all labelled opened | Fixed, RD5-32 |
| Major: Compare lost its intent and anchor | Fixed, RD5-40 (the anchored comparison through the selection's door, on confirm) |
| Major: a pad line's Teach me opened the app's lesson screen | Already routed to the desks' lesson tabs on this branch (RD9a wraps `reader.onTeachMe` with `openLesson`), but only when the app passes that hook; made one path, RD5-36 |
| Major: New desk from these ran gather | Fixed, RD5-39 |
| Major: Show me landed on the desk shown when ready; its poll leaked | Fixed, RD5-38 |
| Major: Teach me on a line linked to two readings mixed their spans | Fixed, RD5-37 |
| Major: a lost `passage.promoted` reply mints another job (no request identity) | Backend half (the key and its replay); the client sends it once the contract names it |
| Major: an interrupted vault's job can still publish rows | Backend half |
| Minor: focus and escape in the sheets, focus restored | Fixed, RD5-44 |
| Minor: the Append submenu by key | Fixed, RD5-43 |
| Minor: a failed label swallowed | Fixed, RD5-45 (retried under its id on the poller; a refusal says so). Labels pending at app close are not kept across a restart |
| Minor: What this knows misses notes and adjustments, opens little | Fixed on the client, RD5-46; `passage.knows` handing the notes in is the backend's |
| Minor: `n`, `b` never ran; `.` stopped at a stack | Fixed, RD5-42 |
| Minor: duplicate candidates keep the older timestamp | Backend half |

**Stopped: Make it practice on an exercise.** The import job writes schedulable items when it finishes, the same path
the Reader's own "use this exercise" takes; a review of the actual draft before admission needs the job to hold its
cards unwritten until an admit call, which is new persisted state (a draft held per import, or a column on the
import's rows). Options: (a) a prepare/admit split in the backend with that state, the menu showing the draft's
question, parts and answer with keep / not now; (b) keep the import as it is and show its written cards after it
finishes, each with the existing retire control, so a wrong one leaves the queue at once; (c) keep it as it is. The
record's earlier "review sheet" was wrong: the sheet is a confirmation of what the import does (judgment call 5),
not a review of its draft.

**Assumed of the backend half** (the client is ready, or reads them when present): a client key on
`passage.promoted` (sent once named); `passage.knows` returning `notes` as `passage.union_range` does (the panel
renders them); a margin note's or figure's promoted row may name its passage (`action.extractionId`,
`action.target.spanId`; the client falls back to the menu's passage); an identity key on `author_practice_item`.

**Assertions changed (the behaviour changed, nothing loosened):** a promoted row's action is called with the menu's
object as well; the Make-it-practice import test expects the selection's nodes without a quote when nothing is
selected (a selection now always carries its slices); the window header test closes What this knows by escape (it
owns the focus now).

**Checks:** typecheck clean; vitest 389 files, 4310 tests; the desk harness, every run, passes (the overview run
needs the comparison's `pillow`: 23 of 23 with it); visual reference `rd5` 2 rows and `rd4` 19, unchanged; pytest
identity pins, structure ratchets, mobile allowlist and desktop RPC contract 759 passed, architecture 18, layout 3;
ruff clean; lint-imports 54 kept. No Rust, config, HTTP use or migration changed. Each fix's test failed with the
code before it (run against the files at the previous commit).
