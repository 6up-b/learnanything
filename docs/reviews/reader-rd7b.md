# Reader workbench v2, RD7b: inline checks and veils (frontend)

Branch `reader/rd7b-inline-checks-ui`, cut from RD7a's backend tip (`b00fbdfc10`) with `origin/main` merged. Spec
§12.6 as the owner's decisions of 2026-11-23 corrected it; RD7a's record is `reader-rd7a.md`, its algorithm record
`algorithm-mvp-0.69.md`. No kill switch, no model call, no prompt change.

## 1. What was built

**The pieces** (`apps/learnloop-tauri/src/screens/desks/checks/`):
- `model.ts`: the pure rules. Where each server veil ref lands in the page (`veilSelector`: a window's body, never its
  head; a passage, a figure or a margin note inside its window; the companion's body; an overview card; a search row).
  What is sent as visible (`visibleNow`): every window on every desk, by kind. For a source or video window it sends
  every passage, margin note and figure it has rendered, not only those scrolled into view, so scrolling shows nothing
  the server has not judged. For any other window it sends the pad blocks it shows. It also sends the companion's
  state and its exchanges, and the overview's cards. Also every word the cards say (§3).
- `controller.ts`: `CheckDesk`, the store (an external store, as `VideoDesk` and `LessonDesk`). It reads the due checks
  of each reading on the desk (`checks.due_for`), keeps one administration, and holds the server's refusals in plain
  words. It sends `check.protect_more` only when the view changed, records an opened veil at once (`check.expose`),
  mints one submission id per administration (a retry is the same submission), and handles not now, close, and
  restart (`check.open_inline`, once).
- `CheckCard.tsx`: the closed marker, the open card at the host passage (the goal lens's callout, opened), the card
  centred near the top, and `CheckLenses`, the lens composed over the goal and follow lenses that puts the marker or the
  card before the host passage.
- `VeilLayer.tsx`: marks what the veils cover and keeps it marked through re-renders (a mutation observer re-marks an
  element whose class a render rewrote), places a pill on each veil that shows, and asks "show it anyway?".
- `styles/checks.css`: the mockup's veil, callout and card values on the desks' tokens.

**In the shell** (`DeskShell.tsx`):
- The store is created; after a restart the open administration comes back with its veils.
- The check lens is composed over the existing lenses; the card is inline when its host reading is on this desk and
  not paused, otherwise centred near the top.
- `check now` sends what is visible and the practice session; search closes first.
- `check.protect_more` runs on every change in view while a check is open: windows, desks, overview, companion,
  readings' status, and any DOM change under a veil, throttled to a frame. A window the server has not judged yet,
  whether new or showing another reading, is veiled whole at once and cannot be opened until its answer arrives.
- The app adopts the session the answer is recorded on (`reader.workbench.onPracticeSession`).

**Today's side**: `IntentCheckDto.beingAnsweredIn`; the practice screen's banner carries `data-being-answered` when
the server says the check is being answered in the Reader (the banner text is the server's).

**Backend changes on this branch**:
- RD7-2 (rd7b-only): `check.begin_inline` takes the session as a workbench submit does. That is the app's open one,
  else the most recent open one, else a new one. It returns it on the card, and refuses before starting a session when
  the check cannot open.
- Three commits made for the RD7a landing: `f06f50395c`, `413cfa8bd2`, `d67ffccb66` (§5).

## 2. The verbs while a check is open, one call each

A verb that would reveal veiled material or send it to a model either goes through the same honest prompt or waits
with the reason. The reason is always "after your check · it is open on this desk".

| Verb or surface | Call | Why |
|---|---|---|
| The source menu's Ask, Find, Compare, Show me, Make it practice, Teach me, What this knows, Open beside (`CHECK_HELD_VERBS`) | Disabled with the reason; reached by key, a toast and nothing done | Each sends the selection to a model or opens more material; the selection may be what a veil covers |
| Carry, Append, Note in margin, moving windows | Allowed | They write the learner's own words or move things; nothing is revealed or sent |
| The companion's ask | Disabled, the input says "the tutor waits · …" | Every model context would need the veils applied; waiting is simpler and honest |
| Show me (pads, menu) | Waits, toast "Show me waits · …" | A figure explains what the veils hold |
| Search (`/`, the menu's Find, a pad's search) | Closed when the check opens; refused while it is open, toast "search waits · …" | Its rows could show what the check asks. So no search row is ever on screen with a check open (the selector still covers rows) |
| A new lesson (Teach me from a passage, a pad line, the menu) | Waits, toast "a lesson waits · …"; resuming a stored lesson is allowed (its window is veiled whole) | A lesson teaches what the veils hold |
| Pen readings (ink transcription) | Wait; the line says "read it after your check · …" | A reading sends the ink to a model |
| Any veil's pill | "show it anyway?" with the cost, then `check.expose`, then the veil lifts | The owner's overlap rule; a note's veil says beforehand that it always makes the answer practice (§5) |

## 3. The words

- **Closed marker**: "◇ a check is due before this page · on your own", plus "whatever states the answer is veiled in
  place while you answer, then comes back" and the buttons "later" and "check now". It names no question, no LO, no
  provenance and no purpose. "later" folds it to a quiet line for the session.
- **Pill**: "hidden during this check · back when you answer".
- **Show it anyway** (a passage, a pad, the companion): "If it shows what the answer says, this answer counts as
  practice and the check stays due. If it doesn't, nothing changes."
- **Show it anyway** (one of the learner's notes): "This is one of your notes. LearnLoop doesn't read your notes, so it
  can't tell whether this one gives the answer away: opening it makes this answer count as practice, and the check
  stays due."
- **Card**: the question; "veiled while you answer · <groups>"; "nothing moves · only an on-your-own answer settles this
  check"; "not now", "answer ↵". After an opened veil: "you looked at <group> first · this answer counts as practice",
  or "you looked at <group> · it said nothing of the answer, so this can still settle the check".
- **The reply's reason** (`[data-check-reason]`):
  - on your own: "on your own · this settles the check";
  - primed: "what you opened showed the answer";
  - primed by a note (`primedBy: unmeasured_note`): "you opened one of your notes during this check; LearnLoop cannot
    tell whether it gave the answer away, so this one counts as practice";
  - with help: "you took help, so the check stays due";
  - seen before: "you had seen this answer before, so the check comes back later";
  - already answered: "this check was already answered in Today";
  - practice: "the check stays due".

  Every reason but on your own begins "counts as practice ·".

## 4. Departures from the mockup and the spec, and why

- **No minutes on the closed marker.** The spec's "about N min" has no estimate behind it (no item duration is served
  before the check opens). Inventing one would be a made-up constant.
- **The open card names no LO and no provenance.** The mockup's card says "A delayed cold check · due today", the LO
  and where the check came from. The spec's card lists only the question, and P3 invariant 10 withholds purpose from
  cold administration. The visual check compares boxes, colours and type only.
- **A textarea, not MathLiveEditor.** The mockup's card is a textarea (`textarea.gqa`), and the visual check measures
  it. The spec says MathLiveEditor. The answer is Markdown with TeX, as Today's open-text answers accept. Swapping the
  editor in is a contained follow-up if the owner wants it.
- **Pads are veiled whole.** The mockup veils pad blocks one by one. The owner's rule (§12.6.3, 2026-11-23) veils every
  window but a source's text whole; the window's head still says what it is.
- **Pills are real buttons in a fixed layer**, not the mockup's `::after`. A pseudo-element cannot be a button, and the
  pill is the one way through a veil. A pill shows only where its veil shows: inside the window's scroller and the
  viewport, not under the companion, the card or the goal band.
- **No readiness line** on the answered card (the mockup's `gqp`). The reply carries no readiness change; the band
  reads it on its own.
- **The goal band's "◇ N checks due today"**, and hiding purpose text on callouts, why cards and path rows while a
  check is due (§12.6.1, "what else changes"), are RD6's band and lens. They were not part of this brief and are not
  changed here.
- **The card centred near the top** is 64 px down and 560 px wide, as in the reference. Its height differs: the spec's
  group line and the rule's wording are longer than the mockup's.

## 5. Notes are never read (the RD7a landing's fence), and what opening one costs

RD7a's gate failed `test_notes_never_read`: the administration read `learner_notes` to measure an opened note. Fixed
in three backend-only commits for the RD7a landing branch:
1. `f06f50395c`: the administration reads no note's words; an opened note is recorded under `unmeasured_notes`.
2. `413cfa8bd2`: an answer after a note's veil was opened is submitted with the attempt's declared `primed` flag (the
   raw attempt row a rebuild reads; replay equality tested), with the reply's `primed_by: unmeasured_note`. The owner
   confirmed it on 2026-11-23 (opening one of your own notes during a cold check counts as practice). The alternative,
   kept as history, was that an unmeasured opening costs nothing. It is recorded in `reader-rd7a.md` §6a and `algorithm-mvp-0.69.md`.
3. `d67ffccb66`: `coldNow` is false once a note was opened.

The frontend words this before and after (§3). On this branch, RD7-1 (reading a margin note's words to measure it) is
withdrawn for the same reason.

## 6. RD9a-3 stays

RD7a's record (§6) sets the conditions for a lesson's quick question to come back into a desk window. The frontend
half now meets the first: veils on every note-bearing surface, `check.protect_more` on new content, and "show it
anyway" through `check.expose`. The second fails without a schema change. A probe is not a commitment, and the lock
would need a probe-keyed administration, while migration 270's CHECK names one surface (`reader_inline`). So lesson
probes stay on the lesson screen, and RD9a-3's interim is unchanged.

## 7. Ledger

- **RD7-1**: withdrawn (§5).
- **RD7-2**: fixed (§1).

## 8. Tests

- **vitest**, `screens/desks/checks/`:
  - `checks.test.tsx`: the pure rules, the store, veils in the page, the cards, arriving windows, restart, and notes.
  - `deskChecks.test.tsx`: DeskShell end to end: the marker with no cues; check now with what is visible; the inline
    card; pads veiled whole with their head clear; the companion waiting; answered with the veils lifted; the lock;
    search waiting; restart at the host passage; not now; the app adopting the session.
  - `gates.test.tsx`: the menu's held verbs, a held verb reached by key, and pen readings waiting.
  - `PracticeScreen.intentCheck.test.tsx`: Today's banner while a check is being answered in the Reader.
- **Fail-first**: each of the new desk, gate and Today tests failed against the sources before the change. The backend
  tests failed against the code before each fix.
- **pytest**:
  - `test_reader_rd7b_check_session.py` (RD7-2);
  - `test_reader_rd7b_cold_followup_parity.py` (the parity row, below);
  - the RD7a tests with the fence commits;
  - `test_notes_never_read`, the RD0 fences, `test_architecture`, identity pins;
  - ruff and import contracts.
- **The harness's `checks` run**:
  - on `?checks=1`: the marker; check now and what it sends; the veils' computed style; the head clear; only covered
    passages veiled; nothing moving; pills; no pill for a veil out of sight; search waiting; the companion waiting and
    veiled through `check.protect_more`; show it anyway's cost before any call; one exposure and one veil lifted; the
    answer sent once with its reason; every veil lifted; marker and card gone;
  - on `?checks=open`: the card centred near the top after a restart; the lock; not now.
- **The visual reference check's `rd7` stage**: `goal=check` (as `goal=check,rd7`), `goal=answered`, `goal=checkb`,
  `s12=check`, `s12=answered` and `pen=veil`, at both viewports. Findings:
  - the card is 23 px narrower than the reference's, because it takes the harness's book column;
  - the overlay's height differs (§4);
  - the textarea's focus border is missing in `goal=check`, where the companion holds the focus;
  - the veiled element's type is each book's own;
  - `pen=veil`'s card is inline, because our check's host is in view.

The parity row "Cold follow-ups (RW6b)" (§21.1) is in `reader-rd-retire.md` under this branch's name.

## 9. Not verified

- No owner vault was opened, and nothing ran in the packaged app (WebKitGTK); the harness is Chromium.
- The module notes for the five new TypeScript files are not generated (references are regenerated at integration);
  `desktop_validate.py`'s counts are moved.

## 10. Fix round (the RD7 adversarial review, 2026-11-24): the frontend half

Branch `reader/rd7-fix-frontend`, cut from the workbench nouns branch, with the backend half
(`reader/rd7-fix-backend`, recorded in `reader-rd7a.md` §8) merged. The backend's contract (§8.1 there) is coded
against in `checks/controller.ts`, the one place the desks call `check.*`. Ledger rows RD7-40 to RD7-59.

### 10.1 The class: what is held is everything not listed as safe

The review's blockers 4, 6, 10, 11 and 12 and major 21 were one defect: the veils looked for known attributes, so
every surface nobody listed stayed readable. Inverted in `checks/hold.ts`. While a check is open, everything on the
page is held unless it is on a short list of safe things:

- the check's card and markers, and the veils' pills;
- each window head's glyph, name and buttons. While a check is open the name says only what the window is: a book's
  or a video's name, else its kind ("Pads", "lesson"). The head's place-in-reading line and its chips are held;
- the desk tabs, the header's buttons, and the app's places;
- a toast that says why something waits (marked by the code that raises it);
- a source's own words (`data-passage-text`, on the desks only) in a passage the server has judged for this check
  and does not veil (its standing set);
- what the learner opened through "show it anyway", for as long as it shows what it showed then. A component says
  what it shows with `data-check-content`; the companion's body does. A change holds it again.

Held means:

- nothing moves;
- the text turns transparent behind a blur;
- canvases, players, frames and images are not painted;
- the element is `inert` and `aria-hidden`, with its title and accessible labels taken off and put back after;
- focus inside a newly held part moves to the answer box;
- a video pauses and will not start.

A mutation observer holds anything new before it paints, for the whole check, whether or not any veil stands. A new
window kind, tooltip, portal, panel or overlay is held by default. `WINDOW_VEIL_DECISIONS` records, for every window
kind, whether its passages can show (source and video) or the window is held whole (every other kind). A vitest
(`checks/windowKinds.test.ts`) reads the kinds from the DTO, the desks' glyphs and the shell's window switch, and fails
on a kind with no decision.

The other direction is kept and tested: the question reads, the answer box takes typing, an uncovered passage
reads, and "show it anyway" opens anything held after saying its cost.

What the desks cannot describe to the server opens by region: the shelf, the goal band, the companion, the pen layer,
or a window's other parts (`data-check-region`; the footer is quiet, with no pill). It is recorded as `check.expose`
kind `left` with `{kind: "surface", surface, window_id?}`, which the server records as an unmeasured opening. The
cost line says so before it opens.

### 10.2 Leaving the desks, and a remount

The vault's checks belong to the app (`App.tsx` makes the `CheckDesk` and passes it to the desks). No place, the
desks included, shows anything before the recovery read (`check.open_inline`) says whether a check is open. A failed
read says so and offers "try again" (fail closed; a vault below the tag counts as known, with no check). While a
check is open, every place but the desks (the old Reader, Today, the library, every tool) gives way to a plain choice
(`app/checkGate.tsx`): "back to the check", or "not now", which closes the administration (the check stays due). The
app's overlays that show study material stay closed meanwhile: review, the inspector, a lesson, Ask, open in source,
and the palette.

Routes are blocked, not recorded. The backend's `left` kind is used only for regions (§10.1).

### 10.3 Findings

| # | Severity | Call | Where |
|---|---|---|---|
| 4 | blocker | fixed (RD7-41) | a note's mark and panel and a `panel` window are held by default |
| 5 | blocker | fixed, client half (RD7-46) | §10.2 |
| 6 | blocker | fixed (RD7-42) | canvas, player and frame not painted; the player paused; the side-by-side pane held |
| 7 | blocker | fixed, client half (RD7-47) | passages judged per request; unjudged ones held; the observer stays |
| 8 | blocker | fixed, client half (RD7-48) | `standing` replaces the set; `veilsRevision`; `veils_stale` resends the same submission |
| 9 | blocker | fixed, client half (RD7-49) | `measured: false` and regions say "practice" before opening |
| 10 | blocker | fixed (RD7-43) | copies held by default; neutral head names |
| 11 | blocker | fixed (RD7-44) | the menu waits; the promoted key does nothing; the menu and its sheets close at begin |
| 12 | blocker | fixed (RD7-45) | `inert`, `aria-hidden`, labels off, focus moved |
| 17 | major | fixed, client half (RD7-50) | reserved submission reused; draft kept by token; replayed card adopted |
| 19 | major | fixed, client half (RD7-51) | "not now" disabled while submitting |
| 20 | major | fixed, client half (RD7-52) | `administration_closed` said; an unknown open administration adopted |
| 21 | major | fixed (RD7-53) | the history tab names no exchanges; an opening covers only what it showed |
| 22 | major | fixed (RD7-54) | a note's veil names the note's surface, never the passage it is anchored to |
| 23 | major | fixed, client half (RD7-55) | card worded from `eligibility`; `primedBy` worded |
| 24 | major | while open: fixed (band, miniatures held). Before "check now": stopped (RD7-56) | owner call, §10.4 |
| 26 | major | partly (RD7-57) | presentation blocks shown with Today's component; self-grade not built (§10.4) |
| 27 | major | fixed, client half (RD7-58) | retries wait; a reading checks again after its save; `check_open` said plainly |
| 28 | minor | partly (RD7-59) | video readings asked; the overlay stands in when no inline card is on the page; due-boundary refresh not built |

The rest (1-3, 13-16, 18, 25, 29) are the backend half's (`reader-rd7a.md` §8). The phone's part of #15 (its Today
screen prints the LO title above a Reader-held item) is not changed here: the desktop's Today does the same, and the
cold card in the Reader names no LO. Left with the backend half's #15 call.

### 10.4 Stopped or not built, with options

- **#24 before "check now" (RD7-56): an owner call; nothing is built for it until the owner answers.** The spec
  places the closed marker before the host passage, and `checks.due_for` names the LO, host and provenance. The
  review's no-topic reading conflicts with that. The two options:
  - **(a) Keep the spec.** The marker stays before the host passage and names nothing (no question, no LO, no
    provenance); its place is the one cue the spec accepts. Nothing changes.
  - **(b) An unlocated marker.** "◇ a check is due on this desk", with an opaque handle instead of the commitment's
    LO. The server resolves the host at begin, and while a check is due the goal band's LO and the overview's
    miniatures are withheld. This needs a `checks.due_for` change (no LO, host or provenance before begin) and a spec
    edit (§12.6.1).

  While a check is open, the band and the miniatures are held either way (§10.1).
- **#26's self-grade.** The cold presentation withholds the rubric, as it must. Self-grading after the answer needs a
  read that discloses the rubric once the answer is frozen (Today's `recordSelfGradeDisclosure` flow). The backend
  accepts `selfGrade` on submit, but nothing gives the card the criteria to grade against. Not built: a server read
  is needed first.
- **#28's due boundary.** `checks.due_for` returns only checks due now. Refreshing at the moment a check becomes due
  needs its due time beforehand. Not built.

### 10.5 Assertions changed

- **`checks.test.tsx`**:
  - the expose call carries `exposureId`, and the submit carries `veilsRevision`;
  - `applyVeils` became `Holder.apply`;
  - "lift what is no longer veiled" now opens the pad's ref (an unveiled pad body is held by default);
  - the test pages carry a safe head and `data-passage-text`, as the desks render them;
  - the "arriving window" test became per-passage judgement;
  - the note selector excludes passages.
- **`deskChecks.test.tsx`**: the companion's ask box is found by its class (its label is off while held). It is
  still disabled, and now inert too.
- **The harness's `checks` run**: with no exchanges, the companion's opening is unmeasured (the contract's
  `measured: false`). Its cost line and the reply's reason are now practice; the exposure carries its id, and the
  answer its revision.
- **Desk and App tests whose fake `api` was `{}`, or a Proxy that never answers**: they now answer
  `checkOpenInline` with no administration. The desks and the app wait for that read, failing closed.

### 10.6 Tests and checks

- **New vitest files:**
  - `checks/holdSurfaces.test.tsx`: every surface kind through DeskShell, both directions, the remount gate, the
    menu, a region's opening;
  - `checks/contract.test.tsx`: the contract;
  - `checks/windowKinds.test.ts`;
  - `app/App.checkGate.test.tsx`: the whole App with the real desks.
- **Added tests in existing files:** the anchored note and an opening re-held on change (`checks.test.tsx`), and a
  reading held after its save (`inkCache.test.ts`).
- **Fail-first:** each new test failed against the sources at the branch's start (saved copies restored after).
- **The harness:**
  - `veilsweep`, a new run: with a check open, it walks the book, video, paper, Guide and path panels and pad stack
    one by one, the companion's two tabs, the overview, the other two desks by key, search and the menu, and four
    surfaces planted live with an answer key (a portal tooltip, a labelled panel, an image, a page canvas). At each,
    no covered passage, pad line or key is in the visible text, titles, labels or fields, and no canvas, player,
    frame or image is painted. The canvas is compared pixel for pixel with the page without it. As a control, once
    answered the canvas paints and the key reads.
  - At the branch's start the run fails 15 of 20 points: the shelf shows the pad lines, the player paints, and more.
  - Now every run passes, `veilsweep` included.
- **Visual stage rd7:** 30 findings before and after (colour 4, geometry 19, type 7), the same rows.

### 10.7 Follow-ups after acceptance

- **The merges.** The workbench nouns branch, with batch 5's protection fix (per-verb `withheld_verbs`), was merged,
  then `origin/main` (G2, mvp-0.70). The vault references were regenerated afterwards. Three conflicting lines on a
  chapter's goal-lens wording took the nouns branch's copy pass.
- **The menu and a verb's own verdict compose.** While a check is open the menu does not open (§10.1). A verb reached
  any other way waits for the check first and does not ask for its verdict; once the check is answered, its own
  verdict decides, per verb (`gates.test.tsx`, "the open check and a verb's own verdict compose").
- **The layer's dialogs stay inside the viewport (RD7-60).** A dialog goes below its pill when it fits, else above
  it, else against the bottom edge; it never goes past either side, and it is placed again on a resize. The harness's
  `checks` run asserts this at 1600 × 960 and, for the lowest pill, at 1024 × 600. At the previous tip the small
  viewport's dialog fell below the viewport and the run timed out on its button.
- **For the deletion branch (the old Reader removed).** The app gate (`app/checkGate.tsx`, `App.tsx`'s
  `checkGateOf(deskChecks, onDesks)`) names no Reader route: it holds every place but the desks.
  - `onDesks` is `tab === "reader" && readerSurface === "desks"`. With the old Reader gone it becomes `tab ===
    "reader"`.
  - `backToCheck` calls `chooseReaderSurface("desks")`, which goes when the surface choice does.
  - `App.checkGate.test.tsx` clicks the desks' "old Reader" button (DeskShell's `onLeave`) for one of its leaving
    paths. Without it, the same test still covers Today by its key.
