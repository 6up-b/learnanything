# Refactor K2.6: one heartbeat and a lapse check for judge claims

Branch `refactor/k2.6-claim-heartbeat`, base `bcccfa21749447cf0d43544a8608bcf4c8e9abea`.
Implements K2.6 in `k2-ingestion-strategy-2026-11-11.md`, with its section 2 and map finding KB2 kept in view.

## Judgment calls to read first

1. Ingest jobs and judgment claims remain separate. Ingest expiry fails a job and waits for a person;
   judgment-claim expiry permits takeover with a new epoch. No schema, migration, config key, algorithm tag,
   model request or identity pin changes.
2. The old loops were `content/authoring/source_exercise_import.py:787-815` and
   `source_retrieval/reading_paths.py:819-844` at the base (paths relative to `src/learnloop`). Both bodies are gone.
   `db/stores/judgment_claims.py:30` now owns
   `claim_heartbeat(repository, claim, *, lease_seconds, interval)`, a context manager.
   Like the existing store's `write_decision` helper in `provenance.py`, it accepts a repository by its methods
   without importing the repository implementation into a store module.
3. The exercise lease stays 120 seconds and the reading-path lease stays 300, passed as `lease_seconds`.
   Both keep their 30-second interval, passed as `interval`. The exercise loop's `None` claim no-op is kept
   in the shared helper: standalone item verification needs it; reading paths always supply a claim.
   The two diagnostic thread names (`source-key-check-lease`, `reading-path-claim-lease`) become
   `judgment-claim-lease`. Scheduling, daemon status, delayed first beat, transactional renewal, exception
   retry and termination on a false renewal keep the old behavior. Exit now sets the stop event **and joins**
   the thread, including an in-flight renewal, on normal and exceptional exits.
4. Claim acquisition, renewal and commit checks stay on wall time, independent of the vault's injected clock.
   `_fenced_complete`, `_clear_pending`, and the reading-path publication transaction now pass `_lease_now()`
   to `holds_claim`. A lease expiring exactly at `now` is fenced, even without a takeover.
5. Spend reservations keep their own injected clock per handle, including two clocks in one database.
   `renew_now` snapshots the handle-to-clock maps, groups handles by resulting expiry and renews those groups
   in one transaction per database. Keeping only the database's first clock would renew later reservations
   in the wrong frame. System-clock reservations still use the system clock.
6. The `renew_claim`/heartbeat search found no third equivalent loop. The existing approach-map loop in
   `hints/map_builder.py` uses `_fenced_txn`, a lost-lease event, additional owner validity checks and release
   ownership; the map already excluded it from this extraction. Its consumers keep those semantics.

## Paid results when a claim is lost

Reading paths return `JudgeResult("held")` without adding section or judgment rows; `judge` then releases
its claim, fenced by owner and epoch. `PaidCalls.call` checkpointed the validated answer before returning it;
the completed receipt can also recover an answer if its checkpoint write failed. The next read claims again
and materializes the same answer without another model call. A competing completed path is read as `fresh`.

Exercise `_fenced_complete` returns `None`; `_clear_pending` returns `False` without changing the import.
`_resume_pending` reports `fenced` and leaves the pending marker for recovery; the delayed `_finish_pending`
likewise cannot append a late check. `PFCaller` retains the paid answers in model-work checkpoints and the
ladder already appended its verdicts to the judgment ledger. Recovery reuses the paid answers and writes the
effective check once. This does not promise one ledger append per recovery: the guard fences effective key
checks and import completion. It does guarantee that fencing does not discard the paid model answer.

`test_a_lapsed_unclaimed_path_keeps_the_paid_answer_for_retry` proves `held`, zero published rows, an epoch-1
released claim (no takeover), then `ready` with **one** fake call and one completed root receipt.
`test_a_fenced_resume_keeps_its_paid_answer_for_retry` proves `fenced`, an unchanged check count and retained
pending marker, then `resumed_check`, one new effective check and **no additional** fake calls.

## Fail-first evidence

Tests were written and run before production edits. Lapse has coverage at both callers:

| Test | Before the fix | After |
|---|---|---|
| `test_reading_paths::test_a_lapsed_unclaimed_path_keeps_the_paid_answer_for_retry` | `AssertionError: assert 'ready' == 'held'` | passes; retry reuses the paid answer |
| `test_source_exercise_import::test_a_lapsed_unclaimed_check_cannot_complete_or_clear_pending` | `AssertionError: assert 'rkc_…' is None` | passes; neither completion nor pending clearing changes the rows |
| `test_source_service_spend_accounting::test_spend_renewal_uses_each_reservations_injected_clock` | `AssertionError: assert '2026-11-20T07:03:57Z' == '2001-01-01T00:05:00Z'` | passes for two clocks in one database |

The first prototype run had an invalid clock fixture (`FixedClock` controls scheduling but has no `now()`),
so its reading-path `AttributeError` is **not** fail-first evidence. That was corrected to `FrozenClock` and
the spend assertion normalized to the store's UTC `Z` format before the recorded three genuine failures.
The exercise retry guard initially misused the config helper by appending the same key twice; restoring the
synthetic fixture's original TOML fixed that test setup. Neither setup issue changed production code.

`test_claim_heartbeat.py` waits on renewal events, not sleeps: a transient failure retries, renewal receives
the supplied duration and wall time, a lost lease ends the thread, normal/exceptional context exit joins it,
and a missing claim starts no thread. The repository's thread-leak guard stayed enabled throughout.

## Commands and results

All commands ran in this worktree, offline, through the supplied clean-environment wrappers. Below,
the step's scratch directory `S`,
`T=$S/t.sh`, `P=$S/py.sh`, and the exact test targets are:

```sh
L=tests/test_reading_paths.py::test_a_lapsed_unclaimed_path_keeps_the_paid_answer_for_retry
E=tests/test_source_exercise_import.py::test_a_lapsed_unclaimed_check_cannot_complete_or_clear_pending
C=tests/test_source_service_spend_accounting.py::test_spend_renewal_uses_each_reservations_injected_clock
R=tests/test_source_exercise_import.py::test_a_fenced_resume_keeps_its_paid_answer_for_retry
```

| Command | Result line |
|---|---|
| `$T $L $C -q -n 2` (prototype) | `2 failed in 3.55s`; one real spend failure, one invalid fixture |
| `$T $L $E $C -q -n 2` (before production edits) | `3 failed in 2.89s` (messages above) |
| `$T $L $E $C -q -n 2` (after production edits) | `3 passed in 2.59s` |
| `$T tests/test_claim_heartbeat.py $R -q -n 2` (retry guard setup) | `1 failed, 5 passed in 1.89s`; duplicate TOML key corrected |
| `$P ruff check` (first run) | `Found 1 error.` (`B905`, cleanup zip; corrected with `strict=False`) |
| `$P ruff check` (corrected and final runs) | `All checks passed!` |
| `$P lint-imports --no-cache` (initial and final runs) | `Contracts: 43 kept, 0 broken.` |
| Name-matched command below | `204 passed, 3 skipped in 24.48s` |
| `$T tests/test_identity_pins.py tests/test_structure_ratchets.py tests/test_kill_switches.py tests/test_sqlite_file_copies.py -q -n 2 -m 'not arc_close'` | `354 passed in 21.34s` |
| `$T tests/test_test_layout.py -q -n 1` (alone) | `3 passed in 19.18s` |
| `$T tests/test_architecture.py -q -n 1` (alone) | `18 passed in 30.27s` |
| `$T tests/test_source_exercise_import.py -q -n 2 -m 'not arc_close'` (after asserting the first resume really paid) | `23 passed in 4.71s` |
| `git diff --check` | exit 0, no output |

The name-matched run includes every added/edited test file and all 14 files whose names contain claim,
heartbeat, reading_path, exercise_import, service_spend, judgment or lease (one chunk, under 40):

```sh
$T tests/test_claim_heartbeat.py tests/test_hypothesis_claim_dispatcher.py tests/test_judgment_ledger.py tests/test_learner_claim_application_migration.py tests/test_learner_claim_superseded_migration.py tests/test_lp_claim_fixes.py tests/test_lp_claim_fixes_rereview.py tests/test_lp_claim_fixes_review.py tests/test_pr4_superseded_claims_landing.py tests/test_reading_paths.py tests/test_rw5c_judgments.py tests/test_source_exercise_import.py tests/test_source_service_spend_accounting.py tests/test_source_service_spend_envelopes.py -q -n 2 -m 'not arc_close'
```

## Size, boundaries and unverified work

Production: **82 added, 87 deleted; net -5 lines**, 169 changed production lines across four files.
Tests: 173 added lines (including the new 50-line heartbeat test file), net +173.
Including this record: 377 added, 87 deleted; net +290 lines.
No existing pin moved. No additional confirmed bug outside the task was found, so the bug ledger is unchanged.
`CLAUDE.md`, `refactor-status.md` and generated vault references are unchanged. Nothing was staged or committed.

The three skips are the opt-in owner-vault cases in `test_lp_claim_fixes.py`; they were not verified.
No test file was excluded for socket access. No full suite, fresh-connections arc-close run, separate durability
lane, private-vault shadow/replay, live provider or model request was run. The synthetic targeted run includes
the existing durability-marked spend process tests, but makes no broader WAL claim. Private vaults, books,
retired vaults, fixtures-local directories, real configuration and credential files were not opened.
