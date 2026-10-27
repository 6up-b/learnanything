# Follow-ups Oct 27 (`fix/followups-oct27`, base `1bcde2096`)

Three small follow-ups. Only tests changed. Nothing touches persisted meaning, no migration, no new config key,
no algorithm version. Item 3 needs a successor: it is pinned with strict xfails, and the design is below. Every run
outside pytest went through `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` under
`fixtures-local/fu27/`. An audit hook refused non-loopback sockets and Codex/node spawns. **Spend: $0. No paid or
model calls.** Owner copies came only from `fixtures-local/owner-copies-mvp035`, as fresh backup-API copies
(`copy_tree_with_databases`), one set per run (`fixtures-local/fu27/lane{1..5}`, `c3-*`). Nothing under
`~/learnloop-vaults`, `~/learnloop-retired` or `~/learnloop-books` was opened.

## 1. The `test_p1_...` load flake

**Cause.** `Harness.drain` ran `IngestRunner.drain` on a thread and `join(60)`. P1 stubs all 446 registered RPCs
with `enqueue=True` and calls each one twice, so the drain has 892 jobs. Alone it takes ~47 s (profiled). Under load
it ran past 60 s. The test then read `seen[...]` before those jobs had run (the `KeyError`), and the thread guard
caught the drain thread still running.

**Why the drain is slow** (cProfile, one run alone, 892 jobs, ~53 ms each):

- ~30 s: about 10,800 SQLite connection opens (`Repository.connection()` opens one per call, ~12 per job). Nearly all
  of it is the first statement on each new connection parsing the 226-migration schema. This is production
  behaviour and is not faked. A pooled or reused connection in the repository would be a product change, outside
  this stage.
- ~13.6 s: about 940 `fsync`s of the vault-lock holder file (`vault_lock._write_holder_fd`). The lock is taken twice
  per job. That file only records crash diagnostics, and none of these tests reads it.

**Fix** (test only, `tests/test_plan_first_transport_offer_grants.py`):

- `Harness.drain` still drains on its own worker thread, off any request, as the sidecar's worker does. The outcome
  no longer depends on timing:
  - it drains until no job of this runner is `queued` or `running` (a claim deferred by a busy vault lock is
    retried);
  - a hang guard (900 s, labelled `keep`: it is not a pass/fail timing) only stops a drain that never ends, after
    its current job;
  - the thread is always joined;
  - it then asserts that nothing is still pending.

  A slow drain can no longer turn into a `KeyError` or a leaked thread.
- The harness fixture gives `vault_lock` an `os` proxy whose `fsync` does nothing. Coverage is unchanged: the holder
  file is still written, and every grant check runs as before.
- Alone: P1 now takes 36 s, down from ~52 s, and the whole file 48 s.

**Load proof.** P1 ran inside a `-n 6` run of 30 other large test files (`ls -S` thirds), under
`flock /tmp/learnloop-fullsuite.lock` in a 5G scope. Five runs; P1 passed in all five:

| run | machine load (start → end) | result | P1 duration |
|---|---|---|---|
| 1 (third 0) | 8.9 → 10.7 | 1461 passed, 8 skipped | (not captured) |
| 2 (third 1) | 10.7 → 11.5 | 1547 passed, 2 xfailed | (not captured) |
| 3 (third 2) | 11.5 → 15.3 | P1 passed. 5 failures in `test_field_workbench_signals.py` were my own mid-edit helper-name clash (`_signals`), fixed and rerun in run 4 | (not captured) |
| 4 (third 2) | 16.6 → 29.3 | 1541 passed, 11 skipped | 45.5 s |
| 5 (third 0) | 29.3 → 21.6 | 1461 passed, 8 skipped | 59.2 s |

At load ~29 the test took 59 s, about the old harness's 60 s cap on the drain alone.

## 2. Owner lane

The owner lane ran at this branch's code with `LEARNLOOP_OWNER_VAULTS` set to fresh copies of
`{linear_algebra, probability, arxiv_v2}`.

- Before this stage: 80 passed, 9 failed (the landing record's count).
- Now: **83 passed, 2 failed, 4 skipped.**

**The three probability-data failures are test assumptions broken by real data, not product bugs.** The probability
copy holds the owner's own plans from 2026-10-25 and 10-26 (2 `daily_plans`, 3 planned `attention_blocks`, written at
mvp-0.31, chosen by `staged` and `mixture`). It also holds a real workbench session with `stuck` steps. linear_algebra
and arxiv_v2 hold neither.

- `test_daily_plan_kill_switch::test_plan_off_is_dl0_on_fixture_copies`
  - It asserted `(plans, blocks) == (0, 0)` after the plan RPCs, but the copy already holds the owner's plans.
  - Now `_plan_rows` returns every plan row and planned block, whole, and the test asserts they are equal before and
    after the calls.
  - This is stronger than before: no row may change, not only none be added. On a vault with no plans it is the same
    `([], [])`.
- `test_router_r2a_serving::test_switch_off_at_the_successor_serves_the_predecessors_plan_on_fixture_copies`
  - `_plan_trace` read every planned block, including the owner's 3. Those were built by the owner's router at
    mvp-0.31, so their detail carries `router`/`staged_frame`, and the "off has no router detail" assertion failed.
    The pre/off equality held trivially on them.
  - Now the trace excludes blocks that existed before this serve. `traces[0]` must therefore be non-empty from the
    test's own serve.
- `test_field_workbench_signals::test_g41_off_is_the_predecessor_on_fixture_copies`
  - The on-copy's workbench signals were asserted to be exactly the 2 the test seeds, but the owner's real stuck
    steps add their own `workbench_stuck:*` signals.
  - Now it reads the owner's own workbench signals from an unseeded on-copy. It asserts that they are disjoint from
    the seeded ones, and that the seeded copy has exactly own ∪ seeded. Every other assertion is unchanged.

**The 6 long-known failures:**

| test | kind | outcome |
|---|---|---|
| `test_doctor::test_plain_doctor_reports_pre_044_migrations_without_touching_database` | needs `conic-sections`, which the lane's copies do not include (environment, not data) | **skips** with the reason via the new `tests/owner_vaults.require_owner_vault` |
| `test_migrate_fresh::test_real_fk_rebuild_153_rolls_back_on_interruption` | needs `arxiv` (same) | **skips** |
| `test_sidecar_contract::test_sidecar_get_recent_ingests_lists_canonical_sources` | needs `arxiv` (same) | **skips** |
| `test_goal_decay_projection::test_linear_algebra_fixture_golden_projection` | needs `linear_algebra_legacy` (same) | **skips** |
| `test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events` | test assumption broken by real data: it needs a legacy attempt with no `activity_observations` row, and every attempt on the linear_algebra copy is already backfilled (`target` is `None`) | **still fails**. Not cheap: making an attempt "legacy" means deleting its observation rows and their dependents. Recommend seeding a synthetic legacy attempt instead |
| `test_placement_fixture_copies::test_placement_ignores_unanswered_opening_episodes_on_fixture_copies[arxiv_v2]` | **possibly a real product gap**, below | **still fails**, reported |

All four skips come from `require_owner_vault(name)`. With a full 8-vault lane, those tests run as before.

**The arxiv_v2 placement failure, possibly a product gap.**

- mvp-0.10 served 29 never-practised LOs. mvp-0.11 serves 28 of them as new material. The missing one is
  `lo_prepare_and_inspect_aligned_coordinate_tensors`.
- Its only item, `pi_a_preprocessing_pipeline`, has one attempt, a `self_report` (rubric score 0, 2026-07-21). That
  attempt set `last_attempt_at` but left no memory state (difficulty, stability and due date are NULL) and no mastery
  evidence.
- `Admission.placement` (`scheduling/scheduler.py`) counts it as attempted (`never_attempted` is false), so it is not
  new material. With no due date it is never reviewed either, and the queue serves it by no path.
- One item on arxiv_v2. The other two copies have none:
  `last_attempt_at NOT NULL AND due_at IS NULL AND active` counts 1 there.
- Fixing it changes serving, so it needs a successor.
- Proposed: "never attempted" for placement should mean "no scheduling-eligible attempt" (`state.stability IS NULL`
  as well as no FSRS-eligible attempt), so a self-report-only item enters as learning. It would sit behind a kill
  switch, with a 0-moves check on the three copies.
- **Owner question:** is a `self_report` with score 0 ("I don't know this") meant to send its LO back to learning?

## 3. Rebuild mismatch: an answer after a sibling closed outside the ledger

**Real production paths that close a row outside the attempt ledger:**

- `retire_item`, through `deactivate_practice_item_serving` (`content/authoring/item_authoring.py`);
- content sync (`substrate/state_sync.py`): YAML `status` retired, item removed from the vault, parked for review, or
  superseded by a measurement correction;
- `probe_lifecycle.retire_probe_instance`;
- a probe dialogue's single use (`diagnosis/probe_dialogue.py`);
- an applied proposal patch (`content/proposals/patches.py`).

None of them records a time in the ledger.

**Cause.** It is not the answered row's own write: the mvp-0.37 `MIN` rule is irrelevant, as the landing saw. The
attempt path reads the lifecycle of the LO's **other** items. `lo_relative_coverage` → `required_facets` counts only
the facets of the LO's *active* items, so closing a sibling that alone measures a facet changes the LO's coverage, its
mastery update and the item's due date. Live, each attempt sees the siblings as they were at its own time. Replay
sees one state for the whole history:

- an **unattempted** sibling's row is not reset (`reset_learning_object_derived_state` rebuilds only attempted items'
  rows), so it is closed throughout;
- an **attempted** item's row is rebuilt active and re-closed after the LO's last attempt
  (`keep_practice_items_inactive`), so it is open throughout.

The placement vault never showed this because every item there measures only `recall`. My earlier 24-seed random
exploration, and the owner-copy runs that closed the answered row itself, were all 0/0/0.

**Reproduction** (`tests/test_rebuild_closed_row_answer.py`). The placement vault gets one `application` item on
`lo_svd_definition`. Each case below fails with `--runxfail` at exactly the landing's signature, **mastery 1 /
schedule 1** (`lo_svd_definition` logit 0.503 live vs 0.789 replayed, and a different `due_at`):

- the sibling is retired (`retire_item` plus content sync) between two answers;
- it is closed by `set_practice_item_active(False)` between two answers (the landing's case);
- it is retired **after** the last answer. This is the most common order, and it means a primary load after retiring
  an unanswered duplicate already makes the next rebuild move mastery.

All three are strict xfails. The control (every sibling open) passes at 0/0/0.

**Why no replay-only fix.** Without the closure's time no rule is exact. "Closed throughout" is right when the
closure came before every answer, and "open throughout" when it came after. Switching rules only moves the error
between orders, and it would change rebuilt mastery on existing vaults. A guess from `practice_item_state.updated_at`
is unreliable: content-hash updates and reopenings move it too.

**Proposed successor design.** Recommended option (a):

- (a) **The attempt records the lifecycle it read.** At the tag, the attempt path stores the LO's required-facet set
  (or the active-sibling set it used) with the attempt, as the grader identity is recorded. Replay feeds the recorded
  set back for attempts at or after the tag (`required_facets` override, as `grader_identity_overrides`). One writer,
  and it covers every closure path, including future ones.
  - Attempts before the tag keep today's replay (predecessor), so the activation moves nothing.
  - Before the tag, an audit must list every lifecycle read on the attempt path (`required_facets` is the one found;
    the post-attempt follow-up and probe selection read `practice_item_states()` too) and record each.
- (b) **Lifecycle ledger.** A source table `practice_item_lifecycle_events` (item, active, reason, writer, time)
  appended by every closer and reopener above. Replay applies each event at its position in the attempt stream (like
  `_ClaimStream`). It is exact for siblings, but it has six writers to instrument, and closures before the tag have no
  time, so they keep the predecessor rule.

Either option needs a migration (a column or a table classified in `db/table_roles.py`), a successor version with a
kill switch, and the rebuild-equivalence property test widened to closures at random positions.

## Gate

- `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken.**
- Targeted pytest (`-n 6`, 5G scope, flock):
  - test files: `test_plan_first_transport_offer_grants.py`, `test_plan_first_transport_offer_grants_r5.py`,
    `test_daily_plan_kill_switch.py`, `test_router_r2a_serving.py`, `test_field_workbench_signals.py`,
    `test_rebuild_closed_row_answer.py`, `test_rebuild_equivalence.py`, `test_migrate_fresh.py`, `test_doctor.py`,
    `test_sidecar_contract.py`, `test_goal_decay_projection.py`;
  - contract tests: `test_sqlite_file_copies.py`, `test_public_tip_guards.py`, `test_tracked_fixture_databases.py`;
  - result: **240 passed, 17 skipped, 6 xfailed.**
- `test_rebuild_closed_row_answer.py` with `--runxfail`: 3 failed (the pinned gap), 1 passed.
- Owner lane (`-m owner_vaults`, fresh copies, `-n 6`): **83 passed, 2 failed (above), 4 skipped.**
- P1 load proof: 5 of 5 passed (table above).
- No migration, DB/connection, frontend or src-tauri change, so there was no durability, vitest, cargo or DB-reference
  run.
