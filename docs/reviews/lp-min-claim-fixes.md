# LP-min (a): the four claim-defect fixes

Stage `lp-claim-fixes`, branch `lp/claim-fixes` from `fa2eb72f8` (main: latest
`mvp-0.31`, migration head 220). Spec: `docs/specs/spec_learned_parameters_v1.md`
§3.0b item 1 and §9 (LP-min (a)); AD §5.5 for the claims rule. Owner-approved
queue, 2026-10-25.

## What was wrong (verified in code first, at `fa2eb72f8`)

| # | Defect | Where | Verified by |
|---|---|---|---|
| 1 | A tutor gap declaration writes a claim and never re-anchors. Sync materializes a mastery row for every LO up front, and `covering_learner_claim` feeds only first materialization, so the claim is inert on every existing LO. | `tutor/promotions.py::_write_gap_claim` (was 773-795) | `test_defect1_off_*`: after the gap promotion the mastery row is byte-identical to before |
| 2 | Replay seeds a reset LO from the claims in force at rebuild time. A claim written after an attempt seeds that attempt's prior; a re-anchoring claim made after the first attempt is lost (or becomes the seed). | `substrate/replay.py::replay_learning_object` → `attempts.load_attempt_prior_state` → `initial_mastery_state_for_learning_object` → `covering_learner_claim` (every claim) | `test_defect2_off_*`: a claim stamped after the only attempt lowers that attempt's rebuilt mean |
| 3 | `apply_claim_evidence` (the warm merge) returns variance `1/(1/P + pseudo_count)`, so a self-report shrinks the variance of an evidence-backed state. AD §5.5: "a claim moves a mean and never shrinks a variance". | `learner/mastery.py::apply_claim_evidence` | `test_defect3_off_*` and the unit test: the merged variance is below the state's |
| 4 | `_claim_rank` breaks specificity ties by pseudo-count, then the HIGHER claimed level, then recency, so an older, more confident or higher claim beats a newer revision. | `learner/mastery.py::_claim_rank` | `test_defect4_off_*`: the older high claim wins; at equal time and pseudo-count the higher level wins |

## What changed

**One successor, one kill switch for all four.** `CLAIM_FIXES_ALGORITHM_VERSION`
(`algorithm_versions.py`, built as `mvp-0.32`: the next free tag after
`mvp-0.31`; reader workbench RW7b builds a successor at the same time, so the
landing renumbers this ONE constant). `CLAIM_FIXES_VERSIONS` is the gate
(`successors_from`). The switch is `[mastery] claim_fixes_enabled = true`
(modelled default, left out of the decision-only template); one switch because
the four fixes are one meaning: a claim is applied at its own time, mean-only,
and the most recent wins; fix 2's replay only reproduces fix 1's live
re-anchor if both are on. `mastery.claim_fixes_live(vault)` is the single
predicate (tag AND switch).

1. **Gap declarations re-anchor** (`tutor/promotions.py::_write_gap_claim`).
   Live: the claim is written with an explicit `created_at` and the LO is
   re-anchored through `reanchor_mastery_from_claim` at that same instant (a
   zero-evidence row is re-seeded from the covering claim; a row with
   evidence gets the mean-only merge). Off: the predecessor's single insert,
   unchanged.
2. **Replay applies claims at their own time** (`substrate/replay.py::_ClaimStream`).
   After the LO's derived state is reset: just before the first attempt the
   row is seeded from the claims made by that attempt
   (`initial_mastery_state_for_learning_object(..., claims_as_of=...)`,
   which is exactly the state the attempt path would construct); each later
   claim from a re-anchoring source (`mastery.REANCHORING_CLAIM_SOURCES`:
   `rung_variant_request`, `learner_report`, `tutor_gap_declaration`, the
   sources whose writers re-anchor live) re-anchors through the live function
   at its own `created_at`, before any attempt stamped after it; claims after
   the last attempt re-anchor at the end. A claim stamped at the same instant
   as an attempt goes first (a rung-variant request writes its claim, then
   its self-report attempt). Other sources (the init wizard's global claim, a
   manual claim) act only through the seed, as they do live once a row
   exists. `covering_learner_claim(..., as_of=...)` honours `as_of` only
   under the successor.
3. **A warm merge keeps a variance floor** (`apply_claim_evidence(..., mean_only=True)`,
   passed by `reanchor_mastery_from_claim` under the successor). The mean
   moves by the same precision weights; the variance is
   `max(merged, current)`, i.e. the state's own. The floor is the state's
   variance itself: structural, no new number.
4. **Ties by recency, then pseudo-count, never by level**
   (`_claim_rank_by_recency`): specificity, then parsed `created_at`, then
   pseudo-count, then the id (determinism only). The level is not in the key.
   This is the ranking every `covering_learner_claim` reader sees at the tag
   (the seed, probes, practice generation's calibration, goal projection, the
   capability grid, field's frozen priors).

**No new weights.** The only quantities are the AD rule's own (the claim's
level and pseudo-count, as before) and a structural `max`. The one new config
key is a boolean, classified `structural / operational` in
`params/parameter_registry.py`.

**Upgrade** (`claim_fixes_upgrade.py::upgrade_to_claim_fixes`, CLI
`learnloop upgrade --to mvp-0.32`, the default target). It accepts
`mvp-0.31`, or `mvp-0.9` up to it through RW2d's chained upgrade, and refuses
anything older. It changes learner state when it activates, so under the
vault mutation lock one transaction covers the predecessor's manifest, the
replay of exactly the LOs with attempts that a claim covers (no other LO's
replay can differ), the re-projection, the registry refresh and, last, the
durable config publication; a failure rolls back and restores the label. Its
note names the replayed LOs. Added to the experiments-stay-outside-production
contract in `pyproject.toml`.

**Defaults snapshots.** Every `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry moved
because the effective config gains the key (inert below the tag); `mvp-0.32`
added. All recomputed from `defaults_fingerprint_for_version`.

**Receipts.** No receipts table and no migration. Claims and attempts are raw
ledgers and the re-anchor is a deterministic function of them at their
stamps, so a rebuild reproduces it; the upgrade's note records which LOs were
replayed and the `derived_state_rebuilds` receipt records the rebuild. (Open
question 3 asks whether a per-claim receipt is wanted.)

## Tests (fail-first)

`tests/test_lp_claim_fixes.py` (24 tests; 3 are the `owner_vaults` lane and
skip by default). Each defect has an `_on` test and an `_off` test
(parametrized `switch_off` and `below_tag`):

- defect 1: `test_defect1_on_a_gap_declaration_reanchors_a_materialized_lo`,
  `test_defect1_on_a_gap_on_a_practised_lo_moves_the_mean_down_and_keeps_the_variance`,
  `test_defect1_off_a_gap_declaration_writes_the_claim_only[...]`;
- defect 2: `test_defect2_on_the_seed_never_reads_a_later_claim`,
  `test_defect2_on_a_claim_after_the_last_attempt_still_reanchors_in_replay`,
  `test_defect2_on_a_claim_between_attempts_reanchors_between_them`,
  `test_defect2_off_replay_seeds_from_the_claims_in_force_now[...]`;
- defect 3: `test_defect3_apply_claim_evidence_mean_only_never_lowers_the_variance`,
  `test_defect3_on_a_warm_reanchor_keeps_the_variance`,
  `test_defect3_off_a_warm_reanchor_shrinks_the_variance[...]`;
- defect 4: `test_defect4_on_the_most_recent_claim_wins_then_pseudo_count_never_level`,
  `test_defect4_off_the_predecessor_prefers_pseudo_count_then_the_higher_level[...]`;
- parity: `test_off_is_the_predecessor_byte_for_byte_live_and_rebuilt` (a
  placement vault with every claim path: live and rebuilt mastery rows equal
  the predecessor's but for the version label),
  `test_off_is_the_predecessor_on_a_tracked_fixture_copy` (backup-API copy of
  `fixtures/mvp017_route_check_replay` with claims added; off equals the
  predecessor, on differs), and
  `test_owner_copies_off_is_the_predecessor_and_on_reports_the_mastery_deltas`
  (owner lane only; prints the per-LO deltas);
- the successor and switch: `test_the_successor_is_one_constant_after_its_predecessor`,
  `test_one_switch_on_by_default_classified_and_gated_by_the_tag`;
- the upgrade: `test_upgrade_from_the_predecessor_replays_claimed_los_and_through_the_chain`.

**Fail-first run.** The `_on` tests were run with the fixes forced off at the
tag (a pytest plugin replacing `claim_fixes_live` with `False` in
`learner.mastery` and `tutor.promotions`, which is exactly the predecessor's
code path): `-k "_on_ or mean_only"` gave **9 failed, 1 passed** (the passing
one is the `mean_only` unit test, which calls the merge with the flag
explicitly; its assertion that the plain merge lowers the variance is the
defect). The 9 failures: the 7 defect `_on` tests, the switch test (patched
predicate) and the tracked-fixture parity test (on equals the predecessor).
With the fixes live: all pass.

**The oracle for replay.** A one-attempt history replays to the live state
exactly, so defect 2's tests compare a rebuild to live on one-attempt
histories. A two-attempt history replays to a slightly different state from
live even with no claim at all (on this placement vault, mean 0.687 live vs
0.560 rebuilt for `lo_svd_definition`; the same on two different items of
`lo_diag`); that is pre-existing and outside claims (open question 4), so the
between-attempts test reads the order of re-anchors and attempts from the
replay itself.

## Shadow rebuild (playbook item 7)

Backup-API copies of the tracked `fixtures/mvp017_route_check_replay` under
the worktree's `fixtures-local/lp-claim-fixes-shadow/` (predecessor, tag with
the switch off, tag on), each with the same three claims added (a global
init-wizard claim at an LO's first attempt, a too-easy report, a later
too-easy report), then a whole-vault `rebuild_all_derived_state`; run under
`env -i` (script kept in the stage's scratchpad, not committed):

```
LOs: 5 off == predecessor: True
lo_transpose: mean 0.8262 -> 1.2364, variance 1.7258 -> 1.3324, evidence 1
moved: 1
```

Only the claimed LO moves. Its variance is lower on because the attempt's
EKF step is taken from a different prior mean (the seed is now the claims
made by the attempt, not the 2099 claim), so the Kalman variance reduction
differs; the later claim's own merge leaves the variance unchanged (fix 3).
The owner copies were not opened (open question 5).

## Gate

Run in the worktree, every pytest inside
`systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`,
`-n 6` at most, one run at a time.

- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken** (after the last change).
- Targeted pytest over the 135 files below: **2,313 passed, 10 skipped,
  1 failed** (`test_architecture.py::test_function_local_domain_imports_match_the_frozen_edge_inventory`:
  replay's function-local `learner.mastery` imports were new edges). Fixed by
  importing the module at top level (replay already depends on
  `learner.mastery` through `attempts`); rerun of `test_architecture.py`,
  `test_lp_claim_fixes.py` and every `test_*replay*.py` / `test_*rebuild*.py`:
  **90 passed, 3 skipped** (the 3 are the owner lane).
- Before that, the latest-successor pin files alone: 623 passed, 6 skipped,
  5 failed (pins still naming mvp-0.31 as the CLI default or missing it from
  a version set); fixed, and the 5 rerun: **5 passed**.
- `--durable-sqlite tests/test_lp_claim_fixes.py`: **21 passed, 3 skipped**.
  No migration and no DB/connection code changed, so no durability lane
  beyond that.
- `db_generate_reference.py` then `db_validate_reference.py`: **0 errors**
  (351 table notes, 1,048 configuration leaves; the prose counts in
  `Configuration.md` and `Database.md` moved 1047 -> 1048). The regeneration
  touches 423 generated files (commit stamps and line citations); the landing
  regenerates on the merged tree.
- CLI help snapshot regenerated (`python -m tests.test_cli_help_snapshot --write`):
  only `upgrade` moves.
- No frontend or `src-tauri` change: no npm, vitest or cargo.

Test files run (targeted):

- `tests/test_ad1_codex_review_fixes.py`
- `tests/test_ad23_fix_r8.py`
- `tests/test_ad23_fix_review.py`
- `tests/test_ad23_owner_decisions.py`
- `tests/test_ad23_successor.py`
- `tests/test_ai_config.py`
- `tests/test_anti_double_count.py`
- `tests/test_approach_map_replay.py`
- `tests/test_architecture.py`
- `tests/test_assumed_known.py`
- `tests/test_attempt_completion.py`
- `tests/test_capability_residual.py`
- `tests/test_causal_activity_policy.py`
- `tests/test_causal_attribution_p0.py`
- `tests/test_causal_attribution_p1.py`
- `tests/test_causal_p2_acceptance.py`
- `tests/test_characterization_mastery_reliability.py`
- `tests/test_characterization_probe_replay.py`
- `tests/test_cli_help_snapshot.py`
- `tests/test_cold_start_revision.py`
- `tests/test_config_refactor.py`
- `tests/test_constraint_engine.py`
- `tests/test_coordinated_migrations.py`
- `tests/test_coverage_denominator_boundary.py`
- `tests/test_daily_plan_replay.py`
- `tests/test_desktop_rpc_contract.py`
- `tests/test_diagnosis_input_provenance.py`
- `tests/test_diagnosis_pipeline.py`
- `tests/test_diagnosis_replay.py`
- `tests/test_diagnostic_probe_single_use.py`
- `tests/test_difficulty_band_guards.py`
- `tests/test_discrimination_profiles.py`
- `tests/test_doctor.py`
- `tests/test_durable_promotion_arms.py`
- `tests/test_evidence_config.py`
- `tests/test_exam_protection_review.py`
- `tests/test_exam_seeding.py`
- `tests/test_facet_diagnostics_v03.py`
- `tests/test_facet_registry_v2.py`
- `tests/test_field_boundaries.py`
- `tests/test_field_priors.py`
- `tests/test_field_workbench_signals.py`
- `tests/test_goal_series.py`
- `tests/test_grading_cli.py`
- `tests/test_graph_correction.py`
- `tests/test_hypothesis_claim_dispatcher.py`
- `tests/test_ingest_instrument_gates.py`
- `tests/test_ingest_runner.py`
- `tests/test_intent_codex_rereview.py`
- `tests/test_intervention_outcomes_replayer.py`
- `tests/test_irt_difficulty.py`
- `tests/test_item_parameters.py`
- `tests/test_kinship_feature.py`
- `tests/test_km2b_consumer_rekey.py`
- `tests/test_km2_write_path.py`
- `tests/test_library_exercises.py`
- `tests/test_lp_claim_fixes.py`
- `tests/test_mastery.py`
- `tests/test_mastery_step_attribution.py`
- `tests/test_measurement_state_labels.py`
- `tests/test_method_explicit_upgrade.py`
- `tests/test_misconception_registry.py`
- `tests/test_misconception_resolution.py`
- `tests/test_mobile_allowlist.py`
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
- `tests/test_open_world_gate.py`
- `tests/test_p0_cutover_mvp08.py`
- `tests/test_plan_determinism_landing.py`
- `tests/test_plan_determinism.py`
- `tests/test_plan_first_transport_offer_grants.py`
- `tests/test_plan_first_transport_offer_grants_r5.py`
- `tests/test_planted_misgrade.py`
- `tests/test_practice_information.py`
- `tests/test_primed_attempts.py`
- `tests/test_probe_orchestration_remainder.py`
- `tests/test_public_tip_guards.py`
- `tests/test_question_promotion_jobs.py`
- `tests/test_question_promotions.py`
- `tests/test_reader_guidance.py`
- `tests/test_reader_recap_review_r2.py`
- `tests/test_reader_recap_review_r3.py`
- `tests/test_reader_rw2b_review.py`
- `tests/test_reading_paths.py`
- `tests/test_reading_step_switch.py`
- `tests/test_rebuild_orchestrator.py`
- `tests/test_recurrence_commands.py`
- `tests/test_reference_gate_imports.py`
- `tests/test_registry_audit.py`
- `tests/test_regrade_contract_replay.py`
- `tests/test_regrade_contract_successor.py`
- `tests/test_regrade_contract_upgrade.py`
- `tests/test_replay.py`
- `tests/test_required_method_grading.py`
- `tests/test_route_rules_in_grader.py`
- `tests/test_rw2c_switch_off.py`
- `tests/test_rw2d_receipts_migration.py`
- `tests/test_sensitivity_certificates.py`
- `tests/test_serve_eligibility_review.py`
- `tests/test_shadow_rebuild.py`
- `tests/test_show.py`
- `tests/test_sidecar_registry.py`
- `tests/test_sidecar_serializer_snapshot.py`
- `tests/test_sidecar_tutor_qa.py`
- `tests/test_source_append.py`
- `tests/test_source_retrieval_tutor.py`
- `tests/test_source_roles.py`
- `tests/test_source_set_synthesis.py`
- `tests/test_state_sync.py`
- `tests/test_structured_transport_parity.py`
- `tests/test_stuck_prompt_replay.py`
- `tests/test_subject_registry.py`
- `tests/test_surprise.py`
- `tests/test_table_roles.py`
- `tests/test_teach_back.py`
- `tests/test_teacher_te0_review_fixes.py`
- `tests/test_tool_registry.py`
- `tests/test_tracked_fixture_databases.py`
- `tests/test_tutor_promotion_service.py`
- `tests/test_tutor_promotion_w2.py`
- `tests/test_ux_phase1_round2_rereview.py`
- `tests/test_ux_phase2_shell.py`
- `tests/test_voi_stopping.py`

## No live calls

No paid or model call was made. Every script outside pytest ran under
`env -i` with an empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` in the
scratchpad. No owner vault, `~/.config/learnloop` or credential file was read.

## Open questions

1. **The cold claim seed's variance** (not one of the four). A claim on a
   zero-evidence LO still seeds variance `max(1/pseudo_count,
   claim_prior_min_variance = 2.0)`, below the 3.0 cold start that AD §5.5
   keeps ("every cell keeps its cold-start variance of 3.0"). Fixing it would
   be a fifth change to the same successor (floor at
   `cold_start_prior_logit_variance`); left as is because the stage is
   "exactly the four".
2. **The warm floor's reading.** "Never lowers a variance below the prior" is
   read as the state's own variance before the claim (the claim's Bayesian
   prior), so a warm claim is mean-only. The other reading, AD's
   `max(current, coordinate prior)`, would raise an evidence-backed variance
   back to 3.0 on every claim, which inflates uncertainty the evidence earned;
   not taken.
3. **Receipts.** None added (see above). If the owner wants each live gap
   re-anchor recorded (before/after mean and variance), it is a small receipt
   table and a migration in the same successor.
4. **Live vs replay on multi-attempt histories** differ without any claim
   (see "The oracle for replay"). Pre-existing; worth a look in the LAST
   architecture stage, since the playbook's rebuild-equivalence compares
   rebuild to rebuild.
5. **Owner-copy deltas** (spec §9's "rebuild-equivalence fixture showing
   owner-copy mastery deltas"): the owner-lane test prints them, but this
   stage may not open the owner's vaults. The landing (or the owner) runs
   `LEARNLOOP_OWNER_VAULTS=<copies> uv run pytest -m owner_vaults tests/test_lp_claim_fixes.py -s`.
6. **Init-wizard edits between sync and the first attempt.** Live, a global
   claim edited after rows exist is inert; replay folds it into the seed when
   it was made before the LO's first attempt (AD's "claims before the first
   eligible observation"). The predecessor's replay used it too (every claim
   in force now), so this is not a new difference.
