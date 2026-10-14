# Method-explicit items: Codex review and fixes

Stage `method-explicit-items`, branch `grading/method-explicit-items`,
worktree `learnanything-merge`. Codex reviewed `1def803a1..39c370ef6`
read-only (job `20261013-203556-Y4ejLU`, no paid calls, import lint 17/17,
suite not run there). This record covers the fix step. The stage record is
`docs/reviews/method-explicit-items.md`.

Each finding was reproduced with a failing test before it was fixed. No
finding was rejected.

## Commits

| Commit | What |
|---|---|
| `6a2ea31fb` | fixes F1 to F8, with their tests |
| `ea2640acb` | regenerated architecture references (moved source-line citations only) |
| `c07f093e6` | the report's token estimates become upper bounds (F7, found by the live check) |
| `92e29b770` | the study-map writer tested end to end on required methods (F2) |
| `5090cca07` | the regrade's frozen-method reader moved into `attempts.attempts` (no new function-local cross-domain edge; the first gate run's one failure) |
| `2736852f3` | regenerated architecture references (moved source-line citations only) |
| (this commit) | this record |

Counts (`git diff --numstat 39c370ef6`): `src/` +797 / −160, `tests/` +553 /
−27. No migration, no new table, no schema or configuration change, nothing
under `apps/learnloop-tauri`.

## Findings

| ID | Severity | Title | Verdict | Commit | Test, or reason |
|---|---|---|---|---|---|
| F1 | High | Required methods are not frozen with the assessment contract | fixed | `6a2ea31fb` | `tests/test_required_method_grading.py`: `test_the_contract_snapshots_the_required_method_and_its_hash_moves_with_it`, `test_a_submission_is_graded_under_the_presented_contracts_required_method`, `test_a_snapshot_without_a_required_method_never_acquires_one`, `test_a_regrade_never_acquires_a_required_method_added_after_the_answer` |
| F2 | High | Merely mentioning a method activates its requirement | fixed | `6a2ea31fb`, `92e29b770` | `tests/test_required_method_items.py`: `test_a_mention_is_not_a_requirement` (25 statements), `test_the_writers_require_an_affirmative_statement`, `test_validation_reports_a_requirement_its_prompt_contradicts`, `test_an_imported_exercise_keeps_a_required_method_only_when_its_statement_states_it[required, only_named]`, `test_synthesis_publishes_a_required_method_only_with_an_affirmative_instruction` |
| F3 | Medium | Repair proposals can overwrite concurrent rubric edits | fixed | `6a2ea31fb` | `tests/test_method_phrasing_report.py`: `test_f3_a_repair_refuses_a_rubric_edited_before_acceptance`, `test_f3_an_accepted_repair_writes_no_proposal_only_key` |
| F4 | Medium | Configuring the Decider also selects it as the prose writer | fixed | `6a2ea31fb` | `test_f4_a_decider_on_the_route_is_never_the_writer` (real route resolution, no injected clients), `test_f4_a_failed_rewrite_keeps_the_deciders_paid_flags_with_labelled_drafts`; live check below |
| F5 | Medium | Missing judge answers become fabricated "fact" verdicts | fixed | `6a2ea31fb` | `test_f5_an_incomplete_reading_is_a_failed_item_never_a_fact_verdict[empty, missing, duplicate, unknown]`, `test_f5_the_required_methods_own_criteria_are_never_ledgered_as_verdicts` |
| F6 | Medium | The rewrite judge's verdicts never reach the judgment ledger | fixed | `6a2ea31fb` | `test_f6_the_writers_verdicts_reach_the_ledger_linked_to_the_repair` (agreed rewrites and a disagreement); `test_the_decider_flags_and_the_llm_route_writes_the_fact_phrasings` no longer expects Decider rows only; live check below |
| F7 | Medium | The dry run omits costs and some paid requests | fixed | `6a2ea31fb`, `c07f093e6` | `test_f7_the_dry_run_plans_rewrites_and_their_cost`; live check below |
| F8 | Medium | Cell 5 counts unassessed facts as successful enforcement | fixed | `6a2ea31fb` | `tests/test_grading_hardcases.py`: `test_every_fact_and_method_state_on_a_required_method_bypassed` (all 27 states), `test_outcomes_on_a_required_method_bypassed` and `test_the_production_path_applies_p1_to_a_divergent_route` corrected |

## The fixes

**F1.** `compile_assessment_contract` snapshots `required_method` (name and
criterion ids). It does so only when the item has one, so every other
contract and its hash are unchanged. Changing only the required method is now
a new contract. `contract_required_method` reads the stored value. A contract
without the key gives no method: an item that had no required method when it
was presented, or a contract written before this stage, never acquires one.

- **Submission.** The live doors (`_complete_attempt_with_agent_*` and the
  planning door) pass `_graded_required_method(item, contract)`. That is the
  presented contract's method. With no presentation snapshot, the submission
  snapshots the current item, so the current method is the presented one.
- **Regrade.** `regrade_attempt` reads the method from the contract its
  evidence rows cite (`attempts.attempts.attempt_required_method`),
  superseded rows included because a regrade's own rows need not cite it.
  With no contract it uses none.
- **Unchanged.** The regrade's prompt and rubric still come from the current
  item, as before; only the method is frozen.
- **Policy.** `reference_policy` / `required_method_policy` take the method
  explicitly. The default, the item's current method, is kept for the
  gold-set harness, which grades in-memory items.

**F2.** `method_statement(prompt, name)` returns one of four readings:

- `required`: the explicit instruction, or a requirement verb governing the
  method ("Use X", "by X", "Using X, ..."), and no clause contradicting it.
- `contradicted`: a negation ("without X", "do not use X", "instead of X",
  "X is not allowed") or an option ("You may use X", "X or any other method",
  "for example by X", "X or Y", "any method, e.g. X").
- `mentioned`: the name appears in some other way.
- `absent`: the name does not appear.

`prompt_requires_method` replaces `prompt_states_method` everywhere: the
grader's presented-prompt guard, doctor, the repair report, the gold-set
loader and the writers.

- **Generated prompts.** One that does not require the method gets the
  explicit instruction appended. One that contradicts it loses the
  requirement (`required_method:dropped_prompt_contradicts_it`), because the
  instruction would contradict the statement.
- **Source statements.** These are still never rewritten, and are kept only
  when they require the method affirmatively.
- **Variants.** A variant stem that contradicts the parent's method is noted
  (`required_method:prompt_contradicts_it`).
- **Doctor.** Reports `required_method:contradicted` as an error, next to
  `required_method:not_stated`, which now also covers a mere mention.
- **Repairs.** A repair never adds a required method that the item's prompt
  contradicts. It rephrases that criterion by fact instead, labelled
  `prompt_contradicts_method`.

The detector is conservative on purpose: an ambiguous statement reads as
contradicting, which drops the requirement and grades leniently.

**F3.**

- **The hash.** Each repair payload carries `expected_target_hash`
  (`compute_target_hash` of the item when the report ran). The existing
  accept-time recheck therefore refuses an item changed in between ("target
  changed after synthesis"), and nothing in the batch is applied. The
  summary tells the owner to run the report again.
- **Writer fix it needed.** `_compile_practice_item` now drops the
  proposal-only keys (`authority.PROPOSAL_ONLY_KEYS`) before the merge.
  Otherwise the hash would be written into the item's YAML, since vault
  models allow extra keys. This also covers graph-edit practice-item updates,
  which already stamp the hash.

**F4.**

- **Resolving the writer.** The writer is resolved apart from the judge
  (`writer_name`, `_ready_writer`). It is the route's chat profile when the
  route names one. Otherwise it is the serving chat provider
  (`LEARNLOOP_AI_PROVIDER`, else `ai.active_provider`): an unset route
  resolves as the task route always did, fallback provider included, and a
  route naming a decider uses the active provider explicitly, then
  `ai.fallback_provider`.
- **Capability check.** `can_write` requires isolated structured
  completions and refuses a decider. The forced LLM judge uses the same
  resolution, so `--judge llm` on a Decider-routed vault no longer gets a
  Decider.
- **Failed rewrites.** A rewrite that fails keeps the Decider's paid flags
  with labelled deterministic drafts (`writer_error`, report
  `writer_failures`). A spend refusal also stops further rewrites
  (`writer_stopped`).
- **Still raised.** Cancellation, and a spend refusal on the judge itself.

**F5.** `llm_readings` raises `IncompleteJudgment` unless the reading covers
exactly the item's criteria, once each. The item is then a failed item with
no readings, no repair and no ledger row. The Decider path likewise refuses
a missing answer.

A required method's own criteria are fact by design (`rule =
required_method`). They are no longer ledgered as either judge's verdict.

**F6.**

- **Ledger.** After a Decider, the writer's verdicts on the flagged criteria
  are appended under the writer's model, `rubric-phrasing-judge-v1` and the
  writer's own input hash, with rationale `llm (writer)`.
- **Repair link.** Each repair action lists `judgment_ids`: the Decider's,
  then the writer's. Each proposal row's `audit.rubric_phrasing` carries the
  ids and the actions.
- **Disagreements.** These are ledgered too: the writer's `fact` verdict sits
  beside the Decider's `method` verdict.

**F7.** `plan_dry_run` plans every judge the run may use, from configuration
alone. It builds no client and sends nothing.

| Judge | Steps planned |
|---|---|
| Decider | classification (one request per item with a judged criterion, at the profile's listed input price), then the writer's rewrites (at most one per such item) |
| LLM judge | one call per item |

- **Costs.** Each step shows its billing, price source, tokens and estimated
  dollars. Each judge shows a total and whether it is within the caps. The
  report gives `estimate.estimated_usd_upper_bound`.
- **Unknown price.** A metered route without a price is refused, not
  rendered as zero. The status is then `refused` and the CLI exits 1 (pass
  `--price-per-million`).
- **Subscription routes.** Codex and the ChatGPT plan are labelled
  `estimated_only`, with marginal $0, an API-equivalent cost at the owner
  price, and a statement that the token and dollar caps are not enforced on
  them.
- **Upper bounds (`c07f093e6`).** The live check showed that the bytes/4
  estimate under-ran reported usage. Admission and the dry run now use the
  PF convention: prompt UTF-8 bytes, plus the result schema for an LLM call,
  plus each Decider question's instructions and options.

**F8.** `judge_outcome` returns `caught` for cell 5 only when every method
criterion failed and every fact criterion has full credit.

| States | Outcome |
|---|---|
| a method criterion at full credit | `wrong_acceptance` |
| a fact criterion marked down | `wrong_rejection` |
| method failed, every fact at full credit | `caught` |
| anything else (a method or fact criterion unassessed) | `unassessed` |

The gold-set README says so. The production-path test with a strict grader
now reports both cell-5 cases `unassessed`, not `caught`: the facts were
marked down by the grader and unassessed by the rule, so the facts were not
credited.

**Effect on the recorded live results.** None. Every recorded cell-5 grade
in the eval copy's `judgment_ledger` had the facts at full credit and nothing
unverified: 2 cases × 2 routes × 2 repetitions, recomputed from the stored
`criterion_points`. The stage record's "required method enforced 2/2" stands
without a paid rerun.

**Docs.**

- The playbook and `Algorithm Versions and Reproducibility.md` now state
  that an answer is graded under the method its contract froze.
- Doctor's docstring names the new code and the command's real name
  (`learnloop grading method-phrasing`).
- The CLI help snapshot was regenerated (only `grading method-phrasing`
  changed).

## Fail-first

`39c370ef6`'s `src` was exported to `fixtures-local/tmp/base_39c370ef6`, with
its migrations and gold set linked in. The four changed test files ran
against it (`pytest -o pythonpath=<export>/src`). A shim aliased the renamed
helper (`prompt_requires_method` to the old substring check), so the
failures are behavioural, not import errors.

**Result on the export: 42 failed, 109 passed.**

| Finding | Failing tests |
|---|---|
| F1 | 4 |
| F2 | 21 (17 of the 25 statements, the writer, validation, exercise-import and synthesis tests) |
| F3 | 1 |
| F4 | 2 |
| F5 | 5 |
| F6 | 2 (the new test and the corrected old one) |
| F7 | 1 |
| F8 | 6 (3 of the 27 states, the corrected unit test, and the production path in 2 variants) |

Every one passes on the fixed tree.

## Live check (owner-authorized paid calls)

**Setup.**

- **Copy.** A backup-API copy (`learnloop.db.copies.copy_tree_with_databases`)
  of the stage's own phrasing copy:
  `fixtures-local/method-explicit/la_phrasing2` →
  `fixtures-local/method-explicit-review/la_phrasing3`. No tracked vault was
  opened.
- **Route.** `ai.routing.rubric_phrasing_judge = "openrouter_decider"` was
  added to the copy's `learnloop.toml`. This is F4's exact scenario. The
  active provider stays `or_haiku` (Haiku 5.5 on OpenRouter, `json_object`).
- **Keys.** The app loaded its own key; no key or env file was read.

**Dry runs.** `--judge decider --dry-run`; 59 items, 105 criteria.

| Dry run | Status | Estimate |
|---|---|---|
| no price | `refused`, exit 1 (unknown price for `rubric_phrasing_judge` / `or_haiku`) | none |
| `--price-per-million 0.5` (Haiku's listed output price, as an upper bound), cap $0.25, before `c07f093e6` | `dry_run` | upper bound $0.0826 |
| the same, after `c07f093e6` | `dry_run` | upper bound $0.183: Decider 102,038 input tokens; writer at most 59 calls, 243,846 input tokens (about 4,130 per call) and 118,000 output |

**Live run.** `--judge decider --price-per-million 0.5 --max-cost-usd 0.25`,
once, with no `--propose`.

- **The judge and the writer (F4).** The judge was the Decider
  (`perplexity/pplx-decider-v1.1-27b`, 59 requests). The writer resolved to
  `or_haiku` (`anthropic/claude-haiku-5.5`), not the Decider.
- **Ledger (F6).** 105 Decider verdicts and 24 writer verdicts went to
  `judgment_ledger`.
- **Flags and repairs.** 24 flags on 17 items, as in the stage's runs; 17
  writer calls; no failed item and no writer failure. Of the 24 rephrase
  repairs, 18 are LLM rewrites and 6 are drafts where the writer read the
  criterion as a fact (`judges_disagree`). Every action links both verdicts.
- **Cost (provider-reported, `model_call_receipts`).** Decider $0.0008573
  (42,866 input / 105 output tokens). Haiku $0.0111187 (27,847 input /
  16,668 output tokens). **Total $0.0120**, under the $1 cap.
- **Estimate accuracy.** The old bytes/4 estimates were 26,377 tokens for
  the Decider and 783 per writer call, both under the reported usage. That
  is why `c07f093e6` changed them; the new estimates bound both.

## Not changed

- **The review's general claim about writer coverage.** The synthesis writer
  now has an end-to-end test (`92e29b770`), and the exercise import a
  requiring-statement case. Other writers' tests that check guidance strings
  are unchanged; the authoring, exercise-import and PF-publication writers
  already have behavioural tests.
- **The old command name.** `learnloop rubrics method-phrasing` (the real
  command is `learnloop grading method-phrasing`) remains in three comments:
  `config/schema.py`, `config/template.py` and `ai/routing.py`. The template
  comment feeds the generated configuration reference, so it is left for the
  relabel at merge rather than widening this step.
- **The prompt the grader sees on a regrade.** A regrade still builds its
  prompt and rubric from the current item, as before the stage; only the
  required method is frozen.

## Gate

Run on the tree at `2736852f3` (the later commit is this record only), with
`TMPDIR` set to the worktree's `fixtures-local/tmp`.

An earlier run, at `92e29b770`, had one failure:
`test_architecture.py::test_function_local_domain_imports_match_the_frozen_edge_inventory`.
The regrade's function-local import of `learner.assessment_contracts` was a
new cross-domain edge. `5090cca07` moved the reader into `attempts.attempts`,
which already imports that module at module level. That run's other results
were 10,405 passed and a 99-test durability lane; both lanes were rerun on
the final tree.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | **17 kept, 0 broken** |
| Full suite: `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10,406 passed**, 0 failed (8 min 6 s) |
| Durability lane: `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **99 passed**, 10,307 deselected |
| `db_generate_reference.py`, then `db_validate_reference.py` | **0 errors**: schema head 199, 318 table notes, 796 configuration leaves in 48 sections (only source-line citations moved) |
| `validate_vault.py` | passed (1,099 notes) |
| CLI help snapshot | regenerated (`grading method-phrasing` only) |
| Frontend and cargo | not applicable: nothing under `apps/learnloop-tauri` changed |
