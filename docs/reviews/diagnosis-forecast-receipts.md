# Saved diagnosis forecasts: receipts written before the outcome, scored after it

**Stage:** `diagnosis-forecast-receipts`, owner go-ahead 2026-10-15 (the queue item "saved diagnosis forecasts" of 2026-10-13).
**Branch:** `diagnosis/forecast-receipts`, base `37a2a7e5f` (main, `mvp-0.25`, migrations to 204).
**Successor:** none. Logging only: no grading, scoring, scheduling, projection or serving change.
**Migration:** 230, a placeholder number (the diagnosis-input-provenance landing holds 205); renumbered at landing.
**Kill switch:** `diagnosis.forecast_receipts` (default on; off writes no receipt, the report still reads).
**Model calls:** none (fakes only). **Paid calls:** none.

## Summary

A diagnosis used to be judged by how well it explained what had already happened. Now every meaningful expectation a decision states is written down, in that decision's own transaction, before its outcome can exist, and scored later against what actually happened:

1. **The diagnosis's forecast** (`diagnosis_next_observation`, forecaster `diagnoser_causal_class_v1`). When the split diagnoser's proposal is persisted (`jobs._persist`), each diagnosed error event that the diagnoser classed (learner state or a transient slip) writes, for each facet it targets, the diagnosis's posterior over the cause (its class and its own confidence; the candidate causes and registry match are recorded beside it) and what that posterior predicts for the **next unaided observation of the facet**: `pass`, `same_error` (the event's error type or registry misconception recurs) or `other_error`.
2. **Check forecasts** (`check_outcome`). The probe and follow-up selections already write their predicted outcomes as `voi_forecasts` (EVSI calibration Part B). They are read as the same family through an adapter (forecaster = the decision site, binding = the site's own receipt chain, joined by `live_report`'s exact adapters), not copied.
3. **Repair expectations** (`repair_cold_outcome`, forecaster `repair_class_cold_rate_v1`). When a primed repair attempt schedules its cold retry (`remediation.record_remediation_attempt`, the primed attempt's transaction), the receipt records the predicted probability that the repair class fixes it on the cold attempt the task binds. A repair whose cold check cannot be scheduled (no episode, no independent surface, no repair class) writes a receipt censored at birth with that reason.

`learnloop diagnosis calibration` resolves each receipt at read time through its exact binding and nothing else, and reports, per kind and forecaster, the honest n and reliability tables (Brier, log loss, ECE, bins). The fail-first tests failed on the base (§Fail-first), eight mutants of the rules are each killed by them, and the gate is green (§Gate). The manual run on backup-API copies of the owner's linear-algebra and probability vaults wrote and resolved receipts on real items with the fake diagnoser and grader (§Manual run).

## Owner decisions built to

| Decision | Where |
|---|---|
| Go-ahead for saved diagnosis forecasts (2026-10-15) | this stage |
| Recommended defaults accepted (2026-10-12) | the defaults below are recorded as open questions with the default taken |
| Frictionless defaults: honest labels, generous defaults, live changes behind kill switches, no shadow stage by default | `diagnosis.forecast_receipts = true`; no UI (glass box on demand: the CLI report) |
| Exact binding, never guessed (EVSI calibration F3/F6) | §Binding |
| No paid calls in this stage | fakes in every test and the manual run |

## The receipt shape (one family)

`forecast_receipts` (RECEIPT, append-only by trigger; `src/learnloop/db/stores/forecast_receipts.py`, the only SQL writer, registered in `tests/test_architecture.py`). `src/learnloop/scheduling/forecast_receipts.py` generalizes `scheduling/voi_forecasts.py` (same body format, same parameter-provenance vocabulary, same never-raise rule):

| Field | Meaning |
|---|---|
| `kind`, `event`, `p` | what is forecast; the binary event and its probability where one exists |
| `forecaster`, `forecaster_version` | who forecast it, and the version of its code, priors and config |
| `scope` | `next_observation`, `followup_task`, `presentation`, `item` |
| `decision_kind`, `decision_ref`, `source_attempt_id`, `learning_object_id`, `facet_id`, `hypothesis_ref`, `practice_item_id` | the decision that wrote it and what it is about |
| `inputs_json`, `inputs_hash`, `inputs_as_of` | what the forecaster read, and as of when (CHECK: never after `created_at`) |
| `forecast_json` | the `voi_forecasts` body: `emission_alphabet`, `predicted_outcomes`, `prior`, `likelihood`, plus the kind's frozen `target` rule |
| `parameters_json`, `versions_json` | every number with its provenance (`measured` / `population_prior` / `heuristic` / `structural`); versions incl. `receipt_shape_version` |
| `binding_kind` + `plan_presentation_id` / `probe_presentation_id` / `followup_task_id` / `scheduler_candidate_id` | the exact chain the resolver may follow |
| `censor_reason` | set exactly when `binding_kind = 'none'` (CHECK): right-censored at birth |
| `status`, `received_at`, `item_content_hash` | AD1's outside forecasters (`failed`, `refused_spend`, a late answer) and item-scoped forecasts |
| resolution | never stored: derived at read time |

**AD1 fit** (`spec_adaptive_difficulty_v1` §8.1). `item_forecasts` is this family with kind `item_unassisted_success`, scope `presentation` (binding `plan_presentation` / `probe_presentation`, or the scheduler candidate) or `item` (`item_content_hash`), `p` and optional `p_categories` (in `forecast_json`), `inputs_hash`, `inputs_as_of`, `created_at` as `issued_at`, `received_at`, `status` and `algorithm_version`. AD1 adds its kind to `FORECAST_KINDS` and needs no migration; its validity rule (`inputs_as_of ≤ served_at`) is the resolver's to check, as here.

## Where each receipt is written

| Kind | Decision transaction | Not written |
|---|---|---|
| `diagnosis_next_observation` | `jobs._persist`, after the `attempt_diagnoses` row, in the same `atomic()` (a savepoint of it): the diagnosis and its receipts commit together | failed, skipped or validation-rejected diagnoses; events classed `unknown` (no expectation stated); events the grader scoped to the item contract, its interpretation or the interaction; with the switch off |
| `repair_cold_outcome` | `record_remediation_attempt` inside `apply_attempt`'s transaction, beside the cold task (or the refusal) | replay and regrades: `apply_attempt` passes the vault only when `replace_existing` is false |
| `check_outcome` | unchanged (`voi_forecasts`, Part B) | — |

A receipt failure rolls back its own savepoint and is logged; the decision proceeds (test: `test_a_failed_receipt_never_breaks_its_diagnosis`).

**The diagnosis forecast's numbers.** The class posterior is the diagnoser's own: `P(learner_state) = causal_confidence` for a learner-state event, `1 - causal_confidence` for a slip, 0.7 when no confidence is given (`DEFAULT_CLASS_CONFIDENCE`, heuristic). The likelihood of the next observation is the system's facet response model (`probes.facet_conditional_distribution` under `probe.irt`) for an item-agnostic check (a = 1, b = 0; the next item is unknown at diagnosis time): the learner-state cause reads as the error's misconception label, the slip as the facet being solid; each is floored by 2% toward uniform. At the defaults, P(pass | learner state) = 0.05 and P(pass | slip) = 0.72; P(same error | learner state) = 0.69. These are labelled `heuristic` in `parameters_json`; the report is what tells whether they are calibrated. The diagnoser's `causal_confidence` is a self-report the contract says is never used as a probability by a decision; here it is scored, not used. One forecast per (facet, error pattern): two events of one pattern on one facet are one prediction (found by the manual run, §Manual run).

**The repair forecast's numbers.** Beta-binomial: the repair class's measured cold successes (`causal_cold_outcomes`, `cold_success` / `cold_failure`) shrunk toward the pooled measured rate (itself Laplace-smoothed) with pseudo-count 2. The cold-success threshold the verification uses (`cold_verification_success_correctness`, 0.8) is frozen in the receipt.

## Binding (exact, never guessed)

**Diagnosis forecast.** The frozen rule (`next_unseen_qualifying_presented_attempt_on_facet_v1`) is in the receipt's `target`: among attempts created at or after the diagnosed one, excluding it and the attempts visible to the receipt's transaction (`seen_attempt_ids`, listed in the receipt), the first in (created_at, id) order whose recorded evidence facets include the facet (canonical at read time: aliases and settled merges) and that tests it unaided (`independent_attempt`, `dont_know`, `diagnostic_probe`, `exam_attempt`; not primed; no hint). Assisted, primed or non-test attempts before it are counted as `intervening`. That attempt must carry an exact presentation receipt: `practice_attempts.plan_presentation_id` (router R2a), `probe_presentation_id`, or the scheduler offer it answered (`scheduler_candidate_id`, AD §8.3's fallback). If it carries none, the forecast is censored `unbound_attempt`. It is never replaced by a later bound attempt: that would be selection on the binding (test `test_an_unbound_next_attempt_censors_the_forecast_never_a_later_bound_one`). The visible-set rule makes "before the outcome" exact: an attempt answered while the diagnosis job ran is never its observation, and one still in flight when the receipt was written can be (test `test_attempts_visible_when_the_receipt_was_written_are_never_its_observation`).

**Repair forecast.** `followup_task_id` → the task's `consumed_attempt_id` → the cold verification's disposition for that attempt (`causal_cold_outcomes` with that task and cold attempt). No other attempt on the cold item is ever read.

**Check forecast.** `live_report`'s adapters, unchanged (R1's taken offers, then the ledgers' exact receipts; staged forecasts through R2a's presentations).

## Resolution (derived at read time)

| Kind | Resolved | Pending | Held | Censored (reason counted) |
|---|---|---|---|---|
| diagnosis | `same_error` if the attempt's current error events show the pattern; else `pass` if the facet's outcome is in the facet updater's `high` bucket; else `other_error` | `awaiting_observation`, `ungraded` | `grade_held_for_review` | `unbound_attempt`, `facet_unassessed`, `facet_not_in_contract`, `graded_contract_unknown`, `no_frozen_rule` |
| repair | `cold_success` / `cold_failure`: the cold attempt's CURRENT correctness against the frozen threshold, on a measured disposition | `awaiting_cold_attempt`, `awaiting_cold_verification`, `ungraded` | `grade_held_for_review` | the disposition (`contaminated_or_assisted`, `same_surface`, `missing_chain`, `right_censored_expired`, `unmeasurable_*`), `cold_attempt_unassessed`, `no_task_receipt`, and every censor-at-birth reason |
| check | `live_report.realized_emission` | `pending` | `grade_held_for_review` | every other join status |

**The facet's outcome** is read as replay reads the attempt (`replay_existing_attempt`): the surviving grading rows, the last row of a criterion winning (a regrade's rows supersede the grade they replace), under the assessment contract the first of them cites, else the current item's (a regrade of an item without a frozen method reads the item as it is now). Each assessed criterion whose observation targets include the facet is weighted by its points and the facet's role-weighted share of its targets, as EVSI calibration reads a follow-up's target facet (review F5) and `derive_facet_outcomes` weights it. An unassessed criterion contributes nothing; a don't-know fails every facet its contract measures. The learner field's facet rows (`field.outcomes.load_facet_rows`) were tried first and dropped: their exact-revision rule excludes every multi-facet item and every attempt without a selection receipt, which censored ordinary bound answers as `answered_revision_unknown`.

**Regrades** re-resolve (resolutions read the current grade; test `test_a_regrade_re_resolves_the_forecast`). **Held grades** never resolve as outcomes until released (`held_grades.held_for_review_attempts`; test `test_a_held_grade_resolves_nothing_until_a_regrade_releases_it`: held, then released by a validating regrade, then `pass`).

## Replay

The table is a RECEIPT: no replayer writes, reads or clears it. `apply_attempt` passes no vault to `record_remediation_attempt` on replay or a regrade, so the repair writer cannot run there; the diagnosis writer lives in the job worker, which replay never calls (S7). Test `test_replay_neither_reads_nor_writes_forecast_receipts`: a rebuild leaves the receipts byte-identical, writes none (every replayed `record_remediation_attempt` call carries `vault=None`, and neither writer is reached), and the derived learner state (`shadow_rebuild._learner_state_snapshot` and every DERIVED table's row count) of a rebuild with the receipts equals that of a rebuild of a backup-API copy with the table dropped.

## The report

`learnloop diagnosis calibration [--since ISO] [--checks/--no-checks] [--vault] [--json]` (`src/learnloop/evsi_calibration/forecast_report.py`; read-only, one snapshot, no migration, `load_vault(load_environment=False)`). Per kind and forecaster:

* **the honest n:** receipts, decisions, resolved, `distinct_outcome_attempts` (several forecasts resolved on one attempt are one observation), and pending, held and censored counts by reason; `small_n` under 30 resolved;
* **binary** (diagnosis `P(pass)`, repair `P(cold_success)`): reliability bins with n, mean predicted and observed, Brier, ECE, log loss, observed rate, and the in-sample base-rate Brier for comparison;
* **categorical** (every kind): multiclass log loss and Brier, one-vs-rest reliability;
* diagnosis splits by causal class and by diagnosis mode (`live` / `shadow`).

A vault without the table reports check forecasts only and says so.

## Fail-first

* **On the base.** `tests/test_forecast_receipts.py` run against a `git archive` of `37a2a7e5f` (its own `src`, `migrations`, `pyproject.toml`): collection error, `ImportError: cannot import name 'forecast_receipts' from 'learnloop.db.stores'`. Nothing of the family existed.
* **Mutants** (each applied alone to the stage's code, its test run, then restored). Rerun after the 2026-10-15 restart at `937ad2954` in an isolated `git archive` of the branch (`fixtures-local/tmp/mutwork/mutate.py`, its own `src` first on `PYTHONPATH`, so the gate's tree was never mutated): unmutated, the file's 16 tests pass; each mutant fails its test on an assertion (M2: a second connection already saw the committed diagnosis and its receipt, `(1, 1) == (0, 0)`; M8: a replayed `record_remediation_attempt` call carried the vault).

| Mutant | Killed by |
|---|---|
| M1 the diagnosis transaction writes no receipt | `test_a_completed_diagnosis_writes_its_forecast_in_its_own_transaction` |
| M2 the receipt is written after the diagnosis commits | the same test (another connection saw the diagnosis before its receipt) |
| M3 an unbound next attempt is accepted | `test_an_unbound_next_attempt_censors_the_forecast_never_a_later_bound_one` |
| M4 held grades resolve | `test_a_held_grade_resolves_nothing_until_a_regrade_releases_it` |
| M5 attempts visible to the receipt are used | `test_attempts_visible_when_the_receipt_was_written_are_never_its_observation` |
| M6 a regrade's rows are ignored | `test_a_regrade_re_resolves_the_forecast` |
| M7 the repair receipt is written outside the primed attempt's transaction | `test_a_scheduled_cold_check_records_its_repair_forecast_and_resolves_on_its_task` |
| M8 replay passes the vault to the repair writer | `test_replay_neither_reads_nor_writes_forecast_receipts` |

The 16 tests: transaction and content of a diagnosis receipt; a failed receipt never breaks its diagnosis; an `unknown` class writes nothing; class, confidence and one forecast per facet and pattern (pure builder); the kill switch (diagnosis and repair); resolution on a presentation-bound attempt; unbound censoring; the visible set; held then released; regrade; the repair receipt bound to its task (in the primed attempt's transaction) through cold attempt and verification; a repair censored at birth (`no_independent_surface`); replay; append-only triggers; the report on a seeded vault (CLI JSON and text); a vault without the table.

## Manual run (backup-API copies, fakes, no paid call)

**Setup.** `learnloop.db.copies.copy_tree_with_databases` of the worktree's tracked `fixtures/linear_algebra` and `fixtures/probability` (the base commit's content, not the main checkout) into `fixtures-local/forecast-manual/{linear_algebra,probability}_run3` (`copy_vault.py`); `LEARNLOOP_CONFIG_DIR` an empty directory, so no key and no network; each copy upgraded `mvp-0.8 → mvp-0.9 → mvp-0.25` with `learnloop upgrade` (schema 230, exit 0; the recurrence guard's advisory notes printed as usual), then `[diagnosis] shadow = true` added to the copy's config (its grades are joint, from before the split). `run_manual3.py`: the report before; rediagnose the newest failed attempts that carry error events (up to 6) through the job worker with the fake diagnoser (`ReviewFakeClient`); answer the first two rediagnosed items through plan presentations, one with its expected answer and one wrong, with the fake grader and the post-attempt pipeline; resolve; the report after. Model calls: 3 diagnosis and 3 grading `agent_runs`, provider `fake` on both copies. **Paid calls: none.**

| Copy | Candidates / rediagnosed | Receipts written | Answered (plan presentation) | Resolutions |
|---|---|---|---|---|
| linear_algebra | 3 / 2 (both `completed`) | 5 `diagnosis_next_observation`, all bound by the frozen rule, 0 duplicate (diagnosis, facet, pattern) groups | `pi_orient_compute_operation_packages_04` right; `pi_exercise_01ky5raxvexp8axggqn8e73vkh` wrong | 1 `pass` and 4 `other_error` (the wrong answer's 2 facets x 2 patterns), each through `plan_presentation`, `realized` |
| probability | 1 / 1 | 1 | `pi_three_independent_birthd` right | 1 `pass` through `plan_presentation` |

The linear-algebra report after (`learnloop diagnosis calibration --vault …`, text and `--json`, exit 0; the database file's SHA-1 unchanged by both):

```
check_outcome: 1 receipts
  followup_value_decision: 1 receipts, 0 resolved on 0 attempts (the honest n), 1 decisions  [small n]
    censored: not_administered=1
    categorical: brier=n/a log_loss=n/a ece=n/a
diagnosis_next_observation: 5 receipts
  diagnoser_causal_class: 5 receipts, 5 resolved on 2 attempts (the honest n), 2 decisions  [small n]
    P(pass): brier=0.163 log_loss=0.508 ece=0.054 mean_predicted=0.254 observed=0.200
      [0.2, 0.3) n=5 predicted=0.254 observed=0.200
```

The in-sample base-rate Brier beside it is 0.160 (categorical: log loss 1.346, multiclass Brier 0.847). The `check_outcome` row is the wrong answer's follow-up decision's `voi_forecasts` row, read through EVSI calibration's adapter (never administered, so censored). Every diagnosis forecast here reads P(pass) = 0.254: the fake diagnoser names `learner_state` without a confidence (the 0.7 default) and the facet model is item-agnostic, so this forecaster only varies with a real diagnoser's confidence and class (open question 1).

**What the run found.** The first run (before the restart, at `942525096`, copy `forecast-manual/linear_algebra`) wrote 6 receipts on 2 diagnoses, two of them identical forecasts of one observation (two `local_slip` events on one facet); `937ad2954` states one forecast per (facet, error pattern), and this run shows 5 receipts and no duplicate group. Two copies the earlier run was upgrading (`linear_algebra_run2`, `probability`) were cut off mid-upgrade by the restart and were abandoned, not used.

## Gate

Run after the restart on the final code (`937ad2954`; only the regenerated references and this record were committed after it). The gate started before the restart had written nothing (its log was empty: it was still waiting for the machine lock), so none of it is counted.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 22 contracts kept, 0 broken |
| Full suite: `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto` (`TMPDIR` = the worktree's `fixtures-local/tmp`, template `.pyc` cleared) | **11845 passed**, 0 failed, 0 skipped, 16 warnings, 934 s |
| Durability lane: `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -m durability` | **106 passed**, 11739 deselected, 111 s |
| `tests/test_forecast_receipts.py` alone, and again with `--durable-sqlite` | 16 passed; 16 passed |
| DB references: `db_generate_reference.py`, `db_validate_reference.py` | regenerated at the branch head (`eebb22af9`: the `forecasts` note now lists `tests/test_coordinated_migrations.py`; the rest are source-commit stamps); validate: 323 table notes, 858 effective config leaves, no errors |
| `tests/test_coordinated_migrations.py`, the CLI help snapshot, the defaults snapshots | green inside the full suite |
| Frontend, `src-tauri` | unchanged: not run |

## Composition notes for the landing

* **Migration 230 → the next free number** after the provenance landing's 205: the migration file name and header, `table_roles.py`'s comment, the store docstring, `scheduling/forecast_receipts.py`'s docstring, the head fixture directory and README, the 24 test paths, both reference scripts (`SCHEMA_PATH`, `SCHEMA_HEAD`), `test_route_rules_in_grader.py`'s max-migration assertion, `docs/decider-tier1-migration.md`, the generator's table description and the Pipeline Map bullet. `tests/test_coordinated_migrations.py::test_f8_the_coordinator_upgrades_under_its_allowance_and_qualifies` now names migration 204 (the ledger its older build lacks) instead of "the newest".
* **Provenance overlaps** (the diagnoser and attempts): this stage touches `jobs._persist` (a `forecasts` callback after the diagnosis row, inside the same `atomic()`), `jobs._diagnose` (the agent run's `started_at` kept as `inputs_as_of`; the final persist's values named), and one call in `attempts._apply_attempt_in_transaction` (`record_remediation_attempt(..., vault=None if attempt.replace_existing else vault)`). If provenance writes its C4 receipt in the diagnosis transaction too, both callbacks run inside the same block.
* **Defaults snapshots:** all seventeen recomputed for `diagnosis.forecast_receipts`; recompute again from the composed defaults at landing.
* **CLI help snapshot:** `diagnosis` (group help) and `diagnosis calibration` (new).
* **References:** regenerated at this branch's head (`forecast_receipts` table note; `diagnosis.forecast_receipts` config leaf; 323 table notes, 858 config leaves).

## Deviation recorded

Before copying, to learn which migration the tracked working vaults were at, `fixtures/linear_algebra`, `fixtures/probability` and `fixtures/arxiv_v2` were each opened once read-only with SQLite's `immutable=1` URI flag (one `SELECT MAX(version) FROM schema_migrations`; 155, 155, 152). Nothing was written and no lock taken, but the rule is to open them only through backup-API copies; every later read and the whole manual run used copies.

## Open questions (default taken in brackets)

1. **The diagnosis forecaster's likelihood** is the facet response model's item-agnostic heuristic, which predicts a strong recurrence of the same error under a learner-state cause (0.69). Should a second, baseline forecaster (the facet's current recall state) write beside it so the report compares the diagnosis against "no diagnosis"? [Not now: the base-rate Brier is reported; add when there are resolved forecasts to compare.]
2. **`voi_forecasts` writes** were not re-audited for "in the decision's own transaction": `record_forecast` writes a savepoint when its caller holds `atomic()`, else commits on its own. [Leave them; the adapter reads them as they are.]
3. **AD1 should write `item_unassisted_success` here** rather than create `item_forecasts`; `spec_adaptive_difficulty_v1` §8.1 and §11.2 name a separate table. [Yes, same family; update the spec at AD1.]
4. **`unknown`-class events** write nothing (no expectation). An "abstained" receipt would count them in a denominator. [Nothing.]
5. **Unbound next observations** (library picks, answers without a presentation or offer) censor the forecast. [Keep: exact binding only.]
6. **No desktop surface.** [CLI only, glass box on demand.]
