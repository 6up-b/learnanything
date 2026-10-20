# Reader RW4b: Codex review, round 1 (stage `reader-rw4b`)

Branch `reader/rw4b`, worktree `learnanything-rw4b`, reviewed at `b318a1b41`
(codex-job `20261020-000148-AgnjzF`). Each finding was reproduced first,
with a failing test where it could be tested, and then fixed. The plan, the
gates and the RW1c hook are in `reader-workbench-RW4b.md`, whose decision 5,
open question 3 and §1.1 registry note this round amends. No migration was
needed (216 is still reserved and unused). No live or paid model call was
made, and no vault copy was opened.

## Findings

| id | severity | title | verdict | commit | test (fail before → pass after) |
|---|---|---|---|---|---|
| F1 | High | Exercise actions crash on the library page | fixed | `60384ab90` | vitest `libraryExercisesReader.test.tsx` › "on the library page both exercise actions open the exercise's book (F1)". Before the fix it threw `ReferenceError: Cannot access 'openLibraryHit' before initialization` |
| F2 | High | Restarting during import loses the learner-pick handoff | fixed | `e0cda60da` | pytest `test_library_exercises.py::test_the_learner_pick_is_owed_durably_across_a_restart_and_acknowledged_only_after_delivery`, `::test_admitting_needs_the_item_and_never_marks_another_problem`; vitest `readerWorkbenchExercise.test.tsx` › restart, "use this one" on a bound problem, failed hand-off retried, hand-off names the problem (5 vitest and 2 pytest failed before the fix) |
| F3 | Medium | Exposure can change after display without changing the independent offer | fixed | `e0cda60da` | pytest `::test_exposure_since_the_card_was_shown_is_read_again_at_the_pick`, `::test_exposure_since_the_pick_is_read_again_at_admission_and_shown`, `::test_a_fallback_pick_is_not_exposed_by_its_own_listing_and_its_request_reaches_the_import_unchanged`; vitest `Workbench.test.tsx` › "RW4b: a picked exercise seen since it was offered…" |
| F4 | Medium | Long exercises open with an incomplete problem | fixed | `e0cda60da` | pytest `::test_a_long_exercise_opens_on_its_complete_statement_not_the_cards_preview` (failed before the fix: the stem was the 12-character preview) |
| F5 | Low | StrictMode leaves fallback searches permanently pending | fixed | `2c58e48bc` | vitest `libraryExercises.test.tsx` › "under StrictMode the fallback's result lands instead of staying pending (F5)" (failed before the fix) |
| Conf. | — | Every new config key classified (spec-conformance row) | fixed | `e0cda60da` | pytest `::test_the_rw4b_switches_are_classified_in_the_parameter_registry` (failed before the fix) |

No finding was rejected.

### What changed

- **F1.** `openLibraryHit` is now defined before every early return in
  `ReaderScreen.tsx`. The library page (no book open) uses it through both
  card actions, and all its dependencies were already defined above it.
- **F2.** Admission is now durable and idempotent, with no migration:
  - **The record.** The problem's stored import request (RW2a's
    `import_request_json`) keeps the pick's record under `reader_exercise`:
    the proposal (null for the fallback), the region, the exposure reading
    and `admitted_at`. The writers are `learnloop/reader/workbench.py`
    (`exercise_pick`, `exercise_pick_due`, `admit_exercise_pick`), and the
    record is stripped before the fallback's request reaches
    `ReaderImportExerciseInput`, so the import still receives the request
    unchanged (G34).
  - **When the pick is owed.** The session view carries
    `exercisePick.due`, which is true while the import has bound the problem,
    the pick was not delivered and the problem is open. The hook hands any
    such problem to the shell, however it saw it: an open, a resume, a
    restart, or "use this one" on a problem that is already bound. The old
    per-visit map is gone.
  - **Acknowledgement.** The shell runs `pickCheckMe`, which now resolves
    whether the pick was made and served. Its hand-off (`workbench.open` with
    `admittedSessionId`) acknowledges the pick on the server only after the
    pick and its serve succeeded, and only once; the
    `workbench_exercise_admitted` event is salience only. A failed or
    refused hand-off acknowledges nothing and is tried again on the next
    sight of the problem.
- **F3.** The server now reads the exposure rule again at two points, through
  the sources service's own `independent_check_eligibility` (via
  `library_exercises.exposure_view`, intent `discriminate`):
  - **At the pick (`workbench.open`).** The server reading decides how the
    problem opens: exposed opens as `work_through`, practice beside the book;
    unexposed opens as `practice_this`, book hidden. The card's entry is only
    a request.
  - **At admission.** The new reading is stored and shown. This covers
    ordinary practice proposals, which the sources service's own
    serve-time check skips.
  - **Which candidate is read.** It is the same input the card was read
    with, so the rule's judge answers from its ledger unless something new
    was studied in between.
  - **The fallback's own listing.** The fallback's listing records its shown
    spans as exposure, so its candidates now carry a `pick`: the listing's
    own exposure-row ids. The server verifies that each id really is a
    `library_exercises` row for those spans, and those rows alone never
    count against the pick, just as a proposal's own impression does not.
  - **Failures and display.** A rule that cannot be read fails closed
    (practice beside the book). The workbench shows the reason followed by
    "practice beside the book, not a check on your own".
- **F4.** The server opens the problem on the exercise region's complete text,
  read from the validated spans (`library_exercises.full_statement`). Only
  the card keeps the `STATEMENT_CHARS` preview.
- **F5.** The mounted flag is set by the effect's setup, so StrictMode's
  setup, cleanup, setup cycle leaves it true.
- **Registry.** `library_exercises.enabled` and `fallback_enabled` are
  classified structural/operational kill switches in
  `params/parameter_registry.py`, as RW2b's fix round 1 F11 did for its
  booleans.

### Notes for the landing

- **Judge calls on the request path.** The F3 re-reading runs on
  `workbench.open`'s request path. In the common case its one judge call is
  answered from the ledger, because the card's reading wrote it. It reaches
  the model only when a worked example was studied between display and pick
  (or admission), under the service's own caps. The sources service sets
  the same precedent at serve time (`imported_exercise_selection`).
- **Item-level reasons at admission.** Admission reads the exercise by its
  statement, not by the new item, so that the judge's ledger answers.
  Attempts and reveals of an item written moments earlier by this import
  cannot exist before its first pick, and the submit's own eligibility
  decision still covers a family reveal.
- **App.tsx overlap.** `App.tsx` (`pickCheckMe`, `exerciseAdmitted`) also
  changes in other in-flight stages. Expect a conflict there at the merge.

## Gate (fix step; targeted, per the owner's 2026-10-17 rule)

- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok
  (`TMPDIR` = `fixtures-local/tmp`).
- `uv run lint-imports --no-cache`: **28 kept, 0 broken**.
- Targeted pytest: `uv run pytest -n auto` over the 189 files in
  `fixtures-local/tmp/rw4b-fix1-pytest-files.txt`. The list is the
  implement step's 159 files (every test file touching the workbench,
  source-service, reader prompt-contract and library-ask handlers; config
  snapshots and upgrades; sidecar registry, contract, serializer and RPC
  pins; mobile allowlist; architecture; table roles; coordinated migrations;
  tracked fixture databases; SQLite copy sites; instructional layering; CLI
  help snapshot), plus every test file referencing `reader.workbench`,
  `handlers.workbench`, `library_exercises`, `parameter_registry`,
  `classify_config_path` or `workbench.open`.
  - Result: **3,436 passed, 2 xfailed**.
  - After the final small edit (an unknown `admittedSessionId` is ignored),
    `test_library_exercises.py`, `test_reader_workbench_rw2a.py`,
    `test_registry_audit.py`, `test_mobile_allowlist.py` and
    `test_rw4_kill_switches.py` were run again: **334 passed**.
  - `test_library_exercises.py` alone now has **25 passed** (18 before this
    round, plus 7 new).
- Durability: no migration and no DB/connection code changed, so no
  durability tests are needed.
- Frontend (`apps/learnloop-tauri`):
  - `npm install` ok, and `npm run typecheck` clean.
  - Vitest over 40 files: **40 files, 352 passed**. The files are
    `app/App.wrapUpSkim`, `app/notices`, `app/readerWorkbench`,
    `app/readerCheck`, `screens/attentionBudget`, `reader/IntentBox`,
    `reader/intentSwitchOff`, `reader/libraryAskSwitchOff`,
    `reader/libraryAsk`, `reader/libraryAskJobs`,
    `reader/libraryExercisesReader`, `reader/libraryExercises`,
    `reader/exerciseCandidates`, `reader/nextStepFold`,
    `reader/readerWorkbenchExercise`, `reader/recapSwitchOff`,
    `reader/rw1bReview`, every `screens/ReaderScreen.*.test.tsx`, every
    `screens/workbench/*.test.tsx` and `components/SourceOffers`.
  - `npm run frontend:build`: ok.
- `src-tauri` unchanged, so no cargo check was run.
- References: `db_generate_reference.py` then `db_validate_reference.py`:
  **0 errors** (919 leaves, head 213; commit labels and line citations
  refreshed in `150b70a47`).
- No live or paid model call; fakes only.

## Re-review (round 2; codex-job 20261020-004635-fEubOE)

Codex re-checked round 1. F1 is confirmed fixed. It reopened F2 and raised
one new finding, F6. Both reproduced in a hook test before the fix
(`readerWorkbenchExercise.test.tsx`: 3 new tests, all 3 failed before and
pass after).

| id | severity | title | verdict | commit | test or reason |
|----|----------|-------|---------|--------|----------------|
| F1 | High | Library page's exercise actions crash (`openLibraryHit` uninitialized) | confirmed fixed (round 1) | `60384ab90` | Codex confirmed; round 1's regression test covers both actions |
| F2 | High (reopened) | A failed acknowledging open leaves the hand-off guard held, so the owed pick is never retried | fixed | `275decf58` | `an acknowledging open that failed releases the hand-off, so the owed pick is handed over again` |
| F6 | Medium | A late import answer associates the exercise with the wrong book | fixed | `275decf58` | `a late import answer from another book admits nothing until the exercise's own book is open again`; `a problem whose source is not the open card's admits nothing` |

### Fixes

- **F2.** `App.tsx`'s hand-off (`exerciseAdmitted` → `pickCheckMe`)
  resolves `true` once the pick is made and served. The acknowledging
  `workbench.open` runs after that, when the "check me" with
  `admitsSessionId` opens.
  - Before the fix, a failed open left the session in the hook's `admitting`
    guard. No later update or resume handed the pick over again, even though
    the server still reported `exercisePick.due`.
  - Now the check's open-failure path drops `admitsSessionId` from the
    guard. The next sight of the problem (an update or a resume, this visit
    or after a restart) hands the owed pick over again.
  - That new pick is served again, and its open carries the new serve's
    `schedulerCandidateId`/`planPresentationId`. The server persists them on
    the problem when it acknowledges the pick, which covers the missing
    serve identifiers Codex noted.
  - A successful open keeps the guard. The acknowledged session is no
    longer due, so the guard is moot. This also avoids a pick-and-open loop
    if an open succeeded without the server acknowledging it.
  - A retry happens on the next sight, not at once, so a persistent failure
    does not keep recording learner picks with nobody acting. This matches
    round 1's rule for a failed hand-off ("tried again, by this visit or the
    next").
- **F6.** `noteAdmission` now resolves the book from the problem itself.
  - It hands the pick over only when the problem's `extractionId` is the
    open extraction and its `sourceId` is the open card's.
  - Otherwise it does nothing. That covers a late import-refresh `update` for
    book A's problem while book B is open, and a moment when the card and the
    extraction disagree.
  - The pick stays `due` on the problem (server state, unchanged). When A is
    open again and the problem is resumed or updated, the pick is handed
    over with A's card and span.

### Gate (re-review fix step; targeted, per the owner's 2026-10-17 rule)

- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok
  (`TMPDIR` = `fixtures-local/tmp`).
- `uv run lint-imports --no-cache`: **28 kept, 0 broken**.
- Pytest: none. No Python file changed this round. Only
  `useReaderWorkbench.ts` and its test changed, and no Python test pins
  that file.
- Durability: none needed (no migration and no DB code changed).
- Frontend (`apps/learnloop-tauri`):
  - `npm install` ok, and `npm run typecheck` clean.
  - Targeted vitest over the same 40 files as round 1: **40 files, 355
    passed** (352 + the 3 new).
    - `app/App.wrapUpSkim`, `app/notices`, `app/readerWorkbench`,
      `app/readerCheck`
    - `screens/attentionBudget`
    - `reader/IntentBox`, `reader/intentSwitchOff`,
      `reader/libraryAskSwitchOff`, `reader/libraryAsk`,
      `reader/libraryAskJobs`, `reader/libraryExercisesReader`,
      `reader/libraryExercises`, `reader/exerciseCandidates`,
      `reader/nextStepFold`, `reader/readerWorkbenchExercise`,
      `reader/recapSwitchOff`, `reader/rw1bReview`
    - every `screens/ReaderScreen.*.test.tsx` and every
      `screens/workbench/*.test.tsx`
    - `components/SourceOffers`
  - `readerWorkbenchExercise.test.tsx` alone: **12 passed** (9 before plus 3
    new; the 3 new ones failed before the fix).
  - `npm run frontend:build`: ok.
- `src-tauri` unchanged, so no cargo check was run. The schema is
  unchanged, so the references were not regenerated, and no doc cites the
  changed lines.
- No live or paid model call; fakes only.

## Fix round 3 (orchestrator rulings)

The final Codex verify (codex-job `20261020-005349-gk5Hn0`, at `e4be125cb`)
confirmed F1 and reopened F2 and F6. The orchestrator ruled that the state
shape be made correct rather than patching each race:

- **R1.** Owed hand-offs are kept per workbench session, not in one slot.
- **R2.** Every async answer is checked against the request it answers before
  any state changes.
- **R3.** A submit's return context comes from the submitted session's own
  source and span.
- **R4.** Tests for all of the above, each failing on `e4be125cb`.

| id | severity | title | verdict | commit | test (fail before → pass after) |
|----|----------|-------|---------|--------|---------------------------------|
| F2 | High (reopened) | A pending pick for exercise A is lost when B's check replaces it in the single `readerCheck` slot | fixed (R1) | `69d70b733` | "R1 (verify F2): a pending pick for A survives B's check replacing it in the shell's slot, and A gets it on return"; "R1: A/B/A interleaving delivers A's owed pick exactly once after returning to A" |
| F6 | Medium (reopened) | A late resume activates A's problem while book B is displayed; its submit returns to `{card: B, spanId: span_A}` | fixed (R2, R3) | `69d70b733` | "R2 (verify F6): a late resume for A's exercise, answering after book B opened, activates nothing"; "R2: a stale open is dropped; the newer request's problem stays"; "R2: a stale post-attempt answer is dropped; it neither closes the problem now open nor leaves for feedback"; "R3: a submit returns to the submitted problem's own book and passage, not the card shown at submit time" |

All six tests are in `readerWorkbenchExercise.test.tsx`.

### Fail-before evidence

The six tests were written first and run on `e4be125cb`: **6 failed, 12
passed**. The log is `fixtures-local/tmp/rw4b-fix3-fail-before.txt`.

- **Verify F2, as written** (an App-like harness keeps the single slot, and
  the pick resolves after setting it): step 4 found **0** acknowledging opens
  for A (`expected [] to have a length of 1`).
- **A/B/A, with the served pick resolved to the hook:** **0** acknowledging
  opens. The old hook ignored a served check that was not delivered through
  the slot.
- **Verify F6, as written:** A's problem was active while B was displayed
  (`expected { session: … } to be null`).
- **Stale open:** the late answer for `wbs_1` replaced the newer `wbs_3`.
- **Stale post-attempt:** A's late submit closed `wbs_3` (`active`
  undefined) and left for feedback.
- **Return context:** the submit returned with the card shown at submit time
  (`other`), not the problem's own `book`.

### What changed

- **R1, owed hand-offs per session** (`useReaderWorkbench.ts`, the `owed`
  map). Each session id maps to one of these phases:

  | phase | meaning |
  |---|---|
  | `picking` | The shell is making and serving the pick. Holds the ticket it was asked under. |
  | `served` | Holds the served check, until the problem is next seen on its own book. |
  | `opening` | The acknowledging `workbench.open` (`admittedSessionId`) is in flight. |
  | `delivered` | That open succeeded, so the server acknowledged the pick. |

  - **Replacement.** No other session's pick touches an entry, so
    replacement is impossible.
  - **When a served check opens.** It opens at once only when it answers the
    newest request on its own book. Otherwise it waits, owed, and opens when
    its own problem is next opened, resumed or refreshed on its own book.
  - **Failures.** A failed pick or a failed acknowledging open removes the
    entry. The next sight of the problem hands it over again with a new
    serve, as round 2 decided. Nothing retries at once.
  - **Loops.** `delivered` stops a pick-and-open loop if a late answer still
    reports the pick as due.
  - **Restart.** After a restart the hook starts empty, and the server's
    durable `exercisePick.due` still drives the hand-off (the round 1 path).
- **The shell** (`App.tsx`).
  - `exerciseAdmitted` now makes and serves the pick, and resolves the served
    `ReaderWorkbenchCheck` to the Reader. It resolves null when there is no
    session, the workbench is off, or the pick fails.
  - It no longer writes the shared `readerCheck` slot. That slot now carries
    only a cue's check, the current display.
  - A check that still arrives through the slot naming `admitsSessionId`
    (the earlier contract, which the round 2 test drives) leaves the slot at
    once and is kept in the same map. A later check that replaces the slot
    cannot displace it either.
- **R2, requests are checked before any state changes.**
  - These requests take a ticket when they are sent (the request token, plus
    the open extraction and source): `openSelection`, `openItem`, `resume`,
    a cue's check, "use this one", the owed delivery, and the read-only
    problem behind feedback.
  - An answer is admitted only if three things hold:
    - its ticket is still the newest;
    - the same extraction and card are open;
    - the answered session is on that book (`extractionId` and `sourceId`).
  - Anything else is dropped before any state changes. The problem stays
    resumable, and owed if its pick is.
  - These events bump the token: a book change, Leave/Abandon, and an
    accepted submit. So an open still in flight cannot reopen over feedback
    or over another book.
  - An import refresh (`update`) for a session that is not on the open book
    changes nothing.
  - A post-attempt answer (`submitted`) is dropped when the submitted
    session is no longer the active one, or its extraction is no longer
    open. It closes nothing and leaves for no feedback. The attempt itself
    is kept server-side, and the marks refresh.
- **R3, the submit returns to the problem's own book.**
  - `ActiveWorkbench.card` is the card captured when the session was
    activated. R2 has already checked that this card is the session's own
    source.
  - `submitted` returns `{card: active.card, spanId: session.spanIds[0]}`. It
    never uses the card shown at submit time, which can run ahead of the
    extraction while a book opens. For that reason a submit is matched on
    the extraction, not the card.

### Notes for the landing

- **Dropped post-attempt answers.** A dropped post-attempt answer does not
  update the shell's practice-session snapshot (`sessionAfterWorkbenchSubmit`).
  This only matters when that submit was the one that started the practice
  session. The next submit or Begin picks the session up as before.
- **No auto-open on returning to a book.** A served pick that waits for its
  book is not opened automatically when the learner returns to that book.
  It opens on the problem's next sight, a resume from its ✎ mark or rail
  line. This avoids pulling the learner off a different problem.
- **`App.tsx` overlap.** `exerciseAdmitted` no longer goes through
  `pickCheckMe`. The merge note from round 1 still applies.

### Gate (fix round 3; targeted, per the owner's 2026-10-17 rule)

- `npm install` ok, and `npm run typecheck` clean.
- **Targeted vitest:** the same 40 files as rounds 1 and 2, listed in
  `fixtures-local/tmp/rw4b-fix3-vitest-files.txt`. Result: **40 files, 361
  passed** (355 + the 6 new).
  - `readerWorkbenchExercise.test.tsx` alone: **18 passed** (12 + 6).
  - Four further files that reference the check or cue path
    (`reader/checkOffer`, `reader/cues`, `reader/readerHooks.parity`,
    `reader/voices`): **4 files, 45 passed**.
- `npm run frontend:build`: ok.
- `uv run lint-imports --no-cache`: **28 kept, 0 broken**.
- Pytest: none. No Python file changed.
- Durability: none needed (no migration, and no DB code changed).
- `src-tauri` is unchanged, so no cargo check was run. The schema is
  unchanged, so the references were not regenerated.
- No live or paid model call was made.

## Fix round 4 (orchestrator rulings)

The final Codex verify `20261020-010830-SQ8D11` (at `7bec979e7`) confirmed
F6 and the A/B/A slot-replacement case. It reopened F2 and raised F3, F7, F8,
F9 and F10. The client-side hand-off kept producing races, so the
orchestrator moved authority to the server:

| ruling | what it requires |
|---|---|
| R1 | One server-side admission, keyed by the workbench session id. |
| R2 | A submit admits an owed pick first, or refuses (retryable). |
| R3 | Open and resume select by explicit session id, and validate the item and book. |
| R4 | One exercise-statement reader that re-checks the held-out predicate and fails closed. |
| R5 | One client generation counter; queued requests consumed by identity. |
| R6 | Server updates reach the mounted workbench. |
| R7 | Fail-before tests for each reproduction. |

### Findings

| id | severity | title | verdict | commit | test (fail before → pass after) |
|----|----------|-------|---------|--------|---------------------------------|
| F2 | High (reopened) | A submit without an App practice session discards the owed pick permanently | fixed (R1, R2) | `91798158c` | pytest `test_r2_verify_f2_submit_with_no_practice_session_admits_the_owed_pick_first`, `test_r2_a_submit_whose_admission_fails_submits_nothing_and_stays_retryable` |
| F7 | High | A stale candidate opens newly held-out material (the tail beyond the preview) | fixed (R4) | `91798158c` | pytest `test_r4_verify_f7_an_exercise_held_out_after_its_card_was_shown_is_never_read_or_opened`, `test_r4_a_problem_opened_before_its_region_was_held_out_is_not_shown_again`, `test_r4_the_statement_reader_fails_closed`, `test_r4_no_handler_or_reader_module_reads_an_exercise_statement_another_way` |
| F3 | Medium | The admission's exposure correction never reaches the mounted Workbench | fixed (R6) | `91798158c` | vitest `Workbench.test.tsx` › "R6 (verify F3): …keeping the unsaved step" |
| F8 | Medium | A late import refresh after Leave re-activates and admits | fixed (R5) | `91798158c` | vitest `readerWorkbenchExercise.test.tsx` › "R5 (verify F8): …", "R5: unmounting makes every answer still in flight stale" |
| F9 | Medium | An older open's completion clears a newer queued exercise | fixed (R5) | `91798158c` | vitest `readerWorkbenchQueue.test.tsx` › "R5 (verify F9): …" |
| F10 | Medium | `workbench.open` selects by item, so acknowledgement marks A while serving B | fixed (R1, R3) | `91798158c` | pytest `test_r1_verify_f10_admission_names_its_problem_never_another_with_the_same_item`, `test_r3_a_resume_opens_the_problem_it_names_on_its_own_item_and_book`, `test_r1_admission_is_idempotent_one_pick_one_admission` |
| F6 | Medium | Late resume on another book | confirmed fixed (round 3) | `69d70b733` | its round 3 tests kept, rewritten to the new protocol |

### Fail-before evidence (R7)

Every reproduction was run against an export of `7bec979e7`
(`git archive` into `fixtures-local/tmp/rw4b-fix4-base`, the worktree's own
venv and `node_modules`; no worktree or stash). The logs are
`fixtures-local/tmp/rw4b-fix4-python-fail-before.txt` and
`fixtures-local/tmp/rw4b-fix4-vitest-fail-before.txt`.

**Pytest: the 9 new tests, 9 failed.**

- **F2, end to end.** The problem was left while importing, the practice
  session ended, then the problem was resumed and submitted with no
  `practiceSessionId`. Result: `exercisePick.admitted` was False after the
  submit.
- **R2 refusal.** A submit with the admission refused did not raise; it
  submitted.
- **F10.** Run with the round 3 delivery (pick, then the acknowledging open
  by item with `admittedSessionId`): the open returned B's session id, not
  A's.
- **F7.** "Use this one" on a candidate held out after display did not
  raise; it opened.
- **Opened before held out.** A resume of a problem whose region was held
  out after it opened did not raise.
- **R3.** A resume with a mismatched item or book did not raise.
- **Fails closed.** `read_exercise_statement` was absent.
- **AST test.** It found 11 other statement reads (`_withheld`,
  `full_statement`, `_region_for`, `region.text`, `.get("statement")`).
- **Idempotent admission.** `workbench.admit` was absent.

**Vitest.**

- **F8.** After Leave, the late refresh made `active` A again (`expected {
  session: … } to be null`).
- **F3.** The exposure note never appeared on the mounted workbench.
- **F9, App half.** The harness that mirrors App at `7bec979e7`
  (unconditional `setReaderExercise(null)`) ended with the newer queued
  exercise cleared (`expected null to be { key: 'srcex:ext_b:t1' … }`). The
  same harness passes on the fixed hook, because a stale answer no longer
  calls the shell.
- **F9, committed test.** It uses App's new `consumeShown` and failed on
  `7bec979e7` (`consumeShown is not a function`; the hook also reported
  "shown" without the request's identity).
- **Rewritten protocol tests.** The tests rewritten to `workbench.admit`
  fail on `7bec979e7` as expected (10 failed across the 3 files, all of them
  admission-protocol or the F3/F8/F9 reproductions).

### What changed

#### R1: one server-side admission (`workbench.admit`)

- **The operation.** `workbench.admit` (`handlers/workbench.py:_admit`) is
  keyed by the workbench session id and runs under `vault_mutation_lock`
  (`purpose="workbench_admit"`). It re-reads the problem inside the lock and
  requires the pick to be owed: bound to the item its import wrote, open,
  and not admitted. Then it:
  1. resolves the practice session (the app's, else the most recent open
     one, else starts one; the submit's own rule);
  2. makes the plan's learner pick with the proposal and import ids;
  3. serves the item in that session (`get_practice_item`, which records a
     plan-off proposal's delivery and refuses held-out items);
  4. writes, in ONE transaction (`WB.admit_exercise_pick`): the serve pair
     on THIS problem, the practice session and the re-read exposure in the
     pick's record, and `admitted_at`.
- **Idempotent.** An admitted problem returns its admission (the same
  practice session) and makes no second pick. A failure before step 4
  leaves the pick owed.
- **What it does not cover.** A crash between steps 2 and 4 is the one
  window. A retry then makes a second learner pick, but the problem is still
  admitted only once. The pick and serve run their own transactions inside
  the lock, so one SQLite transaction cannot span all four steps.
- **Removed.** The round 3 client hand-off is gone: the owed map,
  `admittedSessionId` on `workbench.open`, `onExerciseAdmitted`,
  `admitsSessionId` on checks, and App's `exerciseAdmitted`.
- **Client.** The hook asks `workbench.admit` when it sees a due problem on
  its own book. It renders the answer only if the returned session id is the
  one it asked for, and it tells the shell about the practice session
  (`onPracticeSession`). The Tauri passthrough is `workbench_admit`, and the
  RPC is pinned desktop-only in `test_mobile_allowlist.py`.

#### R2: submit

- `workbench.submit` on a problem whose pick is owed runs `_admit` first, in
  the same request.
- If admission fails, it raises a retryable `admission_pending`: nothing is
  submitted, the problem stays open with its steps, and the pick stays owed.
- An admitted exercise submits in its admission's practice session while
  that session is open, with its admission's serve. A named serve never
  replaces the admission's.

#### R3: open and resume

- A resume selects by `sessionId`. It refuses `validation_error` when the
  request names another item, or (in the Reader) another book than the one
  the problem is on.
- Admission never goes through an open.
- **Interpretation, for the orchestrator.** A NEW cue "check me" still opens
  by item, so it reuses an open problem of that item (RW2a's F14 reuse). No
  admission or acknowledgement rides on it any more. Changing RW2a's reuse
  rule was out of RW4b's scope.

#### R4: one statement reader

- `library_exercises.read_exercise_statement` widens the spans to their
  complete exercise region(s) and asks `exam_withheld` about every span at
  read time. It returns None (fails closed) when the region is withheld,
  the predicate raises, or there is no text.
- Every RW4b path goes through it:
  - the candidate view's withholding;
  - the fallback listing's statement and label (`exercise_region_spans`
    gives boundaries only);
  - the exposure rule's input (`_proposal_candidate` takes the reader's
    statement, bounded as the arm bounds it, so the judge's ledger still
    answers);
  - `pick_exposure`;
  - `_picked_exercise` (refuses `exercise_withheld` before anything is read
    or stored);
  - resume and reuse of a picked exercise (`_refuse_withheld_exercise`);
  - the import queue (`_enqueue_import`, which covers retry).
- `full_statement`, `_withheld` and `_region_for` are gone.
- An AST test walks `learnloop_sidecar/handlers/**` and
  `learnloop/reader/**`. It requires that `exercise_regions`,
  `blocks_by_key`, `exam_withheld` and `full_statement` appear only inside
  the reader, and that no `.get("statement")` appears in RW4b's own
  modules.

#### R5: client hygiene

- **The generation counter.** `useReaderWorkbench` keeps one counter, bumped
  on Leave (`close`), a book change and unmount. Every async callback (open,
  resume, check, exercise, the read-only problem, admit, the workbench's own
  refresh and submit) captures it. A stale callback is dropped before any
  state change or shell callback.
- **Opens.** Among opens the newest wins (`openSeq`).
- **The workbench's callbacks.** `ReaderWorkingPosture` binds the workbench's
  `onSession` and `onSubmitted` to `active.generation`, so a callback from a
  workbench that was left or unmounted is stale.
- **Refresh poll.** `useWorkbenchSession`'s import-refresh poll ignores an
  answer after unmount.
- **`update`.** It requires the problem to be the active one on the open
  book.
- **Queued requests.** The shell consumes them by identity:
  `onExerciseShown(exercise)` and `onCheckMeShown(check)`, with App using
  `consumeShown`.

#### R6: server updates reach the mounted workbench

- `Workbench` takes `serverSession`, and `useWorkbenchSession.applyServer`
  merges the server's metadata: exposure, key, serve, binding and record.
- The window's steps, book choice and write queue are kept.
- The Reader passes `active.session`, which the admission answer updates.

### Notes for the landing

- **`App.tsx` overlap.**
  - `exerciseAdmitted` is gone.
  - `onCheckMeShown`/`onExerciseShown` now take the shown request.
  - `onPracticeSession` is new.
  - Expect conflicts with other stages that touch these props.
- **`workbench.open` input.** `admittedSessionId` was removed from
  `WorkbenchOpenInput`; extra fields are forbidden, so an old client gets a
  validation error.
- **Rust.** `workbench_admit` was added to `commands.rs` and `main.rs`, so
  cargo check was run.
- **New refusal codes.** `exercise_withheld` and `admission_pending`.

### Gate (fix round 4; targeted, per the owner's 2026-10-17 rule)

- **Pytest.** The 189 files of `fixtures-local/tmp/rw4b-fix1-pytest-files.txt`
  (handlers, reader workbench, library exercises, contract, allowlist,
  serializer and registry pins, CLI snapshot, and so on) with `-n auto`:
  **3,448 passed, 2 xfailed**.
  - `test_library_exercises.py` alone: **35 passed**.
- `uv run lint-imports --no-cache`: **28 kept, 0 broken**.
- Frontend:
  - `npm run typecheck` clean.
  - **Vitest**, 50 files (round 3's 40, the new `readerWorkbenchQueue`, the
    4 check/cue files, every `screens/workbench` test, and the 3
    PracticeScreen workbench files; list in
    `fixtures-local/tmp/rw4b-fix4-vitest-files.txt`): **50 files, 447
    passed**.
    - A first run, made while pytest loaded the machine, timed out in
      ReaderScreen suites. It also wrote a spurious second snapshot entry,
      which was reverted; the snapshot passes with `CI=true`. The rerun
      above is the result of record.
  - `npm run frontend:build`: ok.
  - `cargo check`: ok.
- Durability: none needed (no migration, and no connection or pragma code
  changed).
- **References.** `db_generate_reference.py` then `db_validate_reference.py`:
  **0 errors** (head 213). Commit labels and line citations were refreshed
  in `df68e6488`.
- No live or paid model call was made.

## Fix round 5 (orchestrator rulings)

The Codex verify `20261020-022437-5OEypp` (at `5929ff4fb`) confirmed F8, F9
and F10 fixed. It reopened F2 (High), F3 (Medium) and F7 (High), and raised
F11 (High) and F12 (Medium). The orchestrator's rulings:

| ruling | finding | what it requires |
|---|---|---|
| R1 | F2 | The learner pick carries a durable idempotency identity derived from the workbench session id, stored with its receipt; a retry completes only the missing admission write and never picks again. |
| R2 | F7 | One builder of every statement-bearing workbench response, revalidating through the shared reader; the reader moves to a package S1's import worker and `selection_for_region` also use; the AST test covers indirect helpers and stored-statement returns; a registry-enumerated contract test. |
| R3 | F11 | Admission's exposure recheck includes the bound `practice_item_id` (item attempts and family reveals count), keeping the source spans and the originating-proposal exemption; the practice-only result is persisted and rendered. |
| R4 | F3 | Lifecycle validity is an effect generation, set on setup and cleared on cleanup, so StrictMode works and an earlier setup's answers stay stale. |
| R5 | F12 | Departure callbacks (Leave, Abandon, the jump to the passage) carry and validate both the generation and the session id. |
| audit | — | Every remaining client callback in `useReaderWorkbench` and `useWorkbenchSession` checked for the same stale-identity pattern. |

### Findings

| id | severity | title | verdict | commit | test (fail before → pass after) |
|----|----------|-------|---------|--------|---------------------------------|
| F2 | High (reopened) | A retry after an admission-write failure delivers another learner pick | fixed (R1) | `ae8339e6a` | pytest `test_reader_rw4b_admission_idempotency.py` (5 tests): `test_r1_a_retry_after_a_locked_final_write_makes_no_second_pick` (Codex's reproduction), `test_r1_a_lost_pick_record_is_found_by_its_key_in_the_plans_receipt`, `test_r1_a_lost_serve_record_repeats_no_pick_and_no_presentation`, `test_a_pick_made_under_a_key_is_made_once[plan_open/plan_closed]` |
| F7 | High (reopened) | Workbench responses still return newly withheld statements | fixed (R2) | `ae8339e6a` | pytest `test_library_exercises.py`: `test_r2_verify_f7_get_refresh_and_an_admitted_admit_never_return_a_withheld_statement`, `test_r2_contract_no_workbench_or_reader_exercise_rpc_returns_a_held_out_statement`, `test_r2_no_handler_reader_module_or_s1_path_reads_an_exercise_statement_another_way`, `test_r2_every_response_carrying_a_stored_statement_passes_the_gate`, `test_r2_the_shared_reader_lives_where_s1_and_the_reader_import_it`, `test_r4_the_statement_reader_fails_closed` (moved to the shared module); `test_exam_protection.py::test_a_reader_import_of_held_out_material_is_refused_before_any_model_call` (now also asserts `selection_for_region` refuses once held out) |
| F11 | High | Admission misses a revealed sibling and keeps the independent-check offer | fixed (R3) | `ae8339e6a` | pytest `test_r3_verify_f11_admission_reads_the_bound_items_own_exposure_and_says_practice_only` |
| F3 | Medium (reopened) | StrictMode blocks import refreshes and admission metadata | fixed (R4) | `ae8339e6a` | vitest `Workbench.test.tsx` › "R4 (verify F3): under StrictMode the import refresh lands and is handed on", "R4 (verify F3): under StrictMode the admission's exposure correction reaches the mounted workbench", "R4: a refresh sent under an earlier setup changes nothing after unmount" (a guard; it passes on both) |
| F12 | Medium | A delayed Leave or Abandon closes a newer problem | fixed (R5) | `ae8339e6a` | vitest `readerWorkbenchExercise.test.tsx` › "R5 (verify F12): a delayed Leave or Abandon of A never closes B", "R5: a departure from a workbench shown in an earlier generation … changes nothing" |
| audit | — | Two more stale-answer paths | fixed | `ae8339e6a` | vitest "round 5 audit: an older marks refresh landing late never replaces a newer one" (`readerWorkbenchExercise.test.tsx`), "round 5 audit: a bind or reopen answered after unmount is never handed on" (`Workbench.test.tsx`) |

No ruling was rejected. One residual window is recorded under R1.

### Fail-before evidence

Every new or changed test was run against an export of `5929ff4fb`
(`git archive` into the session scratchpad: the backend with the
worktree's venv and `-o pythonpath=<export>/src`, the frontend's `apps/`
with the worktree's `node_modules` linked in; no worktree change, no stash).

**Pytest: 12 new or rewritten tests, 12 failed.** The 3 round 4 tests the
same filter selected passed on both trees.

- **F2, as Codex wrote it.** With today's plan closed and a `database is
  locked` injected on the final admission write, the retry left
  **2 presentations and 2 pick receipts** (`assert (2, 2) == (1, 1)`). After
  the fix: 1 and 1, and the problem names that presentation.
- **R1's other 4.** `learner_pick` had no `idempotency_key`, and
  `WB.record_admission_stage` (the kept admission steps) did not exist.
- **F7.** `workbench.get`, `workbench.refresh_import` and an admitted
  `workbench.admit` returned the statement (`DID NOT RAISE`). The
  registry-enumerated contract test found the sentinel in the first RPC it
  reached (`workbench.abandon` answered with the stem).
- **The AST tests.** The indirect-reader scan found 331 functions reaching a
  statement read outside the shared reader, the first being S1's
  `_import_source_exercise`. The stored-statement scan found 4 ungated
  builders (`workbench_for_item`, `workbench_for_source`, `build_recap`,
  `build_wrap_up`). `learnloop.content.sources.exercise_statements` did not
  exist (2 tests).
- **F11.** With the bound item's answer revealed after the pick, admission
  read `exposed: False` (`assert (False is True)`).
- **Updated tests.** 5 existing tests in `test_exam_protection.py`,
  `test_exam_protection_review.py` and `test_import_split_parity.py` fail on
  the export only because `selection_for_region` now takes `vault=` (one
  needs `fixtures/migration_head_213`, absent from the export). They are API
  changes, not fail-before evidence.

**Vitest: 7 new tests, 6 failed.** The unmount guard passes on both trees,
as a guard should.

- **F12.** A's delayed Leave after B opened returned A's passage (`expected
  't6' to be null`) and closed B. The same for a Leave from a workbench shown
  in an earlier generation.
- **F3.** Under StrictMode the bound import refresh was never handed on,
  and the exposure note never appeared on the mounted workbench.
- **Audit.** An older marks refresh replaced the newer list (`expected [] to
  deeply equal [{ sessionId: 'wbs_1', … }]`). A bind and a reopen answered
  after unmount were handed on (`called 2 times`).
- `Workbench.test.tsx` › "F8: a vault switch freezes …" also failed once in
  that run on the export, under a load average near 67. It passed alone on
  the export and in every worktree run. It is a timing flake, not evidence.

### What changed

#### R1: the learner pick's idempotency identity (F2)

- **The key.** `handlers/workbench.py:admission_key(session_id)` is
  `workbench_admission:<workbench session id>`. `_admit` passes it to the
  plan's learner pick (`PlanLearnerPickInput.idempotency_key`, at most 200
  characters).
- **Stored with the receipt.** `daily_plan.engine.learner_pick` writes the
  key into the pick's `block_chosen` event detail on both branches: the open
  plan's one-item block and the closed plan's open-list pick.
- **Found on retry.** `engine.picked_under(env, key, item)` reads that
  receipt and returns the pick as it was made: its block, candidate and
  presentation. Both `learner_pick` and the sidecar's `plan_learner_pick`
  answer from it before anything is written. A retried pick therefore
  records nothing again: no receipt, presentation, router decision or
  delivery.
- **The admission's own steps.** `WB.record_admission_stage` keeps them on
  the problem's stored pick record:
  - `picked`: the practice session, whether the plan was on, and the serve
    pair;
  - `served`.
  A retry reads them and does only what is missing: no pick when `picked`
  is kept, no serve when `served` is kept, then the one admission write.
- **A lost `picked` record.** If the pick commits but its record on the
  problem fails, the retry asks the plan again under the same key, and
  `picked_under` returns the existing pick.
- **Residual window.** If the serve commits but the `served` record fails,
  the retry serves once more. That serve makes no pick and no presentation
  (the test pins this). Its proposal delivery is deduped, but the serve's
  own side effects can repeat (the diagnosis-serve count, an elicitation
  decision). The pick, the serve and the admission still run as separate
  transactions inside the vault lock, so one transaction cannot span them.

#### R2: one gate, one shared reader (F7)

- **The reader moved.** `learnloop/content/sources/exercise_statements.py`
  now holds `exercise_regions`, `starts_exercise`, `ExerciseRegion`,
  `exercise_region_spans`, `read_exercise_statement` and `selection_nodes`,
  beside the exam predicate. It sits there because S1's
  `content.authoring` is imported by `instructional` and so cannot import
  it. `instructional.exercises` and `library_exercises` re-export it.
  - The reader now also fails closed on a missing asked span.
  - It returns each asked block's stored text, for S1's selection.
- **S1 routed through it.**
  - `source_exercise_import.selection_for_region` now takes `vault=` and
    refuses (`ExerciseAuthoringError`) a region that is exam or held-out
    material now, unreadable, or missing.
  - `_import_source_exercise` reads its statement and selection through the
    reader after the existing exam check, so a region whose other blocks are
    held out is refused too.
  - The fallback listing passes `vault`.
- **The one builder.** `handlers/workbench.py:_view` builds every response
  that carries a problem, and it calls `_refuse_withheld_exercise` (via
  `WB.statement_cleared`, the shared reader on the problem's stored region)
  before building anything. Every RPC that answers with the problem (`get`,
  `open`, `refresh_import`, `admit` whether admitted or not, `submit`,
  `leave`, `abandon`, `reopen`, `bind`, `set_book`, `session_for_attempt`
  and the rest) then answers `exercise_withheld` instead. Submitted problems
  are no longer exempt.
- **Other surfaces.**
  - **Gated.** `workbench.submit` checks before admitting or grading. The
    help handlers check in `_require`.
  - **Filtered out of the lists.** `workbench.for_item` and
    `workbench.for_source`, through `_cleared`. The problem's steps are
    kept.
  - **Not named.** The recap's unfinished problems and the wrap-up's "with
    help" lines.
- **Saves without the statement.** `workbench.save_step` and the help
  ladder's record now use `record_line`: the record line and save time
  only, never the statement. A problem whose region is held out keeps saving
  its steps, and nothing of it is returned.
- **The AST tests.**
  - `test_r2_no_handler_reader_module_or_s1_path_reads_an_exercise_statement_another_way`
    scans `handlers/**`, `reader/**` and S1's two statement paths. It
    closes over indirect calls (a function that calls a reader is a
    reader), and it requires both S1 paths to call `read_exercise_statement`.
  - `test_r2_every_response_carrying_a_stored_statement_passes_the_gate`
    requires every function in the four response modules that reads a
    stored statement (`session_view`, the session lists, `stem_md`) to name
    a gate. The two ungated builders are listed with their reasons.
- **The contract test.** It enumerates every `workbench.*` method and every
  `LIBRARY_EXERCISE_RPCS` method from `METHOD_REGISTRY`, so a new RPC is
  covered without editing the test. A method with a required parameter the
  test cannot fill fails the test.
  - The setup opens the sentinel exercise, saves a step, binds it, then
    holds its region out, and calls each RPC.
  - Neither the lead sentinel nor the region's tail appears in any answer
    or refusal.
  - The six statement-bearing RPCs refuse `exercise_withheld`, and the
    source list leaves the problem out.

#### R3: the bound item counts at admission (F11)

- `library_exercises.pick_exposure(..., practice_item_id=)` adds the bound
  item to the candidate the exposure rule reads, on both the proposal path
  and the fallback path. The rule then counts the item's attempts, its own
  and its family's revealed answers, and its impressions, alongside the
  source spans. The originating proposal's own impression stays exempt
  (`proposal_id`), and so do a fallback's own listing events.
- `_admit` passes the item it bound. `admit_exercise_pick` persists the
  result with `exposureChecked: "admission"`.
- The workbench renders it through the round 4 R6 path. The test reads it
  back through `workbench.get`: `exposed`, `offeredAs: "practice"`.

#### R4: the lifecycle generation (F3)

- `useWorkbenchSession` replaces the `closed` gate with an effect
  generation. Each setup takes a new number (`live`), and its cleanup clears
  it. StrictMode's setup, cleanup, setup therefore leaves the hook live, and
  the import refresh, `applyServer`, abandon, reopen, retry, bind and submit
  apply an answer only while the setup that sent it is still current.
- `closed` remains only for the write queue's retry bound after a close.
- The book write still lands whatever happened to the window; only a live
  workbench shows its answer.

#### R5: departures carry their identity (F12)

- `ReaderWorkingPosture` binds `onLeave` and `onAbandoned` to
  `active.generation`, and ReaderScreen's `leaveWorkbench` passes it on.
- `useReaderWorkbench.close` returns null and changes nothing in two cases:
  the generation is stale, or the session is not the one shown. It sets no
  abandoned receipt and returns no passage, so nothing jumps. Its fallback
  target is read from `activeRef`, not the render's `active`.

#### Audit of the remaining client callbacks

- **`useReaderWorkbench`.**
  - **Fixed.** The marks refresh (`workbench.for_source`) now applies only
    the newest request's answer.
  - **Already guarded.** `admit` checks its generation and that the answer
    is the problem it asked about. Every open path (`openSelection`,
    `openItem`, `resume`, check me, "use this one", the read-only attempt)
    uses `ticket`/`admits`. `update` and `submitted` take the shown
    generation, and `reopenAbandoned` goes through `resume`.
- **`useWorkbenchSession`.**
  - **Fixed.** Bind, reopen, retry, abandon and submit now check the setup
    generation; before, they were handed on after unmount.
  - **Unchanged.** The write queue (`pump`) still finishes after unmount by
    design ("the queue finishes on its own"). Its answers update only this
    hook's own state, and a book write's answer is shown only while the
    hook is live. A step the server refuses is still reported. Leave's `run`
    returns to its caller, whose `onLeave` is now validated (R5).

### Notes for the landing

- **`selection_for_region` signature.** It takes a required keyword `vault`
  and now refuses held-out or missing regions. Its three in-tree callers
  and the tests were updated. Other stages calling it will need `vault=`.
- **Behaviour change: submitted problems are no longer exempt.** A
  submitted picked exercise whose region is held out later now refuses
  `exercise_withheld` from `workbench.get` and
  `workbench.session_for_attempt` too. The Reader's back-from-feedback open
  swallows the error, and the problem is not shown.
- **Re-export.** `instructional.exercises` re-exports the moved region
  helpers (`noqa: F401`), so other importers keep working.
- **Help on a withheld problem.** The help handlers now import
  `_refuse_withheld_exercise` from `handlers.workbench` lazily.
- No migration, no new config key, no new RPC, and no Rust change.

### Gate (fix round 5; targeted, per the owner's 2026-10-17 rule)

- **Pytest.** The 303 files of `fixtures-local/tmp/rw4b-fix5-pytest-files.txt`
  were run with `-n 12`: round 4's 189, plus the files that exercise the
  daily-plan engine, the exercise arm, exam protection, the recap and S1's
  import, plus the new `test_reader_rw4b_admission_idempotency.py`.
  - **First run: 5,245 passed, 2 xfailed, 2 failed.** Both failures were in
    `test_architecture.py`:
    - a new function-local edge `reader.workbench ->
      content.sources.exercise_statements`;
    - `instructional.exercises` importing the private `_LABEL_RE` and
      `_NUMBER_RE`.
  - **Fixed before the commit.** The import in `reader/workbench.py` is now
    module-level, and the shared module exports `LABEL_RE` and `NUMBER_RE`,
    which the arm aliases.
  - **Rerun:** `test_architecture.py` plus the 35 workbench, reader, recap,
    exam-protection, exercise, import-split, registry and architecture files
    of the list: **736 passed**.
- `uv run lint-imports --no-cache`: **28 kept, 0 broken**.
- **Frontend.**
  - `npm run typecheck` clean.
  - **Vitest**, round 4's 50 files (`fixtures-local/tmp/rw4b-fix4-vitest-files.txt`,
    `CI=true`): **50 files, 454 passed** (447 + the 7 new).
  - `npm run frontend:build`: ok.
  - No Rust change, so no cargo check.
- Durability: none needed (no migration, and no connection or pragma code
  changed).
- **References.** `db_generate_reference.py` then `db_validate_reference.py`:
  **0 errors** (head 213, 919 leaves). Commit labels and line citations were
  refreshed in `34f5237f8`.
- No live or paid model call was made, and no owner vault was opened.

## Fix round 6 (orchestrator rulings)

The Codex verify `20261020-123459-EZlKv5` (at `707a64ec5`) confirmed R3,
R4 and R5, import gating, config classification, and G19/G34/G53. It found
two Highs and one Medium:

- **F2 (High), the planned branch.** A keyed pick of an item already in
  today's plan recorded no key, so a retry under a later plan made a second
  presentation.
- **F7 (High), cached exercise jobs.** `reader.library_job` returned a
  finished exercise job's candidates, statement included, after their region
  was held out.
- **F13 (Medium), partial writes.** A keyed `block_chosen` receipt counted
  as a complete pick even when its serve or its proposal's delivery had not
  committed.

The orchestrator's rulings:

| ruling | finding | what it requires |
|---|---|---|
| 1 | F2 | The planned branch records the admission key against the EXISTING presentation, in the serve's transaction, as a keyed receipt row that links the key to the presentation. `picked_under` finds it across plan changes. |
| 2 | F7 | Every job or cache read that returns exercise candidates or statements revalidates at delivery through the shared statement reader. The registry contract test covers completed jobs, `reader.library_job` included. |
| 3 | F13 | Atomicity first: the keyed receipt, the serve and the proposal delivery commit in ONE transaction where the engine allows it. Otherwise, record the stage and recover idempotently. Say which residual remains. |

### Findings

| id | severity | title | verdict | commit | test (fail before → pass after) |
|----|----------|-------|---------|--------|---------------------------------|
| F2 | High (reopened) | A keyed pick of an already-planned item has no durable admission identity | fixed (ruling 1) | `1e7e0df78` | pytest `test_reader_rw4b_fix6.py::test_f2_a_keyed_pick_of_a_planned_item_is_found_under_a_later_plan`, `::test_f2_verify_sequence_planned_pick_locked_picked_write_retry_under_a_later_plan` (Codex's sequence) |
| F7 | High (reopened) | Cached exercise jobs bypass the withholding gate | fixed (ruling 2) | `1e7e0df78` | pytest `test_library_exercises.py::test_r6_verify_f7_a_finished_exercise_job_read_after_its_region_is_held_out_never_delivers_it`, `::test_r2_contract_no_workbench_or_reader_exercise_rpc_returns_a_held_out_statement` (extended: finished jobs seeded before the hold-out, `reader.library_job` enumerated); `test_reader_rw4b_fix6.py::test_f7_a_finished_help_job_on_a_problem_held_out_since_is_never_delivered` |
| F13 | Medium | Receipt recovery skips an unfinished serve and delivery | fixed (ruling 3, atomic route) | `1e7e0df78` | pytest `test_reader_rw4b_fix6.py::test_f13_a_failure_after_the_block_and_before_the_serve_…[planned/new_block]`, `::test_f13_a_failure_after_the_serve_and_before_the_delivery_…[planned/new_block]`, `::test_f13_the_admissions_serve_and_its_served_record_share_one_transaction`, `::test_f13_an_unkeyed_pick_keeps_its_own_transactions` |

No ruling was rejected. The round 5 residual (a repeated serve's side
effects) is closed by the atomic route; see F13.

### Fail-before evidence

Every new or extended test was run against an export of `707a64ec5` in the
session scratchpad (`git archive`, the worktree's venv,
`-o pythonpath=<export>/src`; no worktree change, no stash). **11 tests, 11
failed.** The 4 older tests the same filter selected passed on both trees.

- **F2, engine.** A keyed pick of the planned item, then the same key under
  the next day's plan: `assert (2, <second>) == (1, <first>)`, so two
  presentations and the second one returned.
- **F2, Codex's sequence.** The `picked` write met `database is locked`,
  then the admission was retried under a later plan: 2 presentations of
  the item.
- **F13, block then serve.**
  - New block: the learner-pick block was left behind without its serve
    (`assert 1 == 0` learner-pick blocks).
  - Planned: the serve's presentation was already kept when the failure
    was raised (`assert 1 == 0` presentations).
- **F13, serve then delivery.**
  - Planned: the presentation was kept without its delivery
    (`assert 1 == 0`).
  - New block: the retry returned early and recorded neither the keyed
    pick nor the delivery (`assert 0 == 1` keyed receipts).
- **F13, the admission's serve.** A lost `served` record left the first
  serve committed: 2 probe rows written inside the serve, against 1.
- **F7, library jobs.** The kept `find_exercises` result went out with the
  sentinel statement (`'An eigenvalue t satisfies' … is contained here`),
  and so did `reader.library_job` in the contract test.
- **F7, help job.** A finished help job on a held-out problem was delivered
  (`DID NOT RAISE`).
- **API.** `test_f13_an_unkeyed_pick_keeps_its_own_transactions` fails
  because `engine.PICK_KEYED` and `within` are new.

### What changed

#### Ruling 1: the keyed receipt (F2)

- **The row.** `daily_plan.engine.PICK_KEYED` (`"pick_keyed"`) is an
  `attention_block_events` row on the block that served the pick. Its
  detail names the idempotency key, the item, the presentation id and the
  session.
  - The table's role is RECEIPT, and record replay ignores unknown kinds.
  - No migration was needed.
- **Every branch writes it**, in the serve's transaction:
  - **Planned:** the existing block and its existing presentation.
  - **New one-item block:** the new block.
  - **Open-list pick** (the plan closed): the receipt.
- **The lookup.** `picked_under` reads the keyed receipt by key and item,
  under any plan, and returns the ORIGINAL block, presentation and
  candidate (`presentation_by_id`, falling back to the block's
  presentation). A retry under a later plan therefore returns the first
  presentation and creates none.
- **Kept from round 5.** The key stays in the `block_chosen` detail as a
  record, but recovery no longer reads it.

#### Ruling 3: one transaction (F13)

- **The pick.** With an idempotency key, `learner_pick` runs its write
  section in one `repository.atomic()` (`_keyed_pick_scope`):
  - the block (new-block branch), the serve with its presentation and AD's
    serve record, and the keyed receipt;
  - the caller's `within`, which the sidecar uses for the proposal's
    delivery.
  Unkeyed picks keep their own transactions as before. `within` without a
  key raises `ValueError`.
- **The delivery.** `plan_learner_pick` passes the proposal's delivery
  (`_proposal_delivery`, with the serving block's router decision) as
  `within` when the pick is keyed. A keyed receipt therefore exists only
  for a pick whose block, serve, presentation and delivery all committed,
  and a failure at either boundary leaves nothing to recover.
- **The admission's serve.** `_admit` now runs the practice screen's serve
  (`get_practice_item`, which also records a plan-off proposal's delivery)
  and its `served` stage in one `repository.atomic()`.
  - This closes the round 5 residual: a lost `served` record rolls the
    serve back, so its side effects (the diagnosis-serve count, an
    elicitation decision, a cold administration) never repeat.
  - The serve path writes only through the repository (no direct write
    connection), and no test took a lock wait.
- **Boundaries that stay separate, and why.**
  - **The plan's pick vs the problem's `picked` record.**
    `plan_learner_pick` first runs the queue build's prerequisites (the git
    sweep with its own short busy timeout, the pinned diagnostic-followup
    backfill, and a wait on the diagnosis workers). Those cannot run inside
    a write transaction without blocking on it. Recovery is the keyed
    receipt, which by construction names a complete pick.
  - **The selection (usage signal) before the pick.** It is idempotent.
  - **The final admission write.** The retry does only that write.
  - **Background work after the response** (approach-map builds, AD
    forecasts). It runs outside, as before.

#### Ruling 2: kept jobs revalidated at delivery (F7)

- **The hook.** `library_ask._Job` has a `deliver` hook, run by
  `_job_payload` on every read: the first answer and each
  `reader.library_job`. It runs on a copy, so the kept result is never
  rewritten.
- **Exercise jobs.** Both are started with
  `library_exercises.deliver_exercise_result`: `reader.exercise_candidates`
  and `reader.find_exercises`. At delivery it reads each candidate's region
  again through the shared statement reader.
  - A candidate that is withheld now, or whose predicate cannot be read, is
    dropped. That removes its statement and its permission to render the
    proposal's stored statement.
  - The drop is counted (`withheld`, `dropped.withheld`), and `status`
    becomes `none_found` when nothing is left.
  - With the switch off since, the read refuses `library_exercises_disabled`.
- **Help jobs.** The other kept job that can carry a problem's text is a
  workbench help job. `workbench_help._payload` now passes the workbench
  gate (`_refuse_withheld_exercise`) before delivering. A problem held out
  since refuses `exercise_withheld`, and an undelivered job is cancelled.
- **Not changed.** The library ask, notes, compare and tutor jobs return
  passages and answers, not exercise candidates. `find_practice` is
  computed fresh on each call, under the exam predicate.
- **The contract test.** It now seeds a finished `exercise_candidates` job
  and a finished `find_exercises` job (each showing the sentinel exercise)
  before the hold-out, and enumerates `reader.library_job` from the
  registry. After the hold-out it reads both jobs: neither the exercise's
  key nor its text goes out.

### Notes for the landing

- **New block-event kind `pick_keyed`.** It is written only for keyed picks
  (RW4b's admission). Replay and reconciliation ignore it. No migration.
- **`learner_pick` gains `within=`.** It also now reloads an open-list
  pick's record inside its transaction.
- **`LibraryJobs.start` gains `deliver=`.** Other job kinds are unchanged.
- No frontend, config, RPC or Rust change.

### Gate (fix round 6; targeted, per the owner's 2026-10-17 rule)

- **Pytest.** Round 5's 303 files plus the new `test_reader_rw4b_fix6.py`
  (`fixtures-local/tmp/rw4b-fix6-pytest-files.txt`), `-n 12`: **5,257
  passed, 2 xfailed**.
  - Earlier subsets: the 125 daily-plan, router, library, workbench, hint,
    reader, exam, exercise and architecture files, 1,625 passed; the four
    admission and pick files with `--durations`, 72 passed, slowest 3.0 s
    (no lock wait).
- `uv run lint-imports --no-cache`: **28 kept, 0 broken**.
  `test_architecture.py`: 18 passed.
- **Vitest.** Round 4's 50 files (`CI=true`): **50 files, 454 passed**. No
  frontend change this round, so no build, typecheck or cargo run was
  needed.
- Durability: none needed (no migration; the new transactions use the
  existing `Repository.atomic()` nesting).
- **References.** `db_generate_reference.py` then `db_validate_reference.py`:
  **0 errors** (head 213, 919 leaves). Commit labels and line citations were
  refreshed in `6245dc89f`.
- No live or paid model call was made, and no owner vault was opened.
