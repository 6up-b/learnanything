# Refactor arc D bug fixes, part 1: the facet-belief successor

Ledger rows D-1, D-3, D-4, D-5 and D-6 (`docs/reviews/refactor-bug-ledger.md`), on branch `refactor/d-facet-belief-successor`, based on `16a9e3fd48` (main `e9a7733612` plus K3.5 and D2b part 1, treated as landed). The successor follows `docs/algorithm-change-playbook.md`.

## 0. Step 0: bug or design, row by row

Written before any code change. Each verdict reads the code at the base and the commits and specs that introduced it.

### D-1: a success never resets `consecutive_failures`: **bug**

- Code: `substrate/canonical_projection.py`, `project_canonical_facet_state`. The reset `acc.consecutive_failures = 0` sits in the failure-mass loop, after `if negative_fraction <= 0 or unresolved_negative or unverified_failure: continue`. A full-marks criterion (`fraction == 1`) has `negative_fraction == 0` and never reaches it; a partial success at or above `FAILURE_THRESHOLD` does reach it and resets. So the streak survives exactly the strongest success.
- History: KM2's projection (`408ce91e03`, 2026-07-13) booked success and failure in one loop per allocation, with `if fraction < FAILURE_THRESHOLD: ... += 1 else: ... = 0`, so every success reset the streak. `a29853775f` (2026-07-14, "Hypothesis surfaces") split the loop so failure mass follows the attribution distribution (KM spec §5.4) and moved the streak into the failure branch only. Its message says nothing about the streak: a side effect of the split, not a decision.
- Consumers rely on the reset: `diagnosis/followups.current_same_facet_failure_streak`'s docstring says the facet state "already resets `consecutive_failures` to zero on success"; the follow-up gate's `repeated_facet_failure` and `_open_reason`'s `repeated_facet_failure` read it.

### D-3: `teach_back.transfer_evidence_multiplier` doesn't reach the canonical belief: **bug**

- Code: the multiplier is read in one place, `attempts.py` → `recall_coverage.scale_coverage_for_graded_criteria`, which scales `covered_facets`. That feeds the legacy per-LO facet rows (written only below mvp-0.7) and the attempt's in-memory traces; the canonical projection computes each criterion's mass as `criterion_pseudo_mass(points, rubric_total, emass)` and never reads the criterion's tier. The assessment contract carries the tier (`assessment_contracts.py`: `"tier"` in the frozen contract and `rubric_from_contract`), so the information is on record.
- History: the multiplier predates KM2 (`b0b0834ba8`, 2026-07-06, teach-back). KM2 (`408ce91e03`) and KM2b (`e603b9e295`) re-keyed belief without carrying it over, and no spec, ADR or commit retires it: `config/schema.py`'s `TeachBackConfig` still documents it as "the symmetric evidence-mass multiplier applied to facet evidence contributed by transfer-tier rubric criteria … read from config at apply time so replay reproduces it", the generated config note lists it ACTIVE, and `spec_learned_parameters_v1.md` lists it among the parameters to learn. The KM spec's "transfer belief lives in the diagnostic layer" (§4.3) is about context-family transfer, not the teach-back rubric tier.

### D-4: a targeted error attribution's facet outcome doesn't reach the canonical belief: **design (KM2)**

- Code: the attempt's `facet_outcomes` (`recall_coverage.derive_facet_outcomes`) does mark `numeric` 0.0 from the attribution, but the canonical projection reads criterion observations only. `canonical_projection.attribution_weights` keeps only entries whose `(facet, capability)` is one of the failed criterion's own targets (`if key not in allowed: continue`), and only a failed criterion has failure mass to distribute. In the test, the one criterion maps to `concept` only and scores full marks, so `numeric` has no observation.
- Specs: KM spec §18 resolved decision 3, "Grader attribution alone never mints a new target"; §2 principle 2, "One criterion outcome → one stable observation id → one attached inference factor"; §5.4, "Failure mass follows the criterion's attribution distribution (§5.1) instead of role weights" (over the criterion's candidate targets, §5.1); `grading.enforce_passed_target_firewall` strips negative targets protected by passed criteria at the write boundary. The behaviour is the specified one.
- Kept as a test of the designed behaviour (§4), with an owner recommendation (§6). After D-5's fix the attribution does reach the diagnostic layer: the facet's uncertainty row opens on it.

### D-5: `facet_uncertainty_states_for_lo` returns `[]` on canonical vaults: **bug**

- Code: `learner/facet_state_reader.facet_uncertainty_states_for_lo` returns `[]` for every canonical-state version; `attempts._persist_attempt_application` drops the uncertainty updates it computes (`write_legacy_facet_state=False`), and `repositories._guard_legacy_facet_write` refuses them. Every reader of facet uncertainty is dead at the head: the follow-up slate's facet-EIG and predictive-EIG ranking and its overlap gate (`select_followup`'s `gate_applies`), `_demonstrated_facets`, the follow-up decision features' hypothesis prior, goal projection's and the goal frontier's `known_gap`/`uncertain` labels, `mastery_diagnostic_view`, the teach-back planner's uncertain-core ordering and the tutor's question signal. The updates themselves are still computed every attempt, from a prior that is always empty, so every trace shows a fresh `open` state.
- History: KM2b (`e603b9e295`) retired the per-LO write and said "the facet-only re-key is a named KM4 seam, so the four readers get the conservative empty read". The KM spec §7.1 says `facet_uncertainty` "re-keys to `facet_id` only"; KM4 (taxonomy and misconception composition) shipped without it. A deferred step that never landed, not a decision to drop the diagnostic layer: the spec keeps it (§4.3, "transfer belief therefore lives in the diagnostic layer"), and every consumer above was left in place.
- The fix's keying (decided here, see §2): per learning object on canonical facet ids, the table's existing grain, not the spec's facet-only key. Replay is per learning object (`substrate/replay.rebuild_derived_state`, one LO's attempts in order) and the uncertainty update is sequential (each posterior is the next attempt's prior). A facet-only row shared by two LOs would be folded LO by LO on rebuild and chronologically live, so a rebuild would not reproduce live state. The hypothesis set is also LO-scoped (`_initial_hypothesis_marginal` adds misconception labels by the LO's concept). Recommendation in §6.

### D-6: canonical failure observations carry no coverage mass: **bug**

- Code: `independent_evidence_mass`, `raw_coverage_mass` and the surface group are booked only in the success-mass loop, after `if positive <= 0: continue`. A total failure (`fraction == 0`) books beta mass in the failure loop but no coverage; a partial failure books full coverage. A facet the learner failed outright reads as unmeasured: `min_facet_evidence_mass` labels, the coverage variance floor and the measured cells of the denominator all skip it.
- History: KM2 (`408ce91e03`) booked `independent_mass += w` and `raw_mass += alloc.pseudo_mass` for every observation, success or failure; the spec's normative text says "the first observation from a surface/correlation group can add independent mass" (`documentation.md` §11.2), not the first success. The same loop split as D-1 (`a29853775f`) moved coverage into the success branch, unmentioned. The legacy path (mvp-0.6) books coverage on a don't-know (D2a's pinned `test_dont_know_keeps_full_coverage…` asserts mass 1.0 there).
- The fix follows the split's own rule: a total failure books coverage where its failure mass lands, on the attributed targets at the attributed share (`pmass × share`, independent only in a new surface group), the cells whose surface group the failure loop already marks. An unresolved failure (several candidates, no attribution) books none, as its beta mass is none ("unresolved attributions produce an unresolved cause factor, never marginal mass", KM spec §5.4), and a PF-c unverified shortfall books none. The facet evidence timeline needs no change for this: it mirrors certification credit and group marks, and neither moves.

## 1. The successor

| | |
|---|---|
| Tag | `mvp-0.59`, the one constant `FACET_BELIEF_FIX_ALGORITHM_VERSION`, appended to `SUCCESSOR_CHAIN` after the figure wait estimate's `mvp-0.58`; gate set `FACET_BELIEF_FIX_VERSIONS`; new vaults start there |
| Kill switch | `[facet_diagnostic] canonical_belief_fixes` (default true; classified structural/operational in `params/parameter_registry.py`). Off, or below the tag, every fix is off and the belief and the (empty) uncertainty reads are `mvp-0.58`'s exactly (`test_facet_belief_successor::test_with_the_switch_off_the_belief_is_the_predecessors_exactly`, plus a switch-off twin beside each fail-first test). One predicate, `learner.facet_state_reader.facet_belief_fixes_on` |
| Upgrade link | `learnloop.facet_belief_upgrade.upgrade_to_facet_belief`, the newest link's (`figure_wait_upgrade`) pattern: journalled, predecessor or `mvp-0.9` onward through the chain, refusal of anything older, `complete_interrupted_activation` installed by the CLI and sidecar openers and handing earlier journals to `figure_wait_upgrade`. Its activation is a whole-vault rebuild under the tag in one `BEGIN IMMEDIATE` transaction with the config's publication last (RO1's and rebuild equivalence's shape, because per-attempt state derived from the belief and the uncertainty rows move); completion is read from that rebuild's receipt (`has_whole_vault_rebuild`). `learnloop upgrade` targets it by default; `--to mvp-0.59` names it |
| Projection-switch record | a rebuild receipt at the tag records `facet_diagnostic.canonical_belief_fixes` in `projection_switches_json` (below the tag the record keeps its one predecessor key, byte for byte); `doctor`'s `sql:projection_switches_stale` warns when the config moved since the last whole-vault rebuild (the playbook's RO1 rule: a switch that changes a projection's derivation is a projection change) |
| Table roles | `facet_uncertainty` COMPAT → DERIVED, owned by the `learning_state` replayer (it already reset it per LO); the shadow rebuild diffs it as a `facet` projection. No migration |
| `CANONICAL_PROJECTION_VERSION` | unchanged (`v8`): the fixes are gated by the tag, whose change already makes a recalibration boundary (`derived_state_rebuild_version_changes` reads the algorithm version as well) |

What each fix does in code:

- **D-1** (`substrate/canonical_projection.py`): in the success-mass loop, `fraction >= FAILURE_THRESHOLD` sets `consecutive_failures = 0` on the cell's aggregate and item rows.
- **D-3**: `_HistoricalCriterion` carries the contract's frozen `tier` (the legacy-rubric path reads the rubric's); a transfer-tier criterion's `pmass` is multiplied by `transfer_tier_mass_scale(config, "transfer")` (`teach_back.transfer_evidence_multiplier`, clamped, read at projection time as the repeat-surface discount is). `learner/facet_evidence_timeline` applies the same scale, so the Demonstrated curve still equals banked credit (`test_the_demonstrated_curve_banks_what_the_belief_banks`, both switch states).
- **D-6**: in the failure-mass loop, a total failure (`fraction <= 0`) adds `pmass × share × discount` independent mass (new surface group only) and `pmass × share` raw mass to each attributed target. Unresolved and PF-c unverified failures book none; surface-group marks are unchanged, so the timeline needs nothing.
- **D-5**: `attempts._persist_attempt_application` writes the computed uncertainty updates on a canonical vault at the tag (`write_facet_uncertainty`), each re-keyed to the canonical facet id (`facet_state_reader.canonical_uncertainty_rows`, aliases then merges, a deterministic id for a re-keyed row); `repositories._guard_legacy_facet_write` admits uncertainty rows tagged with the successor (the per-LO recall bridge stays refused); the attempt's prior is read under the canonical id and only from a row the successor wrote (`current_facet_uncertainty`: a legacy-era row never counts); `facet_uncertainty_states_for_lo` returns the successor's rows, merges resolved, the repository's order kept. Readers that query the table directly (`instructional/valuation`, `instructional/reader_followups`, `tutor/promotions`) now see rows on a canonical vault at the tag, by canonical id.

## 2. Fail-first evidence

Before (base `16a9e3fd48`, `--runxfail`): `test_success_resets_repeat_failure_gate_and_coverage_is_not_failed` (`repeated_facet_failure` 2.0, expected 0.0), `test_transfer_tier_evidence_mass_is_discounted_symmetrically` (transfer mass 0.278, expected 0.139), `test_deferred_regrade_replays_targeted_error_attribution_facets` (no `numeric` state: D-4, by design). After, at the tag: the first two pass with their `xfail` markers removed; the third is rewritten to assert the designed behaviour (§0, D-4) and passes.

The facet-uncertainty pins, ported from `pin_old_basic_vault` to the head vault, run once with the fixes forced off (a scratch plugin patching `facet_belief_fixes_on`, not tracked) and once on:

| test | fixes off | fixes on |
|---|---|---|
| test_recall_coverage_interventions::test_success_resets_repeat_failure_gate_and_coverage_is_not_failed | fail | pass |
| test_recall_coverage_interventions::test_dont_know_books_canonical_coverage_where_its_failure_mass_lands (new, D-6) | fail | pass |
| test_teach_back::test_transfer_tier_evidence_mass_is_discounted_symmetrically | fail | pass |
| test_goal_projection::test_known_gap_facet_is_never_on_track (also re-seeded through `seed_canonical_facet_recall`) | fail | pass |
| test_facet_diagnostics_v03:: subthreshold_noisy_item…, single_facet_probe… (VOI minutes seam), open_facet_restriction…, hedged_learner_confidence…, facet_uncertainty_rebuilds…, mastery_diagnostic_view… (6) | fail | pass |
| test_predictive_eig::test_followup_slate_logs_predictive_fields_and_ranking_unchanged_at_weight_zero (VOI minutes seam) | fail | pass |
| test_deferred_regrade::test_deferred_regrade_replays_targeted_error_attribution_facets (D-4's designed behaviour) | fail | pass |
| test_teach_back::test_plan_orders_uncertain_core_first_then_escalates, ::test_plan_reserves_final_slot_for_transfer_when_core_would_crowd_it_out; test_goal_frontier::test_known_gap_and_uncertain_facets_are_both_on_frontier | pass | pass |
| test_recall_coverage_interventions::test_high_unfamiliar_probe_posterior_records_intervention_need | pass | pass |

The three in the second-to-last row now run on the head but don't discriminate the switch (the planner's order and the frontier come out the same from "unexamined" as from "uncertain" in their fixtures); recorded, not strengthened here. The last one was misattributed by D2a and D2b: it reads the opening probe episode's unfamiliar posterior, not facet uncertainty, and is ported with `placement.initial_probes` (D2a's group C convention). The predecessor-exact switch-off twins: `test_with_the_belief_fixes_off_a_success_keeps_the_facet_streak`, `test_dont_know_books_no_canonical_coverage_with_the_belief_fixes_off`, `test_with_the_belief_fixes_off_transfer_tier_mass_is_a_core_criterions`, and the successor file's whole-belief equality against an `mvp-0.58` vault.

Pins still on the old vault after this step: 33, D2b's 45 less the 12 facet-uncertainty readers ported here. D2b's two "legacy per-LO facet masses" pins stay: `test_dont_know_keeps_full_coverage…` is the legacy path's own test (its head counterpart is new, above), and the doctor's alias merge is mvp-0.6's.

## 3. Identity and goldens

- `tests/goldens/effective_defaults.toml`: `algorithms.algorithm_version = "mvp-0.59"` and the new line `facet_diagnostic.canonical_belief_fixes = true`.
- `tests/goldens/identities.toml`, regenerated with `--write`, deliberately: four pins moved, `A1-A4.manifest_hash.init`, `C3.boundary.init`, `C5.init`, `C6.init`. Each takes the `init` template's config, which names the new tag. Proof that the tag alone moves them: with the template's tag set back to `mvp-0.58` (a scratch plugin) all 204 pins hold, and no `.legacy` pin moved, so the new config field moves none. A completed bootstrap synthesis and the router's prefetch and draw identities on a new vault differ by tag, as at every successor.
- `tests/test_retired_config_identities.py`: the new default joins `ADDED_SINCE_BASE` (arc C's whole-config digests hold deletions to their base; a new default is not a deletion).
- Earlier links' version pins (`LATEST == "mvp-0.58"`, version sets, `SUCCESSOR_CHAIN` negative indices and slices), the opener assertions and the CLI surface's `--to` default moved by mechanical exact-pattern scripts (scratch, not tracked), as the `mvp-0.58` landing did.

## 4. Shadow rebuild (playbook item 7)

Fresh backup-API copies (`learnloop.db.copies.copy_tree_with_databases`) of `~/learnloop-backups/20261109-copy` (three vaults, all at `mvp-0.54`) under the worktree's gitignored `fixtures-local/dfb/`, with the final code (`a733b7d021`): upgraded to `mvp-0.58` and rebuilt there as the baseline; `shadow_rebuild` at `mvp-0.58` (all three: 0 mastery, facet and schedule changes, copy unchanged, i.e. replay reproduces live state) and at `mvp-0.59` (copy unchanged); then `upgrade_to_facet_belief` and a row-by-row comparison. Numbers in `fixtures-local/dfb/deltas.md` (gitignored, counts only); the copies are deleted. Orders of magnitude:

| | probability (3 attempts) | linear_algebra (70) | arxiv_v2 (21) |
|---|---|---|---|
| aggregate facet cells whose mean moved | 1 of 1 (|Δ| ~5e-3) | 4 of 29 (|Δ| ~3e-2) | 2 of 11 (|Δ| ~2e-2) |
| cells whose independent mass moved | 0 | 3 (each −0.17, transfer tier) | 6 (+0.2 to +0.35, total 0.9 → 2.2) |
| failed-but-unmeasured cells (D-6) | 0 → 0 | 0 → 0 | 6 → 0 |
| certification credit total | 0.12 → 0.10 | 17.2 → 16.6 | unchanged (0.37) |
| cells with a failure streak (D-1) | 0 → 0 | 0 → 0 | 8 → 8 (each cell's latest observation is a failure) |
| LO mastery means moved | 1 of 18 (~1e-6) | 3 of 21 (up to 4e-2 logit) | 0 of 36 |
| facet uncertainty rows (D-5) | 0 → 1 | 0 → 4 (3 LOs) | 0 → 4 (3 LOs) |
| item and card due dates moved | 0 | 0 | 0 |

The shadow's own "changed" counts (every mastery row, most facet rows) include each row's `algorithm_version` label; the comparison above leaves the label out. No schedule moves on any copy: the fixes reach FSRS only through what an attempt reads of facet state, and none of these histories crossed a threshold.

## 5. Gates

- Targeted tests: `scripts/affected_tests.py` names the whole suite for this diff (`db/repositories.py`, which conftest imports, and `pyproject.toml`); without those two it names 1,332 of 1,405 test files. Those 1,332 ran in 14 chunks of 100 files, `-n 4 -m "not arc_close"`, each behind `flock /tmp/learnloop-fullsuite.lock` in a 5 GB scope with the empty-home wrapper: **28,995 passed, 102 skipped, 13 xfailed, 2 failed**. Both failures were stale version pins of this step's own making (`test_attempt_content_state_successor`'s two-bound chain slice, `test_lp_claim_fixes`' set ending in `LATEST_ALGORITHM_VERSION`), fixed with their siblings in `a733b7d021` and `c860e59baf`; every test file changed after its chunk ran (13 files) reran: 247 passed, 6 skipped, 1 xfailed.
- `tests/test_identity_pins.py` (four `.init` pins regenerated, §3), `test_retired_config_identities`, `test_architecture`, `test_test_layout`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, the successor file: 311 passed on the tip.
- `ruff check`: clean. `lint-imports --no-cache`: 42 kept, 0 broken (a first draft's `router_objective_switches -> learner` import made a cycle; the switch is read directly there). `scripts/check_gate_partition.py`: 31,009 collected, landing 30,949 + arc_close 60.
- Vault: references regenerated after the source commits (`9eeb40feba`, 131 notes), the DB validator's legacy-table set and the reference prose's leaf count (1182) updated (`bec8b943e0`), `_generated.md` re-recorded (`2e8eb3148c`, and `e1d3e594de` after the last test commit); a further run on the clean tree changed nothing (fixed point). `db_validate_reference.py`, `module_validate.py`, `desktop_validate.py` (with its reproducibility check) and `validate_vault.py` pass.
- Not run (the orchestrator's): the full landing selection, the durability lane, `--fresh-connections`, the arc-close gate, vitest.

## 6. Recommendations for the owner

**D-4 (targeted attribution and belief): keep the design.** KM2 folds belief from criterion observations only, and a grader's attribution only redistributes a failed criterion's mass among that criterion's own targets (KM spec §18 decision 3; §5.4). Letting an attribution mint belief on a facet no criterion targets would let a model's diagnosis move certification-grade state on a facet the item never measured, the error the "evidence, not mastery" principle and the passed-target firewall exist to stop. With D-5 fixed, the attribution already does what it should: the attempt's `facet_outcomes` records the facet at 0.0, its uncertainty row opens (`low_facet_outcome`), and the follow-up ranking, goal labels and diagnostic view see a facet to probe. If a facet like `numeric` should be measured, the item's rubric should name it as a criterion target (an authoring fix, which the KM2 contract then counts). Recommended: close D-4 as by design.

**D-5's keying (per LO, not the KM spec's facet-only key).** The spec (§7.1) said `facet_uncertainty` re-keys to the facet alone. Two things in the code argue against doing that now: replay is per learning object (`rebuild_derived_state` replays one LO's attempts in order), and the uncertainty update is sequential (each attempt's prior is the previous posterior), so a facet-only row shared by two LOs would fold LO by LO on rebuild and chronologically live, breaking rebuild equivalence; and the hypothesis set is LO-scoped (misconception labels come from error types related to the LO's concept). Recommended: keep per-LO uncertainty as the diagnostic layer (as built here) and drop the facet-only re-key from the spec, or take it up with a whole-ledger fold like the belief's if a cross-LO diagnostic posterior is wanted.

## 7. Owner steps

Upgrade each live vault to `mvp-0.59` (`learnloop upgrade --vault <path>`; its activation is a whole-vault rebuild, so run `learnloop rebuild --shadow --set algorithms.algorithm_version=mvp-0.59 --json` on a copy first if you want the report), then restart the desktop app and the phone host.

## 8. Ledger

D-1, D-3, D-5, D-6: fixed (`0dda03e99a`; D-5's canonical keying `a733b7d021`). D-4: owner, with the recommendation above (by design). No new row: the one defect found along the way (the uncertainty rows keyed by the item's facet id rather than the merge survivor) was in this step's own change and is fixed in `a733b7d021` before landing.

## 9. Open items and unverified

- The three ported pins that don't discriminate the switch (§2) could get fixtures where "uncertain" and "unexamined" order differently.
- 33 tests remain on `pin_old_basic_vault` (D2b's list less this step's ports), waiting on D3/D1 as D2b records.
- Unverified: whether the owner vaults hold facet merges that the canonical keying (`a733b7d021`) changes (the shadow before and after that commit gave identical numbers, so none of the copies' rows moved key); the desktop and phone surfaces that render facet uncertainty (no GUI was launched).
