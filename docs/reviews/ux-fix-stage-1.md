# UX fix stage 1: broken controls

Stage 1 of the UX journey audit's fix stages (`ux-journey-audit.md` §10, row 1): ledger rows UX-3, UX-4, UX-5, UX-6, UX-7 and UX-9 (`refactor-bug-ledger.md`). Branch `ux/stage1-broken-controls`, from main `e6314fc0df`, one commit per defect. Judged against `ux-journey-audit-criteria.md`.

| Row | Commit | Kind |
|---|---|---|
| UX-3 | `cccf324884` | desktop frontend |
| UX-4 | `6e20e1695d` | desktop frontend |
| UX-5 | `0dddbb03bd` | desktop frontend |
| UX-6 | `c363f23369` | desktop frontend |
| UX-7 | `375e076370` | sidecar (one function) + desktop frontend |
| UX-9 | `9f2d16b544` | phone frontend |

## UX-3: the Ask panel's send control, and a figure that outlives the panel

**What the learner saw** (seasoned-1 #74-81, `seasoned-1-0079-ask-panel-only-show-me.png`). On feedback, with figures on, the Ask panel's only button was "show me ▸". The learner typed a question about the grade, pressed it, and got "building an interactive version". A text question goes only on Enter, and nothing says so. The figure polled after the panel closed, and its outcome was never shown.

**Cause.** `AskOverlay.tsx`: the panel's box (`textarea`, Codex review F11) sends on ↵ and shows a figure on alt+↵. The cost line under it holds only the figure button (`PANEL_FIGURE_COPY.send`). `askFigures.tsx` `usePanelFigures` kept the figure lines in `useState` inside the panel. The panel unmounts when it closes (`App.tsx` `setAskTarget(null)`, `PracticeScreen.closeDockedAsk`), so a figure still building was lost with it.

**What they see now.**
- On every panel host (practice, feedback, the workbench's inline panel; figures on or off) there is a visible **"ask ↵"**, before "show me ▸". Its accessible name is "ask: send your question". It is a real button, so it is reachable by keyboard, and it is disabled while the box is empty or a question is pending. ↵ still asks and alt+↵ still shows.
- The figure lines, the take-step token and the converted flag are now kept per attempt, outside the panel: a module store keyed by the attempt's host reference (`askFigures.tsx`). Opening Ask again on the same attempt shows the figure, its failure or withheld line, or that it is still building. Another attempt's panel does not show it. The building line now reads **"◐ building an interactive version · keep working · it stays here in Ask"**.

**Tests** (`apps/learnloop-tauri/src/components/askFigures.test.tsx`):
- `UX-3: a visible ask ↵ control beside show me ▸ sends the words as a question`
- `UX-3: the ask ↵ control is there with figures off too`
- `UX-3: a figure asked for before the panel closed shows as still building, then built, when it opens again`
- `UX-3: a figure that finished while the panel was closed is there when it opens again`

**Fail-first.** All four failed before the fix. The first two failed with `Unable to find an accessible element with the role "button" and name "ask: send your question"`. The other two failed with `Unable to find an element by: [data-testid="ask-figure-line"]` on the reopened panel.

## UX-4: "Keep going" with nothing to add

**What the learner saw** (student-1 #44, retainer-1 #63). On "Nothing planned for today.", Keep going ↵ redrew the same Today and said nothing.

**Cause.** `TodayPlace.tsx` `keepGoing()` ignored what `plan_keep_going` returned. The sidecar already says it. When the extension plans nothing, `engine.build_plan` returns the empty `keep_going` plan, which is not open, and further taps return that same plan (review F10). So the view's plan stays `status !== "open"`. **No sidecar change was needed.**

**What they see now.** In place, under the buttons, a status line (`role="status"`, dim, never red): **"Nothing more to add today. Reading on, or adding a book, gives LearnLoop more to plan."** It shows in both places Keep going appears: the done plan, and an open plan with no rows. It clears on the next Keep going or Something new, and goes when Today is left. The line does not try to say *why* nothing was planned. That is stage 3 (P1).

**Tests** (`apps/learnloop-tauri/src/screens/today/TodayPlace.test.tsx`, "the states (§7.1)"):
- `UX-4: Keep going with nothing to add says so, in place, and what would give LearnLoop more`
- `UX-4: Keep going that adds a block says nothing extra`

**Fail-first.** The first failed with `Unable to find an element by: [data-testid="today-keep-going-nothing"]`. The second is the control: it passed before and after.

## UX-5: a past exam opened in the Reader

**What the learner saw** (student-1 #28-39, `student-1-0045-empty-today-red-toasts.png`). After adding a file as "This is a past exam or problem set (no reading questions)", the app switched to the Reader. A red error stayed on screen until dismissed: "Source 'src_01M7…' was ingested with the reader off (per-source setting)."

**Cause.** `add_source.py` registers a problem set with `reader_enabled=False` (line 251). It still comes back as the add's `opened` item, and `App.tsx` `openAddedItem` called `openBook` on it regardless. The Reader refused the source, and the refusal reached the error channel.

**What they see now.**
- `useAddSource` hands a problem-set add to a new `onKept`, never to `onOpened`.
- `openAddedItem` also keeps any added source whose library card has the reader off (`addedItemDestination`). This covers re-adding an existing past exam.
- When a source is kept, the app goes to the Library, and a neutral notice says: **"“18.06 Linear Algebra, Exam 1” is in your Library as a past exam. It doesn't open in the Reader, and LearnLoop doesn't write questions from it."**
- The card's details ▸ now say: **"A past exam or problem set, kept in your Library. It doesn't open in the Reader, and LearnLoop doesn't write questions from it."** The card's "for practice only" label is unchanged.
- The words are honest about use. The auto-build skips such a source (`add_source.py:1550`), and Reader search leaves it out. Making real use of a stored exam is F8 / stage 5.

**Tests:**
- `apps/learnloop-tauri/src/components/AddSource.test.tsx`, "UX-5: a past exam or problem set is kept in the Library, never opened in the Reader":
  - `the hook does not open it, and hands it over as kept`
  - `an added item whose library card has the reader off is kept too; the rest open as before`
  - `says where it went and what it does, with no id and no jargon`
- `apps/learnloop-tauri/src/components/BookCard.test.tsx` (new):
  - `UX-5: a past exam's details say where it is and what it does; it offers no Open`
  - `a book that opens in the Reader has no such line`
- The App wiring (+ Add → More options → past exam → Library and the notice) is exercised by `App.shell.test.tsx` `holds a notice while a book is open in the Reader and delivers it at the destination` (see UX-6).

**Fail-first.** The four UX-5 tests failed against behaviour-preserving stubs (`addedItemDestination` returning the old answer, an unrendered line):
- `expected "spy" to not be called at all, but actually been called 1 times` (onOpened)
- `expected 'reader' to be 'kept'`
- `expected '' to be '“18.06 Linear Algebra, Exam 1” is in …'`
- `Unable to find an element with the text: A past exam or problem set, kept in your Library…`

## UX-6: empty states sent as errors

**What the learner saw** (beginner-1 #80-120, student-1 #42 on, retainer-1 #49-61). "Nothing for this goal is ready to practise yet." stayed as a red error over every screen. "Nothing here to ask about: …" came back on Today after the learner had asked in the Reader.

**Cause, and one correction to the brief.**
- "Nothing for this goal is ready to practise yet." went through `onError` (`TodayPlace.tsx` `practiseGoal`). In the simple shell `onError` is the red error, which never expires.
- "Nothing here to ask about: open a question, feedback or a note first." was **not** in the error channel. It was already a neutral notice (`App.tsx`, the palette's "Ask the tutor about this", `notify`), and `retainer-1-0061` shows it neutral, not red. Its defect was its lifetime. Notices are held while the Reader has a book open and delivered at the next destination (`notices.ts`, Reader doc S11). The learner raised it on Today (#49) and went to the Reader within seconds (#51). It was held there, and came back on Today at #61, after they had asked in the Reader.

**What they see now.**
- Practise for this goal with nothing ready shows a status line under the goal card, in place and never red: **"Nothing for this goal is ready to practise yet."** It goes when Today is left or on the next press. A failed queue read is now reported once, by `run`'s own error, instead of also showing this line.
- "Nothing here to ask about: …" (same words) is a **place notice**: `NoticeCondition` gains `"place"`, and `placeNotice()` builds one. It is resolved, held or shown, as soon as the tab changes (an effect on `tab` in `App.tsx`). The classic shell is unchanged.

**Tests:**
- `apps/learnloop-tauri/src/screens/today/TodayPlace.test.tsx`: `UX-6: Practise for this goal with nothing ready says so on the card, as a notice, never an error`
- `apps/learnloop-tauri/src/app/notices.shell.test.ts`: `UX-6: drops a notice about this place once the learner moves to another, held or shown`
- `apps/learnloop-tauri/src/app/App.shell.test.tsx`: `UX-6: 'Nothing here to ask about' is said where it was asked, as a notice, and is gone once the learner moves on`

**Fail-first.** All three failed:
- `Unable to find an element by: [data-testid="goal-nothing-ready"]`
- `expected { kind: 'notice', text: 'x' } to match object { kind: 'notice', resolvedBy: 'place' }`
- The App test failed when it found the notice back on Today: `expected <span class="shell-notice-text"></span> to be null`

**Two existing tests changed, on purpose.** Both used this notice as their example of a notice that survives a tab change, which is the behaviour UX-6 removes:
- `App.shell.test.tsx` `holds a notice while a book is open in the Reader and delivers it at the destination` now raises UX-5's past-exam notice through the real + Add (the api mock gains `addSource`). S11's hold-and-deliver is still tested end to end.
- `App.fixRound2.test.tsx`'s Settings-queue helper raises the notice on Today without leaving it. Each test's own subject is unchanged.

### Other empty states found in the error channel (UX-6 sweep)

The sweep covered every literal sent to `onError`, `reportError`, `onToast`, `setError` and `setToast`, plus constant and thrown messages, in `apps/learnloop-tauri/src` and `apps/learnloop-mobile/src`. The working list is not tracked.

Same pattern, left as is (classic shell only: there `onError` and `notify` are the same toast, so changing the channel changes nothing the learner sees):
- `screens/TodayScreen.tsx:646` "No at-risk goal practice item is scheduled yet."
- `screens/TodayScreen.tsx:842` "Nothing to read yet — import a source first."
- `screens/TodayScreen.tsx:852` "No learning objects to diagnose yet." (also jargon: "learning objects")

Not empty states but the same shape: an explanation or refusal sent as a red, sticky error in the simple shell. Listed, not changed:
- `screens/PracticeScreen.tsx:1196` "No hints on this one: it's a check on your own." This is the closest to the pattern and the first candidate for a notice.
- `screens/PracticeScreen.tsx:1028`, `:1032` "ask-tutor is disabled during a teach-back conversation." and "… during a diagnostic check — use “…” instead." (also jargon: "ask-tutor")
- `screens/PracticeScreen.tsx:1208` "hints are disabled during a diagnostic check — answer with what you know, or stop diagnosing."
- `screens/FeedbackScreen.tsx:2316` "Cannot add note: this item has no associated subject."
- `screens/reader/useReaderInquiry.ts:1018` "That book's passage can't be kept from here; open the book to keep it."
- `screens/reader/useReaderWorkbench.ts:481` "This problem was started on an earlier reading of this book, so it can't be reopened on this one."

The phone: none. Its one literal in a message channel (`App.tsx:460`) is a real conflict, not an empty state. Empty states the sidecar raises as errors (an RPC that refuses with a message when there is nothing to do) cannot be found by this sweep. They need a walk.

## UX-7: "add it" with no subject yet

**What the learner saw** (beginner-1 #54). The library had no subject: no book's questions had been built. Pressing "add it" on "Machine learning fundamentals? not in your library yet" did nothing. The bridge log shows `curriculum_scope_decide` refused with `no_subject`.

**Cause.**
- `deliverables.decide_unmatched` refuses `no_subject` when no `subject_id` is given and `_subject_for` infers none.
- `DeliverableScopePanel` answers that refusal by setting `askSubject`. Its subject picker renders only when `subjects.length > 0`, so nothing changed on screen.
- No RPC creates a subject. Subjects are made only by ingest's `ensure_subject`, when a book's questions are planned. So no frontend-only fix exists.

**Chosen fix: the app makes the first subject** (no "name a subject" box). This is the smallest change and asks the learner for nothing.
- In `decide_unmatched`, when no subject is given, none is inferred, and the vault has **no subject at all**, a new `_first_subject` makes one with `add_subject`, under the vault mutation lock the function already holds.
- The subject is named after the topic being added (the resolver's `proposed_title`, e.g. "Machine Learning"), not after the goal. A goal made this way is titled with the learner's whole sentence, cut at 120 characters ("I want to understand how machine learning works. Someone told me…"), which reads badly as a subject name.
- With subjects to choose from and none inferred, the learner still chooses with the picker (Codex re-review F16, unchanged).
- No schema, config key, algorithm tag or prompt change. Nothing changes in what is sent to a model.

**Frontend.** If the refusal still comes with nothing to pick, the panel says so in place instead of nothing: **"Couldn't add this topic yet: your library has nothing to file it under. Add a book, then try again."** The panel's notice line now has `role="status"`.

**Tests:**
- Python: `tests/test_deliverable_scope.py::test_ux7_add_it_in_a_library_with_no_subject_yet_files_the_topic_under_a_first_subject`. It uses a fresh `init_vault` with no subject, a deliverable, the resolver fake with one unmatched phrase, and *add it*.
- Vitest: `apps/learnloop-tauri/src/screens/reader/DeliverableScope.subject.test.tsx` (new):
  - `UX-7: with no subject yet, add it is live and sends the topic for the server to file`
  - `UX-7: a no-subject refusal with no subject to pick says so in place, never nothing`
  - `with subjects to pick from, the refusal opens the picker as before (Codex re-review F16)`

**Fail-first.**
- The Python test failed with `DeliverableError: Choose the subject this new topic belongs to.` (`deliverables.py:1339`).
- The second vitest failed with `Unable to find an accessible element with the role "status"`.
- The first and third vitest tests are controls and passed before and after. The first passes because the frontend never disabled the button in this state: the dead end was the server's refusal followed by nothing on screen.

## UX-9: phone capture's delivery line

**What the learner saw** (phone-2 #31-48, `phone-2-0031-waiting-to-send.png`). After Save, the screen said "Saved." and "1 waiting to send.", though the desktop had already answered 201. Later the line went away with no word, and no screen ever confirmed delivery.

**Cause.** `CaptureScreen.tsx` `save()` started the app's flush (`App.flush`, not awaited) and read the outbox at once, while that send was still in flight. It never read the outbox again, so the count it showed was stale.

**What they see now.**
- `onSaved` is the app's `flushNow` (a promise). The screen reads the outbox again when the flush settles, and whenever the app's own flush changes the waiting count (`outboxWaiting`: on open, on focus, every minute).
- The status line (`role="status"`) says what became of the last capture:
  - **"Saved. Sending to your desktop…"** while its first send runs.
  - **"Sent to your desktop."** once the desktop took it. It stays until the next capture, including while the next one is typed.
  - **"Saved on this phone. It goes to your desktop when it's in reach."** while it waits.
- "N waiting to send." now reflects the outbox after each send. A refused capture still shows its banner with Dismiss, as before.

**Tests** (`apps/learnloop-mobile/src/capture/Capture.test.tsx`):
- `UX-9: a capture the desktop accepts says it was sent, and nothing is left waiting`
- `UX-9: while the desktop is away it says the capture waits on the phone; when it wakes, that it was sent`

The existing `a capture is saved while the desktop is asleep and sent when it wakes` now expects the waiting line instead of "Saved.".

**Fail-first.** Both failed: `Unable to find an element with the text: Sent to your desktop.` and `Unable to find an element with the text: Saved on this phone. It goes to your desktop when it's in reach.`

## Sidecar change

Only UX-7: `src/learnloop/source_retrieval/deliverables.py`, `decide_unmatched` and the new `_first_subject`, with its test in `tests/test_deliverable_scope.py`. UX-4 needed no sidecar field.

## What was run

Every command ran through the scratch wrapper (`env -i`, isolated HOME, CODEX_HOME and config dir) inside a `systemd-run --user --scope` with MemoryMax 5G for node and 3G for Python. Python ran with `-n 1` on explicit files only.

| Command | Result |
|---|---|
| `npm ci` (desktop, phone) | exit 0, exit 0 |
| `npm run typecheck` (desktop) | exit 0 |
| `npx vitest run --maxWorkers=4` (desktop, whole suite) | 288 files, 2895 tests passed |
| `npm run frontend:build` (desktop) | exit 0 (the existing chunk-size warning only) |
| `npm run typecheck` (phone) | exit 0 |
| `npx vitest run --maxWorkers=4` (phone, whole suite) | 31 files, 356 tests passed |
| `uv sync --extra dev --extra mobile --extra tui`; `uv pip install --offline pypdfium2==5.14.0` | exit 0 |
| `pytest -n 1 tests/test_deliverable_codex_review.py tests/test_deliverable_scope.py tests/test_mobile_allowlist.py tests/test_deliverable_rpcs.py tests/test_curriculum_c0b_landing.py tests/test_deliverable_path.py` | 415 passed |
| `pytest -n 1 tests/test_identity_pins.py tests/test_cli_help_snapshot.py` | 368 passed |
| `ruff check` | All checks passed |
| `lint-imports --no-cache` | 43 kept, 0 broken |

## What a re-walk should look at

- **UX-3, seasoned-1 #74-81 and #87.** On feedback, with figures on: "ask ↵" is visible beside "show me ▸" and sends the question as a question. A figure asked for, then the panel closed with esc and reopened with ?, shows still building or the figure. Also check the docked panel's layout at the walk's width: the cost line now starts with "ask ↵".
- **UX-4, student-1 #44 and retainer-1 #63.** Keep going on "Nothing planned for today." shows the new line under the buttons.
- **UX-5, student-1 #28-39.** Add with "This is a past exam or problem set": the app lands on the Library (not the Reader), the notice names the exam, there is no red error, and the card's details carry the line.
- **UX-6, beginner-1 #80-120, student-1 #42 and retainer-1 #49-61.** Practise for this goal with nothing ready shows the dim line under the goal card. Nothing red appears. The palette's "Ask the tutor about this" on Today shows the neutral notice, and it does not come back after the Reader.
- **UX-7, beginner-1 #54.** "add it" on "Machine learning fundamentals?" turns into "added as a new topic", and the Library's subject (where shown) is named after that topic.
- **UX-9, phone-2 #31-48.** After Save: "Saved. Sending to your desktop…", then "Sent to your desktop.", and no stale "1 waiting to send.".

## Not verified here

- Nothing was walked or launched: no app, browser or dev server. Rendering, layout and focus are verified only in jsdom.
- The whole Python suite was not run, only the files above. The landing gate covers the rest.
- UX-7's first subject in a real vault: how it later sits beside the subject ingest makes from the book's title. The book will usually get its own subject when its questions are planned, so the library may then hold two.
- UX-3's figure store is in memory for the run of the app. A restart forgets a figure line (the figure itself is on the attempt's record server-side; how a reopened attempt shows it after a restart was not checked). The hint chooser's figure lines now outlive the HintPanel too, under their own key.
- UX-9 on a real iPhone: the timing of focus and the minute's flush against the screen's own read.
