# UX-62: the desktop records every passage shown during the learner's own reading

A fix to the first evening's step 2 (`docs/reviews/first-evening-step-2.md`), found by the live walk partread-1 on
2026-11-21. Branch `fix/ux62-seen-viewport` from main `f44283f88e`.

| Commit | What |
|---|---|
| `fca6ecbce4` | The desktop Reader observes every readable passage shown in the view during the learner's own movement (`passagesInView`, `useReadingProgress`), and a video the cue playback moves on from; the tests |
| `3802b4e036` | The phone Reader keeps a passage that came on screen and left within one observer delivery |
| `deb46d46fa` | The desktop tests draw and render each frame of a movement on its own (the fail-first comparison below is with this version) |
| (this record) | This record and the ledger rows UX-62, UX-63 and UX-64 |

No backend change, no wire change, no algorithm tag, config key, prompt, migration or kill switch. No new non-test
TypeScript file (`desktop_validate.py`'s counts do not move). No identity pin, golden or snapshot moved.

## What the walk found

A web-page chapter of **135 passages in one section**, read a screenful at a time to 72 %. The section's progress
count said **97 of 135**; `reader_seen_spans` held **11 passage identities**, one per scroll stop. Of the chapter's
**eight topics one qualified** for a first set (it cites a single passage that happened to sit under the marker at a
stop); the other seven stayed "unseen" though the learner had read their passages, and Today said "read a little
further".

**Cause.** The desktop sent only the passage under its reading marker (70 % down the reading area), plus the one the
marker left behind as it moved forward (`observedPassages`). A screenful step moves the marker a whole screen in one
frame, so each stop recorded one passage and everything else on screen was never named. The count, a position
(passages up to the marker), was right; the identities were not. The backend was not at fault: it keeps every id of
the section it is sent.

## The rule as built

**The guard is the existing one.** A frame observes only when the learner moved the page themselves (a scroll within
1.2 s of their wheel, touch, scroll key or mouse press on the reading pane, or `readingMoved` already true since) and
no placement is settling (1.5 s after a jump, a resume, a seek, a placement). Every placement resets it at once
(`movedRef`, set beside `readingMoved`), so a frame drawn before the placement's render cannot observe where it
landed.

### Text view (and a PDF with passage boxes)

**The geometric test** (`passagesInView`, `screens/reader/readingPosition.ts`): the reading area is the scrolling
pane's box (`getBoundingClientRect` of the Reader's body). A passage element `[data-span-id]` is shown when

    rect.bottom > area.top  &&  rect.top < area.bottom

that is, some part of it lies inside the area (a vertical overlap of more than nothing). This is the phone's notion: an
`IntersectionObserver` with threshold 0 and no root margin, which counts any intersection. The one difference: the
observer also counts a box that only touches an edge (zero pixels shown); this test does not. No fraction is made up.
A box with no size (not laid out, `display: none`) and a passage covered by the next step's fold (`data-folded`) are
not shown. Only ids that are a guide section's readable passages on the reading the report names are kept (as before).

**When it is read:**
- **Each frame of the learner's own movement** (`onReadingScroll`'s frame, one per drawn frame of a scroll): every
  passage shown then. A continuous scroll is observed frame by frame, so what crosses the view is observed.
- **The screen the movement started from**: what is shown when the learner's hand starts a movement (a wheel, a touch,
  a scroll key, a mouse press on the pane) is kept, before the movement counts as reading, and observed with the
  movement's first frame (`startViewRef`; dropped after 1.2 s without a scroll, and by every placement; never taken
  while a placement settles). Without it, a step that lands in one frame (Page Down, End, a scripted scroll) would
  have left the first screen of a reading before its scroll is heard. After a restore or a jump this is the place it
  landed, once the learner moves (rule 3: what is shown counts from their own movement on).
- The marker's own rule is kept beside it (the marker's passage and the one it leaves behind), so nothing observed
  before is observed less.

A PDF with boxes uses the same test on its boxes, which the pane draws only for pages near the view (1,200 px ahead):
a box on a page not drawn at the frame is not observed.

### Page-only PDF (passages know only their page)

Each laid-out page `[data-pdf-page]` that overlaps the area (same test) has a shown part `[from, to]` of its height.
Its passages share the page in order, one `1/n` share each (as `spanOnPage` reads them), and passage `i` is shown when
its share overlaps the shown part: `i/n < to && (i+1)/n > from`. A page with no passage of its own (a figure page) shows
none. Same moments as the text view. The existing 85 %-through rule stays beside it. A page counts by its laid-out place whether or not its canvas has been painted
yet (pages are painted 1,200 px ahead of the view, so a page reached by ordinary scrolling is painted).

### Video and transcript (playback)

The viewport rule is **off** while a video is shown: a video is read by playback, not by what its transcript list or
the page around the player shows. What changed: when playback advances from one cue to the next (playing, not
placing, settled), the cue it moved on from is observed too. Before, the cue a seek, a resume or a pause left playback
at was never observed, though playback played it to its end. What did not: a seek, a cue change while paused, and
settling observe nothing; each cue playback arrives at while moving is observed as before.

### The phone

It already observes what is on screen (an `IntersectionObserver` with no root) once the learner has moved the page,
for the rest of the visit, so it had not the desktop's gap. One narrower gap, fixed the same way: a delivery holding a
passage's coming on screen and its leaving (a fast fling on a busy page) lost that passage, because only what stayed on
screen after the delivery was read. Now a passage reported intersecting during the learner's movement is read at once.

## What each gesture can and cannot observe (desktop)

| Gesture | Observes | Cannot observe |
|---|---|---|
| Wheel, trackpad, touch | the screen it started from and every frame it draws: all passages that crossed the view | nothing it displayed |
| Arrow keys, Space, Page Up/Down, a click in the scrollbar's track | the screen it started from and each screen it lands on (a page step is less than a screen, so a run of them leaves no gap), and any frames between when the step is smoothed | nothing it displayed |
| Home, End | the screen it started from and the screen it lands on, and any frames the browser draws between if it smooths the jump | the passages between, when the jump lands in one frame: never displayed. End still reaches the last passage, so the section's end is recorded |
| Dragging the scrollbar thumb | each frame drawn as it moves, and the starting screen (its mouse press) | passages a fast drag skips between two drawn frames |
| Opening, a restore, a search hit, a Contents or margin jump, a seek, a placement, the page settling | nothing (until the learner moves: then the screen there counts) | everything, by design |
| A page that cannot scroll (a whole book shorter than the window) | nothing: no scroll is heard (as before) | the whole book |
| "Done with this section", a quick check's completion | the completion alone (as before) | no passage |

The geometry and the frames are the browser's: the record holds only what a frame actually laid out in the view.

## What did not change

The wire shape (`seenSpanIds`, `reachedEnd`), the 1.5 s debounce and three retries, "sent until acknowledged and
never after" (an answered report acknowledges every id it carried); the count fields and how the count is computed
(the marker's position; the walk's test still reports 97 for its last stop); what finishes a section; qualification;
Today; the backend.

**A long report is not dropped anywhere on the path** (read, and the desktop tested): the desktop sends every
unacknowledged id of a section in one call with no cap (`sendSeenCounts`); the Tauri shell writes one JSON line to the
sidecar, which reads its standard input line by line with no length limit, and reads replies with an unbounded line
read; `ReaderMarkSectionProgressInput.seen_span_ids` has no length bound (step 2's revision removed it); `check_report`
keeps the section's ids in reading order; the store appends them with one `executemany`. The phone host's 256 KB body
limit bounds a phone report (some ten thousand ids).

**A section's end** still means its last readable passage was shown during the learner's own movement. With the view
rule, the last passage of a short section, and the last passage of the book's last section, are observed once they
are shown by the learner's own scrolling, though they never reach the marker 70 % down (step 2's open item).

## Tests, with fail-first evidence

Desktop, `screens/reader/seenViewport.test.tsx` (new; the hook on fake RPCs with a faked page: a 600 px reading area
and passages or pages at fixed places in the scrolled content; each frame of a movement is drawn and rendered on its
own, as in the browser). Against main's hook (with `passagesInView` stubbed to
return nothing so the file imports; main's hook never called it): **12 failed of 12**.

| Test | On main |
|---|---|
| a screenful-at-a-time read of a long section observes every passage that was on screen at each stop: the read range, whole (135 passages, nine screenful stops) | 9 ids, one per stop (`w16`, `w26`, … : the walk's shape), not `w0`–`w99` |
| a single continuous scroll observes every passage that crossed the view, the first screen included | 50 ids, `w7`–`w56`: the passages that crossed the marker, none above or below it |
| Page Down observes each screen it shows, and the one it started from | `w15`, `w24`, `w33` |
| the End key observes the screen it left and the screen it lands on: the passages in between were never displayed | `["w131"]`, no end |
| a restore observes nothing, nor the page settling after it; the learner's own movement then observes the view | `w62`, `w63` |
| a Contents jump observes nothing where it lands, not even with a hand on the page while it settles; moving on after it does | `["w7"]` before the jump |
| a short section's last passage and the book's last passage are observed once shown, and each end is reported | no end for the short section; the last section's end never |
| a long first report goes whole, is sent again whole after a failed save, and once acknowledged never again | 9 ids |
| a folded passage (covered while the learner tries the next step) is not shown, so not observed | `["w7"]` |
| a page-only PDF observes the passages whose share of a page was shown during the learner's movement | `p0c`, `p1a` |
| a video observes the cues played: the one a seek started from once playback moves on, never a seek's or a pause's | `c2`, `c3` without `c1` |
| passagesInView: a passage is shown when part of it lies inside the reading area; on a page-only PDF, its share of the page | (the stub) |

The step-2 tests (`screens/reader/seenPassages.test.tsx`, 8) pass unchanged: they drive the marker with no page laid
out, so the view adds nothing and they still prove that a restore and a jump invent no passage.

Phone, `src/read/seenPassages.test.tsx`: one case added, **1 failed, 2 passed** against main's Reader:
`a passage that came on screen and left in one delivery, during the learner's own movement, was shown and is read`
(main sent `b0`, `b1` without `b2`).

No existing assertion changed.

## What was run

Every Python run through the scratch wrapper (empty home, config and Codex dirs), each pytest run `-n 1` in a 3 GB
memory scope, one at a time; the frontend suites with four workers.

| Command | Result |
|---|---|
| Desktop `npm run typecheck`; `vitest run` (whole suite, 4 workers); `npm run frontend:build` | clean; 322 files, 3,411 tests passed; built |
| Phone `npm run typecheck`; `vitest run` (whole suite, 4 workers); `npm run build` | clean; 43 files, 441 tests passed; built |
| `tests/test_reader_seen_passages.py`, `tests/test_part_read_first_set.py`, `tests/test_mobile_allowlist.py`, and `tests/test_rw5c_block_policy.py` (the one file `scripts/affected_tests.py` lists for the changed files) | 402 passed |
| `test_identity_pins`, `test_structure_ratchets`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches`, `test_sqlite_file_copies` | 392 passed |
| `tests/test_test_layout.py` alone | 3 passed |
| `tests/test_architecture.py` alone | 18 passed |
| `ruff check` | All checks passed |
| `lint-imports --no-cache` | 45 kept, 0 broken |
| `scripts/check_gate_partition.py` | collected 32507: landing 32441 + arc_close 66 |
| `desktop_validate.py` | only the two changed modules' notes and `_generated.md` stale (the landing regenerates); no count moved |

## What the re-run of the live walk must show

1. **Half the chapter, a screenful at a time** (wheel or Page Down, the learner's own): `reader_seen_spans` for the
   chapter's reading holds every passage from the first one to the bottom of the last screen, origin `desktop`,
   contiguous: not one per stop. The identities now run a little ahead of the count (the count stops at the marker,
   70 % down the last screen; the identities reach its bottom edge).
2. **The topics whose cited passages all lie in that range qualify without further reading**: their first set is
   claimed on the acknowledged report (step 4), and Today stops saying "read a little further" for them. Topics citing
   a passage below the last screen do not.
3. Reopening the book (a restore) and a Contents jump add no row until the learner scrolls; then the screen there and
   what they scroll through.
4. The End key from the top: the first screen and the last are recorded, nothing between, and the section's end
   (`reader_section_ends`). The bottom of the book's last section, and a short section scrolled past: their ends are
   recorded.
5. A video: playback from a seek records the cue it started at once it moves on; a seek and a pause record nothing.
6. The sidecar log has no "seen passages left out of a progress report" warning.

## What was not verified

- No browser, desktop window or phone was run (the rules). The geometry is faked; how often WebKitGTK draws a frame
  during a scrollbar drag or a smoothed Home/End, whether a mouse press on the pane's own scrollbar reaches the pane
  (`onMouseDown`), and real phone deliveries are untested.
- The reading area is the pane's whole box: a passage under a sticky bar at its edge (the side-by-side header, the
  original PDF's section-break offer held at the foot) counts as shown.
- Performance: each frame of the learner's movement reads every passage box once more (the marker already reads them
  all once per frame). Not measured on a long book.
- A long list was not sent through the real sidecar in a test (no backend change; the path was read, above).
