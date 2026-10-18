# Reader workbench RW2b + adaptive hints H3: Codex review and fix round 1 (stage `reader-rw2b-h3`)

Branch `reader/rw2b` in `learnanything-merge4`. Codex reviewed `7d4c5f4ce..ca196c450` (job
`20261018-162520-MEScwa`, read-only) and found **15 findings (3 High, 12 Medium)**. This round
reproduced each one (a failing test where it can be tested), then fixed it. **None were rejected.** Fixes are in
`7ce123267`, the references regenerated on top. The stage record is `docs/reviews/reader-workbench-RW2b.md`.
Its deviation 5 (the check never runs on Codex) and deviation 13 / open question 2 (hints' claims are not verified) are
**superseded** by F12 and F14 below.

**Paid calls: none ($0.00).** Every model is a fake. No manual run was made in this round.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Assistance created after submission admission escapes the final count | fixed | `7ce123267` | `test_reader_rw2b_review.py::test_f1_*` (4 tests). Three of them failed on the old code (hint L3, worked help L4, an answer-box submit with a check shown during grading). |
| F2 | High | Numerical sampling certifies false identities as symbolically checked | fixed | `7ce123267` | `test_f2_*` (real sandbox). Both failed on the old harness (`Abs(x)=x`, `sqrt(x**2)=x` and `1/10000000000=0` came back as `checked` and holding). |
| F3 | High | Checking an unrelated expression can validate the learner's entire step | fixed | `7ce123267` | `test_f3_*` (`6 * 7 = 43` with `1+1 → 2` stays `?` model; the learner's own `6*7 → 43` is `≠ checked`) |
| F4 | Medium | The check's assumptions bypass answer-leak filtering | fixed | `7ce123267` | `test_f4_an_assumption_that_states_the_answer_is_never_shown` |
| F5 | Medium | Help is invisible before the learner writes a first step | fixed | `7ce123267` | `reviewFixes.test.tsx` "F5" (ladder and hint under the problem on a fresh problem) |
| F6 | Medium | Editing a checked step leaves its old verdict displayed as current | fixed | `7ce123267` | `reviewFixes.test.tsx` "F6" ×2 (dimmed at once, stale line, no RPC) |
| F7 | Medium | Polling after unmount counts help that was never displayed | fixed | `7ce123267` | `reviewFixes.test.tsx` "F7" (no `workbenchHelpJob` after unmount; the pending job is cancelled) |
| F8 | Medium | A failed draft flush does not stop hint generation | fixed | `7ce123267` | `reviewFixes.test.tsx` "F8" (no suggest or hint RPC; the ladder keeps the choice and says why) |
| F9 | Medium | Bridges bypass the advertised workbench spend limits | fixed | `7ce123267` | `test_f9_*` (3 tests: a search that finds nothing counts; the search takes its place before it runs; the search runs inside `workbench.max_daily_cost_usd` and a spent day refuses it) |
| F10 | Medium | Check verdicts never reach `judgment_ledger` | fixed | `7ce123267` | `test_f10_*` (the model's verdicts and the verifier's appended with the row; nothing on an unavailable check) |
| F11 | Medium | Five new switches are unclassified in the parameter registry | fixed | `7ce123267` | `test_f11_every_key_rw2b_added_is_classified` (the set must be complete, and every key needs a rule) |
| F12 | Medium | Codex checks are prohibited contrary to the owner decision | fixed | `7ce123267` | `test_workbench_check.py::test_a_check_runs_on_codex_with_its_cost_estimated_from_tokens` (replaces the refusal test) |
| F13 | Medium | The help kill switch does not stop delivery of existing jobs | fixed | `7ce123267` | `test_f13_*` (3 tests; all failed on the old handler) |
| F14 | Medium | Required verification of hints' mathematical claims is omitted | fixed | `7ce123267` | `test_f14_*` (4 tests: checked claim; failed claim re-asked once with the failure named; failing twice falls to `next_step` without it; uncheckable is the model's reading) and `reviewFixes.test.tsx` "F14" |
| F15 | Medium | Workbench hints unintentionally trigger answer-box outcome placement | fixed | `7ce123267` | `test_f15_*`: `not_due`, nothing scheduled, absent from reconciliation, 0 fake calls. It failed with the filter removed. |

## What each fix does

* **F1.** The fix extends `ServerHintFold` with the **held rule**: the help that the item's open workbench problems
  hold, meaning their book, carried hints, shown checks and hints, and worked help. A workbench submit's own problem is
  one of those (it stays open until its attempt commits). That help is read again inside the attempt's
  `BEGIN IMMEDIATE` refold by a callable that the sidecar passes in (`practice._held_reader` →
  `reader.workbench.held_on`). The attempt path still never imports the workbench (`evidence-never-reads-the-workbench`
  is kept). `base_hints` becomes `max(client, held) + tutor questions`, as `_held_assistance` computes it. The count
  and `primed` only ever rise, and an independent attempt takes the assisted type. This covers both workbench and
  answer-box submits. No help is shown after the commit (`mark_shown`'s key fence). The submit-time stamp stays, and
  H2a's fold, fence and delivery are unchanged.
* **F2.** The harness's `zero()` now reports how each verdict was reached:
  * **`checked`**: sympy simplifies to an identity, an exact number is not zero (`is_zero`), or the expression is
    non-zero at sampled rational points on both signs of every variable.
  * **`checked_numerically`**: zero at every sampled point but not proven, or a decimal constant (relative tolerance).
  * **The model's reading**: zero on only part of the samples. This is a domain the step does not state, as in
    `Abs(x) = x`, `sqrt(x**2) = x` and `log(xy) = log x + log y`.

  The controls now need an explicit `True` and `False`.
* **F3.** `claims_from` binds each declared transformation to the learner's own writing. Its result must be in the
  step, and its input in the step, an earlier step or the problem. Spacing, `**`/`^`, LaTeX grouping and implicit
  products are normalised. A product of numbers keeps its sign, so `6*7` never matches `67`. An unbound claim is
  still run and recorded (`placement_json.symbolic[].bound = false`, `transformation_not_in_step:<n>`), but the step
  keeps the model's reading.
* **F4.** Each step's `assumption` and each entry in the check's `assumptions` go through `text_leaks`. A leaking
  line is dropped and recorded (`assumption_gives_answer:<n>`, `assumptions_gives_answer:<i>`).
* **F5.** A ladder, pending line, notice or hint whose step is not a saved live step (a fresh problem's first move, or
  a step deleted since) now renders in a problem-level block under the steps (`workbench-problem-help`).
* **F6.** The check view now carries each verdict's `checkedText` (the snapshot's text, bounded at 2,000
  characters). `helpModel.withLocalEdits` compares it with the steps on screen, so a marker dims and the stale line
  names the step at once, with no save or model call.
* **F7.** `poll` re-checks the lifecycle after every wait, and nothing reads a job after unmount. Pending checks and
  hints are cancelled on unmount, and a start that answers after unmount is cancelled. **Policy for a read already in
  flight:** its result counts (the server showed it) and is never lost, because `workbench.help_state` restores every
  shown check and hint when the problem reopens.
* **F8.** `openHelp`, `take` and every reply or pick handle a failed flush the same way `runCheck` does: no RPC,
  and the line *Your latest steps aren't saved yet, so help can't read them*. The ladder stays open and keeps the
  learner's choice.
* **F9.** A bridge search's row is written **before** the search runs, in the transaction that checks
  `workbench.max_calls_per_session` (`session_calls_on`). Every search counts, found or not. A search that found
  nothing keeps its row, never shown, with `placement_json.status`. `mark_bridge_shown` shows only a row with a
  passage. The search runs inside `spend_envelopes(workbench daily envelope)`, so its metered calls are charged to
  `workbench.max_daily_cost_usd` as well as to the source service's envelope (the two stack). With the day spent and a
  metered verification route, the search is refused before anything is paid. The store owns the SQL
  (`help_assists.settle_bridge`).
* **F10.** `run_check` appends, in the transaction that writes the row:
  * one `llm` judgment per step the model judged (task `workbench_check`), with the model's verdict and a rationale
    giving the verdict shown, its method, what validation did and, on the first questionable step, the error-kind
    guess;
  * one `verifier` judgment per transformation the sandbox ran (task `workbench_check_symbolic`: `holds`,
    `does_not_follow` or `undecided`, with `bound`).

  The left side is `help_assist:<id>` and the right side is `workbench_step:<chain>`. No schema change.
* **F11.** A `structural`/`operational` rule now covers `workbench.{help,symbolic_checks,discriminate,error_kind,bridge}_enabled`.
  The test asserts that the set of keys RW2b added is complete (every `[workbench]` field except RW2a's two, plus
  `ai.routing.workbench_check`) and that every key has a rule.
* **F12.** `CheckRoute.problem` no longer refuses Codex. `PaidCalls` already records subscription calls as
  `estimated_only` with no physical-request bound (owner decision 2026-10-12). `workbench.max_calls_per_session`
  still applies to every route, because it is the spec's G12 per-session cap, not a Codex-specific bound. D7's
  ChatGPT-plan or fast-OpenRouter recommendation stays as guidance; its latency target is reported, not enforced.
  `hint_writer` stays off Codex under the hints spec's D9, which this finding does not touch. The check's docstring,
  the schema comments and the template note are updated.
* **F13.** `workbench.help_job` reads `workbench.help_enabled` again first. With it off, the job is cancelled
  (unless already delivered) and the read refuses `help_disabled`, so nothing is delivered, counted or bridged. A
  bridge still searching when `workbench.bridge_enabled` goes off is cancelled and never shown.
* **F14.** This implements Reader §5.3, "hints are verified separately from how they are written":
  * The workbench's writer output is `WorkbenchHintWriterOutputV1` (H2a's output plus `claims`: step, statement and
    a declared transformation), and the workbench prompt block gains `claims_rule`. The practice screen's prompt,
    schema and result are unchanged.
  * At level 2 and up, `hints.workbench.verify_claims` checks each claim through an injected verifier, which is the
    Reader's check path: `workbench.check.hint_claim_verifier`, with the same binding to the learner's expressions
    and the same sandboxed harness and controls.
  * A claim that does not hold, or names a step that does not exist, fails the round (`wb_claim_failed:<n>`). The
    hint is re-asked once with the failure named, then falls to H2a's level-3 downgrade "without its unverified
    claims" (or nothing is served where the downgrade is not allowed).
  * Every other claim is labelled `checked`, `checked numerically` or *model's reading, not checked*. The claims
    are kept in `contract_failures_json` (per round and as served), returned by the hint job and `help_state`, and
    shown under the hint (`StepHints`).
* **F15.** Every outcome-placement query (`_due`, `_hinted`, the reconciliation page) excludes
  `surface = 'workbench'` rows, as H2b §9 asked. An answer-box hint carried into steps is still placed.

## Gate (this step; the full suite, the whole durability lane and the whole vitest run happen once, in the landing gate)

All runs used `TMPDIR=fixtures-local/tmp`. `/tmp/learnloop-fullsuite.lock` was free (`flock -n`) before each
pytest run.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **27 kept, 0 broken** |
| `uv run pytest -n auto` over the 169 files below (the stage's 143 targeted files; every test file that greps for a changed module: `hint_fold`, `held_*`, `hints.outcome`, `workbench.bridge`, `workbench.symbolic`, `workbench.check`, `hints.workbench`, `hints.writer`, `parameter_registry`, `submit_attempt`, `workbench_help`; the config-defaults upgrade pins; and the contract tests). The template `.pyc` was cleared first. | **3387 passed, 2 xfailed** (459 s). An earlier run found one architecture failure (`test_sql_writes_stay_in_registered_owner_modules`: the bridge's UPDATE). It was fixed by moving the UPDATE into the store (`settle_bridge`), before the commit. |
| `uv run pytest -n 8 -m durability` over `test_hint*.py`, `test_workbench*.py`, `test_reader_workbench*.py`, `test_help_assists_schema.py`, `test_reader_rw2b_review.py` | **2 passed** |
| `uv run pytest -n 8 --durable-sqlite` over `test_reader_rw2b_review.py`, `test_workbench_assistance.py`, `test_workbench_check.py`, `test_workbench_hints.py`, `test_hint_h2b_fix4.py`, `test_hint_evidence.py` (WAL, production pragmas: the transactional refold) | **96 passed** |
| `npm install` (up to date), `npm run typecheck` | ok |
| `npx vitest run src/screens/workbench src/screens/PracticeScreen.workbench.test.tsx src/screens/ReaderScreen.workbench.test.tsx` (7 files: `HelpLadder`, `reviewFixes` (new, 6), `stepModel`, `switchOff`, `Workbench`, `PracticeScreen.workbench`, `ReaderScreen.workbench`) | **7 files, 93 passed** |
| `npm run frontend:build` | ok (the usual chunk-size warning) |
| `cargo check` | not run: nothing under `src-tauri` changed |
| `db_generate_reference.py` then `db_validate_reference.py` | **0 errors**, schema head 212. Only commit labels and line citations moved; there is no schema change. |

There is no migration, no new table and no table-role change. The new `judgment_ledger` tasks
(`workbench_check`, `workbench_check_symbolic`) use the ledger's free-text `task` and its existing judges (`llm`,
`verifier`).

Test files run: test_active_errors_overlay.py test_ai_compare.py test_approach_map_boundaries.py test_approach_map_replay.py test_approach_maps.py test_architecture.py test_blind_grading_contract.py test_chatgpt_plan_landing.py test_chatgpt_plan_provider.py test_chatgpt_plan_sidecar.py test_chatgpt_plan_workspace.py test_cli_help_snapshot.py test_config_refactor.py test_constraint_engine.py test_coordinated_migrations.py test_daily_loop_start_minutes.py test_daily_plan_composition.py test_daily_plan_owner_decisions.py test_daily_plan_replay.py test_daily_plan_review_regressions.py test_decider_landing.py test_desktop_rpc_contract.py test_diagnose_review.py test_diagnosis_async_router.py test_diagnosis_card.py test_diagnosis_context.py test_diagnosis_contract.py test_diagnosis_embeddings.py test_diagnosis_history_modes.py test_diagnosis_input_provenance_landing.py test_diagnosis_input_provenance.py test_diagnosis_isolation.py test_diagnosis_pipeline.py test_diagnosis_replay.py test_diagnosis_reports.py test_embedding_backfill.py test_embedding_recipe_hash_pins.py test_embedding_route_isolation.py test_field_signal_production_paths.py test_forecast_receipts_landing.py test_forecast_receipts.py test_glm_ocr.py test_grading_cli.py test_grading_support.py test_held_grade_composition.py test_held_grade_evidence.py test_help_assists_schema.py test_hint_authored_reveal_ruling.py test_hint_blind.py test_hint_contracts.py test_hint_discriminating.py test_hint_evidence.py test_hint_feedback_texts.py test_hint_feedback_widening.py test_hint_h2a_review.py test_hint_h2a_review_round2.py test_hint_h2a_review_round3.py test_hint_h2a_review_round4.py test_hint_h2b_fix3.py test_hint_h2b_fix4.py test_hint_h2b_rereview.py test_hint_h2b_review.py test_hint_kill_switch.py test_hint_outcome.py test_hint_replies.py test_hint_report.py test_hint_service.py test_hint_telemetry.py test_hypothesis_reference_contract.py test_judge_routes.py test_kinship_feature.py test_learner_text_gaps_composition.py test_learner_text_gaps_flow.py test_learner_text_gaps.py test_learner_text_gaps_rereview.py test_learner_text_gaps_review.py test_learner_text_source_widening.py test_library_asks_migration.py test_mcp_c1a_landing.py test_mcp_c1a_narrow.py test_mcp_c1a_review.py test_mcp_tools.py test_method_explicit_landing.py test_method_explicit_upgrade.py test_mobile_allowlist.py test_mvp010_upgrade.py test_mvp011_upgrade.py test_mvp013_upgrade.py test_mvp014_upgrade.py test_mvp015_upgrade.py test_mvp016_upgrade.py test_mvp017_upgrade.py test_mvp018_upgrade.py test_mvp020_upgrade.py test_mvp021_upgrade.py test_mvp022_upgrade.py test_mvp023_upgrade.py test_mvp024_upgrade.py test_openai_embedding_client.py test_open_world_gate.py test_p0_cutover_mvp08.py test_pfc_unassessed_readers.py test_pfc_unverified_unassessed.py test_pf_sandbox.py test_placement_diagnosis_decides.py test_placement_opening_probes.py test_placement_split_grades.py test_plan_determinism.py test_post_attempt_worker.py test_probability_cli.py test_probability_prep.py test_reader_active_reading.py test_reader_cues.py test_reader_find_sources_callers.py test_reader_formative_texts.py test_reader_guidance.py test_reader_intent.py test_reader_recap.py test_reader_recap_review.py test_reader_recap_review_r2.py test_reader_rw1b_review.py test_reader_rw2b_review.py test_reader_rw3a_landing.py test_reader_workbench_rw2a.py test_reader_wrap_up.py test_reading_step_switch.py test_recurrence_commands.py test_recurrence_groups.py test_recurrence_key.py test_recurrence_live.py test_recurrence_merge_composition.py test_registry_audit.py test_regrade_contract_successor.py test_regrade_contract_upgrade.py test_required_method_grading.py test_required_method_round3_review.py test_router_r2a_serving.py test_router_r2bc_landing.py test_route_rules_in_grader.py test_sensitivity_certificates.py test_serve_eligibility_review.py test_settings_sidecar.py test_sidecar_contract.py test_sidecar_registry.py test_sidecar_serializer_snapshot.py test_sidecar_trace_and_clarification.py test_sidecar_tutor_qa.py test_stuck_prompt.py test_stuck_prompt_replay.py test_t6_followup_composition.py test_table_roles.py test_tier1_decider.py test_tracked_fixture_databases.py test_ux_phase4_feedback.py test_ux_phase4_landing.py test_workbench_assistance.py test_workbench_check_kinds.py test_workbench_check_map.py test_workbench_check.py test_workbench_chooser.py test_workbench_discriminate.py test_workbench_help_kill_switch.py test_workbench_hint_service.py test_workbench_hints.py test_workbench_in_session_gaps.py test_workbench_report.py test_workbench_step_graph.py test_workbench_text_gaps.py test_workbench_trace.py 

## Open questions (with the default taken)

1. **The check on Codex (F12).** Default: allowed (`estimated_only`). The per-problem call cap still applies, and
   `learnloop ai latency` reports whether it meets the 10 s target. The owner may route `ai.routing.workbench_check`
   to a ChatGPT-plan profile for speed.
2. **Hint claims (F14).** Only transformations of the declared kinds are checked. Prose claims ("step 2 stands") are
   always the model's reading. A claim that fails twice drops to H2a's `next_step` downgrade, never a hint with the
   claim edited out.
3. **Binding is textual (F3, F14).** A learner who writes `\frac{1}{2}` where the model writes `1/2` gets the model's
   reading, never a wrong `checked`. A sympy-level binding that parses the learner's LaTeX is left for later.

## Re-review (Codex job `20261018-172852-5htI4v`, `ca196c450..reader/rw2b`)

Codex confirmed **F1** and **F2** fixed, **reopened F3** and raised **F16** (Medium). Both were reproduced
with failing tests first, then fixed in `0ead90ec9`; the references were regenerated on top. **None rejected.**
**Paid calls: none ($0.00).** Every model is a fake; no manual run was made.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Assistance created after admission escapes the count | confirmed fixed by Codex | `7ce123267` | no change |
| F2 | High | Numerical sampling certifies false identities | confirmed fixed by Codex | `7ce123267` | no change |
| F3 (reopened) | High | Substring binding lets part of a side validate the whole step | fixed | `0ead90ec9` | `test_reader_rw2b_review.py::test_f3r_*` (5 tests). All 5 failed on the old binder; the end-to-end repro (`x + x = 2*x + 1`, declared `x+x → 2*x`) came back `valid, checked, ✓` and now stays `questionable, model, ?`. |
| F16 | Medium | New hint claims bypass answer-leak filtering | fixed | `0ead90ec9` | `test_f16_a_claim_that_states_the_answer_withholds_the_hint_and_is_never_stored`, `test_f16_a_harmless_claim_is_kept_and_a_leaking_one_re_asks`. Both failed on the old code (one writer call, the leaking claim served). |

* **F3 (reopened).** The binder is now its own pure module, `learnloop.workbench.binding`, and the check
  (`claims_from`) and a hint's claims (`hint_claim_verifier`) share it through `check._bound`. The step's text is
  read as relations. It is split outside brackets at separators (line breaks, `;`, `:`, `, `, a sentence's `.`,
  `⇒`, the connectives *so / and / or / then...*, and the qualifiers *on / for / where / if / with...*, whose
  conditions become relations of their own), then at `=`, `<`, `≤`, `≠`, `≈`. A transformation binds only when the
  step asserts **exactly one relation** that the problem or an earlier step did not already state, and that relation
  is the transformation's:
  * the operator is `=` (an inequality's own relation);
  * the right side is the **whole** result (`1` for a normalization);
  * the left side is the **whole** input: equal to it (equivalence, inequality), the whole operand of the kind's
    operator (`d/dx(...)`, `\frac{d}{dx}(...)`, `(...)'`, `\int ... dx`, `\lim_{...}`, `\sum_..^..`,
    `[...]_a^b`, `...|_{x=a}`), or a one-letter name (`F(x)`, `f'(x)`, `P(X ≤ 1/2)`) that stands for a whole side
    written in the problem or an earlier step;
  * a step that starts with `=` continues the step before it (its left side is that step's last side);
  * for solving, the relation is `variable = result`, and the solved equation is written whole in the problem, an
    earlier step or the step.

  So `x + x = 2*x + 1`, `y + x + x = 2x`, `d/dx (x^3 + x) = 3x^2` (claim `x^3 → 3x^2`), `x + x = 2x = 5`,
  `x = 2 or x = -2` and a bare expression stay the model's reading. An unbound claim is still run and recorded as
  before (`bound = false`, `transformation_not_in_step:<n>`). The F14 test fixture `FALSE_CLAIM` had been bound only
  by the old substring artifact (`2` inside `x^2`). It now names a step that writes the false derivative
  (`F'(x) = 2`).
* **F16.** `hints.workbench.verify_claims` takes the item and the map (`service.py` passes `item` and
  `state.map`) and runs every claim's statement through H2a's level-aware `leak_flags`, the same check as the hint's
  text and plan labels. Worked levels 4-5 are exempt there, as in H2a. A leaking statement adds
  `claim_<flag>:<step>` to `check.leaks`, so the round is re-asked and then withheld, like any leak. It is recorded
  with status `withheld`, its flags, and an empty statement, so its words are never stored in
  `contract_failures_json` or shown.

### Gate (re-review step)

All runs used `TMPDIR=fixtures-local/tmp`. `/tmp/learnloop-fullsuite.lock` was free (`flock -n`).

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **27 kept, 0 broken** |
| `uv run pytest -n auto` over the 46 files below (every test file that greps for `workbench.check`, `hints.workbench`, `hints.service`, `hint_service`, `verify_claims`, `workbench_help` or the hint/workbench fakes; every `test_workbench*.py` and `test_reader_workbench*.py`; and the contract tests: architecture, serializer snapshot, desktop RPC contract, sidecar contract, mobile allowlist, table roles, coordinated migrations, tracked fixture databases, registry audit, help-assists schema) | **822 passed** (54.9 s) |
| `uv run pytest -n 8 --durable-sqlite` over `test_reader_rw2b_review.py`, `test_workbench_check.py`, `test_workbench_hints.py` | **63 passed** |
| `db_generate_reference.py` then `db_validate_reference.py` | **0 errors**. Only commit labels and line citations moved; there is no schema change. |
| frontend (`npm`), `cargo check` | not run: nothing under `apps/` changed |

There is no migration, no config key and no RPC or serializer change.

Test files run: test_approach_map_replay.py test_architecture.py test_coordinated_migrations.py test_desktop_rpc_contract.py test_help_assists_schema.py test_hint_authored_reveal_ruling.py test_hint_blind.py test_hint_contracts.py test_hint_discriminating.py test_hint_evidence.py test_hint_feedback_texts.py test_hint_h2a_review.py test_hint_h2a_review_round2.py test_hint_h2a_review_round3.py test_hint_h2a_review_round4.py test_hint_h2b_fix3.py test_hint_h2b_fix4.py test_hint_h2b_rereview.py test_hint_h2b_review.py test_hint_kill_switch.py test_hint_outcome.py test_hint_replies.py test_hint_report.py test_hint_service.py test_mobile_allowlist.py test_reader_rw2b_review.py test_reader_workbench_rw2a.py test_registry_audit.py test_sidecar_contract.py test_sidecar_serializer_snapshot.py test_table_roles.py test_tracked_fixture_databases.py test_workbench_assistance.py test_workbench_check.py test_workbench_check_kinds.py test_workbench_check_map.py test_workbench_chooser.py test_workbench_discriminate.py test_workbench_help_kill_switch.py test_workbench_hint_service.py test_workbench_hints.py test_workbench_in_session_gaps.py test_workbench_report.py test_workbench_step_graph.py test_workbench_text_gaps.py test_workbench_trace.py

### Open question (default taken)

* **Stricter binding (F3).** Some natural steps now get the model's reading where the old binder said *checked*:
  a chain `a = b = c`, a step that defines and then derives (`f(x) = x^3, so f'(x) = 3x^2`), and an assertion with
  prose before its left side (`We have x + x = 2x` and `Adding gives x + x = 2x` bind; `Adding up x + x = 2x` does not). The default is the
  honest label, never a wrong *checked*. A sympy-level parse of the learner's LaTeX that could bind a chain
  link by link is left for later.
