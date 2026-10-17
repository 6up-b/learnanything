# Reader workbench RW2a: the resumable scratchpad (stage `reader-rw2a`)

Branch `reader/rw2a` (worktree `learnanything-merge4`), base `main` at
`9cdaefb9e` (`mvp-0.27`, one eligibility decision; migration head 206). Spec:
`docs/specs/spec_reader_workbench_v1.md` §13 row RW2a and what it cites (§5.1,
§5.4 source visibility and what an attempt records, §5.6, §5.7's
`workbench_sessions` and `workbench_steps`, §5.8, §5.9 successor none and
`workbench.enabled`), §3.4, §12, §14 (G5's source-visible and no-help rows,
G6, G10, G11, G32, G58), §16, §20 (§20.9). Presentation:
`docs/specs/ux_reader_workbench_v1.md` §1, §3.4, §4.0, §4.12, §5 (RW2a parts),
W5, W8, W15, §10 S1/S2/S6/S7/S13.

## 0. Plan (written before the code)

**Scope.** RW2a only. No model call of its own (the one paid call it starts is
the existing `import_exercises` job, on its own route and caps). No grading,
regrade, replay or eligibility rule changes.

**Migration 207** (`migrations/207_workbench.sql`):
- `workbench_sessions` (WORKFLOW): §5.7's columns, every CHECK'd column with
  all its values (`import_status` none|pending|bound|failed; `origin`
  reader|practice|plan; `entry` all eight; `status` open|submitted|abandoned;
  `help_style` let_me_struggle|balanced|guide_me, null until RW2b).
- `workbench_steps` (RAW_LEDGER, append-only by trigger): `id`, `session_id`,
  `ordinal`, `kind` step|stuck, `body_md`, `supersedes_id`, `deleted`,
  `client_idempotency_key` (unique per session), `created_at`. An edit is a
  new row superseding the head of its chain; a delete is a tombstone row; an
  undo is a row superseding the tombstone.
- `db/table_roles.py` classifies both; `fixtures/migration_head_206` becomes
  `migration_head_207` (backup-API copy, only 207 applied, rollback journal),
  its README and every hard-coded path; the DB reference scripts regenerate.

**Backend** (`learnloop/reader/workbench.py`, functional core + shell;
`db/stores/workbench.py`; `learnloop_sidecar/handlers/workbench.py`):
- RPCs `workbench.open`, `.get`, `.save_step`, `.set_book`, `.leave`,
  `.abandon`, `.reopen`, `.refresh_import`, `.bind`, `.retry_import`,
  `.submit`, `.session_for_attempt`, `.for_item`, `.for_source` (the last is
  the read RW6a's recap will call: open and abandoned sessions on a source,
  with `unfinished` past `open_session_days`). Desktop only (D20), pinned off
  the phone.
- Opening at once (S2): `open` with a selection stores the verbatim stem and
  enqueues the existing exercise import itself (the same code
  `reader.import_exercise` runs); `refresh_import` binds when the job lands
  (one item binds; several ask which part; none or a failed job is
  `failed`, steps kept, "try again").
- Book visibility by entry (S7, D9): a pure default per `entry`; flipping
  before the first step is free; the first step with the book open, or opening
  it afterwards, stamps when the book first counted.
- Submit composes through the ordinary `submit_attempt` path (one shared
  implementation, `entry_surface = 'desktop_reader_workbench'` for the Reader,
  `'desktop_practice_workbench'` for the practice screen and plan): the
  answer is the live `step` rows in order (stuck rows and tombstones
  excluded); `hints_used` is 1 when the book counted (plus the existing
  tutor-question fold, then the existing cap); the attempt type is the one the
  answer box picks (`stuck_attempt_type`); an empty work list with an empty
  stuck box is the existing empty stuck answer. The submit therefore asks
  `serve_eligibility.decide` exactly as every submit does
  (`attempts._resolve_attempt_target`); a refusal keeps the session open and
  the steps.
- Every lifecycle change logs a salience-only `reader_action_invoked` with a
  payload `event` (no new event kind, no new reveal kind).

**Kill switch** `workbench.enabled` (default true) and `workbench.open_session_days`
(30): modelled defaults, out of the decision-only template. Off: every
workbench RPC refuses `workbench_disabled` and writes nothing, the config DTO
carries no `workbench` key, and no screen shows an entry. Every
`DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry recomputed with the "no scoring,
scheduling, projection or serving change" note. No successor (§5.9), unless
the mapping check (§5.4 against `resolve_attempt_activity_policy`) finds one.

**Frontend** (`screens/workbench/`): the pure step model and record line, the
write queue hook (saved · just now / not saved yet — retrying / sidecar
unreachable), the `Workbench` component (header, problem, book line, steps in
`LiveMarkdownEditor`, I'm stuck, Submit with its record line, Leave for now,
`⋯` Abandon, abandoned · reopen), the half-window split (resizable, remembered,
min 480 px) and the stacked layout under 1,040 px with *show in the book*; the
Reader's entries (*work through this* on a selection and on an imported
exercise, `✎` resume beside the passage, the rail's unfinished problems),
book hidden over the source pane (W8), collapse back to reading at the passage;
App: a Reader workbench submit goes to feedback and Esc/b return to the
problem read-only, then to reading; the practice screen's remembered *Work in
steps* and *resume your steps* on the practice card. Chords checked against
`LiveMarkdownEditor`.

**Tests, fail-first:** a backend file per gate group (lifecycle, source
visible record, eligibility composition, grader blindness, switch-off
identity, migration and roles) and vitest files for the step model, the
workbench component and the screens (Reader working posture, practice
screen, back from feedback, switch-off DOM identity against a snapshot taken
on the base code).

## 1. What was built

| Part | What | Commits |
|---|---|---|
| Fail-first backend tests | `tests/test_reader_workbench_rw2a.py` (50), the fourteen RPCs pinned off the phone in `tests/test_mobile_allowlist.py` | `49065fa71` |
| Backend | migration 207, `db/stores/workbench.py`, `reader/workbench.py`, `handlers/workbench.py`, the shared submit and import helpers, `[workbench]`, the import-linter contract, the head fixture | `e4a79f770` |
| References | DB and configuration references regenerated at head 207 | `f093fc456` |
| Fail-first frontend tests | the switched-off snapshots taken on the base frontend, and the step model, workbench, editor, Reader, practice-screen and App tests | `048acbaed` |
| Frontend | the workbench, the Reader's working posture, the practice screen's *Work in steps*, the App's way back, fourteen Tauri passthroughs | `e6fd14844` |
| Gate fixes | `workbench.open_session_days` classified in `params/parameter_registry.py` (structural, operational: a display limit); `db/stores/workbench.py` registered as a SQL owner in `tests/test_architecture.py`; `test_forecast_receipts_landing.py` allows a head after 206; references regenerated; the Pipeline Map bullet | `3c996b1a8` |
| Record | this file | (last commit) |

**Paid calls:** none ($0.00). RW2a has no model route of its own; the one paid step it starts is the existing exercise import (`canonical_ingest` route, its own caps), and every test fakes it. No provider, no key, no vault opened, no manual run.

### 1.1 Data (migration 207)

- **`workbench_sessions`** (WORKFLOW). §5.7's columns, every CHECK'd column created with all its values: `import_status` none · pending · bound · failed; `origin` reader · practice · plan; `entry` all eight; `status` open · submitted · abandoned (`abandoned → open` on reopen); `help_style` let_me_struggle · balanced · guide_me (NULL until RW2b). Two table CHECKs: `submitted` exactly when `attempt_id` is set, and `bound` only with an item.
- **`workbench_steps`** (RAW_LEDGER, append-only by trigger). An edit is a new row superseding the newest version of its chain (a partial unique index keeps chains linear), a delete a tombstone row (text kept), an undo a row superseding the tombstone; `(session_id, client_idempotency_key)` is unique, so a retried write is answered from its row. `ordinal` is REAL, so a step can go between two.
- `db/table_roles.py` classifies both; neither is DERIVED, so no replayer. Replay and rebuild never read them: the attempt carries the evidence. The new import-linter contract `evidence-never-reads-the-workbench` keeps substrate, learner, attempts, scheduling, goals, diagnosis, placement, field and router from importing `learnloop.reader.workbench` or its store (23 contracts kept).
- **Head fixture** `migration_head_206 → migration_head_207`: a backup-API copy of the 206 database, only 207 applied under `upgrade_allowance(UPGRADE_TEST_HELPER)` (applied `[207]`), `wal_checkpoint(TRUNCATE)` → `(0, 0, 0)`, `journal_mode=DELETE` (header bytes 18-19 are 1/1), `integrity_check` ok, `foreign_key_check` empty, 0 rows in both tables, copied back with the backup API, no companion files. The README gains the 207 paragraph and the build chain. All 25 test files and both reference scripts name `migration_head_207` (`SCHEMA_HEAD = 207`), as does `docs/decider-tier1-migration.md`; the max-migration assertion in `test_route_rules_in_grader.py` is 207. `tests/test_coordinated_migrations.py` stays green (no new `Repository(...)` or `apply_migrations` caller in `src/`).

### 1.2 Backend

**`learnloop.reader.workbench`** (functional core, imperative shell):
- `default_book_visible(entry, origin)`: open for `work_through`, `resume`, `path_exercise` in the Reader; hidden for `check_me`, `practice_this`, `discriminating_problem`, `plan`; never off the Reader.
- `live_steps` folds the ledger into the work as it stands (each chain's newest version, in ordinal order, with its earlier texts newest first, deduplicated); `compose_answer` is the submit's answer.
- `record_line` states what the attempt will record, from the same `book_counted` the submit uses: *your own attempt*, or *book open · 1 hint → practice with help ◌ (not yet checked on your own)*, naming tutor questions when the existing fold adds them (G62); the footer *book open = 1 hint · help used: none*; and *Submitting now records 'stuck' — that's fine* before an empty stuck answer.
- The shell: `open_session` (resumes the open session for the same item, or the same selection, instead of opening a second; a retried key answers its own), `save_step`, `set_book`, `leave`, `abandon`, `reopen`, `mark_import`, `bind`, `submission_plan`, `mark_submitted`, and the reads `session_view`, `session_for_attempt`, `sessions_for_item`, `sessions_for_source` (`unfinished` past `open_session_days`, never closed).
- Every lifecycle change writes one salience-only `reader_action_invoked` with a payload `event`: `workbench_opened`, `workbench_resumed`, `workbench_left`, `workbench_closed` (`reason` abandoned or submitted), `workbench_reopened`, `workbench_bound`, `book_visibility_changed` (`visible`, `counts`, `after_first_step`). No new event kind, no new reveal kind.

**The book's rule (§5.4).** In the Reader the book counts as one hint-equivalent from the first step written with it shown, or from its first showing after a step (`source_shown_at`); flipping it before the first step is free; hiding it again never takes the hint back. A Reader session with no steps submitted with the book shown also counts it. Off the Reader there is no book (`set_book` refuses `no_book`).

**The RPCs** (`learnloop_sidecar/handlers/workbench.py`): `workbench.open`, `.get`, `.save_step`, `.set_book`, `.leave`, `.abandon`, `.reopen`, `.refresh_import`, `.bind`, `.retry_import`, `.submit`, `.session_for_attempt`, `.for_item`, `.for_source`. Each refuses `workbench_disabled`, before reading or writing anything, while `workbench.enabled` is off.
- **Opening at once (S2, G58).** On a selection, `open` stores the verbatim stem and enqueues the exercise import itself through `enqueue_exercise_import`, the code `reader.import_exercise` now shares (unchanged behaviour). An import that cannot start (no provider, the reader off) opens the session `failed` with its reason, steps writable. `refresh_import` reloads the vault once when the job completed (as `reader.exercise_import_status` does) and binds one item; several ask which part (`parts`; `bind` accepts only one of the job's own); none, or a failed job, is `failed` with *try again* (`retry_import` re-enqueues the stored request, also after a restart). Submit before binding refuses `not_bound`: "Submit is available once setup finishes."
- **Submit.** `submit_attempt` is now a thin RPC over `submit_attempt_on(ctx, params, entry_surface=...)`, and `submit_dont_know` over `submit_dont_know_on` (same for the stuck redirect). The workbench builds an ordinary `SubmitAttemptInput`: the composed answer, `hints_used` = the book's 0 or 1, the attempt type the answer box would pick (`stuck_attempt_type`: `hinted_attempt` with the book where the item allows it), `declared_stuck` for a stuck-only answer, the serve's `scheduler_candidate_id` and `plan_presentation_id` from the practice screen, and `submission_id = "workbench:<session>"` (one submit per session, so a lost response is answered from the receipt). The surface is `desktop_reader_workbench` (Reader) or `desktop_practice_workbench` (practice screen and plan), also on the submission intent. The practice session is the app's open one, else the most recent open one, else a new one (`start_session`). A refusal (a cold check answered with the book, grading unavailable) keeps the session open with its steps; a submitted session cannot be edited, abandoned or reopened.
- `get_practice_item`, `submit_attempt`, `save_practice_draft` and every other practice RPC are unchanged; the config DTO carries `workbench` only while it is on.

### 1.3 Confirming §5.4's mapping against `resolve_attempt_activity_policy`

| Assist (RW2a's rows) | Recorded as | `resolve_attempt_activity_policy` gives | Spec |
|---|---|---|---|
| Book visible in the Reader | `hints_used = 1`, `attempt_type = hinted_attempt` (where allowed) | `verification` class, `counts_as_assisted`, FSRS-eligible, `eligible_for_certification = False` | assisted: schedules, certifies nothing |
| Book hidden before step 1, no help | `hints_used = 0` | `verification`, not assisted, certification-eligible (unless near-clone) | an ordinary attempt |
| Stuck text, then Submit with steps | the steps are the answer, `declared_stuck = false` | as the book's row decides | — |
| Only stuck text / nothing | the existing written / empty "I'm stuck" answer (`declared_stuck = true`; empty is scored 0 with no model call) | the existing stuck semantics | §5.1 |
| Abandoned | no attempt | — | — |

Every RW2a assist maps onto fields with an existing meaning; no new discount or eligibility rule is needed, so **no successor**. (Checks and hints, `primed` for levels 4-5 and `help_assists` are RW2b's rows.)

### 1.4 The one eligibility decision (mvp-0.27)

A workbench submit is an ordinary submit, so `attempts._resolve_attempt_target` asks `serve_eligibility.decide(inputs, SUBMIT)` exactly as the practice screen's answer box does (the spy test counts the same number of SUBMIT decisions for both, with the workbench's `hints_used = 1, hinted_attempt`). A due cold check answered with the book open is refused (`COLD_CHECK_ASSISTED`, `validation_error`), the session and its steps stay, and the same problem with the book hidden is admitted. With `eligibility.enabled = false` the mvp-0.26 guard refuses it the same way. Nothing in the eligibility module changed.

### 1.5 Frontend

- **`screens/workbench/`**: `stepModel.ts` (the local list, book default by entry, the problem's title, the saved line, `WORKBENCH_COPY`), `splitWidth.ts` (half the window, min 480 px, the book keeps 360 px, stacked below 1,040 px, remembered under `ll.workbench.splitWidth` with try/catch), `useWorkbenchSession.ts` (the write queue: a 600 ms per-step debounce, one serial queue, each write's key kept across retries at 1, 2, 4, 8 s, the text read when the write runs, a failing write *not saved yet — retrying · your text is safe in this window*, a sidecar down *sidecar unreachable — keeping your steps here; they'll save when it's back*, never "error"; refusals a retry cannot fix are dropped and said; resting edits flush on blur, Submit, Leave and unmount; the import is polled every 2 s while pending), and `Workbench.tsx`.
- **The workbench** (W5, W8, W15): header *WORKING · Exercise 5.14 · from the book, verbatim* (without the book: *WORKING · Exercise 5.14*; after submit *SUBMITTED*), the setup line (*◐ setting up checks and hints for this exercise…*, the part chooser, *Setup didn't finish … Your steps are kept. try again ↵*), the problem in the source's voice, the book line before step 1 (a radiogroup: *● with the book open — practice beside the book (counts as one hint)* · *○ without it — your own attempt; you can open it any time*; typing the first step accepts it), *Your work* with *saved · just now*, steps `1 ›` in `LiveMarkdownEditor` (stuck steps in the learner's voice with *Write what you can, or what's confusing you. Being stuck here is useful information.*), *↺ your earlier versions* dimmed, *step 2 deleted · undo*, the record line and the stuck note above *I'm stuck · Submit · Leave for now*, `⋯` with *Abandon this problem* (no confirmation), *abandoned · your steps are kept · reopen*, the footer. Keys: ↵ at a step's end, ⇧↵, Alt+↑/↓, Ctrl+Backspace in an empty step, Ctrl+D, Ctrl+↵, Ctrl+Shift+B, Esc then Esc. Nothing a save, a poll or a result does moves focus; the only focus moves are the learner's (a new step, Alt+↑/↓, opening).
- **The Reader** (`useReaderWorkbench.ts`, `ReaderScreen.tsx`, `NotesRail.tsx`): *work through this ▸* in the capture's EXERCISES group and on each imported exercise; the working posture replaces the rail (kept mounted, hidden) with a resizable separator (drag or ←/→, `aria-valuenow`) and the pane at the remembered width; the book hidden is W8's cover over the source pane (`aria-hidden` on it); below 1,040 px the pane takes the screen and *show in the book ▾* opens the book in the lower half; no margin cues while working (RW3a's `working` seam, friction note 3); `✎` beside the first passage of each open or set-aside problem (*Resume this problem: Exercise 5.14*) and a line per problem in the rail (no count, UX U12); Leave, Abandon and Submit collapse back to reading at the problem's passage.
- **The practice screen** (D9, UX §5.12): *Work in steps*, beside the answer box and remembered once chosen (`ll.workbench.workInSteps`), opens the workbench full width under the item's own presentation; *answer box instead* forgets the choice; *resume your steps* or *reopen your steps* on the card; never on a diagnostic check, a teach-back, a guided redo or a primed retry; in steps the screen's own keys yield to the workbench. Submit uses this serve's candidate and presentation and lands on feedback.
- **Back from feedback** (S6, `app/readerWorkbench.ts`): a Reader workbench submit sets the app's practice session if the submit started one, keeps the way back (`ReaderReturn.workbenchAttemptId`), and opens feedback; Esc or b open the Reader at the problem, read-only, through `workbench.session_for_attempt`, and Esc there returns to reading at its passage; Next returns to reading at the passage; every other attempt goes back as today.
- **`LiveMarkdownEditor`** gains optional props only (`ariaLabel`, `focusable`, `compact`, `focusSignal`, `onKeyDown` with `{atEnd, empty}`, `onBlur`); without them it renders as before (tested). **The chords:** the editor binds no key of its own, so Ctrl+K (left free for RW2b's check), Ctrl+Shift+B, Ctrl+D and Ctrl+↵ never clash with it; the Reader's own Ctrl+Z (undo a removed highlight) ignores text fields.
- **Switched off**: `algoConfig().workbench` is false until the sidecar sends a `workbench` key, and every entry point is absent (no disabled ghost).

## 2. Gates and where they are tested

| Gate | Backend (`tests/test_reader_workbench_rw2a.py` unless named) | Frontend |
|---|---|---|
| **G5** (the book's rows and no help) | `the_book_open_in_the_reader_is_one_hint_and_the_attempt_is_assisted`; `the_book_hidden_before_the_first_step_is_the_learners_own_attempt`; `flipping_the_book_before_the_first_step_is_free`; `opening_the_book_after_a_step_counts_from_then_on_even_if_hidden_again`; `an_abandoned_session_writes_no_attempt_and_a_rebuild_leaves_the_workbench_alone` (two rebuilds leave the attempt, its grading evidence and both workbench tables identical); `the_lifecycle_writes_only_workbench_rows_and_salience_only_events`; `every_workbench_event_is_salience_only` (7) | — |
| **G6** blind grader | `the_grader_reads_the_composed_answer_only` (no superseded version, tombstone, stuck text, session id or record line in what the grader received) | — |
| **G10** source visibility | the G5 rows above, plus `the_practice_screen_never_shows_the_book_and_records_its_own_surface`, `submit_uses_the_open_practice_session_or_starts_one`, `a_retried_submit_answers_the_same_attempt` | `Workbench.test.tsx` (the book line, Ctrl+Shift+B), `ReaderScreen.workbench.test.tsx` (W8 cover) |
| **G11** kill switch | `switched_off_every_workbench_rpc_refuses_and_writes_nothing` (14 RPCs); `switched_off_the_config_and_the_practice_rpcs_are_what_they_were` | `switchOff.test.tsx` (4): the practice screen, the Reader and its notes rail match the snapshots written on the base frontend, with no `workbench` key and with `enabled = false` |
| **G32** resume | `steps_save_as_typed_with_versions_tombstones_and_idempotency_keys`; `a_step_added_after_another_takes_its_place_and_a_stale_id_edits_the_newest_version`; `steps_and_the_book_survive_a_sidecar_restart`; `leave_keeps_it_open_abandon_closes_it_reopen_opens_it_and_none_writes_an_attempt`; `a_submitted_session_cannot_be_reopened_or_edited` | `Workbench.test.tsx`: saving as typed, retry with the same key, sidecar down, flush before submit, Esc Esc; `ReaderScreen.workbench.test.tsx`: the ✎ mark and rail line resume where it was, Leave keeps it resumable; `PracticeScreen.workbench.test.tsx`: resume / reopen your steps |
| **G58** opens at once | `a_selected_problem_opens_at_once_and_steps_save_before_the_import_binds`; `a_multi_part_import_asks_which_part_and_binds_only_one_of_its_own`; `a_failed_import_keeps_the_steps_writes_no_attempt_and_tries_again` (and after a restart); `an_import_that_cannot_start_opens_the_session_failed_with_the_steps_writable`; `the_default_book_visibility_follows_the_entry` (9); `an_opened_session_starts_with_its_entrys_book`; `the_session_for_an_attempt_is_found_for_a_workbench_attempt_and_nothing_else` | `Workbench.test.tsx`: Submit waits and says so, the binding lands without moving focus, try again, the part chooser; `ReaderScreen.workbench.test.tsx`: opens at once beside the book, back from feedback read-only then Esc to reading; `readerWorkbench.test.ts` (3): Esc/b to the problem, Next to the passage, every other attempt as today |
| Eligibility composition | `a_workbench_submit_asks_the_same_eligibility_decision_as_every_submit`; `a_cold_check_with_the_book_open_is_refused_and_the_session_and_steps_stay`; `with_the_eligibility_switch_off_the_old_cold_guard_still_refuses_the_book` | `Workbench.test.tsx`: a refused submit keeps the steps and says why |
| Migration, roles, config | `migration_207_creates_both_tables_with_every_check_value`; `both_tables_are_classified_and_never_derived`; `the_kill_switch_and_open_session_days_default_on_and_30`; `test_config_refactor.py` (the nineteen snapshots); `test_table_roles.py`; `test_migrations.py`; `tests/test_mobile_allowlist.py` (14 pins) | — |
| Stuck | `an_empty_submit_is_the_existing_empty_stuck_answer_with_no_model_call`; `stuck_text_stays_learner_work_and_the_steps_are_an_ordinary_answer`; `only_stuck_text_is_submitted_as_the_existing_written_stuck_answer` | `Workbench.test.tsx`: Ctrl+D, the stuck note |
| G54 attention (the workbench's part) | — | `attentionBudget.test.tsx`'s lint now covers `screens/workbench/*.tsx` (no animation, no transition); focus unchanged when a binding lands; no dialog on Abandon |

**Fail-first evidence.**
- Backend: `tests/test_reader_workbench_rw2a.py` failed at collection on the base (no `learnloop.reader.workbench`), and 14 of the mobile pins failed (unregistered RPCs), committed as `49065fa71`. Two tests were tightened after the implementation, each recorded: the rebuild test compares the evidence and workbench tables instead of a whole DERIVED fixed point (the shared post-attempt worker's recurrence fingerprint moved between two wall-clock rebuilds, unrelated to RW2a), and the eligibility spy compares the workbench's SUBMIT decisions with the answer box's (the submit path asks the decision more than once, the same number of times on both).
- Frontend (`048acbaed`): the switched-off snapshots were written on the base frontend; on the base, the step model, workbench and App helper failed at collection, 3 of 4 editor tests, 5 of 6 practice-screen tests and 8 of 8 Reader tests failed (the passing ones were the unchanged editor and "a diagnostic check never offers it", both right before RW2a). After the implementation two test harness changes were needed and are recorded: a memory `localStorage` (jsdom's is shadowed in this Node, as in `ReaderScreen.parity.test.tsx`), and longer timeouts on the debounced saves; one assertion now finds the stem in the source column and the pane separately; the header is found by test id rather than as a `banner` landmark.

## 3. Decisions taken within the spec, and deviations

1. **Five columns beyond §5.7 on `workbench_sessions`**: `import_batch_id`, `import_request_json`, `import_error` (the import a session waits on, so binding and *try again* survive a restart), `source_shown_at` (when the book first counted, since `source_visible` is only the current choice and `source_hidden_at` the last hiding) and `client_idempotency_key`. Additive; no spec column is changed.
2. **A stuck-only submit** (stuck text and no ordinary step) is the existing *written* "I'm stuck" answer (`declared_stuck = true`, graded), the natural reading of §5.1 next to §5.4's "stuck text, then Submit" row (which has steps). An empty one is the existing empty stuck answer.
3. **Check me (RW3a) opens in the Reader's working posture** (D40; added by the Codex review's F12, `docs/reviews/reader-rw2a-codex-review.md`): `plan_learner_pick` as before, the item served once as the practice screen served it, then entry `check_me` with the book hidden, answering the pick's candidate and presentation. With the workbench off it opens on the practice screen as before.
4. **The rail's tabs do not fold into the workbench header's `⋯`**: the rail is hidden while working and returns, as it was, on leaving. The `⋯` holds Abandon.
5. **The `✎` mark is drawn on the extracted-text view only**; on the original PDF and on a transcript the rail's line is the resume entry. **"original page ↗"** in the header is not built.
6. **Exposures.** The book's visibility changes are recorded as `book_visibility_changed` events with whether it counts, and every showing of the book (the initial visible opening included) records `source_exposure_events` on the anchored spans, context `reader` (review F11).
7. **No answer-confidence row** in the workbench yet (D22; `workbench.submit` accepts `answerConfidence`): open question 3.
8. **Grading unavailable**: a workbench submit says so and keeps the steps; it offers no self-grade (the answer box's fallback). Open question 2.
9. **Leave on navigation**: navigating away or closing keeps the session open and flushes resting edits; the `workbench_left` event is written by the explicit Leave (button or Esc Esc), not by an unmount.
10. **The record line's tutor-question count** uses the session's practice session, else the most recent open one, the same session the submit would use.
11. **A multi-part import** binds the part the learner picks; the other parts stay ordinary items.
12. **The practice screen's Leave for now** returns to the answer box (the problem stays resumable from the card).

## 4. Friction audit (G52) for the workflows RW2a touched

| Workflow | Before RW2a | After |
|---|---|---|
| Work a textbook exercise | Select, *add exercise to practice*, wait for the import, find the item in the queue, answer it on the practice screen, away from the book | Select, *work through this*: step 1 at once beside the book; setup binds in the background |
| Come back to a half-done problem | Not possible (the practice draft lives only in the session checkpoint) | `✎` beside the passage, the rail's line, *resume your steps* on the card; same steps, same book choice |
| Decide whether the book counts | Not stated anywhere | One line before step 1, and the record line before Submit |
| Back from feedback | To the queue or the plan | To the problem (read-only), then the passage |

Keyboard reachability: every new action has its key (UX §3.5), the separator is a focusable `separator` with arrow keys, the mark and rail lines are buttons.

## 5. Friction notes for RW6a and RW2b

1. **RW6a's recap** reads `workbench.for_source` (open and abandoned, `unfinished` past `open_session_days`, `stepCount`, `updatedAt`); resume is `workbench.get`, reopen `workbench.reopen`. Nothing to add server-side.
2. **RW2b's fold at Submit** belongs in `workbench.submit`: today `hints_used` is the book's 0/1; add one per shown check and level 1-3 hint from `help_assists`, and `primed` for levels 4-5, in `learnloop.reader.workbench.submission_plan` (so the record line and the submit keep one source).
3. **Step identities for `step_snapshot_json`**: a step's stable id is its `chainId` (first row); `stepId` is the newest version. Checks should snapshot `(chainId, stepId, sha(body))`.
4. **Room in the step row** for the verdict column: each step is a flex `li`; a 120 px column fits after the editor. Ctrl+K is free.
5. **`ReaderScreen.tsx` is 2,760 lines** (RW2a added about 190 of layout); the working posture's block (cover, separator, pane) could become `ReaderWorkingPosture.tsx` before RW2b adds the ladder.
6. **The `✎` and the cue mark share the gutter**; a passage with both shows both at the same offset. RW3b should offset one.
7. **The write queue retries forever while the workbench is open** (backing off to 8 s) and five more times after it closes; a durable local outbox (as the Reader's annotations have) would keep unsaved steps across an app restart with the sidecar down.

## 6. Open questions (with the default taken)

1. *Check me* from a cue in the Reader's working posture, book hidden (D40)? **Built in the review fix step (F12), keeping `plan_learner_pick`.**
2. A self-grade fallback in the workbench when AI grading is unavailable? **Default: no; the refusal says so and keeps the steps; the answer box still has its fallback.**
3. The optional answer-confidence row before Submit (D22)? **Default: add with RW2b's submit-line work.**
4. A stuck-only submit as the written "I'm stuck" answer (decision 2)? **Default: as built.**
5. The rail's tabs in the workbench's `⋯` (decision 4)? **Default: with RW2b, if the ladder leaves room.**

## 7. Owner-run commands

None needed: RW2a makes no model call of its own. To try it on a backup copy (never the tracked vaults), make a copy with `learnloop.db.copies.copy_tree_with_databases` into `fixtures-local/`, then `LEARNLOOP_VAULT=<abs path to the copy> npm run dev` from `apps/learnloop-tauri`; *work through this* on a selection starts the existing exercise import on its own route and caps. `uv run learnloop doctor --fix-state --vault <copy>` after manual edits.

## 7a. Codex review

Twelve findings (nine High) were fixed or answered in `docs/reviews/reader-rw2a-codex-review.md`: the presented contract and the item's whole presentation, carried hints, the cross-surface resume, the write queue (frozen payloads, refusals held, the book serialised, Abandon, a vault switch and closing all drained), the lost submit receipt, the book's exposures and check me in the Reader. Migration 207 gained `assessment_contract_version_id` and `carried_hints` and the head fixture was rebuilt. The gate below is this stage's first run; the review file records the gate after the fixes.

## 8. Gate

Run in the worktree with `TMPDIR` set to `fixtures-local/tmp`.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **23 kept**, 0 broken (22 on the base plus `evidence-never-reads-the-workbench`) |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto` | **12,861 passed**, 2 xfailed, 0 failed (1,210 s), on `3c996b1a8`. The first run on `e6fd14844` had 10 failures, all the gate fixes above: the parameter registry's unclassified `workbench.open_session_days` (8, including `test_p0_cutover_mvp08`'s audit), the SQL-owner registry (1) and the forecasts landing test's head pin (1) |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -m durability` | **106 passed**, 12,757 deselected (113 s) |
| `npm install`, `npm run typecheck` | ok, clean |
| `npm test` (vitest) | **108 files, 866 tests passed** (48 new: switchOff 4, stepModel 7, Workbench 16, LiveMarkdownEditor 4, Reader workbench 8, practice screen 6, App helper 3) |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` | finished, exit 0 (fourteen passthroughs) |
| `db_generate_reference.py`, `db_validate_reference.py`, `validate_vault.py` | regenerated (head 207, 327 table notes, 863 configuration leaves in 54 sections); errors []; passed, 1,115 notes |
| `tests/test_config_refactor.py` (nineteen snapshots, template `.pyc` cleared), `test_cli_help_snapshot.py`, `test_sidecar_serializer_snapshot.py`, `test_desktop_rpc_contract.py`, `test_coordinated_migrations.py` | pass; CLI help and the serializer snapshot unchanged |

**Not done:** no real-UI look (optional; the screens are exercised through the real `ReaderScreen` and `PracticeScreen` in jsdom).

## Landing onto main

Landed in the `learnanything-merge2` worktree on branch `merge/rw2a-onto-main`. The stage's base and main's tip are both `9cdaefb9e` (mvp-0.27, schema head 206). The stage's tip is `9f640a0a6` (21 commits), unchanged. Main was neither fast-forwarded nor pushed here.

**Commits:**
- `1c3f440b3`: a real `--no-ff` merge of `reader/rw2a` onto `9cdaefb9e`. The merged tree is byte-identical to the stage tip's (`git diff 9f640a0a6 1c3f440b3` is empty).
- `da62f32c0`: the references regenerated on the merged tree.
- This record.

### Merge

- **No conflicts.** Main had not moved since the stage's base, so migration 207 stays 207 and `fixtures/migration_head_207` keeps its paths.
- **No algorithm successor** (§5.9): the vaults' labels and the Pipeline Map's `implementation_version` stay as they were. One config section (`[workbench] enabled`, `open_session_days`), fourteen `workbench.*` RPCs (desktop only, pinned off the phone), fourteen Tauri passthroughs.

### Regenerated

- **References.** `db_generate_reference.py`, then `db_validate_reference.py`: **0 errors**, `schema_head` 207, 327 table notes. 383 notes' `source_commit` and `source_commit_timestamp` labels moved. Content: the two `workbench.*` leaves' line citations in `src/learnloop/reader/workbench.py` (rounds 3-4 moved them) and the test list of one note. Committed as `da62f32c0`.
- **Defaults snapshots.** The template `.pyc` was deleted and `template.py` touched. All 19 `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries equal `defaults_fingerprint_for_version`: **0 mismatches**.
- **CLI help snapshot.** Rewritten with `python tests/test_cli_help_snapshot.py --write`: no change.
- **The Pipeline Map.** The stage's RW2a bullet is already there; nothing to add (no successor, so no version or gate change). `validate_vault.py` passes (1,115 notes, 1,113/1,113 reachable).
- **Head fixture.** `fixtures/migration_head_207/state.sqlite` is rollback-mode (header bytes 18-19 are 1/1, `journal_mode=DELETE`), with no `-wal` or `-shm`.

### Gate

Run on `da62f32c0`, the final code tree; the only later commit adds this section. Python 3.12.14, `TMPDIR` set to merge2's `fixtures-local/tmp`, `uv run --no-sync` after the install; both suite lanes under `flock /tmp/learnloop-fullsuite.lock`. No paid call: every test uses fakes.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `lint-imports --no-cache` | **23 kept**, 0 broken |
| `pytest -n auto -q -p no:cacheprovider` (full suite) | **12,879 passed, 2 xfailed**, 0 failed (15 min 30 s; `fixtures-local/rw2a-landing-fullsuite.log`) |
| `pytest -m durability` | **106 passed**, 12,775 deselected (1 min 55 s) |
| `npm install`, `npm run typecheck` | ok, clean |
| `npm test` (vitest) | **108 files, 901 tests passed** |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path src-tauri/Cargo.toml` | finished, exit 0 (`src-tauri` differs from main: the passthroughs) |
| tracked fixtures | `git status` clean after both lanes |

The counts equal the stage's round-4 gate on `0947b8fce`. Nothing failed, so nothing was rerun; `test_mcp_c1a_review.py`'s known `"8841"` flake did not fire.

### Parity (backup-API copies; no model call)

**Setup:**
- **Copies.** The owner's `fixtures/linear_algebra` and `fixtures/probability` (with probability's `.learnloop/state.sqlite`) were copied with `copy_tree_with_databases` from the main checkout into `fixtures-local/landing-rw2a/orig/`. Each original was read once; every other copy came from `orig/` or another copy through the same helper. `arxiv_v2` was not opened.
- **Code.** Main's code is `git archive 9cdaefb9e` and the merge's is `git archive da62f32c0` (each without the top-level `fixtures/`), each first on `PYTHONPATH`; every run printed the `learnloop` package it imported.
- **Environment.** `LEARNLOOP_CONFIG_DIR` was an empty directory, `LEARNLOOP_AI_PROVIDER` unset, the sidecar started with a working directory holding no `.env`. `model_call_receipts` is 0 in every copy.
- **Starting state.** Both vaults at schema 165, label `mvp-0.8`; linear_algebra has 70 attempts, probability 2.
- **Cleanup.** The previous landing's `fixtures-local/landing-eligibility/` (2.8 GB) was deleted once these copies existed, behind guards on the exact path, that git ignores it, that it holds no tracked file, nothing in it modified in the last 30 minutes (`-mmin`), and no process working in it.

| Check | linear_algebra | probability |
|---|---|---|
| **(a)** open (migrate), main's code / the merge's | 165 → 206 (41) / 165 → 207 (42); main's `sqlite_master` hash `7b8f3398f1fed234`, as at the last landing | 165 → 206 (41) / 165 → 207 (42); `84e519863059c42f` |
| `.dump`, main's vs the merge's, outside the two new tables and the `schema_migrations` stamps | **identical** (17,443 lines). Excluded on the merge's side only: the 207 row, the two tables, their five indexes and two triggers | **identical** (8,541 lines), same exclusions |
| `rebuild --shadow --json`, main vs merge | **0 differences** besides the live file's sha256 and the marker id (facet 0, mastery 2, schedule 8; live unchanged) | **0 differences** (facet 0, mastery 1, schedule 1) |
| `doctor --json`, main vs merge | **0 differences** (57 issues, 1 error) | **0 differences** (101 issues, 48 errors) |
| **(b)** upgrade shadow: main's code migrates to 206, then the merge's opens it | the merge's code applies **207 only** (206 → 207); `.dump` equals main's outside the new tables, and equals the directly migrated merge copy | **207 only**; equal |
| shadow and doctor on the upgraded copy vs main | **0 differences** (sha and marker id only) / **0** | **0** / **0** |
| the two new tables | 0 rows in `workbench_sessions` and `workbench_steps` on every 207 copy | 0 rows |

Every shadow and doctor run left its live database byte-identical (sha256 before and after).

**(c) The kill switch, through the real sidecar.** A 207 copy of linear_algebra with `[workbench] enabled = false` appended (`config effective` shows `{"enabled": false, "open_session_days": 30}`) was opened over stdio (`initialize`, `get_config`), and each of the fourteen `workbench.*` RPCs was sent once. All fourteen refused `workbench_disabled`, `get_config` carried no `workbench` key, and the database's `.dump` hash was the same before and after the fourteen calls (both tables 0 rows). A control copy with the switch on carried the key, and the same calls reached the handlers (`not_found` for the placeholder ids, the three reads answered), also writing nothing.

### For the owner

- **No upgrade command.** RW2a has no successor; the vaults keep their label.
- **The migration applies on the next open** by the new code (206 → 207: two empty tables, nothing else changed, shown above). Before that first open, close the desktop app, the MCP runtime and the mobile host, and back up each vault with the backup API, for example from the repository root: `uv run python -c "from pathlib import Path; from learnloop.db.copies import copy_tree_with_databases as c; c(Path('fixtures/linear_algebra'), Path('fixtures-local/backup-linear_algebra-pre-207'))"` (the same for `probability`; its copy includes `.learnloop/state.sqlite`). Rolling the schema back is restore-only: restore that backup.
- **Turning it off:** add `[workbench]` / `enabled = false` to the vault's `learnloop.toml`. Every workbench entry disappears, every workbench RPC refuses and writes nothing, and the practice screen is as before (shown above and by the stage's snapshot tests). Steps already saved stay in the tables, unread.
- **Open questions (defaults taken):** the stage record's §6 (1 built; 2 no self-grade fallback in the workbench; 3 the answer-confidence row with RW2b; 4 a stuck-only submit as the written "I'm stuck" answer; 5 the rail's tabs with RW2b) and the Codex review's 1-5 (`carried_hints` folded into `help_assists` when that table exists; a practice-screen problem resumed in the Reader opens book hidden; a failed close save holds the window once; a book counted on an open problem counts on its answer box, not on an abandoned one; a failed `workbench.for_item` lookup lets the answer box submit).
- **Deferred conformance items** (none changes what is recorded): the *original page ↗* link; the `✎` mark on the original PDF and transcripts (the rail's line is the entry there); the rail's tabs in the header's `⋯`; scrolling to the last edited step on resume (`lastEditedStepId` is sent); newly returned step versions merged into *earlier versions* before a reopen; the answer-confidence row; a durable local outbox for unsaved steps across an app restart with the sidecar down (friction note 7); splitting `ReaderScreen.tsx`'s working posture out before RW2b (friction note 5).
- **Pre-existing, unchanged here:** the `"8841"` flake in `test_mcp_c1a_review.py` (did not fire); the vaults are still at mvp-0.8 (the two-command mvp-0.27 upgrade from the eligibility landing still applies if the owner wants it).
