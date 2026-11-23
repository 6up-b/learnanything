# Reader workbench v2, RD6b: the goal lens (frontend)

The frontend half of stage RD6 of `docs/specs/spec_reader_workbench_v2.md` (§12 except §12.6, §4, §16's RD6 row,
§18.3). Branch `reader/rd6b-goal-lens-ui`, on the RD6a tip with RD3's and RD4's fix-round branches merged in. It calls
RD6a's contract as built (`goal.band`, `goal.lens`, `goal.section_choice`, and `curriculum.path`, `set_depth`,
`path_override`, `set_scope`, `scope_decide`; `docs/reviews/reader-rd6a.md`). There is no backend change, migration,
algorithm tag, prompt change, config key, kill switch or Rust change, nothing of §12.6 (inline checks are RD7's), and
nothing on the phone.

## 1. What landed

| Scope item | Where |
|---|---|
| The band (§12.2): "◎ your goal · <kind> · <deadline>" with "your words, <date>", the sentence (Literata), "N learning objects · a likely · b untested", one dot per LO in path order (filled demonstrated, half likely, hollow untested; small for prerequisites; dimmed beyond the depth), a ◇ after an LO with a due check (no name, no hover; filled once answered), a dashed dot per unmatched phrase, the ring on the LO being read, the three depths, "you are reading", "next for the goal", dimmed/shown with the legend, and "path p" | `F:screens/desks/goal/GoalBand.tsx` |
| Criticality marks (§12.3): a 3 px bar 11 px left of the text (8 px gap in a book, 11 px in a paper, as the reference), solid / 34 % / dotted / a short grey tick for partial / none for unmapped; dimming (`nodim` toggles it; remembered per machine); the why card on a 120 ms hover or a tap (hides 160 ms after leaving; esc closes it): the level ("later · kept at learn to use it"), "For <goal>: <why>.", the learner's line, the coverage line and "judged per section" | `F:screens/desks/goal/marks.tsx`; drawn through a new optional `lens` on the Reader's windowing (`F:screens/ReaderScreen.tsx`, `windows/SourceWindow.tsx`) |
| Callouts (§12.4): a dark callout at the start of a section the path places (core, prerequisite, another way), from the path's own reason; a paper's section heads in the reference's light one-line form | `marks.tsx` |
| The path view (§12.5) on `p` (through the key router; a menu scope while open; esc or `p` closes it): the goal, what it resolved to, the unmatched phrases with "add it", the three depths with each one's size, "am I ready?" with the real pace line, the margin legend; per LO its readiness, primary section, "another way" with "use this one instead" (stored, `curriculum.path_override`), its check row, the exercise worth trying; "┊ not needed for your goal · read it anyway" (stored, `goal.section_choice`) | `F:screens/desks/goal/PathView.tsx` |
| A pad stack's goal line (`#goal=pads`): "◎ for your goal · …" from its pads' anchors through the lens | `F:screens/desks/goal/GoalLayer.tsx` |
| Every empty state (§12.8): no goal (no band; "◎ set a goal" in the top bar), a goal not mapped ("LearnLoop hasn't mapped this goal to your sources yet · map it", which runs `curriculum.set_scope` with the goal's sentence), a goal the learner did not set, "how deep for this?", a reading with no coverage (no marks; the reading says unmapped) | `GoalBand.tsx`, `GoalLayer.tsx` |
| The goal's state: the desk's goal (else the primary active one), `curriculum.path {judge: true}` once per goal per session, the band read again while the path is judged or its coverage checked, one whole-reading `goal.lens` per reading in a window that is not paused (filtered client-side; a scroll asks nothing), the learner's choices through the RPCs that own them | `F:screens/desks/goal/controller.ts`, `goal/model.ts` (pure) |
| The mount: the band row under the top bar, the chip, each source window's lens, the pad line over a stack, the overlays, `p` (the router's binding, no longer marked later), the desk's goal (`set_goal`, a new `setGoal` step) | `DeskShell.tsx` (additive mount points), `keys/router.ts`, `model/workspace.ts` |
| Tokens and styles: the goal variant's five tokens in `desk.css` (`--desk-gl`, `--desk-gl-sup`, `--desk-gl-skip`, `--desk-gdim`, `--desk-gband`); the rest of the reference's values in `goal.css` | `F:styles/desk.css`, `F:styles/goal.css` |
| Fixture: a synthetic goal over the softmax book and the attention note, answering as the sidecar does, on the harness's `?goal=1` page (the other runs keep no goal) | `F:fixtures/desks/goal.ts`, `fixtures/desks/fakeCore.ts` |
| The harness's goal run and the visual reference's `rd6` stage | `scripts/desk_harness/run.py`, `scripts/desk_harness/visual_reference.py` |

**Lifecycle and keys.** A paused window (hidden desk, offscreen, a preview card) asks for no lens; it keeps the marks
it has. `p` is the router's reading-scope binding; while the path view is open the router reads a menu scope, so no
desk key fires (the view takes esc and `p` on its own dialog). The why card's esc goes through the hovered window's
listener hub. "You are reading" reads the passage 80 px below the focused window's top (the reference's rule), again
on scroll through the window's hub.

**Display math.** No goal surface sets math: callouts, why cards and path rows carry the path's plain-text reasons.
Passages keep the Reader's own fitting (§13.4); a mark is a gutter element and changes no passage's layout.

## 2. Judgment calls (please confirm)

1. **"No goal" is remembered per desk on this machine.** A desk with no stored goal shows the learner's primary goal
   (§12.1), so `set_goal(null)` cannot also mean "the lens off". Choosing "no goal" stores `null` and a per-machine
   "off" flag for that desk; choosing a goal clears it. Options: keep, or a sentinel goal id in `desks.goal_id`.
2. **The why card opens per passage, explains per section.** The hovered passage's mark lights (`.on`, as the
   reference); the card is its section's (D1), with "judged per section" on its last line.
3. **A pad stack's line covers the stack.** The reference writes one line per pad body; the line sits between the
   window's head and its body (pads are another worker's files this stage) and names the highest-need level among
   the stack's pads' anchors.
4. **A later LO's dot is small too:** the band's later LOs are always prerequisites the deeper depth reaches.
5. **The path view's not-needed list** is the skippable and later sections of the readings on the desk (the lens
   is read per reading), with "read it anyway" or "dim it again".
6. **`curriculum.path {judge: true}`** runs once per goal per session, when the goal opens (RD6a §5.1): it starts
   coverage and the judgment in the background; the band is read again every 6 s while either runs (a design value).

## 3. The reference compared (measured)

The shared private reference set (the goal variant's captures, 1440 × 900 and 1280 × 800) and its tool,
`scripts/desk_harness/visual_reference.py --stage rd6`. The goal lens's 55 regions were added to the tool and to the
private capture's selectors, and the nine goal states captured again (the private capture's merged index kept every
other capture). Colours, type and tokens exact; geometry within 2 px where it does not follow content (§3 of
`reader-visual-reference.md`). Screenshots and measurements stay in scratch and the private directory.

| State | Regions compared (design / laptop) | Exact | What differs, and why |
|---|---|---|---|
| `#goal=frame` | 19 / 17 | all | — |
| `#goal=why` | 24 / 22 | all | — |
| `#goal=whysup` | 24 / 22 | all | — |
| `#goal=whyskip` | 24 / 22 | 23 / 21 | The band's reading ring sits on another dot: the reference reads a prerequisite's passage, the fixture a core LO's (the ring's own values are equal). A supporting mark is out of view at 1440 (the fixture's layout) |
| `#goal=basics` | 23 / 21 | 22 / 20 | The hovered later mark is purple: the harness hovers it, the reference opens its card from code; the reference's own `.g-later > .gm:hover` is the same purple. Core marks are scrolled out of view at the later passage |
| `#goal=path` | 36 / 34 | 34 / 33 | The reading ring on another dot (as above) |
| `#goal=paper` | 18 / 16 | all | — |
| `#goal=pads` | 17 / 15 | all | — |
| `nodim` | 18 / 16 | all | — |

Tokens: the five goal tokens equal the reference's in every state (the other token rows are the landed stages', in
`reader-visual-reference.md` §4). The type follows the reference: interface text JetBrains Mono, the goal sentence and
the path's heading Literata. The mark's gap to its text (8 px in a book, 11 px in a paper) and its 5 px insets are the
goal run's checks (below); the tool compares the mark's width. The pixel figures (14–50 % changed) track the fixture's
different text and arrangement, as for every stage.

**Left as they are:** the reading ring's LO (content), a hover style against a programmatic one (equal values), and
regions out of view in one viewport (layout).

## 4. Tests

- vitest: `goal/model.test.ts` (indexing a whole-reading lens, the client-side range filter, dimming, the why's lines,
  the band's lines, "you are reading", callouts, held LOs), `goal/components.test.tsx` (the band, the marks and
  callouts, a paper's form, the why card and a held one, the why's 120 ms / 160 ms / tap / esc timing, the path view
  and its stored choices, a held row), `goal/GoalDesk.test.tsx` (on the real DeskShell: the band, `curriculum.path`
  judged once, one whole-reading lens per reading in view and none for a paused window, `p` through the router and the
  menu scope, the depth, the goal switch and the chip, an unwired transport). 29 tests.
- Fail-first: the paused-window filter removed, the lens test fails; the path view's menu scope removed, the key test
  fails (each restored after).
- The harness's goal run (`run.py --only goal`, 21 checks): every RD6 deep link's equivalent, including the marks'
  colours, widths, gaps and insets, the dimmed colour, the why on core, supporting, skippable and later passages,
  `set_depth`, the path view's frame (300, 70, 1240 × 770 at 1600 × 960) and read it anyway stored, the paper's
  marks and head, the pad line, nodim, and the lens calls.

## 5. Not built here, and what waits

- **RD7:** inline checks and veils; the ◇ to administer (a due check shows "◇ n cold checks due today" and hides the
  LO's purpose text, as the backend sends it).
- **Shelf rows' marks and minimap ranges, transcript marks and video scrub segments** (§12.3 "where the marks go"):
  not built. The shelf is another worker's file this stage; transcript paragraphs render inside the watch panel, which
  the lens hook does not reach yet. The backend sends what they need (`goal.lens` per transcript reading by `t0/t1`).
- **Callouts on video transcripts and pads beyond the stack line, "◎ goal in context" in the companion** (the
  companion already marks a desk with a stored goal), and **the Teacher lesson row** in the path view (it needs the
  lesson RPCs; RD9a). The exercise row is the path line's own `exercise` when it has one.
- **The blue highlight exemption from dimming** (§12.3): the lens classes passages, not the Reader's highlights.
- **RD-retire:** the Guide rail and the reading-path panel stay beside the lens until then (§21.1).

## 6. Bugs

None found in landed code. Found and fixed before landing in this stage's own code: a new callback each render
re-ran the band read in a loop (callbacks are read through refs); the band's reset rule outranked its own button
sizes (now `:where`); a whole section's marks lit for one hovered passage.

## 7. Not verified

- WebKit (WebKitGTK, the packaged app's engine): the harness and the reference run Chromium only.
- The desktop app against a real vault's goal (the lens was driven through the fixture).
- Pointer gestures on a touchpad.
