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
4. **Owner note (fix round 9).** Symbolic checks are off by default until the renderer-equivalent checker lands. The
   owner can turn them on (`[workbench] symbolic_checks_enabled = true`) knowing the limits recorded in "Fix round 9
   (orchestrator decision)".
5. **The two-attempt rule (fix round 10), superseded in fix round 13.** RW2b's server assists now follow H2b's R1
   rule. The counted set is the item's WINDOW: shown, unattached, server-counted workbench checks and level 1-3
   hints requested since the item's last attempt, whatever their problem's status. The attempt that counts them
   attaches them in its own transaction, so whichever attempt commits first takes them and no later attempt
   counts them again. The RW2a book keeps its own rule unchanged.

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

## Fix round 3 (orchestrator ruling)

The final verify (Codex job `20261018-175123-prT5bb`) **reopened F3 a second time**. It confirmed F1, F2 and F16.
Five reproductions came back `valid, checked, ✓` after being marked questionable:

* a name resolved to the wrong definition (`g'(x) = 3x^2` checked as the derivative of `f`'s `x^3`);
* `d/dy` checked as `d/dx`;
* `\int_0^2` checked over `[0, 1]`;
* a limit at 2 checked at 1;
* `x^{2+1} = x^2+1` losing its grouping.

The hint-claim path shared the flaw. The cause: the model declared the transformation and its expressions and
parameters, and `binding.py` only loosely matched that declaration to the learner's text.

**Ruling: heuristic binding had not converged, so the design changes. "Checked" comes only from the learner's own
written step, parsed by code.** Fixed in `28bb9da42`; the references were regenerated on top. **Paid calls: none
($0.00).** Every model is a fake.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F3 (reopened twice) | High | Declared parameters and loose binding certify wrong steps | fixed by redesign | `28bb9da42` | `test_reader_rw2b_fix3.py` (19 tests, all 19 fail on `86611ee9e`); `test_workbench_check_kinds.py` rewritten (16); the F2, F3, F10, F14 and F3r tests in `test_reader_rw2b_review.py` restated on LaTeX steps |

**What the check does now** (`learnloop.workbench.symbolic`, the sandboxed harness):

* **The parse.** It parses the step's (or a hint claim's own statement's) LaTeX with
  `sympy.parsing.latex` on the **lark** backend (an Earley parse, `ambiguity="explicit"`). Grouping is kept:
  `x^{2+1}` is `x**3`. A transformer subclass keeps a relation as a relation; sympy's `Eq` would evaluate
  `\int_0^2 2x\,dx = 1` to `False`. The parse gives one relation, both sides, the left side's operator
  (`Derivative`, `Integral`, `Limit`, `Sum`, a defined name) and that operator's variable, bounds and point.
  The check is run on THAT relation (`simplify(lhs - rhs) == 0`, or the operator applied to the parsed operand
  and compared with the parsed right side), with the same positive and negative controls as before.
* **The declaration only picks the kind.** Its expression, result, variable, bounds, point and relation are never
  check inputs. Each one that is set is compared with the parse, and the expression is required. Any disagreement
  (`declaration_disagrees:<field>`) means the model's reading.
* **Names.** A name resolves only to a definition `name(var) = expr` that code parses from an earlier learner step
  or from a delimited math segment of the problem (`$...$`, `\(...\)`, `\[...\]`). The step being checked is never
  a source. A name defined twice differently does not resolve. Primes differentiate the definition (`f'(x)`). An
  ambiguous parse (`f(x)` read as `f*x`) is resolved only by the names in force: a reading that uses an undefined
  name as a function refuses, and a reading that uses a defined name as a variable is dropped.
* **What stays the model's reading:**
  * anything that does not parse;
  * an ambiguous parse (`\lim_{x \to 2} x^2`, `\sin^2 x + ...`, `x(x+1)`);
  * an unresolved name;
  * prose: a run of two or more letters that is neither a LaTeX command nor a differential;
  * more than one relation (`a = b = c`, a step continuing with `= ...`);
  * an operator nested inside a side or on the right side;
  * an unsupported kind;
  * the lark backend being unusable (`latex_parser_unavailable`).

  There is no string or regex fallback that can produce "checked". The only regex rejects prose before the parse.
* **No "doesn't follow" while unknowns remain.** A difference that is not zero but still has free symbols gives the
  model's reading, never `≠`: the step may be an equation to solve (`(x-2)(x+2) = 0`), not a false identity. `≠ checked`
  needs an exact non-zero constant (`6 \cdot 7 = 43`, `\int_0^2 2x\,dx = 1`).
* **Kinds that can be checked:**
  * equivalence;
  * substitution (`f(a)` for a defined `f`);
  * differentiation (`\frac{d}{dx}(...)`, or `f'(x)`);
  * integration, definite or an antiderivative up to a constant;
  * normalization (a definite integral equal to 1);
  * limit;
  * sum;
  * solving: `x = v` against the step before's one equation, or, for a first step, the problem's only equation
    in `x`. The negative control skips other roots.

  **Inequality and boundary are no longer checked.** Sampling can certify a false inequality, and the parser reads
  no evaluation bar. Both stay declared kinds in the prompt.
* **The hint-claim path uses the same rule.** A claim is checked only when its own `statement` parses, its
  declaration agrees, and the relation holds. Names resolve to the problem's and the learner's definitions up to
  the claim's step. A statement in words stays the model's reading. The persisted claims, and so what `help_state`
  shows again, are these verdicts. The workbench `claims_rule` now asks for the statement as one LaTeX relation.
* **The host.** It trusts a harness verdict only when the harness reports `bound: true` (it parsed the text and the
  declaration agreed). Otherwise the result is `transformation_not_in_step:<n>` and the model's reading.
  `learnloop/workbench/binding.py` (substring, normalization and name-fallback matching) is **deleted**.
  `placement_json.symbolic[].bound` and the ledger's `bound` now come from the harness. The check prompt is
  `workbench_check.v2`: the declaration must match what the step writes.
* **Unchanged:**
  * the PF-b sandbox path;
  * the controls;
  * the bubblewrap-missing behaviour (every verdict is the model's reading);
  * `workbench.symbolic_checks_enabled`.

  No migration, no config key, and no RPC, serializer or check-label rendering change. The frontend was not
  touched, so vitest was not run.

**New dependency: `lark>=1.3.1`** (pure Python, MIT), a core dependency in `pyproject.toml` and `uv.lock`, added with
`uv add lark`. sympy's LaTeX parser needs it for the lark backend. It is importable in the sandbox, which runs the
venv's interpreter with `-I`.

**Fail-before** (`git archive 86611ee9e | tar -x` into `fixtures-local/tmp`, run with `-o pythonpath=<tmp>/src`; `lark`
importable there):

* `test_reader_rw2b_fix3.py`: **19 failed of 19**. These are:
  * the five reproductions;
  * the integral case through the hint-claim path;
  * positive controls for all nine kinds (equivalence, derivative, definite integral, antiderivative,
    normalization, limit, sum, solve, substitution), each a correct step parsed from LaTeX that must come back
    `✓ checked`;
  * grouping (`x^{2+1} = x^2+1` not checked, `x^{2+1} = x^3` checked);
  * a name defined in an earlier step resolving and an undefined one not resolving, in both the check and the
    hint paths.
* `test_workbench_check_kinds.py`: 16 of 16 failed. The file is rewritten, and on the old code its claims carry no
  `text`.
* `test_reader_rw2b_review.py`: 7 of 29 failed (the restated F2, F3r and F14 tests).

### Gate (fix round 3)

All runs used `TMPDIR=fixtures-local/tmp`. `/tmp/learnloop-fullsuite.lock` was free (`flock -n`).

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **27 kept, 0 broken** |
| `uv run pytest -n auto` over the 50 files below (every `test_workbench*.py`, `test_hint*.py`, `test_pf_sandbox*.py`, `test_reader_workbench*.py`, `test_reader_rw2b_review.py`, `test_reader_rw2b_fix3.py`, the contract tests: architecture, registry audit, judge routes, mobile allowlist, desktop RPC contract, sidecar contract; and every test that greps for `uv.lock` or `pyproject`: approach-map boundaries, daily-plan owner decisions, project redaction, project capture, reader observation records, workbench hint service) | **980 passed** (45.5 s) |
| `uv run pytest -n 8 --durable-sqlite` over `test_reader_rw2b_fix3.py`, `test_workbench_check_kinds.py`, `test_reader_rw2b_review.py`, `test_workbench_check.py` | **82 passed** |
| `db_generate_reference.py` then `db_validate_reference.py` | **0 errors**. Only commit labels and line citations moved; there is no schema change. |
| frontend (`npm`), `cargo check` | not run: nothing under `apps/` changed, and no check-label rendering changed |

### Open question (default taken)

* **Fewer checked verdicts, none wrong.** Several natural notations now get the model's reading:
  * `\sin^2 x`, `\exp(-t) + t` and `x(x+1)` parse ambiguously in sympy's lark grammar;
  * `d/dx` and `\pi` are not in that grammar;
  * steps with words (`F(x) = x^2 on [0, 1]`) and chains do not parse to one relation;
  * a wrong step that still has unknowns gives no `≠`.

  The default is the honest label. A learner who writes `(\sin x)^2`, `x \cdot (x+1)` or brackets a limit's body
  gets a check. *Updated in fix round 6:* the list of notations that stay the model's reading is now longer, and
  the full list is in "Fix round 6 (orchestrator)" below, as widened by "Fix round 7 (orchestrator)" and "Fix round 8 (orchestrator)".

## Fix round 4 (orchestrator)

The whole-stage Codex verify (job `20261018-183325-jlC3Dn`, at `2293d793a`) confirmed:

* the host's `bound=true` gate and the missing-sandbox fallback;
* lark locked at 1.3.1 and importable in the sandbox;
* the ordinary SQL fold;
* the shared service, the discriminating question, the text adapter and T6.

It raised seven items (five High, two Medium). The orchestrator ruled on each. Six are fixed in `6cca393ac`
and one is rejected. Each fixed item has a test in `tests/test_reader_rw2b_fix4.py` that fails on `2293d793a`.
**Paid calls: none ($0.00).** Every model is a fake.

| item | severity | title | verdict | test or reason |
|---|---|---|---|---|
| 1 | High | Truncated learner text can certify a false step | fixed | `test_item1_*` (2, both fail before): `1=1`, then 1,997 spaces, then `+1` is checked whole (`≠`); past the bound the result is `too_long:text` |
| 2 | High | Solving loses excluded values in parsing | fixed | `test_item2_*` (fails before: `\frac{x^2}{x} = 2x`, then `x = 0`, came back `✓`) |
| 3 | High | A clipped claim keeps its "checked" label | fixed | `test_item3_a_claim_longer_than_its_display_bound_is_never_checked` (fails before); `..._stored_exactly_as_it_was_verified` (guard) |
| 4 | High | `max(client, held)` loses a distinct assist | fixed | `test_item4_a_workbench_check_and_an_answer_box_reveal_are_two_assists` and `..._transactional_refold_...` (both fail before: 1, now 2); the carried-alone and the carried-plus-check workbench submit guards (1, 2) pass before and after, and the G5 rows (`test_workbench_assistance.py`, `test_reader_workbench_rw2a.py`) hold |
| 5 | High (as calibrated) | `workbench_check` permits Codex | **rejected** | The stage brief allows Codex where the spec explicitly allows it. `spec_reader_workbench_v1` says Codex "may run every paid LLM role", and D7 makes latency reported, not enforced: F12's ruling. No code change; `test_a_check_runs_on_codex_with_its_cost_estimated_from_tokens` stays. |
| 6 | Medium | A true real odd-root equation came back `≠ checked` | fixed | `test_item6_*` (fails before: `\sqrt[3]{-8} = -2` came back `checked, holds false`) |
| 7 | Medium | `workbench.cancel_help` bypasses the switch | fixed | `test_item7_every_help_rpc_refuses_when_help_is_switched_off` over all eight RPCs. The `cancel_help` case fails before (it cancelled the job); the other seven pass before and after. |

* **Item 1.** `SymbolicClaim.oversized()` names any bound a claim exceeds:
  * the step or claim text (4,000 characters, the check's step bound);
  * any earlier step (4,000) or more than 200 of them;
  * the problem (8,000);
  * a declared field (400; variable 40, relation 4).

  Such a claim is never sent to the sandbox. Its outcome is `model` with reason `too_long:<what>`, `bound = false`.
  The payload no longer clips anything: whatever is sent is sent whole.
* **Item 2.** The harness's transformer records what the written text restricts, before sympy evaluates it:
  * every denominator (`_handle_division`);
  * every log argument;
  * every square-root radicand;
  * the base of a negative or fractional power.

  A definition carries its restrictions to every use of its name. Solving is never checked (`restricted_domain`)
  when any restriction of the solved equation contains the variable, or when the evaluated residual still has the
  variable in a denominator. lark's evaluating parse cannot substitute into an unevaluated form, so per the ruling
  such a step stays the model's reading. Other kinds are unchanged.
* **Item 3.** `verify_claims` normalises each statement's spacing first and hands the verifier exactly that
  statement, so what is verified is what is stored and shown. A statement longer than `CLAIM_STATEMENT_CHARS = 240`
  is never `checked`. It is stored clipped with a visible `…` as the model's reading, unless it fails, which fails
  the round as before. A checked statement is never clipped.
* **Item 4.** The open problems' help is kept in two parts per problem, `(carried, server)`
  (`reader.workbench.held_parts_on`):
  * `carried` is the RW2a book once counted plus the answer-box hints carried into steps, which a client may also
    send;
  * `server` is the problem's shown checks and level 1-3 hints, which no client holds.

  `learnloop.attempts.hint_fold.combine_held(client, parts)` is `max(client, carried) + server`, taking the
  larger total over open problems. Only the overlap is deduplicated. `held_primed` still ORs in. The same rule runs
  in `_held_assistance` before grading and in the transactional refold, where `held_reader` now returns the parts.
  It is only ever raised. `ServerHintFold.held_parts` carries them. The workbench submit now sends only its carried
  part as the client's count (`SubmissionPlan.client_hints`); its own checks and hints join once through the held
  fold. Its attempt type still follows the full count.
* **Item 6.** `\sqrt[n]{...}` with n ≠ 2 (`nth_root`), and any numeric fractional power whose base is not provably
  non-negative (`fractional_power`), are the model's reading. Real-root semantics are not implemented.
  `4^{1/2} = 2` and `\sqrt{9} = 3` still check.
* **Item 7.** `_guard(ctx)` is the one switch guard, `help_disabled` while `workbench.help_enabled` (or
  `workbench.enabled`) is off. `_require` (check, suggest, request, answer_discriminating, set_help_style,
  help_state) calls it. `help_job` calls it and, when refused, still cancels a pending job (F13). `cancel_help` now
  calls it before looking the job up or changing it.

### Gate (fix round 4)

All runs used `TMPDIR=fixtures-local/tmp`. `/tmp/learnloop-fullsuite.lock` was free.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **27 kept, 0 broken** |
| `uv run pytest -n auto` over 53 files: round 3's 50, plus `test_reader_rw2b_fix4.py`, `test_facet_reword_confirm_review.py` and `test_reread_safety.py` (they name the held read) | **1087 passed** (52.6 s) |
| `uv run pytest -n 8 --durable-sqlite` over `test_reader_rw2b_fix4.py`, `test_reader_rw2b_fix3.py`, `test_workbench_assistance.py`, `test_reader_rw2b_review.py` | **86 passed** |
| `npx vitest run src/screens/workbench src/screens/PracticeScreen.workbench.test.tsx src/screens/ReaderScreen.workbench.test.tsx` | **7 files, 93 passed**. No rendering changed; recorded counts did, so this was run to be safe. |
| `db_generate_reference.py` then `db_validate_reference.py` | **0 errors**. Only commit labels and line citations moved. |

There is no migration, no config key and no RPC or serializer shape change.

## Fix round 5 (orchestrator)

The verify (Codex job `20261018-185606-c4kwx7`, at `3f86c1308`) confirmed these work:

* the bounds and the normalised claim storage;
* the over-240 downgrade;
* the root fallbacks;
* all eight RPC guards;
* the counting on a single problem.

It found five Highs. The ruling was to narrow the scope rather than chase domain edge cases. Everything is fixed in
`c1910d81d`. Each item has a test that fails on `3f86c1308`: `tests/test_reader_rw2b_fix5.py`, `fingerprint.test.ts`
and `test_mobile_allowlist.py::test_rw2b_fix5_*`. **Paid calls: none ($0.00).**

| item | severity | title | verdict | test |
|---|---|---|---|---|
| 1 | High | Solving loses restrictions through defined names (`f(x)=\frac{x^2}{x}`, `f(x)-f(x)=x`, then `x=0` came back `✓`) | fixed | `test_items_1_2_a_solve_through_a_restricted_name_is_never_checked`, `..._two_definitions_differing_only_in_their_restriction_never_resolve` |
| 2 | High | Substitution ignores restrictions (`f(x)=\frac{(x-1)^2}{x-1}`, then `f(1)=0` came back `✓`) | fixed | `..._a_substitution_into_a_restricted_name_...`, `..._not_used_by_any_kind_and_taints_...` (a restricted-name equivalence too), `..._a_hint_claim_through_a_restricted_name_...`; the guard `..._an_unrestricted_name_still_checks` passes before and after |
| 3 | High | The stale-check comparison truncated at 2,000 characters | fixed | `fingerprint.test.ts` (the verify's long-step edit is stale at once), `test_item3_the_snapshot_and_the_check_view_carry_a_full_text_fingerprint` |
| 4 | High | Distinct assists on two open problems were lost | fixed | `test_items_4_5_one_check_on_each_of_two_open_problems_records_two` |
| 5 | High | The carried count could not tell a book from an authored hint | fixed | `test_items_4_5_a_book_on_another_surface_and_an_authored_hint_record_two`, `..._a_book_alone_records_one`, `..._a_book_counted_on_two_problems_records_one`, `..._a_hint_free_submit_is_unchanged`; the guard `..._an_older_client_without_authored_hints_keeps_round_4s_rule` passes before and after |

* **Items 1-2 (domain restrictions through names).** The harness now reads restrictions from the **lark parse
  tree**, before anything is evaluated (`spots`, `names_in`). A restriction is any of:
  * the denominator of a `\frac`, `/` or `\div`;
  * a `\log`, `\ln` or `\lg`;
  * a `\sqrt`;
  * a power whose exponent is not a plain whole number.

  Each restriction records the letters it involves. The rules:
  * A definition `name(var) = body` is **restricted** when one of its body's restrictions involves `var`. A
    definition whose written body names a restricted (or conflicting) name is restricted too, taken to a fixpoint.
  * A step, or a hint claim's statement, that writes a restricted name is the model's reading for **every kind**
    (`restricted_name`). This is detected from the tokens, so an evaluation that cancels `f(x) - f(x)` cannot
    hide it.
  * A solve or substitution step is the model's reading (`restricted_domain`) if its own written text has a
    restriction involving any letter, or if the equation it solves does. Equivalence and the operator kinds keep
    round 4's rule.
  * Two definitions of one name whose bodies differ, or whose restriction status differs, never resolve.

  Hint claims go through the same harness, so all of this applies to them.
* **Item 3 (the stale-check comparison).**
  * Each snapshot entry (`step_snapshot_json`) now carries `fingerprint`, a fingerprint of the **full** step text:
    FNV-1a 64 over its UTF-8 bytes, written `fnv1a64:<hex>` (`learnloop.hints.workbench.text_fingerprint`).
  * `check_view` returns it as `checked_fingerprint`.
  * The workbench computes the same synchronously (`helpModel.ts` `textFingerprint`, pinned to the same reference
    values on both sides), so any edit to the content dims the verdict at once.
  * A row written before this round has no fingerprint. Its text is compared only within the 2,000-character
    bound, and any text past the bound counts as edited.
* **Items 4-5 (counting assists).** The count is now a sum of explicit components:
  * Each open problem of the item holds its help as `(book, carried, assist_ids)` (`held_parts_on`). The ids come
    from `help_assists.workbench_assist_ids`: shown, server-counted, unattached checks and level 1-3 hints.
  * When the client sends the new optional **`authoredHints`** (`submit_attempt`, `submit_dont_know`;
    desktop-only, pinned in `test_mobile_allowlist.py`; sent by the practice screen), `combine_held` adds:
    * the **authored** reveals: the larger of `authoredHints` and the problems' carried count, because the
      carried hints are the same answer-box reveals;
    * the **book**: 1 if any open problem counted it, never more than once;
    * every **distinct server assist id** over the open problems (a row belongs to one problem);
    * a floor of the client's own `hintsUsed`, which matters only when the client knows of a book the server's
      open problems no longer hold;
    * H2b's **window fold** and the tutor questions, unchanged.
  * `primed` is the OR of all of them.
  * The transactional refold recomputes the same parts under the lock, only ever raising the count.
  * Without `authoredHints` (an older client), round 4's rule applies unchanged.
  * The workbench submit sends its carried hints as `authored_hints`. Its book, checks and hints come from the
    held fold.
  * **"In this practice session":** a workbench problem records its practice session only when it is submitted,
    so the relevant problems are the item's **open** problems (the held rule since RW2a F2).

### Gate (fix round 5)

All runs used `TMPDIR=fixtures-local/tmp`. `/tmp/learnloop-fullsuite.lock` was free.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **27 kept, 0 broken** |
| `uv run pytest -n auto` over round 4's 53 files plus `test_reader_rw2b_fix5.py` and `test_sidecar_serializer_snapshot.py` | **1105 passed** (51.9 s) |
| `uv run pytest -n 8 --durable-sqlite` over `test_reader_rw2b_fix5.py`, `test_reader_rw2b_fix4.py`, `test_workbench_assistance.py`, `test_reader_rw2b_review.py` | **81 passed** |
| `npx vitest run src/screens/workbench src/screens/PracticeScreen src/screens/ReaderScreen.workbench.test.tsx` | **14 files, 177 passed** |
| `npm run typecheck`, `npm run frontend:build` | ok |
| `db_generate_reference.py` then `db_validate_reference.py` | **0 errors**. Only commit labels and line citations moved. |

There is no migration and no config key. The one RPC change is the optional `authoredHints` on the two submits.
The check view adds `checkedFingerprint`.

## Fix round 6 (orchestrator)

The verify (Codex job `20261018-191835-vPxfGb`, at `a1ad3737c`) confirmed:

* the round-5 counting, every component of it;
* the fingerprint, across Python and JavaScript;
* no other High or Medium.

**Two Highs remained, both in defined-name resolution:**

1. Greek identifiers bypassed restriction detection:
   * `f(\alpha)=\frac{(\alpha-1)^2}{\alpha-1}` then `f(1)=0`;
   * `\phi(x)=\frac{(x-1)^2}{x-1}` then `\phi(1)=0`.
2. An unsupported redefinition was skipped, which left the earlier definition in force:
   * `f(x)=x`, `f(x)=x^{\frac{1}{2}}`, then `f(4)=4`;
   * `g(x)=1/x`, `f(x)=x`, `f(x)=g(x)`, then `f(4)=4`.

**Ruling: remove defined-name resolution from every "checked" path.** Three rounds had shown it could not be made
sound cheaply. Fixed in `459b48202`. **Paid calls: none ($0.00).**

| item | severity | title | verdict | test |
|---|---|---|---|---|
| 1 | High | Greek identifiers bypass restriction detection | fixed by removal | `test_reader_rw2b_fix6.py::test_a_greek_parameter_*`, `..._a_greek_function_name_is_a_name_too`, `..._a_hints_claim_through_a_greek_function_name_*` (all fail on `a1ad3737c`) |
| 2 | High | An unsupported redefinition leaves the earlier one in force | fixed by removal | `..._a_fractional_power_redefinition_*`, `..._a_nested_redefinition_*`, `..._a_hints_claim_through_a_redefined_name_*` (all fail on `a1ad3737c`) |

**What changed** (`learnloop.workbench.symbolic`, the sandboxed harness):

* **Deleted:**
  * the definition table (`definitions`, `definition`, its cache);
  * conflict detection;
  * the restriction propagation through names;
  * the name-dependent `_ambig` filtering;
  * the defined-name branch of `classify` (substitution, `f'(x)`, `f(x) = ...`).

  `resolve` became `explicit`, which only refuses an expression that names a function.
* **Names are refused, read from the syntax.** `applies_a_name` returns the model's reading (`applies_a_name`)
  for a step or hint claim that:
  * contains a `function_applied`, `symbol_prime` or `matrix_prime` node in the lark tree;
  * contains a prime token;
  * writes an identifier, or any command other than the parser's own functions (`\sin`, `\exp`, `\log`,
    `\sqrt`, `\frac`, `\int`, `\lim`, ...), immediately before an argument.

  `defined_names` collects the names that the problem or an earlier step defines (`name(var) = ...`), including
  Greek ones. A text that writes one of them, with or without an argument, is the model's reading
  (`defined_name`). Identifiers are canonicalised, so `\alpha` and `alpha` are the same name and `\phi` is `phi`.
* **Solving.** Any restriction token in the step's own text, or in the equation it solves, gives the model's
  reading, whatever letters it involves. A restriction token is a denominator, a log, a root, or a power that is
  not a plain whole number. The solved equation may not apply or write a name either.
* **Kinds that can still be "checked"**, all on explicit expressions only (`CHECKABLE_KINDS`):
  * equivalence;
  * differentiation written as `\frac{d}{dx}(...)` of an explicit expression;
  * definite and indefinite integration;
  * normalization;
  * limit;
  * sum;
  * solve without restrictions.

  `substitution` and `f'(x)` are never checked. They stay declared kinds in the prompt's list, as the model's
  reading, like inequality and boundary. Restriction detection for a step's own text stays (round 4, items 2
  and 6).
* **Tests.**
  * The round-3 to round-5 tests that expected a defined name to resolve now expect the model's reading:
    * `test_reader_rw2b_fix3.py`: the earlier-step name, the hint path, the substitution control;
    * `test_reader_rw2b_fix5.py`: the unrestricted name;
    * `test_reader_rw2b_review.py::test_f3r_*`: `f'(x)`;
    * `test_workbench_check_kinds.py`: substitution.
  * The solve controls were rewritten without a fraction (`3x - 6 = 12`, `2x = 12`).
  * `test_a_name_free_correct_step_of_each_remaining_kind_still_checks` and the name-free hint claim are guards.
    They pass before and after.

**Notations that stay the model's reading** (updating round 3's open question; the default is the honest label):

* ambiguous parses: `\sin^2 x`, `\exp(-t) + t`, `x(x+1)`, `\lim_{x \to 2} x^2`;
* notation outside the grammar: `d/dx`, `\pi`, an evaluation bar;
* words and chains;
* every function name, defined or not, including Greek ones: `f(2)`, `f'(x)`, `\phi(x)`, `F(x) = ...`;
* any step that writes a name the problem or an earlier step defines;
* `\sqrt[n]{...}` with n ≠ 2, and fractional powers of a base that may be negative;
* a solve with any fraction, log, root or non-whole power in its text or its equation;
* inequalities;
* a wrong step that still has unknowns (no `≠`).

### Gate (fix round 6)

All runs used `TMPDIR=fixtures-local/tmp`. `/tmp/learnloop-fullsuite.lock` was free.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **27 kept, 0 broken** |
| `uv run pytest -n auto` over round 5's files plus `test_reader_rw2b_fix6.py` | **1113 passed** (50.6 s) |
| `uv run pytest -n 8 --durable-sqlite` over `test_reader_rw2b_fix6.py`, `test_reader_rw2b_fix5.py`, `test_reader_rw2b_fix3.py`, `test_workbench_check.py` | **59 passed** |
| `db_generate_reference.py` then `db_validate_reference.py` | **0 errors**. Only commit labels and line citations moved. |
| vitest | not run: no rendering changed (only the harness and Python tests) |

There is no migration, no config key and no RPC or serializer change.

## Fix round 7 (orchestrator)

The verify (Codex job `20261018-193340-5s348l`, at `8535477c2`) found two Highs:

1. **Defined names written with subscripts or formatting were missed** (a regression from round 6). After
   `f(x_1)=x_1`, `f_1(x)=x`, `\mathrm{f}(x)=x` or `\operatorname{f}(x)=x`, the step `\frac{d}{dx}(f)=0` came
   back `✓`.
2. **A solve skipped a restricted previous equation because it evaluated the same.** The sequence `2x=0`,
   `\frac{x^2}{x}=0`, `x=0` came back `✓`, and so did the `\dfrac` and `\tfrac` versions.

**Ruling: make both rules blunt and syntactic, and prefer refusing over cleverness.** Fixed in `8218788b7`.
**Paid calls: none ($0.00).**

| item | severity | title | verdict | test (`tests/test_reader_rw2b_fix7.py`) |
|---|---|---|---|---|
| 1 | High | Subscripted or formatted defined names are missed | fixed | `test_a_subscripted_or_formatted_definition_still_makes_its_name_a_name` (×4), `test_a_primed_or_applied_identifier_anywhere_is_a_name`, `test_a_hints_claim_about_a_formatted_or_subscripted_name_is_never_checked` (×2): all fail on `8535477c2`. `test_a_text_that_formats_or_subscripts_is_never_checked` is a guard and passes before and after. |
| 2 | High | A solve skips a restricted preceding equation | fixed | `test_a_solve_never_skips_a_restricted_preceding_equation` (`\frac`, `\dfrac`, `\tfrac`) and `test_a_hints_solve_claim_uses_the_step_just_before_its_step`: all fail on `8535477c2`. The guards `test_a_solve_checks_only_against_the_immediately_preceding_step` and `test_name_free_steps_of_each_kind_still_check` pass before and after. |

**Rule 1, names** (`name_rule`, `scan_names`, `identifiers` in the harness). A step or hint claim is the model's
reading if any of these holds:

* **Its own text writes a command outside the allow-list** (`formatting_or_command`). The allow-list holds:
  * the parser's own functions (`\sin` ... `\exp`, `\log`, `\ln`, `\sqrt`, `\frac`, `\dfrac`, `\tfrac`,
    `\int`, `\sum`, `\prod`, `\lim`, `\left`, `\right`, `\cdot`, `\times`, `\div`, `\to`, `\min`,
    `\max`);
  * relations and constants (`\le`, `\ge`, `\ne`, `\infty`, `\pm`, `\approx`, ...);
  * Greek letters.

  So `\mathrm`, `\operatorname`, `\text`, `\mathit`, `\mathbf`, `\prime` and every other formatting command
  refuse.
* **Its own text puts a subscript on an identifier** (`subscript`): `x_1`, `\alpha_1`. The `_` of `\int`,
  `\sum`, `\lim` and `\log` is not on an identifier.
* **It writes an identifier that is a NAME** (`names_a_name`). A name is any identifier written directly before
  `(` (whitespace, `\left`, a subscript or primes may come between), or with a prime (`'`, `\prime`,
  `^{\prime}`), anywhere in:
  * the problem text, its prose included;
  * any earlier step;
  * a hint claim's own step;
  * the text itself.

  Identifiers are canonical: formatting wrappers are taken off (`\mathrm{f}` is `f`), `\alpha` is `alpha`, and a
  subscript is dropped to its base letter (`f_1(x)` makes `f` a name). The parser's built-in functions are
  excepted.

The scan works on tokens. It deliberately over-matches: `x(x+1)` makes `x` a name, and so does a one-letter word
before a bracket in the problem's prose. A wrong extra name only costs a `✓`. Round 6's tree checks (function
applications, prime tokens) stay as well.

**Rule 2, solve** (`solved_equation`):

* A solve step is checked **only** against the **immediately preceding** step's relation, never an older one, and
  only when that step:
  * is exactly one relation;
  * passes rule 1;
  * has no restriction token in its written text (a denominator, log, root, or a power that is not a whole
    number).
* The solve step itself also passes rule 1 and has no restriction token.
* A first step may be checked against the problem's single equation, under the same conditions.
* The "skip earlier relations that evaluate the same" logic is removed.
* On the hint-claim path, a solve claim about step n is checked against step n-1. Step n is read for its names
  only (`SymbolicClaim.names_context`), so a claim restating step n is never checked against itself.

**Notations that stay the model's reading** (adding to round 6's list):

* any formatting or other unlisted command, such as `\mathrm{d}x` in an integral;
* any subscripted identifier;
* every identifier written before `(` or with a prime anywhere in the problem, the earlier steps or the text.
  This includes a variable such as `x` once `x(x+1)` or `x (` appears;
* a solve whose immediately preceding step is not one unrestricted equation in its variable.

### Gate (fix round 7)

All runs used `TMPDIR=fixtures-local/tmp`. `/tmp/learnloop-fullsuite.lock` was held at first by another worktree's
landing gate. These runs waited until it was free (`flock -n`). The fix commit was made before the gate ran, and
the gate then passed on it unchanged.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **27 kept, 0 broken** |
| `uv run pytest -n auto` over round 6's files plus `test_reader_rw2b_fix7.py` | **1127 passed** (52.7 s) |
| `uv run pytest -n 8 --durable-sqlite` over `test_reader_rw2b_fix7.py`, `test_reader_rw2b_fix6.py`, `test_reader_rw2b_fix3.py`, `test_workbench_check.py` | **59 passed** |
| `db_generate_reference.py` then `db_validate_reference.py` | **0 errors**. Only commit labels and line citations moved. |
| vitest | not run: no rendering changed |

There is no migration, no config key and no RPC or serializer change.

## Fix round 8 (orchestrator)

The verify (Codex job `20261018-201040-6YibdJ`, at `367d43ac5`) confirmed:

* counting, fingerprints, parameter binding and grouping;
* the immediately-preceding selection;
* no other regression.

**Two Highs remained:**

1. **Spellings defeated the name scan.**
   * Spacing commands, a brace group, `\left.`: `f\!(x)`, `f\,(x)`, `f\;(x)`, `{f}(x)`, `f\left.(x)`.
   * Unicode and prose names: `α(x)=x`, and `Let alpha(x)=x.`.

   In each case `\frac{d}{dx}(f)=0` came back `✓`.
2. **The first-step solve against the problem dropped restricted equations.**
   * With `Solve $2x=0$ and $\frac{x^2}{x}=0$.` the first step `x=0` came back `✓`.
   * So did `Solve $2x=0$ subject to $x>0$.`.

**Ruling: cut both at the root.** Fixed in `b113e76b0`. **Paid calls: none ($0.00).**

| item | severity | title | verdict | test (`tests/test_reader_rw2b_fix8.py`) |
|---|---|---|---|---|
| 1 | High | Spellings defeat the name scan | fixed | `test_a_spaced_grouped_or_left_dotted_definition_disables_the_problem` (×5), `test_a_unicode_or_prose_function_disables_the_problem`, `test_a_step_with_a_spacing_command_or_non_ascii_text_is_never_checked`, `test_a_hints_claim_after_a_spaced_definition_is_never_checked`, `test_a_hints_claim_on_a_problem_with_function_notation_is_never_checked`: all fail on `367d43ac5` |
| 2 | High | The first-step solve drops restricted problem equations | fixed | `test_a_first_step_that_solves_is_never_checked_against_the_problem` (the two-equation problem, `subject to x>0`, and a plain one), `test_a_hints_first_step_solve_claim_is_never_checked`: all fail on `367d43ac5`. The two positive controls (`..._on_a_function_free_problem_still_check`, `..._name_free_claim_on_a_function_free_problem_still_checks`) pass before and after. |

**Rule 1: function notation disables the whole problem** (`normalised`, `function_notation` in the harness).

* **Normalisation.** The problem's FULL text (prose included), every earlier step, and a hint claim's own step
  are normalised:
  * spacing commands (`\!`, `\,`, `\;`, `\:`, `\>`, `\ `, `\quad`, `\qquad`) and `~` are deleted;
  * all whitespace is deleted;
  * formatting commands (`\mathrm`, `\operatorname`, `\text`, `\mathbf`, `\mathit`, `\mathbb`, `\bm`, ...)
    are deleted, their argument kept;
  * every `{` and `}` is deleted;
  * `\left.` and `\right.` (and the `\big`/`\Big` sizes) are deleted.
* **One deviation from the ruling's wording:** before any other delimiter, `\left`/`\right` is deleted but **the
  delimiter is kept**. Deleting it as well would turn `f\left(x\right)` into `fx)` and hide it.
* **Detection.** If any letter (Unicode `str.isalpha`) or `\command` (other than the parser's built-ins) is then
  immediately followed by `(`, `[`, `'`, `\prime` or `^\prime`, the problem uses function notation. **Every step
  and hint claim on it is then the model's reading** (`function_notation`).
* **Over-matching is intended.** The CDF test item's own problem (`density f(x) = 2x on [0, 1]`,
  `P(X ≤ 1/2)`) disables every check on it. So does prose such as `on [0, 1]` or `g (x)`, and so does an earlier
  step written `\frac{d}{dx}(x^3)` (braces deleted, `x(` follows).
* This replaces round 7's per-name collection as the primary guard. Round 7's own-text rules stay on top.

**Rule 2: the current step's text is strict** (`name_rule`). The text must be ASCII only, must write no spacing
or symbol command (`\,`, `\!`, `\;`, `\ `, ...) and no `~`, and may use allow-listed commands only. Anything else
is the model's reading. Integrals are therefore written `\int_0^1 2x dx`, not `\int_0^1 2x \, dx`.

**Rule 3: solve.** A solve step is checked only against the immediately preceding LEARNER step. The first-step
path against the problem's equations is removed, so a first step that solves is the model's reading
(`first_step_solve`). On the hint path, a solve claim about step 1 is the model's reading.

**Tests updated.**

* `tests/workbench_help_fakes.py` gains `sidecar(..., prompt=...)` and `FUNCTION_FREE_PROMPT`.
* The rounds 3-7 tests whose steps must come back checked through the sidecar now use that prompt
  (`test_reader_rw2b_fix3.py` to `fix7.py`, and `test_reader_rw2b_review.py` F3, F10, F14 and F3r). The F14
  steps are written without function notation.
* `\, d` became ` d` in the positive controls.
* Round 7's first-step-against-the-problem expectation is now the model's reading.

**Notations that stay the model's reading** (adding to rounds 6 and 7):

* **every** check on a problem whose text, prose included, or any earlier step uses function notation in any
  spelling. This includes a letter or command before `(` or `[`, and so `f(x)`, `P(X ...)`, `on [0, 1]`,
  `x(x+1)`, `\frac{d}{dx}(x^3)` and `\left(` after an identifier;
* any spacing command or `~`, and any non-ASCII character, in the checked text;
* a first step that solves.

### Gate (fix round 8)

All runs used `TMPDIR=fixtures-local/tmp`. `/tmp/learnloop-fullsuite.lock` was free (`flock -n`).

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **27 kept, 0 broken** |
| `uv run pytest -n auto` over round 7's files plus `test_reader_rw2b_fix8.py` | **1142 passed** (52.7 s) |
| `uv run pytest -n 8 --durable-sqlite` over `test_reader_rw2b_fix8.py`, `test_reader_rw2b_fix7.py`, `test_reader_rw2b_fix3.py`, `test_workbench_check.py` | **65 passed** |
| `db_generate_reference.py` then `db_validate_reference.py` | **0 errors**. Only commit labels and line citations moved. |
| vitest | not run: no rendering changed |

There is no migration, no config key and no RPC or serializer change.

## Fix round 9 (orchestrator decision)

The verify (Codex job `20261018-202749-h7GveE`, at `dd56cf6ed`) confirmed counting, the fingerprints and the
first-step solve fix. It found two more Highs and a Medium:

1. **High: rendered function notation bypasses the normaliser.**
   * `Let $f\lparen x\rparen=x$.`, `Figure 1 caption: f&#40;x&#41;=x.` and `Let **f**(x)=x.` all render as `f(x)=x`.
   * With any of them, `\frac{d}{dx}(f)=0` came back `✓`, on both paths.
2. **High: an unbraced exponent is parsed differently from how KaTeX displays it.**
   * `$2^12=4096$` came back `✓`. KaTeX superscripts only the `1`, while sympy reads the exponent `12`.
   * `$2^12=4$` came back `≠ checked`, although the displayed `2^1 2 = 4` is right. This was already present at
     `367d43ac5`.
3. **Medium: a subscripted function does not disable the problem.**
   * On `Let $f_1(x)=x$.`, an unrelated `1+1=2` still checks. So does `f_1'=1`.

**Decision.** Six rounds have shown that a LaTeX-text checker cannot be made to agree with the renderer by
patching. **RW2b ships with symbolic checks OFF by default.** The three findings are not fixed. They are recorded
below with every bypass found in rounds 3-8, as the test corpus for a follow-up stage. Fixed (by decision) in
`fa3c6bbfb`. **Paid calls: none ($0.00).**

| item | severity | title | verdict | test |
|---|---|---|---|---|
| 1-3 | High, High, Medium | Rendered function notation, unbraced exponents, subscripted functions | **deferred**: symbolic checks off by default; corpus recorded below | `tests/test_reader_rw2b_fix9.py` (6 tests, all fail or error on `dd56cf6ed`); `symbolicOff.test.tsx` (3, fail on `dd56cf6ed`: no `verdictMark`, and `claimLine` showed `✓` for a non-checked claim) |

**What changed:**

* **The default.** `workbench.symbolic_checks_enabled` now defaults to **false**.
  * It is a modelled default, so the decision-only template does not write it. The schema comment and the
    template's history comments are updated.
  * All 19 `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries were recomputed with `defaults_fingerprint_for_version`, after
    clearing the config `.pyc` first.
  * The parameter registry records no default (its rule is unchanged). The CLI help does not show it, and its
    snapshot is unchanged.
  * The config references were regenerated.
* **At the default, every path is the model's reading**, and the sandbox is never invoked (pinned by
  `test_reader_rw2b_fix9.py`, each test at the default switch):
  * the check: every verdict is `model` and its mark `≈`, `?` or `·`;
  * `placement_json.symbolic` is `[]`;
  * `step_verdicts_json` holds `model` only;
  * `judgment_ledger` has no `workbench_check_symbolic` row, and the `llm` rows' method is `model`;
  * `help_state` shows no `✓` or `≠`;
  * the workbench report's `verdict_methods` is `{"model": n}` and `symbolic_outcomes` is `{}`;
  * a hint's claims are stored and restored as `model`.
* **The frontend guard** (`helpModel.verdictMark`, `claimLine`, `CheckColumn`). A `✓` or `≠` marker, or a
  "checked" label, is shown only when the verdict's method is `checked` or `checked_numerically`, whatever marker
  arrives. Every other verdict reads `≈`, `?` or `·` with "model's reading, not checked". A claim is `✓` only when
  its status is `checked` or `checked_numerically`. Before this round, `failed` showed `✓`.
* **The checker stays unchanged behind the switch.** Its tests turn it on: `workbench_help_fakes.sidecar(...,
  symbolic=True)`, and the direct `run_checks` tests need no switch.

**Follow-up stage: renderer-equivalent symbolic checks.** Parse the KaTeX output (MathML) rather than the LaTeX
text, so what is checked is what is displayed.

Design note:

* KaTeX renders the step's LaTeX to MathML, the same renderer the learner sees, with the same macros and grouping.
  The client sends the MathML with the step, or the server renders it with the same KaTeX version.
* The server converts a small MathML subset to sympy: `mn`, `mi` (single letters and Greek), `mo` (`+ − × · / = ( )`),
  `mfrac`, `msup` with an `mn` or `mrow` exponent, `msqrt`, `munderover`/`msubsup` for `∫` and `∑` with bounds,
  and `\lim` as `munder`.
* Anything outside that subset is the model's reading. This includes any `mi` that is followed by `(`, `mo` stretchy
  delimiters around an argument after an identifier, any `msub` on an identifier, any `mtext` and any `mi` with
  `mathvariant`, and any Unicode outside the subset.
* Function notation is then judged on the rendered problem and steps, with Markdown and HTML entities already
  resolved, not on their source.

**Test corpus** (every bypass found, rounds 3-9; each must come back the model's reading, or `≠` where the
displayed relation is false):

* **round 3** (heuristic binding):
  * a name resolved to the wrong definition: `f(x)=x^3`, `g(x)=x^2`, then `g'(x)=3x^2`;
  * `d/dy (x^3) = 3x^2` checked as `d/dx`;
  * `\int_0^2 2x dx = 1` checked over `[0,1]`;
  * `\lim_{x \to 2} x^2 = 1` checked at 1;
  * `x^{2+1} = x^2+1` losing its grouping;
  * the same integral through the hint-claim path.
* **round 4:**
  * `"1=1" + 1997 spaces + "+1"` truncated to `1=1`;
  * `\frac{x^2}{x}=2x`, then `x=0`;
  * a 479-character claim `0=N-N` clipped to `0=N`;
  * `\sqrt[3]{-8}=-2`, where sympy uses the principal complex root;
  * `max(client, held)` losing a distinct assist (counting: fixed, not deferred).
* **round 5:**
  * `f(x)=\frac{x^2}{x}`, `f(x)-f(x)=x`, then `x=0`;
  * `f(x)=\frac{(x-1)^2}{x-1}`, then `f(1)=0`;
  * a stale-check comparison truncated at 2,000 characters (fixed);
  * two open problems' checks counted once (fixed);
  * a book against an authored hint (fixed).
* **round 6:**
  * `f(\alpha)=\frac{(\alpha-1)^2}{\alpha-1}`, then `f(1)=0`;
  * `\phi(x)=\frac{(x-1)^2}{x-1}`, then `\phi(1)=0`;
  * `f(x)=x`, `f(x)=x^{\frac{1}{2}}`, then `f(4)=4`;
  * `g(x)=1/x`, `f(x)=x`, `f(x)=g(x)`, then `f(4)=4`.
* **round 7:**
  * `f(x_1)=x_1`, `f_1(x)=x`, `\mathrm{f}(x)=x` and `\operatorname{f}(x)=x`, each then `\frac{d}{dx}(f)=0`;
  * `2x=0`, `\frac{x^2}{x}=0`, `x=0`, also with `\dfrac` and `\tfrac`.
* **round 8:**
  * `f\!(x)`, `f\,(x)`, `f\;(x)`, `{f}(x)` and `f\left.(x)`, each `=x`, then `\frac{d}{dx}(f)=0`;
  * `α(x)=x`;
  * `Let alpha(x)=x.`;
  * `Solve $2x=0$ and $\frac{x^2}{x}=0$.` with the first step `x=0`;
  * `Solve $2x=0$ subject to $x>0$.` with the first step `x=0`.
* **round 9:**
  * `Let $f\lparen x\rparen=x$.`, `Figure 1 caption: f&#40;x&#41;=x.` and `Let **f**(x)=x.`, each then
    `\frac{d}{dx}(f)=0`;
  * `$2^12=4096$`, which displays as `2^1 2`, and `$2^12=4$`;
  * `Let $f_1(x)=x$.`, then `1+1=2`, and `f_1'=1`.

### Gate (fix round 9)

All runs used `TMPDIR=fixtures-local/tmp`. `/tmp/learnloop-fullsuite.lock` was free (`flock -n`).

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **27 kept, 0 broken** |
| `uv run pytest -n auto` over round 8's files, `test_reader_rw2b_fix9.py`, `test_config_refactor.py` (the defaults snapshot) and `test_cli_help_snapshot.py`; `test_registry_audit.py` is among round 8's | **1187 passed** (81.2 s) |
| `uv run pytest -n 8 --durable-sqlite` over `test_reader_rw2b_fix9.py`, `test_reader_rw2b_fix8.py`, `test_reader_rw2b_fix3.py`, `test_workbench_check.py` | **57 passed** |
| `npx vitest run src/screens/workbench src/screens/PracticeScreen.workbench.test.tsx src/screens/ReaderScreen.workbench.test.tsx` | **9 files, 99 passed** |
| `npm run typecheck`, `npm run frontend:build` | ok |
| `db_generate_reference.py` then `db_validate_reference.py` | **0 errors**. The workbench config reference now shows the default `false`, and commit labels and line citations moved. |

There is no migration and no RPC or serializer change. The one config change is the default of
`workbench.symbolic_checks_enabled`.

## Fix round 10 (orchestrator)

The final verify (Codex job `20261018-204415-a6csgq`, at `b5664a24f`) confirmed:

* the defaults and fingerprints;
* the registry and the references;
* the sandbox bypass at the default;
* the eight RPC refusals;
* the stamped-delivery refusal;
* ordinary counting.

It found four Highs. Fixed in `4ae737c4f`. **Paid calls: none ($0.00).**

| item | severity | title | verdict | test (`tests/test_reader_rw2b_fix10.py`; all fail on `b5664a24f`) |
|---|---|---|---|---|
| 1 | High | Stored symbolic results bypass the default-off switch | fixed | `test_item1_enable_check_disable_then_resume_recheck_hint_and_report_never_read_checked`; `symbolicOff.test.tsx` "with the switch off, ..." |
| 2 | High | An older client loses assists across two open problems | fixed | `test_item2_an_older_client_counts_the_union_of_assists_over_two_open_problems` |
| 3 | High | The refold can drop an assist it already counted | fixed | `test_item3_the_refold_never_drops_an_assist_it_already_counted` (A1 and B1 before grading, B2 in the transaction: 3) |
| 4 | High | Help disabled does not restore RW2a's counts | fixed | `test_item4_with_help_off_and_no_rw2b_assist_the_counts_equal_the_base_codes` |

**Item 4's base-versus-tip test.** It runs the same help-disabled sequence, in a subprocess, against `git archive
7d4c5f4ce` (`src`, `tests`, `migrations`) and against the code under test (`tests/rw2b_fix10_base_sequence.py`,
which uses only APIs present at the base). It requires the stored counts to be equal: 1 for the workbench submit,
and the same for an answer-box submit afterwards.

**Item 1: the switch on every read path.** The stored rows stay unchanged; they are history.

* `hints.workbench.unchecked_verdict` and `unchecked_claim` map a stored `checked` or `checked_numerically` method
  or status to `model` while `workbench.symbolic_checks_enabled` is off. They are applied by:
  * `check_view` (help_state, the check job, and a recheck that reuses the unchanged steps' row);
  * `ladder._verdicts` (the hint context, so the writer is never told, and a new hint row never copies, a checked
    verdict);
  * `row_claims` and `served_claims` (the hint views and the hint job's claims).
* `build_workbench_report(..., symbolic_enabled=)`, which `learnloop hints report` passes from the vault, reports
  historical symbolic counts only while the switch is on, and otherwise folds them into `model`.
* The check view carries `symbolic_enabled` and each hint view `symbolic_enabled`. The frontend's
  `verdictMark(verdict, symbolicEnabled)` and `claimLine(claim, symbolicEnabled)` refuse `✓` and `≠` when it is off.

**Item 2: one counting rule** (`attempts.hint_fold.combine_held`, `held_components`).

* **(a) The base path.** When the UNION of RW2b server assist ids (checks and level 1-3 hints, shown, unattached,
  on any open problem of the item) is empty, the count is RW2a's `_held_assistance` exactly, as at `7d4c5f4ce`: the
  larger of the client's `hintsUsed` and each problem's book plus carried hints. H2b's window fold is added on top.
  `authoredHints` is ignored. This covers help disabled and every submit with no RW2b assistance.
* **(b) The component path.** When the union is non-empty, the count is:
  * the client part: `max(authoredHints, carried)` when sent, else the legacy `max(hintsUsed, carried + book)`;
  * plus the book once, when it is not already inside the client part. With `authoredHints`, round 5's floor at
    the client's `hintsUsed` stays;
  * plus the size of the UNION of server assist ids over ALL open problems, never a per-problem maximum, for new
    and old clients alike;
  * plus the window fold.
* **(c) The refold.** `ServerHintFold` carries the components observed so far (`held_union`, `held_book`,
  `held_carried`). The transactional refold takes the union of the ids seen before grading and those seen in its
  transaction, ORs the book and keeps the larger carried count. It never drops an id it already counted. Counting
  an id that another problem's attempt also took is the accepted two-attempt rule (open question 5).
* **(d)** `primed` is the OR across every part.
* **Superseded test.** Round 5's `test_items_4_5_a_book_on_another_surface_and_an_authored_hint_record_two` had no
  server assist. Under ruling (a) it is RW2a's count, so it now records **1** (the larger of the client's 1 and the
  book's 1), as the base code does. This is the only existing expectation the round changed.

### Gate (fix round 10)

All runs used `TMPDIR=fixtures-local/tmp`. `/tmp/learnloop-fullsuite.lock` was free (`flock -n`).

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **27 kept, 0 broken** |
| `uv run pytest -n auto` over 62 files: round 9's, plus `test_reader_rw2b_fix10.py`; `test_reader_workbench_rw2a.py` and `test_workbench_assistance.py` (the G5 files) are included | **1191 passed** (75.5 s) |
| `uv run pytest -n 8 --durable-sqlite` over `test_reader_rw2b_fix10.py`, `test_reader_rw2b_fix9.py`, `test_reader_rw2b_fix5.py`, `test_workbench_assistance.py` | **43 passed** |
| `npx vitest run src/screens/workbench src/screens/PracticeScreen.workbench.test.tsx src/screens/ReaderScreen.workbench.test.tsx` | **9 files, 100 passed** |
| `npm run typecheck`, `npm run frontend:build` | ok |
| `db_generate_reference.py` then `db_validate_reference.py` | **0 errors**. Only commit labels and line citations moved. |

There is no migration and no config key. The check view and the hint views gain `symbolicEnabled`, which is
additive.

## Fix round 11 (orchestrator)

The verify (Codex job `20261018-210716-tgbjPD`, at `d8cbf3f3c`) confirmed:

* the no-assist arithmetic, over 17,550 combinations;
* the concurrent id union;
* the RPC guards.

It found four Highs. Fixed in `6ff2176bc`. **Paid calls: none ($0.00).**

| item | severity | title | verdict | test (all fail on `d8cbf3f3c`) |
|---|---|---|---|---|
| 1 | High | A cached hint job bypasses the switch, and the frontend drops the flag | fixed | `test_reader_rw2b_fix11.py::test_item1_a_hint_job_finished_while_on_reads_as_the_models_after_the_switch_goes_off`; `reviewFixes.test.tsx` "a hint job's claims follow the server's symbolic switch" (×2) |
| 4 | High | Historical checked verdicts reach the diagnoser unchanged | fixed | `test_item1_the_diagnosers_trace_reads_a_stored_checked_verdict_as_the_models_when_off` |
| 1, 4 | (structural) | No reader can miss the switch again | fixed | `test_architecture.py::test_stored_symbolic_results_are_read_only_through_the_one_accessor`. Run against the `d8cbf3f3c` tree, it reports 5 raw reads and 5 readers without the accessor. |
| 2 | High | A client-held book absorbs a distinct RW2b assist | fixed | `test_item2_a_client_held_book_and_a_check_on_another_problem_are_two`, `test_item2_the_refold_applies_the_same_floor` |
| 3 | High | The no-assist refold is not byte-identical to the base | fixed | `test_item3_a_book_opened_during_grading_leaves_the_count_and_type_as_the_base_stores_them`, run against `git archive 7d4c5f4ce`: both store `0, independent_attempt` |

**Items 1 and 4: one accessor, `learnloop.symbolic_view`.**

* It is dependency-free, so the diagnosis package may import it under `evidence-never-reads-the-workbench`. It
  provides:
  * `switch(config)`;
  * `symbolic_view(raw, *, enabled)`;
  * `verdict_records(row, *, enabled)`;
  * `symbolic_outcomes(placement, *, enabled)`;
  * `stored_claims(row, *, enabled)`;
  * `claims_view(...)`;
  * `hint_result_view(result, *, enabled)`.
* Every reader goes through it, with the CURRENT switch at read time:
  * `check_view` (help_state, the check job, a recheck's reused view);
  * `ladder._verdicts` (the hint context) and `row_claims`/`served_claims`;
  * the hint job's payload on EVERY read, first delivery and cached alike. The job stores claims as decided, and
    `_payload` remaps them and sets the current `symbolic_enabled` each time;
  * `build_workbench_report`;
  * `diagnosis/split/workbench_trace.trace_for_attempt`, given the switch by `current_attempt_for`.
* Round 10's `unchecked_verdict` and `unchecked_claim` are removed.
* **Architecture test.** `_SYMBOLIC_FIELD_TOKENS` is grep-based. It covers `step_verdicts_json`,
  `verdict_from_record`, `checked_numerically`, the placement's `symbolic` key and the claims key. It fails on any
  module under `src/` that reads one of these, unless the module and that token are in `_SYMBOLIC_FIELD_ALLOWED`.
  The allow-list holds:
  * the accessor;
  * the writers: the harness, `check.run_check`, `hints.workbench`, `hints.service`, the store's columns, and the
    hint job writing claims as decided;
  * `ladder` decoding the accessor's records;
  * the report's waypoint map-node read, which reads no method;
  * modules whose `claims` belong to another domain: the evsi comparisons, source synthesis, and
    `repositories`.

  The five named readers must import the accessor, and a synthetic reader is rejected.
* **Frontend.** `useWorkbenchHelp` carries the job result's `symbolicEnabled` into the hint view.
  `verdictMark`/`claimLine` show `✓`/`≠` only when the flag is exactly `true`, so a missing flag refuses too. The
  vitest fixtures that show a checked mark now pass `symbolicEnabled: true`.

**Item 2: the client floor** (`combine_held`, path (b)).

* `non_server = max(hintsUsed, client part + book)`, where the client part is `max(authoredHints, carried)` when
  `authoredHints` is sent. Without it, round 10's legacy `max(hintsUsed, carried + book)` is unchanged.
* `count = non_server + |union of assist ids| + window fold`.
* A book the client holds (`bookLeft`) therefore counts even when no open problem holds it.
* The refold uses the same rule with the unioned ids.

**Item 3: the base path in the refold** (`refolded_draft`).

* While the accumulated union of RW2b assist ids is empty, both before grading and in the transaction, the refold
  keeps RW2a's PRE-GRADING count, parts and type exactly. Only H2b's window fold refolds, as at `7d4c5f4ce`, and
  priming still ORs in.
* If the union becomes non-empty in the transaction, the refold switches to path (b) with every component.
* `tests/rw2b_fix11_base_sequence.py` runs the sequence through the base code and the code under test: an
  independent answer-box attempt while another process opens the book on the item's open Reader problem during
  grading.

### Gate (fix round 11)

All runs used `TMPDIR=fixtures-local/tmp`. `/tmp/learnloop-fullsuite.lock` was free (`flock -n`).

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **27 kept, 0 broken** |
| `uv run pytest -n auto` over 101 files: round 10's 62, plus `test_reader_rw2b_fix11.py` and `test_architecture.py`, plus every test file that imports `learnloop.diagnosis.split` (42) | **2027 passed, 2 xfailed** (94.2 s) |
| `uv run pytest -n 8 --durable-sqlite` over `test_reader_rw2b_fix11.py`, `test_reader_rw2b_fix10.py`, `test_workbench_trace.py`, `test_workbench_assistance.py` | **31 passed** |
| `npx vitest run src/screens/workbench src/screens/PracticeScreen.workbench.test.tsx src/screens/ReaderScreen.workbench.test.tsx` | **9 files, 102 passed** |
| `npm run typecheck`, `npm run frontend:build` | ok |
| `db_generate_reference.py` then `db_validate_reference.py` | **0 errors**. Only commit labels and line citations moved. |

There is no migration and no config key. The hint job result gains `symbolicEnabled`, which is additive.

## Fix round 12

The verify (Codex job `20261018-212800-g3CbjU`, at `d5126d45b`) confirmed 4,200 no-assist arithmetic cases and
15,552 base-versus-tip refold comparisons. Those comparisons covered count, priming, type and window under
concurrent changes.

It found four Highs and one Low. All are fixed in `5c00e00ab`. **Paid calls: none ($0.00).**

| item | severity | title | verdict | test (all fail on `d5126d45b`) |
|---|---|---|---|---|
| 1 | High | An empty refold snapshot is reread as legacy carried hints (a round-11 regression: 1 became 2) | fixed | `test_reader_rw2b_fix12.py::test_item1_the_refold_keeps_one_when_the_last_problem_closed_during_grading` (the verify's pure case), `..._end_to_end_a_problem_submitted_during_grading_is_not_counted_twice` |
| 2 | High | A carried hint absorbs a client-held book | fixed | `test_item2_a_book_left_a_carried_hint_and_a_check_are_three`, `test_item2_the_refold_keeps_the_client_held_book` (3 each); `test_mobile_allowlist.py::test_rw2b_fix5_*` pins `bookCounted` |
| 3 | High | In-flight hint jobs keep checked verdicts after the switch turns off | fixed | `test_item3_a_hint_in_flight_when_the_switch_goes_off_writes_and_stores_the_models_reading` |
| 4 | High | The empty-stuck fallback drops `authoredHints` | fixed | `test_item4_a_stale_stuck_screens_empty_answer_keeps_its_authored_hint` (3) |
| 5 | Low | The architecture allow-list does not enforce the boundary | fixed | `test_architecture.py::test_symbolic_field_detector_rejects_a_synthetic_reader` (including the verify's `row.get("step_verdicts_json")` injected into `hints/workbench.py`), `::test_stored_symbolic_results_are_read_only_through_the_one_accessor`, `::test_only_verdict_mark_and_claim_line_render_symbolic_marks`. Run against the `d5126d45b` tree, the AST rule reports `report_workbench.build_workbench_report`'s raw `step_verdicts_json` read. |

* **Item 1.** `ServerHintFold.held_known` is set by every submit that reads the held parts. It marks "components
  known, possibly none" apart from a legacy fold built before components existed. `base()` reads an aggregate
  `held_hints` as carried hints only for a legacy fold with no union, and never when assist ids exist.
* **Item 2.** The client already sent the book only inside `hintsUsed` (`answerHints = hintsUsed + bookCarried`),
  so a new optional `bookCounted` is added beside `authoredHints`.
  * It is accepted by `submit_attempt` and `submit_dont_know`, is desktop-only, and is pinned in
    `test_mobile_allowlist.py`. The practice screen sends it.
  * It is its own component (`ServerHintFold.held_client_book`, `combine_held(client_book=)`), ORed into `book`
    before the formula, in the refold too.
  * The verify's case: `max(1, max(0, 1) + 1) + 1 = 3`.
  * Path (a) is unchanged, because there the client's `hintsUsed` already holds the book.
* **Item 3.** `WorkbenchHintContext.symbolic_now` holds the sidecar's live switch reader
  (`workbench_help._live_symbolic_switch`, through `ctx.require_vault()` after any reload).
  * `current()` maps the verdicts through the one accessor (`learnloop.symbolic_view.symbolic_view`) with the
    switch read NOW.
  * `prompt_block()` calls it before every writer invocation, and `verdicts_record()` calls it on every row
    serialization (`row_columns`).
  * The ladder sets the reader on every hint context. A context without a reader, the check's own row, writes its
    verdicts as decided.
* **Item 4.** The empty-stuck fallback (`submit_attempt` to `submit_dont_know_on`) now forwards `authored_hints`
  and `book_counted`. It is the only place that builds a `DontKnowInput` or `SubmitAttemptInput` from another
  input; the workbench submit builds its own from the plan. AD1's fields are not on this base.
* **Item 5.** The architecture test is now AST-based.
  * Exemptions are by FUNCTION: the writer operations `check_view`/`_verdicts` decoding the accessor's records,
    `verify_claims` deciding a status, and the module-level constants and store columns. Only the accessor and
    the other-domain `claims` modules are exempt as whole modules.
  * A dict key or an assignment target writes a stored field, so it is not counted as a read.
  * Every reader must CALL a name imported from `learnloop.symbolic_view`. This is checked by AST, so a substring
    no longer counts.
  * The TypeScript test allows `✓`/`≠` on the workbench, and reads of `verdict.mark`, only inside helpModel's
    `verdictMark`/`claimLine`, and keeps the unused `CheckMarker` unimported.
  * The report's waypoint read now goes through `verdict_records` too.

### Gate (fix round 12)

All runs used `TMPDIR=fixtures-local/tmp`. `/tmp/learnloop-fullsuite.lock` was free (`flock -n`).

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **27 kept, 0 broken** |
| `uv run pytest -n auto` over round 11's 101 files plus `test_reader_rw2b_fix12.py` | **2034 passed, 2 xfailed** (94.2 s) |
| `uv run pytest -n 8 --durable-sqlite` over `test_reader_rw2b_fix12.py`, `test_reader_rw2b_fix11.py`, `test_workbench_assistance.py` | **30 passed** |
| `npx vitest run src/screens/workbench src/screens/PracticeScreen*` and `src/screens/ReaderScreen.workbench.test.tsx` | **14 files, 170 passed**, and **1 file, 13 passed** |
| `npm run typecheck`, `npm run frontend:build` | ok |
| `db_generate_reference.py` then `db_validate_reference.py` | **0 errors**. Only commit labels and line citations moved. |

There is no migration and no config key. The two submits gain the optional `bookCounted`.

## Fix round 13

The verify (Codex job `20261018-233138-S4mHeC`, at `6f11b0fee`) confirmed round 12's targeted fixes:

* 336 no-assist cases;
* 13,824 base-versus-tip refold comparisons;
* the empty-snapshot fix;
* the architecture tests.

It found three Highs. All are fixed in `d7cf8363b`. **Paid calls: none ($0.00).**

| item | severity | title | verdict | test (all fail on `6f11b0fee`) |
|---|---|---|---|---|
| 1 | High | Abandoning steps loses shown assists | fixed (H2b's R1 rule) | `test_reader_rw2b_fix13.py::test_item1_a_check_on_an_abandoned_problem_counts_on_the_answer_box_attempt` (1, and the row attached), `::test_item1_reopened_the_answer_box_counts_it_and_the_problems_later_submit_does_not` (1, then 0) |
| 2 | High | In-flight verification creates checked results after the switch turns off | fixed | `::test_item2_a_check_in_flight_when_the_switch_goes_off_is_never_checked` and `::test_item2_a_hint_in_flight_when_the_switch_goes_off_stores_no_checked_claim`, each ×2 (off during the model call, so the sandbox is never called, and off during verification) |
| 3 | High | Marks already on screen survive a switch-off reload | fixed | `symbolicOff.test.tsx` "a displayed checked verdict loses its ✓ when the snapshot's switch goes off" (no remount) |

**Item 1: the window** (`help_assists.workbench_window_ids`, `unattached_ids`, `attach_workbench_rows`;
`attempts.hint_fold.attach_held`).

* **What is counted.** Every shown, unattached, server-counted workbench check or level 1-3 hint row of the item,
  requested at or after the item's last attempt, whether its problem is open, abandoned or reopened.
  * The window starts at the row's practice session's last attempt when the row records a session. Workbench rows
    record one only when their problem is submitted, by which point they are attached, so **the rule used is the
    item's last attempt in any session**.
  * The comparison is `>=`. Timestamps are whole seconds, and an unattached row in the last attempt's second is
    never lost.
* **How it is counted.** The window rides in the held parts as one more part, `(0, 0, window ids)`, beside the
  open problems' RW2a `(book, carried)` parts. The rest of round 10-12's arithmetic is unchanged:
  * the union of server ids is now exactly the window;
  * the RW2a book keeps its rule;
  * when the window is empty both times, the base path applies exactly as before.
* **Attaching.** The attempt attaches exactly those rows (`attach_held`, after `attach_keyless` in
  `apply_attempt`'s `BEGIN IMMEDIATE`), NULL to the attempt id as H0's attach writes. No migration was needed.
* **The refold.** It reads the window again in the transaction and unions it with the ids seen before grading
  that are still unattached, so rows another attempt attached in between are excluded.
* **Primed.** Levels 4-5 set primed, as before.
* **Tests updated for this ruling** (open question 5 changed):
  * round 10's refold case now records 1 for the answer box and 2 for problem A's attempt, which committed first
    and took the window (A1 and B1);
  * round 12's end-to-end case records 0, because the workbench attempt committed first and took the check.

**Item 2: in-flight verification** (`check._switch_now`).

* `run_check(..., symbolic_now=)` and `hint_claim_verifier(..., symbolic_now=)` receive the sidecar's live switch
  reader (`workbench_help._live_symbolic_switch`).
* They read it right before invoking symbolic verification, and again right after it, before the claims, outcomes,
  verdicts and ledger rows are serialized.
* If it is off at either point, everything is the model's reading, and in the first case the sandbox is never
  called.
* The hint service also reads `request.workbench.symbolic_now` right before serializing the row
  (`symbolic_view.claims_view`, `rounds_view`), so no claim is stored as checked once the switch is off.

**Item 3: marks on screen.**

* The app snapshot's `workbench.help` block now carries `symbolic` (`workbench.symbolic_checks_enabled`). The
  config watcher's `setAlgoConfig` notifies subscribers (`subscribeAlgoConfig`).
* `useSymbolicChecksLive()` (`useSyncExternalStore`) gates `VerdictCell`, `QuestionableNote` and the hint claims,
  AND-ed with each view's `symbolicEnabled`, so retained results re-render when the switch changes.
* `test_workbench_help_kill_switch.py` pins the new key.
* Two vitest fixtures that show a checked mark set `symbolic: true`.

### Gate (fix round 13)

All runs used `TMPDIR=fixtures-local/tmp`. `/tmp/learnloop-fullsuite.lock` was free (`flock -n`).

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **27 kept, 0 broken** |
| `uv run pytest -n auto` over round 12's 102 files plus `test_reader_rw2b_fix13.py` | **2040 passed, 2 xfailed** (91.5 s) |
| `uv run pytest -n 8 --durable-sqlite` over `test_reader_rw2b_fix13.py`, `test_reader_rw2b_fix12.py`, `test_reader_rw2b_fix10.py`, `test_workbench_assistance.py` | **35 passed** |
| `npx vitest run src/screens/workbench src/screens/PracticeScreen* src/screens/ReaderScreen.workbench.test.tsx` | **15 files, 184 passed** |
| `npm run typecheck`, `npm run frontend:build` | ok |
| `db_generate_reference.py` then `db_validate_reference.py` | **0 errors**. Only commit labels and line citations moved. |

There is no migration and no config key. The app snapshot's `workbench.help` gains `symbolic`, which is additive.
