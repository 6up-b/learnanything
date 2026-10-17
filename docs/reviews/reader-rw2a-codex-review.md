# Reader workbench RW2a: Codex review and fixes (stage `reader-rw2a`)

Branch `reader/rw2a` (worktree `learnanything-merge4`), reviewed at
`39d859e2d` (codex job `20261017-060424-6kGQdY`). Stage record:
`docs/reviews/reader-workbench-RW2a.md`. Spec:
`docs/specs/spec_reader_workbench_v1.md` §5.1, §5.4, §5.7, §6.1, D40, G5, G10,
G32; UX `docs/specs/ux_reader_workbench_v1.md` S6, S7.

Each finding was reproduced first: a failing test written against the
reviewed code, then the fix. The fail-first runs swapped the reviewed
versions of the changed source files back in (backend: `reader/workbench.py`,
`handlers/workbench.py`, `db/stores/workbench.py`, migration 207 and the head
fixture; frontend: the nine changed modules), ran the new tests, and restored
the fix: **9 of 10** new or changed backend tests failed on the reviewed code
(the tenth only widens an allowed-table set), and **17 of 17** new or changed
vitest tests failed on it. All pass on the fix.

**Paid calls:** none ($0.00). Fakes only; no provider, no key, no vault opened.

## Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Workbench submissions lose the presented assessment contract | fixed | `88295e951` | `test_f1_a_resumed_problem_is_graded_against_the_contract_it_showed`, `test_f1_a_bound_import_snapshots_the_contract_of_the_item_it_bound` |
| F2 | High | Switching to steps erases previously used hints | fixed | `88295e951`, `2750fbd9c` | `test_f2_hints_shown_on_the_answer_box_are_carried_into_steps_and_counted`; vitest *hints shown on the answer box go into steps with the work, and come back with it*, *a resumed problem that carried hints brings them back to the answer box* |
| F3 | High | Hiding the book before the debounce bypasses assistance recording | fixed | `2750fbd9c` | vitest *F3: hiding the book within the save's debounce saves the step written with it shown first*, *F3: a failing save holds the book's change behind it* |
| F4 | High | Resuming a practice-origin session in the Reader exposes an uncounted book | fixed | `88295e951`, `2750fbd9c` | `test_f4_a_practice_problem_resumed_in_the_reader_moves_there_book_hidden_and_counts_the_book_if_shown`, `test_f4_a_reader_problem_resumed_on_the_practice_screen_keeps_the_book_it_counted`, `test_f4_resuming_an_abandoned_problem_by_its_id_reopens_it_on_the_asking_surface`; vitest *a resumed problem whose book is not shown has the source covered, whatever its origin* and the two resume tests (now one explicit resume) |
| F5 | High | Retrying an acknowledged-late save silently discards newer edits | fixed | `2750fbd9c` | vitest *F5: a write retried after its response was lost resends what it sent, and newer text saves under a new key* |
| F6 | High | A rejected save still permits submission of stale work | fixed | `2750fbd9c` | vitest *F6: a write the server refuses stays not saved, and Submit sends nothing until it is fixed* |
| F7 | High | Abandon overtakes queued saves | fixed | `2750fbd9c` | vitest *F7: Abandon waits for every queued save before setting the problem aside*, *F7: Abandon with a save still retrying sets nothing aside* |
| F8 | High | Workbench drafts bypass window-close and vault-switch protection | fixed | `2750fbd9c` | vitest *F8: a vault switch freezes the steps and saves them against their own vault before it selects the next*, *F8: a vault switch with steps that cannot be saved does not happen, and editing resumes*, *F8: closing the window waits for the steps to save before it goes* |
| F9 | High | The Reader omits required-method instructions and other stimulus blocks | fixed | `88295e951`, `2750fbd9c` | `test_f9_the_bound_problem_carries_the_items_whole_presentation`; vitest *F9: a bound problem shows the item's whole presentation* |
| F10 | Medium | A lost submit response cannot recover through Retry | fixed | `88295e951` | `test_a_retried_submit_answers_the_same_attempt` (rewritten: it asserted `already_submitted`, contradicting its name) |
| F11 | Medium | Showing the source never records the required exposure | fixed | `88295e951` | `test_f11_showing_the_book_records_an_exposure_of_the_anchored_spans` |
| F12 | Medium | The accepted "check me" Reader workflow remains unimplemented | fixed | `2750fbd9c` | vitest *check me opens in the working posture with the book hidden and submits as the pick's serve* (Reader), *check me with the workbench on opens in the Reader as the pick's serve, plan on or off* (App helper) |

Nine High findings fixed, three Medium fixed, none rejected. References
regenerated in `0b2d4eb85`.

## What changed, by finding

**F1 (the presented contract).** `workbench_sessions` gains
`assessment_contract_version_id`. The handler snapshots the contract with the
same `snapshot_for_presentation` the practice screen's serve uses (only under
a canonical-state algorithm version, as the serializer does) when a session
opens on its item or binds to one, and never replaces it: a resume keeps the
contract the problem was opened with, and a bind to another item clears a
stale one first. `submission_plan` carries it, and `workbench.submit` passes
it as `SubmitAttemptInput.assessment_contract_version_id`, so the grader and
the grading evidence use the contract the learner saw.

**F9 (the whole presentation).** A bound session's view carries
`presentation`: `item_presentation(item)` (the prompt, a required method's
instruction, a laddered stem's shared setup, an error hunt's worked solution)
with the statement and the required method the session's contract froze, the
same substitution `answered_presentation` makes for a reviewed answer. The
workbench renders it through `ItemPresentation`; before binding the verbatim
selection stays the provisional display.

**F2 (carried hints).** `workbench_sessions` gains `carried_hints`: the hints
the learner revealed on the practice screen's answer box before choosing
*Work in steps*. `workbench.open` takes `carriedHints` and keeps the highest
count seen (never taken back); the record line, the footer and the submit's
`hints_used` and attempt type all read book + carried from the session row,
so the line and the attempt cannot disagree. The practice screen sends its
count when it opens or resumes steps, keeps the revealed hints in view above
the workbench, and on *answer box instead*, Leave or Abandon takes the
session's count back into the answer box (shown and counted there). The
answer box is the only place an RW2a learner can reveal a hint, so both
directions are covered.

**F4 (the cross-surface resume).** A resume on another surface is an explicit
move, made by `open_session` (by item) and the new `resume_session`
(`workbench.open` with `sessionId`, which also reopens an abandoned session):
the session's `origin` becomes the asking surface (the store now lets a resume
change it), so the submit records the surface it is sent from. Into the
Reader it gains the Reader's anchors when it had none and opens with the book
only when no step was written yet (the entry's default, UX S7); with steps,
the book starts hidden, so work written without it stays the learner's own
until they choose to show it, which counts from then on. Out of the Reader
there is no book (`source_visible = 0`); a book once counted
(`source_shown_at`) stays counted on any surface (`book_counted`). The move is
logged on `workbench_resumed` with `moved_from`. The practice card and the
Reader's `✎`, rail and reopen lines all resume through this one call, and the
Reader covers the source whenever the session's book is not shown, whatever
its origin.

**F10 (the lost submit receipt).** `workbench.submit` on a submitted session
answers from the submission's receipt (`_cached_submission` on
`workbench:<session>`) with the session and its practice session, before the
open-session check, so Retry after a lost response lands on the same attempt
(also after a restart) and writes nothing.

**F11 (the book's exposures).** Every showing of the book records one
`source_exposure_events` row per anchored span, context `reader` (an existing
value, so no table rebuild), with the revision, source, page, locator and
section path when the extraction resolves, and entity `practice_item` (or the
`workbench_session` before binding): the initial visible opening, `set_book`
to visible, and a move into the Reader with the book shown. Hiding records
nothing.

**F3, F5, F6, F7, F8 (the write queue, `useWorkbenchSession.ts`).**
- *Frozen payloads (F5).* A write's payload is read once, when first sent, and
  frozen under its key: a retry resends exactly it. Text typed meanwhile goes
  in a later write under a new key (an edit coalesces only into an unsent
  write), and after each acknowledged step write the stored text is compared
  with the window's; a difference queues a new edit. *Saved* therefore means
  the text on screen is the text stored.
- *Refusals held (F6).* A permanent refusal keeps the step's text and marks it
  *not saved (why) — your text is still here*; `drained()` resolves false while
  any refusal stands, and it clears when a later write of that step lands or
  the step is deleted. An empty queue is no longer success by itself.
- *The book in the queue (F3).* Ctrl+Shift+B and the book line flush resting
  edits, update the window at once (the Reader covers or uncovers the source),
  and queue the visibility change behind the steps written under the old
  visibility, so a failing step write holds the change behind it.
- *Abandon (F7)* saves every pending write first and refuses, with the steps
  kept, while one is failing or refused.
- *Vault switch and close (F8).* The workbench registers with
  `registerVaultDraft`: a switch freezes editing, saves every pending write
  against the steps' own vault before the next is selected, refuses the switch
  (and resumes editing) when a write cannot land, and after a switch the
  unmount sends nothing to the new vault. It also registers with
  `useCloseWithFlush`, which now waits for every mounted screen's close save
  (the practice screen's draft and a workbench can both listen) before
  destroying the window, takes an optional failure message, and does nothing
  outside a Tauri window. On the practice screen the open workbench stays
  mounted through the switch's freeze, so it is never remounted from a stale
  session.

**F12 (check me in the Reader).** With the workbench on, *check me* keeps
`plan_learner_pick` and `readerCheckOffer` as they were, serves the item once
through `get_practice_item` exactly as the practice screen's serve did (the
plan-off proposal's delivery, the cold-check revalidation and administration),
and hands the check to the Reader (`readerWorkbenchCheck`), which opens it in
the working posture with entry `check_me` and the book hidden (the server's
default for the entry), anchored to the cue's passage. Its submit answers the
pick's scheduler candidate and plan presentation; feedback's back returns to
the problem and Next to the passage (S6). With no session open it waits for
Begin and then opens the Reader at the passage. With the workbench off it
opens on the practice screen as before.

## Data

Migration 207 is unlanded, so the two columns are added to it rather than to
a 208: `assessment_contract_version_id TEXT` and
`carried_hints INTEGER NOT NULL DEFAULT 0 CHECK (carried_hints >= 0)`; the
`origin` comment says it moves on a cross-surface resume.
`fixtures/migration_head_207` was rebuilt: a backup-API copy of the base's
`migration_head_206` (`9cdaefb9e`) with only the revised 207 applied under
`upgrade_allowance(UPGRADE_TEST_HELPER)` (applied `[207]`),
`wal_checkpoint(TRUNCATE)` `(0, 0, 0)`, `journal_mode=DELETE` (header bytes
18-19 are 1/1), `integrity_check` ok, `foreign_key_check` empty, no companion
files; its README says so. Both roles unchanged; replay and rebuild still never
read the workbench tables. No new RPC, event kind, reveal kind or table.

## The review's claims

- *"A lost response is answered from the receipt."* True now (F10); the test
  asserts it, after a restart too.
- *"Saved" means the latest text persisted.* True now (F5, F6): frozen payloads,
  the post-acknowledgement comparison, and refusals held as not saved.
- *Abandon and closing preserve pending work.* True now (F7, F8), and a vault
  switch too.
- *G5/G10 assistance mapping holds across the workflow.* The missing paths are
  covered: prior answer-box hints (F2), debounce ordering (F3), the
  cross-surface resume (F4) and the exposure rows (F11).
- *Submission preserves ordinary practice behaviour.* It now carries the
  presented contract (F1) and the existing assistance (F2), and shows the
  learner what the grader is sent (F9).

## Not changed (outside the twelve findings)

The conformance table's other rows stay as the stage record states them
(§3 decisions 4, 5, 7): the answer-confidence row (open question 3), the
*original page ↗* link, the rail's tabs folded into the header, the `✎` mark on
the original PDF, and scrolling to the last edited step on resume
(`lastEditedStepId` is sent; the screen does not scroll to it yet). Newly
returned step versions are not merged into the live *earlier versions* list
until the problem is reopened. None changes what is recorded.

## Open questions (with the default taken)

1. `carried_hints` is the answer box's own client-side count (the number its
   ordinary submit already sends as `hints_used`), now stored on the session so
   it is durable and read back by both the line and the submit. Once
   `help_assists` exists (RW2b or adaptive hints H0), should the answer box's
   hints be written there and the column folded into the server's fold?
   **Default: yes, with that table.**
2. A practice-screen problem with steps resumed in the Reader opens with the
   book hidden (its work was written without it). **Default: as built; the
   learner can show it, and it counts from then.**

## Gate

Run in the worktree with `TMPDIR` set to `fixtures-local/tmp`, at `0b2d4eb85`
(code) plus this record.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok (`uv sync` rebuilt the editable `learnloop`; `pypdfium2` 5.14.0 present) |
| `uv run lint-imports --no-cache` | **23 kept**, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto` | **12,869 passed**, 2 xfailed, 0 failed (1,217 s) at `0b2d4eb85` |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -m durability` | **106 passed**, 12,765 deselected (115 s) |
| `npm install`, `npm run typecheck` | ok, clean |
| `npm test` (vitest) | **108 files, 881 tests passed** (15 new, 2 rewritten) |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check` | not needed: nothing under `src-tauri` changed in this step |
| `db_generate_reference.py`, `db_validate_reference.py` | regenerated (327 table notes; `workbench_sessions` gains the two columns); errors [] |
| `test_desktop_rpc_contract.py`, `test_sidecar_serializer_snapshot.py`, `test_cli_help_snapshot.py`, `test_config_refactor.py`, `test_coordinated_migrations.py`, `test_architecture.py`, `test_tracked_fixture_databases.py`, `test_sqlite_file_copies.py`, `test_migrations.py`, `test_table_roles.py`, `test_mobile_allowlist.py`, `test_reader_workbench_rw2a.py` | **346 passed**; no snapshot, CLI help or RPC pin changed |

## Re-review (codex job `20261017-070302-R8NqXR`)

Codex re-reviewed `39d859e2d..reader/rw2a` at `7c92629fb`: F4, F5, F6, F7 and
F9 confirmed fixed; F1, F2, F3 and F8 reopened; two new Medium defects (F13,
F14). Each was reproduced first with a failing test, then fixed. The
fail-first runs swapped the reviewed versions of the changed source files back
in (backend: `reader/workbench.py`, `handlers/workbench.py`,
`db/stores/collection.py`, `db/stores/workbench.py`, migration 207; frontend:
`PracticeScreen.tsx`, `useWorkbenchSession.ts`, `useCloseWithFlush.ts`,
`useReaderWorkbench.ts`, `dto.ts`), ran the new tests, and restored the fix:
**4 of 4** new backend tests and **7 of 8** new vitest tests failed on the
reviewed code (the eighth, *showing the book never waits behind a refused
step*, guards the fix's own rule and passes on both). All pass on the fix.

**Paid calls:** none ($0.00). Fakes only; no provider, no key, no vault opened.

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Practice shows the item's current presentation, not the workbench's frozen one | fixed | `10b5f8cf9` | vitest *in steps the problem shows the presentation the session froze, not the item's current one* |
| F2 | High | Going back to the answer box drops a book the problem counted | fixed | `7943a9259`, `10b5f8cf9` | `test_f2_a_book_counted_in_steps_goes_to_the_answer_box_and_back_into_steps_counted`; vitest *a book counted in steps counts on the answer box and goes back into steps* |
| F3 | High | A permanently refused step lets a queued book-hide apply | fixed | `10b5f8cf9` | vitest *re-review F3: a refused step holds hiding the book, so its corrected text is saved with the book shown* (the reviewer's 20,001-character scenario), guard *re-review F3: showing the book never waits behind a refused step* |
| F4-F7, F9 | High | (confirmed fixed by the re-review) | — | — | no change |
| F8 | High | `useCloseWithFlush` destroys the window after a failed flush | fixed | `10b5f8cf9` | vitest *a save that fails keeps the window open once and says so; a second close request closes it* (hook), *re-review F8: closing with a step that cannot be saved keeps the window open once, then closes on a second request* (workbench) |
| F13 | Medium | Leaving "check me" loses its submission attribution | fixed | `7943a9259`, `10b5f8cf9` | `test_f13_a_resumed_check_still_submits_as_the_serve_it_was_opened_from`, `test_f13_a_kept_offer_that_went_stale_never_fails_the_submit`; vitest *check me puts the pick's serve on the problem, so it survives leaving and resuming*, *opening steps puts this serve's offer and plan presentation on the problem* |
| F14 | Medium | "Check me" can reopen a reused problem with the book visible | fixed | `7943a9259` | `test_f14_check_me_on_a_problem_left_with_the_book_open_opens_it_hidden_keeping_what_it_counted` |

Four High findings fixed (F1, F2, F3, F8), two Medium fixed, none rejected.
References regenerated in `f34c7186b`.

### What changed

**F1.** In steps the practice card renders the session's `presentation` (the
statement and required method the session's contract froze, review F9), and
the item's current presentation only on the answer box.

**F2.** A book counted in steps now travels both ways. Back on the answer box
(*answer box instead*, Leave, Abandon) the screen keeps a book the closing
session counted, and also counts one on the item's open problem after a
restart (`workbench.for_item` summaries carry `bookCounted`). The answer box
says so ("the book you had open while working in steps counts as one hint"),
and its submit and "I'm stuck" send `hintsUsed` = its hints + 1 (attempt type
`hinted_attempt` where allowed). Into steps again, `workbench.open` takes
`carriedBook`, which marks the session's book counted (`source_shown_at`) when
it was not counted already. A book is one hint, so carrying it into the
session that counted it never counts it twice. `carried_hints` stays the
answer box's own hint count, so the hints shown come back exactly.

**F3.** While a step's write stands refused, the queue holds a book *hide* and
every book change queued after it, and sends the step writes behind them
first. So the corrected text of a step written with the book shown is saved
while the server still has the book shown, and counts it. Showing the book is
never held: holding it would save new work as unassisted while the book is on
screen. Deleting the refused step releases the hold. `drained()` treats a
queue with only held writes as settled, and settled as not saved while the
refusal stands.

**F8.** A close save that fails now keeps the window open and tells the
learner why, adding "The window stayed open so nothing is lost. Close it again
to close anyway." Every mounted listener (the practice draft, a workbench)
reports whether its save landed, and the window goes only when all of them
did. A second close request after a hold closes the window, so a refusal the
learner cannot fix never traps them. This applies to the practice draft too,
which shares the hook: it used to close on a failed save.

**F13.** Migration 207 (still unlanded) gains `scheduler_candidate_id` and
`plan_presentation_id` on `workbench_sessions`, with no new table or role.
`workbench.open` stores the serve it names: *check me* sends the pick's offer
and plan presentation, and the practice screen sends its serve on open and
resume. A later serve of the item replaces them, and a resume that names none
(the rail, the `✎` mark) keeps them. `workbench.submit` uses the request's
serve when it sends one. Otherwise it uses the kept offer, but only while that
is still an unanswered offer of the item in the practice session the submit
runs in (`Repository.scheduler_offer_open`, the read-only form of the check
`bind_submission_offer` makes). A stale offer is dropped, never refused. The
kept plan presentation is validated where every plan presentation is, at the
attempt insert. The head fixture was rebuilt: a backup-API copy of the base's
`migration_head_206` with only the revised 207 applied, with
`wal_checkpoint(TRUNCATE)` `(0, 0, 0)`, `journal_mode=DELETE` (header bytes
18-19 are 1/1), `integrity_check` ok, `foreign_key_check` empty and no
companion files. Its README says so.

**F14.** A resume with entry `check_me` hides the book (`source_visible = 0`,
`source_hidden_at` set) on the same surface as well as across surfaces, and
records no exposure. It keeps `source_shown_at`, so a book already counted
stays counted.

### Open questions (with the default taken)

3. A failed close save holds the window once, and the second close request
   closes it anyway. **Default: as built.** An unfixable refusal (a step that
   is too long) must never trap the learner in the window.
4. A book counted on the item's *open* problem counts on its answer box. A
   book counted on an abandoned one counts only for the visit that left it.
   **Default: as built.** A problem set aside long ago does not tax today's
   answer.

### Gate (re-review)

Run in the worktree with `TMPDIR` set to `fixtures-local/tmp`, at `f34c7186b`
(code) plus this record.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok (`pypdfium2` 5.14.0) |
| `uv run lint-imports --no-cache` | **23 kept**, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto` | **12,873 passed**, 2 xfailed, 0 failed (904 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -m durability` | **106 passed**, 12,769 deselected (112 s) |
| `npm install`, `npm run typecheck` | ok, clean |
| `npm test` (vitest) | **108 files, 889 tests passed** (8 new) |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check` | not needed: nothing under `src-tauri` changed |
| `db_generate_reference.py`, `db_validate_reference.py` | regenerated (327 table notes; `workbench_sessions` gains the two serve columns); errors [] |
| `test_desktop_rpc_contract.py`, `test_sidecar_serializer_snapshot.py`, `test_cli_help_snapshot.py`, `test_config_refactor.py`, `test_coordinated_migrations.py`, `test_architecture.py`, `test_tracked_fixture_databases.py`, `test_sqlite_file_copies.py`, `test_migrations.py`, `test_table_roles.py`, `test_mobile_allowlist.py`, `test_reader_workbench_rw2a.py` | **350 passed**; no snapshot, CLI help or RPC pin changed (the template `.pyc` was cleared first) |

## Round 3 (Codex final verification, job `20261017-074609-UuHUGN`)

Codex verified `7c92629fb..reader/rw2a` at `f8bdc4b8c`. It confirmed F1, F3-F7,
F9, F13 and F14 fixed, which this round leaves alone. It reopened F2 and F8,
each with a reproduction, and found one new Medium defect, F15. The
orchestrator's scope rulings bound the fixes: the server is authoritative for
assistance (F2); Leave follows Abandon's and close's rule (F8); a serve is one
pair (F15). Nothing else changed: no conformance-table row, no redesign, no
other finding. No schema change was needed, so migration 207, the head fixture
and the DB references are as round 2 left them.

Each finding was reproduced first with a failing test, then fixed. Backend:
the four new tests were run on `f8bdc4b8c` before any source change, and
**4 of 4 failed**. Frontend: the reviewed versions of the five changed
modules (`PracticeScreen.tsx`, `ReaderScreen.tsx`, `Workbench.tsx`,
`useWorkbenchSession.ts`, `dto.ts`) were swapped in from `f8bdc4b8c`, and the
seven new vitest tests were run: **7 of 7 failed**. All pass on the fix.

**Paid calls:** none ($0.00). Fakes only; no provider, no key, no vault opened.

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F2 | High | Assistance restoration can be bypassed (a submit before the lookup answers; carried hints clamped to the current hint list) | fixed | `b986d6ce9`, `24010c8ea` | `test_final_f2_an_answer_box_submit_counts_the_book_its_open_problem_counted_whatever_the_client_sent`, `test_final_f2_carried_hints_still_count_after_the_items_authored_hints_were_removed`; vitest *final F2: Submit waits for the item's problems to be looked up, then counts the book one counted*, *final F2: a failed lookup is never read as no assistance: it says so, and a later failure keeps what was found*, *final F2: hints a problem carried still count after the item's authored hints were removed* |
| F8 | High | Leave for now unmounts unsaved steps, stripping the vault-switch and close protection (the Reader too) | fixed | `24010c8ea` | vitest *final F8: Leave with a refused step stays, says why, and keeps the vault switch and close held; a second Leave leaves and says the text was discarded*, *final F8: answer box instead waits for the steps the same way*, *final F8: in the Reader, Leave with a refused step keeps the workbench and the window's close held* |
| F15 | Medium | Replacing a serve keeps the previous plan presentation | fixed | `b986d6ce9`, `24010c8ea` | `test_final_f15_a_replacement_serve_replaces_both_identifiers_and_a_resume_naming_none_keeps_both`, `test_final_f15_a_submit_naming_a_serve_never_mixes_it_with_the_kept_one`; vitest *final F15: a submit with no serve of its own names none, so the server answers the pair the problem kept* |
| F1, F3-F7, F9, F13, F14 | High / Medium | (confirmed fixed by the final verification) | — | — | no change |

### Fail-first evidence

- Backend, on `f8bdc4b8c`: the F2 tests recorded `hints_used` 0 where 1 and
  2 were due (`assert (0 == 1)`, `assert (0 == 2)`). The F15 tests got
  candidate B with `pres_P` where the pair was (B, None), both in the stored
  session and in the `SubmitAttemptInput` the workbench submit built.
- Frontend, with the reviewed modules swapped in: the answer box sent its
  submit while `workbench.for_item` was still pending. A failed lookup showed
  nothing. Carried hints came back as 0 against an empty hint list. The first
  Leave (and "answer box instead") with a 20,001-character refused step
  left at once; in the Reader that collapsed the workbench and removed its
  close handler. The workbench submit sent `schedulerCandidateId: null` and
  `planPresentationId: null` when its surface had no serve.

### What changed

**F2: the server holds the assistance.** `held_hints(repository, item)`
(`reader/workbench.py`) is the largest `session_hints` (a book counted, plus
the answer-box hints the session carried) over the item's **open** workbench
problems. `submit_attempt_on` and `submit_dont_know_on` (`handlers/practice.py`)
fold it in through `_held_assistance`. They record the larger of it and the
client's `hints_used`, never the sum, because a client that restored the
assistance already sends it. The existing tutor-question fold and the
`max_useful_hints` cap then apply as before. When the item's problems hold
any assistance, an `independent_attempt` becomes the assisted type the answer
box picks (`stuck_attempt_type`: `hinted_attempt` where allowed). A
diagnostic probe keeps its type. The empty-stuck path folds too. Nothing
clamps the count to the hints the item shows today. A workbench submit folds
its own session, so the count is the same, not doubled.

The client no longer carries correctness, but it still shows the assistance
before Submit. The answer box's Submit (button, Ctrl+Enter, and the
empty-stuck submit) waits until `workbench.for_item` has answered for this
item. A failed first lookup is never read as "no assistance". It says
"Couldn't check this problem's earlier steps. Any help they counted still
counts when you submit." and offers "check again". A failed refresh keeps
what an earlier lookup found. The lookup is keyed by item, so one item's
problems never show on the next. Carried hints come back unclamped. When
they exceed the hints the item shows, a line says "N hints you saw earlier
on this problem count".

**F8: Leave waits like Abandon and close.** `useWorkbenchSession.leave` flushes
resting edits and waits for every write. If one is not saved, the first press
stays: `left: false`, with a note in plain words, for example "A step isn't
saved (This step is too long to save.), so you're still here. Shorten it or
delete it, or leave again to leave without it." The workbench stays mounted,
so its vault-switch registration and close handler stay in force. A second
press leaves anyway and tells the screen, through `onError`, "Left without
saving a step (…): its unsaved text was discarded." When the write is still
retrying instead of refused, the line says it may be lost. "Answer box
instead" uses the same departure. The Reader collapses only through the
workbench's Leave, so closing from the Reader gets the same protection. A
vault switch and the window's close, while the workbench is mounted with a
refused step, stay as built in round 2.

**F15: a serve is one pair.** `workbench.open` passes `_named_serve(params)`.
That is `None` when the request names neither `schedulerCandidateId` nor
`planPresentationId` (keep both), and otherwise both values, explicit nulls
included (replace both). `_serve_changes` writes both columns, or none.
`workbench.submit` follows the same rule. A request naming either identifier
answers that pair. Otherwise the submit answers the kept pair: the kept offer
while it is still open (round 2's `_kept_offer`) and the kept plan
presentation. The frontend names a serve only where a surface has one. The
practice screen always sends its serve as a pair. The Reader passes a check's
serve and nothing for a resumed problem, so that submit names none.

### Open question (with the default taken)

5. A failed `workbench.for_item` lookup lets the answer box submit, with the
   notice and "check again", instead of holding Submit indefinitely. The
   server records the assistance either way, and an unreachable lookup must
   not trap the learner. **Default: as built.**

### Gate (round 3)

Run in the worktree with `TMPDIR` set to `fixtures-local/tmp`, at `24010c8ea`
(code) plus this record.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok (`pypdfium2` 5.14.0) |
| `uv run lint-imports --no-cache` | **23 kept**, 0 broken (the practice handler reads the workbench lazily; `learnloop_sidecar` is outside the evidence-never-reads-the-workbench contract) |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto` | **12,877 passed**, 2 xfailed, 0 failed (1,093 s); 4 new |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -m durability` | **106 passed**, 12,773 deselected (114 s) |
| `npm install`, `npm run typecheck` | ok, clean |
| `npm test` (vitest) | **108 files, 896 tests passed** (7 new) |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check` | not needed: nothing under `src-tauri` changed |
| `db_generate_reference.py`, `db_validate_reference.py` | not needed: no schema change (migration 207 and `fixtures/migration_head_207` unchanged) |
