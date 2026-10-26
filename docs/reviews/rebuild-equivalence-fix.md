# Rebuild equivalence fix (2026-10-25)

Branch `fix/rebuild-equivalence` from `0db8291c1`, worktree `learnanything-ad1`. It is an
orchestrator-queued bug stage, and the launch was owner-approved.

The stage fixes two mismatches between live state and `rebuild --shadow`. Both were already on main:

1. **Mastery on multi-attempt histories.** A history with no claims replayed to a different mastery
   mean and variance than live. The LP-min record's oracle case is `lo_svd_definition` on the placement
   vault: 0.687 live, 0.560 rebuilt.
2. **`practice_item_state.active` after a primary load.** It differed on 30 rows of the
   `linear_algebra` copy. This is finding 2 of `mobile-pr1-secondary-attach.md`.

**Verdict: replay was wrong in both cases, and live was right.** The fix changes replay only, with no
migration. The evidence is in §3.

> **Superseded by the Codex review (2026-10-25,
> [`fix-rebuild-equivalence-codex-review.md`](fix-rebuild-equivalence-codex-review.md)).** §3's "bug fix,
> no successor" does not hold: the bounded replay changes the same-version golden projection, so it is
> now the successor `mvp-0.34` behind `replay.ledger_bounded` (F4). A direct per-LO replay is one
> transaction (F1), and a rebuild finishes its own recurrence reconciliation (F3). The lifecycle fix
> (1b) still acts at every version.

## 1. Root causes

### 1a. Mastery: replay read the future

Replay (`replay_learning_object` → `replay_existing_attempt` → `apply_attempt`) recomputes each
attempt while the whole attempt ledger is already on disk. Two of its reads were not bounded:

- **The recent-attempt windows.** `load_attempt_prior_state` reads two windows:
  `list_recent_attempts_by_learning_object` (20) and `list_recent_attempts_by_practice_item` (5). These
  feed familiarity (`independent_evidence_discount`, and so `observation_weight`), event severity and
  the item-quality failure count.
  - Live, the attempt's own row and every later row do not exist yet.
  - In replay, both windows contained the attempts recorded **after** the one being recomputed.
  - On the repro, attempt 1's replayed `observation_weight` was 0.47 against 0.80 live. Its
    `same_item_recent_mass` was 0.5 against 0 live, because it counted attempt 2.
- **The canonical facet cache.** On canonical vaults (mvp-0.7 and later), `apply_attempt` re-projects
  the cache with `project_canonical_facet_state` over the whole observation ledger. Two things read
  that cache:
  - the next attempt's prior state, through `CanonicalFacetStateReader`, which feeds the prediction,
    `covered_required_fraction` (and so the variance floor) and the facet updates;
  - everything after the projection inside `apply_attempt`, such as causal materialization.

  Live, the fold ends at the current attempt. In replay it included every later attempt.
  - On the repro, attempt 1's replayed `facet_readiness` was 0.62 against 0.50 live.
  - Its `facet_blend_weight` was 0.17 against 0.

Which side was wrong is clear: replay's input contained events that did not exist when the live write
happened.

### 1b. `active`: replay reopened retired items

- `practice_item_state.active` is the item's serving lifecycle.
  - On every primary load, `sync_vault_state` sets it to 0 for retired items. It does the same for
    items parked for review, superseded measurement and microprobes.
  - Retirement, probe lifecycle and coherence also close it.
- Replay's per-LO reset deletes the row of every item that has attempts. The attempt path then
  rewrites the row with `active = (practice_mode != "diagnostic_probe")`, which is 1 for a retired item.
- All 30 rows on the LA copy are `status: retired` items that have attempts:
  - 15 constructed_response;
  - 10 recognition;
  - 4 recall;
  - 1 structured_calculation.
- On a copy that no primary had loaded, live had 1 as well: the upgrade's rebuild had already reopened
  them. That is why TE0's parity saw no difference.
- So replay was wrong: the lifecycle is not in the attempt ledger. A real `rebuild-derived-state`
  reopened retired items until the next load, though serving rejects retired items by YAML status
  anyway.

## 2. The fix (replay only)

- **`ApplyAttemptInput.replay_ledger_position`** carries `(created_at, id)`. It is set only by
  `replay_existing_attempt`, from the attempt row. Live callers leave it `None`.
- **Bounded windows.**
  - `list_recent_attempts_by_learning_object(s)` and `list_recent_attempts_by_practice_item` take
    `before=(created_at, id)`. With it they keep only the rows strictly earlier in the ledger's own
    `(created_at, id)` order.
  - `load_attempt_prior_state(..., ledger_before=)` passes the bound on replay only.
  - Unbounded calls run the same SQL as before.
- **Bounded canonical fold.** `project_canonical_facet_state(..., before=|through=)` folds only the
  ledger rows up to that position. Replay calls it twice per attempt:
  - `before` the attempt, before computing it: this is the cache the live write read;
  - `through` the attempt, after persisting it: this is the cache the live write left.

  A bounded fold reconciles the unresolved-cause factors in two steps:
  - it inserts the bounded ledger's factors, stamped with the attempt's clock, as live did;
  - it retires only open factors **of attempts inside the bound**.

  A partial ledger never judges a later attempt's factor. Without that limit, rebuild 1 opened fewer
  causal hypotheses and rebuild 2 added 24 more on the head fixture. That was found by
  `test_replay_never_reads_the_switch` ×3, and is fixed.

  Capability residuals are left to the whole-ledger projection that every replay already ends with:
  either `project_canonical_state=True` at the end of `replay_learning_object`, or the umbrella's
  `canonical_projection` replayer. Nothing an attempt computes reads them.
- **Lifecycle kept.** Before its reset, `replay_learning_object` reads which of the LO's items are
  inactive (`inactive_practice_item_ids`). After replay, `keep_practice_items_inactive` closes those
  rows again. Only the flag moves.
  - Nothing is ever reopened.
  - The attempt path's own flip still applies: an administered diagnostic probe that a pre-fix vault
    left active is still closed. This is pinned.
- **No new parameter, config key, table or migration.** The parameter registry and the schema
  references are unchanged.

Files:
- `src/learnloop/attempts/attempts.py`
- `src/learnloop/substrate/canonical_projection.py`
- `src/learnloop/substrate/replay.py`
- `src/learnloop/db/repositories.py`
- `tests/test_rebuild_equivalence.py` (new)
- `tests/test_mvp017_route_check_replay.py`
- `fixtures/mvp017_route_check_replay/README.md`

## 3. Successor or bug fix: bug fix, no successor

**The live path is byte-identical.**
- Every bound is `None` on a live write: `replay_ledger_position` is set only in
  `replay_existing_attempt`, the only caller with `replace_existing=True`.
- **Parity on owner copies:**
  - Setup: the same `f31` copy (built with this branch's code). The base code (`git archive
    0db8291c1`) and this branch each ran a primary load and then 12 self-graded live attempts across
    2–3 LOs per vault, with a frozen clock and no model.
  - The databases were compared on six tables: `learning_object_mastery`, `practice_item_state`,
    `facet_recall_state`, `facet_capability_evidence`, `practice_item_quality_state` and
    `attempt_surprise`.
  - Result: **identical**, on LA and on probability.

**Base code: its own replay diverged from its own live state.**
- Live attempts on owner copies made with base code, then base `rebuild --shadow`:
  - LA: mastery 2, schedule 33;
  - probability: mastery 2, schedule 3.
- The same with this branch: **0 / 0 / 0**.

**What does move: stored state that an old replay wrote.**
- A vault's derived state comes from its last rebuild, and every upgrade rebuilds. So the next rebuild
  or upgrade with this code corrects LOs whose stored state came from the old replay.
- On the owner's backups as they stand (`u31`: mvp-0.30 → mvp-0.31 with **main's** code, rebuilt
  twice), this branch's shadow shows those corrections. Every change is a correction toward
  live-equivalent state:

| Vault | Mastery rows | Schedule rows | Field changed |
|---|---|---|---|
| linear_algebra | 8 LOs; \|Δmean\| ≤ 0.195 logit, every variance down by 0.002–0.262 | 52 | `due_at`, −87 to +105 min |
| probability | 1 LO (mean −0.487 → −0.415, variance 1.586 → 1.473) | 1 | `due_at`, +74 min |

The playbook's test is whether the change alters persisted meaning. It does not: the meaning of
mvp-0.31 is the live update, and replay now reproduces it. That is the task's own definition of a bug
fix with no successor. The one-time correction above is the reason I list it as open question 1.

## 4. Owner-copy runs (backup-API copies; no model call)

**Copies.**
- Source: the owner's backups `fixtures-local/vault-backups-20261025-mvp030/{linear_algebra,probability}`
  in the main checkout (mvp-0.30).
- Each was copied once with `copy_tree_with_databases` to
  `learnanything-ad1/fixtures-local/rbeq/orig/`, and every other copy came from there.
- **Not opened:** anything in `~/learnloop-vaults`.

**Environment.**
- Every Python and CLI run went through `fixtures-local/rbeq/scripts/run.sh`, which uses `env -i` with
  `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` set to existing empty directories. They were still
  empty afterwards.
- `guard.py` installs an audit hook that refuses every socket connect, every DNS lookup and every
  process start.
- Base-code runs used `run_base.sh` on `git archive 0db8291c1` (`src` and `migrations`).

Shadow summaries, as facet / mastery / schedule, with the live database unchanged in every run:

| Run | linear_algebra | probability |
|---|---|---|
| Main's code, `u31` fresh (the issue's baseline) | 0 / 0 / 0 | 0 / 0 / 0 |
| Main's code, `u31` after a primary load (`SidecarContext.load`, maintenance on) | **0 / 0 / 30** (`active`: 0 live, 1 replay) | 0 / 0 / 0 |
| Main's code, `u31` + 12 live attempts | 0 / 2 / 33 | 0 / 2 / 3 |
| **This branch, `f31`** (upgraded and rebuilt ×2 with this code), fresh | **0 / 0 / 0** | **0 / 0 / 0** |
| **This branch, `f31` after a primary load** | **0 / 0 / 0** | **0 / 0 / 0** |
| **This branch, `f31` + primary load + 12 live attempts** | **0 / 0 / 0** | **0 / 0 / 0** |
| This branch on `u31` (state an old replay wrote) | 0 / 8 / 52 (the §3 corrections) | 0 / 1 / 1 |

The scripts are in `fixtures-local/rbeq/scripts/` (gitignored) and the JSON outputs in
`fixtures-local/rbeq/out/`.

**Calls.** All 34 learner databases under `fixtures-local/rbeq/` have **0 `model_call_receipts`**. No
model was called. **Spend: $0.**

The backup-API reads refreshed the `-shm` beside the two source backups in the main checkout, as at
earlier landings. Their `state.sqlite` files are untouched (mtime 00:25 / 00:26) and their `-wal` is
empty.

## 5. Tests

`tests/test_rebuild_equivalence.py` has 23 tests:
- **The two cases.** A two-attempt history with no claims rebuilds to live mastery exactly (same item,
  and two items). A retired item stays inactive through a primary load and a rebuild.
- **No leakage.** Every replayed attempt's familiarity, prediction, facet-update and mastery trace
  equals its live trace.
- **The probe flip** still closes an administered diagnostic probe that was left active.
- **The bounds.** The windows stop strictly before the position. A bounded fold equals the fold live
  left, and an empty bound gives an empty cache. Both bounds together is a `ValueError`.
- **Property tests: 16 seeded random histories.**
  - Each has 3–12 attempts across 4 LOs, interleaved so the per-LO replay order differs from the
    ledger's.
  - They mix independent, hinted, primed and "I don't know" attempts, with gaps from a minute to 4 days.
  - Odd seeds carry claims. Half the seeds retire an item. All end with a primary load.
  - Each must satisfy two checks: `shadow_rebuild` reports 0 / 0 / 0, and an applied rebuild leaves
    every mastery row (mean, variance, count, last evidence) exactly equal to live.

**Fail-first.** Against the base code (`-o pythonpath=<git archive 0db8291c1>/src`), 22 of the 23 fail.
The one that passes is the probe-flip pin, which pins behaviour that is unchanged.

**Two scope limits on claims.** Claims in the property tests are made before the vault's first sync.
- A claim made after an LO's first attempt is the LP claim fixes' defect 2 (mvp-0.32, on
  `lp/claim-fixes`).
- A `too_easy` retirement writes such a claim, so the random retirements use `duplicate_surface`.

**`tests/test_mvp017_route_check_replay.py`.**
- The fixture's derived rows were written by `e238fa07a`'s replay, the old leaky one.
- The test now pins the following:
  - the first rebuild moves exactly `attempt_surprise`, `learning_object_mastery` and
    `practice_item_quality_state`;
  - the single-attempt LO (`lo_transpose`) and every grade stay as written;
  - the ledgers are unchanged;
  - from the second rebuild on, the vault is at its fixed point.
- An example of the correction: `pi_unrelated_001`'s `bad_item_suspicion` goes from 0.12 to 0.06. Its
  first attempt had counted its second attempt's failure.
- The fixture database itself is unchanged. It stays at migration 186, so it cannot be regenerated
  with today's code. Its README says this.

## 6. Gate

Per the owner rule of 2026-10-17, the full suite was not run here: it runs once, in the landing gate.
Every pytest command ran in `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`, with `-n 6`.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken |
| Targeted run 1 (code at `d80c01392` plus the uncommitted tests), 239 files | 10,077 passed, 20 skipped, **4 failed**: `test_replay_never_reads_the_switch` ×3 (factor reconciliation, fixed in §2) and `test_an_mvp017_vault_replays_its_grades_exactly` (contract updated, §5) |
| Those 4 files plus `test_rebuild_equivalence.py` and `test_diagnostic_probe_single_use.py`, after the fix | 77 passed |
| Targeted run 2 on the final code (`593273412`), the same 239 files | **10,081 passed, 20 skipped, 0 failed** (44 min) |

The targeted list is every test file that names a changed function, or replay or rebuild in general,
plus the retirement tests and these contract tests:
- `test_architecture.py`
- `test_table_roles.py`
- `test_tracked_fixture_databases.py`
- `test_state_sync.py`
- `test_sidecar_serializer_snapshot.py`

The list is `fixtures-local/rbeq/out/targeted.txt`; Appendix A reproduces it. Run 1 took
49 minutes beside another stage's full suite.

Nothing was needed beyond that:
- **No durability lane:** there is no migration and no DB or connection code change. The new
  repository methods are plain queries.
- **No frontend, Tauri or schema change**, so no vitest, cargo check or reference regeneration.

## 7. Open questions

1. **The one-time correction on the owner's vaults.** At the next rebuild or upgrade with this code,
   their stored mastery moves: LA has 8 LOs moving by up to 0.195 logit and probability has 1. 52 and
   1 due times shift by up to about 1.7 h. The owner may want it labelled, for example in the upgrade
   note of whichever successor lands next (RW7b, or the LP claim fixes at mvp-0.32). My reading is
   that it needs no tag of its own (§3).
2. **Cost.** Replay now runs two bounded folds per attempt (live runs one). That is O(N²) over a
   rebuild, as live already is over a vault's life. LA's shadow still takes about 2 s.
   - A cheap optimization: skip the `before` fold when the previous replayed attempt is the global
     predecessor.
   - I left it out because it adds state for little gain at these sizes.
3. **Ties in `created_at`.** Live insertion order and `(created_at, id)` order can differ only for two
   attempts with the same timestamp. Replay already uses that order everywhere.
4. **Claims after the first attempt.** These stay a live-versus-replay difference until the LP claim
   fixes land (their defect 2). Running the property test with post-sync claims after that landing
   would close the last known class.

## Appendix A. Targeted test files (both runs)

- `tests/test_activity_backfill.py`
- `tests/test_activity_families.py`
- `tests/test_ad23_contract.py`
- `tests/test_ad23_fix_r5.py`
- `tests/test_ad23_fix_r6.py`
- `tests/test_ad23_fix_r8.py`
- `tests/test_ad23_fix_review.py`
- `tests/test_ad23_migration.py`
- `tests/test_ad23_owner_decisions.py`
- `tests/test_ad23_successor.py`
- `tests/test_ad2_model.py`
- `tests/test_ad3_reading.py`
- `tests/test_ad3_subject_view.py`
- `tests/test_adaptive_difficulty_ad1.py`
- `tests/test_ad_epoch.py`
- `tests/test_ad_guard.py`
- `tests/test_ad_protected_readings.py`
- `tests/test_answer_calibration_duel.py`
- `tests/test_answer_signal_arms.py`
- `tests/test_anti_double_count.py`
- `tests/test_approach_map_replay.py`
- `tests/test_approach_maps_schema.py`
- `tests/test_architecture.py`
- `tests/test_assessment_contracts.py`
- `tests/test_assumed_known.py`
- `tests/test_canonical_projection_rollout.py`
- `tests/test_capability_residual.py`
- `tests/test_card_lineage.py`
- `tests/test_causal_activity_policy.py`
- `tests/test_causal_attribution_exhibit.py`
- `tests/test_causal_attribution_p0.py`
- `tests/test_causal_attribution_p1.py`
- `tests/test_causal_attribution_p2.py`
- `tests/test_causal_factor_deferral.py`
- `tests/test_causal_orchestrator.py`
- `tests/test_causal_p2_acceptance.py`
- `tests/test_causal_repair_mapping_p2.py`
- `tests/test_causal_repair_sidecar_rpcs.py`
- `tests/test_causal_trace_consistency_p2.py`
- `tests/test_characterization_certification_ledger.py`
- `tests/test_characterization_probe_regrade.py`
- `tests/test_characterization_probe_replay.py`
- `tests/test_characterization_probe_submission.py`
- `tests/test_cli_entrypoint.py`
- `tests/test_commitment_arcs.py`
- `tests/test_common_repair_delivery.py`
- `tests/test_compare_sources_keep.py`
- `tests/test_conjunctive_instruments.py`
- `tests/test_contract_frontier_coverage.py`
- `tests/test_coverage_denominator_boundary.py`
- `tests/test_daily_loop_reader_authored_practice.py`
- `tests/test_daily_loop_reader_retire.py`
- `tests/test_daily_loop_reentry_break.py`
- `tests/test_daily_plan_composition.py`
- `tests/test_daily_plan_replay.py`
- `tests/test_deferred_regrade.py`
- `tests/test_depth_transition.py`
- `tests/test_diagnosis_adjudication.py`
- `tests/test_diagnosis_input_provenance.py`
- `tests/test_diagnosis_pipeline.py`
- `tests/test_diagnosis_replay.py`
- `tests/test_diagnostic_augmentation.py`
- `tests/test_diagnostic_probe_freshness.py`
- `tests/test_diagnostic_probe_single_use.py`
- `tests/test_discrimination_profiles.py`
- `tests/test_doctor.py`
- `tests/test_durable_promotion_arms.py`
- `tests/test_e0_review_round6.py`
- `tests/test_e1_harness.py`
- `tests/test_e2e_local.py`
- `tests/test_embedding_store.py`
- `tests/test_error_hunt_items.py`
- `tests/test_event_sufficiency.py`
- `tests/test_evsi_router_composition.py`
- `tests/test_exam_protection_review.py`
- `tests/test_exam_seeding.py`
- `tests/test_facet_diagnostics_v03.py`
- `tests/test_facet_evidence_timeline.py`
- `tests/test_facet_identity_actions.py`
- `tests/test_facet_identity_ingest.py`
- `tests/test_failure_triage_causal_gate.py`
- `tests/test_family_memory_projection.py`
- `tests/test_field_cli.py`
- `tests/test_field_priors.py`
- `tests/test_field_signal_production_paths.py`
- `tests/test_field_workbench_signals.py`
- `tests/test_figures_migration.py`
- `tests/test_followup_diagnostic_selection.py`
- `tests/test_forecast_receipts.py`
- `tests/test_goal_series.py`
- `tests/test_golden_path_run.py`
- `tests/test_grade_resolution_pipeline.py`
- `tests/test_grading_cli.py`
- `tests/test_grading_support.py`
- `tests/test_guided_redo.py`
- `tests/test_held_grade_composition.py`
- `tests/test_held_grade_evidence.py`
- `tests/test_help_outcomes.py`
- `tests/test_hint_telemetry.py`
- `tests/test_ingest_instrument_gates.py`
- `tests/test_interaction_signals.py`
- `tests/test_intervention_outcomes_replayer.py`
- `tests/test_item_authoring.py`
- `tests/test_item_fingerprints.py`
- `tests/test_item_parameters.py`
- `tests/test_keep_local_retired.py`
- `tests/test_km2b_consumer_rekey.py`
- `tests/test_km2_canonical.py`
- `tests/test_km2_write_path.py`
- `tests/test_learner_review_system_entries.py`
- `tests/test_local_fusion_core.py`
- `tests/test_mcp_c1a_narrow.py`
- `tests/test_method_explicit_upgrade.py`
- `tests/test_minimal_repair_selection_a1.py`
- `tests/test_misconception_resolution.py`
- `tests/test_missing_vocabulary_notes.py`
- `tests/test_model_grade_lane.py`
- `tests/test_mvp010_upgrade.py`
- `tests/test_mvp011_upgrade.py`
- `tests/test_mvp013_upgrade.py`
- `tests/test_mvp014_upgrade.py`
- `tests/test_mvp015_upgrade.py`
- `tests/test_mvp016_upgrade.py`
- `tests/test_mvp017_route_check_replay.py`
- `tests/test_mvp017_upgrade.py`
- `tests/test_mvp018_upgrade.py`
- `tests/test_mvp020_upgrade.py`
- `tests/test_mvp021_upgrade.py`
- `tests/test_mvp022_upgrade.py`
- `tests/test_mvp023_upgrade.py`
- `tests/test_mvp024_upgrade.py`
- `tests/test_observation_ledger_bulk.py`
- `tests/test_p0_cutover_mvp08.py`
- `tests/test_p0_projection_cutover.py`
- `tests/test_p2_acceptance.py`
- `tests/test_p2_leakage_suite.py`
- `tests/test_p3_journeys.py`
- `tests/test_pfc_unassessed_readers.py`
- `tests/test_pfc_unverified_unassessed.py`
- `tests/test_placement_split_grades.py`
- `tests/test_plan_determinism.py`
- `tests/test_post_attempt_worker.py`
- `tests/test_practice_index_dossiers.py`
- `tests/test_probability_arms.py`
- `tests/test_probability_cli.py`
- `tests/test_probability_prep.py`
- `tests/test_probe_audit.py`
- `tests/test_probe_belief_posterior.py`
- `tests/test_probe_block_end.py`
- `tests/test_probe_dialogue.py`
- `tests/test_probe_episodes.py`
- `tests/test_probe_lifecycle.py`
- `tests/test_probe_longform_families.py`
- `tests/test_probe_migration.py`
- `tests/test_probe_orchestration_remainder.py`
- `tests/test_probe_policy.py`
- `tests/test_probe_pool_empty.py`
- `tests/test_probe_remint.py`
- `tests/test_probe_robust_cutover.py`
- `tests/test_probe_surface_mint.py`
- `tests/test_project_experiment_store.py`
- `tests/test_projection_evidence_polarity.py`
- `tests/test_public_tip_guards.py`
- `tests/test_reader_dialogue.py`
- `tests/test_reader_recap_review_r2.py`
- `tests/test_reader_recap_review_r3.py`
- `tests/test_reader_rw1c_review.py`
- `tests/test_reader_rw7a_migration.py`
- `tests/test_reader_workbench_rw2a.py`
- `tests/test_reading_step_switch.py`
- `tests/test_rebuild_equivalence.py`
- `tests/test_rebuild_orchestrator.py`
- `tests/test_recall_coverage_interventions.py`
- `tests/test_receipt_derivation.py`
- `tests/test_receipt_exactness.py`
- `tests/test_recurrence_benchmarks.py`
- `tests/test_recurrence_commands.py`
- `tests/test_recurrence_deferral.py`
- `tests/test_recurrence_live.py`
- `tests/test_reentry_short_session.py`
- `tests/test_reference_gate_imports.py`
- `tests/test_regrade_contract_replay.py`
- `tests/test_regrade_contract_successor.py`
- `tests/test_regrade_contract_upgrade.py`
- `tests/test_remediation_cold_retry.py`
- `tests/test_repair_splice.py`
- `tests/test_replay.py`
- `tests/test_required_method_authority.py`
- `tests/test_required_method_grading.py`
- `tests/test_retrieval_spaces_migration.py`
- `tests/test_reveal_ledger.py`
- `tests/test_robust_composition.py`
- `tests/test_router_coldness_covariates.py`
- `tests/test_router_g4_restraint.py`
- `tests/test_router_outcomes.py`
- `tests/test_router_p2_bridge.py`
- `tests/test_router_r1_composition.py`
- `tests/test_router_r2a_serving.py`
- `tests/test_router_r2b_agreement.py`
- `tests/test_router_r2c_retrieval.py`
- `tests/test_route_rules_in_grader.py`
- `tests/test_rw2c_fix_round2.py`
- `tests/test_salience_firewall.py`
- `tests/test_scheduler.py`
- `tests/test_scoreboard.py`
- `tests/test_self_attributed_misconceptions.py`
- `tests/test_serve_eligibility.py`
- `tests/test_shadow_rebuild.py`
- `tests/test_sidecar_measurement.py`
- `tests/test_sidecar_serializer_snapshot.py`
- `tests/test_sidecar_tutor_qa.py`
- `tests/test_source_append.py`
- `tests/test_source_block_fts.py`
- `tests/test_source_set_synthesis.py`
- `tests/test_sources_merge_composition.py`
- `tests/test_source_space_resolver.py`
- `tests/test_sqlite_file_copies.py`
- `tests/test_sqlite_wal_lifecycle.py`
- `tests/test_sqlite_wal.py`
- `tests/test_staged_policy_evsi.py`
- `tests/test_state_sync.py`
- `tests/test_stuck_prompt_composition.py`
- `tests/test_stuck_prompt.py`
- `tests/test_stuck_prompt_replay.py`
- `tests/test_substrate_cutover.py`
- `tests/test_success_head_cli.py`
- `tests/test_surfaced_belief_corrections.py`
- `tests/test_table_roles.py`
- `tests/test_teach_back.py`
- `tests/test_tracked_fixture_databases.py`
- `tests/test_unresolved_cause_gate.py`
- `tests/test_ux_phase1_round2_rereview.py`
- `tests/test_ux_phase2_error_type_proposals.py`
- `tests/test_ux_phase2_shell.py`
- `tests/test_ux_phase4_feedback.py`
- `tests/test_valuation_calibration_fields.py`
- `tests/test_voi_merge_composition.py`
- `tests/test_voi_stopping.py`
- `tests/test_workbench_assistance.py`


## Landing onto main (2026-10-26)

This stage and mobile PR-2 (`mobile/pr2-content-sync`, [`mobile-pr2-content-sync.md`](mobile-pr2-content-sync.md))
landed together, in one merge branch with one full gate. The branch is `merge/rbeq-pr2-onto-main` in
`learnanything-merge2`, cut from `main` at `eaf9859ad`. At that point main held the LP claim fixes' `mvp-0.33`,
migrations through 222 (C0a) and the head fixture `fixtures/migration_head_222`. Main was neither fast-forwarded nor
pushed. **`mvp-0.34` now follows `mvp-0.33`. There is no migration.**

### Commits and conflicts

- `6b388e6f5`: the `--no-ff` merge of `fix/rebuild-equivalence` (`060653244`). Every conflict was composed so that
  both sides survive:
  - `algorithm_versions.py`: `REPLAY_LEDGER_ALGORITHM_VERSION` after `READING_PATH_PLAN_` and `CLAIM_FIXES_`, in the
    chain and the version sets. The comment now says `mvp-0.34` is built on `mvp-0.33`.
  - `cli/app.py`: the imports, `--to` help, dispatch and error text name `mvp-0.32`, `mvp-0.33` and `mvp-0.34`. The
    docstring describes all three, and `mvp-0.34` is the default.
  - `config/template.py`:
    - each defaults-snapshot comment names RW7b's, LP-min (a)'s, C0a's and this stage's keys;
    - the `mvp-0.33` entry says new vaults started there until this successor landed;
    - a new `mvp-0.34` entry was added, built on `mvp-0.33`;
    - **all 25 fingerprints were recomputed** with `defaults_fingerprint_for_version`. Dropping `[replay]` from the
      effective config reproduces main's value for every version except the new `mvp-0.34`, so the key changes
      nothing else. The template `.pyc` was cleared first.
  - `substrate/replay.py`: LP's `_ClaimStream`, which applies claims at their own time, `finish()`es first. This
    stage's `keep_practice_items_inactive` runs after it, and both sit inside the one-transaction
    `_replay_learning_object`.
  - `Concepts/Algorithm Versions and Reproducibility.md`: the `mvp-0.33` row (main's landing had not added it) and
    the `mvp-0.34` row ("successor to `mvp-0.33`"). The chain paragraph lists every set through `mvp-0.34`.
  - `db_generate_reference.py`: both the `curriculum` and the `replay` section descriptions.
  - The chain pins in 21 test files: this stage's head-indexed pins (`SUCCESSOR_CHAIN[n]`), with `mvp-0.32` and
    `mvp-0.33` added to every version set.
  - `cli_help_snapshot.json` and the 425 generated reference notes: main's text, then regenerated (below).
- `replay_ledger_upgrade.py`: `PREDECESSOR = CLAIM_FIXES_ALGORITHM_VERSION`, and `_upgrade_to_predecessor =
  upgrade_to_claim_fixes`. Its tests take `PREDECESSOR` from the constant.
- `03b86177c`: the `--no-ff` merge of `mobile/pr2-content-sync`. Only generated reference notes conflicted.
  `repositories.py`, `state_sync.py` and `context.py` merged cleanly.
- `5563d6960`: the journalled activation (below), the remaining tail pins, and the interaction tests:
  - `test_lp_claim_fixes.py` and `test_plan_follows_path.py` pinned `LATEST == "mvp-0.33"` and the bare upgrade's
    target. They are now adjacency pins, and LP's CLI step names its own `--to`.
- `bcb26db88`: the CLI help snapshot (`upgrade` only) and docstrings. `beeb7a759`: the references. Then these
  records.

Against main, the diff adds `src/learnloop/replay_ledger_upgrade.py`, four test files (this stage's two, PR-2's
race file and `tests/test_rbeq_pr2_landing.py`) and the four review records. **It adds no database or binary file,
and the root `.gitignore` is unchanged.**

### The chain, and the activation journal (a landing change)

The LP claim fixes landed after this stage was built. Their activation is **journalled**, and no entry point serves a
vault while a journal stands (`learnloop.activation_journal`, LP re-review F2). This stage's activation is the same
kind: one transaction, with the config's publication last. Without a journal, a death between this activation's
publication and its commit would have left `mvp-0.34`'s label over `mvp-0.33`'s database, and every opener would have
served that state until someone reran the upgrade. The brief requires the next guarded open to complete such an
activation, or to refuse it with the upgrade message. So the landing gives `mvp-0.34` the same journal:

- **Before the publication**, `_activate` writes the journal (`{"predecessor": "mvp-0.33", "target": "mvp-0.34"}`)
  at the same path, using LP's `write_activation_journal`, which is now public. It removes the journal after the
  commit. A failure that restores the predecessor's label removes it too.
- **`replay_ledger_upgrade.complete_interrupted_activation`** is now the completion that the CLI
  (`cli/runtime.py`) and the desktop sidecar (`learnloop_sidecar/context.py`) install. Both completers are renamed
  `_complete_interrupted_activation`.
  - A journal naming `mvp-0.34` is completed here, under the lock, inside `completing_activation()`.
  - A torn journal at `mvp-0.33` is removed: it was torn before its fsync, which precedes the publication.
  - Any other journal goes to the claim fixes' own completion.
  - So one completion serves the whole chain, and the latest link hands earlier journals back.
- **`upgrade_to_replay_ledger`** first completes any journalled activation, its own or an earlier link's. An
  interrupted `mvp-0.34` then reports "completed the interrupted activation of mvp-0.34". The stage's F5 path, for a
  label without a journal, stays as it was.
- These tests failed first on `03b86177c`: 8 of the 10 in `tests/test_rbeq_pr2_landing.py`.
  - The 10 cover a real death (a forked `os._exit` after the publication), then the next CLI command; each of the
    four writing openers; the refusal with no completion installed (every attach); the upgrade's own completion; a
    failure after the rename; the hand-off of a claim-fixes journal; and a torn journal.
  - The 2 that passed on the base pin behaviour that was already right: an attach refuses while any journal stands,
    and a failure leaves no journal.

The upgrade itself: `learnloop upgrade --to mvp-0.34` from `mvp-0.33`, or from `mvp-0.9` to `mvp-0.32` through the
chain (and `mvp-0.8` is refused). Bare `learnloop upgrade` targets `mvp-0.34`. `chain_from.py` ran on placement
vaults from `mvp-0.9`, `0.27`, `0.29`, `0.30`, `0.31`, `0.32` and `0.33`, from `mvp-0.8` by `--to mvp-0.9` then
`--to mvp-0.34`, and with the bare upgrade from `mvp-0.33`: **all OK**.

### Interactions

**(i) LP's claims at their own time, with the bounded folds.** The stage deferred two classes until LP landed: claims
made after an LO's first attempt, and `too_easy` retirements. Both are now in
`test_random_histories_with_claims_after_attempts_and_too_easy_retirements_rebuild_to_live`, which runs 16 seeds:

- 1-3 live re-anchoring claims are placed between and after attempts on random LOs. They are tutor gap declarations,
  which append.
- Odd seeds also carry a claim made before the first sync.
- Each history ends with a `too_easy` retirement (three seeds in four) or a `duplicate_surface` one, then a primary
  load.
- Every seed shadow-rebuilds to **0/0/0**, and two applied rebuilds leave mastery exactly as live.

**Finding, pre-existing on main at `mvp-0.33`:** a second learner report on one LO, after an attempt, breaks
rebuild equivalence. A learner report is a `too_easy`/`too_hard` retirement or a rung-variant request.

- Each such report replaces the LO's earlier `learner_report` claim (`delete_learner_claims`, "the replace seam").
- That earlier claim's live re-anchor had already moved mastery. Replay cannot apply a claim that is gone, so the
  rebuild differs from live.
- With one attempt and two `too_easy` retirements, the result is identical at `mvp-0.33` and `mvp-0.34`: mastery 1
  (Δmean −0.269 on `lo_diag`). So the bounds do not cause it.
- The first random run found it in 6 of 16 seeds, because the generated claims used the `learner_report` source.
- It is pinned as a strict xfail at both versions:
  `test_a_second_learner_report_on_an_lo_after_an_attempt_rebuilds_to_live[mvp-0.33|mvp-0.34]`.
- The fix keeps the replaced claim, or a tombstone with its time, so that replay can apply it. That changes the claim
  ledger's meaning, so it is LP's successor work, not a landing change. It is reported as an open item.

**(ii) PR-2's reconcile and this stage's retired items.** `test_a_full_sync_after_a_rebuild_keeps_retired_items_retired`:

- A `too_easy` retirement and a `duplicate_surface` one are closed by a primary load.
- A rebuild, then a full sync, leaves both inactive. Their `due_at`, stability and difficulty are not written, and the
  shadow reads 0/0/0.
- The retired class this stage keeps is YAML `status: retired`. `practice_item_activatable` already rejects every
  status except `active`, so nothing needed adding.
- Deactivations that are not in the YAML (probe lifecycle, coherence) are kept by replay. A later sync still decides
  them by PR-2's rule, as before both stages.

**(iii) Nesting `atomic()`.** `test_content_sync_nests_inside_a_rebuild_transaction_and_rolls_back_with_it`:

- Inside a caller's `Repository.atomic()`, the per-LO replays (this stage's F1) and PR-2's reconcile are savepoints.
- A rebuild then a sync, followed by a raise, roll back `learning_object_mastery` and `practice_item_state` byte for
  byte.
- The same pair commits together without the raise, and the stale active flag of the retired item is closed.

### Regeneration

- `db_generate_reference.py`: the `[replay]` section is in, at **1,055 leaves and 72 sections**. The prose counts in
  `Configuration.md` and `Database.md` were updated by hand. `db_validate_reference.py` reports **errors: []**.
- `validate_vault.py`: passed.
- `module_validate.py` and `desktop_validate.py` fail on main too (stale module notes, and an unclassified
  `syntheticBook.ts`). That predates this landing and is left to the queued docs workflow.
- `tests/cli_help_snapshot.json`: only `upgrade` changed.
- The RPC and serializer pins needed nothing: their contract tests pass as merged.

### Gate

Setup ran in 5G scopes: `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`. The pytest lanes ran
under `flock /tmp/learnloop-fullsuite.lock` in 10G / 2G-swap scopes, with `env -i` and empty, existing `HOME`,
`CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` (still empty afterwards). Every lane ran at `beeb7a759`. Logs are in
`fixtures-local/landing-rbeq/logs/`.

| Step | Result |
|---|---|
| `lint-imports --no-cache` | **36 kept**, 0 broken |
| targeted run on the composed merge, before the landing commits (the chain, contract, replay, sync and LP/RW7b files) | 1,013 passed, 4 failed: the four tail pins fixed in `5563d6960`/`bcb26db88` |
| full suite, run 1 (`pytest -n 8`) | **stopped at 21,514 of 21,796 tests** after 4 h (`fullsuite-run1-killed.log`). Under a load average of 120-200 from other stages, one worker held all 84 `test_reader_rw1c_review::test_every_sent_model_written_fragment_was_checked` cases. Each sidecar context there leaks 5 threads (two reading sweeps and three post-attempt workers), so that worker reached ~750 threads, ran at ~20 CPU cores, and needed about 20 minutes per test. Neither stage adds threads, and the leak is in the test file's contexts. The run was stopped and rerun |
| **full suite, run 2** (`pytest -n 8 -p no:cacheprovider --dist worksteal`, 52 min) | **21,663 passed, 12 failed**, 80 skipped, 41 xfailed. **10 are the installed Codex CLI**: the system's `@openai/codex` was upgraded to **0.164.0** today at 11:21, and its feature list no longer reports `realtime_conversation` and `worktrees` as off. So the lockdown fails closed ("Codex does not report feature … off; refusing the isolated turn") in `test_codex_isolation_mcp_check` ×3, `test_codex_lockdown_round2` ×3, `test_codex_lockdown_round3` ×3 and `test_diagnosis_isolation::test_configured_mcp_servers_are_listed_and_disabled`. **The same 10 fail on main's tree** (`git archive main`, run alone). The other 2 are known load flakes, each **3/3 passed** alone: `test_plan_first_transport_offer_grants::test_p1_…` and `test_reading_hardening_2_fixes::test_f1_a_build_whose_worker_failed_to_start_is_run_by_the_sweep` |
| durability (`-m durability`; it includes PR-2's race tests and this stage's F1 tests) | **137 passed**, 1 skipped |
| owner lane (`-m owner_vaults`, backup-API copies of the three mvp030 backups in `fixtures-local/owner-lane-rbeq/`) | 83 passed, 6 failed. These are exactly the 6 known, pre-existing failures: 4 need the retired vaults (`test_doctor` pre-044, `test_migrate_fresh` 153, `test_goal_decay_projection`, `test_sidecar_contract` recent ingests), plus `test_activity_backfill` and `test_placement_fixture_copies[arxiv_v2]`. The copies' `model_call_receipts` are 0 |
| `npm install`; `npm run typecheck` | ok; clean |
| `npm test -- --maxWorkers=4` (whole vitest) | **214 files, 1,834 tests passed** |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path src-tauri/Cargo.toml` | finished |
| worktree | `git status` clean apart from `fixtures-local/` |

### Parity (backup-API copies of the mvp030 backups; no real model call)

**Setup** (`fixtures-local/landing-rbeq/scripts/`; the C0a landing's kit, re-pathed, plus `b34/c34/d34.sh`,
`chain_from.py`, `sched_dump.py`, `sched_delta.py` and `live_attempts_frozen.py`):
- `orig/` holds backup-API copies of `learnanything/fixtures-local/vault-backups-20261025-mvp030/{linear_algebra,probability}`.
- `u33/` is `orig` brought to **mvp-0.33 with main's code**: routes sent to a `127.0.0.1:9` blackhole (all 64
  tasks), `upgrade --to mvp-0.33` (mvp-0.30 → mvp-0.33), then `rebuild-derived-state` twice.
- `code_main` and `code_merge` are `git archive` exports of `eaf9859ad` and `beeb7a759`.
- Every run went through `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. `run.py`'s audit hook
  refuses any Codex process start and any non-loopback socket.

**(a) Main vs merge at mvp-0.33** (`a33.sh`, with a second main copy as the noise control):
- **Whole databases** after the normal primary sidecar load: **every row of 357 tables is identical**: 18,496
  rows on linear_algebra and 8,129 on probability. There are no schema diffs, `schema_migrations` is identical (head 222), integrity is ok,
  `foreign_key_check` is 0 and `model_call_receipts` is 0.
- **Certification, Today and the plan: byte-identical** main vs merge, and main vs main, on both vaults.
- **`doctor`: identical**: 57 issues / 1 error on LA, and 101 / 48 on probability, which predate the stages.
- **`rebuild --shadow`**: probability is 0/0/0 on both sides.
  - On linear_algebra, main's shadow reports **30 schedule changes** and the merge's **0**.
  - Those 30 rows are this stage's 1b: main's replay reopens 30 retired items.
  - The lifecycle fix acts at every version, by design.
  - Live state is identical, so PR-2 changes nothing without a concurrent writer.

**(b) The upgrade to mvp-0.34** (merge code; `b34.sh`):
- **Direct** (`up34`, from u33): "mvp-0.33 → mvp-0.34".
  - **Rows**: every row of every ledger keeps its id. Only derived tables and re-derived columns are rewritten:
    - `error_events.severity` on 17 of 19 rows, from the bounded window;
    - `attempt_debug_payloads`;
    - the `parameter_registry` refresh.
    - This is the same set as at the LP landing, plus `hypothesis_recurrence_state` (the F3 reconciliation).
  - **The one-time correction:**

    | Vault | LOs that move | Δ mean (logit) | Δ variance | Due times |
    |---|---|---|---|---|
    | linear_algebra | 8 of 21 | −0.248 to +0.006 (largest `lo_what_makes_a_vector_space`, 1.123 → 0.875) | −0.471 to −0.003 (all down) | 52 items, `due_at` −89 to +81 min |
    | probability | 1 of 18 (`lo_analyze_and_optimize_nonuniform_collision_probab`) | −0.440 → −0.348 | 2.167 → 1.964 | 1 item, +66 min |

  - **Shadow 0/0/0** right after the upgrade, and again after two rebuilds. The two rebuilds move no LO.
  - **Then a primary load and 12 self-graded live attempts** (frozen clock, on `live34`): shadow **0/0/0** on both
    vaults.
- **Bare `upgrade`** (`dflt34`): "mvp-0.33 → mvp-0.34".
- **The owner's chain from mvp-0.30.**
  - `ch34`: `--to mvp-0.34` in one command, "mvp-0.30 → mvp-0.34". LP's step notes are passed through. Shadow
    0/0/0 right after and after two rebuilds. The rows are kept as in the direct case (plus migrations 219-222).
  - `st34`: `--to mvp-0.33`, then `--to mvp-0.34`, then a rebuild: shadow 0/0/0.
- `doctor` after the upgrade: unchanged (57/1 and 101/48).

**(c) `[replay] ledger_bounded = false` at mvp-0.34 equals mvp-0.33** (`c34.sh`; `base33` is u33 opened by the merge):
- `k34` has the switch off before the upgrade, then the upgrade and two rebuilds.
- `kr34` was upgraded with the switch on and rebuilt twice, then had the switch turned off and was rebuilt once.
- Against `base33`, both are identical after the version stamp in certification, Today, mastery and every schedule
  row, on both vaults. Today's and the schedules' raw bytes are identical too.
- **The plan differs in exactly one value**: the router card's `card_hash` (and the snapshot hash and receipt
  that carry it).
  - The card carries the version label, so this is the label. It is the same effect the LP landing recorded.
- For the record, `on34` (the switch on) differs from `base33` by the correction in (b): mastery, 52 and 1 due
  times, and Today and the plan that read them.

**(d) An interrupted activation** (`d34.sh`, `dx2.sh`; the upgrade dies with `os._exit(17)` right after the
publication, leaving the `mvp-0.34` label, `mvp-0.33`'s mastery and the journal):
- **A guarded writing CLI command** (`backfill-originals`) completes it. The journal is gone, and the mastery equals
  `up34`'s right after its upgrade, on both vaults.
- **`learnloop upgrade --to mvp-0.34`** completes it ("completed the interrupted activation of mvp-0.34"), with
  mastery equal to `up34`'s. Running it again answers "vault is already mvp-0.34".
- **The desktop start** (`SidecarContext.load`) completes it, with mastery equal to `up34`'s.
- **Every attach that may not complete it refuses** with the message "The upgrade to mvp-0.34 did not finish (…) run
  `learnloop upgrade --to mvp-0.34`". That covers a script's `Repository`, `open_vault_repository` with no
  completion, the PR-1 secondary attach and the remote runtime (`SchemaMismatch`). Nothing changes, and the upgrade
  then completes it.
- **Plain `doctor --json`** is a read-only attach. It refuses with the same message, but as a traceback. That is the
  LP landing's recorded Low; it is fail-closed.

**Receipts and calls.**
- There are 74 databases under `fixtures-local/landing-rbeq/`. 52 have **0 `model_call_receipts`**. The other 22
  are the probability backup's empty 4 KB `.learnloop/state.sqlite` stubs, with no tables.
- `run.py`'s audit log was never created, so no process start and no socket connection happened.
- **Spend: $0.**
- Nothing under `~/learnloop-vaults` was opened or listed.

### Owner notes

- **Before upgrading:** back up the vaults, and close the desktop app, the MCP server and the phone page.
- **Then run `learnloop upgrade --to mvp-0.34`** on each vault. It works from `mvp-0.33`, and from `mvp-0.30` or
  `mvp-0.31` it chains through `mvp-0.33` in the same command. Bare `learnloop upgrade` does the same.
- **What changes:**
  - Once, the topic estimates and due times that the old rebuild wrote are corrected to what your answers produced
    live.
  - On the backups: linear algebra moves 8 topics (at most 0.25 logit, each a little more certain) and shifts 52 due
    times by up to about 1.5 h. Probability moves 1 topic and 1 due time (+66 min).
  - After that, every rebuild reproduces your live state.
  - Grades, attempts and certification do not change.
- **If the upgrade is interrupted** (a crash or power loss mid-way), the vault is not served until it completes.
  Opening the desktop app or running the upgrade again completes it. The phone page and MCP show the upgrade
  message meanwhile.
- **Kill switch:** `[replay] ledger_bounded = false` in `learnloop.toml`. A rebuild then reads the history as before
  (`mvp-0.33`'s replay), with no downgrade.

### Open items

- **F2 (Low, from the stage):** attempts with the same `created_at` second, committed in reverse id order, replay by
  id. The strict xfail stays until a commit-sequence column lands (its own stage).
- **New (Medium, LP's class, pre-existing):** the learner-report replace seam (interaction (i) above). Two learner
  reports on one LO after an attempt make a rebuild differ from live. Every upgrade rebuilds, so the owner's vaults
  carry it wherever that has happened.
  - Proposed: keep replaced `learner_report` claims as superseded rows, or tombstones with their time. Replay can
    then apply each claim at its own time, and the covering read uses only the latest.
  - That is a successor, behind LP's switch or its own. It is pinned by the strict xfail at `mvp-0.33` and `mvp-0.34`.
- PR-2's reverse race (an attempt writing the whole `practice_item_state` row) is PR-4's. See the PR-2 record.
- `module_validate.py` and `desktop_validate.py` fail on main already, which is for the docs workflow.
- **Environment (for the orchestrator):** the installed Codex CLI 0.164.0 (upgraded on the machine on 2026-10-26)
  fails LearnLoop's Codex lockdown check closed. Every opted-in Codex turn is refused until the lockdown learns the
  new feature list, and 10 tests fail on main too. Serving routes are on the plan (T1), so this is not learner-facing
  by default.
- `test_reader_rw1c_review.py` leaks 5 sidecar threads per test. Under heavy machine load that serializes onto one
  xdist worker, which is what stalled gate run 1. `--dist worksteal` avoided it.
