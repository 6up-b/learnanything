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

## Landing onto main

Branch `merge/lp-claims-onto-main` in `learnanything-merge2`, cut from `main` at `eae00d58a` (mobile PR-1, the docs
specs, the owner-capture 1025 fixes and RW7b's `mvp-0.32` on top of this stage's base `fa2eb72f8`). Main did not move
during the gate, and it was neither fast-forwarded nor pushed. **The successor is renumbered to `mvp-0.33`, with
predecessor `mvp-0.32` (RW7b). Migration 221 lands on main's head 220. The kill switch is
`mastery.claim_fixes_enabled`.**

### Commits and conflicts

- `7e244fce5`: the `--no-ff` merge of `lp/claim-fixes` (`7def209ca`). The code conflicts were the places where both
  successors append, and every one was composed so that both sides survive:
  - `algorithm_versions.py`: RW7b's constant and version set, then this stage's (`SUCCESSOR_CHAIN` ends
    `... mvp-0.31, mvp-0.32, mvp-0.33`).
  - `cli/app.py`: the `--to` help, the docstring (RW7b's `--to mvp-0.32` paragraph, then `--to mvp-0.33` as the
    default), the dispatch and the unknown-target message.
  - `config/template.py`: every snapshot comment names both keys; `mvp-0.33` is added.
  - Four chain-pin tests: `test_ad23_successor`, `test_field_workbench_signals`, `test_intent_codex_rereview` and
    `test_recurrence_commands`.

  423 generated reference notes and `tests/cli_help_snapshot.json` were taken from main and then regenerated (below).
  `substrate/replay.py`, the parameter registry, `config/schema.py`, `sidecar/context.py` and `remote/runtime.py` merged
  without a textual conflict.
- `dff50db22`: the renumber (below).
- `dc80efaf7`: the head fixture's README. RW7b's `tests/test_plan_follows_path.py` pointed at `migration_head_220`;
  it now points at `migration_head_221`.
- `295bf012c`, `b703549d0`: the regenerated references and the CLI help snapshot.
- `e7653a9cb`: **a semantic conflict with mobile PR-1.** PR-1 rewrote `remote.runtime.check_schema` without its local
  `path`, and the stage's added line `refuse_interrupted_activation(path)` then raised `NameError` on every remote and
  MCP attach. The fail-first tests were the stage's own: `test_f2_attaches_that_never_write_refuse_while_the_journal_stands`
  and `test_f2_an_mcp_server_already_attached_stops_serving_when_a_journal_appears` failed on the merge and pass now.
  The same commit moves RW7b's own pins and the method-explicit pins so that `mvp-0.33` is the latest.
- `f086a95a5`: **the field arms' version hashes.** The stage's new `MasteryConfig` key changed all 19 arm hashes in the
  learner field's evaluation manifest, though no prediction changed. As a result
  `test_eval_harness::test_the_cluster_option_leaves_every_other_report_byte_identical` failed on the merge, 3 runs out
  of 3 when run alone; it passes on main's tree. The offline arms (`LoGeneral`/`MasteryEKF`, the T8 success head) take
  their priors as inputs and never read claims, so their hashes now leave out `claim_fixes_enabled`
  (`field.predictors._mastery_hash_view`). The hashes match main's again, and the pinned digests hold.
- `2aa5550c5`: **the stage's owner-lane test.** `test_owner_copies_off_is_the_predecessor_and_on_reports_the_mastery_deltas`
  failed in all three cases (`append_config_toml`: "learnloop.toml already has [mastery]"; real vaults already have
  that table). The stage never ran it. It now sets the switch inside the existing table, and its 3 cases pass.
- This record (docs only).

Against main, the diff adds the head fixture's rename (`migration_head_220` -> `migration_head_221`; `state.sqlite`
R099), migration 221, two modules, two desktop component files, four test files and the two review records. **No other
database or binary file is added, and the root `.gitignore` is unchanged.**

### Renumber and chain check

- `CLAIM_FIXES_ALGORITHM_VERSION = "mvp-0.33"`. `claim_fixes_upgrade.PREDECESSOR` is
  `READING_PATH_PLAN_ALGORITHM_VERSION` (`mvp-0.32`), and the chained step is `upgrade_to_reading_path_plan`. The
  module docstring, the CLI docstring, the snapshot comment and the constant's comment say that the number changed at
  landing.
- Tests: the chain-tail literals now read `mvp-0.33`, and every version set that ended `"mvp-0.31", "mvp-0.32"` gains
  `"mvp-0.33"`. Every negative `SUCCESSOR_CHAIN[...]` index in the upgrade tests moves by one link. The stage's pin is
  `PREDECESSOR == READING_PATH_PLAN_ALGORITHM_VERSION == "mvp-0.32"` and `TAG == "mvp-0.33"`. RW2d's and RW7b's
  default-target CLI checks now pass `--to` their own tag.
- `learnloop upgrade --to mvp-0.33` on placement vaults (the merge's tree, `env -i`, `fixtures-local/landing-lp/logs/chain.log`):
  - `mvp-0.9`, `mvp-0.27`, `mvp-0.29`, `mvp-0.30`, `mvp-0.31` and `mvp-0.32` each succeed, ending at `mvp-0.33`.
  - From `mvp-0.8` it is refused; `--to mvp-0.9` then `--to mvp-0.33` succeeds.
  - A bare `upgrade` from `mvp-0.32` goes to `mvp-0.33`.

  Result: **ALL OK**.
- Defaults snapshots: after clearing `config/__pycache__/template*.pyc`, all **24** entries were recomputed from
  `defaults_fingerprint_for_version`, with both keys and `mvp-0.33` added. 0 mismatches.

### Head fixture

`fixtures/migration_head_221` is rebuilt as the convention describes. A backup-API copy of main's
`fixtures/migration_head_220/state.sqlite`, which is byte-identical to `fa2eb72f8`'s, had only 221 applied, under
`UPGRADE_SCRATCH_COPY`:
- `wal_checkpoint(TRUNCATE)` gave (0, 0, 0), then `journal_mode=DELETE`; header bytes 1/1;
- `integrity_check` ok, `foreign_key_check` empty, no companion files; schema_migrations holds 208 rows, head 221.

Its `iterdump` equals the branch's fixture except for 221's `applied_at` stamp, so the branch's file is kept and no
second 6.7 MB blob enters history. The other 23 files are byte-identical to main's `migration_head_220`.
`migration_head_220` is removed (the rename). The README records the landing. The five hard-coded paths and the two
`db_*_reference.py` scripts already named 221 on the branch. RW7b's test was the one new path, and it now names 221.
Curriculum C0a (222) rebuilds its head from this one.

### Regeneration

- **References.** On the merge, `db_validate_reference.py` reported 5 errors: the field catalog counts, and the prose
  counts in `Configuration.md` and `Database.md` (1048 against 1049 leaves, because each side added one key).
  `db_generate_reference.py` rewrote 425 notes and 422 were kept. Every Configuration field note's line citations into
  `config/schema.py` moved, as did the table notes' `schema_head` (221). Three table notes now list
  `src/learnloop/claim_fixes_upgrade.py`. The two prose counts are 1,049 by hand. The validator reports **0 errors**,
  and again after the late fixes.
- **CLI help snapshot**: regenerated (`upgrade` only).
- **RPC pins and serializer snapshots**: no change. `test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot`
  and `test_sidecar_registry` pass with no file changed.
- **`validate_vault.py`**: passes (1,155 notes, 1,153/1,153 reachable).

### Gate

Setup ran in 5G scopes, with the merge2 venv as RW7b's landing left it (no dependency change). The pytest lanes ran
under `flock /tmp/learnloop-fullsuite.lock` in 10G / 2G swap scopes. Every Python run used `env -i` with empty `HOME`,
`CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, and all three directories existed beforehand. Logs are in
`fixtures-local/landing-lp/logs/`.

| Step | Result |
|---|---|
| `lint-imports --no-cache` | **36 kept**, 0 broken |
| full suite 1 (`pytest -n 8`, at `e7653a9cb`, 56 min) | 21,522 passed, 4 failed, 80 skipped, 38 xfailed. The two `test_mcp_c1a_narrow` cases (the known MCP `8841` random-id flake), `test_reading_hardening_2_fixes::test_f1_a_failed_check_for_queued_work_is_retried_by_the_sweep` (known load flake), each **3/3 passed** alone; `test_eval_harness` **0/3** alone: real, fixed in `f086a95a5` |
| full suite 2 (`pytest -n 8`, at `f086a95a5`, 58 min) | 21,525 passed, **1 failed**, 80 skipped, 38 xfailed. The failure was `test_reading_hardening_2_fixes::test_f1_a_build_whose_worker_failed_to_start_is_run_by_the_sweep`, a known load flake, which passed **3/3** alone |
| targeted re-runs after the fixes | the field package's 43 test files and `test_architecture`: 1,520 passed, 3 skipped. `test_lp_claim_fixes`: 21 passed, 3 skipped (the owner lane) |
| durability (`-m durability`) | **125 passed**, 1 skipped |
| owner lane (`-m owner_vaults`, `LEARNLOOP_OWNER_VAULTS` = backup-API copies of the three mvp030 backups in `fixtures-local/owner-lane-lp/`) | 80 passed, 9 failed. 3 were the stage's own test (the `[mastery]` table, fixed in `2aa5550c5`; then **3 passed**). The other 6 match RW7b's landing exactly, and predate this stage: 4 need the retired early vaults, plus `test_activity_backfill` and `test_placement_fixture_copies[arxiv_v2]` |
| `npm install`; `npm run typecheck` | ok; clean |
| `npm test -- --maxWorkers=4` (whole vitest) | **214 files, 1,834 tests passed** |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path src-tauri/Cargo.toml` | finished |
| worktree, tracked fixtures | `git status` clean apart from `fixtures-local/` |

### Parity (backup-API copies; no real model call)

**Setup** (`fixtures-local/landing-lp/scripts/`, RW7b's landing scripts re-pathed, plus new ones):
- `orig/` holds backup-API copies of `learnanything/fixtures-local/vault-backups-20261025-mvp030/{linear_algebra,probability}`.
- `u32/` is `orig` brought to **mvp-0.32 with main's code**: routes neutralized to a `127.0.0.1:9` blackhole,
  `upgrade --to mvp-0.32`, then `rebuild-derived-state` twice.
- `code_main` and `code_merge` are `git archive` exports of `eae00d58a` and of the merge (`e7653a9cb`; the later
  commits change only offline field hashes and tests).
- `run.py`'s audit hook refuses any Codex process start and any non-loopback socket.
- The frozen clock is 2026-10-19 09:00 UTC, with deterministic ids.

**(a) Main vs merge at mvp-0.32** (`a32.sh`; a second main copy is the noise control).
- Whole databases after the normal primary sidecar load (the merge applies 221 there):
  - The schema is identical except `learner_claims.applied_after_attempts` (all NULL) and the one extra
    `schema_migrations` row (221). The common rows are identical.
  - **Every row of 356 tables is identical**: 18,303 rows on linear_algebra and 8,210 on probability.
  - Integrity ok, `foreign_key_check` 0, `model_call_receipts` 0 on both sides.
- `rebuild --shadow` and `doctor`: **0 differences** main vs merge. The shadow's 30 schedule differences on
  linear_algebra, and doctor's 57 / 1 error and 101 / 48 errors, are the same on both sides and predate the stage.
- Certification, curves, Today and the plan: **byte-identical** main vs merge, and main vs main, on both vaults.

**(b) `upgrade --to mvp-0.33` and the chain** (`b33.sh`, the merge's code).
- On `u32` copies the result is rc 0, "mvp-0.32 -> mvp-0.33". The notes name the LOs.
  - linear_algebra: **8 LOs with attempts replayed** (every LO with attempts; the init wizard's global claim covers
    them all) and **13 attempt-free LOs re-seeded**.
  - probability: 1 replayed and 17 re-seeded.
- A bare `upgrade` gives the same result. Straight from the mvp-0.30 backup, `--to mvp-0.33` chains through RW2d's and
  RW7b's steps; the owner's three steps (`--to mvp-0.31`, `--to mvp-0.32`, `--to mvp-0.33`) also succeed.
- Rows:
  - Every `learner_claims` and `practice_attempts` row is kept.
  - What differs is the DERIVED state the replay rewrites (mastery, transitions, surprise, facet state, outcome
    labels, item quality), the FTS shadow pages (repacked), and the refreshed `parameter_registry`.
  - The two ledgers that replay rewrites when mastery moves also differ: `attempt_debug_payloads`, whose
    `algorithm_version` stamp and posterior change, and `error_events`, whose `severity` changes (16 of 19 rows; 1 of
    2). Every rebuild under a different mastery does the same.
  - The usual receipts are added.
- `rebuild --shadow` straight after the upgrade gives **0 / 0 / 0** on both vaults (the activation is exactly what a
  rebuild writes). Two `rebuild-derived-state` runs leave mastery unchanged (0 LOs move), and the shadow stays
  0 / 0 / 0. Doctor is unchanged.
- **Mastery deltas** (mean, variance; the owner-lane test on copies, `-s`, agrees with the upgrade):
  - **linear_algebra, 21 of 21 LOs move.**
    - The 13 attempt-free LOs keep their mean, and their variance goes 2.0 -> 3.0 (review F4's seed floor at the
      cold-start variance).
    - The 8 practised LOs, mean / variance: `lo_orient_to_the_vector_space_idea` -0.565 / +0.096,
      `lo_coordinates_require_a_basis` -0.326 / +0.363, `lo_compute_with_complex_numbers` -0.196 / +0.229,
      `lo_from_linear_combinations_to_a_basis` -0.101 / +0.531, `lo_operations_and_the_vector_space_axiom_checklist`
      +0.092 / +0.585, `lo_prove_vector_identities_from_scalar_laws` -0.007 / +0.320,
      `lo_read_and_apply_the_vector_space_definition` -0.002 / +0.455, `lo_what_makes_a_vector_space` +0.004 / +0.385.
  - **probability, 18 of 18 move.** 17 attempt-free LOs go 2.0 -> 3.0, and
    `lo_analyze_and_optimize_nonuniform_collision_probab` moves +0.047 / +0.580.
  - **arxiv_v2 (owner lane only), 3 of 34 move**, by variance (+0.91 to +1.0), with one mean change of +0.003.

  So no estimate becomes more certain. Means move only where the claim timing changed the attempt's prior.
  Certification is unchanged on both vaults (below).

**(c) The kill switch at mvp-0.33** (`c33.sh`). Two variants were compared with `base32` (the mvp-0.32 copy opened by
the merge):
- `k33`: `claim_fixes_enabled = false` set before the upgrade, then the upgrade and two rebuilds;
- `kr33`: upgraded with the switch on, then switched off and rebuilt once.

Results, on both vaults:
- **mastery rows identical** apart from the version label;
- **certification identical** apart from the label;
- **Today byte-identical**;
- the plan (every served read and step, every plan row) identical apart from the label and the router card's three
  hashes (`card_hash`, `snapshot_hash`, `content_hash`). Those hash the card, which carries the label; the card's
  content is identical once the label is masked.
- The shadow summaries equal `base32`'s.

So off is the predecessor exactly, label aside, and a rebuild after turning it off restores the predecessor's mastery.
With the defaults (`d33`), mastery moves as in (b). Today's priorities shift slightly (for example the first item's
predicted correctness goes 0.6756 -> 0.6762), and the plan's review load goes 23.95 -> 23.75 per day. Certification is
unchanged.

**(d) The activation journal** (`d33.sh` and `d_extra.log`). On copies of `u32`, the upgrade was killed with
`os._exit(17)` right after it published the config. That leaves the successor's label, the predecessor's mastery
(0 LOs moved) and the journal. From there:
- the next `learnloop upgrade --to mvp-0.33` reports "completed the interrupted activation of mvp-0.33" and removes the
  journal, and its mastery equals the clean upgrade's (0 LOs differ). A second run reports "vault is already mvp-0.33";
- the desktop start (`SidecarContext.load`) completes it the same way (0 LOs differ);
- the next writing CLI command (`backfill-originals`) completes it (0 LOs differ, on both vaults);
- the attaches that may not complete it all refuse, naming `learnloop upgrade --to mvp-0.33`:
  - `InterruptedActivation` from a script's `Repository` and `open_vault_repository`, and from PR-1's
    `SidecarContext.load_secondary`;
  - `SchemaMismatch` from `remote.runtime.check_schema` (the MCP server and the phone host);
  - plain `doctor`, which raises `InterruptedActivation` with a traceback.

  The vault is unchanged by the refusals.
- `placement status` and `plan show` still answer from the uncompleted vault (the open Low F2 below).

**Receipts and calls.** Over all 42 databases under `fixtures-local/landing-lp/`, `model_call_receipts` has **no rows
at all**. `run.py`'s audit log was never created, so no process start or socket connection happened in any parity run.
Spend: $0. No vault or file under `~/learnloop-vaults` was opened (one stray `ls` of the directory, with its output discarded, was the only access).

### Owner notes: what changes for the learner

- **Upgrade**: back up, close the app, the MCP server and the phone page, then run `learnloop upgrade --to mvp-0.33`
  (or plain `learnloop upgrade`) on each vault. From an older vault the same command chains (`mvp-0.9` onwards; from
  `mvp-0.8`, run `--to mvp-0.9` first). Migration 221 adds one empty column. Claims and attempts are never rewritten.
  If the upgrade is interrupted, the next desktop start or `learnloop upgrade --to mvp-0.33` finishes it. Until then,
  the MCP server, the phone page and read-only reports refuse the vault and name that command.
- **What you see**:
  - A gap you declare to the tutor ("I don't know this") and a too-easy/too-hard report now move that topic's estimate
    when you make them.
  - A claim about your level never makes an estimate you have practised look more certain. Topics you have not
    practised start from the full cold-start uncertainty (3.0), even when a claim set their level.
  - When you have made several claims, the most recent one counts.
  - A rebuild applies each claim at the time you made it, so it reproduces what you saw live.

  On these copies, topics you have practised shift by up to about half a logit, and every estimate's uncertainty grows.
  Nothing is certified or uncertified by the change.
- **Kill switch**: `[mastery] claim_fixes_enabled = false` in `learnloop.toml`. It acts immediately for new claims, and
  after `learnloop rebuild-derived-state` it restores the predecessor's estimates.

### Open items

- **Recorded Lows (orchestrator ruling, non-blocking):**
  - **F2**: the raw read-only reports `placement status` and `plan show` skip the journal check after an interrupted
    upgrade. Confirmed in (d). Plain `doctor` refuses, but with a traceback rather than a one-line message.
  - **F7**: two concurrent claims with the same attempt count replay in creation order.
  - **F8**: a replacement claim made after a pseudo-count config change loses the earlier variance history.
- **The fifth fix** (the cold claim seed's variance, 2.0 against AD's 3.0) is queued as a follow-up. Note for that
  stage: review F4 already floors a claim seed at `cold_start_prior_logit_variance` (3.0) under the tag, and that is
  the 2.0 -> 3.0 visible in (b). Whatever remains of the follow-up should be restated against F4.
- **Live vs replay on multi-attempt histories**: the separate `fix/rebuild-equivalence` stage lands after this one.
- The stage's other open questions stay at their defaults: the warm floor is the state's own variance (mean-only); no
  per-claim receipt table.
- Observation (Low): the live placement predictor's `version_hash` (`placement/predictor.py`), which AD forecast
  receipts and placement decisions record, hashes the whole `[mastery]` table. New such receipts therefore carry a
  different `predictor_version` from main's, even below the tag, because the key exists. No existing row changes
  ((a) is row-identical).
- `migrations/221_learner_claim_application_point.sql` still says RW7b "may take the same number". RW7b added no
  migration, and the comment was left as is so the applied migration's text does not change.
- The owner lane's 6 pre-existing failures (missing early vaults, data assumptions) fail the same way on RW7b's landing.
