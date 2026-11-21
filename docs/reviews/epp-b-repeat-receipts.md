# EPp, second part: the predecessor's prediction on a repeat presentation

Evidence packets spec (`docs/specs/spec_evidence_packets_v1.md`) §7.7.3 item 1, §7.7.5, §8 EPp, §10; the second of
EPp's three parts ("repeat capture"). The first (prediction snapshots, `docs/reviews/epp-a-prediction-snapshots.md`)
is landed; the third (the SR-2/SR-3 receipt repairs, EPp-1) was not started. Receipts only: no migration, table,
config key, algorithm tag, kill switch or prompt change, and nothing reads the new receipts to decide anything.

- **Base:** `f44283f88e` (origin/main). **Branch:** `ep/epp-b-repeat-receipts`.
- **New module:** `src/learnloop/adaptive_difficulty/repeat_receipts.py`.
- **Changed:** `adaptive_difficulty/serve.py` (the hook calls it last, for a repeat only; `ServeRecord` gains
  `repeat_receipt_ids`, `repeat_skipped`), `scheduling/forecast_receipts.py` (`record_receipts(new_id=...)`),
  `db/stores/forecast_receipts.py` (`insert_receipt(receipt_id=...)`). `adaptive_difficulty/serving.py` (shared with
  the L4.5 extraction) and `adaptive_difficulty/serve_inputs.py` are untouched.

## 1. The two forecasters and when each is written

| Forecaster | Computation | Written |
|---|---|---|
| `ad_threshold_repeat@subject` | `ad_threshold@subject`'s: the subject view (`snapshot.subject`), the bank's mixture weights, the item spec with its loadings | at every newly inserted ordinary-plan presentation (`daily_plan.engine._serve`'s hook, unchanged) of an item the hook's own freshness test (`serve_inputs.never_attempted`, unchanged) finds attempted before |
| `ad_threshold_repeat@lo` | `ad_threshold@lo`'s: the item's learning-object view, the spec without loadings | the same presentations |

Both are `item_unassisted_success`, scope `presentation`, binding `plan_presentation` (the presentation's id in
`plan_presentation_id` and `decision_ref`), decision kind `serve`, receipt key
`item_unassisted_success:plan_presentation:<presentation>:<forecaster>` (AD's other serve-time keys' form, so a
second write is ignored), forecaster version `ad-threshold-repeat-v1:<priors>:<hyper>`, versions
`{forecaster, threshold: ad-threshold-v1, replay, memory_assumptions: ad_predecessor_memory_v1, priors, hyper,
feature_schema, protection_epoch}`, the serve's algorithm version, `inputs_as_of` and `created_at` the serve's time.
Gated as the threshold receipts are: nothing below AD's successor (`repeat_skipped = "below_successor"`), nothing
with `forecast_receipts` or AD off (the hook returns before), nothing for a protected item (the hook's existing
early returns). Not written at a reopened presentation (no insert, no hook; called again directly, the hook finds
the presentation recorded) and never for a fresh item.

`forecast_json`: `p` (`round(p̄, 8)`), `p_band`, `p_categories` (`predict.category_mixture` at the very view, spec
and warmth: category 2 is `p̄` to the bit, tested), and part one's `distribution` (unit `ad_category3`). The `p`
column is `p̄` unrounded. `versions_json.snapshot`: part one's `threshold_parts` with two changes for a repeat:
`cutoff.source` names `repeat_inputs: "inputs_json"` instead of an `item_serve_inputs` row (a repeat has none),
and `provenance` adds `memory_assumptions` and `label_closure` ("the presentation's bound attempt (AD's scorer);
unanswered stays pending"). Target: the item at its served revision, LO, facets, the surface group as served
with its source; action serve; horizon presentation; anchor the presentation; resolver `ad_forecast_scores_v1`.

## 2. `inputs_json` field by field (schema `ad_repeat_inputs_v1`)

All read at the serve, inside the serve's AD operation and its material view; no write and no model call.

| Field | Source | Availability |
|---|---|---|
| `inputs_kind` | constant `frozen_at_serve` (as against a repeat replay resolves later from history) | always |
| `practice_item_id`, `learning_object_id` | the served item | always |
| `item_revision` | `feature_audit.item_revision(item)` (the served revision's content hash) | always; the revision's content is in `practice_item_snapshots` only if some other path saved it (this path saves nothing: §3) |
| `surface` `{key, source, singleton}` | `serving.served_item` (`replay.surface_group`, `snapshot_parts.surface_source`) as served | always |
| `state_hash`, `replay_version`, `coupling_versions` | `RP.snapshot(...)` (the serve's view) | always |
| `features` `{stamped_features, task_feature_schema, audit, resolved_features, resolution_version}` | `serve_inputs.feature_inputs` at the serve (the audit answered by then, per dimension, with its judgment id) | a dimension no audit answered is `null` in `audit`; `resolved_features` is `null` with no stamped tuple |
| `signals` | `serve_inputs.signal_vector` at the serve: `z_llm`, `z_panel`, `z_v1` (with its recalibration), `z_origin`, each `{value, available, why or receipt_id/received_at/source}`, plus `read_by_prediction` and, for an available one not read, `not_read_because` (`outside_arm_only` for `z_v1`) | an unavailable signal is `value: null, available: false, why: <reason>` (`not_llm_estimate`, `not_solver_panel`, `no_panel_rates`, `received_after_serve`, `not_received_before_serve`, `no_item_forecast`), never a default |
| `signals_read` | the item spec's signals the prediction used (`predict.current_spec`, as the threshold receipts) | always (may be `{}`) |
| `z_v1_recalibration` | the recalibration's version | always |
| `loadings` | the spec's loadings in force (subject view); `{}` in the LO view, as `ad_threshold@lo` | `{}` with coupling off |
| `warmth` `{value, last_exposure}` | `value`: `serving._warmth` (the predecessor's own); `last_exposure`: `repeat_receipts.last_exposure`, the same reads, order and strict comparison: `{available, id, at, kind (attempt, reveal, reading:<kind>), hours_before_serve}` | `{available: false, why: no_exposure_before_serve}` with none (warmth 0) |
| `pre_exposed` | `serve_inputs.pre_exposed` at the serve (§5.3's reveal-sum rule) | always |
| `memory.item` `{attempts, last}` | the item's visible attempts at or before the serve (the freshness test's boundary); `last`: `{attempt_id, at, hours_before_serve, practice_item_id, attempt_type, plan_presentation_id, correctness, hints_used, primed}` | always (a repeat has at least one) |
| `memory.surface_group` `{key, source, singleton, attempts, items_attempted, sibling_attempts, last, last_sibling}` | the served item's group as served; another item's group read off it as it stands at the serve (an item no longer in the vault is its own group) | `last_sibling: null` with none |
| `memory.item_reveals` `{count, last}` | the item's visible reveals at or before the serve | `last: null` with none |
| `memory.case` | `{item: practised, group: singleton / family_siblings_practised / family_item_only}` | always |
| `delay` `{kind, origin, block_id, router_decision_id, scheduler_candidate_id, hours_since_item_attempt, hours_since_group_attempt, assignment_propensity, redraw_probability}` | the presentation row (through the view): `kind` is `randomized_check` when its origin is the router's check origin (restated, pinned equal), else `natural` | `assignment_propensity` is **unavailable** (`not_readable_in_ad_operation`: the propensity is in `router_decisions`, outside AD's protection registry, so the serve's AD operation may not read it; the decision id names the row) or `no_router_decision`; `redraw_probability` unavailable (`not_applicable` for a natural delay; `not_recorded_at_serve` for a check) |
| `predecessor_memory` | `PREDECESSOR_MEMORY`: no item or group memory term, residual `(A·τ0)² = 1.0` integrated out at every presentation, repeats excluded from the update (D10), `γ` once per surface group, no decay of the mean, warmth `exp(−h/6)` | always |
| `view`, `mixture` | `subject`/`bank` or `lo:<id>`/`lo_view` | always |

A computation that fails writes the two receipts as failed forecasts: status `failed`, `p` null,
`forecast.reason = compute_failed:<ExceptionType>`, inputs `{schema, practice_item_id, learning_object_id,
failure}`, the snapshot's distribution not issued with reason `failed` (§4).

**Reported as unavailable (a stop point of the brief, recorded rather than read):** the router's assignment
propensity and a check's redraw probability are not readable at the serve boundary without reading tables AD's
guard refuses; reading them would need reclassifying `router_decisions` / `policy_experiment_assignments` in the
protection registry (out of scope). A randomized check never serves an attempted item (RO5's eligibility), so a
repeat's delay is natural in practice; the receipt names the decision id a report can join.

## 3. The pure assembly; `build_row` untouched

`serve_inputs.build_row` (which inserts the revision snapshot) is not called and not changed:
`git diff f44283f88e -- src/learnloop/adaptive_difficulty/serve_inputs.py src/learnloop/adaptive_difficulty/serving.py`
is empty. The repeat path calls the pure parts `build_row` composes (`signal_vector`, `feature_inputs`,
`pre_exposed`) and its own read helpers (`memory_context`, `last_exposure`, `delay_context`, each taking a view and
plain values); the dict is assembled by two pure functions with no read (`shared_inputs`, `view_inputs`), which
the identity pin calls with plain values. Tested: during a journey with a repeat, `build_row` and
`insert_item_snapshot` are called for the two fresh items only, and `item_serve_inputs` holds exactly the fresh
presentations' rows.

## 4. Lifecycle cases

| Case | What is recorded | Tested |
|---|---|---|
| issued | status `ok`, `created_at` = `inputs_as_of` = the serve | yes |
| received | in-process: issued and received at once (`received_at` null, as every in-process receipt) | by construction |
| answered / resolved | the scorer's row for the presentation's attempt: `excluded` (`repeat_surface`) once answered, exactly the in-process receipts' row at that presentation | yes |
| censored (unanswered) | `pending` (`no_attempt`) | yes |
| unbound | cannot arise at write (always bound to the inserted presentation); a presentation withheld later reads `pending` (`no_bound_presentation`) by the scorer's existing rule | rule unchanged, not separately tested |
| invalid | a failed forecast reads `invalid` (`status:failed`); `inputs_after_serve` cannot arise (`inputs_as_of` is the serve) | yes (failed) |
| failed | both receipts `failed` with the reason; every other receipt of the serve stands | yes |
| write failed | `record_receipts`' savepoint rolls the repeat receipts back alone, nothing forced, `repeat_skipped = not_written`; the in-process receipts stand | yes |
| guard refusal | re-raised (`operation.is_denial`): the serve's whole AD record rolls back as for any refusal in it, the plan still serves; never bypassed | yes |
| reopened presentation | nothing (no insert, no hook; a direct call finds it `recorded`) | yes |
| protected revision | at the serve: no receipt of any kind (the hook's existing early return); later: withheld by part one's snapshot rule (item at its revision) and the presentation column; every receipt is epoch-stamped (`versions.protection_epoch`), so a protection change also makes it unreadable to AD | yes |
| serve transaction fails after the hook | rolled back with it | yes |

## 5. The id stream

`repeat_receipts._RECEIPT_IDS = ids.UlidStream()`, read through `new_receipt_id()`; the hook passes it to
`record_receipts(new_id=...)`, which hands each id to `insert_receipt(receipt_id=...)`. Without the argument
both behave exactly as before (the next `new_ulid`), so no existing writer moved streams. Tested: the repeat
receipts' ids carry the test stream's prefix, disjoint from the global stream's; `new_receipt_id` never calls
`ids.new_ulid` (patched to raise).

## 6. Non-interference (no-tag proof)

`test_repeat_receipts_move_no_id_seed_receipt_score_or_state_under_a_frozen_clock`: a frozen clock and a counting
global id stream (`ad23_contract_helpers._deterministic`/`_reset_ids`); `pi_m1a` attempted (wrong) three days
before, due again; the plan serves it (a repeat) and then the two fresh items, each answered; AD's state and the
forecast scores rebuilt. Two copies (after a discarded warm-up, part one's oddity): with repeat capture, and with
the hook's `repeat_receipts` replaced by a no-op (the base). With the two repeat receipts and their two score
rows left out, **every row of every table is identical**: router decisions (ids, seeds, propensities), AD
selections and their seeds, plan presentations and served items, every fresh-item receipt (keys, `p`,
`inputs_hash`, bodies), `item_serve_inputs` with `z_v1` available on both fresh serves, `ad_state`,
`ad_attempt_trace`, every other `item_forecast_scores` row. **Mutation check:** a copy whose repeat receipt ids
also take one global `new_ulid` each differs from the base in `plan_presentations` and `forecast_receipts` (and
the tables after), and the test asserts that.

Readers checked by source: `z_v1` reads item-scoped `llm_v1` only; `serve._recorded` is satisfied by the
in-process receipts first; `report.py`'s §9.6 share reads `ad_threshold@subject` only; RO2's history report
compares named forecasters only; `item_forecast_scores` has no decision reader. Two report-only outputs gain the
new forecasters: the scorer's rows (as §7.7.5 states) and `evsi_calibration.forecast_report`'s per-forecaster
groups (`learnloop diagnosis calibration`), and `data_check`'s count by forecaster. No decision changes.

## 7. Cost (synthetic benchmark; no threshold chosen)

A scratch benchmark (not tracked; the test suite's fast-lane SQLite shortcuts and connection reuse apply, so
absolute numbers are below a production vault's):

| Measure | Value |
|---|---|
| The serve hook on a repeat presentation (journey, 2 attempts), median of 5 | 19.9 ms with capture, 6.1 ms without: **+13.8 ms** |
| `repeat_receipts` alone, 2 attempts in the vault, cold / warm AD cache | 16.7 ms / 15.6 ms |
| the same, 62 attempts | 32.5 ms / 27.2 ms |
| the same, 242 attempts | 80.4 ms / 66.0 ms |
| reads per repeat serve (material-view `SELECT`s / filter calls), any history size | 33 / 34 |

"Warm" means the replayed state is cached; `RP.snapshot` re-reads the events and fingerprints them either way,
so most of the cost is the replay's event load plus the repeated full scans of the visible attempts (the replay,
`_warmth`, `last_exposure`, `memory_context`, `pre_exposed`) and `z_v1`'s recalibration (once in
`current_spec`, once for the recorded vector). The cost grows linearly with the visible attempts.

## 8. New pins

Identity site **EPp-repeat** in `tests/identity_pins_helpers.py` (sources `repeat_receipts.shared_inputs`,
`view_inputs`, `memory_context`, `delay_context`, `build_receipt`):

- `EPp-repeat.keys` = `2a38d83c48b736c1902062eaa857cf1a05fbf1e20556a2f2e08147eb6cedec95` (both receipts' keys,
  versions, forecaster version, columns at a fixed presentation)
- `EPp-repeat.inputs` = `15051da73d28b454b66139d6a5a90088936fa0bce75383e172505e4c19d72e9b` (`inputs_json` at fixed
  plain values: a family with a practised sibling)

`--write` added these two lines to `tests/goldens/identities.toml` and changed nothing else; no existing pin moved.

## 9. What the memory successor (ADM2a) can and cannot reconstruct from these rows

Against the design's list (`ep-adm` design §3):

| Must distinguish | From these rows |
|---|---|
| same item / unseen sibling in a practised family / singleton / novel family | **Same item:** every repeat row, with `memory.case.group` singleton, family with practised siblings, or family met only through this item, and the counts. **Unseen sibling / novel family** are fresh serves: the fresh `ad_threshold@*` receipts (unchanged) name the served surface group and its source in their snapshot target; whether that family was practised before is reconstructible from the earlier presentations' as-served group keys (repeat rows here, fresh rows' targets, `item_serve_inputs` → the revision's snapshot), not stated on the fresh row itself. Attempts made outside plan presentations carry only their item and revision hash. |
| exact revision and grouping as served | revision hash and group key with its source as served (tested after a later family edit). The revision's **content** is recoverable only if `practice_item_snapshots` holds it (the attempt's submission usually saves it; an unanswered repeat at a never-saved revision has its hash only). Other items' groups in `memory` are as they stood at the serve, from current content then. |
| frozen versus historical inputs | `inputs_kind: frozen_at_serve`; no `item_serve_inputs` row, so replay still resolves the repeat historically (unchanged); whether ADM2a trains on these is its step 0's call |
| natural versus randomized delay, with probabilities | the kind and the origin; the router decision id and block; hours since the item's and group's last attempts. **Not** the assignment propensity or a redraw probability (unavailable with reasons: §2) |
| available versus unavailable signals; pre-exposure; assistance context | every signal with availability and reason and whether it was read; `pre_exposed`; the last item attempt's hints, primed and correctness; the item's reveals. Help during the repeat itself is the attempt's, after the serve (the scorer reads it). |
| issued, received, answered, resolved, invalid, failed, unbound, censored | §4: issued/failed in the row; the rest from the scorer's derived rows and the ledgers, as for every receipt |
| prediction event, horizon, resolver version, label closure | the snapshot target (event `ad_category:<priors>`, horizon presentation, resolver `ad_forecast_scores_v1`) and `label_closure` in provenance |

The state hash attributes the prediction; it does not reconstruct the bank. The three category probabilities
make each receipt scorable without the bank.

## 10. Tests and fail-first evidence

`tests/test_epp_repeat_receipts.py` (21 tests), helpers in `tests/epp_repeat_helpers.py` (the repeat journey, the
two-copy comparison, a fake view for the pure reads). Committed first (`bfa484dde1`) and run with the new module
present but unwired (serve.py and the writer at the base): **16 failed, 5 passed** (the 16 journey tests fail at
the journey's patch of the hook's `new_receipt_id`, `AttributeError: ... serve has no attribute
'new_receipt_id'`; the 5 passing are the pure memory/exposure/delay tests over the unwired module). With the
module absent entirely: collection `ImportError`. At the tip: **21 passed**.

## 11. Commands and results

All through the scratch wrapper, pytest in a 3G memory scope at `-n 1` with explicit targets, `-m "not arc_close"`.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile --extra tui`; `uv pip install --offline pypdfium2==5.14.0` | installed |
| `pytest tests/test_epp_repeat_receipts.py`, module present, hook and writer at the base | `16 failed, 5 passed` |
| the same at the tip | `21 passed` |
| `python tests/test_identity_pins.py --write` | `identities.toml`: 2 insertions (`EPp-repeat.*`), nothing else |
| `pytest tests/test_identity_pins.py` after each source commit | `351 passed` (writer commit), `353 passed` (hook commit) |
| journey goldens and determinism: `test_diagnosis_journey_golden`, `test_due_queue_golden`, `test_grade_application_golden`, `test_plan_determinism`, `test_plan_determinism_landing`, `test_pinned_draws` | `62 passed` |
| `scripts/affected_tests.py --files` the four changed source files: 297 test files, **all run** in 8 chunks of at most 40. First the 68 matching `test_(ad[0-9_]\|adaptive\|*forecast\|*voi\|evsi\|*serve\|*receipt\|*material_view\|placement\|*scoring\|epp_\|ro2_\|*golden\|daily_plan\|ad23\|*presentation)` plus the brief's name filter (8 files; 69 together): chunk 1 | `2 failed, 769 passed, 3 skipped`: the two are EPp-2 (`test_ad1_fix_round5.py::test_the_draft_keeps_hint_seen_under_its_retry_key[on/off]`, failing alone at the base too, ledgered by part one) |
| chunk 2 | `843 passed, 3 skipped, 2 xfailed` |
| the other 229 files, chunks 1-6 | `637 passed, 2 xfailed`; `1218 passed`; `460 passed, 6 skipped`; `522 passed`; `547 passed, 6 skipped`; `505 passed` |
| `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches`, `test_sqlite_file_copies`, `test_public_tip_guards`, `test_identity_pins`, `test_structure_ratchets`, `test_epp_repeat_receipts`, `test_epp_prediction_snapshots` | `448 passed, 1 xfailed` |
| `pytest tests/test_structure_ratchets.py` | `3 passed` (no count rose) |
| `pytest tests/test_test_layout.py` (alone) | `3 passed` |
| `pytest tests/test_architecture.py` (alone) | `18 passed` |
| `ruff check` | `All checks passed!` |
| `lint-imports --no-cache` | `Contracts: 45 kept, 0 broken.` |
| `python scripts/check_gate_partition.py` | `collected 32530: landing 32464 + arc_close 66` |
| `git diff --check` | clean |

## 12. Not verified

- The landing and arc-close gates, the durability lane, the vault reference regeneration.
- Production latency: the benchmark ran under the test suite's SQLite shortcuts.
- A repeat whose earlier attempt did not consume the surface (a skip or self-report only): the scorer would give
  the repeat receipts the row it gives the in-process receipts there, possibly `scored`; reasoned from source, not
  tested.
- No owner vault was opened.
