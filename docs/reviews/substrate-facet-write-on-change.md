# Substrate: the canonical facet writers write only what changed

Branch `substrate/facet-write-on-change`, from main `2eb4bf6e61`. Fix 1 of the facet-table rewrite
investigation in `docs/reviews/followups-oct31.md`. No migration, no algorithm successor: stored
values and their meaning are unchanged; only when (and whether) rows are rewritten changes.

## What changed

`Repository.replace_canonical_facet_state` and `Repository.replace_capability_residual_state`
(`src/learnloop/db/repositories.py`) no longer `DELETE FROM` their tables and re-`INSERT` every row.
They hand the whole projection to one helper, `_write_projection_on_change`, which:

- reads the stored rows, keyed by (`facet_id`, `capability_key`, `practice_item_id`) for
  `facet_recall_state` and (`facet_id`, `capability`) for `facet_capability_evidence` and
  `capability_residual_state`;
- compares value columns only (every column the projection decides, including `id` and
  `algorithm_version`; never `created_at`/`updated_at`);
- writes nothing at all when every cell matches and the key sets are equal;
- otherwise deletes the vanished keys, updates only the changed rows (`updated_at = now`) and inserts
  the new ones (`created_at` and `updated_at = now`).

`created_at`:
- **capability and residual rows** carry none from the projection, so the stored `created_at` is
  kept. Before, every reload reset it to "now".
- **recall rows** carry a projected `created_at` (the first contributing observation's time). It is
  still written as projected, so a rebuild reproduces it. A row whose projected `created_at` moved
  (only possible when a measurement correction removes its first observation) counts as changed.
  Keeping the stale stored value instead would make the live table differ from a fresh rebuild in a
  column the projection owns. This is the one place where "keep every `created_at`" was read
  narrowly; the old writer already wrote these values.

**Transactions.** Outside an owning transaction, the comparison runs first on a read snapshot
(`BEGIN` ... `ROLLBACK`). The common no-op takes no write lock and commits nothing. When something
differs, the comparison runs again under `BEGIN IMMEDIATE` and is applied from that second
comparison, so a writer that committed in between is never applied against stale rowids. Inside
`Repository.atomic()` (an `AtomicConnection`, already under `BEGIN IMMEDIATE`), the single comparison
runs under the owner's lock. Two projected rows for one cell still raise `sqlite3.IntegrityError`,
as the unique index made the old `INSERT` do.

**Readers of these timestamps.** I re-checked the investigation's finding before building. No reader
makes a decision from `created_at`/`updated_at` of these three tables. `facet_state_reader._fold`
carries min/max into the legacy-shaped `FacetRecallState`, and nothing downstream reads those two
fields. The AD column registry only classifies the columns. `hints/state.py` reads value columns
only. The shadow rebuild compares value columns only. So I did not stop. `updated_at` now has a
meaning: "this estimate last changed then".

## Tests (fail-first)

New file: `tests/test_facet_state_write_on_change.py` (10 tests). On base `2eb4bf6e61`, 7 failed for
the intended reasons (`data_version` moved 2→3, `updated_at` moved on unchanged cells, capability
`created_at` reset) and 3 passed (created_at-projected, duplicate-cell refusal, algorithm-version
rewrite; these pin behaviour that must not regress). All 10 pass on the branch, in both the plain and
the `--durable-sqlite` lanes.

- A second `project_canonical_facet_state` over an unchanged ledger, at a later clock, leaves
  `PRAGMA data_version` unchanged and both tables identical (every column plus `rowid`). There is a
  plain variant and a `durability`-marked variant that asserts the vault is WAL.
- A new attempt: every pre-existing cell keeps its `created_at`. Cells whose values changed get
  `updated_at` = the attempt's time. Cells it left alone keep their `updated_at` and `rowid`. The
  test asserts that both kinds occur.
- Capability rows keep `created_at` across later attempts and projections.
- `SidecarContext.load(maintenance=False)`, then the stored timestamps are marked with a sentinel,
  then `reload(maintenance=False)`. Both facet tables are unchanged, and so is the whole database:
  `data_version` does not move across the reload.
- Repository level: vanished, new and changed cells (including NULL `practice_item_id`), a moved
  projected recall `created_at`, an `algorithm_version` change, a duplicate cell refused, and the
  residual writer's no-op, change and removal.

## Reload timing (synthetic vault)

`/tmp` is tmpfs, where fsync is free and hides the commit cost. So I measured on btrfs under the
worktree's gitignored `fixtures-local/facet-timing/` (deleted afterwards), outside pytest, under
`env -i` with empty HOME/CODEX_HOME/LEARNLOOP_CONFIG_DIR. The vault was built with
`create_placement_vault` and `add_followup_item`: 10 items, 300 self-graded attempts, WAL,
`synchronous=FULL`. The 11 recall rows and 1 capability row are a small cell count. Each variant
("before" = the base writer methods patched back on, "after" = this branch) ran 2×15 rounds of one
`project_canonical_facet_state` plus one `SidecarContext.reload(maintenance=False)`, with
`prepare_new_revisions` stubbed.

| | projection alone, median | reload, median | `data_version` moved |
|---|---:|---:|---:|
| before | 89.5 ms | 186.0 ms | 30/30 rounds |
| after | 78.5 ms | 172.7 ms | 0/30 rounds |

The fold dominates, so the reload saving is the one fsynced commit (about 11–13 ms). On tmpfs the
two are equal (before 152.6 ms, after 152.2 ms). Writer alone, no-op, same disk:

| cells | before | after |
|---|---:|---:|
| 100 recall + 40 capability | 41.3 ms | 3.8 ms |
| 1000 recall + 400 capability | 45.6 ms | 8.6 ms |

The bigger gains are not timing. A no-op reload no longer grows the WAL, no longer takes the write
lock (less contention with a second process such as the mobile host or a CLI), and no longer makes
storage-sync snapshots see a changed database. The O(ledger) fold on every reload remains; that is
fix 2.

`learnloop rebuild --shadow --json` on the same synthetic vault (`env -i`): facet 0 / mastery 0 /
schedule 0 changes (11 facet, 4 mastery, 10 schedule rows unchanged).

No paid or model calls were made.

## Gate (this step; the full suites run once in the landing gate)

Every pytest run was inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`,
with TMPDIR in the stage scratch directory.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken |
| `uv run pytest -n 6 tests/test_facet_state_write_on_change.py`, on base code (fail-first) | 7 failed, 3 passed |
| `uv run pytest -n 6 <81 targeted files below>` (under `flock /tmp/learnloop-fullsuite.lock`) | 1293 passed, 15 skipped, 7 xfailed |
| `uv run pytest -n 6 --durable-sqlite` new file + `test_rebuild_orchestrator`, `test_rebuild_equivalence`, `test_rebuild_equivalence_review`, `test_canonical_projection_rollout`, `test_km2_canonical`, `test_km2_write_path`, `test_capability_residual`, `test_shadow_rebuild` | 101 passed, 4 xfailed, 1 failed: the new plain variant asserted rollback mode, which is wrong in that lane. Fixed: the plain variant no longer asserts a journal mode |
| after that fix: `uv run pytest -n 6 --durable-sqlite tests/test_facet_state_write_on_change.py` / plain lane | 10 passed / 10 passed |
| `uv run pytest -m durability tests/test_facet_state_write_on_change.py` | 1 passed |
| `learnloop rebuild --shadow --json` on the synthetic vault (`env -i`) | 0/0/0 |

Not needed: npm/vitest/cargo (no frontend or `src-tauri` change), and the DB reference scripts (no
schema change).

Targeted files (every test file that names the three tables or the projection/rollout/writer
functions, plus the rebuild, shadow, replay, table_roles, architecture, coordinated-migrations,
tracked-fixture and sqlite-copy contracts):
`tests/test_ad23_contract.py`, `tests/test_ad2_model.py`, `tests/test_ad3_reading.py`, `tests/test_ad3_subject_view.py`, `tests/test_anti_double_count.py`, `tests/test_architecture.py`, `tests/test_assumed_known.py`, `tests/test_canonical_projection_rollout.py`, `tests/test_capability_residual.py`, `tests/test_causal_p2_acceptance.py`, `tests/test_characterization_certification_ledger.py`, `tests/test_conjunctive_instruments.py`, `tests/test_contract_frontier_coverage.py`, `tests/test_coordinated_migrations.py`, `tests/test_coverage_rollup.py`, `tests/test_curriculum_locks.py`, `tests/test_deferred_regrade.py`, `tests/test_diagnosis_pipeline.py`, `tests/test_difficulty_band_guards.py`, `tests/test_doctor.py`, `tests/test_error_hunt_items.py`, `tests/test_exam_seeding.py`, `tests/test_exam_session.py`, `tests/test_facet_identity_actions.py`, `tests/test_facet_outcome_view.py`, `tests/test_facet_state_write_on_change.py`, `tests/test_goal_projection.py`, `tests/test_grading_cli.py`, `tests/test_grading_support.py`, `tests/test_hint_feedback_texts.py`, `tests/test_km2_activation.py`, `tests/test_km2b_consumer_rekey.py`, `tests/test_km2_canonical.py`, `tests/test_km2_sim_gates.py`, `tests/test_km2_write_path.py`, `tests/test_km5_sim_gates.py`, `tests/test_learner_read_model_pinning.py`, `tests/test_learner_text_gaps.py`, `tests/test_map_untested.py`, `tests/test_measurement_corrections.py`, `tests/test_measurement_state_labels.py`, `tests/test_migrations.py`, `tests/test_mvp017_route_check_replay.py`, `tests/test_observation_ledger_bulk.py`, `tests/test_p0_cutover_mvp08.py`, `tests/test_p0_projection_cutover.py`, `tests/test_pfc_unassessed_readers.py`, `tests/test_pfc_unverified_unassessed.py`, `tests/test_post_attempt_worker.py`, `tests/test_probe_episodes.py`, `tests/test_projection_evidence_polarity.py`, `tests/test_rbeq_pr2_landing.py`, `tests/test_reader_active_reading.py`, `tests/test_reader_branches.py`, `tests/test_reader_recap_review_r2.py`, `tests/test_reader_recap_review_r3.py`, `tests/test_rebuild_closed_row_answer.py`, `tests/test_rebuild_equivalence.py`, `tests/test_rebuild_equivalence_review.py`, `tests/test_rebuild_orchestrator.py`, `tests/test_recall_coverage_interventions.py`, `tests/test_receipt_derivation.py`, `tests/test_receipt_exactness.py`, `tests/test_regrade_contract_successor.py`, `tests/test_replay.py`, `tests/test_required_method_grading.py`, `tests/test_route_rules_in_grader.py`, `tests/test_scheduler.py`, `tests/test_scoreboard.py`, `tests/test_shadow_rebuild.py`, `tests/test_sqlite_file_copies.py`, `tests/test_stuck_prompt_composition.py`, `tests/test_substrate_cutover.py`, `tests/test_table_roles.py`, `tests/test_teach_back.py`, `tests/test_today_headline.py`, `tests/test_tracked_fixture_databases.py`, `tests/test_tutor_promotion_w2.py`, `tests/test_unresolved_cause_gate.py`, `tests/test_workbench_discriminate.py`, `tests/test_workbench_text_gaps.py`

Test files added or changed: `tests/test_facet_state_write_on_change.py` (new).

## Open items

- **Fix 2 (not done, as instructed): skip the fold on reload when nothing it reads changed.**
  `refresh_canonical_projection_on_startup` still folds the whole ledger on every load and reload.
  That is about 78 ms on a 300-attempt synthetic vault, and it grows with the ledger. A cheap input
  fingerprint would need to cover everything the fold reads: ledger count and max position,
  `algorithm_version`, `CANONICAL_PROJECTION_VERSION`, merges and aliases, measurement corrections,
  quarantine, calibration lineage. Fix 1 made `PRAGMA data_version` a usable signal: a no-op
  projection no longer moves it, so "nothing committed since the last projection" can be detected
  within a process.
- **Fix 3 (not done, as instructed): capability `created_at` backfill.** Existing capability rows
  keep the `created_at` of the last reload before this branch landed, which carries no meaning.
  From now on it is kept, so it means "first written after this fix" or "the cell first appeared".
  The first contributing observation's time, as recall rows already have, would let a rebuild
  reproduce it. That changes stored column values (timestamp only, excluded from shadow and
  equivalence comparisons), so it goes to the owner as a choice.
- A full rebuild (`rebuild_all_derived_state` clears the tables first) still stamps every capability
  and residual row with the rebuild time, as before. That is expected: the owner boundary clears.
- The no-op compare costs about 8.6 ms at 1400 cells, in Python. It is not worth optimizing at
  today's sizes (76 recall + 36 capability rows on the largest owner copy).

## Landing onto main

The branch `substrate/facet-write-on-change` (worktree `learnanything-dl2`, stage tip `9fffc73cdb`) lands onto main
`2eb4bf6e61`. The orchestrator fast-forwards main and pushes.

### Merges

None. Main's tip was `2eb4bf6e61`, the branch's own base, when the landing started and again just before the full
gate and before this record was committed, so the branch fast-forwards as it is. No conflict, no regeneration: no
schema, config, template, frontend or `src-tauri` change, so the DB reference scripts, the desktop catalog, npm and
cargo were not needed.

### Gate (at `9fffc73cdb`)

Every run under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, `TMPDIR` outside the worktree,
`LEARNLOOP_AD_MODELS=off`; every pytest run inside `systemd-run --user --scope` (full suite 10G, the rest 5G) under
`flock /tmp/learnloop-fullsuite.lock`. No live model call.

- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- **Full pytest** (`-n 8 --dist worksteal`, 10G): **23095 passed, 89 skipped, 47 xfailed, 0 failed** (37:44). The 4
  grader tests that failed on main in the CA6b landing pass (main's `2eb4bf6e61` fixed them).
- **Durability lane** (`-m durability`, `-n 6`): **178 passed, 1 skipped**.
- **Owner lane** (`-m owner_vaults`, `-n 6`, fresh backup-API copies, `learnloop.db.copies.copy_tree_with_databases`,
  of `learnanything-ad1/fixtures-local/owner-copies-mvp035/{linear_algebra,probability,arxiv_v2}` in the gitignored
  `fixtures-local/landing-facet/`): **83 passed, 2 failed, 4 skipped**. The failures are exactly the two known ones,
  `test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events` and
  `test_placement_fixture_copies::…[arxiv_v2]`.

### Smoke on fresh owner copies (`fixtures-local/landing-facet-smoke/`, driver `scripts/smoke.sh`)

**Setup.** Fresh backup-API copies of the three mvp035 owner copies, neutralized under each side's own code
(`neutralize3.py`: every route at the `127.0.0.1:9` blackhole, key variable unset; rewrite, rerank, dense and
embeddings off). Main's code is `git archive 2eb4bf6e61` and the branch's `git archive 9fffc73cdb`, both with `src/`
and `migrations/`. Each copy, under its own side's code: a bare `upgrade` (**mvp-0.35 → mvp-0.40**, head 228), the
desktop start (`SidecarContext.load`, primary), `migrate_vault` (0 applied), `rebuild-derived-state`. Every process
ran under `env -i` with empty `HOME`, `CODEX_HOME` and config dir and an audit hook that refuses non-loopback sockets
and Codex process starts.

**Reload probe** (`scripts/reload_probe.py`, on a further copy of each side's rebuilt vault, under that side's code;
WAL, `synchronous=FULL`). Deterministic ids; the system clock is frozen and moved one hour before each step, so a
rewrite shows in `updated_at`. Steps: a desktop start (`load`, maintenance on); `reload(maintenance=False)` twice (the
refresh path the RPCs use); `refresh_canonical_projection_on_startup` alone; `close()` and a second desktop start in
a new `SidecarContext` (maintenance on). After each step: `PRAGMA data_version` from an observer connection opened
after the first load, and a sha256 of every table's rows (rowid order, every column including `rowid` and the
timestamps).

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| rows: recall / capability / residual | 76 / 36 / 0 | 2 / 1 / 0 | 4 / 2 / 0 |
| upgrade, desktop start, rebuild-derived-state (main and branch) | mvp-0.35 → mvp-0.40, ok (70 attempts replayed) | same (3) | same (3) |
| facet value columns, main vs branch after rebuild-derived-state (timestamps excluded) | **identical** in all three tables | identical | identical |
| Today (3 queue variants, frozen clock), branch vs main | **identical** (525,266 bytes) | identical (740,827) | identical (344,204) |
| `rebuild --shadow --json` (branch copy) | **0/0/0**, live unchanged | 0/0/0, live unchanged | 0/0/0, live unchanged |
| **main**: `data_version` over load → reload → reload → refresh → second start | 2 → 3 → 4 → 5 → 6 | 2 → 3 → 4 → 5 → 6 | 2 → 3 → 4 → 5 → 6 |
| **main**: tables changed at each of the 4 steps | `facet_recall_state`, `facet_capability_evidence` (every step); nothing else | same | same |
| **branch**: `data_version` over the same steps | **2 → 2 → 2 → 2 → 2** | 2 → 2 → 2 → 2 → 2 | 2 → 2 → 2 → 2 → 2 |
| **branch**: tables changed at any step | **none**: the three facet tables and every other table byte-identical, timestamps included | none | none |

- On main each step rewrites both facet tables, and it is the only write on that path: capability `created_at` and
  `updated_at` moved from 09:00 to 13:00 over the four steps (linear_algebra), recall `updated_at` likewise. On the
  branch the capability rows keep the `rebuild-derived-state` stamps through all four steps. The second desktop start
  (maintenance on) committed nothing at all on the branch.
- Timestamps differ between main's and the branch's rebuilt copies only where they are wall-clock stamps of the
  rebuild (recall `updated_at`, capability `created_at`/`updated_at`; the rebuilds ran about a minute apart). Recall
  `created_at` (projected: the first observation's time) is identical.
- `capability_residual_state` is empty on all three owner copies, so the residual writer is exercised by the tests only
  (`test_the_residual_writer_*` and the interleaving test `fe1953bed0`).
- **Model call receipts:** across the 18 smoke databases compared with their base copies, **0 new**. probability's 56
  historical rows (42 completed, 14 failed) are unchanged in each copy.
- **Audit:** the audit log was never written, so there was no process start and no socket connect of any kind. No
  Codex process ran.

### Orchestrator rulings (verbatim)

- R1: "Recall rows keep taking the created_at the projection supplies (first observation's time); a moved value counts as a change. Accepted: the live table must equal a fresh rebuild."
- R2: "Fix (2) (fingerprint skip of the fold) and fix (3) (capability created_at backfill) are queued follow-ups; fix (3) changes stored timestamp values and goes to the owner."

### Open items

1. **Fix 2 (queued follow-up):** skip the fold on reload when nothing it reads changed (input fingerprint; see the
   stage's open items). The fold still runs on every load and reload; only its write is gone.
2. **Fix 3 (owner decision):** backfill capability `created_at` with the first contributing observation's time, as
   recall rows have, so a rebuild reproduces it. It changes stored timestamp values (excluded from the shadow and
   equivalence comparisons), so it goes to the owner. Until then, existing capability rows keep the `created_at` of
   the last write before this landing (on the owner's vaults: their last reload or rebuild).
3. A full rebuild still stamps every capability and residual row with the rebuild time (the owner boundary clears the
   tables), as before.
