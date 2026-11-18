# Refactor E2: the choice, pure

Branch `refactor/e2-choice-pure`, based on main `931c8d072e`. Step E2 of arc E (`docs/specs/refactor_strategy_v3.md`
§2.7, finding F1). Structure track: no served or persisted value changes. Line numbers in §1 are at the base, in
`src/learnloop/daily_plan/objective_chooser.py` unless another file is named.

## 1. Step 0: the method at the base

The strategy's `objective_chooser.py:1331-1490` is, at this tip, `ObjectiveChooser._decide_objective`
(`:1544-1712`, 169 lines), entered from `ObjectiveChooser.choose` (`:1374-1470`) through `decided()` (`:1462`), which
first runs `RouterChooser._freeze_objective` (`router_chooser.py:480`, a read: `data_capture.objectives.freeze`).
Key: **R** read (database, clock, job results, process state), **C** computation that decides nothing, **D** a
decision, **M** an id mint, **W** a write (rows, process state, a thread).

### `choose` (`:1374-1470`): what reaches the decision

| # | Lines | What | Kind |
|---|---|---|---|
| a | 1378-1383 | the boundary's lesson offer taken out of `feasible`; IH2's contest (a candidate annotated `FOLLOWUP_CONTEST_NOTE`); `StagedChooser.choose` | C |
| b | 1384-1388 | `router_settings(config)`; the record starts as staged's record plus `mode`, `why_version` | C |
| c | 1390-1403 | deterministic exits: `single_option`, `irreversible` (staged's choice, `policy = staged_v1`; the card is built, `_build_card`) | D (before the mix; not this step's) |
| d | 1399-1409 | the support: `[contest]` or `support_order(... k, stop_offered=True, ties_only)`; the offer inserted before stop | D (before the mix; not this step's) |
| e | 1412-1413 | `staged_ref`: the contest, stop when `minutes_left < STOP_OFFER_MINUTES`, else staged's pick | D (before the mix; an input to it) |
| f | 1414-1433 | readiness (`runtime.readiness`), the boundary identity: `_latest_attempt` (R `practice_attempts`), `_preference_mark` (R preferences), `_miss_cause_mark` (R miss sensor and ledgers), `objective_settings`; `key = _hash(identity)`, `seed = numeric_seed(identity)` | R, C |
| g | 1435-1461 | job control: `start_only` (start and raise `DecisionPending`), `runtime.lookup`/`_start_objective`/`_await` (models and the numeric job on threads), or the no-model branch: `run_numeric` on this thread and `_NoModels` | R, W (threads) |
| h | 1462-1470 | `_noting(entry, decided, ...)`: a raise inside notes the models' results on the exception | C |

a-h are job control and the support (E3's ground and the staged frame's); they end before any draw. The step
leaves them in place.

### `_decide_objective` (`:1544-1712`)

| # | Lines | What | Kind | Depends on |
|---|---|---|---|---|
| 1 | 1548-1555 | `entry.results()` (the job's component results, under its lock); `results_at = wall_now()`; a missing Decider or LLM result filled as `not_ready` with the readiness reason | R job, R wall clock | — |
| 2 | 1556-1574 | which numeric answer serves: the no-model branch's (`material["numeric"]`), the job's final one, or (F1) its earlier publication `material[PUBLISHED]` (read under the lock) labelled `published_uncorrected`, which also rewrites `results[NUMERIC]`; else a status-only `NumericPolicy` | R job material, C | 1 |
| 3 | 1575 | `_with_carried`: the residual's carried valuation if the job has it (`material[CARRIED]`, under the lock), else `not_before_the_serve` | R job material, C | 2 |
| 4 | 1576-1580 | the LLM policy's distribution (answered and parsed, else None); `numeric_ok` (answered and its choice in the support); `failed` | D | 1-3 |
| 5 | 1581 | `current_weight(repository, config, at=now_iso)`: `policy_experiment_assignments`, `scores.scores` (traces, assignments, outcomes) or `store.traces`; `W.posterior`, `W.weight` | R database | inputs only |
| 6 | 1582-1585 | `failure_share_to_other_policy_on(config)`; `mix.effective_weights` (IH5's failure share); `mix.components` | D | 4, 5 |
| 7 | 1586 | `decision_id = new_ulid()` (the shared id stream: it seeds the draw) | M | — |
| 8 | 1587-1589 | `_carry_on(config)`; `_defer_carry(numeric, entry, decision_id)`: registers the served answer's carried valuation in the process-wide `_CARRY` list and, for a no-model decision, starts the `learnloop-objective-carried` thread; relabels the residual's `deferred_to` | W process state, W thread, C | 3, 7 |
| 9 | 1590 | `seed = self._seed(entry.key, decision_id)` (`runtime.seed` or `mix.seed_for`, looked up at call time, which `tests/pinned_draws.py` wraps) | C | 7 |
| 10 | 1591 | `mix.draw(support, parts, effective, epsilon_min, seed)`: uniforms `component`, `candidate` | D (seeded) | 6, 9 |
| 11 | 1594-1598 | `rate = stop_coin_rate(config)`; `coin_minutes = _session_minutes(now_iso)` when `rate > 0` and stop is in the support (`price.session_active_minutes`: `practice_attempts`, lessons) | R database | config, support |
| 12 | 1599-1601 | when `rate > 0 and SC.eligible(support, session_minutes=coin_minutes)`: `_availability(state, numeric)` (R `router_objective_session_receipts`, only with a session), then `SC.flip` on its own uniform `stop_coin` (and `stop_coin_next`) after the mix's | R database, D | **11** (and 3 for the numeric inputs it records) |
| 13 | 1602-1604 | the served ref (the coin's, else the draw's); the rule code and sentence: the served candidate's `reason_code` annotation through `router_why.sentence` (`router_chooser._rule_sentence`), or `stop_offer` for stop | D | 10, 12 |
| 14 | 1605 | `titles` (the vault's LOs, in memory) | C | — |
| 15 | 1606-1619 | rationale and cited ids (only with the LLM's distribution); `favoured`; `router_why.rationale_guard` over the LLM card's evidence ids (`material["policy_card"]`), `absent` with no rationale, `another_option` when the LLM component drew something it did not favour; `shown`, withdrawn when the coin overrode the draw; `router_why.objective_why` | D | 4, 10, 12, 13 |
| 16 | 1620-1624 | the session guard's minutes for the trace (`price.guard_minutes`) | C | 3 |
| 17 | 1625-1639 | `_trace(...)`; `learner_statements`, `followup_contest`, `goal_dates` | C | all |
| 18 | 1640-1645 | `_carried_for(repository, decision_id)`: `_CARRY` and `router_objective_traces` (which carriers were written); marks this decision a carrier | R process state, R database, W process state | 7, 8 |
| 19 | 1646-1654 | with a coin: the trace's `mixing` (served, its propensity), `stop_coin`, the score note; the pending `stop_coin` assignment row | C | 12 |
| 20 | 1655-1694 | the router's record (`record.update`): policy, `decided_by` (`objective`, or `objective_no_models` for `_NoModels`), decision id, seed, `why_code`, the mixture (incl. `waited_ms` from `runtime.clock()`), weights, distributions, model ids, latency, cost, payloads, the trace, the card fields | C, R clock | all |
| 21 | 1695 | `seen(entry, ...)`: the prefetch trace, `results_at`, `may_defer` | C | 1 |
| 22 | 1696-1712 | `BlockChoice`: with a coin, the record's `pi` is the served distribution, `mix_pi` the mix's, `stop_coin`, `served`, `ro5_assignments`; the propensity the coin's served propensity, else `1.0` when the draw is deterministic, else its propensity | C | all |

**What the method writes.** No row: its record and trace ride on `BlockChoice.router_record` to the `plan_block`
logger, and the engine writes the decision records. Process state only: 8 (the carry registry and its thread) and
18 (this decision as a carrier).

**Reads that depend on an earlier decision.** None depends on the draw (10), the coin (12) or anything after them.
Two reads wait on something before the decision:

- 11 (the session's minutes) on the config and the support: inputs.
- 12's availability read on 11's value through `SC.eligible` (stop beside a block, and minutes above zero): a pure
  predicate over a read. Read unconditionally, it would add a connection and two statements at every session's
  opening boundary with a session; kept behind the predicate, it is a second pure call between two reads.

5 depends on nothing decided; 18 runs after the decision and feeds only the trace (E4's assembly). So the choice is
**two pure stages**: the coin's eligibility (one predicate), then everything else. That is within the brief's limit,
so the step continues.

**Order the shell keeps.** 1, 2, 3, 5, 7, 8, 9, 11, 12's read, then the call, then 14 and 16-22 with 18's read. 8 is a
write that needs only 3 and 7 and that the choice never reads; it stays before the call, where it is today, so a
choice that raises after it still leaves the registration it leaves today (§8).

**Values the decision needs** (`ChoiceInputs`): the support and staged's ref; per support option, its reason code,
topic and section; the LLM policy's status, distribution, rationale and cited ids, and the evidence ids on its card;
the numeric policy's status and choice; `w`; the failure-share switch; `epsilon_min`; the mix's seed; the coin's rate,
the session's minutes and the availability; staged's own why; whether models were asked; and, for its record, the
boundary key, the algorithm version, the question set and the LLM schema.

**Rule codes it can return** (`why_code`): `stop_offer` when stop is served; otherwise the served candidate's
`reason_code` as the staged frame or the boundary set it (`router_why.SENTENCES`' keys for a block, `lesson_offer`
for an offer, the follow-ups' code for IH2's contest), or none when the candidate carries no code. The why's kinds:
`computed`, `model_written`, `model_no_rationale`; the guard's verdicts: `absent`, `empty`, `too_long`, `jargon`,
`probability`, `unknown_evidence`, `another_option`, or none.

**Where the decision record is built today.** `daily_plan/boundary_records.py`, `plan_block_records` (`:149-252`),
called by `engine._write_boundary_records` (`engine.py:2760`) in the block's transaction, from `engine.Decision`: it
derives the decision's own fields (status, chosen ref, `decided_by`, rule, the support's alternatives with their
probabilities, propensity, drawn component, mix fallback, option count, boundary key, versions and seed) from the
chooser's record dict, and adds what only the container knows (the block, the router row, the trace, parent,
feasible and infeasible alternatives, waits, forced items, the offer it supersedes). `daily_plan/plan_records.py`
builds the restraint gate's `plan_interrupt` record (`engine.py:4930`), not this method's.

**Outside this method.** `ObjectiveRestraintGate._mixed` (`:1845-1960`) draws the same mix for mid-block follow-ups,
with no coin, its own why and its own record (`plan_records.plan_interrupt`). The brief names this method; `_mixed`
stays as it is (§8).
