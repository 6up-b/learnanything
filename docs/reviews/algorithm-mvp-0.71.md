# mvp-0.71: the difficulty label leaves mastery, and surprise reads AD's forecast (arc H, H3)

Branch `refactor/h3-difficulty-design`, from origin/main `69b0ec9886`, with origin/main merged at `8d920e5eaa`,
`0d4dea79e1`, `e66c055d84` and `473005e9c9` (`604f17b706`: G2's second round with migration 273). The tag before it is
`mvp-0.70` (the probe router). H3 lands first and takes `mvp-0.71`; L4-2 follows as `mvp-0.72` with migration 274 and
merges onto this branch (its integrator's note is below). The design is `docs/reviews/refactor-h3-h6-design.md`
(§2.1 Q1 (iii), §2.2 as the owner decided Q18, §2.3 (i)). Everything here was measured on synthetic vaults and fakes;
the owner's copies are the orchestrator's (the last section, runnable from an `mvp-0.70` copy).

| Commit | What |
|---|---|
| `113490dcfb` | The tag: one constant, the chain entry, its set and predicate, one upgrade row, one test row; the seam, surprise, the grade-time receipt, the KL measure; their tests; the structure ratchet raised for the two files that grew |
| `7d8b7e619e` | Tests that pin the chain's tail moved by one; identity pins and goldens regenerated (what moved: below) |
| `072488b416` | The grade-time receipt's id keyed by its attempt; the test of a writer between the read and the write |
| `30751316f1` | Tests whose subject relied on the label run at the tag before; two tests of what the retirement does there |
| `42be2d8a8c` | This record, the design note's decision, the status rows, ledger H-4 |
| `0d4dea79e1` | origin/main merged (`1966a33cbf`) |
| later | The remaining receipt counts, the joint grading golden, IH4's twins (ledger H-5); the merged diagnosis journey golden and the raised ratchets; the vault's generated references |

No migration, no config key, no kill switch (owner rule 2026-11-16), no made-up constant (the forecast is AD's own
prediction, the priming shift is mastery's existing `priming_b_offset`), no prompt changed.

## The owner's decision (Q18, 2026-11-24)

**(a + b):** surprise's prediction comes from AD's serve-time receipt when the answer's presentation has one, and a
grade-time AD forecast receipt is recorded for every graded answer (Reader checks, the tutor, the phone, anything not
served through the plan). Built with the **AD-native KL** (the KL of AD's own posterior after the answer from before
it), recorded as a measure beside the existing surprise: it decides nothing, and it joins the gated-experiments
follow-up for later comparison. History: no AD replay over old answers; they fall back to mastery, marked.

On timing, the orchestrator chose **(A)**: the AD read is read-only and runs before the grade's write transaction; the
receipt and the surprise row are written in the grade's own transaction.

## What changes at the tag

1. **Mastery's IRT seam reads no label.** `item_irt_params` and `resolve_item_irt_params` (`learner/mastery.py`) return
   `(a, 0.0)` at the tag, for every caller (mastery, surprise's mastery curve, the scheduler, selection rewards,
   probes, placement's predictor, the field's outcomes, the teacher's brief and checks, lesson suggestions, lesson
   weight, delayed checks, AD's forecasters). The EB path never runs at the tag. A primed answer keeps its shift
   (`b = −priming_b_offset`), applied by the callers as before. Every caller now passes the vault's tag; the guard
   (`tests/test_difficulty_kinds_apart.py`) checks each caller's expression and that every caller reads no label at
   the tag. Placement's predictor version names the absent item term, so its identity moves deliberately (C1).
2. **Surprise is scored against AD's forecast made before the answer**
   (`adaptive_difficulty/surprise_forecast.py`), in this order:
   - the **serve-time receipt** (`ad_threshold@subject`, or `ad_threshold_repeat@subject` for a repeat) of the
     answer's plan presentation, when the answer binds it by the attempt door's own rule (`bindable_presentation`),
     the receipt is `ok`, has a `p`, is the item's, and read nothing after the serve (`valid_for_serve`);
   - else the **grade-time receipt** (below);
   - else **mastery's own prediction** (no item term), as before.

   The scored curve is `b' = μ − logit(p̄_eff)/a` with `p̄_eff = σ(logit p̄ + a·offset)` for a primed answer: the
   shift mastery applies. The surprise row's `predicted_score_dist` keeps mastery's `a`, `b` and
   `expected_correctness`. Those are the keys `lesson_weight.py` and L4-2's capture read. It adds
   `prediction_source` (`serve_receipt`, `grade_receipt` or `mastery`), `receipt_key`, `forecaster`, `p_ad`,
   `p_scored` and `b_scored`. Bayesian surprise still describes the mastery update. The FSRS interval factor still
   reads mastery's residual. AD reaches neither mastery nor scheduling.
3. **The grade-time receipt** (`adaptive_difficulty/grade_forecast.py`) is a new kind,
   `item_unassisted_success_at_grade`: scope `attempt`, decision kind `grade`, binding kind `graded_attempt`,
   forecaster `ad_threshold@grade`, version `ad-threshold-grade-v1`. Its key is `kind:graded_attempt:<attempt>:<forecaster>`.
   - **What it holds:** AD's subject-view `p̄`, the three category probabilities and `p_band`. Its inputs are the
     state hash, warmth, features, signals, loadings and `events_fingerprint`, the fingerprint of the AD events the
     forecast read. `source_attempt_id`, `practice_item_id` and `learning_object_id` are columns, and
     `inputs_as_of = created_at =` the grade's instant.
   - **When it is written:** only for a live answer (not on replay, not on a regrade) and only when AD's successor and
     its receipts are on.
   - **When it is not written:** a withheld (A8) or covered item gets none, as at a serve.
   - **No migration:** `forecast_receipts` constrains `kind`, `scope`, `binding_kind` and `decision_kind` only in code
     (`scheduling/forecast_receipts.py`). The DB CHECKs are on status, the `p` range,
     binding ⇔ censor reason, and `inputs_as_of ≤ created_at`.
   - **Its id** is a function of its attempt (`ids.keyed_ulid`: the attempt id's time, and randomness from the
     receipt key's digest). Drawn from `ids.new_ulid` it would shift every id the grade mints after it. Drawn from a
     stream of its own it would differ between two runs of one history, which the comparison tests (AD's protection
     contract, the receipt repairs, the prediction snapshots) caught.
   - **A failure never costs the grade:** `safe_grade_receipt` logs and returns none, and surprise falls back.
4. **The AD-native KL.** From the tag, AD's replayer adds `kl_observation` to the detail of each trained answer's
   subject-view trace row: `{"total", "weights", "states"}` in nats (`ad_attempt_trace.detail_json`, a DERIVED table;
   no schema change).
   - **What it computes:** `observation_kl` in `adaptive_difficulty/replay.py`. The bank is a mixture over its grid
     points, so the KL is exact by the chain rule. It is the KL of the posterior grid weights from the prior ones
     (`w_k ∝ w'_k / z_k`), plus the posterior-weighted KL of each point's Gaussian. For a rank-one update that is the
     update record's `information`.
   - **When it appears:** AD's replayer writes it, so a live answer's KL appears with AD's next derived rebuild, as
     every trace row does.
   - **Where it is absent:** a repeat (no AD update) and an answer AD does not train on carry none. Below the tag the
     trace is byte-identical (the setting enters AD's settings key only when on).
   - **What reads it:** nothing.

## Timing (the orchestrator's first ask)

The AD read was timed on synthetic vaults through the real grade (`complete_self_graded_attempt`), at -n 1 on this
desktop. The miss and hit columns are the grade with the forecast read; the self-grade column is the grade without
it.

| History | Snapshot miss | Snapshot hit | Self-grade without the read |
|---|---|---|---|
| broad, about 20 answers | 20 ms | 18 ms | 14 ms |
| served, 18 answers | 25 ms | 22 ms | 13 ms |
| scaled, 158 answers | 72 ms (max 119) | 67 ms | 20 ms |

- **The cost is linear in history.** It is about 0.4 ms per answer, and loading AD's events dominates it: the
  fingerprint cache saves the replay but not the load, so a hit costs nearly what a miss does.
- **Why (A):** 20 to 70 ms on a self-grade is not perceptible, and one consistent row with one write path is worth
  more than the milliseconds.
- **Follow-up (C), not in this landing:** a per-vault change stamp for AD's events load (status file).

## The read and the write are two snapshots

**The ordering.** The forecast is read before the grade's write transaction (`with_grade_forecast`, called in
`apply_attempt` before `repository.atomic()`), so another writer (a background job, the phone) can commit in between.
The forecast is still "AD before this answer": this answer is not written until the transaction, and the receipt
records the events it actually read (`inputs.events_fingerprint`).

**When they differ:** another answer or reading event committed after the read and before the write.

- The recorded forecast stands. It is AD as of the read, which is before this answer, and it lacks only the
  concurrent event.
- The grade scores against it in the same transaction.
- Replay and a regrade read the receipt (`attempt_forecast`, by `source_attempt_id`) and never recompute it, so the
  row is reproduced exactly whatever AD has become.
- The fingerprint lets an audit tell such a receipt from one whose events are exactly AD's events before the
  attempt. Nothing decides on it.

`tests/test_surprise_reads_ad_forecast.py::test_a_writer_committing_between_the_read_and_the_write_leaves_the_recorded_forecast_standing`
commits a second answer between the read and the write. The receipt's fingerprint is the read's and differs from AD's
just before the write; surprise reads the receipt; a rebuild reproduces both.

## For L4-2's integrator (L4-2 merges onto this tag as mvp-0.72)

- **One capture point:** the grade's persist step (`_persist_attempt_application`, the live branch), right after
  `record_attempt_outcome`.
- **H3's record there:** the grade-time receipt.
- **L4-2's record there:** `capture_grade_curve(connection, attempt_id, surprise["predicted_score_dist"], version)`
  into its own table. It reads `a` and `b` from the surprise row's `predicted_score_dist`, which H3 keeps as
  mastery's, so it captures mastery's pair: `(discrimination_default, 0)`, or `−priming_b_offset` when primed. It
  never captures AD's `b_scored`.

A trial merge of L4-2's tip `937c0b0084` onto this branch names the conflicts below; the resolution is the
orchestrator's (accepted 2026-11-24).

**`src/learnloop/attempts/attempts.py`:**
- **`GradeEvidence` / reads:** keep both fields, H3's `surprise_forecast: Any = None` and L4-2's
  `recorded_curve: tuple[float, float] | None = None`.
- **`_belief_update`:** take L4-2's `recorded_curve` branch, with H3's `algorithm_version=` inside it, and the
  condition `if reads.recorded_curve is None or retired:`.
  - Why: H3's upgrade re-derives history with no item term, so the seam rules at and above this tag.
  - For an epoch graded at the tag, the recorded curve and the seam agree, because the pair no longer depends on
    content.
  - L4-2's recorded curves govern vaults below the tag.

**`src/learnloop/learner/lesson_weight.py` (`recorded_updates`):** take L4-2's deletion of the `item_irt_params(...)`
lines. It reads the recorded curve, which holds mastery's pair at the tag.

**The tag:** L4-2's constant follows `LABEL_RETIRED_ALGORITHM_VERSION` in the chain.
- Bookkeeping: `ops/upgrades.py` and `tests/test_upgrades.py` take one row each after this tag's.
- The tests that pin the chain's tail shift by one more.
- Regenerate, never hand-merge: the CLI surface, the effective defaults, the identity pins, and the placement,
  diagnosis journey and grade application goldens.

Its migration 274 meets main's migration tests, not this branch's. `db/stores/attempts.py` and the persist step merge
cleanly: H3 does not touch `record_attempt_outcome`, and H3's call follows the outcome.

## Consequences the gate found (selection readers on "no item term", Q6)

The design kept every selection reader on the seam with no item term (Q6). The affected set shows what that costs
where a feature relied on the label telling items of one LO apart. These are not defects: they are the label's
absence, and AD's `p̄` for selection is a later question, item by item.

- **Placement's first-review check** (`placement/state.py`, `choose_check_items`, "the median predicted success"):
  every never-attempted item of the LO now predicts alike, so the median falls to the item ids. It is still
  deterministic. Test: `test_assumed_known.py::test_from_the_label_retirement_the_check_choice_reads_no_label`.
- **The delayed check's pick** (`delayed_checks.py`, the item nearest the practice band, from the data-capture tag):
  items of one LO tie, so the pick is the uniform draw its receipt records. That draw is seeded, logged and
  replayable:
  - **seeded:** `delayed_checks.seed_for(seed_key)`, where the key names a persisted decision (`decision:<id>` for a
    measurement, the lesson and LO for a teacher's retention check, `dry:<lo>` for a read). It is never the
    candidates or the run;
  - **logged:** the receipt carries the considered items with their predictions, the tied set (sorted by item id),
    `n`, the propensity `1/n`, the seed, the draw and the choice, and the commitment's provenance stores it;
  - **replayable:** `tied[int(draw·n)]` from the receipt alone. `test_serve_tie_breaks.py` checks this in every
    candidate order.

  Test: `test_data_capture_a6_delayed_pick.py::test_from_the_label_retirement_an_los_items_tie_and_the_pick_draws`.
- **The label-miscalibration check** (`learner/calibration.py`, doctor's `difficulty:miscalibrated`): it compares the
  answers with mastery's curve, which no longer reads the label. So from the tag it flags items that play easier or
  harder than their LO, and its message now says that and that no difficulty label is read (ledger H-4, fixed).
- **The plan's next step** weighs labelled items differently. One C1 journey now takes an item where it took the
  fresh reading. That test is checked at the tag before.
- **Readers of the surprise row's direction** (the re-probe on repeated prediction errors, the follow-up gate)
  now see surprise against AD's forecast wherever AD made one. A mastery state set by hand, as one probe test does,
  no longer makes failures surprising; that test runs at the tag before.
- **Fast-track placement:** the assumed-known tests' fixture states that "items carry authored difficulties so the
  incumbent's predicted success orders them". Those tests now run at the tag before (`assumed_known_helpers`).

## Ties on the serve path (ledger H-5)

**What failed.** At the tag IH4's twin tests split in most runs: one twin ended a block early and served one more
block. They split with fixed hash seeds too.

**The read that differed.** The decision's measurement (`daily_plan/measurement.py`) reserves a delayed check on the
decided LO through the pick above. With the label retired, the LO's items tie, so the seeded draw decides. Its seed
names the decision, and each twin's decision id is a fresh ULID. So the twins reserved different items, and the
reserved item is withheld from the open block (`intent_check_waiting`).

**Production is not nondeterministic.** Given the persisted decision, the pick is fixed and replays from its receipt.
What was missing was the tests' pin: the router's other seeded draws are pinned by default (`tests/pinned_draws.py`),
and this one was not.

**The fix:**
- the seed is one module function, `delayed_checks.seed_for`;
- `pinned_draws` pins it as the `delayed_pick` family;
- IH4's twin pin gives both twins production's seed of one pinned decision;
- IH4's file is back at the head; it passed 5 of 5 runs, where it failed 5 of 6 before.

**The guard.** `test_serve_tie_breaks.py` serves one day at the head in three processes: hash seed 0, hash seed 1,
and hash seed 0 with SQLite's `reverse_unordered_selects` on every connection. All three must give the same staged
picks, served steps and measurement picks, and the day must meet a tie. With the draw unpinned it fails (negative
control run); pinned, it passes.

**The staged pick's own last tie-break** (`LaneQuotaChooser`: lane share, lane rank, planner value, then the
candidate's position in the feasible list) depends on the list's build order. The guard's reversed row order does not
move it.

## History and replay

- **No AD replay over history:** at the upgrade (`Link(mvp-0.71, whole_vault_rebuild)`) every mastery row is replayed
  with no item term, and every surprise row is rebuilt from its receipt.
- **Answers graded before the tag** have no grade-time receipt. They read their serve-time receipt where one binds,
  else mastery, marked `prediction_source: "mastery"`.
- **The rebuild writes no receipt.** The replay guard (`tests/test_replay_writes_no_ledger.py`) passes at the tag, and
  `test_a_rebuild_reproduces_every_surprise_row_and_writes_no_receipt` rebuilds twice and compares every surprise row
  and every grade-time receipt.
- **Below the tag** (a vault at mvp-0.70) the predecessor runs unchanged: label, EB if switched on, mastery-only
  surprise with no source keys.

## Pins, goldens and tests that moved

- **Identity pins** (`tests/goldens/identities.toml`):
  - `A1-A4.manifest_hash.init`, `C3.boundary.init`, `C3.boundary_offer.init`, `C3b.chooser`, `C3b.chooser_offer`,
    `C3b.start_key`, `C3b.start_key_offer`, `C5.init` and `C6.init` hash the vault's tag.
  - `C1.init` moves because placement's predictor version names the absent item term: another predictor from the
    same config.
- **Effective defaults:** the tag line only.
- **`due_queue` (14 goldens):** predicted correctness, expected skill gain, practice information, gradient fit,
  placement's predicted success and the selection reward lose the item term (`item_demand_vector.difficulty_b` is 0).
  The order changed in 10 of 14.
- **`grade_application/history`:** the surprise rows gain their source, `p_ad`, `p_scored` and `b_scored`, and their
  predictive surprise and `sigma_z` move. 11 grade-time receipts are added, and ulid placeholders renumber around them.
  Mastery's `expected_correctness` is unchanged: that vault's items carry no label that moved the seam.
- **`diagnosis_journey`:** the tag string, the surprise rows' source fields, the grade-time receipts, and mastery,
  predicted correctness and the conceptual-slip bonus where an item had a label.
- **`mastery_seed_replay`:** `lo_svd_definition`'s mean and variance in two scenarios.
- **`placement_stored_misses`:** the tag in its manifest.
- **Structure ratchet:** `attempts.py` 5831 → 5853 (the forecast threaded through the grade's input, reads, evidence,
  surprise call and receipt write; the logic lives in AD's two new modules) and `scheduler.py` 4442 → 4443.
- **Import contract:** one frozen edge, `attempts.attempts -> adaptive_difficulty.surprise_forecast`, with its
  reason. AD reads attempts only through `salience_firewall`, already frozen, and its guard refuses `attempt_surprise`,
  an unclassified table, inside its operations.
- **Two tests now pin the tag before the retirement:** `test_placement_unevidenced_return.py` and
  `test_rebuild_equivalence_review.py::test_a_live_write_is_the_same_below_and_at_the_tag` used the latest tag to mean
  "the switch's own tag". The retirement moves the queue and mastery on its own, so they now compare at
  `PROBE_ROUTER_ALGORITHM_VERSION`, the newest tag before it.

New tests are in `tests/test_surprise_reads_ad_forecast.py` (8):

- the source per answer;
- a rebuild reproduces the rows and writes no receipt;
- a regrade re-reads the first forecast;
- history falls back to mastery, marked;
- the label does not move mastery;
- the KL from the tag on, none below;
- the receipt is stamped at the grade's instant;
- a writer between the read and the write.

The seam guards are in `tests/test_difficulty_kinds_apart.py` and `tests/test_item_parameters.py`.

## Proof

- **The affected set by import:** `scripts/affected_tests.py --files` over the branch's source and test changes
  selected 1108 files. They ran in eight chunks with `-m "not arc_close"`: 27,825 passed and 61 failed in the first
  pass.
  - Every failure was read. Each is a consequence named above, a test pinned to the latest tag as "its own tag", a
    count of every receipt or AD prediction, or a grade-time receipt id drawn from a per-process stream (now keyed).
  - All are fixed in `072488b416`, `30751316f1` and the commits after them.
  - IH4's twin claims were the last; their root cause and fix are in "Ties on the serve path" (ledger H-5).
- **After merging origin/main (`1966a33cbf`):**
  - the 25 failing files, plus every test file the merge changed: 680 passed;
  - the pins, ratchets, architecture, layout, upgrade, CLI surface, the replay guards
    (`test_replay_writes_no_ledger.py`, `test_gate_records_survive_replay.py`, `test_replay_keeps_diagnosis_ids.py`),
    every golden this tag moved, the seam guards and the migrations test: 1220 passed. The diagnosis journey golden
    and two ratchets were then regenerated or raised with reasons, and pass;
  - the two gates collect every test once (34716: landing 34650 and arc close 66).
- **After H-5's fix, H-4 and merging origin/main `88c0a42823` (`e66c055d84`):**
  - the affected set by import over the branch's source and tests (1111 files), plus every test file that reaches the
    daily plan, the objective, measurement, the teacher or the pinned draws: 1196 files in eight chunks, 29,290 passed
    and 0 failed;
  - pins, ratchets, architecture, layout, pinned draws and migrations: 438 passed;
  - the two gates collect every test once (34733: landing 34667 and arc close 66).
- **Lint:** ruff clean; lint-imports 55 kept, 0 broken.
- **Not run here:** the whole landing gate and the arc-close gate in one piece, and the durability lane.

## The owner-copy procedure (for the orchestrator, from an mvp-0.70 copy; counts only into tracked files)

Per vault, through the scratch wrapper (`env -i`, scratch `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`, `TMPDIR`), from
the repository root at this tip. `$BACKUP` is a backup of the vault at `mvp-0.70`; `$WORK` and `$PRIVATE` are outside
every checkout and every live vault. Use one `$AS_OF` for every vault (for example `2026-11-24T00:00:00Z`). The three
scripts refuse a path under `~/learnloop-vaults` or `~/learnloop-retired`; each hashes the copy's databases before and
after it reads, and fails on a change.

```sh
# 0. Two copies of the predecessor (backup API), and the original's hash.
uv run python -c "import sys; from pathlib import Path; from learnloop.db.copies import copy_tree_with_databases as c; \
  [c(Path(sys.argv[1]), Path(d)) for d in sys.argv[2:]]" "$BACKUP" "$WORK/a" "$WORK/b"
sha256sum "$BACKUP"/state.sqlite > "$PRIVATE/original.sha256"

# 1. On copy a (mvp-0.70): coverage, the four-way replay (arm f is this tag on history exactly), the before snapshot.
uv run python scripts/difficulty_receipt_coverage.py "$WORK/a" --out "$PRIVATE/coverage.json"
uv run python scripts/difficulty_four_way.py "$WORK/a" --out "$PRIVATE/four_way.json" --as-of "$AS_OF"
uv run python scripts/label_retirement_counts.py snapshot "$WORK/a" --as-of "$AS_OF" --out "$PRIVATE/before.json"
uv run learnloop rebuild --shadow --json --vault "$WORK/a" > "$PRIVATE/shadow_a.json"

# 2. Copy b: the upgrade, the doctor, the successor's shadow rebuild, the after snapshot, the comparison.
uv run learnloop upgrade --vault "$WORK/b" --to mvp-0.71
uv run learnloop doctor --vault "$WORK/b"
uv run learnloop rebuild --shadow --json --vault "$WORK/b" > "$PRIVATE/shadow_b1.json"
uv run python scripts/label_retirement_counts.py snapshot "$WORK/b" --as-of "$AS_OF" --out "$PRIVATE/after.json"
uv run python scripts/label_retirement_counts.py compare "$PRIVATE/before.json" "$PRIVATE/after.json"

# 3. Rebuild again: the semantic digests agree with step 2; the original is untouched.
uv run learnloop rebuild --shadow --json --vault "$WORK/b" > "$PRIVATE/shadow_b2.json"
sha256sum -c "$PRIVATE/original.sha256"
```

**What to report, counts only:**

1. **From step 1, the four-way's stdout line for `f_label_off_and_receipt`,** set against the three numbers the
   earlier lane gave for arm (b) (H3's mastery path):
   - **mastery movement** (`mastery changed n/N`, delta mean and max): vault 2 gave 8 of 21, mean +0.106, max +0.606;
     vault 1 nothing changed (design note §1 and §10.1 for vault 3);
   - **queue rank correlation** (`spearman`, `top-10 overlap`): vault 2 gave 0.948 and 9 of 10, vault 3 0.967;
   - **surprise direction flips** (`direction changed`): 0 on every vault. Also the rows above the follow-up
     threshold: vault 2 gave 3 against arm (a)'s 4.
2. **From step 2's `compare`:**
   - `mastery_changed` and `mastery_delta_logit_mean` must equal arm (f)'s mastery line;
   - `surprise_direction_changed`, with its transitions;
   - `due_items_moved`;
   - `queue_spearman` and `queue_top10_overlap`, against step 1's arm (f).
3. **From the `after_counts` of step 2's `compare`:**
   - `surprise_by_source`: `serve_receipt` only where a bound serve receipt existed (0 on the Nov 23 copies), every
     other row `mastery`;
   - `grade_time_receipts` must be 0, since the upgrade replays no AD over history;
   - `ad_rows_with_kl` must equal `ad_trained_subject_rows`;
   - `attempts_with_gate_records`, against `before.json`'s count. A rebuild keeps them since H-1;
   - integrity `ok`, and 0 foreign-key violations.
4. **From the doctor and the shadow rebuilds:** the doctor's issue counts by code. `difficulty:miscalibrated` now
   reads "plays easier/harder than its learning object", per H-4. Also whether `shadow_b1` and `shadow_b2` report the
   same digests, and the original's `sha256sum -c` line.

After the live upgrade, the first graded answers show the new tier: their surprise rows read `grade_receipt` (or
`serve_receipt` from a plan step), and `forecast_receipts` gains one `item_unassisted_success_at_grade` row per live
answer AD can read.
