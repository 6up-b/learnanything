# mvp-0.67: the mastery seed a topic started from is recorded and replayed (refactor step D8, gap 3)

Branch `refactor/d8-mastery-seed`, from origin/main `ca104b4983` (latest tag `mvp-0.66`, migration head 263). The
kept-replaced-claims stage (mvp-0.36) found the gap and pinned it as a parametrized strict xfail at mvp-0.35 and
mvp-0.36 (`tests/test_learner_report_superseded.py`); D8 fixes it, one landing per gap. The design is the D8 design
pass's section 3 ("Claims that never re-anchor"), its landing rules and its order of landings; the orchestrator decided
its two owner calls on the design's recommendations (below). Everything here was measured on synthetic vaults and
fakes; the owner's vaults are the orchestrator's (the last sections).

| Commit | What |
|---|---|
| `03571d947d` | Migration 265: `mastery_seed_inputs` (empty), its roles, seventeen earlier migrations' diffs |
| `3530e9929f` | The head fixture upgraded from 263 to 265, on its own (whichever of this branch and a 264 lands second redoes it) |
| `1af1ab2a5e` | The tag: one constant, the chain entry, its set and predicate, one upgrade row (a whole-vault rebuild for now), one test row; the mechanical moves by the tag string |
| `92fbcb0d27` | The behaviour: the capture at the three first-persistence seams, replay and the attempt-free rebuild reading it back, the upgrade's own activation; the strict xfail turned into below-tag characterization plus the successor's equality scenario; the new tests and their golden |
| `48abf4dc98` | The new table in the tests that see every write: the journey, grade-application and synthesis-tail goldens record its rows |
| `b0fdc6a620` | The curriculum C1 landing's two-sided chain slice, one further (missed by the tag commit's mechanical pass) |
| `2a079231ef` | The new golden written one scenario per line (the structure ratchet counts golden JSON lines) |
| (this record) | This record, the G2 design renumbered to `mvp-0.68`, ledger row D8-3, the profile setter's docstring |

One migration (265, the table and nothing else), no config key, no kill switch (owner rule 2026-11-16), no prompt
change. Nothing else about claims, mastery math, the profile setter's contract or adaptive difficulty changes.

## The defect

A learning object's mastery row is created once, from the learner claims then in force: vault sync creates every
missing row, an attempt on a learning object without a row builds its prior from the claims and its write persists it,
and a re-anchoring claim (a rung-variant request, a too-easy or too-hard report, a tutor gap declaration) on a
learning object without a row creates it. Later sync skips an existing row, and a claim that does not re-anchor (the
init wizard's starting level, which the profile setter replaces; a manual claim) only lands in `learner_claims`, by the
profile setter's explicit contract ("a changed starting level does not re-seed existing mastery"). Below the tag replay
seeded a practised learning object from the claims made before its first attempt (`_ClaimStream`) and an attempt-free
one from the claims in force at rebuild time (the umbrella's cold rows), so a rebuild after a starting-level change, or
after a manual claim, left other mastery than live, practised and unpractised topics alike (the minimal case: sync, a
new starting level, a rebuild before any answer). No race is needed: the production profile handler exposes the
operation.

## The two decisions (orchestrator, on the design's recommendations; the owner may revisit)

1. **A starting-level change affects future materializations only**, the current explicit contract. The profile setter
   stays seed-only; the three re-anchoring sources and their writers are unchanged. The fix records what each row was
   actually seeded from, rather than re-anchoring existing rows.
2. **Legacy learning objects get a labelled canonical seed** (`basis = 'legacy_reconstructed'`, `materialized_at`
   NULL): a practised learning object the claim set the predecessor's replay seeds it from (the claims made before its
   first attempt), an attempt-free one the predecessor rebuild's current claim set. It is reported as the upgrade's
   deltas and never described as observed history; it is never a copied measured mastery row (replay would count that
   row's evidence twice).

## The table and where it is written

`mastery_seed_inputs` (migration 265; RAW_LEDGER in `db/table_roles.py`, never cleared by replay; DENIED to adaptive
difficulty in `protected_tables.py`, every column metadata in `column_classes.py`):

| Column | Meaning |
|---|---|
| `learning_object_id TEXT PRIMARY KEY` | one row per learning object; no foreign key (learning objects are vault content, not rows) |
| `claims_made_json` | every covering claim the seed considered, replaced ones included, each with the fields the seed reads (`id`, `source`, `scope_type`, `scope_id`, `claimed_level`, `prior_pseudo_count`, `created_at`, `superseded_by`) and `in_force`; a JSON list in `(created_at, id)` order; `[]` for a cold start |
| `selected_claim_id` | the claim whose level seeded the mean, NULL for the cold start |
| `materialized_at` | when the row was first persisted; NULL for a legacy reconstruction (unknown) |
| `basis` (CHECK `'captured_at_materialization'`, `'legacy_reconstructed'`) | written by the writer that persisted the row, or by the upgrade |
| `policy_version` | how the seed reads the claims: `covering_claims_seed_v1` |
| `recorded_at` | when it was written (orders nothing, reaches no hash) |

**The columns are the design's; one addition inside a column.** Each recorded claim carries `in_force`: the live seed
reads the claims whose `superseded_by` is empty, replay's seed reads `_in_force` over the claims made by its point, and
recording which of the considered claims were in force makes the replayed seed exact without relying on those two
rules agreeing. All claims are recorded, not only the winner, because the seed's variance is bounded by every earlier
re-anchoring claim's own seed (`_retained_cold_variance`).

**Where it is written** (only at the tag, in the transaction that first persists the row):

- **Vault sync** (`learner/mastery_seed.materialize_mastery`): one `BEGIN IMMEDIATE` per missing learning object
  re-reads the row (another process may have materialized it since sync's snapshot), seeds, writes the row and the
  record. Below the tag sync is byte-for-byte the predecessor's.
- **An attempt on a learning object without a row**: `load_attempt_prior_state` keeps the seed it built the prior from
  (`AttemptPriorState.mastery_seed`); a live application carries it as `AttemptApplication.mastery_seed_inputs`, and
  `record_attempt_outcome` inserts it in the attempt's write, which persists the row. A replayed application hands it
  to the upgrade's observer instead (below) and records nothing.
- **A live re-anchoring claim that materializes the row** (`mastery._reanchor_in_transaction`, `current is None` and no
  replay `claims_made`): the record (the new claim included, normally the winner) commits with the row.

The insert is `ON CONFLICT DO NOTHING`: the first persistence wins and a record is never replaced (a writer that found
no row because another process had not yet committed still writes its mastery, as before, but the record names the
seed the row started from).

**The seed stays pure.** `mastery.seed_for_learning_object` returns the state together with what it read;
`initial_mastery_state_for_learning_object` is its `.state`, so the forecast, teacher, probe and field-prior readers
that ask for a hypothetical prior record nothing (tested).

**Replay** (`substrate/replay._replay_learning_object`): after the reset, a recorded seed's state
(`mastery.recorded_seed_state`, the same rule over the recorded claims) is written before anything replays, and the
claim stream opens `seeded_with` the record's claim ids: it seeds nothing, applies every re-anchoring claim placed
before the first attempt at its own point too (below the tag those were folded into the invented seed), and never
applies a claim the record holds. A learning object without a record is seeded the predecessor's way.

**The attempt-free rebuild** (`rebuild_orchestrator._seed_attempt_free`): the recorded seed, then the same claim
stream over no attempts (`finish`), so each later re-anchor re-seeds the zero-evidence row at its own point with the
claims made by then, as live did. A learning object no writer ever materialized (in the vault, never synced, no row)
is materialized by the rebuild from the claims in force, and its seed recorded as sync would record it: from then on
the rebuild and live agree. Replay of a practised learning object never writes a record.

## Playbook ruling and activation

The playbook's test (step 1): the change alters persisted meaning (what a rebuild derives wherever a claim that does
not re-anchor came after a row's materialization). So a tag: `mvp-0.67`, the immediate successor of `mvp-0.66` (step
3), no kill switch.

- `MASTERY_SEED_ALGORITHM_VERSION = "mvp-0.67"`, appended to `SUCCESSOR_CHAIN`; `MASTERY_SEED_VERSIONS`; the one
  predicate `mastery_seed_on(config)`.
- **A custom activation**: `legacy_mastery_seeds_then_rebuild`, in mvp-0.66's shape. Inside the activation's one
  transaction it first observes the predecessor's whole-vault rebuild in a rolled-back savepoint under
  `reconstructing_legacy_mastery_seeds`, which collects the seed that rebuild gives every learning object without a
  record (the claim stream's seed before the first attempt, the attempt path's prior where the stream did not seed, the
  attempt-free rows); it then records them (`legacy_reconstructed`, `materialized_at` NULL, the activation's clock) and
  rebuilds under the tag, which reads them. Its `committed` is that rebuild's receipt. `tests/test_upgrades.py` runs
  the row through activation, recovery after a death at each point, an idempotent re-run and a refused jump.
- What the activation changes: since each reconstruction is the predecessor's own reading, the rebuild under the tag
  reproduces the predecessor's rebuild; a live row the predecessor left divergent from its rebuild (a claim that does
  not re-anchor made after the row's materialization) is normalized to it, once. From the tag on, such claims reach no
  existing row, live or rebuilt.

## Pins and goldens that moved

- **The tag commit, by the tag string alone** (as at mvp-0.62 to mvp-0.66): `tests/goldens/identities.toml` the same
  nine pins (`A1-A4.manifest_hash.init`, `C3.boundary.init`, `C3.boundary_offer.init`, `C3b.chooser`,
  `C3b.chooser_offer`, `C3b.start_key`, `C3b.start_key_offer`, `C5.init`, `C6.init`), `--write`;
  `tests/goldens/effective_defaults.toml` (the algorithm line, `--write`); `tests/cli_surface.json` (`upgrade --to`'s
  default, by hand); `tests/goldens/placement_stored_misses.json` (its manifest's tag); the journey golden (320 tag
  strings and its two decision states' `config` and `snapshot_hash`, nothing else); latest-tag and chain-position pins
  in 46 earlier successors' test files: every negative `SUCCESSOR_CHAIN[-n]` index (n > 1) and every negative slice
  bound one further (two-sided slices included), `mvp-0.67` appended to tails and to the version sets that include
  every later tag, the fresh-vault tag in `test_ad23_successor`, `test_serve_eligibility_review` and
  `test_intent_codex_rereview`; `tests/test_teacher_te1_successor.py`'s mixed tail (`"mvp-0.66"` inserted before
  `LATEST_ALGORITHM_VERSION`, by hand); the application order's and the lifecycle inputs' own tag tests name their
  places from the end. The curriculum C1 landing's slice was missed by the mechanical pass and is its own commit.
- **The migration commit:** `MASTERY_SEED_ADDED_OBJECTS` (the table and its autoindex) subtracted in seventeen earlier
  migrations' "nothing else changed" diffs, through `tests/mastery_seed_inputs_migration_helpers.py`.
- **The behaviour's goldens** (`48abf4dc98`): the journey golden gains its journeys' seed rows (52 insertions, no
  deletion); the grade-application golden gains the table's one row and the application's `mastery_seed_inputs` field
  (null on all 44 applications); the three bootstrap synthesis-tail goldens gain their syncs' seed rows (16 lines
  each). Parsed, each file with the new table and field left out equals the file before: **no existing value moved**.
  The due-queue golden and the AD protection contract hold unchanged (sync writes the same seeds in both of the
  contract's copies).
- **New golden** `tests/goldens/mastery_seed_replay.json`: the mastery and seed rows of three histories (seed-only
  profile edits, actual re-anchors, attempt-free replay), live and after a rebuild (`MASTERY_SEED_WRITE_GOLDEN=1`).
- **The structure golden** (by hand, with comments): `attempts.py` 5833 to 5840 (the prior's seed field, the
  application's capture field, the seed read, the capture call, its persistence keyword; the logic is in
  `learner/mastery_seed.py`), `golden_json_lines` 281654 to 281804 (the 150 golden lines above), then 281809 (the new golden's 5 lines).
- **No identity pin moved in the behaviour commit and none was added.**
- **Assertions changed:** `test_a_global_claim_made_after_materialization_rebuilds_to_live` was a strict xfail
  parametrized at mvp-0.35 and mvp-0.36. At those two tags it becomes
  `test_below_mvp067_a_global_claim_made_after_materialization_rebuilds_to_other_mastery`, asserting the defect (the
  practised learning object's mastery changes in the shadow); the original equality assertion, unchanged, runs on a
  vault born at mvp-0.67 and on one made at mvp-0.66 and upgraded before the scenario (the design's "important test
  handling": no claim that a successor fixed the old tags).

## Tests, with fail-first evidence

`tests/test_mastery_seed_inputs_migration.py` (new, 4 tests): roles; the head fixture holds the table empty in rollback
mode; the migration adds the table and its autoindex and nothing else; the key, uniqueness, basis check and a NULL
`materialized_at` for a reconstruction.

`tests/test_mastery_seed_replay.py` (new, 25 tests):

| Test | What |
|---|---|
| `test_the_tag` | the predicate off at mvp-0.66, on at mvp-0.67 |
| the profile contract at both tags | a starting level changed after materialization leaves live mastery as it was (sync re-run included) |
| below the tag | nothing recorded; the rebuild reads today's claims (the defect, kept) |
| sync records | every learning object recorded at sync, the manual claim considered, in force and selected; the cold start records `[]` and no selection; the clock, basis and policy |
| a hypothetical prior | asking for one writes no row and no record |
| interrupted materialization | a failure at the record leaves neither the row nor the record; the retry records the claims in force at it; rebuild equals live |
| the attempt seam | an attempt on a learning object without a row records the seed its prior read at the attempt's time; a later starting level: rebuild equals live |
| rollback | a failure at the attempt's last write leaves no attempt, no row and no record |
| the re-anchor seam | a gap declaration materializing the row records itself as the seed; after an attempt and a new starting level the rebuild equals live, and no rebuild applies that claim again (counted) |
| the successor contract | a starting level after materialization, with an attempt and attempt-free; a manual claim, both ways; three replacements around an attempt; a re-anchor before the first attempt reading a later starting level at its point; an attempt-free learning object with a too-easy report between two starting levels; a learning object no writer materialized, materialized and recorded by the rebuild: each shadow 0/0/0, two applied rebuilds equal live, the records unchanged by both |
| the upgrade | at mvp-0.66 the shadow is nonzero; the upgrade records every learning object `legacy_reconstructed` with NULL `materialized_at`, the practised one from the claims before its first attempt and an attempt-free one from today's; live mastery normalized; shadow 0; a later starting level and answer rebuild to live; records frozen; a second upgrade does nothing |
| the upgrade where nothing came after materialization | records only; mastery as before; shadow 0 |
| goldens | the three histories, live equals rebuilt equals the golden |

**Fail-first.** The strict xfail stayed strict through the migration, fixture and tag commits (2 xfailed in the tag
commit's run). With the new and edited test files at the tag commit (`1af1ab2a5e`, no behaviour): 19 failed, 46
passed. The successor-contract cases fail at their signature (`{'mastery': 4} != {'mastery': 0}`, 3, 1), the recording
tests on the absent rows, the upgrade tests on the absent records, the two equality cases of
`test_learner_report_superseded.py` with the shadow nonzero, the goldens on the absent file; the passing ones are the
characterizations, the profile contract, `test_the_tag`, the hypothetical-prior and rollback tests and the unchanged
rest of that file. With the behaviour all pass.

## Commands and results

Every pytest run went through a script file with explicit targets, `-q -n 1 -p no:cacheprovider`, in a 3G memory
scope under the scratch wrapper (`env -i`, empty `HOME`/`CODEX_HOME`, isolated config dir).

| Run | Result |
|---|---|
| `uv sync --extra dev --extra mobile --extra tui --extra notebook`, `uv pip install pypdfium2==5.14.0` | installed (5.14.0 replaced 4.30.0) |
| Head fixture upgrade (backup API, scratch copy, `upgrade_allowance(UPGRADE_SCRATCH_COPY)`) | applied `[265]`; checkpoint (0, 0, 0); `delete`; `integrity_check` ok; `foreign_key_check` empty; added the table and its autoindex; rows changed only in `schema_migrations`; header 1/1; no companions |
| `test_mastery_seed_inputs_migration`, `test_attempt_lifecycle_inputs_migration`, `test_migrations`, `test_table_roles`, `test_ad_protected_tables`, `test_drop_dead_tables_migration` | 66 passed |
| The seventeen diff files plus every file asserting `range(n, migration_head() + 1)` (21 files) | 25 failed, 72 passed, 2 collection errors (an import indented wrong in two files, fixed in the migration commit); every failure the missing 264 (`265 != 264`); with a local stand-in 264 (never committed) 106 passed, 3 failed: `test_data_capture_migration`'s two exact-list tests and this migration's own downgrade test, which then also apply the stand-in (artefacts of it) |
| Tag commit's own files (47: the moved successor files, identity pins, effective defaults, CLI snapshot, journey golden, upgrades, placement), `-m "not arc_close"`, on a clean tree | 6 failed (five two-sided chain slices and the lifecycle inputs' version set, missed by the mechanical pass; fixed in the tag commit), 1407 passed, 12 skipped, 2 xfailed; the six files then 60 passed |
| Fail-first (the new and edited test files at the tag commit) | 19 failed, 46 passed |
| Behaviour: the same two files | 62 passed, 3 failed (the golden file not yet written); after `MASTERY_SEED_WRITE_GOLDEN=1`: all pass |
| Upgrades, identity pins, the closed-row file, both grade-application files, journey golden, due-queue and synthesis-tail goldens, ratchets, same-second order, AD contract, both rebuild-equivalence files, replay, `-m "not arc_close"` | 9 failed (grade-application golden, four journey cases, three synthesis-tail cases: the new table's rows and field; ratchets: `attempts.py` +16), 898 passed; goldens regenerated (each equal to the old with the table and field left out), `attempts.py` trimmed to +7 and the golden raised: ratchets, identity pins, both grade-application files, the new file 402 passed |
| `tests/test_architecture.py` alone | 1 failed (the seed insert's SQL outside a registered owner module), 17 passed; after moving the insert into `db/stores/practice_state.py`: 18 passed (then the new file, upgrades, the superseded-claims file, the grade-application golden: 413 passed) |
| Name filter over `scripts/affected_tests.py`'s 1,407 files (`rebuild|replay|equivalence|canonical|projection|upgrade|successor|shadow|regrade|apply_attempt|attempt_pipeline|mastery|grade_application|golden|table_role|protected|ad23_contract|ad_guard|backfill|recalibration|state_sync|same_second|attempt_order|doctor|landing|sim_|claim|seed|profile|learner_report|starting|wizard|sync|bootstrap|reanchor|tutor_gap|rung|promotion|priors|closed_row|lifecycle|migration_head`) united with every test file the branch adds or edits: 189 files, five chunks of at most 40, `-m "not arc_close"` | 4 failed, 483 passed, 9 skipped, 2 xfailed; 4 failed, 528 passed, 5 skipped; 5 failed, 405 passed, 6 skipped; 10 failed, 508 passed; 1 failed, 583 passed, 1 skipped. 23 failures are migration-range tests, 1 the curriculum C1 landing's slice (`b0fdc6a620`); the 24 with the local stand-in 264: 24 passed |
| `test_identity_pins`, `test_structure_ratchets`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches`, `test_sqlite_file_copies`, `test_public_tip_guards`, `test_retired_config_identities`, the two new files, the superseded-claims file, the C1 landing | 1 failed (ratchets: `golden_json_lines` +181, the new golden indented), 503 passed; after `2a079231ef` (one scenario per line, +5): ratchets and the new file 26 passed |
| `tests/test_test_layout.py` alone | 3 passed |
| `tests/test_architecture.py` alone (final) | 18 passed |
| `uv run python scripts/check_gate_partition.py` | collected 33224: landing 33158 + arc_close 66 |
| `uv run ruff check` | All checks passed! |
| `uv run lint-imports --no-cache` | Contracts: 51 kept, 0 broken. |
| The owner-copy procedure on a demonstration vault | below |

## What the orchestrator must run on owner copies

On backup-API copies (never a live vault), each at `mvp-0.66` (after mvp-0.66's landing), from the landed tip, with
the scratch wrapper's isolation. Two read-only scripts (counts only; they attach the database read-only, write nothing
and call no model):

```python
# seed_counts.py <copy root>: mastery seeds and claims, counts only (reads the database read-only, writes nothing)
import json, sqlite3, sys
from contextlib import closing
from pathlib import Path
from learnloop.algorithm_versions import MASTERY_SEED_VERSIONS
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

REANCHORING = ("rung_variant_request", "learner_report", "tutor_gap_declaration")
vault = load_vault(Path(sys.argv[1]))
database = VaultPaths(vault.root, vault.config).sqlite_path
los = set(vault.learning_objects)
out = {"algorithm_version": vault.config.algorithms.algorithm_version, "learning_objects": len(los)}
with closing(sqlite3.connect(f"file:{database}?mode=ro", uri=True)) as connection:
    connection.row_factory = sqlite3.Row
    one = lambda sql, *args: connection.execute(sql, args).fetchone()[0]
    attempts = {row[0]: row[1] for row in connection.execute(
        "SELECT learning_object_id, COUNT(*) FROM practice_attempts GROUP BY learning_object_id")}
    out["practised_learning_objects"] = len(los & set(attempts))
    out["attempt_free_learning_objects"] = len(los - set(attempts))
    claims = [dict(row) for row in connection.execute("SELECT * FROM learner_claims")]
    by = {}
    for claim in claims:
        key = f"{claim['source']}|{claim['scope_type']}|{'replaced' if claim.get('superseded_by') else 'in_force'}"
        by[key] = by.get(key, 0) + 1
    out["claims_by_source_scope_state"] = dict(sorted(by.items()))
    anchors = [c for c in claims if c["source"] in REANCHORING and c["scope_type"] == "learning_object"]
    out["reanchors_without_application_position"] = sum(1 for c in anchors if c.get("applied_after_attempts") is None)
    out["reanchors_positioned_past_their_attempts"] = sum(
        1 for c in anchors if c.get("applied_after_attempts") is not None
        and int(c["applied_after_attempts"]) > attempts.get(c["scope_id"], 0))
    if out["algorithm_version"] in MASTERY_SEED_VERSIONS:
        rows = [dict(row) for row in connection.execute("SELECT * FROM mastery_seed_inputs")]
        seeded = {row["learning_object_id"] for row in rows}
        for basis in ("captured_at_materialization", "legacy_reconstructed"):
            out[f"seeds_{basis}"] = sum(1 for row in rows if row["basis"] == basis and row["learning_object_id"] in los)
        out["learning_objects_without_a_seed"] = len(los - seeded)
        out["seeds_for_learning_objects_not_in_the_vault"] = len(seeded - los)
        out["seeds_with_a_selected_claim"] = sum(1 for row in rows if row["selected_claim_id"] is not None)
        out["seeds_selecting_a_claim_not_considered"] = sum(
            1 for row in rows if row["selected_claim_id"] is not None
            and row["selected_claim_id"] not in {c["id"] for c in json.loads(row["claims_made_json"])})
        considered = {c["id"] for row in rows for c in json.loads(row["claims_made_json"])}
        out["seed_claims_no_longer_on_record"] = len(considered - {c["id"] for c in claims})
        # A re-anchoring claim inside a seed that was applied after an attempt: the seed and the stream would both apply it.
        positions = {c["id"]: c.get("applied_after_attempts") for c in anchors}
        out["seeded_reanchors_applied_after_an_attempt"] = sum(
            1 for row in rows for c in json.loads(row["claims_made_json"])
            if (positions.get(c["id"]) or 0) > 0)
        out["mastery_rows_without_a_seed"] = one(
            "SELECT COUNT(*) FROM learning_object_mastery m WHERE NOT EXISTS "
            "(SELECT 1 FROM mastery_seed_inputs s WHERE s.learning_object_id = m.learning_object_id)")
print(json.dumps(out, sort_keys=True))
```

```python
# seed_values.py snapshot <state.sqlite> <private out.json> | compare <before.json> <after.json>
# Reads the database read-only; the snapshot holds values (keep it private), compare prints counts only.
import json, sqlite3, sys
from contextlib import closing

QUERIES = {
    "mastery": "SELECT learning_object_id, logit_mean, logit_variance, evidence_count, last_evidence_at "
               "FROM learning_object_mastery",
    "facet": "SELECT facet_id || '|' || capability_key || '|' || COALESCE(practice_item_id, ''), recall_alpha, "
             "recall_beta, independent_evidence_mass, raw_coverage_mass, last_observed_at, last_error_at, "
             "consecutive_failures FROM facet_recall_state",
    "schedule": "SELECT practice_item_id, difficulty, stability, due_at, last_attempt_at FROM practice_item_state",
    "surprise": "SELECT attempt_id, posterior_delta_json FROM attempt_surprise",
    "mastery_seeds": "SELECT learning_object_id, claims_made_json, selected_claim_id, materialized_at, basis, "
                     "policy_version, recorded_at FROM mastery_seed_inputs",
}
if sys.argv[1] == "snapshot":
    with closing(sqlite3.connect(f"file:{sys.argv[2]}?mode=ro", uri=True)) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        values = {name: ({str(row[0]): list(row[1:]) for row in connection.execute(sql)}
                         if sql.split(" FROM ")[1].split()[0] in tables else {})
                  for name, sql in QUERIES.items()}
    with open(sys.argv[3], "w") as handle:
        json.dump(values, handle)
else:
    before, after = (json.load(open(path)) for path in sys.argv[2:4])
    out = {name: {"changed": sum(1 for k in before[name].keys() & after[name].keys() if before[name][k] != after[name][k]),
                  "added": len(after[name].keys() - before[name].keys()),
                  "removed": len(before[name].keys() - after[name].keys())}
           for name in QUERIES}
    moved = [k for k in before["mastery"].keys() & after["mastery"].keys() if before["mastery"][k] != after["mastery"][k]]
    out["mastery"]["practised_changed"] = sum(1 for k in moved if (after["mastery"][k][2] or 0) > 0)
    out["mastery"]["attempt_free_changed"] = sum(1 for k in moved if not (after["mastery"][k][2] or 0))
    due = [(before["schedule"][k][2], after["schedule"][k][2]) for k in before["schedule"].keys() & after["schedule"].keys()]
    out["schedule"]["due_earlier"] = sum(1 for old, new in due if old and new and new < old)
    out["schedule"]["due_later"] = sum(1 for old, new in due if old and new and new > old)
    out["schedule"]["due_set_or_cleared"] = sum(1 for old, new in due if (old is None) != (new is None))
    print(json.dumps(out, sort_keys=True))
```

Per copy (keep the JSON value files private; publish counts only):

1. `seed_counts.py` at `mvp-0.66`: **practised and attempt-free learning objects**, **claims by source, scope and
   state** (in force or replaced), and two re-anchor application anomalies (re-anchoring claims with no recorded
   position, positions past their learning object's attempts).
2. `learnloop rebuild --shadow --json --vault "$COPY"` at `mvp-0.66` (comparison 1, predecessor live to predecessor
   shadow: the discrepancies that exist today), then `seed_values.py snapshot` (before).
3. `learnloop upgrade --vault "$COPY" --to mvp-0.67`, `learnloop doctor --vault "$COPY"`, `integrity_check`,
   `foreign_key_check`; `seed_values.py snapshot` (after) and `compare` (comparison 2: the **activation's mastery
   changes**, practised and attempt-free, the other tables and the due dates; expected nonzero only where step 2's
   shadow was nonzero; `mastery_seeds` added = the learning objects in the vault).
4. `seed_counts.py` at `mvp-0.67`: **exact seeds** (`seeds_captured_at_materialization`, expected 0 on a copy nobody
   used), **reconstructed seeds** (`seeds_legacy_reconstructed`, expected = the learning objects), **missing**
   (`learning_objects_without_a_seed`, expected 0), `mastery_rows_without_a_seed` (0), seeds selecting a claim they did
   not consider (0), seeded re-anchoring claims applied after an attempt (0: the seed and the stream would both apply
   one) and seed claims no longer on record (0).
5. `learnloop rebuild --shadow --json` at `mvp-0.67` (comparison 3, **successor shadow changes**: identical semantic
   values and no due date moved in `schedule_effects` required), then a second live rebuild of the copy (`learnloop
   rebuild-derived-state --vault "$COPY"`) and `compare` against step 3's snapshot (comparison 4, idempotence: 0 changed
   in every table, `mastery_seeds` included: the records are frozen).
6. Verify the live databases' SHA-256 unchanged.

On a scratch-built demonstration vault (the placement vault at `mvp-0.66` plus its follow-up item, synced, then a
new starting level, then answers on two learning objects), through the CLI: step 1 gave 4 learning objects, 2
practised and 2 attempt-free, one claim (`init_wizard|global|in_force`), no re-anchor anomaly; step 2's shadow mastery
4, facet 0, schedule 0 (no due date moved: every row was seeded cold live and from the new level in the rebuild); step
3's upgrade passed, `learnloop doctor` exit 0, `integrity_check` ok, no foreign-key violation, and the compare: mastery
4 changed (2 practised, 2 attempt-free), surprise 2 changed (the practised learning objects' attempts, now replayed on
the normalized seed), facet 0, schedule 0 (0 earlier, 0 later), 4 seed rows added; step 4: 4 legacy reconstructions,
0 captures, 0 missing, 0 rows without a seed, every anomaly count 0; step 5's shadow 0, 0, 0 with no due date moved,
and after a second live rebuild 0 changed in every table (the seed rows included); both shadow runs left the
database's hash unchanged.

## Limitations

- **Historical materialization stays unknown.** A learning object materialized before the upgrade keeps the
  predecessor's reading (its first attempt's claims, or today's when unpractised); the activation normalizes a live row
  the predecessor left divergent to it. Only rows first persisted at or after the tag are exact.
- A record names claims by their content at materialization; a claim's coverage of a learning object follows today's
  vault (a concept or subject moved later changes which claims a new learning object's seed reads, as before; a record
  already written is unaffected).
- A record standing without its row (nothing live deletes a mastery row outside a rebuild's own transaction) is
  re-materialized by sync from the record alone, without the re-anchors after it; the next rebuild applies them.
- With `mastery.claim_fixes_enabled` off (a kill-switch state) the claim stream is closed, so replay applies no
  re-anchor after the recorded seed, as the predecessor's replay applied none in that state.
- A practised learning object without a record (only attempts written outside the attempt pipeline; none in
  production) is seeded the predecessor's way on every replay, and replay never records one.

## Judgment calls to read first

1. **Migration 265 is provisional.** 264 is reserved for a parallel fix round; the 23 migration-range tests that name
   every number fail on this branch alone (`265 != 264`) and pass with a local stand-in 264 (never committed).
   Whichever lands second renumbers and redoes the head fixture (its own commit).
2. **Each recorded claim carries `in_force`** (inside `claims_made_json`, no extra column): exactness does not depend
   on the live and replay in-force rules agreeing.
3. **The attempt-free rebuild records a seed for a learning object nobody materialized**, the one place a rebuild
   writes this ledger: that rebuild is the row's first persistence, and without the record every later rebuild would
   re-seed it from the claims of its own day while live kept the first. Practised learning objects' replay never
   writes one (as mvp-0.66's replay never writes lifecycle inputs).
4. **The insert keeps the first record** (`ON CONFLICT DO NOTHING`) instead of failing: sync re-reads under its write
   lock, so a conflict is reachable only from an attempt whose prior was read before another process materialized the
   row (the pre-existing race on the row itself, untouched).
5. **The observation pass is the predecessor's rebuild in a rolled-back savepoint** (mvp-0.66's shape), collecting at
   the three replay seed points through a context variable rather than re-deriving claim sets beside it.
6. **`AttemptPriorState` and `AttemptApplication` each gain a field** (the prior's seed, the capture), which is why the
   grade-application golden moves by a field as well as by the table's rows.
7. **The three re-anchoring sources and AD's claim policy are untouched**; only replay's seed and its first-attempt
   folding changed.

## What was not verified

- The owner's vaults: no copy opened (the orchestrator's lane, above).
- The full suite, the arc-close gate and the durability lane (WAL, production pragmas).
- Vault references were not regenerated (the landing does).
