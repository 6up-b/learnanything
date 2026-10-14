# Router R2b + R2c: Codex review fixes

Branch `router/r2bc`, worktree `learnanything-merge4`. Codex reviewed the
stage at `d2372dddf` (`28c6040ca..router/r2bc`, job
`20261014-104631-ZWkG5n`) and returned eight findings: two High and six
Medium. All eight are fixed. None was rejected. The review's "claims that
don't hold" are answered below; one of them led to a correction of the
stage record. No model, Decider or embedding call was made, no migration
was added, and no money was spent.

Owner decisions in force (2026-10-12):

- the spec defaults are accepted;
- Codex on the subscription may run every paid LLM role without a
  physical-request bound;
- the Decider is `perplexity/pplx-decider-v1.1-27b` on OpenRouter;
- frictionless defaults: honest labels, generous defaults, and live changes
  behind kill switches.

## Findings

| ID | Severity | Title | Verdict | Commit | Test (tests/…) or reason |
|---|---|---|---|---|---|
| F1 | High | Inserted follow-ups cannot bind to their actual outcomes | Fixed | `37d71de7a` | `test_router_g4_restraint.py::test_an_inserted_follow_up_is_bound_to_its_own_decision_by_its_presentation` (the presentation id serving returned) |
| F2 | High | Teach-back summaries bypass the held-grade predicate | Fixed | `fcb254903` | `test_router_r2c_teach_back.py::test_a_held_teach_back_is_never_summarized`, `::test_a_summary_leaves_the_card_once_its_grade_is_held_or_regraded` (real blind grade records through the predicate) |
| F3 | Medium | Embedding calls bypass spend admission | Fixed | `bf8548737` | `test_router_r2c_retrieval.py::test_the_query_embedding_is_admitted_by_the_daily_guard`, `::test_the_backfill_is_held_to_its_money_cap`, `::test_the_backfill_dry_runs_and_then_embeds_what_is_missing` (the priced dry run) |
| F4 | Medium | The daily guard admits operations, not every physical request | Fixed | `bf8548737` | `test_router_r2b_serving.py::test_a_json_repair_is_admitted_as_its_own_request` (the production chat provider with a fake SDK) |
| F5 | Medium | Restarting forgets reservations for unfinished paid calls | Fixed | `bf8548737` | `test_router_r2b_serving.py::test_an_unfinished_request_keeps_its_reservation_after_a_restart` |
| F6 | Medium | Competing follow-ups log choices that are never applied | Fixed | `bf6641566` | `test_router_g4_restraint.py::test_competing_follow_ups_log_only_the_insertions_that_happen` |
| F7 | Medium | The displayed rationale can describe a different block | Fixed | `ad3c0b4cf` | `test_router_r2b_serving.py::test_the_llm_rationale_is_shown_only_for_the_option_it_explains` |
| F8 | Medium | "Wait for the next block" can silently lose the follow-up | Fixed | `bf6641566` | `test_router_g4_restraint.py::test_a_follow_up_that_waiting_would_drop_joins_now`, `::test_a_waiting_follow_up_keeps_its_room_until_the_boundary` |

The DB and config references were regenerated after the fixes (`ea4d8ae84`:
provenance and moved line citations only).

### Reproductions on the original code

The twelve new tests ran against `d2372dddf`'s `src/` and `migrations/`,
extracted into a scratch root and put first on `PYTHONPATH`, with pytest's
`pythonpath` cleared. All twelve failed there, each for the reported reason:

| Finding | Test | On `d2372dddf` |
|---|---|---|
| F1 | `test_an_inserted_follow_up_is_bound_to_its_own_decision_by_its_presentation` | the interrupt's outcome was `('open', None, None)`, not `taken` by the answer bound to the follow-up's presentation |
| F2 | `test_a_held_teach_back_is_never_summarized` | the held teach-back was summarized (a summary came back, one request sent) |
| F2 | `test_a_summary_leaves_the_card_once_its_grade_is_held_or_regraded` | the summary stayed in the card after a regrade held the grade |
| F3 | `test_the_query_embedding_is_admitted_by_the_daily_guard` | with `max_daily_cost_usd = 0` the embedding provider was still called at each prefetch |
| F3 | `test_the_backfill_dry_runs_and_then_embeds_what_is_missing` | the dry-run report had no money estimate (`KeyError: 'estimate'`) |
| F3 | `test_the_backfill_is_held_to_its_money_cap` | the backfill took no budget at all (`TypeError: unexpected keyword argument 'caps'`) |
| F4 | `test_a_json_repair_is_admitted_as_its_own_request` | two physical requests were sent under one admission |
| F5 | `test_an_unfinished_request_keeps_its_reservation_after_a_restart` | after the restart the Decider was asked three more times: the receipt left `started` counted as $0 |
| F6 | `test_competing_follow_ups_log_only_the_insertions_that_happen` | two `insert_now` rows (`pi_f1a`, `pi_f1b`) for one insertion (`pi_f1b`) |
| F7 | `test_the_llm_rationale_is_shown_only_for_the_option_it_explains` | the rationale for the 0.6 option was shown on the drawn 0.4 option (`shown` was true) |
| F8 | `test_a_follow_up_that_waiting_would_drop_joins_now` | the follow-up waited (the next step was `pi_m1b`) and was never served: the boundary had no room |
| F8 | `test_a_waiting_follow_up_keeps_its_room_until_the_boundary` | the later follow-up took the waiting one's minutes without displacing the tail, so the waiting one could not open the next block |

Two of these were reordered after the first run so the behaviour fails
first: F1's outcome assertion now comes before its presentation-owner
assertion, and F7's `shown` assertion before the new `about` field.

### What changed

**F1. An inserted follow-up binds to its own decision** (`router/outcomes.py`, `daily_plan/records.py`, `daily_plan/engine.py`).

- **The problem.** `_action_attempt` read presentations only for
  `plan_block` decisions. Its session-rule fallback skips attempts bound to
  a presentation, so a follow-up answered through Today left its
  `plan_interrupt` decision `open`, `superseded` or `not_taken`.
- **The receipt.** The follow-up's `item_planned` event already named its
  decision. The plan item now carries it (`PlannedItem.decision_ref`), and
  the follow-up's presentation records that decision as its
  `router_decision_id`.
- **The join.** A `plan_interrupt` decision binds through the presentation
  of its block (from its receipt key) and its chosen item. A block and item
  name exactly one presentation. A `plan_block` decision no longer takes a
  presentation that another decision placed.
- **Versioning.** Only `plan_interrupt` rows change, and those are new at
  `mvp-0.24`, which has not landed. `router_outcomes_v2` therefore keeps its
  version.

**F2. Held grades and regrades** (`daily_plan/router_teach_back.py`).

- **Before summarizing.** `summarize` sends nothing while THE predicate
  (`held_grades.attempt_grade_held`) holds the attempt's grade.
- **Bound to the grade.** Each summary records its attempt's grading
  revision: a fingerprint of the score, the latest blind grade record and
  the live grading evidence. The checkpoint key names the revision
  (`router_teach_back_summary:v1:<attempt>:<revision>`).
- **When gathering.** `summaries_for` drops a summary whose attempt is held
  now (`held_for_review_attempts`) or whose revision is no longer current.
  Any regrade, into a hold or out of one, leaves the old summary out of the
  card. Summarizing the current grade puts a fresh summary in.
- **Not done.** A regrade does not trigger a new summary on its own. The
  only trigger is the teach-back RPC's grading. Until the next summary, the
  card simply has no summary for that attempt.

**F3, F4, F5. Every metered request is admitted in its own start receipt** (`daily_plan/router_runtime.py`, `router_chooser.py`, `router_teach_back.py`, `router_retrieval.py`, `cli/router.py`, `db/stores/model_calls.py`).

- **The guard.** `RouterSpend.metered` wraps every router model call: both
  models, the prefetch's query embedding and the teach-back summary. It
  installs two things:
  - the shared request gate (`ai.execution.gate_model_requests`), which
    prices EACH physical request (a transport retry and a JSON repair
    included) as its input at about 4 bytes per token plus its output room,
    at the route's price (the Decider prices its input only);
  - the receipt observer. In one `BEGIN IMMEDIATE` transaction it checks
    today's guarded receipts plus this request's estimate against
    `router.max_daily_cost_usd`, then writes the start receipt with the
    estimate (`budget_json.router_reserved_usd`). This is the reader quick
    check's pattern, which plan §8.4 named. A refusal raises `SpendRefused`
    before anything is sent, and the model's share goes to the rule
    (`spend`).
- **Restarts and lost finishes (F5).** `receipt_usd` counts a receipt that
  reported no usage at its reservation: still running, its finish lost to a
  crash or a failed write, or failed. Unknown usage is never free. An
  operation's own receipt around its requests carries no reservation and
  counts $0, as before. The in-memory reservation map is gone: the
  reservation is the durable start receipt, so it holds across processes.
- **Retrieval (F3).** The query embedding runs inside the decision's
  metered context. A refusal is a logged `unavailable` with reason `spend`.
- **The backfill (F3).** `learnloop router embed-decisions` now runs
  through the shared embedding backfill (`ops.embedding_backfill`):
  - enforced caps (`--max-cost-usd` 0.25, `--max-calls` 100,
    `--max-tokens` 2,000,000, `--max-candidates` 2,000, `--max-retries` 2,
    `--price-per-million`);
  - a priced dry run;
  - both embedding switches and its lock;
  - receipts owned by `embedding_backfill`.

  It exits non-zero on any status other than `dry_run` or `complete`. The
  CLI help snapshot was regenerated.
- **Tests.**
  - The fakes now send each request through `model_call`, with its usage
    reported, as real providers do, so a refused request never reaches a
    fake.
  - The old guard test (`test_the_daily_guard_counts_todays_router_receipts`)
    was rewritten against `metered`.
  - F4's test uses the production `OpenAIChatProviderClient` with the fake
    SDK.

**F6 and F8. The restraint decides each follow-up against the plan as it stands** (`daily_plan/engine.py`, `router_chooser.py`, `router/plan_log.py`, `daily_plan/records.py`).

- **F6.** `_restrained_followups` decides each placeable follow-up in turn.
  When one joins, its placement (its displaced victims and the follow-up
  itself) is applied to the in-memory plan before the next is considered.
  A single write then logs each decision with exactly the placement it
  describes. If the plan can no longer hold a follow-up, that follow-up is
  not decided (G4) and stays pending.
- **F8: waiting must leave room.**
  - Waiting is offered only when the boundary keeps room for the follow-up
    after the current block (its minutes and, on a re-entry plan, an item
    slot).
  - Otherwise the follow-up joins now, deterministically and with no model
    asked (`decided_by = no_room_to_wait`). The row marks `continue_current`
    infeasible (`detail.wait = {feasible: false, reason:
    "no_room_after_block"}`).
  - The restraint decides now or at the boundary, never whether. VOI
    decides whether.
- **F8: a waiting follow-up keeps its room.**
  - Its estimate is recorded on its `followup_deferred` event
    (`kept_minutes`). Later follow-ups cannot use those minutes; they must
    displace the tail or wait.
  - At the boundary it is placed first, in that room.
  - The fix exposed a second way to lose it: estimates drift during a
    session as answers add latency evidence. In the test,
    the follow-up's estimate grew from 1.525 to 1.72 minutes between its
    deferral and the boundary, which alone would have dropped it. So a
    waiting follow-up is placed at its kept estimate when its current one is
    larger. The plan still never exceeds its budget (asserted).

**F7. The rationale is bound to the block it explains** (`daily_plan/router_chooser.py`).

- **The binding.** The LLM's prompt asks why "the block you favour" is a
  good next step, so the rationale explains the one option the LLM's
  distribution puts the most on (`favoured_option`). With a tie at the top,
  it explains no single option. The record keeps this as
  `rationale.about`.
- **When another block is drawn.** The rationale is hidden (guard
  `another_option`), and the block shows the model label with the computed
  reason. The text stays on the receipt.

## Claims that don't hold

- **"The daily guard bounds metered router spend."** Agreed. F3, F4 and F5
  are fixed above. The guard's dollars are estimates, reconciled from each
  receipt's reported cost or tokens. As in the shared framework, a provider
  that overspends its estimate stops the next request, not its own. The
  OpenRouter key's credit limit remains the backstop.
- **"The follow-up waits and opens the next block."** Agreed. F8 is fixed,
  including the estimate drift the fix exposed.
- **"G3 coverage establishes faithful decision receipts."** Agreed for the
  applied choice: F6 is fixed. G3's arithmetic (the propensity recomputed
  from the row) is unchanged.
- **"Card leakage coverage is complete."** Agreed. F2 is fixed.
- **"The live product configuration passed the live-session gate."**
  Agreed that it did not.
  - **What the record already said.** The stage record described attempt 3's
    scratch override, which switched isolated Codex turns off, and kept the
    failure of the shipped isolated configuration as open question 1.
  - **What was missing.** Neither its summary nor attempt 3 said plainly
    that the shipped configuration had not passed.
  - **The correction.** Attempt 3 in `router-r2bc.md` now says so. The cause
    is an owner fix on this machine: the Codex MCP config's `code-review`
    server rejects the isolated launch's override. The other route is the
    shared Codex provider's isolated launch. This stage changes neither.

## Spec conformance: items noted, not changed

Codex's conformance table raised two gaps that were not filed as findings.
They are left as they are and recorded here so they are not lost:

- **§3.7.** A similar decision is shown as one line: its option count, the
  choice and its chance, and the outcomes. It is not shown as its full
  candidate set.
- **§7.** A rationale's cited answers appear as plain labels in the details
  line, not as links to the attempts.

Both are presentation choices inside R2c's scope. Neither affects what is
logged or replayed.

## Corrections to the stage record

`docs/reviews/router-r2bc.md` now points here. It corrects in place the
statements the fixes changed:

- the spend summary and the runtime's spend bullet;
- deviation 6 (the in-memory reservation, now superseded);
- the restraint's placement and mixture steps;
- the teach-back storage key and the held-grade rule;
- the retrieval embedding and backfill bullet;
- the why's rationale binding;
- attempt 3 of the live session.

## Gate

Both suite runs are on `ea4d8ae84`, whose code equals the last fix commit
`fcb254903` (`ea4d8ae84` adds only the regenerated references).

- **Install:** `uv sync --extra dev --extra mobile` (163 packages) and
  `uv pip install pypdfium2` (5.14.0). `TMPDIR` was the worktree's
  `fixtures-local/tmp`.
- **`uv run lint-imports --no-cache`:** 17 contracts kept, 0 broken.
- **`flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto`:**
  **10883 passed**, 0 failed, 48 warnings (18 min 17 s, after about 14 min
  waiting for the lock). That is the stage's 10872 plus the 11 new tests. It
  ran with `-p no:randomly`, a no-op because pytest-randomly is not
  installed.
- **`flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability`:**
  **100 passed**, 10783 deselected, 1 warning (1 min 46 s).
- **Frontend and `cargo check`:** not required. Nothing under `apps/`
  changed in this fix step (`git diff d2372dddf -- apps` is empty).
- **References:** no schema or config change, but the config reference's
  line citations had moved (`db_validate_reference.py` reported 9 stale
  citations). `db_generate_reference.py` was rerun (`ea4d8ae84`), and
  `db_validate_reference.py` then reported `errors: []`: 321 table notes,
  834 effective config leaves, schema head 202.
- **CLI help snapshot:** regenerated for `router embed-decisions`'s cap
  options (`bf8548737`).
- **Defaults snapshots:** no config default changed. They pass in the
  suite.
- **RPC pins:** no RPC added or changed, so `tests/test_mobile_allowlist.py`
  is unchanged and passes.
- **Targeted runs:**
  - Before the commits, the router, daily-plan, decider, embedding, spend,
    teach-back, CLI-help and mobile-allowlist files: 818 passed and 1
    failure, the CLI help snapshot before its regeneration.
  - Each fix commit's index state was exported and its own files run against
    it. The only failure was `test_mvp024_upgrade.py`'s head-fixture test
    in the F6/F8 check, because the export left out `fixtures/`; it passes
    in the suite.
- **Paid calls:** none.
- **Migration:** none.

## Open questions

1. **Isolated Codex turns on this machine** (the stage record's open
   question 1) still keep the router LLM and the teach-back summaries from
   answering here. This is the owner's machine fix or the shared Codex
   provider's isolated launch.
2. **The decision backfill now needs `embedding.backfill_enabled`** as well
   as `embedding.enabled`, like every other embedding backfill. The owner's
   copies set both (the stage's live session did), so nothing changes
   there.
3. **A regraded teach-back is not re-summarized automatically.** Its old
   summary leaves the card; a new one is made only by a later `summarize`
   call. Recommended: accept, since a regrade is rare and the card stays
   honest. Otherwise, hook the summary into the regrade paths in a later
   stage.
