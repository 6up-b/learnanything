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
