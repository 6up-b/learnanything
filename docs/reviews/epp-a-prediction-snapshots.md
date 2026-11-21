# EPp, first part: prediction snapshots on new forecast receipts

Evidence packets spec (`docs/specs/spec_evidence_packets_v1.md`) §7.7, §8 EPp, §9, §10; the first of EPp's three
parts ("contract and enrichment"). The other two, the repeat-presentation receipts (`ad_threshold_repeat@*`) and
the SR-2/SR-3 receipt repairs, are separate later steps and were not started. Receipts only: no migration, table,
config key, algorithm tag, kill switch or prompt change; no extra receipt row; no reader of the new fields.

- **Base:** `3f42da228a` (origin/main). **Branch:** `ep/epp-a-snapshots`.
- **New modules:** `src/learnloop/scheduling/prediction_snapshots.py` (the writer's snapshot, shared by the
  generic receipt writer and the VOI writer) and `src/learnloop/adaptive_difficulty/snapshot_parts.py` (what AD's
  serve-time forecasts state). **New function:** `adaptive_difficulty/predict.py::category_mixture`.
- **Changed:** `scheduling/forecast_receipts.py` (`ForecastReceipt.snapshot`, one call in `record_receipts`),
  `scheduling/voi_forecasts.py` (`record_forecast`), `adaptive_difficulty/serving.py` (`threshold_receipts`: the
  loop names its item spec once, computes the categories and passes the snapshot; nothing else in the file),
  `adaptive_difficulty/forecasters.py` (the two in-process forecasters pass a snapshot),
  `adaptive_difficulty/material_view.py` and `protected_tables.py` (the snapshot's own withholding rule).

## 1. The snapshot's shape

Everything rides in JSON bodies the receipt already has. `inputs_json`, its digest, the receipt key, `p`, every
column, `parameters_json` and the producer's own forecast and version keys are untouched (the writer only adds
keys it does not find: `setdefault`).

### `forecast_receipts.versions_json.snapshot` (schema `prediction_snapshot/1`)

| Field | Source | Absent when |
|---|---|---|
| `cutoff.cutoff` | the producer's `SnapshotParts.cutoff`, `Cutoff.to_dict()` (EP0t's serialization, its `approximate` list inside) | the producer states none: `null`, with `cutoff.absent` = "the producer does not state the evidence cutoff it read under" (or the producer's own reason) |
| `cutoff.source` | the producer's reference to what it read (AD: `ad_state_hash`, `replay_version`, the `item_serve_inputs` receipt key `plan_presentation:<id>`, the time spec and warmth were read at, the protection epoch; the challenger: its attempt-row count, digest and latest time) | the producer gives none: `null` |
| `cutoff.inputs_as_of` | `{original, recorded, status}`: the producer's `inputs_as_of` as given, the clamped value the column keeps (unchanged clamp), and `exact` (readable, not after the issue time), `unknown` (None or empty) or `invalid` (after the issue time) | never; `original` is `null` when none was given |
| `target.target` | `PredictionTarget.to_dict()`: stated by the producer, else derived by the writer from the columns (item at `item_content_hash`, learning object, facet; action = `decision_kind`/`decision_ref`; horizon = the binding kind; anchor = the first bound id column) | the receipt names no item, learning object or facet and the producer states none: `null`, with `target.absent` |
| `target.target_hash` | `PredictionTarget.target_hash()` (EP0t, pinned) | with the target |
| `target.stated_by` | `producer` or `writer` | with the target |
| `target.unversioned` | the fields the writer could not version: a derived target's event and resolver versions are written `<event>@unversioned` and `<binding_kind>@unversioned` and listed here, never invented | empty for a stated target |
| `provenance` | `forecaster`, `forecaster_version`; for a model forecast (the receipt's versions name a `prompt` or `model`) `model_call: {model, prompt_version, call_receipt_id: null, call_receipt_absent}` (the writer is not given the call's receipt id: recorded absent, not looked up); then the producer's own entries | never |
| `binding` | `{kind, censor_reason}` from the receipt | never |

### `forecast_receipts.forecast_json` additions

| Key | Content |
|---|---|
| `distribution` | `{unit, event, outcomes, event_outcomes, reason}`. A producer's categorical distribution (AD thresholds: unit `ad_category3`, outcomes `{"0","1","2"}`, event outcomes `["2"]`); otherwise binary: `{"event": p, "not_event": 1 - p}` with `p` the body's own `p`. A forecast not issued: `outcomes: null`, `reason` set |
| `reason` | only where no forecast was issued: the status (`failed`, `refused_spend`) or `no_forecast` (status ok, no `p`) |
| `p_categories` (thresholds only; the key existed as `null`) | the three category probabilities, unrounded floats (JSON round-trips them exactly) |

### Producers in this part

| Producer | Cutoff | Target | Distribution | Provenance |
|---|---|---|---|---|
| `ad_threshold@subject`, `@subject_uniform`, `@lo` | `Cutoff.ad_replay(None)` (the serve's `RP.snapshot` reads every readable event, protection through the serve's material view; nothing approximate: at the serve, now is then) | item at its served revision (`item_revision`), LO, each canonical facet, the surface group with its source (`surface_group_with_source`, the key equal to `replay.surface_group`'s); unit `ad_category3`; action `serve`/item; horizon `presentation`; anchor the presentation; event `ad_category:ad_priors_v1`; resolver `ad_forecast_scores_v1` | categorical (§2) | prior and hyper versions; likelihood `graded_response`, version `ad-threshold-v1`, source `adaptive_difficulty.model.category_probabilities`, constants A, LAPSE, KAPPA, TAU0; fitted artifact `ad_state` by state hash; training cutoff `ad_replay`, as_of none; `mixture`: `bank`, `uniform` or `lo_view` |
| `mastery_ekf` | `Cutoff.current()` (it reads the persisted mastery states as they stand) | the same members, unit `binary` | binary | version hash; training cutoff absent ("the persisted mastery states keep no cutoff of the evidence they fold") |
| `lo_general+composite` | `Cutoff.completed_by(served_at)` (the field rows as of the serve) | as above | binary | version hash; training cutoff `completed_by` at the serve |
| every other producer of the generic writer (outside `llm_v1`/`llm_v3`, `llm_history_v1`, diagnosis, repair, teacher) | absent, with the reason above | derived from columns (`stated_by: writer`, two fields unversioned) | binary, or not issued with its reason | writer's (model call fields where the versions name a prompt or model) |

## 2. The category computation and its equality proof (SR-4)

`predict.category_mixture(view, spec, warmth, weights)` computes `(m, v) = view.prediction(spec, warmth)`,
`w = mixture_weights(view)` unless weights are given, then
`rows = M.category_probabilities(asarray(m), asarray(v) + (A·τ0)², full(shape(m), spec.guess))` and each category
as `float(dot(w, rows[..., k]))`. `predict` computes `p̄ = float(dot(w, expected_success(m, v, guess)))`, and
`expected_success` is defined as exactly that `category_probabilities(...)` expression's `[..., 2]`: same inputs,
same operations, same strided column, same dot. So category 2 is `p̄` bit for bit; no posterior-update
probability, no unweighted grid average. `threshold_receipts` passes the very view, item spec (`_no_loadings`
in the LO view), warmth and weights its `p̄` used (`threshold_snapshot`, which never raises: on a failure
`p_categories` stays `null` as before and the receipt is written).

Tested (`test_threshold_receipts_store_categories_whose_category_two_is_the_binary_value`): at each of two serves
(the first on the prior, the second on a state the first answer moved), for all three mixture variants (the
bank's weights over a multi-point grid, the uniform-sharing restriction, the LO view's single point), the
recorded call's categories satisfy `categories[2] == predict(...).p_bar` (exact `==`), `|sum − 1| ≤ 1e-12`, the
stored `p_categories` equal them, `forecast.p == round(p̄, 8)`, the `p` column `== p̄`, `p_band` its old rounding.
Example (first serve, `@subject`): `{"0": 0.4244180934005768, "1": 0.21262626161535314, "2": 0.36295564498407007}`,
`p̄ = 0.36295564498407007`, `p = 0.36295564`.

## 3. The VOI path

`voi_forecasts.record_forecast` adds `versions_json.snapshot` (`voi_snapshot`) to its own body through its own
persistence path; the forecast body, receipt key, columns and id are unchanged, and a snapshot error leaves an
`error` marker. Cutoff: absent ("a value-of-information site does not state the evidence cutoff it read under").
Target: kind `check_outcome`, members the chosen item and the LO, unit `emission`, action = site and `chosen_ref`,
horizon `next_observation`, anchor presentation / probe episode / scheduler candidate / source attempt, event
version `voi_forecast_v4`, resolver `voi_forecast_report@unversioned` (listed). Distribution: the body's
`predicted_outcomes` with `administered` = (`forecast_of == "committed"`), so a stop or nominal best keeps its
forecast marked as never administered. Placement/VOI identity (C1) is unchanged.

## 4. The material view

`forecast_receipts.versions_json` is now classified `self` (it was a value): `MaterialView._snapshot_withheld`
withholds a receipt whose snapshot target names an item the view withholds (by id, or its revision by
`revision_hash_withheld`) or a facet only withheld material names; a receipt without a snapshot (every existing
one) is judged by its columns exactly as before; an unreadable snapshot is withheld (fail closed). A
presentation-bound receipt was already withheld with its presentation's frozen revision; the rule covers what a
snapshot names beyond the columns (facets, a revision on a presentation with no frozen inputs). The rule can only
withhold new receipts, and only where withholding is the existing policy: no decision reads the snapshot's
values. `z_v1`'s `llm_v1` receipts carry a writer-derived target whose members are their own columns (item,
revision, LO), so the rule judges nothing new for them.

Tested (`test_a_protected_revision_withholds_the_receipts_whose_snapshot_names_it`): on a served presentation's
five receipts, a withheld revision withholds all five; the same rows with their item and presentation columns
blanked are withheld through the snapshot alone, and without a snapshot are kept (5); likewise a protected-only
facet (the epoch is read before patching, so the rows stay current and only the rule is tested); an unreadable
snapshot is withheld.

## 5. Non-interference (no-tag proof)

`test_snapshots_move_no_id_seed_digest_score_or_state_under_a_frozen_clock`: two copies of one journey under a
frozen clock and a counting id stream (`ad23_contract_helpers._deterministic`/`_reset_ids`): three item-only
`llm_v1` forecasts written through the writer, a plan built, two items served and answered, AD state and the
forecast scores rebuilt. One copy has snapshots; in the other `prediction_snapshots.receipt_bodies` is the identity
(the bodies as written before this part). Every row of every table is identical, receipts compared without the
added keys (`distribution`, `reason`, `snapshot`) and with `p_categories` set back to `null`. A discarded warm-up
journey runs first: the first journey of a process mints one id more than later ones whether snapshots are on or
off (observed by the dump below: warm-up "with" vs "with" differ, "with" vs "without" vs a second "with" agree), a
one-time process setup, not this change. A mutation check (an extra `new_ulid()` in `receipt_bodies`) makes the
test fail on every table.

Values from the dump of the two copies (identical in both; ids are the counting stream's):

| What | Value (both copies) |
|---|---|
| Router decision (`router_decisions`) | id `01M3250V000000000000000007`, propensity 1.0 |
| Plan presentations | `01M3250V00000000000000000H` (pi_m1a), `01M3250V00000000000000002G` (pi_m1b) |
| AD selections' seeds / u | `917d2720…5066` / 0.48512579881, `3eaa376c…6025` / 0.52814993684, `a333e33d…ba69` / 0.57856345851 (first three) |
| Receipts | 13 (3 `llm_v1`, 5 per serve), same ids, keys, `p`, `inputs_hash`, `inputs_as_of`; e.g. `@subject` at serve 1 `inputs_hash` `3f159141…281f`, `p` 0.36295564498407007; at serve 2 `0b4ff7a6…58b2`, 0.7169527966380249 |
| `z_v1` (frozen in `item_serve_inputs`) | serve 1: available, p 0.62, value −0.48954823, recalibration n 0; serve 2: available, p 0.41, recalibrated 0.48653707, intercept 0.31010064, n 1, value 0.05386474 |
| Scores (`item_forecast_scores`) | 13 rows, 12 scored, 1 pending; e.g. `@subject` log loss 1.01347464231 and 0.332745275085 |
| AD state | `subject` `41c75123…aab1`, `lo:lo_m1` `b0ed84cb…5834`; 4 trace rows |

Also: no old receipt is updated (receipts are append-only by trigger; the writer only inserts), no new scoring or
training eligibility (no row added, no reader of the new keys), the clamped `inputs_as_of` is unchanged.

## 6. The new pin

Identity site **EPp** in `tests/identity_pins_helpers.py` (sources `prediction_snapshots.receipt_bodies`,
`prediction_snapshots.voi_snapshot`), three pins at fixed inputs:

- `EPp.stated` = `b6c90d07ce28ad75ae9f6978625cf591285f857812b09d4fa483a1c0ba59f7b5`
- `EPp.derived` = `44667972914ebc2e820312124f58589b76ebd3a21d7a8ba70a935eddf8f12dcc`
- `EPp.voi` = `5dc168a94a81d9b42614a99701d85f763fa38c0cbdc1d7b649866e30a99affe0`

`--write` added these three lines to `tests/goldens/identities.toml` and changed nothing else; no existing pin moved.

## 7. Tests and fail-first evidence

`tests/test_epp_prediction_snapshots.py` (18 tests and one strict xfail), helpers in `tests/epp_snapshot_helpers.py`.
Committed first (`f8128c0f65`) and run before the writer was wired (the two new modules present, unused): 16
failed (`TypeError: ... unexpected keyword argument 'snapshot'`, `KeyError: 'snapshot'`/`'reason'`, the threshold
test's `assert 0 == 3` category calls; the two-copy journey compared every table equal and failed only on
`all("snapshot" in ...)`), 2 passed (the unreadable-time characterization and the persist-nothing guards, which
hold before and after), 1 xfailed. After: 18 passed, 1 xfailed. Two assertions were corrected after the fail-first
run, both test mistakes: the `p` column stores `p̄` unrounded (the test had compared it with the rounding), and the
material-view test now judges rows by their snapshot alone (the existing presentation rule already withholds the
full rows) and reads the epoch before patching the facet rule. The non-interference test later gained the
warm-up journey (above) and the `llm_v1` item forecasts that make `z_v1` available.

## 8. Commands and results

All through the scratch wrapper, each pytest run in a 3G memory scope at `-n 1` with explicit targets.

See the final report for the command table (filled at the end of the step).

## 9. What the two later parts need from this one

- **Repeat capture:** `ForecastReceipt.snapshot` and `snapshot_parts.item_target`/`threshold_parts` for the
  repeat forecasters; `category_mixture` for their three categories; the ids of new repeat rows from an own
  `UlidStream` (this part draws none).
- **Receipt repairs (SR-2, SR-3):** EPp-1 (an unreadable `inputs_as_of` drops the batch) is due with them; the
  snapshot already records `invalid` once the clamp stops raising.

## 10. Not verified

- The landing and arc-close gates, the durability lane; `scripts/affected_tests.py` lists 348 files for the
  changed modules; the run used a name filter (record in the final report).
- Producers other than AD's state no cutoff; their targets are writer-derived. Stating theirs (diagnosis, repair,
  teacher, `llm_history_v1`, the outside forecasters) is further work, not done here.
- The cost of the extra `snapshot.state_hash()` call and the category computation per threshold receipt was not
  measured (one extra quadrature per receipt).
- No owner vault was opened.
