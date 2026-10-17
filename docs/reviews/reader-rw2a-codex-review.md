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
