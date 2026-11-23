# mvp-0.65: same-second grades replay in the order they were applied (refactor step D8, gap 1)

Branch `refactor/d8-same-second-order`, from origin/main `533495a5c9` (latest tag `mvp-0.64`, migration head 260). The
rebuild-equivalence review of 2026-10-25 (finding F2) pinned the gap as a strict xfail; D8 fixes it, one landing per
gap. The design is the D8 design pass's section 2 ("Same-second grades"), its landing rules and its order of
landings; the orchestrator decided its two owner calls on the design's recommendations (below). Everything here was
measured on synthetic vaults and fakes; the owner's vaults are the orchestrator's (the last sections).

| Commit | What |
|---|---|
| `0852385a98` | Migration 261: `attempt_application_order` (empty), its roles, the head fixture upgraded from 260, seventeen earlier migrations' diffs |
| `d5592244ea` | No behaviour change: `learnloop.db.attempt_order`, the one order and boundary helper (SQL and Python forms; its writers later moved, `5f92a8a15c`); the attempt lists and the canonical scan take an order that defaults to the legacy one |
| `db3db4d3a7` | The tag: one constant, the chain entry, its set, predicate and the readers' door, one upgrade row with its own activation, one test row; the mechanical moves by the tag string |
| `6e8bee61b8` | The behaviour: the reservation in `apply_attempt`, every prefix reader on the order; the strict xfail's marker removed; `tests/test_same_second_order.py` |
| `e8232b746e` | The new table in the tests that see every write: the AD contract compares it through the view; the journey golden records its rows; a timeline test's stand-in takes the order |
| `5f92a8a15c` | The table's two writers move into the attempt store (SQL writes stay in registered owners); the J2 migration test applies through its own number; a review-feed test's stand-in takes the order; the rollback test fails the write through the repository instance; the structure golden's `golden_json_lines` raised for the journey rows |
| (this record) | This record, the G2 design renumbered to `mvp-0.66`, ledger row D8-1 |

One migration (261, the table and nothing else), no config key, no kill switch (owner rule 2026-11-16), no prompt
change. Nothing else about grading, scheduling or the time policies changes.

## The defect

An attempt's id is a ULID minted when its grading starts (`new_ulid` in the submit path); its `created_at` is the
clock when its grade is applied (`utc_now_iso`, whole seconds, `Z`). Live recording applies resolved grades in the
order their `BEGIN IMMEDIATE` transactions commit (`apply_attempt`, `attempts/attempts.py`), each reading the state the
previous one left. Every prefix reader ordered the ledger by `(created_at, id)`: replay's per-LO list
(`list_attempts_by_learning_object`), the recent LO and item windows and their exclusive bounds (`before`), the
canonical observation scan and its bounded folds (`before`/`through`), and the folds beside them. Two grading jobs for
one learning object that complete within one second, in the opposite order from their ids, therefore rebuild to other
state than live: the pinned case (grade B passes, then A fails, same item, same second, `B.id > A.id`) rebuilt to other
mastery, and the boundary tests below show each replayed attempt also saw another recent window and canonical prefix
than its live write had. Plausible with concurrent jobs, two surfaces or a batch; rare in sequential practice; no
incidence rate is known (the owner-copy counts below measure exposure, not inversions).

## The two decisions (orchestrator, on the design's recommendations; the owner may revisit)

1. **Tie-order correction only.** Occurrence time (`created_at`) stays the primary order; the new sequence breaks ties
   inside one `created_at` and nothing else. No global commit-order chronology: an imported or backdated attempt keeps
   its occurrence time, and occurrence and availability (`received_at`) keep their meanings
   (`docs/reviews/ep0t-time-policies.md`).
2. **Historical rows keep the predecessor's order, labelled.** Attempts applied before the upgrade are ranked in the
   predecessor's deterministic `(created_at, id)` order with `basis = 'legacy_order_unknown'`. Their real application
   order was never recorded; rowid, receipt times and grading revisions do not establish it, and nothing guesses it.

## The table and where the sequence is reserved

`attempt_application_order` (migration 261; RAW_LEDGER in `db/table_roles.py`, never cleared by replay; PROTECTED to
adaptive difficulty, by the attempt it names, in `protected_tables.py` and `column_classes.py`):

| Column | Meaning |
|---|---|
| `sequence INTEGER PRIMARY KEY` | the attempt's place among applications |
| `attempt_id TEXT NOT NULL UNIQUE REFERENCES practice_attempts(id) DEFERRABLE INITIALLY DEFERRED` | one row per attempt; the reservation precedes the attempt's own row in the same transaction, so the key is checked at commit |
| `basis` (CHECK `'applied'`, `'legacy_order_unknown'`) | reserved by `apply_attempt`, or ranked by the upgrade |
| `algorithm_version`, `recorded_at` | the tag and the time it was written (a capture time: it orders nothing and reaches no hash) |

**One change from the design:** no `AUTOINCREMENT`. Rows are never deleted (RAW_LEDGER) and a rolled-back reservation
leaves no row, so SQLite's next rowid is always above every row that exists, which is all the order needs;
`AUTOINCREMENT` would add `sqlite_sequence`, an internal table every schema diff, backup and table-role walker would
then carry.

**The reservation** (`reserve_application_sequence` in `db/stores/attempts.py`, a registered SQL owner) is the first thing `apply_attempt` does inside its
`repository.atomic()` (the `BEGIN IMMEDIATE` write transaction), before the server-hint refold and before anything is
computed, at the tag and only for a new application (`replace_existing` false): `INSERT ... ON CONFLICT(attempt_id) DO
NOTHING`, then the row's sequence. So the sequence is the order the write lock admitted the applications in; a
rollback takes the reservation with it; a second reservation of an attempt that has a row returns that row. A replay
or a regrade (`replace_existing`) takes none: a regrade is not a new observation, and the attempt keeps its place
while the grading epoch's revision still chooses the current grade. Below the tag nothing writes or reads the table.

## The order and its boundaries: one helper

`learnloop.db.attempt_order` (stdlib only, beside `db/attempt_availability.py` and `db/evidence_cutoff.py`; the tag set
is imported inside the two door functions; it reads the table and writes nothing, its two writers being the attempt
store's):

- `LEGACY_ORDER` (`created_at_id`): `(created_at, id)`. `APPLICATION_ORDER` (`created_at_application_sequence`):
  `(created_at, sequence, id)`, an attempt with no row sorting after every attempt of its second that has one, then by
  id (`UNBOUND_SEQUENCE`), so a ledger with no rows orders exactly as the legacy policy (tested).
- `attempt_order_for(config)` / `attempt_order_for_version(tag)`: the only doors, by the predicate
  `algorithm_versions.application_order_on`.
- SQL forms: `order_sql` (ascending or descending `ORDER BY` terms) and `before_sql` (strictly before a position), the
  sequence read by a correlated scalar subquery so `SELECT *` keeps exactly the attempt's columns (no row dict, and so
  no hash, gains a key). Python forms: `key`, `within` (strict or inclusive) and `sorted`, over a loaded
  `application_sequences` map.
- A position stays the pair `(created_at, attempt id)` replay already passed (`replay_ledger_position`); its sequence
  is looked up the same way as the rows' (SQL from the table, Python from the map), so a bound and the rows it bounds
  are always keyed alike. Every form agrees with every other on every pair (`tests/test_attempt_order.py`).
- Below the successor each consumer keeps its predecessor SQL text where it had one (the legacy branch of every
  adapted query is the old query; the one live window that had no id tie-break, the per-item window, keeps
  `ORDER BY created_at DESC`).

### Every consumer moved

| Reader | Where | At the tag |
|---|---|---|
| Replay's per-LO attempt list | `substrate/replay.py` (`list_attempts_by_learning_object(order=...)`) | applied in `(created_at, sequence, id)` |
| Recent LO window and its exclusive bound | `load_attempt_prior_state` → `list_recent_attempts_by_learning_objects` (window function `ORDER BY` and `before`) | newest applied first; replay's bound by the same key |
| Recent item window and its exclusive bound | `load_attempt_prior_state` → `list_recent_attempts_by_practice_item` (live and `before` branches) | the same |
| `replay_ledger_position` | `replay_existing_attempt` | unchanged pair; its sequence is looked up by every bound |
| Canonical observation scan | `observation_ledger.load_canonical_observation_ledger` / `load_authoritative_observation_ledger` via `canonical_observation_ledger_v2(order=...)` | the fold's order |
| Canonical `before` / `through` predicates | `project_canonical_facet_state` (the snapshot carries the order and the sequences; `_ledger_position_within` replaced by `AttemptOrder.within`) | bounded by the same key |
| Field FSRS history | `field/outcomes.py::fsrs_predicted_retrievability` | each item's reviews chained in application order |
| Family-memory fold | `substrate/family_memory.py` (`in_fold_order`) | `(observed_at, sequence, id)` |
| AD attempt ordering and first surface | `adaptive_difficulty/replay.py::load_events` (visible attempts sorted, sequences read through the material view) and `Events.ordered` | attempts at one time by sequence; attempts before claims before opportunities unchanged |
| Facet timeline | `facet_evidence_timeline.py` (`list_attempt_history(order=...)` and the events' tie sort) | the projection's order, so the receipt-exactness invariant holds |

**Not changed, by decision:** the grading epochs' order (`grading_epochs`, the evidence rows' `(created_at,
grading_revision, id)`); the diagnoser's `history_v1` and `corrected_before` (`diagnosis/split/history.py`); AD's
attempt/claim/opportunity precedence; replay's claim placement (`_ClaimStream`: a claim with a recorded
`applied_after_attempts` count is placed after that many attempts of the list, which is now the application order, so
the recorded count reads more exactly; an unrecorded claim is placed by `(created_at, id)` against the attempts, the
claims gap's subject). **The successor's fold-order policy is named on its own:** `created_at_application_sequence`
(`AttemptOrder.policy`); no time-policy preset changed.

### Other readers ordering attempts by `(created_at, id)` (searched, not moved)

A scan of `src/` for an `ORDER BY ... created_at` near `practice_attempts` finds about 119 sites. Besides the ones
moved above and the decisions above:

- **Whole-ledger folds recomputed the same way live and on rebuild** (they cannot disagree with themselves, only with
  the application order at a tie): `field/outcomes.py::_load` (the field rows' familiarity and reveal windows, the
  rows family memory reads; AD passes its material view's rows, still `(created_at, id)`), `MaterialView.attempts`,
  `router/outcomes.py` (R1's outcome replayer), `substrate/intervention_outcomes.py`, `placement/state.py`,
  `learner/lesson_weight.py`, `diagnosis/misconceptions.py` (the LO's posterior after replay).
- **The FSRS fitter's review log** (`scheduling/review_log.reconstruct_review_log` over `list_all_attempts`): the twin
  of the field history above; a fitting job the owner runs, left on `(created_at, id)` to keep the bounds (a follow-up
  candidate).
- **Live serving reads of the newest attempts** (scheduler frontier, familiarity at serve time, follow-ups, hints,
  tutor, probes, the TUI): not prefix readers of replay; their tie order is a display/serving choice.
- **Latest-attempt pickers** (`LIMIT 1`: `daily_plan/engine.py`, `router_chooser.py`, `remote/views.py`,
  `teacher/service.py`, `instructional/policy.py` and others) and **reports and evaluations** (scoreboards, recurrence,
  EVSI, reader, placement, hints, recognition, `practice_state.item_attempt_history`).

None of them writes state replay must reproduce at a tie; the record names them so a later step can move any that
should.

## Playbook ruling and activation

The playbook's test (step 1): the change alters persisted meaning (what a rebuild derives at a tie, and what new
attempts store). So a tag: `mvp-0.65`, the immediate successor of `mvp-0.64` (step 3), no kill switch.

- `APPLICATION_ORDER_ALGORITHM_VERSION = "mvp-0.65"`, appended to `SUCCESSOR_CHAIN`; `APPLICATION_ORDER_VERSIONS`;
  the one predicate `application_order_on(config)`.
- **A custom activation** (step 3's "an `Activation` of its own"): `legacy_order_then_rebuild`. Inside the activation's
  one transaction it ranks every attempt without a sequence in `(created_at, id)` order after every existing sequence
  (`rank_legacy_attempts`, beside the reservation in the attempt store; basis `legacy_order_unknown`, the tag, the activation's clock), then runs the whole-vault
  rebuild under the tag. Its `committed` is the whole-vault rebuild's receipt under the tag, so a re-run after a
  committed activation does nothing, and one after a death before the commit ranks from an empty table again (the
  transaction rolled the ranks back). `tests/test_upgrades.py` runs the row through activation, recovery after a death
  at each point, an idempotent re-run and a refused jump (its `EXPECTED_ACTIVATIONS` row).
- What the activation changes on a vault: nothing where no two attempts of one learning object share a second. Where
  they do, the legacy rank is the predecessor's order, so the rebuild under the tag reproduces the predecessor's
  rebuild; a live row the predecessor left divergent from its own rebuild (an inversion that really happened) is
  normalized to it. New writes are exactly reproducible from the tag on.

## Pins and goldens that moved

- **The tag commit, by the tag string alone** (as at mvp-0.62 to mvp-0.64): `tests/goldens/identities.toml` nine pins
  (`A1-A4.manifest_hash.init`, `C3.boundary.init`, `C3.boundary_offer.init`, `C3b.chooser`, `C3b.chooser_offer`,
  `C3b.start_key`, `C3b.start_key_offer`, `C5.init`, `C6.init`: the same nine), `tests/test_identity_pins.py --write`;
  `tests/goldens/effective_defaults.toml` (the algorithm line, `--write`); `tests/cli_surface.json` (`upgrade --to`'s
  default, by hand); `tests/goldens/placement_stored_misses.json` (its manifest's tag);
  `tests/fixtures/diagnosis_journey_golden.json` (311 tag strings and its two decision states' `config` and
  `snapshot_hash`, nothing else; `DIAGNOSIS_JOURNEY_WRITE_GOLDEN=1`); latest-tag and chain-position pins in 40 earlier
  successors' test files: every negative `SUCCESSOR_CHAIN[-n]` index (n > 1) one further and every negative slice
  bound one further (`grep -n "SUCCESSOR_CHAIN\[-" tests/`, `tests/test_curriculum_c1_landing.py`'s `[-28:-25]`
  among them), `mvp-0.65` appended to tails and to the version sets that include every later tag
  (`COMMITTED_CHECK_DELIVERY_VERSIONS`, `SECTION_END_VERSIONS`, `FACET_BELIEF_FIX_VERSIONS`, `FIGURE_WAIT_VERSIONS`,
  `FAILURE_SHARE_VERSIONS`), the fresh-vault tag in `test_ad23_successor`, `test_serve_eligibility_review` and
  `test_intent_codex_rereview`; `tests/test_teacher_te1_successor.py`'s mixed tail (`"mvp-0.64"` inserted before
  `LATEST_ALGORITHM_VERSION`, by hand).
- **The migration commit:** the head fixture (above) and `APPLICATION_ORDER_ADDED_OBJECTS` (the table and its
  autoindex) subtracted in seventeen earlier migrations' "nothing else changed" diffs, through
  `tests/attempt_application_order_migration_helpers.py`.
- **The behaviour's tests** (`e8232b746e`): `tests/fixtures/diagnosis_journey_golden.json` records every persisted
  row of its journeys, so it gains nine `attempt_application_order` rows across its cases (`99 insertions(+)`, no
  deletion: no existing value moved; `DIAGNOSIS_JOURNEY_WRITE_GOLDEN=1`). `tests/ad23_contract_helpers.py`: the AD
  protection contract compares every table's new rows between a copy with protected material and one without; the
  incumbent's answer pipeline numbers every application, the protected answers included, so the raw sequences differ
  by construction (10/9 against 3/4 for the run's two answers); the table joins `COMPARED_THROUGH_VIEW` and is
  compared as AD reads it, the visible attempts in sequence order (`out["application_order"]`), which the two copies
  must give alike. `tests/test_facet_evidence_timeline.py::test_bulk_timelines_read_grading_history_once`: its
  stand-in for `list_attempt_history` takes the `order` keyword the snapshot now passes (its assertion, one read, is
  unchanged).
- **The behaviour commit:** no identity pin moved and none was added: the sequence and `recorded_at` reach no
  generator, cache or identity hash (the SQL forms read the sequence by a subquery, so no attempt row dict gains a
  key; AD's `events_fingerprint` sees the attempts in their new order, which is what its in-process cache must see,
  and `Events.attempt_sequences` is outside it). One structure number rose: `golden_json_lines` 237130 to 237229,
  edited by hand in `tests/goldens/structure.toml` with a comment (the journey golden's 99 new lines). A first draft
  of the rollback test patched a private module function (`private_patch_sites` +2); it now fails the write through
  the repository instance, and that number is unchanged. **No numerical golden moved:** the
  journey golden's values (beside the new table's rows above), the due-queue goldens and every other golden in the
  runs below hold at the tag, because their
  histories record no two attempts of one learning object in one second whose application order differs from their
  id order (ids minted in one process are monotonic, `ids.py`).
- **Assertions changed:** `tests/test_rebuild_equivalence_review.py::test_two_same_second_attempts_committed_in_reverse_id_order_rebuild_to_live`
  loses its strict xfail marker (its assertion is unchanged; the module docstring says F2 was fixed at mvp-0.65).
  `tests/test_rebuild_equivalence.py` still passes `(created_at, id)` tuples as bounds, which the helper resolves.

## Tests, with fail-first evidence

`tests/test_attempt_order.py` (new, 10 tests; the helper on plain values): legacy order and boundary equal the
predecessor expression on every pair; the application order breaks ties by sequence, unbound rows last by id;
occurrence time stays first; the SQL and Python boundaries agree on every pair under both policies and are the order's
own prefixes; a bound without a row is keyed as its rows are; a reservation is the next sequence and a second one
returns it; ranking fills only unbound rows, in the predecessor's order, after every sequence; with no rows the
application order is the legacy order.

`tests/test_attempt_application_order_migration.py` (new, 4 tests): roles; the head fixture holds the table empty in
rollback mode; the migration adds the table and its autoindex and nothing else; the deferred key refuses a dangling
reservation at commit, the UNIQUE and CHECK constraints hold.

`tests/test_same_second_order.py` (new, 19 tests):

| Test | Below the tag | At the tag |
|---|---|---|
| `test_the_tag` | legacy order, predicate off | application order, predicate on |
| `test_below_the_tag_no_sequence_is_reserved_and_a_reversed_pair_rebuilds_in_id_order` | no row; replay lists A, B; rebuilt mastery differs from live (the defect, kept) | |
| `test_at_the_tag_each_live_attempt_reserves_the_next_sequence_in_application_order` | | B 1, A 2, `applied`; replay lists B, A |
| `test_two_connections_with_reversed_allocation_and_completion_rebuild_to_live` | | each grade through its own connection; rebuild mastery equals live; shadow summary zero |
| `test_a_rolled_back_application_leaves_no_reservation_and_its_retry_takes_the_next` | | an injected failure after the reservation leaves no row and no attempt; the retry takes 2; a second reservation returns 2 |
| `test_a_replay_and_a_regrade_keep_the_attempts_sequence` | | the rows are byte-equal after a rebuild and after a regrade; rebuild after the regrade equals live |
| `test_at_the_tag_each_replayed_attempt_sees_the_windows_and_cache_its_live_write_saw` | | four attempts (three in one second over two items, ids reversed): live windows as applied; replay's LO and item windows and the canonical cache values each attempt computed against equal live's |
| `test_below_the_tag_the_replayed_windows_follow_the_ids` | replay hands B the miss A as history, which live never did | |
| `test_distinct_seconds_replay_alike_at_both_tags[mvp-0.64, mvp-0.65]` | control: one second apart, same windows, cache and mastery | the same |
| `test_the_upgrade_ranks_legacy_attempts_in_id_order_then_new_ones_follow_in_application_order` | | legacy A 1, B 2 (`legacy_order_unknown`); the predecessor's divergent live mastery normalized; shadow zero; a new same-second attempt with a lower id is 3 and folds last; rebuild equals live; a second upgrade does nothing |
| `test_the_field_fsrs_history_chains_a_tie_in_the_ledgers_order[...]` | A first (no prediction) | B first |
| `test_adaptive_difficultys_replay_gives_the_first_surface_to_the_first_in_the_ledgers_order[...]` | A, first surface | B, first surface |
| `test_adaptive_difficultys_stream_keeps_attempts_before_claims_and_opportunities_at_one_time` | id order | sequence order; precedence unchanged |
| `test_the_family_memory_fold_breaks_a_tie_by_the_ledgers_order` | id order | sequence order |
| `test_the_facet_timeline_walks_the_attempts_in_the_projections_order[...]` | A, B; no sequences | B, A; the sequences |

**Fail-first.** The strict xfail stayed strict through the migration, helper and tag commits (`1 xfailed`). With the
seven behaviour files checked out from the tag commit `db3db4d3a7` (and restored after): the old strict-xfail test and
the five at-tag reservation, two-connection, rollback, boundary and upgrade tests fail (`assert [] == [('01ZZ...',
'mvp-0.65')]`, `assert ('01ZZ...A') == ('01ZZ...B')`, the mastery dicts differ), the field, AD, family-memory and
timeline tests fail at the tag on their order and below it on the absent API (`attempt_sequences`, `in_fold_order`,
`snapshot.order`): 12 failed, 7 passed of the then nineteen in the file; with the behaviour all pass. The below-tag
characterizations (`no_sequence_is_reserved...`, `the_replayed_windows_follow_the_ids`, the distinct-second controls)
pass on both.

## Commands and results

Every pytest run went through a script file with explicit targets, `-q -n 1 -p no:cacheprovider`, in a 3G memory
scope under the scratch wrapper (`env -i`, empty `HOME`/`CODEX_HOME`, isolated config dir).

| Run | Result |
|---|---|
| `uv sync --extra dev --extra mobile --extra tui --extra notebook` | installed; `uv pip install --offline pypdfium2==5.14.0` refused (not in the offline cache; 4.30.0 stays installed) |
| Head fixture upgrade (backup API, scratch copy, `upgrade_allowance(UPGRADE_SCRATCH_COPY)`) | applied `[261]`; checkpoint (0, 0, 0); `delete`; `integrity_check` ok; `foreign_key_check` empty; added the table and its autoindex; header 1/1; no companions |
| Migration tests (`test_attempt_application_order_migration`, `test_ingest_job_progress_migration`, `test_migrations`) | 45 passed |
| The seventeen diff files, `test_ad_protected_tables`, `test_table_roles` | 102 passed |
| `test_attempt_order`, `test_rebuild_equivalence`, `test_rebuild_equivalence_review` at the helper commit | 58 passed, 1 xfailed |
| Tag commit's own files (47: the moved successor files, identity pins, effective defaults, CLI snapshot, journey golden, upgrades, placement, untaken episode), `-m "not arc_close"` | 1 failed (`test_teacher_te1_successor`'s mixed tail), 1320 passed, 12 skipped, 3 xfailed; after the fix with `test_upgrades`: 279 passed |
| Fail-first (seven behaviour files from `db3db4d3a7`) | `test_same_second_order` + review: 6 failed, 11 passed; with the consumer tests added: 12 failed, 7 passed |
| `test_same_second_order`, `test_rebuild_equivalence_review`, `test_attempt_order` at the behaviour commit | 35 passed |
| `test_identity_pins`, `test_structure_ratchets`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches`, `test_sqlite_file_copies` | 398 passed |
| Name filter over `scripts/affected_tests.py`'s 1,400 files (`rebuild|replay|equivalence|canonical|projection|timeline|family_memory|field_|outcome|fsrs|review_log|ad2_|ad23|ad3_|ad1_|adaptive|first_surface|attempt_order|same_second|mastery|upgrade|successor|receipt_exact|shadow|regrade|familiar|diagnosis_journey|recall_coverage|apply_attempt|attempt_pipeline|claim|ledger`: 130 files) united with every test file the branch adds or edits: 161 files, five chunks, `-m "not arc_close"` | 1 failed (AD contract), 519 passed, 3 skipped; 7 failed (six journey cases, one timeline stand-in), 411 passed, 4 skipped; 416 passed, 6 skipped, 5 xfailed; 465 passed, 1 skipped; 270 passed |
| After `e8232b746e`: `test_ad23_contract`, `test_diagnosis_journey_golden`, `test_facet_evidence_timeline`, `test_identity_pins` | 414 passed |
| Every other test file naming `SUCCESSOR_CHAIN`, `LATEST_ALGORITHM_VERSION`, the order's names, the moved store methods, `load_events`, family memory, the FSRS history, the canonical ledger or projection, `TABLE_ROLES`, `sqlite_master`, `protected_tables` or `column_classes`: 206 files, six chunks, `-m "not arc_close"` | 2 failed (`test_architecture`'s SQL owners, the J2 migration diff), 1090 passed, 1 skipped, 1 xfailed; 728 passed; 1 failed (a review-feed stand-in), 695 passed, 13 skipped; 571 passed, 1 skipped; 9537 passed, 5 skipped; 126 passed |
| After `5f92a8a15c`'s changes: the three failed files, `test_attempt_order`, `test_same_second_order`, `test_upgrades`, both rebuild-equivalence files, `test_facet_evidence_timeline`, `test_ad23_contract`, the migration test, identity pins, ratchets, effective defaults, CLI snapshot, kill switches, sqlite copies, public tip guards, journey golden, retired config identities | 1 failed (ratchets: `private_patch_sites` +2, `golden_json_lines` +99), 858 passed; after the fix: `test_structure_ratchets`, `test_same_second_order`, `test_identity_pins` 379 passed |
| `tests/test_test_layout.py` alone | 3 passed |
| `tests/test_architecture.py` alone | 18 passed |
| `uv run ruff check` | All checks passed! |
| `uv run lint-imports --no-cache` | Contracts: 45 kept, 0 broken. |
| `uv run python scripts/check_gate_partition.py` | collected 32977: landing 32911 + arc_close 66 |
| `db_generate_reference.py`, then `db_validate_reference.py` (the generated notes then discarded: the landing regenerates them) | generated (16 notes changed or added: the new table's note, the catalog, `practice_attempts`, `grading_evidence`, `schema_migrations`, ten config field notes, `_generated.md`); `"errors": []` |
| The owner-copy scripts on a fresh `learnloop init` vault, and on the demonstration vault (below) | all zero; the counts below |

## What the orchestrator must run on owner copies

On backup-API copies (never a live vault), each at `mvp-0.64` after mvp-0.64's landing, from the landed tip, with the
scratch wrapper's isolation. Two read-only scripts (counts only; they attach the database read-only, write nothing and
call no model):

```python
# order_counts.py <copy root>: exposure and bindings
import json, sqlite3, sys
from contextlib import closing
from pathlib import Path
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

vault = load_vault(Path(sys.argv[1]))
database = VaultPaths(vault.root, vault.config).sqlite_path
out = {"algorithm_version": vault.config.algorithms.algorithm_version}
with closing(sqlite3.connect(f"file:{database}?mode=ro", uri=True)) as connection:
    one = lambda sql: connection.execute(sql).fetchone()[0]
    out["attempts"] = one("SELECT COUNT(*) FROM practice_attempts")
    out["same_lo_same_second_groups"], out["attempts_in_those_groups"] = connection.execute(
        "SELECT COUNT(*), COALESCE(SUM(n), 0) FROM (SELECT COUNT(*) AS n FROM practice_attempts "
        "GROUP BY learning_object_id, created_at HAVING COUNT(*) > 1)").fetchone()
    out["same_item_same_second_groups"] = one(
        "SELECT COUNT(*) FROM (SELECT 1 FROM practice_attempts GROUP BY practice_item_id, created_at "
        "HAVING COUNT(*) > 1)")
    if one("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = 'attempt_application_order'"):
        for basis, n in connection.execute(
                "SELECT basis, COUNT(*) FROM attempt_application_order GROUP BY basis ORDER BY basis"):
            out[f"orders_{basis}"] = n
        out["attempts_without_an_order"] = one(
            "SELECT COUNT(*) FROM practice_attempts a WHERE NOT EXISTS "
            "(SELECT 1 FROM attempt_application_order o WHERE o.attempt_id = a.id)")
        out["orders_without_an_attempt"] = one(
            "SELECT COUNT(*) FROM attempt_application_order o WHERE NOT EXISTS "
            "(SELECT 1 FROM practice_attempts a WHERE a.id = o.attempt_id)")
        out["duplicate_orders"] = one(
            "SELECT COUNT(*) FROM (SELECT attempt_id FROM attempt_application_order GROUP BY attempt_id "
            "HAVING COUNT(*) > 1)")
        out["same_lo_same_second_groups_reordered"] = one(
            "SELECT COUNT(*) FROM (SELECT GROUP_CONCAT(p.id, ',' ORDER BY p.id) AS by_id, "
            "GROUP_CONCAT(p.id, ',' ORDER BY COALESCE(o.sequence, 9223372036854775807), p.id) AS by_sequence "
            "FROM practice_attempts p LEFT JOIN attempt_application_order o ON o.attempt_id = p.id "
            "GROUP BY p.learning_object_id, p.created_at HAVING COUNT(*) > 1) WHERE by_id != by_sequence")
print(json.dumps(out, sort_keys=True))
```

```python
# order_values.py snapshot <state.sqlite> <private out.json> | compare <before.json> <after.json>
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
}
if sys.argv[1] == "snapshot":
    with closing(sqlite3.connect(f"file:{sys.argv[2]}?mode=ro", uri=True)) as connection:
        values = {name: {str(row[0]): list(row[1:]) for row in connection.execute(sql)} for name, sql in QUERIES.items()}
    with open(sys.argv[3], "w") as handle:
        json.dump(values, handle)
else:
    before, after = (json.load(open(path)) for path in sys.argv[2:4])
    print(json.dumps({name: {"changed": sum(1 for k in before[name].keys() & after[name].keys()
                                            if before[name][k] != after[name][k]),
                             "added": len(after[name].keys() - before[name].keys()),
                             "removed": len(before[name].keys() - after[name].keys())}
                      for name in QUERIES}, sort_keys=True))
```

Per copy (keep the JSON value files private; publish counts only):

1. `order_counts.py` at `mvp-0.64`: **same-LO timestamp collision groups** and **participating attempts** (a collision
   group is exposure, not a confirmed inversion: below the tag nothing recorded which was applied first), and the
   same-item groups.
2. `learnloop rebuild --shadow --json --vault "$COPY"` at `mvp-0.64` (comparison 1, predecessor live to predecessor
   shadow: the discrepancies that exist today), then `order_values.py snapshot` (before).
3. `learnloop upgrade --vault "$COPY" --to mvp-0.65`, `learnloop doctor --vault "$COPY"`, `integrity_check`,
   `foreign_key_check`; `order_values.py snapshot` (after) and `compare` (comparison 2: the **activation's value-change
   counts** per table; expected nonzero only where step 2's shadow was nonzero, since the legacy rank is the
   predecessor's order).
4. `order_counts.py` at `mvp-0.65`: **legacy-unknown orders** (`orders_legacy_order_unknown`, expected = `attempts`),
   `orders_applied` (expected 0 on a copy nobody practised on), **missing** (`attempts_without_an_order`) and
   **duplicate or orphaned bindings** (`duplicate_orders`, `orders_without_an_attempt`), all expected 0, and
   `same_lo_same_second_groups_reordered` (0: no applied row yet).
5. `learnloop rebuild --shadow --json` at `mvp-0.65` (comparison 3, **successor shadow changes**: identical semantic
   values and empty `schedule_effects` required), then a second `rebuild` of the copy and `compare` again
   (comparison 4, idempotence: 0 changed).
6. Verify the live databases' SHA-256 unchanged.

On the scratch-built demonstration vault (the diagnosis fixture with its seeded history plus one reversed same-second
pair, at `mvp-0.64`): step 1 gave 1 group, 2 participating attempts; step 2's shadow 2 mastery, 1 facet, 1 schedule
changes; step 3's compare mastery 1 changed (1 added: a learning object the rebuild materialized), schedule 1
changed, surprise 2 changed, facet 0; step 4 nine legacy-unknown orders, no missing, duplicate or orphaned binding, 0
reordered; step 5's shadow 0, 0, 0.

## Limitations

- **Historical order stays unknown.** A same-second pair applied before the upgrade in the opposite order from its ids
  keeps the predecessor's reading; the activation normalizes such a live row to it. Only ties applied at or after the
  tag are exact.
- Tie-order only: an attempt applied after another but stamped earlier (a backdated or imported answer, a clock step)
  still folds by occurrence time, and a live write still reads every committed attempt, whatever its stamp; replay's
  bound excludes the later-stamped ones. Unchanged by decision.
- The readers listed as searched-not-moved keep `(created_at, id)`; the field's own row derivation (`_load`) and the
  FSRS fitter's review log are the ones closest to the moved set.
- An attempt written outside `apply_attempt` (none in production; test helpers that insert rows) has no sequence and
  sorts after the sequenced attempts of its second.

## Judgment calls to read first

1. **No `AUTOINCREMENT`** (above): the order needs only a rowid above every existing row, which holds without it.
2. **The reservation is tag-gated and new-application-only**: below the tag nothing is written, so the activation's
   legacy rank is never interleaved with real application data; replays and regrades never reserve (a missing row on
   replay sorts last in its second rather than taking a number at rebuild time, which would make a second rebuild
   disagree with the first).
3. **A position stays `(created_at, id)`** and its sequence is looked up wherever it is compared, instead of a new
   position type: every existing caller and test keeps its bound, and the SQL bound and Python bound cannot disagree.
4. **The per-item live window gains an id tie-break at the tag** (it had none, so its tie order was SQLite's): at the
   tag it is the application order like its replay bound.
5. **AD's sequences are read through the material view** (the table is PROTECTED by its attempt), and the attempts are
   sorted in `load_events` rather than in `MaterialView.attempts`, whose other callers keep their order.
6. The FSRS fitter's review log and the field's `_load` were left on `(created_at, id)` (searched, not in the design's
   list); say if they should move with this tag.

## What was not verified

- The owner's vaults: no copy opened (the orchestrator's lane, above).
- The full suite, the arc-close gate and the durability lane (WAL, production pragmas); the deferred foreign key is
  exercised in the fast lane and by the migration test on a plain connection.
- Concurrency under real parallel writers (the two-connections test runs them one after the other; the order comes
  from the database under `BEGIN IMMEDIATE`, which serializes them).
- Vault references were not regenerated (the landing does); the generator and validator ran clean, and their output
  was discarded.
- The 206-file run's last five chunks started while the table's writers moved into the attempt store (a pure move);
  the files that touch the moved functions, and the three that had failed, were rerun after it (above).
- `pypdfium2==5.14.0` was not in the offline cache; 4.30.0 stayed installed (no test in these runs needed it).
