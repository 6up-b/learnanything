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

## Re-review (Codex, 2026-10-13)

Codex re-reviewed `39c370ef6..164c77990` read-only (job
`20261013-220458-juQEy5`, no paid calls, suite not run there). Verdict:
REOPENED. It reopened F1 and F2 and raised F9, F10 and F11. This section
covers the fix step for those findings.

Every finding reproduced with a failing test and was fixed. None was
rejected. Part of the fix had been written by a fix run that crashed before
it committed. That work was checked against the findings, reproduced (below),
and corrected where probing found new misreadings (F2) and one over-plan
(F11) before it was committed.

### Commits

| Commit | What |
|---|---|
| `d3af07fb9` | F1: a method-explicit regrade reads its whole assessment contract |
| `88268b7c9` | F2, F9, F10: instructions, not descriptions or formatting; contradicting variants refused |
| `c3c43fb30` | F11: the dry run prices every writer the run may select |
| `4404cc10f` | regenerated architecture references (moved source-line citations only) |
| `5294d2674` | the playbook and `Algorithm Versions and Reproducibility.md` state F1's rule |
| (this commit) | this record |

Counts (`git diff --numstat 164c77990`): `src/` +460 / −66, `tests/` +344 /
−1. No migration, no new table, no schema, configuration or CLI change,
nothing under `apps/learnloop-tauri`.

### Findings

| ID | Severity | Title | Verdict | Commit | Test, or reason |
|---|---|---|---|---|---|
| F1 | High | Regrades combine the frozen method with the current prompt and rubric | fixed | `d3af07fb9` | `tests/test_required_method_grading.py`: `test_a_regrade_grades_the_statement_and_rubric_its_method_was_frozen_with` (the reviewer's scenario: the current statement changed to "Use row reduction", the method criterion edited), `test_a_regrade_never_acquires_a_required_method_added_after_the_answer` (now also checks the statement the grader sees), `test_every_other_regrade_still_reads_the_item_as_it_is_now[kill_switch, no_method]` |
| F2 | High | Descriptions and "not required to use" still read as requirements | fixed | `88268b7c9` | `tests/test_required_method_items.py`: `test_rereview_an_instruction_is_read_through_descriptions_negations_and_formatting` (31 statements, including both of the reviewer's), `test_rereview_instructions_beyond_the_imperative_list_and_descriptions_with_math` (20 statements), `test_rereview_source_normalization_and_grading_read_the_instruction_not_its_formatting` |
| F9 | Medium | Formatting drops an explicit source requirement | fixed | `88268b7c9` | the same 31-statement test (7 formatted statements) and the source-normalization-and-grading test (the reviewer's statement, through `normalize_required_method(source_statement=True)`, the grader's `required_method_policy` and doctor) |
| F10 | Medium | Variant normalization appends a contradictory instruction | fixed | `88268b7c9` | `test_rereview_a_contradicting_variant_gains_no_instruction_and_is_never_published` (the reviewer's stem), `test_rereview_publication_rejects_a_selected_variant_that_contradicts_the_parents_method` (end to end through `publish_backlog`) |
| F11 | Medium | The dry run omits the configured fallback writer | fixed | `c3c43fb30` | `tests/test_method_phrasing_report.py`: `test_f11_the_dry_run_prices_the_configured_fallback_writer[unset, decider]` (refused without a price; with one, inside the bound; the run really selects it when Codex is missing), `test_f11_an_explicit_chat_route_or_an_env_override_has_no_fallback_writer`, `test_f11_an_unset_route_without_a_serving_provider_reaches_no_fallback` |

### The fixes

**F1.** The method, the statement that required it, and the rubric whose
criteria it lists form one assessment contract. A regrade now reads all
three from it.

- **Which contract.** `attempts.attempts.attempt_graded_contract` returns
  the contract the attempt's evidence rows cite, superseded rows included.
  It replaces `attempt_required_method`, which was removed as unused.
- **When.** `regrade_reads_contract` is true only while the required-method
  rules are on (`method_rules_active`) and the contract froze a method or
  the item has one now. In that case `regrade_attempt` builds the grading
  context from the contract's prompt and expected answer, uses
  `rubric_from_contract`, and passes the frozen method to the policy. The
  policy guard therefore reads the statement the learner answered.
- **Replay.** The new evidence rows cite that contract
  (`assessment_contract_version_id`), so replay reads the same criteria.
- **Everything else unchanged.** Every other regrade, and every regrade
  with the kill switch off, reads the item as it is now (canonical sources
  §7.3a; mvp-0.20 exactly). This supersedes the earlier "Not changed" note
  on the regrade prompt, for required-method items only.

**F2.** A requirement verb counts only inside an instruction to the learner
(`_requires_here`, `_instructs`). The clause's main part, its first comma
segment that is neither a fronted adverbial or condition nor bare math, must
open with one of these:

- an imperative from the list, now broadened;
- a verb missing from the list followed by its object or by nothing ("Tabulate
  the values by X", "Proceed by X"), unless it is a determiner, pronoun,
  auxiliary, preposition or discourse word ("Note", "Recall", "Earlier");
- an address to the learner ("You must", "Your answer should", "Your task is
  to").

The following read as `mentioned`:

- **Third-person verbs.** "The worked example uses X" counts only in a
  relative clause on the learner's work ("Write a proof that uses X").
- **A subject before a base-form verb.** "In the worked example, we use X".
- **A participle before "by" or "using".** "the value obtained by X".
- **Subordinate clauses.** "..., which the example finds by X", "Explain
  how to use X", "Decide whether to use X".
- **Fronted conditions.** "If using X, ...", "When using X, ...".

"Determine whether S is a basis by X" still instructs. Negations now
include "not required, necessary, needed, expected or obliged to use", "no
need to use", "do not need to" and "don't have to".

**Probe against regressions.** Before committing, 99 realistic phrasings were
compared with `164c77990`. The crashed run's version had dropped explicit
instructions whose verb was not on its list: "Proceed by induction" (also
misread as a participle), "Fit the model using least squares" and "Rank the
matrix using row echelon form". It also still read "The worked example
solves Ax = b by Gaussian elimination" as required, because any segment with
`=` counted as math. All of these are fixed and pinned by the 20-statement
test. On the final tree 14 of the 99 readings differ from `164c77990`; each
is a description, conditional or "whether to" now read as a mention.

The rule stays conservative: ambiguous text is read as a mention, not a
requirement.

**F9.** `_plain_text` removes inline formatting before the statement and the
method name are read:

- Markdown emphasis, code spans and strike-through;
- links, keeping their text;
- simple HTML tags;
- LaTeX text macros such as `\textbf{...}` and `\emph{...}`.

Source normalization, the grader's guard and doctor all read through
`method_statement`, so a formatted explicit instruction keeps its
requirement. The statement itself is never rewritten.

**F10.** `inherit_required_method` no longer appends the instruction to a
stem that contradicts the method (negated or optional). It returns
`VARIANT_CONTRADICTS_METHOD` instead. `ops.pf_publish.build_item_payload`
raises `VariantContradictsRequiredMethod`, a `PublishRefused`. Publication
then:

- ledgers a `refuse_contradicts_required_method` verdict;
- rejects the candidate (`rejection_filter = required_method_contradicted`)
  so a later run regenerates it;
- counts it as `refused_candidates` in `publish_selected` and in the PF run
  report (`refused`).

**F11.** `writer_names` lists every chat profile a run may write with, in
the order `_ready_writer` tries them:

- the primary;
- then `ai.fallback_provider`, exactly where the run falls back to it. That
  is a route naming a decider, or an unset route with a serving provider and
  no `LEARNLOOP_AI_PROVIDER` override, as `fallback_provider_for` resolves.

There is no fallback writer for a route naming a chat profile, an
environment override, or an empty or `manual` serving provider. The last
case was an over-plan in the crashed run's version, now fixed.

`plan_dry_run` prices each writer step on every such writer:

- the fallback is labelled `fallback_for` the primary;
- an unknown metered price on any writer is refused;
- a step is bounded by its dearest writer, since only one of them runs.

### Fail-first

`164c77990`'s `src` was exported to `fixtures-local/tmp/base_164c77990`.
`migrations` and the two gold fixture directories were linked in; no tracked
vault was linked. The four changed test files ran against the export
(`pytest -o pythonpath=<export>/src`).

**Result on the export: 32 failed, 116 passed, 1 collection error.**

| Finding | Failing tests |
|---|---|
| F1 | 2 |
| F2 | 20 (5 negations, 8 of the 31 descriptions, 7 of the 20 descriptions and conditions) |
| F9 | 7 formatted statements |
| F2 + F9 | 1 (the source-normalization-and-grading test) |
| F10 | 2 |
| F11 | the collection error: `test_method_phrasing_report.py` imports `writer_names`, which the export lacks |

Earlier in the step, before that import existed, the two F11 pricing tests
failed behaviourally against `164c77990`'s `src`. The 13 `required`
statements of the 20-statement test (the instructions the crashed run's
version dropped, and their neighbours) pass on the export, as they should.
Every test passes on the fixed tree.

### Live check

Not run. Every finding is deterministic: statement reading, regrade context,
publication and dry-run planning. None needs a model call to show it fixed,
so no paid calls were made.

### Gate (re-review)

Run on the tree at `5294d2674` (the later commit is this record only), with
`TMPDIR` set to the worktree's `fixtures-local/tmp`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | **17 kept, 0 broken** |
| Full suite: `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10,467 passed**, 0 failed (8 min 18 s) |
| Durability lane: `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **99 passed**, 10,368 deselected |
| `db_generate_reference.py`, then `db_validate_reference.py` | **0 errors** (only source-line citations and source-commit stamps moved) |
| `validate_vault.py` | passed (1,099 notes) |
| CLI help snapshot | unchanged (no CLI change) |
| Frontend and cargo | not applicable: nothing under `apps/learnloop-tauri` changed |

## Redesign (2026-10-14)

The final Codex verify (job `20261013-235413-bgDA2U`, read-only,
`164c77990..c9c5e6e4c`, no paid calls) confirmed F1 and F11 fixed, reopened
F2 (High), F9 and F10, and raised F12 and F13 (Medium). Every remaining
defect came from one design choice: READING FREE TEXT to decide whether a
method is required. Each round of the statement reader found new phrasings.
The owner directed a redesign, not another patch. The same lesson as the
held-grade and exam predicates applies: one structured authority.

### The verify's findings

| ID | Severity | Verify's reproduction | Now |
|---|---|---|---|
| F2 | High (reopened) | "In the worked example, using cofactor expansion gives 13. Compute det(B)." and "Compute det(A) without having to use cofactor expansion." read as requirements: kept at import, enforced at grading | Grading never reads the text. At import the one-time judgment decides (live: `allows` 0.88, `prohibits` 0.99); with no judgment nothing is required |
| F9 | Medium (reopened) | `Compute det(A) using \(\text{cofactor expansion}\).` and a reference-style Markdown link read as mentions: requirement deleted at import, policy `None` | Grading reads the field. At import the judgment decides (live: `requires` 0.99 for both) |
| F10 | Medium (reopened) | A cofactor-required parent's variant "Compute det(B), but do not use the method of cofactor expansion." got "Use cofactor expansion in your answer." appended and passed `PracticeItem.model_validate` | The one-time publication judgment (live: `contradicts` 0.9996) refuses it; `build_item_payload` refuses any required-method variant without a recorded verdict |
| F12 | Medium | "Determine which matrix is singular using cofactor expansion." read as a mention | As F9 (live: `requires` 0.98) |
| F13 | Medium | A frozen regrade bound the CURRENT (edited, unverified) content and lowered a verified attempt's `reference_status` | The regrade binds the content it graded: the attempt's recorded status stands unless the frozen content is the current content |

### The design

1. **One authority.** `PracticeItem.required_method`, frozen in the
   assessment contract the learner answered (F1's fix, kept), is the only
   thing grading, regrading and replay read. `required_method_policy` and
   `reference_policy` no longer take the presented prompt; the policy is the
   frozen field and nothing else. A test pins that neither has a statement
   parameter left.
2. **The text agrees with the field, without being read.** A writer that
   sets the field on a generated prompt appends the one canonical sentence
   generated from it, `Use {name} in your answer.`, unless it is already
   there verbatim (`ensure_method_instruction`). Validation
   (`required_method_problems`: doctor and the gold-set loader) checks for
   exactly that sentence, normalized only for whitespace
   (`has_method_instruction`; case, punctuation and wording count). "Compute
   det(A) by cofactor expansion." is therefore `required_method:not_stated`
   until the sentence is there.
3. **Source statements are judged once.** `RequiredMethod.statement` is
   `instruction` (the default, omitted from YAML and hashes) or `source` (a
   textbook stem that is never rewritten). When an exercise's author
   proposes a required method on a method target, the import asks one
   question of the new `content/proposals/method_statement_judge.py`: does
   this statement require the learner to use the method (`requires` /
   `allows` / `prohibits`)?
   - **Judge.** The Decider through `ai.routing.rubric_phrasing_judge` (or
     the code-default `openrouter_decider`), else the existing LLM judge on
     that route; no heuristic fallback.
   - **Decision.** The argmax of the Decider's probabilities, with no
     hand-set threshold; a tie goes to the conservative option.
   - **Ledger.** `judgment_ledger`, task `required_method_statement`, with
     the probabilities in the rationale and the argmax's probability as the
     score. A second ask with the same statement and method reuses the row,
     with no call.
   - **Result.** Only `requires` keeps the field: `statement: source`,
     `decided_by: judgment`, `judgment_id`. No judge ready, a refusal or a
     failure leaves no requirement (`required_method:dropped_source_statement_unjudged`,
     with a warning).
   - **Spend.** Each request is admitted before it is sent, under the
     judge's own cap ($0.25 and 50 judgments per import): the Decider at its
     listed input price, a metered LLM judge at
     `source_service.llm_price_per_million` (refused without one). The
     receipts are owned by the import, so the service's daily guard counts
     them. `plan_import_cost` lists the judgment.
4. **PF variants are judged once (F10).** After selection, each selected
   variant of a parent with a required method gets the same kind of
   judgment: does its stem prohibit or contradict the method
   (`consistent` / `contradicts`)? It is recorded in the ledger whether or
   not the candidate is published that day.
   - **Publication.** It reads the verdict under the vault lock, never the
     stem. `contradicts` is refused and rejected
     (`required_method_contradicted`). No verdict leaves the candidate
     selected (`unjudged_candidates`). Only a `consistent` stem gains the
     sentence.
   - **Binding.** A verdict binds the stem it judged, so an edited stem has
     none.
   - **Backlog.** `learnloop pf publish` still makes no model call.
   - **Spend.** The judgments are admitted under the PF run's own caps (its
     metered or subscription budget, `dcd993ad8`), and the PF dry run plans
     them as metered calls.
5. **The owner overrides through the proposal/confirm path.**
   - **Command.** `learnloop grading required-method ITEM --method NAME
     --criterion ID [--criterion ID ...]` (or `--clear`) persists one
     pending update proposal (purpose `required_method_override`, never
     auto-applied) carrying the item's content hash. `learnloop accept`
     applies it.
   - **Text.** A generated prompt gains or loses the canonical sentence with
     the field. A source statement is untouched and records
     `decided_by: owner`.
   - **Generated proposals.** These never change a source item's field: the
     key is dropped and the item keeps its field.
6. **The statement reader is demoted to flags.** `advisory_statement_flag`
   keeps only the negation and option regexes the earlier tests pinned (plus
   "having", "method" and "technique" as filler words). It now feeds:
   - doctor's `required_method:statement_may_disagree` warning
     (`judge = heuristic`);
   - a `statement_may_disagree` label on a repair action;
   - a study-map review diagnostic.

   It never decides grading, a writer's field or a publication. The
   instruction-detection half (imperatives, subjects, participles,
   subordinate clauses, about 230 lines) is deleted.
7. **Repairs.** `learnloop grading method-phrasing` never adds a required
   method to a source statement; the criterion is rephrased by fact,
   labelled `source_statement`. On a generated item, it adds the method with
   the canonical sentence.
8. **F13.** `regrade_attempt` binds `bind_replacement_grade` to the item
   only when the regrade read the item as it is now, or when the frozen
   contract's content (`item_content_hash`, `rubric_content_hash`) IS the
   current content (`GradedContract.matches_current_content`). Otherwise the
   status the attempt recorded for the content it was graded on stands. A
   frozen content whose own key is later disputed is still lowered.
9. **Kept as they were.** F1 (the frozen contract), F11, the successor
   placeholder `mvp-0.22-placeholder` and the kill switch
   `required_method.enabled`.
   - **No schema, migration, configuration key or prompt version change.**
     The authoring prompts already ask for the sentence; the new task route
     reuses `rubric_phrasing_judge`.
   - **PF publication policy.** `pf-publish-v2` is kept: the new gate
     applies only to parents with a required method (a field new on this
     branch), so every other publication is unchanged.
   - **Gold set v3.** The two hand-written cell-5 statements now record
     `statement: source, decided_by: owner`. The grader's input and the case
     keys are unchanged (the key hashes only the method's name and
     criteria), so the recorded live grades stand.

**Where each writer stands.**

| Writer | Statement | How the text agrees with the field |
|---|---|---|
| Authoring proposals, practice generation, diagnostic authoring, tutor promotion and gap seeds, rung variants, canonical ingest and exam imports (creates) | generated | canonical sentence appended (`_hold_required_method_to_rule`) |
| Study-map synthesis | generated | canonical sentence appended; advisory review diagnostic |
| Exercise imports (Reader, source import, harvest, needs) | source | one-time import judgment |
| PF variants | generated | canonical sentence, only after a `consistent` publication judgment |
| Method-phrasing repairs | generated only | canonical sentence; never on a source statement |
| Owner override | either | canonical sentence on generated; `decided_by: owner` on source |
| A generated update proposal on a source item | source | field unchanged |

### Commits

| Commit | What |
|---|---|
| `b8ba7c7d1` | the redesign, F13 and their tests; CLI help snapshot (`grading`, new `grading required-method`) |
| `dcd993ad8` | a PF run's judgments are admitted under the run's own caps |
| `ac97a428c` | regenerated architecture references (citations, stamps, the two route and switch notes) |
| (this commit) | this record and the stage record's pointer |

Counts (`git diff --numstat c9c5e6e4c dcd993ad8`): `src/` +1,452 / −506,
`tests/` +981 / −211. New: `tests/test_required_method_authority.py` (57
cases). No migration, no new table, no configuration key, nothing under
`apps/learnloop-tauri`.

### Fail-first

`c9c5e6e4c`'s `src` and gold set were exported to
`fixtures-local/tmp/base_c9c5e6e4c`, with `migrations` linked in. No tracked
vault was linked. The tests ran against the export
(`pytest -o pythonpath=<export>/src`).

**`tests/test_required_method_authority.py`: 46 failed, 11 passed.**

| Kind | Failing |
|---|---|
| Behavioural: the base ran and gave the wrong answer | 18 |
| New API: module, function, parameter, CLI command or report key missing | 28 |

The 18 behavioural failures:

| What the base did | Failing |
|---|---|
| The grading policy dropped a frozen method because of the wording (LaTeX, reference link, "which" clause, the contradictory variant) | 4 |
| A live grade and its regrade ignored the frozen method on a LaTeX-wrapped statement | 1 |
| A generated "worked example" or "without having to use" prompt gained no sentence | 2 |
| Validation passed those two without the sentence | 2 |
| Validation treated the contradictory variant as an error rather than flagging it | 1 |
| A source statement was validated by its wording | 1 |
| An import with no judgment kept a requirement read into "worked example" and "without having to use" | 2 |
| An import dropped the other three requirements, but under the old note "does not state it" | 3 |
| A generated update proposal changed a source item's field | 1 |
| F13: the frozen regrade lowered a verified attempt to `unverified` | 1 |

The 11 that pass on the base were expected to:

- the policy for "worked example" and "without having to use" with the
  field set;
- the sentence appended to four generated prompts;
- three validation cases;
- two F13 controls: binding when the frozen content is the current content,
  and binding without a frozen method.

**F10 probe on the export.** `build_item_payload` on the verify's stem
returned `'Compute det(B), but do not use the method of cofactor
expansion.\n\nUse cofactor expansion in your answer.'`.

**The four changed test files on the export: 3 failed, 70 passed, 2
collection errors.**

- The frozen-field plan test failed, as did the gold-set loader's
  `not_stated` and `undecided` refusals.
- `test_required_method_items.py` and `test_method_phrasing_report.py`
  failed to collect: they import `advisory_statement_flag` and
  `has_method_instruction`, which the base lacks.

Every test passes on the redesigned tree.

### Live check (owner-authorized paid calls)

**Setup.** A backup-API copy
(`learnloop.db.copies.copy_tree_with_databases`) of the earlier phrasing
copy: `fixtures-local/method-explicit-review/la_phrasing3` →
`fixtures-local/method-explicit-redesign/la_judge`.

- **Route.** `ai.routing.rubric_phrasing_judge = "openrouter_decider"`.
- **Keys.** The app loaded its own key; no key or env file was read.
- **Tracked vaults.** None was opened.

**Dry run.** 10 requests (8 source questions, 2 variant questions), an
upper bound of 17,238 tokens at the Decider's listed $0.02 per million:
**$0.00034**, within the $0.05 cap.

**Live run.** Each question was asked once, with method "cofactor expansion"
(`perplexity/pplx-decider-v1.1-27b`). Every argmax matched the intended
reading:

| Question | Statement | Verdict | Probability |
|---|---|---|---|
| source | worked example (F2) | `allows` | 0.884 |
| source | "without having to use" (F2) | `prohibits` | 0.989 |
| source | LaTeX-wrapped (F9) | `requires` | 0.992 |
| source | reference-style link (F9) | `requires` | 0.993 |
| source | "which" clause (F12) | `requires` | 0.977 |
| source | the canonical sentence | `requires` | 0.993 |
| source | "Using cofactor expansion along the first row, compute ..." | `requires` | 0.986 |
| source | "you may use cofactor expansion or any other method" | `allows` | 0.995 |
| variant | the contradictory stem (F10) | `contradicts` | 0.9996 |
| variant | a plain stem | `consistent` | 0.997 |

**Cost (provider-reported, `model_call_receipts`).** 10 requests, 2,287
input and 10 output tokens: **$0.0000457**. The admission reserved 7,295
tokens ($0.000146), an upper bound. No other paid call was made in this
step.

### Gate (redesign)

Run on the tree at `ac97a428c` (the later commit is this record only), with
`TMPDIR` set to the worktree's `fixtures-local/tmp`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | **17 kept, 0 broken** |
| Full suite: `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10,523 passed**, 0 failed (7 min 36 s) |
| Durability lane: `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **99 passed**, 10,424 deselected |
| `db_generate_reference.py`, then `db_validate_reference.py` | **0 errors**: schema head 199, 318 table notes, 796 configuration leaves in 48 sections (citations, stamps, the two new modules in the table notes, the route and switch notes) |
| `validate_vault.py` | passed (1,099 notes) |
| CLI help snapshot | regenerated (`grading`, new `grading required-method`) |
| Defaults snapshots | unchanged (no configuration key added) |
| Frontend and cargo | not applicable: nothing under `apps/learnloop-tauri` changed |

An earlier full-suite run was stopped before it finished, because a code
change (`dcd993ad8`) landed while it ran. The gate above ran on the final
tree.

### Not changed, and open questions

1. **An exercise whose author proposes no required method is not judged.**
   The question needs the method's name. A textbook stem that requires its
   target method but whose author missed it keeps no requirement and is
   graded leniently. The owner can add one with `learnloop grading
   required-method`.
2. **An unjudged selected variant waits.** No judge was ready, or it refused
   or failed, during its run. The model-free backlog never publishes it, and
   no later run revisits it. Say if `learnloop pf publish` should judge such
   a variant (that would be a model call).
3. **A judgment row may outlive its item.** A row written for an import that
   is then rejected (leakage, validation, an unverified key) stays in the
   append-only ledger.
4. **The advisory heuristic is still a regex.** It only flags, so its misses
   and false flags change nothing that is graded.
5. **The stage record's §1 and §2** describe the earlier reader-based writer
   check; a note there points here.
