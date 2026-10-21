# Reader RW7a: Codex review and fix round 1

Codex job `20261021-014015-qgX3JQ` (read-only sandbox; it could not run `uv`,
so its test counts were not reproduced). Branch `reader/rw7a` in
`learnanything-rw4b`, base main `a76c8358a`. Every finding was reproduced
first with a test that failed on `5fddecf7d` and passes on the fix.

## Review

### Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | A learner-gap commitment can become "assumed known" | fixed | 65d05c98a | `test_f1_a_learner_gap_commitment_is_never_assumed_known`. Placement's `_commitment_decisions()` puts these commitments into `open_by_lo`, and the old status read `assumed=True` with zero `assumption_decisions` rows. `open_assumption_rows()` now counts only open assumptions whose id is an actual `assumption_decisions` row. A real assumption next to a commitment still counts. |
| F2 | Medium | "Try it" opens a truncated problem | fixed | 65d05c98a | `test_f2_try_it_carries_the_whole_exercise_and_only_the_preview_is_clipped`. The old `statement` was 600 characters and dropped the closing condition. `statement` is now the whole exercise; it is ReaderScreen's `stemMd`, which the workbench shows while the import is pending and for good if it fails. A new `preview` field holds the clipped text, and the DTO documents both. The import selection already spanned the whole statement (asserted). |
| F3 | Medium | A ready path never refreshes as the learner reads | fixed | 65d05c98a | `ReadingPathCard.test.tsx` "a ready card reads the path again when what it depends on changes, without a remount" and "the refresh key ..."; `readingPathsReader.test.tsx` "a ready path is read again when the Guide is shown again, without a remount" (fails with the ReaderScreen wiring removed). The card takes a `refreshKey` from `readingPathRefreshKey`. The key covers sections finished or fully seen (the server's own `_done` rule), plan re-reads (a diagnosis landing), quick checks answered, workbench sessions submitted or set aside, and the Guide shown again. The re-read is debounced by `READING_PATH_REFRESH_MS` (2 s), which is longer than `SEEN_REPORT_MS` so the progress save lands first. |
| F4 | Medium | A daily-budget refusal survives the next day | fixed | 65d05c98a | `test_f4_a_budget_refusal_is_reconsidered_when_the_day_turns_or_the_cap_changes` (same context, UTC day rollover at the same cap) and `test_f4_raising_the_cap_or_pricing_the_route_lifts_the_refusal_in_the_same_context` (unpriced, then capped, then a raised cap). Admission refusals (`ADMISSION_REASONS`: capped, unpriced, unrouted, models_off) are no longer kept: each read calls `admission_problem()` against today's envelope and the loaded config, before any call. A lifted refusal is dropped and the path is judged; one still in force is kept with today's wording. Model failures (`judge_failed`) keep their explicit "try again" and are not re-called on their own (asserted). |
| F5 | Medium | The cache key leaves out inputs that change the judgment | fixed | 65d05c98a | `test_f5_a_role_proposal_the_role_switch_and_title_edits_rejudge_a_cached_path`. `state_key` now also hashes the whole canonical prompt (`judgment_input`): roles, LO titles, the goal title and the depth wording. Each of these triggers one re-judgment: an RW4e proposal added, an LO retitled, a goal retitled. With `roles.positive_filter_enabled` off, the prompt is the same as before the proposal, so the path is the earlier cached one (no call), never the one built from the proposal. |
| F6 | Medium | Concurrent sidecars can pay for the same judgment twice | fixed | 65d05c98a | `test_f6_two_sidecars_opening_one_uncached_path_pay_for_one_judgment` uses a barrier: two threads, each with its own vault load and `Repository`. The first holds the call open while the second finds the claim held and waits. Result: one model call, one top-level receipt, claim `done`, second result `fresh`. A second test, `test_f6_a_failed_judgment_gives_its_claim_back`, checks that a failed call releases its claim and a retry completes it. The judge takes a durable leased claim in `judgment_work_claims`, the shared judge's existing pattern with no migration: (1) one claim per (reading, depth, state key), taken in a write transaction that first re-reads the cache; (2) the call runs under a heartbeat; (3) the write happens only while `holds_claim`, then `complete_claim`; (4) on any other outcome the claim is released. A second process waits on a held claim (up to `CLAIM_WAIT_SECONDS`, then `held`, which the handler treats as "not failed") and reads the first one's rows. |

**Non-numbered claim ("the two depth controls stay one setting").** This is
recorded as working as intended, with no change. The Guide writes only
`reader_path_depths`, and DL2's intent is read-only. That follows orchestrator
note 7: nothing in RW7a writes DL2's commitments, so what DL2 serves does not
change. The docstring already says the mapping is display-level, with the newer
of the two choices governing the path. If the owner wants the Guide's choice to
write DL2's intent, that is a DL2-side decision for its checkpoint.

**Spec-conformance note ("merged sources-spec candidates omitted").** Out of
scope for this fix step; no change. RW7a names a section-local exercise block,
as built.

### Files changed

- `src/learnloop/source_retrieval/reading_paths.py`: `open_assumption_rows`,
  `state_key`'s `judgment_input`, `exercise_view`'s `preview`,
  `ADMISSION_REASONS` / `admission_problem`, and the claim (`CLAIM_TASK`,
  `claim_key`, `_acquire`, `_heartbeat`, `_release`, `_judge_claimed`).
- `src/learnloop_sidecar/handlers/reading_paths.py`: `_readmit`, and `held`
  treated as "not failed".
- `apps/learnloop-tauri/src/screens/reader/ReadingPathCard.tsx`:
  `refreshKey`. `readingPath.ts`: `READING_PATH_REFRESH_MS`,
  `readingPathRefreshKey`. `ReaderScreen.tsx`: the key's signals.
  `api/dto.ts`: `preview`.
- Tests: `tests/test_reading_paths.py` (+7 tests),
  `tests/reading_path_fixtures.py` (`units=` and the fake's `output_tokens=`),
  `ReadingPathCard.test.tsx` (+2), `readingPathsReader.test.tsx` (+1).

There are no new config keys (nothing to classify in the parameter registry),
no migration, no new RPC, and no CLI or serializer change. No live or paid
model call was made; everything ran on fakes. No vault copy was used.

### Gate (fix round 1)

- `uv sync --extra dev --extra mobile`: ok. `uv pip install pypdfium2`:
  pypdfium2 5.14.0.
- `uv run lint-imports --no-cache`: **28 kept, 0 broken**.
- `TMPDIR=fixtures-local/tmp uv run pytest -n auto` over these targeted files:
  **460 passed**.
  - `tests/test_reading_paths.py`
  - `tests/test_reader_rw7a_migration.py`
  - `tests/test_architecture.py`
  - `tests/test_mobile_allowlist.py`
  - `tests/test_compare_keep_switch_off.py`
  - `tests/test_reader_tutor_switch_off.py`
  - `tests/test_reader_intent.py`
  - `tests/test_reader_intentions.py`
  - `tests/test_rw4_kill_switches.py`
  - `tests/test_judge_routes.py`
  - `tests/test_table_roles.py`
  - `tests/test_coordinated_migrations.py`
  - `tests/test_tracked_fixture_databases.py`
  - `tests/test_sqlite_file_copies.py`
  - `tests/test_desktop_rpc_contract.py`
  - `tests/test_sidecar_serializer_snapshot.py`
  - `tests/test_cli_help_snapshot.py`
  - `tests/test_learner_text_gaps.py`
  - `tests/test_reader_active_reading.py`
- `tests/test_reading_paths.py` alone: **47 passed** (40 before, plus 7 new).
- Durability lane: not applicable (no migration, no DB or connection code
  changed; the claim reuses migration 176's table through its store).
- Frontend (`apps/learnloop-tauri`): `npm install` ok; `npm run typecheck`
  ok; `npm run frontend:build` ok.
- `npx vitest run`: **41 files, 291 passed**. These are every test file that
  renders `ReaderScreen` or imports `ReadingPathCard` / `readingPath`:
  - `App.wrapUpSkim`, `attentionBudget`
  - `ReaderScreen.{branches, checkOffer, cuesSwitchOff, discoveredCues,
    discoveredCuesReview, followsLearner, guide, inquiry, inquiryOff, k7,
    marginMarks, marginMarksReview, parity, pdfSelection, preparing,
    quickcheck, recap, recapReview, review, workbench}`
  - `reader/{IntentBox, ReadingPathCard, compareKeep, compareKeepSwitchOff,
    intentSwitchOff, libraryAsk, libraryAskSwitchOff, libraryExercisesReader,
    libraryRoles, nextStepFold, readingPathsReader, readingPathsSwitchOff,
    recapSwitchOff, rw1bReview, tutorBoundAsk, tutorExercises, tutorReader,
    tutorSwitchOff}`
  - `workbench/switchOff`
- `cargo check`: not applicable (no `src-tauri` change). References and
  snapshots: not applicable (no schema, config, CLI or RPC change).

**Process note.** One plain text-edit `python3` script (string replacement in
`tests/reading_path_fixtures.py`, no learnloop import, no network) ran outside
`env -i`. All later edits used the editor tools or `node` text scripts.

## Re-review (Codex job 20261021-020351-qET0p4)

Codex confirmed F1 fixed and reopened F3; it found no new defects in the fix
diff.

| id | severity | title | verdict | commit | test or reason |
|----|----------|-------|---------|--------|----------------|
| F1 | High | "assumed known" from synthetic learner-gap commitments | confirmed fixed by Codex (fixed in 65d05c98a) | 65d05c98a | `tests/test_reading_paths.py` (unchanged this round, 47 passed) |
| F3 (reopened) | Medium | a ready path card can keep a stale "next": the timed refresh reads progress whose save the learner's further reading postponed, and nothing reads again after the save lands | fixed | 142fb9bdd | `apps/learnloop-tauri/src/screens/reader/readingPathsRefresh.test.tsx` (2 tests, both failed before the fix) |

**Reproduction.** `readingPathsRefresh.test.tsx` drives `ReadingPathCard` with
the real `useReadingProgress` hook, with the refresh key built the way
`ReaderScreen` builds it, against a fake server whose `next` moves only with
the progress it was sent. It follows Codex's scenario: section A is read
through at 0 ms, so the refresh is due at 2,000 ms. Partial reading in B at
1,000 ms moves the save to 2,500 ms. The test checks that the timed refresh
still sees A unsaved, then that the save lands. On 5044bc86d both tests
failed on the final assertion (`Next: read Section B` was never shown). The
second test covers a save that fails once and lands on its timed retry.

**Fix.** `sendSeenCounts` takes an `onSaved` callback, called on every
acknowledged count. Retries pass the callback through. `useReadingProgress`
counts the open book's acknowledged saves as `progressSaves`. A save that
lands after the learner has left the book is not counted.
`readingPathRefreshKey` now requires `progressSaves` as a typed input, so
`ReaderScreen` has to pass it. When a save lands, the key changes and the
mounted card reads the path again after the usual 2,000 ms debounce. The
reads this adds cost no model call. Reading progress is not in the server's
`state_key`: `next` is worked out from progress when the path is read, and
the judgment is cached by depth, sections, LO statuses, goal and prompt. The
older "section done" trigger stays, so the common case still needs only one
read. The key's string form gained a `saved:<n>` component, and the key unit
test in `ReadingPathCard.test.tsx` was updated to match.

### Re-review gate

- `uv sync --extra dev --extra mobile`: ok. `uv pip install pypdfium2`: ok.
  `TMPDIR` was the worktree's `fixtures-local/tmp`.
- `uv run lint-imports --no-cache`: **28 kept, 0 broken**.
- No Python changed this round. As a sanity check,
  `uv run pytest -n auto tests/test_reading_paths.py`: **47 passed**.
  Durability, references, snapshots, CLI help and RPC pins: not applicable
  (no schema, config, CLI, RPC or DB change).
- Frontend (`apps/learnloop-tauri`): `npm install` ok; `npm run typecheck`
  ok; `npm run frontend:build` ok.
- `npx vitest run`: **45 files, 326 passed**. These are every test file that
  renders `ReaderScreen` or imports `useReadingProgress`, `ReadingPathCard`
  or `readingPath`, plus the new file:
  - `App.wrapUpSkim`, `attentionBudget`
  - `ReaderScreen.{branches, checkOffer, cuesSwitchOff, discoveredCues,
    discoveredCuesReview, followsLearner, guide, inquiry, inquiryOff, k7,
    marginMarks, marginMarksReview, parity, pdfSelection, preparing,
    quickcheck, recap, recapReview, review, workbench}`
  - `reader/{IntentBox, ReadingPathCard, checkOffer, compareKeep,
    compareKeepSwitchOff, intentSwitchOff, libraryAsk, libraryAskSwitchOff,
    libraryExercisesReader, libraryRoles, nextStepFold, readerHooks.parity,
    readingPathsReader, readingPathsRefresh (new), readingPathsSwitchOff,
    recapSwitchOff, rw1bReview, tutorBoundAsk, tutorExercises, tutorReader,
    tutorSwitchOff, voices}`
  - `workbench/switchOff`
- `cargo check`: not applicable (no `src-tauri` change).

**Process note.** One empty `python3` heredoc ran outside `env -i`. It was a
no-op placeholder with no code, no import and no network. Every edit in this
round used the editor tools or `sed`.

## Fix round (orchestrator)

The whole-stage verify, Codex job `20261021-081146-cZ35am` (read-only;
`a76c8358a..bb2a75f85`), confirmed these points:

- serving isolation;
- the override and depth writes;
- no skip-to-known;
- no DL2 writes;
- honest labels (312 input combinations);
- migration 217 and the head fixture.

It reopened the stage with three Highs. The orchestrator's rulings and what
was done:

| id | severity | title | ruling | commit | test |
|---|---|---|---|---|---|
| V1 | High | A cached reason can disclose material withheld since | fix | 7e0641fee | `test_fix_a_cached_reason_quoting_a_section_held_out_since_is_never_shown`; guard `test_fix_a_judgment_whose_sections_are_all_still_sendable_keeps_its_model_lines`; vitest `ReadingPathCard.test.tsx` "a code-written line on a core section is never labelled the model's reading" |
| V2 | High | Switched off, the reader report still has `reading_paths` | fix | 7e0641fee | `test_fix_switched_off_the_reader_report_is_a76c8358a[empty_tables]`, `[populated_tables]` |
| V3 | High (ruled Low) | Switched off, the disclosure registry, `get_settings` and `eval judges` still list `reading_path_judge` | no change | none | none (see below) |

**V1 (ruling 1).** The input set comes from what is already stored, so
there is no new column and migration 217 is unchanged. `validate` answers
every section the judge was sent and writes one judge row per section, all
in one transaction. The table is append-only. A state key's judge rows are
therefore exactly the prompt's section list (`judged_sections`).

`reasons_held_back(rows, inputs)` is true when one of those sections is
missing from today's sendable list. A withheld section (held out, or exam
material) is missing for that reason. The check is fail closed: a section
missing for any other reason also counts. When it is true, `path_view`
shows code's line in place of every stored reason from that judgment: the
evidence lines for already shown and assumed, otherwise the default line for
the label ("Central to what you want from this book at this depth."). It
does this in the stale view, while the path is re-judged, and after a
failed re-judge.

Each section gains `reason_by` (`model` | `code`) and the view gains
`reasons_held_back`. The Reader's `reasonIsModels` now reads `reasonBy`, so
code's line is never shown as "model's reading". Before this, a core line
that code rewrote also carried that label.

The re-judge is already triggered: withholding a section changes the
section list, and with it the state key, so the view is no longer `ready`.
`reader.reading_path` then starts one judgment, the existing behaviour, and
the test asserts it runs.

An override on a stale path no longer copies a held-back line into the
learner's row. The base override also copied the reason of a label code had
changed; it now copies code's line in that case too.

Reproduction: the verify's sequence.

1. Every section's reason is `Prepares you for "3 Diagonalization"`.
2. `sec_diag` ("3 Diagonalization") is then held out.
3. The read-only stale view is checked.
4. A background judgment is held open by a gated fake and the view is
   checked (`judging`).
5. The judgment fails and the view is checked again (`failed`).
6. A "skip it" row is written, and a successful re-judge restores the
   model's lines.

On `bb2a75f85` the test fails at step 3: the view's JSON contains the
quote (`'Prepares you for "3 Diagonalization"' is contained here`). The
guard test fails there on the missing `reasonBy` key. The vitest case fails
on `bb2a75f85`'s `readingPath.ts`, and the other 11 tests in that file pass.

**V2 (ruling 2).** `build_reader_report` takes `reading_paths_enabled`
(default true). When it is false, the report has no `reading_paths` key
and does not query the path tables. `learnloop reader report` passes
`reading_paths.enabled`.

The pin is `tests/fixtures/reading_paths_report_base_a76c8358a.json`. It
holds the output of `a76c8358a`'s own CLI (`git archive a76c8358a src` under
`fixtures-local/tmp`, first on `sys.path`, run under `env -i` with an empty
HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR) on the test's two databases:

- path tables empty;
- 10 path rows: judgments at two depths, a read-anyway, a skip and two
  depth choices.

`[reading_paths]` was dropped from those scratch copies' toml, since the
base has no such table. Only `window.until` (the CLI's clock) and ULIDs are
normalized. On `bb2a75f85` both cases fail on `'reading_paths' not in ...`.

**V3 (ruling 3, Low, no change).** The disclosure registry, `get_settings`
and `learnloop eval judges` list configured routes. `reading_paths.enabled`
governs behaviour (no call, every RPC refuses, no contract key, no palette
action, no report block), not route metadata, so `reading_path_judge` stays
listed while it is off. Recorded as the orchestrator's ruling.

### Files changed

- `src/learnloop/source_retrieval/reading_paths.py`: `CODE_REASONS`,
  `judged_sections`, `reasons_held_back`, `_reason_by`; `path_view`'s
  `reason_by` and `reasons_held_back`; the line `override` copies.
- `src/learnloop/reader/reader_report.py`: `reading_paths_enabled`.
  `src/learnloop/cli/reader.py`: passes the switch.
- `apps/learnloop-tauri/src/api/dto.ts`: `reasonBy` and `reasonsHeldBack`.
  `screens/reader/readingPath.ts`: `reasonIsModels` reads `reasonBy`.
- Tests:
  - `tests/test_reading_paths.py` (+4: 51);
  - `tests/fixtures/reading_paths_report_base_a76c8358a.json` (new);
  - `ReadingPathCard.test.tsx` (+1, fixtures gain `reasonBy`);
  - `readingPathsReader.test.tsx` (fixture gains `reasonBy`).
- References regenerated (ef8012498): commit labels, the CLI as a
  `reading_paths.enabled` consumer, and moved line citations.

There is no migration change, no new config key, no new RPC and no CLI
option change. No model call was made: fakes only.

### Gate (orchestrator fix round)

- `uv sync --extra dev --extra mobile`: ok. `uv pip install pypdfium2`:
  pypdfium2 5.14.0. `TMPDIR` was the worktree's `fixtures-local/tmp`.
- `uv run lint-imports --no-cache`: **28 kept, 0 broken**.
- `pytest -n auto` over 65 files: **1,269 passed, 1 skipped**. The files are
  RW7a's own, every file that calls the reader report, every file that
  names `migration_head_217`, the pins (table roles, mobile allowlist,
  desktop RPC contract, architecture, CLI help snapshot, sidecar serializer
  snapshot, tracked fixture databases, coordinated migrations, SQLite
  copies, judge routes) and RW4b's, RW4d's and RW4e's pin files:
  ```
  test_ad1_migration.py test_approach_maps_schema.py test_architecture.py test_cli_help_snapshot.py
  test_compare_keep_switch_off.py test_compare_sources_keep.py test_coordinated_migrations.py
  test_desktop_rpc_contract.py test_diagnosis_replay.py test_exam_protection_review.py
  test_help_assists_schema.py test_hint_telemetry.py test_judge_routes.py test_label_roles_cli.py
  test_library_ask.py test_library_asks_migration.py test_library_exercises.py
  test_method_explicit_upgrade.py test_migrations.py test_mobile_allowlist.py test_mvp010_upgrade.py
  test_mvp011_upgrade.py test_mvp013_upgrade.py test_mvp014_upgrade.py test_mvp015_upgrade.py
  test_mvp016_upgrade.py test_mvp017_upgrade.py test_mvp018_upgrade.py test_mvp020_upgrade.py
  test_mvp021_upgrade.py test_mvp022_upgrade.py test_mvp023_upgrade.py test_mvp024_upgrade.py
  test_pfc_unverified_unassessed.py test_plan_determinism.py test_reader_cues_cli_report.py
  test_reader_cues.py test_reader_intentions.py test_reader_intent.py test_reader_report.py
  test_reader_rw1b_review.py test_reader_rw3b_migration.py test_reader_rw3b_review_fixes.py
  test_reader_rw7a_migration.py test_reader_tutor_offers.py test_reader_tutor_switch_off.py
  test_reading_paths.py test_reading_step_switch.py test_rebuild_orchestrator.py
  test_recurrence_commands.py test_regrade_contract_upgrade.py test_roles_concurrency.py
  test_roles_judges.py test_roles_switch_off_legacy_parity.py test_roles_switch_off.py
  test_route_rules_in_grader.py test_rw4d_rw3b_composition.py test_rw4_kill_switches.py
  test_shadow_rebuild.py test_sidecar_serializer_snapshot.py test_source_objects.py
  test_source_roles.py test_sqlite_file_copies.py test_table_roles.py
  test_tracked_fixture_databases.py
  ```
- `--durable-sqlite` over `test_reading_paths.py` and
  `test_reader_rw7a_migration.py`: **55 passed**.
- Frontend (`apps/learnloop-tauri`): `npm run typecheck` ok;
  `npm run frontend:build` ok.
- `npx vitest run` on every test file that renders `ReaderScreen` or
  imports `ReadingPathCard`, `readingPath` or `useReadingProgress`:
  **45 files, 327 passed**.
- `cargo check`: not applicable (no `src-tauri` change).
- `db_generate_reference.py` and `db_validate_reference.py` under `env -i`:
  945 leaves in 68 sections, 337 table notes, head 217, **0 errors**.

**Fail-before.** `git archive bb2a75f85` was extracted under
`fixtures-local/tmp`, the new test file and golden were copied in, and the
tests ran with `-o pythonpath=<tmp>/src`. All 4 new Python tests failed
there, as described above. For the vitest case, `bb2a75f85`'s
`readingPath.ts` was written over the working copy, the test run, and the
file restored.

**Process note.** Every Python run outside pytest used `env -i` with an
empty HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR: the base-report recording
and the two reference scripts. Those directories were checked empty after
the runs, apart from uv's `.cache` in HOME. File edits used `node` text
scripts. No vault outside `fixtures-local/tmp` was opened, and no stash was
used.
