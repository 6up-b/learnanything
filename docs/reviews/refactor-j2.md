# Refactor J2: drop the first family of dead tables

Step J2 of `docs/specs/refactor_strategy_v3.md` (§2.12). Branch `refactor/j2-drop-dead-tables`, based on main
`ef403d953d` (migration head 259). It takes **migration 260** (`260_drop_dead_tables.sql`); if another step lands a
260 first, the orchestrator renumbers the file at the merge (the number lives in the file name only; no test names it).

**Owner decision (Nov 20):** "I approve the dead and retired groups, but for retired groups wait until their readers
are removed by the steps that own that code." This step drops dead tables only, and only those still dead with
nothing in the way.

**What it delivers.** One migration dropping five empty tables; an upgrade guard that refuses, unchanged, a database
in which any of them holds a row; the migration-head fixture upgraded in place; every list that named the five updated.
No reached code changes behaviour. No algorithm tag, no config key, no kill switch.

## 1. Re-verification at this tip

`scripts/table_review.py` rerun at `ef403d953d` (no copies; removals compared with `5ba0fded47`, the C6 tip the review
was refreshed at): 401 tables, 18 dead, 14 retired but still read, 342 live, 27 derived. The same 18 tables are dead as
at C6. Each candidate was then checked by hand for the four conditions the brief sets. "Code" means `src/`, `scripts/`,
`apps/` and `tests/` (by `git grep`); "seeded" means a migration after the creating one inserts rows (the script's
"rows written by migration" flag, plus a grep of `migrations/`); "FK in" is the script's foreign-key children over a
schema built from every migration, confirmed on the head fixture with `PRAGMA foreign_key_list` over every table, and a
scan of every view and trigger for the name.

### Group A (11)

| Table | Reached SQL | Any code at all | Seeded | FK in | Verdict |
|---|---|---|---|---|---|
| `angle_inventories` | none | registry only | no | none | **dropped** |
| `family_evidence_cap_policies` | none | registry only | no | none | **dropped** |
| `controller_constraint_manifests` | none | registry; a name in `tests/test_migrations.py`'s 096 schema list | no | none | **dropped** |
| `controller_prequential_reports` | none | registry; the vault reference scripts' status lists | no | none | **dropped** |
| `learner_theta` | none (the doctor and debug-time sites are list entries that skip an absent table) | registry, doctor's deprecated list, debug time's timestamp list, `tests/test_doctor.py`, `tests/test_table_roles.py`, the vault scripts | no | none | **dropped** |
| `progression_policy_versions` | none | registry only | no | **`activity_family_authoring` (group B, retired but still read)** | **not dropped**: dropping the parent would leave a retired-but-read table's FK pointing at a missing table. It goes with the authoring family, after that table's reader goes. |
| `controller_outcome_windows` | none reached | 3 unreached SQL sites in `scheduling/controller_store.py`, called by `tests/test_randomization_layer.py` | no | none | **not dropped**: its writer and reader still exist and a test exercises them; dropping it would fail that test. |
| `familiarity_kernel_events` | none reached | `scheduling/kinship_feature.py` (`ensure_model`, `_append_kernel_event`), exercised by `tests/test_kinship_feature.py` | no | none | **not dropped**, same reason (C6 kept `kinship_feature`). |
| `familiarity_kernel_features` | none reached | `kinship_feature.py` (`_cache_feature`, `cached_feature`); `tests/test_kinship_feature.py` counts its rows | no | none | **not dropped**, same reason. |
| `shadow_component_events` | none reached | `scheduling/shadow_components.py`, exercised by `tests/test_shadow_components.py` | no | none | **not dropped**, same reason (C6 kept `shadow_components`). |
| `source_exam_profiles` | none reached | `SourceDocumentStoreMixin.upsert_exam_profile` / `get_exam_profile`, exercised by `tests/test_source_layer.py`; `tests/test_doctor.py` seeds a row for doctor's telemetry | no | none | **not dropped**, same reason. |

The five not dropped are still dead (no reached code), but each has code that a test runs (four) or a live FK child
(one). The strategy drops a table only after its readers and writers are gone, and the brief allows test edits only to
lists of names, so they wait for the steps that own that code.

### Group F's dead tables (7): the follow-up family, not dropped here

| Table | Still dead | What stands in the way |
|---|---|---|
| `p2_ladder_policies` | yes | rows seeded by migration 084 in every vault (a drop would refuse every vault under this step's guard: the seeded rows need an owner decision, or the guard's rule needs a "seeded rows only" carve-out); unreached readers in `db/stores/task_blueprints.py`; FK parent of `p2_ladder_stages` |
| `p2_ladder_stages` | yes | rows seeded by 084; unreached reader in `task_blueprints.py`; goes with its parent |
| `diagnostic_pack_cards` | yes | unreached store methods in `db/stores/probes.py`, read by `diagnosis/diagnostic_pack.py` and exercised by `tests/test_diagnostic_pack.py` and `tests/diagnosis_identity_helpers.py`; FK child of `diagnostic_packs` (retired but still read) |
| `diagnostic_pack_events` | yes | the same store methods; `tests/test_diagnostic_pack.py` reads its events |
| `practice_pool_events` | yes | unreached store methods in `db/stores/task_blueprints.py` |
| `practice_pool_surfaces` | yes | the same |
| `lapse_episodes` | yes | **nothing**: no SQL in `src/`, `scripts/` or `tests/`, no seed, no FK child. Its only parent link is to `card_lineages` (live). It can join the next family as is. |

## 2. The family dropped, and its order

`260_drop_dead_tables.sql` drops, in this order: `angle_inventories`, `family_evidence_cap_policies`,
`controller_constraint_manifests`, `controller_prequential_reports`, `learner_theta`. None is another's parent, so no
order is forced; `angle_inventories` (the only one with a foreign key, to `activity_family_versions`, which stays) goes
first by the children-first rule. `DROP TABLE` takes each table's own indexes and autoindexes: 16 objects in all (5
tables, 7 autoindexes, 4 indexes; `tests/drop_dead_tables_migration_helpers.py`). No view or trigger names any of them.

**Under the algorithm-change playbook:** no tag. Nothing derived or served reads these tables (no reached SQL, no
replayer, no projection, no upgrade module), so no persisted meaning moves. Two outputs move with the schema, as with
any migration: `learnloop dataset-export` no longer writes four empty files (`angle_inventories.jsonl`,
`family_evidence_cap_policies.jsonl`, `controller_constraint_manifests.jsonl`, `controller_prequential_reports.jsonl`:
the role registry put the RAW_LEDGER and RECEIPT ones in the export) and its `schema_sha256` changes; doctor's
`deprecated_table_row_counts` loses its `learner_theta` key. `tests/test_identity_pins.py` passes unchanged: no pin
moved.

## 3. The guard

**Mechanism.** A migration that drops a table names it on a comment line, `-- refuse-upgrade-if-rows: <table>`, beside
the `DROP`. (A `DROP` alone cannot be the signal: the temp-then-rename rebuilds drop tables whose rows they have just
copied.) In `learnloop.db.migrate._migrate`, after the existing coordination check and **before anything opens the
file for writing** (before the WAL switch and before the first pending migration), `_refuse_dropping_rows` reads every
pending migration's lines, opens the database read-only, counts the named tables that exist, and raises
`NonEmptyDropError` if any holds a row. The whole upgrade is refused, not only 260: a vault at 250 with a row in
`learner_theta` stays at 250, byte-identical, rather than committing 251-259 and stopping. A table an older database
does not have yet is skipped (an earlier pending migration creates it empty). A fresh build creates and drops the
tables in one go, with nothing to check.

**What a refusal looks like.** The exception names the database, the migration, and each table with its count:

> `<vault>/state.sqlite was not upgraded: migration 260 (drop_dead_tables) removes tables that no LearnLoop code uses
> any more, and in this database they still hold rows: learner_theta (1 row). Nothing was changed and no row was
> deleted. Keep the rows by staying on the LearnLoop version you have, and report this with the table names above so
> the rows can be kept before the tables go.`

Every entry point opens a vault through the migration coordinator, so the vault does not open on this version. Shown
on a scratch vault at 259 with one `learner_theta` row: `learnloop doctor --fix-state --vault <copy>` exits 1, prints
the message above at the end of its traceback, and the database's SHA-256 is unchanged (an empty `-wal` and a `-shm`
appear beside it, as for any read-only open of a WAL database). **What the owner can do:** stay on the earlier version
for that vault, and decide what the rows mean (export them, or keep the table by moving its drop to a later family).
The desktop app's rendering of the error was not checked (no GUI in this step).

**Tests** (`tests/test_drop_dead_tables_migration.py`, 9):
- no role, and no AD protection entry, names a dropped table;
- the head fixture holds 260, in rollback mode, with none of the 16 objects;
- a database at 259 with the five empty is upgraded by `[260]` alone: exactly the 16 objects go, nothing is added, no
  remaining definition changes, `integrity_check` ok, `foreign_key_check` empty;
- for each of the five tables (parametrized), a database at 259 with one row in it is refused with
  `NonEmptyDropError`, `row_counts == {table: 1}`, the message naming `<table> (1 row)`, the file byte-identical and
  no companion file left;
- a database at 258 with rows in two family tables is refused before 259 applies (byte-identical, still at 258), both
  tables named.

**Fail first.** With the migration and the tests in place but `migrate.py` at `ef403d953d`: 7 failed, 2 passed (the
six refusal tests fail at `migrate.NonEmptyDropError`, which does not exist; the head-fixture test fails because the
fixture was still at 259). Without the guard, SQLite's `DROP TABLE` drops a table with rows and its rows with it: the
silent emptying the guard exists to stop.

## 4. Everything the removal touches

**Lists of names edited** (each is a list or a sample; none ran on these tables):
- `src/learnloop/db/table_roles.py`: the five entries.
- `src/learnloop/ops/doctor.py`: `learner_theta` out of `_DEPRECATED_STATE_TABLES` (the ADR-010 telemetry list; the
  refusal message now carries any count).
- `src/learnloop/ops/debug_time.py`: `learner_theta` out of `TIMESTAMP_FIELDS` (it skipped absent tables anyway).
- `docs/learnloop-architecture-vault/_scripts/db_generate_reference.py`: the purpose and status entries for
  `learner_theta` and `controller_prequential_reports`, and the `angle_inventor` and `family_evidence` prefixes of a
  domain-grouping tuple.
- `docs/learnloop-architecture-vault/_scripts/db_validate_reference.py`: the two `EXPECTED_STATUS_OVERRIDES` entries.
- Hand-written vault notes that linked a dropped table's (generated) note: `Reference/Database/Deprecated State
  Gates.md` (the `learner_theta` row; "Three" → "Two"; one sentence on its drop) and `Reference/Database/Table
  Roles.md` (the COMPAT examples). ADR-010's evidence paragraph is history and is left as it is.
- Tests: `tests/test_doctor.py` (the `learner_theta` key in two expected dicts and one expected set, and the one
  `INSERT INTO learner_theta` that seeded the escalation test's list); `tests/test_table_roles.py` (the COMPAT sample
  `learner_theta` → `lo_probe_state`); `tests/test_migrations.py` (the name out of 096's table list).
- Earlier migrations' "nothing else changed" diffs that upgrade to head (16 files: `test_ad1_migration`,
  `test_ad23_migration`, `test_approach_maps_schema`, `test_help_assist_figures_migration`, `test_help_assists_schema`,
  `test_help_assist_work_md_migration`, `test_learner_claim_application_migration`,
  `test_learner_claim_superseded_migration`, `test_library_asks_migration`, `test_reader_rw3b_migration`,
  `test_reader_rw7a_migration`, `test_retrieval_spaces_migration`, `test_rw2d_receipts_migration`,
  `test_section_coverage_migration`, `test_t1_batch_origin_migration`, `test_reader_ca2_fix_orchestrator`): each
  admits `J2_DROPPED_OBJECTS` (from the new helper module) as removed, the way it admits later migrations' added
  objects. No other assertion changed.

**Checked and found nothing to edit:** AD's `protected_tables.py` and `column_classes.py`, the dataset export's
`_CAPTURED_WORKFLOW_TABLES` and `CAPTURE_EXCLUDED_TABLES`, every `DerivedStateReplayer` and the rebuild orchestrator,
`find_record`'s table list, state sync, the upgrade table, `tests/cli_surface.json`, the desktop and phone code.
`fixtures/mvp017_route_check_replay/state.sqlite` (head 186) has the five tables empty; tests that upgrade it pass.

**The fixture upgrade, as done.** `fixtures/migration_head/state.sqlite` copied with `backup_database` to a scratch
path outside the checkout; `apply_migrations` under `upgrade_allowance(UPGRADE_SCRATCH_COPY)` applied `[260]`;
`wal_checkpoint(TRUNCATE)` (0, 0, 0); `journal_mode=DELETE`; `integrity_check` ok; `foreign_key_check` empty; no
companion files; the tracked file removed and the copy written into place with `backup_database`; header bytes 1/1,
`integrity_check` ok, `foreign_key_check` empty, no companion files. A row-by-row comparison with the 259 file: 16
objects removed (exactly `J2_DROPPED_OBJECTS`), none added, no definition changed, only `schema_migrations`'s rows
changed. **Size: 7,626,752 bytes before and after** (1,862 pages of 4,096; freelist 0 → 16 pages; the procedure does
not vacuum). The fixture README has the section.

## 5. No behaviour change

- The reach analysis at this tip: the five tables have no SQL site in `src/` other than the role registry and the two
  list files above (`table_review.py`'s site list: `angle_inventories`, `family_evidence_cap_policies`,
  `controller_constraint_manifests`, `controller_prequential_reports` have only their registry entry; `learner_theta`
  has its registry entry, `ops/debug_time.py` `TIMESTAMP_FIELDS` and `ops/doctor.py` `_DEPRECATED_STATE_TABLES`), and
  `git grep` finds none in `scripts/`, `apps/` or tests other than those listed in §4.
- Every existing test passes with edits only to lists of table names (§4); the one non-list line removed is the
  `learner_theta` seed row in `test_doctor.py`'s escalation test, which seeded an entry of the list it checks.

## 6. Commands and results

All pytest runs through the scratch wrapper, `-n 1 -p no:cacheprovider`, in a 3G scope, one at a time.

| Command | Result |
|---|---|
| `tests/test_drop_dead_tables_migration.py` (fail-first, guard reverted) | 7 failed, 2 passed |
| `tests/test_drop_dead_tables_migration.py` | 9 passed |
| the 64 test files named `*migration*`, `*table_roles*`, `*tracked_fixture*`, `*rebuild_orchestrator*`, `*collection_dataset*`, `*protected_tables*`, `*column_classes*`, `*doctor*`, `*table_review*`, `*upgrades*`, `*schema*` (two chunks, `-m "not arc_close"`) | first run: 13 + 8 failed, all "nothing else changed" diffs to head (the list edits in §4); final run: 651 passed, 3 skipped; 317 passed |
| 17 other files that upgrade to head or name the tables (`test_activity_families`, `test_decision_records_retention`, `test_evidence_cutoff_readers`, `test_evidence_reading_successor`, `test_mobile_host_coexistence`, `test_pf_generation`, `test_re0_capture`, `test_reader_ca2_fix_orchestrator`, `test_ro1_availability`, `test_ro1_projection`, `test_ro5_checks`, `test_section_end`, `test_hint_feedback_widening`, `test_mvp017_route_check_replay`, `test_tracked_fixture_databases`, `test_debug_advance`, `test_coordinated_migrations`) | 318 passed, 1 failed (`test_reader_ca2_fix_orchestrator::test_223…`, the diff list), then 1 passed after the list edit |
| `test_identity_pins`, `test_structure_ratchets`, `test_public_tip_guards`, `test_sqlite_file_copies`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches` | 412 passed |
| `tests/test_test_layout.py` alone | 3 passed |
| `tests/test_architecture.py` alone | 18 passed |
| `ruff check` | All checks passed |
| `lint-imports --no-cache` | 45 kept, 0 broken |
| `python scripts/check_gate_partition.py` | collected 32819: landing 32753 + arc_close 66 |
| `db_generate_reference.py` (as is) | exit 1: `expected 396 table notes, got 401` (the generator writes notes but does not delete the five dropped tables' notes) |
| `db_validate_reference.py` (as is) | exit 1: table-note coverage differs, extra = the five dropped tables |
| the same two after deleting `Reference/Database/Tables/{angle_inventories,controller_constraint_manifests,controller_prequential_reports,family_evidence_cap_policies,learner_theta}.md` | generator exit 0 (`table_notes: 396`, `uncommitted_inputs: 0`); validator exit 0, `errors: []`. The generated changes were then reverted: the landing regenerates. |

## 7. What the orchestrator must run on owner copies

For each of `arxiv_v2`, `linear_algebra`, `probability` (and any retired vault that will be opened by this version):

1. **Backup step:** a backup-API copy (`learnloop.db.copies.copy_tree_with_databases`) of the vault, recorded by path
   and time, before anything else.
2. **Row counts, must all be 0:** `SELECT COUNT(*)` from `angle_inventories`, `family_evidence_cap_policies`,
   `controller_constraint_manifests`, `controller_prequential_reports`, `learner_theta` on the copy (read-only). A
   nonzero count stops the lane: the upgrade would refuse that vault, and the owner decides.
3. **Size before:** the database file's bytes, `page_count`, `freelist_count`.
4. **Upgrade** the copy through the coordinator (`learnloop doctor --fix-state --vault <copy>`): it must apply `[260]`
   (or 260 plus whatever else is pending) and not raise `NonEmptyDropError`.
5. **After:** `PRAGMA integrity_check` ok, `PRAGMA foreign_key_check` empty, the five tables absent, `schema_migrations`
   holds 260, size after (bytes, `page_count`, `freelist_count`; expect the same bytes with the freed pages on the
   freelist), and `learnloop doctor --json --vault <copy>` with no new error.
6. Optional P-shadow: `learnloop rebuild --shadow --json --vault <copy>` before and after should report the same
   deltas (no replayer touches these tables).

## 8. Follow-up

- **The second family** (§1, group F's dead tables): `lapse_episodes` is ready now. The two `p2_ladder_*` tables need
  the owner's call on 084's seeded rows (with this guard, a drop would refuse every vault until those rows are
  accepted as droppable). The diagnostic-pack and practice-pool tables need their unreached store methods and the
  tests that call them removed first.
- **Group A's remainder:** `progression_policy_versions` with the authoring family (after `activity_family_authoring`'s
  reader goes); `controller_outcome_windows`, `familiarity_kernel_events`, `familiarity_kernel_features`,
  `shadow_component_events` after `controller_store`'s window functions, `kinship_feature` and `shadow_components` go
  with their tests; `source_exam_profiles` after its store CRUD and its doctor telemetry go (ADR-010).

## 9. Not verified

- Owner vaults and retired vaults (the orchestrator's lane, §7). "Empty" in the review covers only the three live
  vaults as of Nov 9.
- How the desktop app and the phone host show the refusal (no GUI run); the CLI shows it at the end of a traceback.
- The landing gate as a whole; the vault references were not regenerated (the landing does). **The landing must delete the five dropped tables' notes** under `Reference/Database/Tables/` before `generate_all.py`, or the database generator stops at its note count (shown in §6).

## The owner-copy lane, as run (2026-11-21; counts only)

Backup-API copies of the owner's three vaults in a gitignored directory, with this branch; the copies were
deleted afterwards and the live databases' SHA-256 were unchanged.

| | arxiv_v2 | linear_algebra | probability |
|---|---|---|---|
| Rows in each of the five tables before | 0 in all five | 0 in all five | 0 in all five |
| Migration head before and after | 255 and 260 | 255 and 260 | 255 and 260 |
| The guard refused | no | no | no |
| The five tables after | absent | absent | absent |
| Database bytes before and after | 198,946,816 and the same | 53,366,784 and the same | 38,449,152 and the same |
| Freelist pages before and after | 226 and 228 | 149 and 151 | 234 and 236 |
| `integrity_check`; `foreign_key_check` | ok; 0 rows | ok; 0 rows | ok; 0 rows |

Doctor's errors after the upgrade are the content findings that predate this step (unknown criterion
dependencies, two invalid YAML files in one vault) and one missing directory in the copies; none names a
dropped table. No space is reclaimed: the tables were empty and the procedure does not vacuum.

