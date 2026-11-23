# mvp-0.66: retired items replay at the right point in history (refactor step D8, gap 2)

Branch `refactor/d8-retired-items`, from origin/main `544a6d529a` (latest tag `mvp-0.65`, migration head 261). The
followups of 2026-10-27 (item 3) found the gap on an owner copy and pinned it as three strict xfails
(`tests/test_rebuild_closed_row_answer.py`); D8 fixes it, one landing per gap. The design is the D8 design pass's
section 1 ("Retired items"), its landing rules and its order of landings; the orchestrator decided its two owner calls
on the design's recommendations (below). Everything here was measured on synthetic vaults and fakes; the owner's
vaults are the orchestrator's (the last sections).

| Commit | What |
|---|---|
| `cd19225f42` | Migration 263: `attempt_lifecycle_inputs` (empty), its roles, seventeen earlier migrations' diffs |
| `7ea4efe692` | The head fixture upgraded from 261 to 263, on its own (whichever of this branch and the parallel 262 lands second redoes it) |
| `10597547aa` | No behaviour change: the grade application reads its learning object's required facets once and hands the set to coverage and breadth (`read_lo_coverage`, `read_breadth`, `contract_frontier` take it) |
| `a5dd11ed8f` | The tag: one constant, the chain entry, its set and predicate, one upgrade row (a whole-vault rebuild for now), one test row; the mechanical moves by the tag string |
| `b12487621d` | The behaviour: the capture at the live seam, replay and regrade reading it back, the integrity refusal, the upgrade's own activation; the three strict xfails' marker removed; the new tests |
| `0f79029923` | The new table in the tests that see every write: the journey and grade-application goldens record its rows; the AD contract leaves it out of scope |
| `92177b4711` | The activation's import of the collector moves to the module head (`tests/test_architecture.py` froze function-local cross-domain imports) |
| (this record) | This record, the G2 design renumbered to `mvp-0.67`, ledger row D8-2 |

One migration (263, the table and nothing else), no config key, no kill switch (owner rule 2026-11-16), no prompt
change. Nothing else about grading, coverage policy, serving state or the retirement writers changes.

## The defect

A grade's relative coverage (`lo_relative_coverage`) and the legacy breadth denominator (`covered_required_fraction`'s
item-derived branch, the variance floor's input) count the facets of the learning object's **active** items
(`facet_diagnostics.required_facets`). A sibling that alone measures a facet therefore changes the coverage, the mastery
update and the answered item's due date while it is open, and stops changing them once it is closed. Production closes
items outside the attempt ledger: `retire_item` and content sync (retired in its YAML, removed from the vault, parked
for review, superseded by a measurement correction), probe retirement, a probe dialogue's single use, an applied
proposal patch. None records a time replay could apply the closure at. Below the tag, replay resets the attempted
items' rows, leaves an unattempted sibling's current flag in place and restores the inactive flags only after the
learning object's last attempt (`keep_practice_items_inactive`), so an unattempted retired sibling looked closed
throughout history (wrong for every answer before its closure) and an attempted one open throughout (wrong for every
answer after it). The pinned cases rebuilt to other mastery and `due_at` (logit 0.503 live against 0.789 replayed in
the followups' reproduction). Ordinary content maintenance reaches it; it matters only where the closed item measured a
facet no other item of the learning object measures and the open-uncertainty restriction does not replace the set.

## The two decisions (orchestrator, on the design's recommendations; the owner may revisit)

1. **Capture the attempt's lifecycle inputs, not a general lifecycle ledger.** The one writer that reads the
   lifecycle on the attempt path (the grade application) records what it read; every closure path, present and
   future, is covered without instrumenting its writers, and a sibling deleted from the vault is still accounted for.
2. **Old attempts get an explicit, labelled legacy reconstruction.** For every attempt applied before the upgrade, the
   activation records the set the predecessor's own replay reads at that attempt (`basis = 'legacy_reconstructed'`),
   from the item lifecycle as it stands at the upgrade, and freezes it. It is reported as the upgrade's deltas and never
   described as observed history: when those siblings closed was never recorded. An attempt applied at the tag that
   has no record is an integrity failure, never a reason to read today's lifecycle.

## The table and where it is written

`attempt_lifecycle_inputs` (migration 263; RAW_LEDGER in `db/table_roles.py`, never cleared by replay; DENIED to
adaptive difficulty in `protected_tables.py`, every column metadata in `column_classes.py`):

| Column | Meaning |
|---|---|
| `attempt_id TEXT PRIMARY KEY REFERENCES practice_attempts(id)` | one row per attempt; written after the attempt's own row in the same transaction, so the key is checked at once (no deferral needed, unlike the application order's reservation) |
| `learning_object_id` | the learning object the set was read for; replay uses the row only for that learning object |
| `required_facets_json` | the set, a sorted JSON list of facet ids (its canonical iteration order) |
| `basis` (CHECK `'captured_at_application'`, `'legacy_reconstructed'`) | written by the live grade application, or by the upgrade |
| `policy_version` | how the set was read: `active_item_evidence_facets_v1` (the evidence facets of the learning object's items whose serving row is active or absent, `required_facets`' rule) |
| `recorded_at` | when it was written: the attempt's clock for a capture, the activation's for a reconstruction (orders nothing, reaches no hash) |

**The columns are the design's.** `policy_version` names the reading rule rather than the vault tag: the rule is what
a later reader needs to interpret the set, and a capture's tag is already the attempt's application-order row's.

**Where it is written.** `_compute_resolved_grade_application` reads the set once through
`attempts.lifecycle_inputs.application_required_facets` and hands the same set to `read_lo_coverage` and to
`read_breadth` (its item-derived branch and the contract frontier's legacy fallback). At the tag a live application's
set becomes the application's `lifecycle_inputs` (a new `AttemptApplication` field: the application holds every row the
attempt writes), and `record_attempt_outcome` inserts it right after the attempt's row (`_insert_attempt_lifecycle_inputs`,
a plain INSERT: a second row for one attempt is a writer's bug). The capture and the attempt commit or roll back
together (tested by failing the attempt's last write). Below the tag nothing writes or reads the table and every
application reads today's lifecycle, as at mvp-0.65.

**Replay and regrade.** `replay_existing_attempt` loads the row (`recorded_for_replay`) before recomputation and passes
it in `ApplyAttemptInput.recorded_lifecycle_inputs`; the application counts the recorded set, never a cached coverage
number, so the open-uncertainty restriction, recall and the authored frontier still derive normally. A regrade replays
its learning object the same way, so it reuses the original capture. Replay never appends or replaces a row. An attempt
whose application-order row says the attempt pipeline applied it at the tag (`attempt_applied_at_version`) and that has
no row raises `LifecycleInputsMissing`, and the rebuild rolls back. An attempt with no row that was not applied at the
tag (written outside the attempt pipeline, as test helpers do; none in production) is read the predecessor's way.

**The inactive flags stay.** The final inactive-row restoration is unchanged: the recorded set feeds arithmetic only and
reopens nothing.

**Canonical iteration.** At the tag the coverage sums iterate the measured facets in sorted order
(`LoCoverageReads.canonical`), live and on replay alike; below it the set's own order, as before (a set of strings
iterates in an order that varies with the process's hash seed, so the last bit of a sum with unequal importances could
move between processes). No golden moved for it (below).

## Playbook ruling and activation

The playbook's test (step 1): the change alters persisted meaning (what a rebuild derives wherever a sibling's lifecycle
changed between answers, and what new attempts store). So a tag: `mvp-0.66`, the immediate successor of `mvp-0.65`
(step 3), no kill switch.

- `LIFECYCLE_INPUTS_ALGORITHM_VERSION = "mvp-0.66"`, appended to `SUCCESSOR_CHAIN`; `LIFECYCLE_INPUTS_VERSIONS`; the one
  predicate `lifecycle_inputs_on(config)`.
- **A custom activation** (step 3's "an `Activation` of its own"): `legacy_lifecycle_inputs_then_rebuild`. Inside the
  activation's one transaction it first **observes** the predecessor's whole-vault replay: `rebuild_all_derived_state`
  runs inside a savepoint that is then rolled back, under `reconstructing_legacy_lifecycle_inputs`, which collects, for
  every replayed attempt without a row, the set its application reads (the predecessor's reading: today's flags,
  attempted items reset as replay resets them, a diagnostic probe closed after its own replayed attempt). Nothing that
  pass wrote survives (no receipt, no appended version). It then records those sets (`record_legacy_lifecycle_inputs`,
  basis `legacy_reconstructed`, the activation's clock) and runs the whole-vault rebuild under the tag, which reads
  them. Its `committed` is that rebuild's receipt, so a re-run after a committed activation does nothing and one after a
  death before the commit reconstructs from no rows again. `tests/test_upgrades.py` runs the row through activation,
  recovery after a death at each point, an idempotent re-run and a refused jump (its `EXPECTED_ACTIVATIONS` row).
  Reconstructing the sets from the flags directly was rejected: it would have to repeat every reset and re-close replay
  makes on the way, and could drift from it.
- What the activation changes on a vault: nothing where no learning object's item is closed or gone. Where one is, the
  reconstruction is the predecessor's reading, so the rebuild under the tag reproduces the predecessor's rebuild; a live
  row the predecessor left divergent from its own rebuild (a closure that happened between or after answers) is
  normalized to it. New attempts are exactly reproducible from the tag on.

## Pins and goldens that moved

- **The tag commit, by the tag string alone** (as at mvp-0.62 to mvp-0.65): `tests/goldens/identities.toml` nine pins
  (`A1-A4.manifest_hash.init`, `C3.boundary.init`, `C3.boundary_offer.init`, `C3b.chooser`, `C3b.chooser_offer`,
  `C3b.start_key`, `C3b.start_key_offer`, `C5.init`, `C6.init`: the same nine), `tests/test_identity_pins.py --write`;
  `tests/goldens/effective_defaults.toml` (the algorithm line, `--write`); `tests/cli_surface.json` (`upgrade --to`'s
  default, by hand); `tests/goldens/placement_stored_misses.json` (its manifest's tag);
  `tests/fixtures/diagnosis_journey_golden.json` (320 tag strings and its two decision states' `config` and
  `snapshot_hash`, nothing else; `DIAGNOSIS_JOURNEY_WRITE_GOLDEN=1`); latest-tag and chain-position pins in 41 earlier
  successors' test files: every negative `SUCCESSOR_CHAIN[-n]` index (n > 1) and every negative slice bound one
  further, `mvp-0.66` appended to tails and to the version sets that include every later tag
  (`COMMITTED_CHECK_DELIVERY_VERSIONS`, `SECTION_END_VERSIONS`, `FACET_BELIEF_FIX_VERSIONS`, `FIGURE_WAIT_VERSIONS`,
  `FAILURE_SHARE_VERSIONS`, `APPLICATION_ORDER_VERSIONS`), the fresh-vault tag in `test_ad23_successor`,
  `test_serve_eligibility_review` and `test_intent_codex_rereview`; `tests/test_teacher_te1_successor.py`'s mixed tail
  (`"mvp-0.65"` inserted before `LATEST_ALGORITHM_VERSION`, by hand); `tests/test_same_second_order.py::test_the_tag`
  (mvp-0.65 is now one from the end).
- **The migration commit:** `LIFECYCLE_INPUTS_ADDED_OBJECTS` (the table and its autoindex) subtracted in seventeen
  earlier migrations' "nothing else changed" diffs, through `tests/attempt_lifecycle_inputs_migration_helpers.py`. The
  head fixture is its own commit (above).
- **The behaviour's goldens** (`0f79029923`): `tests/fixtures/diagnosis_journey_golden.json` records every persisted row
  of its journeys and gains their `attempt_lifecycle_inputs` rows (133 insertions, no deletion);
  `tests/goldens/grade_application/history.json` records every row and every field of every `AttemptApplication`, and
  gains the table's eleven rows and the new `lifecycle_inputs` field (an object on the eleven live applications, null
  on the 33 replayed ones; 192 insertions, 33 deletions that are `}` lines gaining a comma). Parsed, each file with the
  new table (and field) left out equals the file before: **no existing value moved**, numerical or otherwise, so the
  canonical iteration moved nothing these histories reach. The due-queue and synthesis-tail goldens hold.
  `tests/ad23_contract_helpers.py`: the AD protection contract compares every table's new rows between a copy with
  protected material and one without; this table holds the facets of the protected items too (the incumbent's grade
  application reads every current item), so it joins `OUT_OF_SCOPE` with the incumbent's other answer-pipeline tables
  (AD cannot read it: DENIED).
- **The structure golden** (by hand, with comments): `src/learnloop/attempts/attempts.py` 5820 to 5833 (the seam's two
  fields, its call and the replay's read; the logic is in `attempts/lifecycle_inputs.py`), `golden_json_lines` 269250
  to 269542 (the 292 golden lines above). The no-behaviour commit `10597547aa` alone takes `attempts.py` to 5821, one
  over the golden, until the behaviour commit raises it.
- **No identity pin moved in the behaviour commit and none was added:** the capture reaches no generator, cache or
  identity hash.
- **Assertions changed:** the three strict xfails of `tests/test_rebuild_closed_row_answer.py` lose their marker (their
  assertions are unchanged; the module docstring says the gap is fixed at mvp-0.66).
  `tests/test_grade_application_core.py::test_the_core_reads_no_database_clock_or_id_stream` refuses the new seam
  (`application_required_facets`) where it refused nothing for the lifecycle read before.

## Tests, with fail-first evidence

`tests/test_attempt_lifecycle_inputs_migration.py` (new, 4 tests): roles; the head fixture holds the table empty in
rollback mode; the migration adds the table and its autoindex and nothing else; the key, uniqueness and basis check.

`tests/test_rebuild_closed_row_answer.py` (17 tests; 4 before):

| Test | Below the tag | At the tag |
|---|---|---|
| `test_the_tag` | predicate off | predicate on |
| the three gap cases (retired between answers, closed directly between answers, retired after the last answer) | | shadow summary zero |
| `test_control_every_sibling_open_rebuilds_to_live` | | zero (unchanged) |
| `test_each_answer_records_the_set_it_read_and_coverage_and_breadth_both_count_it` | | the two rows (both facets, then recall only, `captured_at_application`, the policy, the attempt's clock); the stored coverage and breadth traces count each; after reopening the sibling and rebuilding, rows byte-equal and both traces as live |
| `test_below_the_tag_nothing_is_recorded_and_replay_reads_todays_flags` | no row; the rebuild gives the first answer today's (closed) reading: the defect, kept | |
| `test_an_attempted_sibling_closed_between_answers_rebuilds_to_live` | | the later answer recorded recall only; shadow zero; the closed row stays closed |
| `test_a_sibling_closed_and_reopened_between_answers_rebuilds_to_live` | | both, recall, both; shadow zero |
| `test_a_sibling_removed_from_the_vault_between_answers_rebuilds_to_live` | | the item's file deleted: both, then recall; shadow zero; the first answer still reads both after a rebuild |
| `test_a_close_in_the_same_second_between_two_answers_rebuilds_to_live` | | one `created_at`; both, then recall; shadow zero |
| `test_a_regrade_reuses_the_original_capture` | | the regrade (score 1) leaves the rows byte-equal and re-applies under both facets with the sibling closed; rebuild equals live |
| `test_a_rolled_back_application_leaves_neither_its_attempt_nor_its_capture` | | a failure at the attempt's last write leaves no attempt and no row |
| `test_an_attempt_applied_at_the_tag_without_its_capture_refuses_to_replay` | | the row deleted: the rebuild raises `LifecycleInputsMissing` and mastery is as it was |
| `test_the_upgrade_freezes_the_predecessors_reading_then_new_answers_capture_their_own` | at mvp-0.65 the shadow is nonzero | two `legacy_reconstructed` rows (recall only: the predecessor's closed-throughout reading); live mastery normalized; shadow zero; the sibling reopened later reaches neither; a new answer captures both; rebuild equals live; the legacy rows unchanged; a second upgrade does nothing |
| `test_the_upgrade_changes_nothing_where_no_sibling_changed` | | legacy rows only; mastery as before; shadow zero |
| `test_at_the_tag_relative_coverage_sums_the_facets_in_their_sorted_order` | | `lo_relative_coverage_from` with unequal importances equals the sum in sorted order |

**Fail-first.** The three strict xfails stayed strict through the migration, fixture, seam and tag commits (`3
xfailed` at `10597547aa` with the seam's tests). With the new test file at the tag commit `a5dd11ed8f` (no behaviour):
14 failed, 3 passed (the control, the below-tag characterization, `test_the_tag`). The three gap cases fail at their
signature (`{'mastery': 1} != {'mastery': 0}`), the capture, attempted-sibling, reopen, removal, same-second, rollback
and upgrade tests on the absent rows, the regrade on the replayed reading (`['recall'] != ['application', 'recall']`),
the refusal with `DID NOT RAISE`, the canonical-order test on the absent field; with the behaviour all 17 pass.

## Commands and results

Every pytest run went through a script file with explicit targets, `-q -n 1 -p no:cacheprovider`, in a 3G memory
scope under the scratch wrapper (`env -i`, empty `HOME`/`CODEX_HOME`, isolated config dir).

| Run | Result |
|---|---|
| `uv sync --extra dev --extra mobile --extra tui --extra notebook`, `uv pip install pypdfium2==5.14.0` | installed (5.14.0 replaced 4.30.0) |
| Head fixture upgrade (backup API, scratch copy, `upgrade_allowance(UPGRADE_SCRATCH_COPY)`) | applied `[263]`; checkpoint (0, 0, 0); `delete`; `integrity_check` ok; `foreign_key_check` empty; added the table and its autoindex; rows changed only in `schema_migrations`; header 1/1; no companions |
| `test_attempt_lifecycle_inputs_migration`, `test_attempt_application_order_migration`, `test_migrations`, `test_table_roles`, `test_ad_protected_tables`, `test_drop_dead_tables_migration` | 66 passed |
| The seventeen diff files plus every file asserting `range(n, migration_head() + 1)` (20 files) | 28 failed, 77 passed: every failure the missing 262 (`At index ...: 263 != 262`); with a local stand-in 262 (an empty migration, never committed) 103 passed and 2 failed, `test_data_capture_migration`'s two exact-list tests, which then also apply the stand-in (an artefact of it; they pass without it) |
| Seam commit: `test_grade_application_core`, `test_grade_application_golden`, `test_contract_frontier_coverage`, `test_rebuild_closed_row_answer`, `test_recall_coverage_interventions`, `test_replay`, `test_identity_pins` | 413 passed, 3 xfailed |
| Tag commit's own files (48: the moved successor files, identity pins, effective defaults, CLI snapshot, journey golden, upgrades, placement), `-m "not arc_close"` | 1361 passed, 12 skipped, 2 xfailed |
| Fail-first (the new `test_rebuild_closed_row_answer.py` at the tag commit) | 14 failed, 3 passed |
| Behaviour: `test_rebuild_closed_row_answer` | 17 passed |
| `test_upgrades`, `test_same_second_order`, both rebuild-equivalence files, both grade-application files, journey golden, AD contract, identity pins, replay, recall-coverage interventions, due-queue and synthesis-tail goldens, AD tables and guard, the migration test, `-m "not arc_close"` | 8 failed (the grade-application golden, six journey cases, the AD contract: the new table's rows), 911 passed; after `0f79029923`: AD contract, journey golden, grade-application golden, identity pins, ratchets 408 passed, 1 failed (ratchets: `attempts.py` +38, `golden_json_lines` +292); after moving the seam's logic out of `attempts.py` and raising the golden: ratchets, the gap file, core, golden, upgrades, identity pins 704 passed |
| Name filter over `scripts/affected_tests.py`'s 1,389 files (`rebuild|replay|equivalence|canonical|projection|coverage|breadth|facet_diag|retire|lifecycle|closed|upgrade|successor|shadow|regrade|apply_attempt|attempt_pipeline|mastery|recall_cov|grade_application|golden|table_role|protected|ad23_contract|ad_guard|backfill|recalibration|state_sync|frontier|same_second|attempt_order|doctor|landing|teach_back|exam_seed|sim_`) united with every test file the branch adds or edits: 195 files, five chunks of at most 40, `-m "not arc_close"` | 3 failed, 455 passed, 9 skipped; 4 failed, 506 passed, 5 skipped, 2 xfailed; 5 failed, 380 passed, 6 skipped, 2 xfailed; 10 failed, 511 passed; 1 failed, 679 passed, 1 skipped. All 23 failures are migration-range tests; with the local stand-in 262: 23 passed |
| `test_identity_pins`, `test_structure_ratchets`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches`, `test_sqlite_file_copies`, `test_public_tip_guards`, `test_retired_config_identities`, `test_rebuild_closed_row_answer` | 449 passed |
| `tests/test_test_layout.py` alone | 3 passed |
| `tests/test_architecture.py` alone | 1 failed (a new function-local cross-domain edge, the activation's import), 17 passed; after `92177b4711`: 18 passed (then `test_upgrades`, the gap file, identity pins, ratchets: 685 passed) |
| `uv run ruff check` | All checks passed! |
| `uv run lint-imports --no-cache` | Contracts: 45 kept, 0 broken. |
| `uv run python scripts/check_gate_partition.py` | collected 33058: landing 32992 + arc_close 66 |
| The owner-copy procedure on the demonstration vault, the counts script and a shadow on a fresh `learnloop init` vault | below |

## What the orchestrator must run on owner copies

On backup-API copies (never a live vault), each at `mvp-0.65` (after mvp-0.65's landing), from the landed tip, with
the scratch wrapper's isolation. Two read-only scripts (counts only; they attach the database read-only, write nothing
and call no model):

```python
# lifecycle_counts.py <copy root>: exposure and records, counts only (reads the database read-only, writes nothing)
import json, sqlite3, sys
from contextlib import closing
from pathlib import Path
from learnloop.algorithm_versions import LIFECYCLE_INPUTS_VERSIONS
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

vault = load_vault(Path(sys.argv[1]))
database = VaultPaths(vault.root, vault.config).sqlite_path
item_lo = {item.id: item.learning_object_id for item in vault.practice_items.values()}
lo_facets: dict[str, set[str]] = {}
for item in vault.practice_items.values():
    lo_facets.setdefault(item.learning_object_id, set()).update(str(facet) for facet in item.evidence_facets)
out = {"algorithm_version": vault.config.algorithms.algorithm_version}
with closing(sqlite3.connect(f"file:{database}?mode=ro", uri=True)) as connection:
    one = lambda sql: connection.execute(sql).fetchone()[0]
    out["attempts"] = one("SELECT COUNT(*) FROM practice_attempts")
    inactive = {row[0] for row in connection.execute("SELECT practice_item_id FROM practice_item_state WHERE active = 0")}
    out["inactive_items"] = len(inactive)
    attempted = {(row[0], row[1]) for row in connection.execute(
        "SELECT DISTINCT learning_object_id, practice_item_id FROM practice_attempts")}
    attempted_los = {lo for lo, _item in attempted}
    # Exposure: a practised learning object with an item closed now, or a practised item no longer in the vault.
    exposed = {item_lo[item] for item in inactive if item in item_lo} | {
        lo for lo, item in attempted if item not in item_lo}
    out["affected_learning_objects"] = len(exposed & attempted_los)
    if out["algorithm_version"] in LIFECYCLE_INPUTS_VERSIONS:
        for basis, n in connection.execute(
                "SELECT basis, COUNT(*) FROM attempt_lifecycle_inputs GROUP BY basis ORDER BY basis"):
            out[f"inputs_{basis}"] = n
        out["attempts_without_inputs"] = one(
            "SELECT COUNT(*) FROM practice_attempts a WHERE NOT EXISTS "
            "(SELECT 1 FROM attempt_lifecycle_inputs i WHERE i.attempt_id = a.id)")
        out["inputs_without_an_attempt"] = one(
            "SELECT COUNT(*) FROM attempt_lifecycle_inputs i WHERE NOT EXISTS "
            "(SELECT 1 FROM practice_attempts a WHERE a.id = i.attempt_id)")
        out["inputs_on_another_learning_object"] = one(
            "SELECT COUNT(*) FROM attempt_lifecycle_inputs i JOIN practice_attempts a ON a.id = i.attempt_id "
            "WHERE a.learning_object_id != i.learning_object_id")
        narrower = [lo for lo, facets in connection.execute(
            "SELECT learning_object_id, required_facets_json FROM attempt_lifecycle_inputs")
            if set(json.loads(facets)) < lo_facets.get(lo, set())]
        out["inputs_narrower_than_todays_items"] = len(narrower)
        out["learning_objects_with_narrower_inputs"] = len(set(narrower))
print(json.dumps(out, sort_keys=True))
```

```python
# lifecycle_values.py snapshot <state.sqlite> <private out.json> | compare <before.json> <after.json>
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
    "lifecycle_inputs": "SELECT attempt_id, learning_object_id, required_facets_json, basis, policy_version, "
                        "recorded_at FROM attempt_lifecycle_inputs",
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
    due = [(before["schedule"][k][2], after["schedule"][k][2]) for k in before["schedule"].keys() & after["schedule"].keys()]
    out["schedule"]["due_earlier"] = sum(1 for old, new in due if old and new and new < old)
    out["schedule"]["due_later"] = sum(1 for old, new in due if old and new and new > old)
    out["schedule"]["due_set_or_cleared"] = sum(1 for old, new in due if (old is None) != (new is None))
    print(json.dumps(out, sort_keys=True))
```

Per copy (keep the JSON value files private; publish counts only):

1. `lifecycle_counts.py` at `mvp-0.65`: **attempts**, **inactive items** and **affected learning objects** (practised
   learning objects with an item closed now or a practised item no longer in the vault: exposure, not a confirmed
   disagreement, since when they closed was never recorded).
2. `learnloop rebuild --shadow --json --vault "$COPY"` at `mvp-0.65` (comparison 1, predecessor live to predecessor
   shadow: the discrepancies that exist today), then `lifecycle_values.py snapshot` (before).
3. `learnloop upgrade --vault "$COPY" --to mvp-0.66`, `learnloop doctor --vault "$COPY"`, `integrity_check`,
   `foreign_key_check`; `lifecycle_values.py snapshot` (after) and `compare` (comparison 2: the **activation's value
   changes per table** and the **due dates earlier and later**; expected nonzero only where step 2's shadow was
   nonzero, since the reconstruction is the predecessor's reading; `lifecycle_inputs` added = the reconstructed rows).
4. `lifecycle_counts.py` at `mvp-0.66`: **exact captures** (`inputs_captured_at_application`, expected 0 on a copy
   nobody practised on), **legacy reconstructions** (`inputs_legacy_reconstructed`, expected = the attempts on learning
   objects the vault still has), **missing** (`attempts_without_inputs`: attempts whose learning object is gone from the
   vault, which no replay reads; expected 0 otherwise), `inputs_without_an_attempt` and
   `inputs_on_another_learning_object` (0), and `inputs_narrower_than_todays_items` /
   `learning_objects_with_narrower_inputs` (where a closure shaped the reconstructed reading).
5. `learnloop rebuild --shadow --json` at `mvp-0.66` (comparison 3, **successor shadow changes**: identical semantic
   values and no due date moved in `schedule_effects` required), then a second live rebuild of the copy (`learnloop
   rebuild-derived-state --vault "$COPY"`) and `compare` against step 3's snapshot again (comparison 4, idempotence: 0
   changed in every table, `lifecycle_inputs` included: the rows are frozen).
6. Verify the live databases' SHA-256 unchanged.

On the scratch-built demonstration vault (the placement vault at `mvp-0.65` plus one `application` item on
`lo_svd_definition`; two answers on its definition item and one on another learning object; the application item then
retired, and its row closed by content sync, after the last answer), through the CLI: step 1 gave 3 attempts, 1
inactive item, 1 affected learning object; step 2's shadow mastery 1, facet 0, schedule 0 (no due date moved); step 3's
upgrade passed, `integrity_check` ok, no foreign-key violation, and the compare: mastery 1 changed, surprise 2 changed,
facet 0, schedule 0 (0 earlier, 0 later), 3 lifecycle rows added; step 4: 3 legacy reconstructions, 0 captures, 0
missing, 0 orphaned or on another learning object, 2 records narrower than today's items, on 1 learning object; step
5's shadow 0, 0, 0 with no due date moved, and after a second live rebuild 0 changed in every table (the lifecycle rows
included); the shadow runs left the database's hash unchanged. `learnloop doctor` exits 1 on it for a content finding of
the demonstration's own item (its `application` facet is not registered in `facets.yaml`). On a fresh `learnloop init`
vault (at `mvp-0.66`) every count is 0 and the shadow is 0, 0, 0.

## Limitations

- **Historical closure times stay unknown.** An attempt applied before the upgrade keeps the predecessor's reading
  (today's flags at the upgrade); the activation normalizes a live row the predecessor left divergent to it. Only
  attempts applied at or after the tag are exact.
- An item moved to another learning object after an attempt replays under its new learning object (unchanged, outside
  this gap); the recorded set belongs to the old one, so replay reads the new learning object's lifecycle the
  predecessor's way for that attempt.
- An attempt written outside `apply_attempt` (none in production; test helpers that insert rows) has no record and no
  application-order row, and is read the predecessor's way on every replay.
- Only the grade application's lifecycle read is captured. The followups' audit also named the post-attempt follow-up
  and probe selection, which read `practice_item_states()`; they decide what is served next, not what a replay derives,
  and are not prefix inputs of the rebuild.
- The authored contract frontier (blueprint components) is content, not lifecycle, and still derives from today's
  vault, as before.

## Judgment calls to read first

1. **Migration 263 follows RD0's 262.** It was built beside RD0, before 262 existed, and its 28 migration-range tests
   failed on the branch alone until RD0 landed. After merging main, the fixture upgrade was redone on main's 262 file
   and all 28 pass ("After merging main", below).
2. **The observation pass is the predecessor's own rebuild in a rolled-back savepoint** rather than a re-derivation of
   its reading from the flags: exact by construction, at the cost of one extra whole-vault replay at the upgrade.
3. **A context variable carries the observation's collector** into the rebuild, instead of a parameter threaded through
   the orchestrator, the per-LO replay and the attempt step, which have no other use for it.
4. **`policy_version` names the reading rule** (`active_item_evidence_facets_v1`), not the tag.
5. **`AttemptApplication` gains a field** for the capture (the application holds every row its attempt writes), which
   is why the grade-application golden moves by a field as well as by the table's rows.
6. **A recorded set is used only for its own learning object**; a mismatch (an item moved) falls back to the
   predecessor's reading rather than refusing the rebuild.
7. **No doctor check** counts attempts without a record: replay refuses the integrity case itself, and the copy lane's
   counts cover the rest.

## What was not verified

- The owner's vaults: no copy opened (the orchestrator's lane, above).
- The full suite, the arc-close gate and the durability lane (WAL, production pragmas).
- Vault references were not regenerated (the landing does).

## After merging main

RD0's migration 262 and I2b landed while this was built. The branch merged main twice. The head fixture's 263
upgrade was redone on main's 262 file by CLAUDE.md's procedure: only 263 was applied, integrity and foreign keys are
clean, and only `schema_migrations` changed. The 28 migration-range tests that failed on the branch alone (the commands
table above) pass, with the migration set at 183 passed. The row-recording goldens, the AD contract, pins, ratchets
and public-tip guards gave 818 passed, and `db_validate_reference` reported no errors. After merging I2b, the
overlapping files (due-queue and journey goldens, the frozen intent view, the grade-application golden, the
closed-row tests and the upgrade table) gave 729 passed.

## Owner copies (run by the orchestrator)

The procedure above, on backup-API copies of the owner's three vaults (vault A from `mvp-0.61`, B and C from
`mvp-0.58`, each upgraded to `mvp-0.65` first). Counts only.

| Step | A | B | C |
|---|---|---|---|
| 1. Attempts; inactive items; affected learning objects | 60; 8; 4 | 70; 41; 7 | 3; 10; 1 |
| 2. Predecessor shadow: mastery, facet, schedule changed | 0, 0, 0 | 0, 0, 0 | 0, 0, 0 |
| 3. Activation: lifecycle rows added; mastery, facet, schedule, surprise changed; due dates earlier, later | 60; 0, 0, 0, 0; 0, 0 | 70; 0, 0, 0, 0; 0, 0 | 3; 0, 0, 0, 0; 0, 0 |
| 3. `integrity_check`; foreign-key violations | ok; 0 | ok; 0 | ok; 0 |
| 4. Legacy reconstructions; exact captures; missing; orphaned; on another LO | 60; 0; 0; 0; 0 | 70; 0; 0; 0; 0 | 3; 0; 0; 0; 0 |
| 4. Reconstructions narrower than today's items | 0 | 0 | 0 |
| 5. Successor shadow: mastery, facet, schedule changed | 0, 0, 0 | 0, 0, 0 | 0, 0, 0 |
| 5. Second live rebuild, then compare (lifecycle rows included) | 0 changed | 0 changed | 0 changed |
| 6. Live database unchanged | yes | yes | yes |

The three vaults have closed items on practised learning objects, but no reconstructed reading is narrower than
today's items, so the activation changes no value on them. `learnloop doctor` exits 1 on each copy
for content findings that predate this tag; none concerns state.

