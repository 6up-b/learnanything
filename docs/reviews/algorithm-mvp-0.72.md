# mvp-0.72: the difficulty label leaves mastery, and surprise reads AD's forecast (arc H, H3)

Branch `refactor/h3-difficulty-design`, from origin/main `69b0ec9886` (merged at `8d920e5eaa`, and origin/main `1966a33cbf` at `0d4dea79e1`; latest tag `mvp-0.70`; the G2 fix round may take `mvp-0.71`). The design is `docs/reviews/refactor-h3-h6-design.md` (§2.1 Q1 (iii), §2.2 as
the owner decided Q18, §2.3 (i)). The tag is provisional: the orchestrator renumbers at landing. Everything here was
measured on synthetic vaults and fakes; the owner's copies are the orchestrator's (the last section).

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

## One capture point, two records; L4-2 either order

- **One capture point:** the grade's persist step (`_persist_attempt_application`, the live branch), right after
  `record_attempt_outcome`.
- **H3's record there:** the grade-time receipt.
- **L4-2's record there:** `capture_grade_curve(connection, attempt_id, surprise["predicted_score_dist"], version)`
  into its own table. It reads `a` and `b` from the surprise row's `predicted_score_dist`, which H3 keeps as
  mastery's, so it captures mastery's pair: `(discrimination_default, 0)`, or `−priming_b_offset` when primed. It
  never captures AD's `b_scored`.

A trial merge (`git merge-tree`) of this branch with L4-2's tip `937c0b0084` names these conflicts. They are the same
whichever lands first, since each side's hunks are the other's context.

**`src/learnloop/attempts/attempts.py`:**

- **`GradeEvidence` / reads:** H3's `surprise_forecast: Any = None` beside L4-2's
  `recorded_curve: tuple[float, float] | None = None`. Keep both fields.
- **`_belief_update`:** H3 passes `algorithm_version=` to `resolve_item_irt_params` (and its EB gate reads
  `not retired`); L4-2 wraps the same call in `if reads.recorded_curve is None: … else: item_a, item_b =
  reads.recorded_curve`. Merge as L4-2's branch structure with H3's `algorithm_version=` inside it.
- **One semantic call in that merge.** H3's upgrade re-derives history with no item term (§2.3 (i)), while L4-2's
  recorded curves for epochs graded *before* H3's tag hold the label's `b`. Taking L4-2's branch as is would replay
  those epochs on the label's curve, so H3's upgrade would no longer drop the item term from history.
  - My recommendation is `if reads.recorded_curve is None or retired:`, so the seam rules at the tag.
  - For epochs graded at the tag, the recorded curve and the seam agree, because the pair no longer depends on
    content (design note §9).
  - L4-2's freeze then governs vaults below the tag only.
  - If the owner prefers L4-2's freeze to win for pre-tag epochs, keep L4-2's branch unchanged; history's mastery then
    keeps the label for those epochs.

**`src/learnloop/learner/lesson_weight.py` (`recorded_updates`):** L4-2 deletes the `item_irt_params(...)` lines that
H3 gave `algorithm_version=`. Take L4-2's deletion: it reads the recorded curve, which holds mastery's pair at the tag.

**Tag and goldens:**

- **The tag bookkeeping:** `algorithm_versions.py`, the chain and `__all__`; `ops/upgrades.py` and
  `tests/test_upgrades.py`, one row each.
- **The tests that pin the chain's tail:** about 60 files; index shifts plus one set member each.
- **The goldens:** `cli_surface.json`'s default tag, `effective_defaults.toml`, `placement_stored_misses.json`,
  `diagnosis_journey_golden.json` and `grade_application/history.json`. Regenerate these, never hand-merge them.

Where L4-2's migration lands (main took 271 and 272; G2's second round takes 273 and L4-2 274), its migration tests conflict with main's, not with this branch.

Clean either way: `db/stores/attempts.py` (H3 does not touch `record_attempt_outcome`) and the persist step (H3's call
follows the outcome; L4-2's capture is inside it).

## Consequences the gate found (selection readers on "no item term", Q6)

The design kept every selection reader on the seam with no item term (Q6). The affected set shows what that costs
where a feature relied on the label telling items of one LO apart. These are not defects: they are the label's
absence, and AD's `p̄` for selection is a later question, item by item.

- **Placement's first-review check** (`placement/state.py`, `choose_check_items`, "the median predicted success"):
  every never-attempted item of the LO now predicts alike, so the median falls to the item ids. It is still
  deterministic. Test: `test_assumed_known.py::test_from_the_label_retirement_the_check_choice_reads_no_label`.
- **The delayed check's pick** (`delayed_checks.py`, the item nearest the practice band, from the data-capture tag):
  items of one LO tie, so the pick is the uniform draw its receipt records. Test:
  `test_data_capture_a6_delayed_pick.py::test_from_the_label_retirement_an_los_items_tie_and_the_pick_draws`.
- **The label-miscalibration check** (`learner/calibration.py`, doctor's `difficulty:miscalibrated`): it compares
  the answers with mastery's curve, which no longer reads the label. So it now flags items that play easier or
  harder than their LO, and its wording still speaks of the label's `b`. It goes with the label's other readers in
  H5 or H6 (Q9's neighbour).
- **The plan's next step** weighs labelled items differently. One C1 journey now takes an item where it took the
  fresh reading. That test is checked at the tag before.
- **Readers of the surprise row's direction** (the re-probe on repeated prediction errors, the follow-up gate)
  now see surprise against AD's forecast wherever AD made one. A mastery state set by hand, as one probe test does,
  no longer makes failures surprising; that test runs at the tag before.
- **Fast-track placement:** the assumed-known tests' fixture states that "items carry authored difficulties so the
  incumbent's predicted success orders them". Those tests now run at the tag before (`assumed_known_helpers`).

## History and replay

- **No AD replay over history:** at the upgrade (`Link(mvp-0.72, whole_vault_rebuild)`) every mastery row is replayed
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
  - One is open and pinned to the tag before: IH4's twin claims (ledger H-5).
- **After merging origin/main (`1966a33cbf`):**
  - the 25 failing files, plus every test file the merge changed: 680 passed;
  - the pins, ratchets, architecture, layout, upgrade, CLI surface, the replay guards
    (`test_replay_writes_no_ledger.py`, `test_gate_records_survive_replay.py`, `test_replay_keeps_diagnosis_ids.py`),
    every golden this tag moved, the seam guards and the migrations test: 1220 passed. The diagnosis journey golden
    and two ratchets were then regenerated or raised with reasons, and pass;
  - the two gates collect every test once (34716: landing 34650 and arc close 66).
- **Lint:** ruff clean; lint-imports 55 kept, 0 broken.
- **Not run here:** the whole landing gate and the arc-close gate in one piece, and the durability lane.

## The owner-copy procedure (for the orchestrator; counts only into tracked files)

Run on backup-API copies (`learnloop.db.copies.copy_tree_with_databases`) of one predecessor backup per vault, through
the scratch wrapper, with one `--as-of` for every vault. Never on a live vault.

1. **On the predecessor copy** (at `mvp-0.70`, or `mvp-0.71` if G2's fix round lands first), record the database
   hash. Run `scripts/difficulty_receipt_coverage.py "$COPY"` and
   `scripts/difficulty_four_way.py "$COPY" --out "$PRIVATE/four_way.json" --as-of <one instant>`. Arm (f)
   (`f_label_off_and_receipt`) is H3 on history exactly: no item term, surprise from a bound serve-time receipt, else
   mastery. History has no grade-time receipt, so the grade-time tier never appears there. From arm (f) against
   arm (a), report the three numbers the earlier lane gave:
   - **mastery movement:** LOs changed of all, mean and max logit-mean shift (vault 2 gave 8 of 21, mean +0.106, max
     +0.606);
   - **queue rank correlation:** Spearman and top-10 overlap (vault 2: 0.948 and 9 of 10; vault 3: 0.967);
   - **surprise direction flips:** rows whose `surprise_direction` changes (0 on every vault), plus rows above the
     follow-up threshold (vault 2: 3 against 4).
2. Run `learnloop rebuild --shadow --json` on the predecessor copy. Then `learnloop upgrade --vault "$COPY" --to
   mvp-0.72`, `learnloop doctor`, and the successor's shadow rebuild. Report counts:
   - LOs whose mastery changed, which must equal arm (f)'s count from step 1, and the mean and max shift;
   - surprise rows by `prediction_source` (expected: `serve_receipt` only where a bound serve receipt existed, all
     others `mastery`), and rows whose direction changed;
   - stored follow-up actions before and after;
   - grade-time receipts, which must be 0 (the upgrade replays no AD over history);
   - subject trace rows carrying `kl_observation` against trained subject rows, which must be equal;
   - due dates moved, and the queue's Spearman and top-10 overlap against step 1's arm (a);
   - lesson weight, facet and capability deltas as counts.
3. Rebuild again. The semantic digests must agree with step 2. Check the original database's hash is unchanged.
   Report before any live upgrade.

After the live upgrade, the first graded answers show the new tier: their surprise rows read `grade_receipt` (or
`serve_receipt` from a plan step) and `forecast_receipts` gains one `item_unassisted_success_at_grade` row per live
answer AD can read.
