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
   raw attempt row a rebuild reads; replay equality tested), with the reply's `primed_by: unmeasured_note`. This is an
   orchestrator interim, still to be confirmed by the owner. The alternative is that an unmeasured opening costs
   nothing. It is recorded in `reader-rd7a.md` §6a and `algorithm-mvp-0.69.md`.
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
