# Router objective RO4: Codex review fixes (`router/ro4-objective`)

Review job `20261105-044310-mIr8Nh` (gpt-6.1-sol), on the stage record `docs/reviews/router-ro4.md` at `220bb12fda`.
Every finding was reproduced first: each has a test that fails on the pre-fix source (checked by putting the
pre-fix files back in place, running the new tests, then restoring the fixed files) and passes after the fix.
Fakes only. No paid or real model call was made, no owner vault was opened, and no tracked working vault was touched.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | A slow LLM suppresses an already-computed numeric answer | fixed | `96ba40f55c` | `test_ro4_codex_review.py::test_f1_the_numeric_answer_is_published_before_any_wait_on_the_llm`, `::test_f1_a_slow_llm_leaves_the_numeric_share_in_place` (pre-fix: `failed == ["llm", "numeric"]` behind a gated LLM) |
| F2 | High | Probe repair selection uses the repair's future result | fixed | `cdd676b936` | `test_ro4_value.py::test_f2_the_probe_branch_never_sees_the_repairs_future_result` (flipping every outcome, duration and tail draw after the probe changes no draw's choice; a miss still makes the repair likelier) |
| F3 | High | Time accounting credits learning after a crossed goal date; multi-day actions double count | fixed | `cdd676b936` | `::test_f3_a_date_crossed_by_a_probe_is_scored_on_the_state_before_it_and_its_repair` (0.5, not 0.98), `::test_f3_a_multi_day_action_counts_no_interval_twice_and_no_session_before_its_end` (5.0, not 5.5; no session before the action ends) |
| F4 | Medium | Empirical return gaps apply only to the first return | fixed | `cdd676b936` | `::test_f4_the_return_gap_follows_every_session_end` (one session in six days with a three-day gap, not three) |
| F5 | Medium | Mid-block valuation collapses two action orders into one action | fixed | `cdd676b936`, `96ba40f55c` | `::test_f5_a_sequence_values_its_steps_in_order_with_their_own_kinds`, `test_ro4_codex_review.py::test_f5_mid_block_alternatives_are_ordered_sequences_of_their_own_blocks` |
| F6 | Medium | The LLM effect feature uses the wrong scale | fixed | `cdd676b936` | `::test_f6_the_effect_feature_is_the_difference_of_forecast_probabilities` (0.098, not 0.919) |
| F7 | Medium | Refinement timeout discards a successful numeric evaluation | fixed | `cdd676b936` | `::test_f7_a_refinement_cut_by_the_deadline_keeps_the_last_complete_batch` (controlled clock) |
| F8 | Medium | Every reading candidate starts with zero previous reading doses | fixed | `96ba40f55c` | `test_ro4_codex_review.py::test_f8_ad_reports_the_reading_dose_position_only_when_asked` (AD vault with two section reads: 2.0), `::test_f8_a_reading_candidate_starts_from_ads_dose_position` |
| F9 | Medium | RO4 forecasts never reach the claimed outcome resolver | fixed | `96ba40f55c` | `::test_f9_the_drawn_options_forecast_is_resolved_and_reported` (an unseen item 3 days after the block: both bindings scored at the realized lag; the report counts it once) |
| F10 | Medium | The LLM policy cannot see per-topic goal preferences | fixed | `96ba40f55c` | `::test_f10_the_policy_card_names_each_goals_topics_and_their_weights` (reversing `per_lo` changes the card) |
| F11 | Medium | The frozen evaluation population depends on candidate support | fixed | `96ba40f55c` | `::test_f11_the_evaluation_population_does_not_depend_on_candidate_support` |

None rejected. Each fix is inside RO4, and none re-argues the owner's §1 decisions.

## What changed, and where the spec was open

- **F1** (`objective_chooser.run_numeric(publish=...)`, `_objective_job`, `_decide_objective`): every complete
  uncorrected answer goes into the prefetch material (`numeric_published`) before any wait on the LLM policy.
  If a serve finds the numeric event unset, it serves that answer as `answered` with
  `policies.numeric.stage = "published_uncorrected"`, and the trace says so. The LLM-forecast correction is still
  applied when it finishes in time (opportunistic).
- **F2** (`value._probe`, `_probe_choice`, `_belief_model`): the branch is chosen in the belief's own world: ability
  drawn from the updated belief's mean and variance, the combiner's, `γ`'s and the reading curve's means, and noise
  streams seeded apart from the true path's. That integrates over the repair's outcomes. The chosen repair is then
  simulated on the true path. It is still one rollout per draw and branch, not a nested `Q̄` (the stage record's
  choice 8 stands, with this correction).
- **F3** (`value._segment`, `run_tail`): one chronological accumulator, as described in the module docstring and in
  §8.11. Undated uses during an action that crosses `C` now go to `T_C`'s reward, at the pre-effect state. Before
  the fix they were dropped.
- **F4**: return gaps form a `(draws, sessions)` common-random-number matrix. The first gap after the action counts
  from the day it ended (`floor(end) + gap`).
- **F5**: `V.SEQUENCE` with ordered `steps`, validated: no nested sequence, stop or offer. A probe step inside a
  sequence is its observation alone, and its information reaches the tail's allocation. The restraint gate passes
  `sequences={insert_now: (follow-up, rest), continue_current: (rest, follow-up)}`.
- **F8** (`readiness.decision_state_fields(reading_doses=True)`): the subject view's open `("reading", main facet)`
  window, averaged over the bank's rows. Only RO4 asks for it, so RO0's row 9 and every other caller stay
  byte-identical.
- **F9** (`router_objective/forecast_resolve.py`, binding `ro4-policy-forecast-binding-v1`): the drawn option's
  forecasts, bound to its decision's first served presentation and the option's main LO (now `main_lo` on each
  trace candidate). They are resolved at read time by RO2's resolver through the new
  `history_resolve.resolve_curves`, which shares `resolve`'s body. RO2's own receipts and rows are unchanged. The
  resolver is handed in by the CLI, because `router_objective` importing adaptive difficulty closed a frozen cycle
  (lint caught it). The stop offer, a fallen-back LLM and a decision that served nothing are censored at birth and
  counted. This evaluation never enters `w`.
- **F10**: `router-policy-card-v2`. Each goal lists `topics` and `topic_weights` (the `per_lo` overrides of `dated`).
  The card version starts a new comparator row.
- **F11**: `sources["population"]` holds the active goals' scopes plus the LOs with FSRS memory, built apart from the
  candidates. The trace's `evaluation.uses.topics` comes from it. A candidate-only topic is still valued in the
  rollouts at the config's density (`density: candidate_only` in the sources).

No new decision constant was added. The binding and card versions are labels. There is no new table, migration or
config key.

## Left unbuilt (smallest finish)

- **The memory model's own forecast curve** for §8.9. Only the LLM policy's forecasts are resolved. Smallest
  finish: record the rollout's believed `P(perform)` for the chosen option's main LO at 1, 7 and 30 days on the
  trace, then bind it with the same `forecast_resolve.groups` under a second forecaster name.

## For the owner before landing (unchanged by these fixes)

- **Calls per decision:** these fixes add no request. Each plan-block decision still makes one `router_llm` request
  (`router_llm_choice_v3`), each follow-up decision one (`router_llm_restraint_v3`), and each decision one Decider
  request (advice). The card grows by the goals' topic lists, a few hundred bytes per goal of ordinary size, inside
  the same `llm_card_token_budget` (48,000 bytes).
- **Tokens per decision:** at most about 12-16k input tokens. The router's floor of 16,384 output tokens is
  reserved, with one retry at double on truncation; the answer itself is a few hundred tokens.
- **A typical day:** about 5-9 LLM requests and as many Decider requests, so at most about 9 x 16k input tokens.
  These count as $0 on the ChatGPT plan route (`estimated_only`); on a metered route they come under the router's
  daily guard. No request was sent, so these are estimates, not measurements.
- **First-day report (§8.10), synthetic vault**, rerun on the fixed tree
  (`test_ro4_trace_report.py::test_the_first_day_report_against_the_predecessor_on_a_synthetic_vault`; 7 topics,
  25 suggested minutes, no model set up):

  | | Predecessor (mvp-0.46) | Objective (mvp-0.47) |
  |---|---|---|
  | Blocks served | 5 | 5 |
  | Planned minutes | 22.8 of 25 | 26.6 of 25 (past the plan, the soft frame) |
  | Stop in the support | only under 5 minutes left | at every boundary (1.0) |
  | Stop chosen | at the end | 0 of 5 decisions (the run ended with the plan's list) |
  | Longest session | (not recorded) | 18 active minutes |
  | Policy share of the draws | staged and the floor | staged 0.8, numeric 0.2 (no LLM set up) |
  | `κ0` | (none) | 0.00144 per minute (`tail_average`: the 64-draw marginal at `m̄` came out non-positive) |

  The stage record's earlier run had 4 blocks, 23.9 minutes and stop drawn once (1 of 5). The fixes change the
  rollouts (F2-F5), so these numbers moved. Draws differ by seed, so one synthetic day is not evidence of a trend.

## The gate (this step)

| Step | What ran | Result |
|---|---|---|
| Setup | `uv sync --extra dev --extra mobile`; `uv pip install --offline pypdfium2==5.14.0` | ok |
| Import contracts | `uv run lint-imports --no-cache` (under `env -i`, empty `HOME`/`CODEX_HOME`/`LEARNLOOP_CONFIG_DIR`) | 43 kept, 0 broken (a first draft broke the frozen-cycles contract; fixed by injecting the resolver) |
| New tests, pre-fix check | the 7 new value tests and the 8 new serving tests on the pre-fix sources | 7 failed, 8 failed (all, each on its finding) |
| Targeted batch | 82 files: every `tests/test_router_*.py`, `test_ro0_*.py`, `test_ro2_*.py`, `test_ro4_*.py`, `test_ad3_*.py`, `test_ad23_contract.py`, `test_ad23_fix_r7.py`, `test_ad23_fix_review.py`, `test_ad_guard.py`, `test_salience_firewall.py`, `test_desktop_rpc_contract.py`, `test_sidecar_serializer_snapshot.py`, `test_mobile_allowlist.py`, `test_table_roles.py`, `test_coordinated_migrations.py`, `test_tracked_fixture_databases.py`, `test_data_capture_*.py`, `test_teacher_te1b_suggestions.py` (`pytest -n 6`, 5G scope) | 6878 passed, 6 skipped, 0 failed |
| Contract and audit set, after the last edit | every `tests/test_ro4_*.py`, `test_ro2_history_resolve.py`, `test_architecture.py`, `test_cli_help_snapshot.py`, `test_codex_tool_lockdown.py` (process-launch allowlist), `test_module_catalog_inventory.py`, `test_router_why_copy.py` (display copy) | 337 passed, 1 skipped |
| Earlier contract run | `test_architecture.py`, `test_module_catalog_inventory.py`, `test_cli_help_snapshot.py`, `test_codex_tool_lockdown.py`, `test_registry_audit.py`, `test_router_why_copy.py` | 253 passed, 1 skipped |
| Durable SQLite | `--durable-sqlite` on `test_ro4_codex_review.py`, `test_ro4_objective_serving.py`, `test_ro4_trace_report.py` | 20 passed |
| References | `module_generate.py`, `module_validate.py` | PASS (the new `forecast_resolve` note) |
| Not needed | migrations, DB reference, frontend, `src-tauri` | no schema, frontend or Rust change |

Every test ran inside `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`, at most `-n 6`, one run
at a time. The full suite, the whole durability lane and the whole vitest run are left to the landing gate.
