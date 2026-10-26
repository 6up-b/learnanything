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
