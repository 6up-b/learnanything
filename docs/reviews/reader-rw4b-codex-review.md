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
