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

## 2. What changed

Commits, in order (each in this worktree, on `refactor/e2-choice-pure`):

1. `6a6cc9e6ed`: step 0 (§1).
2. `04fbf6582f`: `provenance.ref`, the id rule every decision record uses (an id, or a 16-hex hash of one that isn't
   a code), moved from `daily_plan/boundary_records.py`, which imports it, so `boundary_records.ref` still works.
   The core lives under `router_objective`, which may not import `daily_plan` ("a leaf consumer: nothing in the
   domain below imports it"), and it builds its own record. The body is the old one with `provenance.is_code` read
   as the module's own `is_code`.
3. `2bc640bf05`: the split.
   - **`router_objective/choose.py`** (new, 264 lines): `OptionFacts`, `ChoiceInputs`, `Choice`, `choose`, two read
     predicates for the coin (`coin_reads_minutes`, `coin_applies`) and `_with_record`. Its imports are the mix,
     the stop coin, `router.why`, `router.mixture` and `provenance`, none of them in an import cycle (§5, P3).
     The mix's and the coin's functions are called through their modules (`mix.draw`, `SC.flip`), so the tests
     that replace `mix.draw` (the ih2 `draw` fixture, `te3b_offers_helpers.offer_drawn`, `test_router_failure_records`)
     still reach the served draw.
   - **`ObjectiveChooser._decide_objective`** (169 to 141 lines): the reads, in their old order and under their old
     conditions, into `ChoiceInputs`; `C.choose(...)`; then the trace (`_trace` and the fields after it), the router's
     record and the `BlockChoice`, all from the `Choice`. The numeric answer's resolution (final, or the F1
     publication) moved unchanged into `_numeric_answer`; `_option_facts` reads a candidate's reason code, topic and
     section for the rule sentence (the reads `router_chooser._rule_sentence` makes). `MODE` and `WHY_VERSION` now
     come from `choose.py`, whose copy they version; `objective_chooser.MODE` and `.WHY_VERSION` keep their names.
   - **`BlockChoice.decision_record`** (`daily_plan/types.py`): the core's record rides on the choice
     (`compare=False`, like `router_record` and `provenance`, so no equality between choices moves).
   - **`boundary_records.plan_block_records`**: the decision's part of the record comes from the choice's own
     record when the choice carries one, is not a fallback and names the same chosen ref; otherwise from
     `_derived_part`, the old derivation from the chooser's record dict (staged, the R2 mixture, every fallback),
     moved out unchanged. The container's part (the block, the router row, the trace, parent, created time, feasible
     and infeasible alternatives, waits, `card_error`, forced items, the offer it supersedes, a crash's type and
     place) is added once, for both.
4. `5704038e61`: the tests (§6).
5. `681f26b223`: this record (first part), the vault's router note (Concepts/Scheduling and Selection, "The daily
   plan's block router": how the choice is made now), the status row, and the ledger's SR-1 pointer to where the
   guard is decided now (its row is otherwise untouched).
6. `bc5e38eb0b`: the generated references.
7. `1f7aff8730`: comments and docstrings only. The touched comments no longer name a ruling or a finding, and the
   structure golden is lowered: stage-naming comment lines 2,370 to 2,368, 38 to 36 in `objective_chooser.py`.
8. `cd6f8edd88`: the references regenerated after 7, which moved line numbers. A second run changed nothing.
9. This record's proofs and results.

`daily_plan/plan_records.py` is unchanged: it builds the restraint gate's record, and nothing of this method's was
there. The plan_block record's builder is `boundary_records.py`; what moved out of it is the decision's own part for
objective decisions, now built by the core, while the derivation stays for the choosers that have no core.

| File | Base | Tip |
|---|---|---|
| `daily_plan/objective_chooser.py` | 2,224 | 2,231 |
| `_decide_objective` | 169 | 141 (+ `_numeric_answer` 24, `_option_facts` 6) |
| `router_objective/choose.py` | — | 264 (`choose` 59, `_with_record` 37, `ChoiceInputs` 38, `Choice` 38) |
| `daily_plan/boundary_records.py` | 322 | 336 (`plan_block_records` 104 to 85, `_derived_part` 44) |
| `daily_plan/plan_records.py` | 280 | 280 |
| `provenance.py` | 468 | 481 |
| `daily_plan/types.py` | 251 | 255 |

`objective_chooser.py` grows by 7 lines: the decision's ~45 lines left, and the inputs' construction (14 lines), the
method's docstring and the two helpers' docstrings came in. What remains of `_decide_objective` past the call is the
trace and the router's record (about 85 lines), E4's.

## 3. The two dataclasses

**`ChoiceInputs`**, every field and where the shell reads it:

| Field | From |
|---|---|
| `support`, `staged_ref` | `choose`'s support and staged's ref (§1 a-e) |
| `options` | per support candidate, its `reason_code`, `topic`, `section` annotations (`_option_facts`); stop has none |
| `llm_status` | the LLM component's result status (`entry.results()`, or `not_ready` with its readiness reason) |
| `llm_distribution`, `rationale`, `cited` | the parsed `ParsedPolicy` when the LLM answered and parsed, else None, None, () |
| `card_evidence_ids` | `material["policy_card"]["evidence_ids"]` (the LLM card the prefetch built) |
| `numeric_status`, `numeric_choice` | the served numeric answer (`_numeric_answer`, then `_with_carried`); None, None with no answer at all |
| `w` | `current_weight(repository, config, at=now_iso)` |
| `to_other_policy` | `failure_share_to_other_policy_on(config)` |
| `epsilon` | `router_settings(config)["epsilon_min"]` |
| `seed` | `self._seed(entry.key, decision_id)` after `new_ulid()` (`runtime.seed`, else `mix.seed_for`, looked up at call time) |
| `stop_rate` | `stop_coin_rate(config)` |
| `session_minutes` | `_session_minutes(now_iso)` when `coin_reads_minutes(rate, support)`, else None |
| `availability` | `{**_availability(state, numeric), "session_minutes": ...}` when `coin_applies(rate, support, minutes)`, else None |
| `staged_why` | staged's own `why` |
| `no_models` | the entry is `_NoModels` (the no-model branch) |
| `boundary_key`, `algorithm_version`, `question_set_version`, `llm_schema_version` | `entry.key`, `config.algorithms.algorithm_version`, `material["policy_request"].question_set_version`, `rq.LLM_POLICY_SCHEMA` (the record's facts and versions) |

**`Choice`**, every field and where the shell writes it:

| Field | Written to |
|---|---|
| `failed`, `effective`, `components`, `numeric_choice` | `mixture.failed`, `mixture.effective_weights`, `mixture_weights.effective`, the trace's `mixing.effective`, `model_distributions.numeric`, `mixture.numeric_choice` |
| `drawn` | `mixture.drawn_component`, `u1`, `u2`, `pi` (the mix's μ), `drawn_component`; the trace's `mixing` |
| `coin` | `mixture.stop_coin`, the trace's `stop_coin`, `mixing.drawn_chosen`, the score note when its arm is not `policy` |
| `served`, `propensity` | `BlockChoice.candidate_id`, `.propensity`; `mixture.served` and the trace's `mixing.chosen` under a coin |
| `pi` | `mixture.pi` under a coin (the served distribution); without one it equals `drawn.pi` |
| `rule_code`, `rule` | `why_code` (`rule_code or None`); `rule` enters the why |
| `favoured`, `guard`, `shown`, `rationale_hidden`, `evidence_labels` | `mixture.rationale.about`, `.guard`, `.shown`; `rationale_hidden`; `evidence_labels` |
| `why`, `why_kind` | `BlockChoice.why` (staged's when the mix's is empty), `.why_kind` |
| `decided_by`, `fallback`, `fallback_reasons` | the router's record |
| `assignments` | `ro5_assignments` (the coin's pending `policy_experiment_assignments` row) |
| `record` | `BlockChoice.decision_record`, completed and written by the engine |

## 4. Reads: none hoisted

No read moved ahead of a decision. Every read the method made is made at the same point relative to the others and
under the same condition: the results, the wall time, the published and carried answers, `current_weight`, the id,
the carry registration, the seed, the session's minutes (when the rate is positive and stop is in the support) and
the availability (when the coin applies), then, after the call, `_carried_for` and the waited-ms clock. The two
coin predicates are the conditions the method tested inline before, now named in `choose.py` so the core and the
shell ask the same question (`choose` flips the coin under `coin_applies` too). The decision path's cost is
therefore unchanged by construction, and measured in §7 (P1): connection opens and statements on the deciding
thread during `_decide_objective`, equal at the base and the tip on every scenario.

## 5. What keeps each KEEP item, and its test

| Kept | How | Pinned by |
|---|---|---|
| IH5's failure share | `mix.effective_weights(w, failed, to_other_policy=...)`, called by the core with the switch as it serves | `tests/test_ih5_successor.py` (the table of weights, exact propensities, the real chooser's logged rule, switch off = predecessor); `tests/test_choose.py` (four failure cases with literals) |
| IH2's contest | the support (`[contest]` plus the offer) and staged's ref are built before the call, as before; the trace's `followup_contest` after it | `tests/test_ih2_lessons_compete.py`, `tests/test_why_cases.py` case 2; P-draw `contest` |
| Exact propensities | `1.0` for a deterministic draw, else its propensity; under the coin its served propensity and the served distribution as `mixture.pi`, the mix's μ as `mix_pi` | `tests/test_ih5_successor.py::test_the_floor_is_kept_and_propensities_are_exact_in_every_row`, `ih2_lessons_compete_helpers._assert_exact_mu` (used across IH2's file), `tests/test_ro5_stop_coin.py::test_serving_records_each_coin_with_its_exact_probability_and_availability`; `tests/test_choose.py` |
| RO5's coin order | `mix.draw` (uniforms `component`, `candidate`), then `SC.flip` (its own `stop_coin`, `stop_coin_next`), the availability read before | `tests/test_ro5_stop_coin.py::test_the_coin_never_depends_on_the_mix_or_either_policy`, `tests/test_ro5_landing.py::test_r4_the_coin_is_not_drawn_before_any_active_minute_of_the_session`; `tests/test_choose.py::test_the_coin_draws_after_the_mix_on_its_own_uniform_and_leaves_the_mixs_draw_alone` |
| The seeds and what each depends on | the mix's seed is still `runtime.seed` or `mix.seed_for(boundary_key, decision_id)` in the shell; the numeric seed (`numeric_seed(identity)`) is untouched; the core takes the seed as a value | `tests/pinned_draws.py`'s wrappers (they wrap `mix.seed_for` and `numeric_seed`, still looked up at call time), `tests/test_rospeed2_connections.py`, `tests/test_ih_lesson_candidate_after_cold_miss.py`; P-draw |
| The served decision at fixed seeds | as above | the pinned-draw router files in §6's run; P-draw, every scenario |
| Every logged row and trace field | the router's record and the trace are written from the `Choice` with the old keys in the old order (the coin's keys added after, `pi` replaced in place) | P-draw (every table, byte-equal after normalization); `tests/test_ro4_objective_serving.py`, `tests/test_ro6_serving.py`, `tests/test_router_failure_records.py` |
| The rationale guard's rules | `router_why.rationale_guard` unchanged, called by the core with the same arguments; `absent`, `another_option` and the coin's withdrawal as before. SR-1 is not touched (its pointer in the ledger now names `choose.py`) | `tests/test_router_r2b_serving.py::test_the_rationale_guard`, `::test_the_llm_rationale_is_shown_only_for_the_option_it_explains`; `tests/test_choose.py` (each verdict) |

## 6. Tests added

- **`tests/test_choose.py`** (23 tests, no vault): the statuses it compares are the runtime's; one per rule code
  (`stop_offer`, a block's own code and sentence, no code: no rule and staged's why); IH5 (LLM failed with the switch
  on and off, numeric choice outside the support, both failed with a missing answer as `not_ready`); the propensities
  (μ and the draw's propensity, the alternatives' `p`, a one-hot mix served at 1.0); the coin (drawn after the mix on
  its own uniform, the mix's draw unchanged by it, the served distribution, the assignment row; an offered stop shows
  no model's words; the opening boundary; missing availability refused); the guard (shown with evidence, each refusal:
  `jargon`, `unknown_evidence`, `too_long`, `probability`, `empty`, `absent`; `another_option`); the record's fields;
  and the core reaching no database, clock or id stream and leaving its inputs alone. Seeds that land a draw where a
  test needs it are found by trying seeds, never by patching the draw.
- **`tests/test_objective_decision_record.py`** (2): a plan journey (both models with the coin at 0.45; no model),
  every `plan_block_records` call made twice, with the core's record and with it taken away: the records are equal
  field for field but their ids. Fail-first: with the core's `option_count` off by one, both fail.
- **`tests/test_why_cases.py`** gains `test_the_objective_choice_names_its_rule_code` (4 cases, L6): `stop_offer`,
  a repair block's `repair_open_problem`, a maintain block's `review`, a lesson offer's `lesson_offer`, each staged
  through the real plan with the ih2 `draw` fixture and read from `why --json` alone (status, rule, why version,
  seed, the support's alternatives with their probabilities). Helper: `why_cases_helpers.stage_rule_case`.
- **Ported:** none. No test patched or read the source of a name this step moved (`current_weight`, `new_ulid`,
  `_rule_sentence`, `rationale_guard` and `mix.draw` are still reached where the tests reach them; the ones that
  patch `OC._hash`, `OC._latest_attempt`, `OC.run_numeric`, `OC._drain_carry`, `OC._await`, `ObjectiveChooser._defer_carry`
  patch names the shell keeps). No assertion changed.

## 7. Proofs

**P1. P-draw.** The harness of `docs/reviews/router-speed2.md` ("Identity") is not in the repository (I2 found the
same), so it was rebuilt from that description as a scratch script (`pdraw.py` in the step's scratch directory). It
runs on synthetic vaults, not the owner's copies (see §9). Each run:

- a plan journey on the wide vault (`router_mixture_helpers.mixture_env`) at the head tag, the objective serving,
  with fake models (`router_model_fakes`);
- every seed pinned (`tests/pinned_draws.py`: the mix's, the numeric policy's, picks, the check day, lessons) and one
  batch of numeric draws, so the draw count is fixed;
- the shared ULID stream and the records' stream seeded, so every draw seeded on a fresh id repeats;
- each served item answered and the feedback prefetch run, as the desktop does.

After each run it dumps every table of the vault's database, every LLM request's prompt, every Decider call's state
and questions, and `learnloop why <trace> --json`. The code under test is the base's (a `git archive` of
`931c8d072e`'s `src/`, `tests/` and `migrations/`) or the branch's at `5704038e61` (the later source commit,
`1f7aff8730`, changes comments and docstrings only).

Before comparing, these were normalized: ULIDs, UUIDs, 32- and 64-hex digests and `sha256:` short refs (numbered by
first appearance); wall-clock stamps from the real date; keys ending in `_ms` (latencies, waits, the residual fit's
`fit_ms`); the code stamp (`git:<commit>` against the archive's `package:0.1.0`) and the two blob sizes it changes.
Compressed state blobs (`*_z`) were compared by their decompressed content.

Two base runs of `both` agree byte for byte, so the normalization leaves nothing that varies by run. Base and branch
then agree byte for byte on all nine scenarios (26 runs):

| Scenario | Runs | What it reaches |
|---|---|---|
| `both` | 3 | both models answering (`policy_answer`); llm, numeric and uniform components; coin arms `policy`, `present_next`; guard shown and `another_option` |
| `coin` | 6 | `stop_coin = 0.45`: `offer_stop`, `present_next`, `policy`; `stop_offer` rule codes |
| `llm_fails` | 3 | the LLM raising; IH5 on: numeric takes the mix (`fallback = llm`), coin arms all three |
| `llm_fails_ih5_off` | 3 | the same with `failure_share_to_other_policy = false`: staged takes the share |
| `no_models` | 3 | no model set up: `objective_no_models`, the carried valuation's thread (joined, as `router_mixture_helpers.join_carried_valuations` does) |
| `guard` | 3 | a rationale with internal terms and an id not on the card: `jargon` |
| `evidence` | 3 | a rationale citing an id on the card: shown, with its evidence label |
| `offers` | 3 | TE1b's candidates pinned (`te3b_offers_helpers._candidates`): lesson offers in the support, `lesson_offer` codes |
| `contest` | 2 | IH2: an open offer, then a probe made ready while it waits (`ih2_lessons_compete_helpers._open_offer`, `_ready_probe`): the contest's support and `repair_followup` |

Rule codes seen across them: `stop_offer`, `repair_open_problem`, `repair_followup`, `review`, `new_material`,
`goal_step`, `lesson_offer`. Not reached by the harness: both policies failed at once, and a numeric policy that
failed. `tests/test_choose.py` covers both with literals, and `tests/test_ih5_successor.py` covers them in the
chooser.

**Decision-path cost.** In the same runs, connection opens and statements on the deciding thread while
`_decide_objective` ran (another thread's, such as the carried valuation's, not counted). The counts are equal at
the base and the tip:

| Scenario | Decisions | Opens | Statements |
|---|---|---|---|
| both | 13 | 57 | 436 |
| coin | 11 | 44 | 352 |
| llm_fails | 13 | 57 | 436 |
| llm_fails_ih5_off | 13 | 55 | 428 |
| no_models | 16 | 74 | 552 |
| guard | 8 | 34 | 264 |
| evidence | 12 | 52 | 400 |
| offers | 13 | 55 | 428 |
| contest | 6 | 20 | 168 |

**P2. The pinned draws and the router's goldens.** None regenerated; no golden file or pin changed in the diff.
They ran unchanged in §8's targeted runs: `tests/pinned_draws.py`'s wrappers (installed by `conftest.py` for every
test); the router mixture, objective and lesson files that read them; the ih2 `draw` fixture's users
(`test_ih2_lessons_compete.py`, `test_why_cases.py`); `test_ro4_objective_serving.py`, `test_ro5_stop_coin.py`,
`test_ro5_landing.py`, `test_ro6_serving.py`, `test_ih5_successor.py`, `test_router_failure_records.py` (plan log
rows, traces, why sentences, decision records); `test_due_queue_golden.py` (the due queue's goldens, reached through
`types.py`).

**P3. Identity pins and the structure ratchet.** `tests/test_identity_pins.py` passes with nothing written (§8). Import
cycles, measured with untracked files included (`scripts/refactor_measures.py`'s sweep over tracked plus untracked
source): the largest component is 84 → 84, modules in any cycle 220 → 220, and both member lists are identical.
`router_objective.choose` is in no cycle; its imports are `provenance`, `router.mixture`, `router.why`,
`router_objective.mix` and `router_objective.stop_coin`, none of which is in one either. `tests/test_structure_ratchets.py`:
§8.

**P4. P-shadow: not required.** Replay and rebuild (`substrate/replay.py`, `substrate/rebuild_orchestrator.py`, the
replayers and `ops/upgrades.py`) import none of the changed modules: `objective_chooser`, `router_objective.choose`,
`boundary_records`, `provenance` or `daily_plan.types`. What replay reads of the router is `router_decisions` and the
outcome rows (the `router_outcomes` replayer), whose bytes P1 shows unchanged. `decision_records` is a RECEIPT nothing
replays. The step touched nothing replay reads.

**P5. Decision records.** In every P1 run, the `decision_records` table (every `plan_block`, `model_answer` and
other record, field for field) and the `why <trace> --json` output are byte-equal after normalization between base
and tip. `tests/test_objective_decision_record.py` checks the same in the suite: on every boundary of two journeys,
the record written from the core equals the container's own derivation.

## 8. Targeted gate

All through the scratch directory's `t.sh`, one command at a time, `-m "not arc_close" -n 3`, inside a 5 GB memory
scope.

| Selection | Files | Result |
|---|---|---|
| The gate's own files: `test_identity_pins`, `test_retired_config_identities`, `test_architecture`, `test_test_layout`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_structure_ratchets`, `test_public_tip_guards`, and the three added or edited (`test_choose`, `test_objective_decision_record`, `test_why_cases`) | 11 | 468 passed (at the final tip, after the comment commit; also before it) |
| Every `tests/test_*.py` naming `objective_chooser`, `ObjectiveChooser`, `router_objective.mix` (or importing `mix` from it), `stop_coin`, `plan_records`, `rationale_guard`, `boundary_records` or `choose` | 52 | 856 passed, 3 skipped |
| The rest of `scripts/affected_tests.py --base 931c8d072e` over the diff (869 files; `provenance.py` and `daily_plan/types.py` reach most of the suite), in 14 chunks of at most 60 | 815 | 14,012 passed, 45 skipped, 5 xfailed, 0 failed |

- `tests/test_identity_pins.py` passes with nothing written. `tests/test_structure_ratchets.py` passes; its golden
  was lowered with `--write` (stage-naming comments 2,370 to 2,368). Functions over 200 lines: 71, unchanged.
  The largest import component: 84, unchanged.
- `lint-imports --no-cache`: 43 kept, 0 broken. `ruff check`: all checks passed.
- The four vault validators pass (`db_validate_reference`: no errors; `desktop_validate`, `module_validate` and
  `validate_vault`: pass). `scripts/check_gate_partition.py`: 31,103 collected, landing 31,038 + arc_close 65.
- The references were regenerated after the source commits, and again after the comment commit. A further run
  changed nothing.
- Fail-first for the added tests: with the core's `option_count` off by one, both cases of
  `test_objective_decision_record.py` fail. The new module's own tests cannot fail at the base, because the module
  does not exist there. Their seeds are found by search, not patched.

## 9. Judgment calls, observations, and what E3 and E4 should know

**Judgment calls.**

1. **The record is built in two places, on purpose.** The core builds its decision's part directly from its
   values. `boundary_records._derived_part` still derives the same part from the chooser's record dict, because
   staged, the R2 mixture and every fallback have no core. The container's part is shared. The two derivations
   must agree on objective decisions; `tests/test_objective_decision_record.py` holds them equal on real journeys,
   and P1/P5 hold the written records byte-equal. When the R2 mixture leaves (or gets a core), `_derived_part`
   shrinks to fallbacks.
2. **`provenance.ref` moved out of `boundary_records`** so the core, which may not import `daily_plan`, builds ids
   by the same rule. `boundary_records` imports it, so its name is kept.
3. **The carry registration (`_defer_carry`) stays before the call.** It is a write (the process-wide carry
   list, and a thread with no models), but it needs only the served answer and the decision id, the choice never
   reads what it changes, and keeping its place keeps what a choice that raises leaves behind exactly as today.
   Moving it after the call would read more cleanly; E3, which owns the carry, can make that move.
4. **The restraint gate's `_mixed` is not on the core.** It draws the same mix with no coin, a different staged
   ref, its own LLM parse per schema, its own why (`FOLLOWUP_WAITS`, or an offer's guarded why over the card's
   evidence) and its own record (`plan_records.plan_interrupt`). The brief names `_decide_objective`. Putting
   `_mixed` on `choose` needs a second mode in the core, or a smaller shared core (failure share, weights, draw)
   that both call. That is a later step's decision.
5. **Two named predicates for the coin's reads** (`coin_reads_minutes`, `coin_applies`) rather than reading the
   availability ahead. That is the second pure stage step 0 allowed, and it adds no query. `choose` flips the coin
   under the same `coin_applies`, so the shell and the core cannot disagree about whether the availability was
   needed. If they ever did, the core refuses: `ValueError`.

**Observation (no ledger row).** `effective_weights` and `components` used to run before the decision's id was
minted and its carry registered. They now run inside the call, after both. They can raise only on inputs the
configuration and the support already rule out: `w` outside [0, 1], or staged's ref outside the support. So the
only path where this order is visible is one that does not occur. `mix.draw`, whose raise `test_router_failure_records`
plants, was already after both, and still is.

**For E3 (job control and the clock).** The `_NoModels` name check now feeds one input (`ChoiceInputs.no_models`),
and `_defer_carry` keeps its own copy. `_numeric_answer` (the final answer or the early publication) is job-side and
belongs in `objective_job.py`. The shell's clock reads are `wall_now()` (`results_at`) before the call and
`runtime.clock()` (`waited_ms`) after it. Neither reaches `choose`. The mix's seed is still minted in the shell
(`new_ulid` then `_seed`), so E3's seed module can produce it without touching the core.

**For E4 (trace assembly).** After the call, the shell builds the trace (`_trace`, `learner_statements`,
`followup_contest`, `goal_dates`, `carried_for`, the coin's trace fields and the score note) and the router's record
dict from `Choice` fields only: `drawn`, `coin`, `served`, `effective`, `failed`, `numeric_choice`, `components`,
`guard`, `shown`, `favoured`. `_carried_for` is the one read in the write phase. It reads the carry list and
`router_objective_traces`, and only the trace uses it. The record dict's key order is what the router's ledger
stores, so its writer keeps it.

## 10. Not verified

- **The owner's copies.** P-draw ran on synthetic vaults, not on the three owner copies `router-speed2.md` used.
  Building that harness on the copies (a real journey per copy with fake models) was more than this step's budget.
  The synthetic scenarios do reach every component, every coin arm, the failure-share switch both ways, no models,
  the guard's shown and refused paths, offers and IH2's contest.
- **The whole suite, durability, `--fresh-connections` and `arc_close`**: the orchestrator's gate.
- **The restraint gate's paths** (`_mixed`): unchanged code, run only by the targeted files that reach it.
- **Both policies failing together, and a numeric policy that failed**, were not reached by the P-draw scenarios.
  `tests/test_choose.py` and `tests/test_ih5_successor.py` cover them.
