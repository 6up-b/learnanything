# G2b. The router decides: steps 4 and 5 (the successor evaluator, unserved; the comparison report)

Branch `refactor/g2b-successor-evaluator`, on `refactor/g2-router-decides` at `efeb21f171` (steps 1 to 3,
[`refactor-g2a.md`](refactor-g2a.md)), main `0f309a8687`. Steps 4 and 5 of the design's §4
([`refactor-g2-design.md`](refactor-g2-design.md)). Nothing served changes: no decision, draw, seed, trace, stored value
or prompt byte. Nothing under `src` calls the new evaluator (a test scans for it). The behaviour step (6, `mvp-0.62`) is
not started. [Strategy §2.10, G2](../specs/refactor_strategy_v3.md#210-arc-g-one-decider-one-record-of-each-fact-one-belief-one-protection)

## Commits

| Commit | Step | What |
|---|---|---|
| `d642135954` | 4, tests first | `tests/test_diagnostic_probe_value.py` and the kinds test's payload case; they fail on import here |
| `ca5328185e` | 4 | `diagnostic_payload.py`; `Action.diagnostic`; the rollouts refuse a payload |
| `1df93873bb` | 4 | `diagnostic_value.evaluate_probe` |
| `4127028653` | 4 | the test that the probe's answer is not also a binary-ability observation |
| `2529c2f246` | 5 | the evaluator's cost record splits the acting-now arms from the probe's paths |
| `f4048a4f44` | 5 | `scripts/probe_router_report.py` and `tests/test_probe_router_report.py` |
| `832657145a` | 5 | the evaluator's docstring states its approach (a function over 100 lines); a comment reworded |

Step 4 lands as `d642135954`..`4127028653` (its first commit fails alone, by design); step 5 as `2529c2f246`..`832657145a`.


## Read first: the judgment calls

1. **Cost: the stop rule's line is touched at six hypotheses with five distinct repairs.** At G1's scale (seven
   topics, the served 90-day horizon, 8 draws; the predecessor's probe value is 218-226 ms there, G1 measured 227 ms),
   the whole evaluator takes 553 ms at H = 3 (1.46× G1's 379 ms estimate for H = 3) and 1,225 ms at H = 6 with five
   distinct repairs (2.02× G1's 607 ms estimate; G1 measured the 227 ms and the per-branch times and estimated the per-hypothesis
   costs from them, and the design lists those estimates as its cost). The probe's own paths (what pricing the probe adds; the rest are
   the acting-now arms) are 364 ms and 798 ms (0.96× and 1.31×). Reported, not optimized, as the brief says. Measured
   detail below ("Measured cost").
2. **Decision 2's uncovered-repair seed is AD's practice slope `γ`** (`types.Learning.gamma`): a repair that does not
   cover the true hypothesis is priced as an ordinary graded practice opportunity on the topic, which is what the
   rollouts already give every untargeted attempt (a review, new practice, the tail's own blocks). It claims neither
   zero nor a measured effect. **Its consequence:** `γ_gap`'s seeded prior is `γ`'s (miss_cause, the owner's Nov 9
   default), so at the seeded priors a repair covering a gap cause is worth exactly what one that misses it is
   (draw for draw), and between gap causes the probe's information is exactly zero. On the synthetic journeys at the
   seeded priors the successor never asks the probe; it values discrimination only where `γ_gap` is (illustratively)
   learned above `γ`. `γ_gap` moves only with lessons offered on a diagnosed miss and followed by a cold check, so a
   vault with few such lessons stays near the prior (no vault was checked). This is what the owner decides in decision 2.
3. **A slip cause is priced oddly under that seed.** A repair covering a slip-class hypothesis learns at `γ_slip`
   (seeded at 0), one missing it at `γ`, so the model prefers missing a slip. That is SG2's meaning of `γ_slip` (the
   slope of instruction after a slip, whatever it targeted), not a claim that covering hurts; the gap-and-slip
   journeys show it (zero information even with a learned `γ_gap`). An alternative the owner could choose: the world's
   class slope for every repair, cover adding only for a gap. Not built.
4. **The probe's segment observes nothing on the ability scale.** Its one answer is the channel's result; the
   predecessor's binary-ability observation of the same answer would count it twice (design §2b). A test shows an
   observing probe would change the path on inputs where it matters.
5. **`Action` gains `diagnostic`, and the rollouts refuse it.** `types.Action.diagnostic` (default None; only a probe
   may carry it); `rollouts._Model.value` raises on any action that carries a payload anywhere (itself, a step, its
   repair or declined branch), so until step 6 a payload can never be priced silently as a binary probe. With no
   payload nothing changes (identity pins, the journey golden, the post-miss grid and every affected test pass
   unchanged). This is a served module's edit that refuses only; no served path builds a payload.
6. **The repair policy chooses in the belief's own world** (the rollouts' `_belief_model`: believed parameters, its
   own noise), as the predecessor's probe chooses its repair, so the choice never sees the true path's noise.
7. **Acting now uses the repair's stream 2** (the predecessor probe's repair stream), the same as after the probe, so
   the two arms differ by the probe and not by a duration draw. An `act_now:<repair>` row is therefore not
   draw-for-draw the router's standalone repair candidate (stream 0).
8. **An offer's declined probe is exposed.** A lesson won at the post-miss boundary releases the feedback, so the
   evaluator prices the probe after a "Not now" as exposed (zero information), whatever its payload says, and records
   why (design §6.7).
9. **Only implementable decision values are accepted.** `OwnerDecisions` refuses any decision-1 value but "no
   information credit" (no generation-channel prior exists) and any decision-2 value but the cause-class slopes and
   practice's `γ`; nothing is approximated.
10. **The evaluator's own choice lists acting now first**, so a probe that only ties acting now within the paired
    precision is not chosen. It is a record convenience: step 6 uses the router's support order.
11. **The report's predecessor on synthetic journeys** is the causal gate's verdict (`probe_facts` and `probe_verdict`
    at the pinned defaults) on facts derived from the case (separability: two hypotheses whose channel rows differ;
    the orchestrator's 8-minute repair default; the probe's 3 minutes), the automatic lane's deterministic rules (no
    plan, no room), and the predecessor rollouts' probe kind (one binary result, the first repair). FG1's served stand-in
    on a plan without a lesson is repair practice, not the probe kind, so that last column is the IH-annotated case.
12. **As of.** A row stamped in the decision's own second counts as available (the store keeps no finer order across
    tables). The automatic lane's locked set is written at authoring, after the decision, so it is never read.
13. **The learner lane's exposure is unknown at the receipt.** The receipt is written while the feedback screen is
    open; whether the eventual quick-check answer is exposed is decided when it is answered (G3: three of four real
    answers were refused as not independent). The report marks exposure `missing` there. If most learner-lane answers
    are exposed, the successor gives them no information.

## Step 4: the payload and the evaluator

**Where it lives.** `router_objective/diagnostic_payload.py` (plain values; imports only `miss_cause`'s class names) and
`router_objective/diagnostic_value.py` (imports `types`, `objective`, `rollouts`). Neither imports `diagnosis`; nothing
under `src` imports `diagnostic_value`.

**Payload** (`DiagnosticProbe`, design §2a):

| Field | What |
|---|---|
| `topic` | the factor's learning object (whose repair effect the hypothesis conditions) |
| `hypotheses` | `Hypothesis(id, prior, cause_class)`, the locked order, the open one (`other_or_unknown`, unknown class) included |
| `prior_basis` | where the prior came from |
| `channel` | `Channel(results, rows, version, source)`: one complete row `P(result | h)` per locked hypothesis (validated: a distribution, every member present); or `MissingChannel(reason)` |
| `repairs` | `RepairOption(ref, action, covers, source)`: an executable repair block and the hypotheses it covers |
| `exposed` | the answer would come after the miss's feedback, causes or a reveal |
| `hard_stops` | reasons the probe is out of the support (learner refusal, machine checks, a measured foreign episode, an unexecutable contract) |
| `routing_weights`, `routing_version` | LI4's separately versioned positive weights; a zero is refused (never removes) |
| `source`, `facts` | the decision's identity and the repair lane's facts, for the record only (never priced) |

**Owner decisions** (`OwnerDecisions`, a required keyword of the evaluator; `DESIGN_RECOMMENDATIONS` is what the
tests and the report pass; each recorded with `"status": "pending the owner"`):

| Decision | Named input | Value used | Why this value |
|---|---|---|---|
| 1. prior of an unauthored probe | `unauthored_channel` | `no_information_credit` | the design's recommendation; no generation-channel prior exists, so it is the only implementable value |
| 2. covered repair | `covered_repair_effect` | `cause_class_slopes` | the SG2 slopes (`γ_gap`, `γ_slip`, `γ` for unknown) the lesson and repair values already read |
| 2. uncovered repair | `uncovered_repair_effect` | `practice_gamma` | seeded from AD's `γ`: an untargeted graded attempt, as the rollouts price every other one (judgment call 2) |
| 3. no intervention without WAIT | `no_intervention_without_wait` | `True` | the design's recommendation: no room removes WAIT, not the open arm |
| 4. launch tradeoff | (none) | decided from the report | nothing to build |

**Evaluator.**

```python
evaluate_probe(inputs: Inputs, action: Action, *, decisions: OwnerDecisions, draws: int, seed: str,
               wait_feasible: bool = True, base_stream: int = 0, merged_sessions=False,
               consistent_review_draw=False, held_ad_link=False, clock=time.perf_counter) -> ProbeValuation
ProbeValuation(valued: tuple[Valued, ...], choice: str | None, record: Mapping)
```

`action` is a probe carrying a payload, a sequence holding one such probe (at any position), or an offer whose
declined branch is one of those. `valued` holds the candidate's row (`ref` = the action's) and one row per acting-now
arm (`act_now:none`, `act_now:<repair>`), each an `objective.Valued` with its `q_draws` and `_terms`. With
`p(h)` the effective prior and `L(r | h)` the channel:

```
a*(r)    = argmax over {none, repairs} of Σh p(h | r)·Q̄_belief(probe, a | h)      (ties: none first, then payload order)
Q(probe) = Σh p(h) Σr L(r | h)·Qpath(probe, a*(r) | h)                        (one weighted ledger)
Q(act a) = Σh p(h)·Qpath(a | h)
```

A path is the rollouts' own: the steps before the probe once, the probe's segment (its minutes, no observation), the
repair with its topic learning at the effect the hypothesis gives it (`_cause_gain` with a one-hot split, or `γ`), the
steps after, the tail once. Nothing is added to the objective's terms. A repair's path depends on the hypothesis only
through its effect key (`gap`, `slip`, `unknown`, `uncovered`), so an option has at most four paths. No information
(exposed, or a missing channel) is one posterior, the prior; when every result picks the prior's repair the policy's
ledger *is* that repair's ledger (information exactly 0).

**Record keys.** `version` (`diagnostic_probe_value_v1`, a scoped probe-policy version; the objective's versions do not
move), `decisions`, `given` (`payload` summary with the effective prior, `position`, `exposed_by`, `draws`, `seed`,
`wait_feasible`, `topic_valued`), `excluded` (a hard-stopped probe; decision 3's removed arm), `channel_use`
(`channel`, `exposed`, `missing:<reason>`), `results` (per result: `p`, the posterior over every locked hypothesis,
the choice, each option's believed value), `prior_choice`, `prior_q_belief`, `policy_changes_with_result`,
`branch_terms` (each path's terms, probe and act-now), `values` (`probe_policy`, `probe_then_prior_choice`,
`information`, `clairvoyant`, `act_now`), `choice` (`numeric_choice`'s record), `offer` (an offer's acceptance and
branch values), `cost` (ms in all, for the acting-now arms and for the probe's paths; tails run; hypotheses, results,
repairs, effect paths).

## Step 4: the tests and what each proves

`tests/test_diagnostic_probe_value.py` (16 tests, literal inputs, no vault):

| Test | Proves |
|---|---|
| `test_an_informative_channel_changes_the_preferred_repair` | after a result pointing at the less likely cause the policy picks that cause's repair; information > 0 |
| `test_a_flat_channel_changes_nothing_and_its_probe_is_worth_only_its_burden` | identical rows: every posterior is the prior, every result picks the prior's repair, information exactly 0, the probe's value is exactly "ask then act on the prior", below acting now with that repair |
| `test_acting_now_is_always_valued_beside_the_probe` | the open arm is valued with a channel, without one, exposed, and alone when a hard stop excludes the probe (recorded) |
| `test_no_clairvoyance` | the policy's value never exceeds "ask, then act knowing the hypothesis"; a perfect channel reaches it, a noisy one falls short |
| `test_the_probe_duration_is_charged_once` | the κ integral of probe-then-none is the probe's minutes once; probe-then-repair the two back to back; acting now has no probe minutes |
| `test_a_probe_anywhere_in_a_sequence_appends_the_rest_and_the_tail_once` | first or last in a sequence, each path's κ integral is its segments back to back (the chosen repair right after the probe); a one-step sequence is the probe alone; two payload probes in one sequence are refused |
| `test_a_lesson_declined_at_the_same_boundary_prices_its_probe_as_exposed` | the offer is `p·accepted + (1 − p)·declined`, the declined probe is exposed (information 0) and equals a standalone exposed probe on the declined stream, its minutes charged once |
| `test_the_probe_answer_is_not_also_a_binary_ability_observation` | probe-then-nothing equals, term for term, the rollouts' path of a probe observing no topic, on inputs where an observing probe differs |
| `test_an_exposed_answer_gives_no_information` | a discriminating channel, exposed: one posterior (the prior), information 0 |
| `test_a_missing_channel_is_explicit_and_earns_no_information_credit` | `missing:unauthored` named in the record, information 0, decision 1 recorded pending; a channel missing a hypothesis's row cannot be built |
| `test_hypotheses_are_reweighted_never_removed` | a ruled-out hypothesis stays at 0 in every posterior, the open one stays; routing weights reweight and a zero weight is refused |
| `test_the_owner_decisions_are_named_inputs_marked_pending` | every decision recorded pending; unimplementable values refused; decision 3 keeps `act_now:none` with no room, its predecessor shape removes it (recorded) |
| `test_at_the_seeded_priors_a_covering_repair_on_a_gap_is_worth_what_practice_is` | judgment call 2's consequence: information 0 at the seeded `γ_gap`, and with no cause slopes |
| `test_the_evaluator_is_deterministic_and_its_record_names_its_inputs` | same inputs, same values and record (cost aside) |
| `test_a_probe_without_a_payload_is_the_predecessors_and_a_payload_is_refused_there` | no payload: the rollouts as before; a payload reaching them is refused; only a probe carries one |
| `test_no_served_module_imports_the_evaluator` | no file under `src` imports `diagnostic_value` (by name, from its package, or through importlib) |

`tests/test_action_kinds_complete.py` gains one test (the design's "extend"): a probe with a payload is refused by the
rollouts and has its effect through the successor evaluator. Its other tests are unchanged.

**Fail-first.** The tests were committed before the code (`d642135954`; they fail on import there). Seven mutations
of the code, each run against the file and restored: the probe also observes ability (fails the observation test);
exposure ignored (2 tests); the policy sees the hypothesis (no clairvoyance); the probe charged twice (4 tests); a
ruled-out hypothesis dropped from the posterior (3 tests); every repair learning the same whatever it covers (2 tests);
the offer's declined probe not exposed (1 test). Each mutation fails at least one test.

## Step 5: the comparison report

`scripts/probe_router_report.py`, read-only, aggregates only (counts, rates, timings; no id, label, path or text: a
test checks every id and hypothesis label the journeys' rows hold is absent from both outputs). It follows
`scripts/vault_report.py` (whose read-only URI rule it loads) and G3's measurement (fresh backup copies, read in
`mode=ro`, opened by the orchestrator, never by an agent).

**Inputs.** `--vault DIR_OR_DATABASE` (repeatable; a copy), `--synthetic`, `--draws`, `--json`.

**Opportunities read from a vault.**

| Lane | Rows | Predecessor's answer | What the successor's answer can be from recorded facts |
|---|---|---|---|
| automatic (FG1's post-miss Next) | `decision_records` of kind `followup_gate`, the first per workflow (retries counted) | the arm (`ask_now`, `wait`, `none`, `lesson`, `refused`) and its rule (`no_plan`, `no_room_to_wait`, drawn, refused) | a hard stop; otherwise no information credit (the channel is missing by construction: the decision precedes authoring); the classes' verdict when they settle it |
| learner (causal gate B/C) | every `causal_probe_decision_receipts` row (a status read per panel mount, a held repair request) | the verdict | a hard stop (machine checks, preference, budget, no executable instrument, an episode conflict); no information when the classes settle it; otherwise not computable (no stored likelihood) |
| practice (G) | `followup_value_decisions` | the outcome | not computable (no payload is gathered for a general follow-up before step 6) |

**Coverage classes**, per payload input: `exact` (stored with the decision, or fixed by how the decision is made),
`as_of` (a row stamped at or before the decision), `missing` (not stored, or only after the decision; never filled in),
`synthetic`. The successor's numeric choice needs the frozen objective inputs, which no vault stores today, so on a
vault it is `not_computable` in every row and only what recorded facts fix is reported. Coupled-draw disagreement is not
computed (the successor has no mixture before step 6).

**On the diagnosis journeys' 21 vaults** (the tests' vaults: every case of `tests/diagnosis_journey_helpers.py`, built
as the golden builds them, the report run on each):

| Lane | Opportunities | Predecessor's answers | Which authority answered | Successor's information (from recorded facts) | Coverage | Numeric successor computable |
|---|---|---|---|---|---|---|
| automatic | 4 (0 retries) | ask now 2, wait 1, refused 1 | no plan, asked with no draw 2; the router's draw 1; hard stop 1 | no credit (channel missing by construction) 3; excluded by a hard stop 1 | channel, hard stops, exposure, wait feasibility `exact` 4/4; repair classes `exact` 3, `missing` 1; locked set and frozen inputs `missing` 4/4 | 0 of 4 |
| learner | 13 (receipts per factor: 1 for 8 factors, 2 for 1, 3 for 1) | `probe_now` 8, `defer_learner_preference` 2, `defer_machine_checks` 1, `skip_common_repair` 1, `skip_no_discrimination` 1 | the gate's offer 8; hard stop 3; no executable instrument 1; classes settle it 1 | not computable (no stored likelihood) 8; excluded 4; none, one repair 1 | hard stops, repair classes, locked set `exact` 13/13; prior `as_of` 10, `missing` 3; channel, repair per hypothesis, exposure, frozen inputs `missing` 13/13 | 0 of 13 |
| practice | 4 | suppressed (value below minutes cost) 4 | general follow-up value | not computable (no payload) 4 | frozen inputs `missing` 4/4 | 0 of 4 |

So on vault-shaped data the report can say what recorded facts fix and nothing more: every automatic-lane probe would
earn no information credit under decision 1, and every learner-lane offer waits on a channel no vault stores. Zero
computable successor answers is not agreement.


**On the synthetic journeys** (41 controlled snapshots, seven topics, 14-day horizon, 8 draws; `learned_gap` marks an
illustrative `γ_gap` of 0.6 against `γ` 0.2, a sensitivity and not a claim; every other case is at the seeded priors):

| Lane | Cases | Predecessor's answer known | Predecessor asks | Successor asks | Successor's information | Disagree with the gate | Disagree with the final answer (where a rule gave it) | Differ by |
|---|---|---|---|---|---|---|---|---|
| automatic | 11 (8 on a plan: a draw) | 3 | 2 (no plan 1, no room 1) | 0 | no credit, missing 9; exposed 1; excluded 1 | 1 | 2 of 3 | asks -> no: no plan 1, no room (decision 3) 1 |
| learner | 30 | 30 | 13 (gate `probe_now`) | 4 | zero 21; positive 5 (all `learned_gap`); exposed 2; excluded 2 | 11 | 11 of 30 | asks -> no: the gate's offer 10; no -> asks: the recent-burden rule 1 |

The predecessor's rollouts (the probe kind) would pick the probe in 1 automatic and 2 learner cases; they disagree with
the successor in 1 and 6.

| case | lane | predecessor_gate | predecessor | predecessor_numeric_asks | information | information_value | successor_choice | ms | ms_probe | predecessor_probe_ms |
|---|---|---|---|---|---|---|---|---|---|---|
| missing/different/H2 | automatic | skip_action_equivalent | router draw | False | none_missing | 0.0 | act_now_none | 51.7 | 34.2 | 34.0 |
| missing/different/H3 | automatic | skip_no_discrimination | router draw | False | none_missing | 0.0 | act_now_repair | 86.1 | 56.9 | 34.3 |
| missing/different/H6 | automatic | skip_no_discrimination | router draw | True | none_missing | 0.0 | act_now_repair | 191.7 | 126.7 | 34.2 |
| missing/common/H2 | automatic | skip_common_repair | router draw | False | none_missing | 0.0 | act_now_none | 52.2 | 34.5 | 34.4 |
| missing/common/H3 | automatic | skip_common_repair | router draw | False | none_missing | 0.0 | act_now_repair | 52.0 | 34.3 | 34.2 |
| missing/common/H6 | automatic | skip_common_repair | router draw | False | none_missing | 0.0 | act_now_none | 52.5 | 34.6 | 34.3 |
| flat/different/H2 | learner | skip_action_equivalent | skip_action_equivalent | False | zero | 0.0 | act_now_repair | 52.0 | 34.3 | 34.1 |
| flat/different/H3 | learner | skip_no_discrimination | skip_no_discrimination | False | zero | 0.0 | act_now_repair | 86.4 | 57.3 | 33.9 |
| flat/different/H6 | learner | skip_no_discrimination | skip_no_discrimination | True | zero | 0.0 | act_now_none | 189.7 | 125.6 | 34.2 |
| flat/common/H2 | learner | skip_common_repair | skip_common_repair | False | zero | 0.0 | act_now_none | 52.1 | 34.3 | 34.2 |
| flat/common/H3 | learner | skip_common_repair | skip_common_repair | False | zero | 0.0 | act_now_repair | 52.7 | 34.9 | 34.5 |
| flat/common/H6 | learner | skip_common_repair | skip_common_repair | False | zero | 0.0 | act_now_none | 52.2 | 34.5 | 34.2 |
| informative/different/H2 | learner | skip_action_equivalent | skip_action_equivalent | False | zero | 0.0 | act_now_none | 52.1 | 34.4 | 34.2 |
| informative/different/H3 | learner | probe_now | probe_now | False | zero | 0.0 | act_now_repair | 86.0 | 57.0 | 34.1 |
| informative/different/H6 | learner | probe_now | probe_now | False | zero | 0.0 | act_now_none | 190.1 | 126.1 | 34.0 |
| informative/common/H2 | learner | skip_common_repair | skip_common_repair | False | zero | 0.0 | act_now_repair | 51.7 | 34.3 | 34.0 |
| informative/common/H3 | learner | skip_common_repair | skip_common_repair | False | zero | 0.0 | act_now_repair | 51.9 | 34.3 | 34.0 |
| informative/common/H6 | learner | skip_common_repair | skip_common_repair | True | zero | 0.0 | act_now_repair | 52.6 | 34.6 | 34.1 |
| perfect/different/H2 | learner | skip_action_equivalent | skip_action_equivalent | False | zero | 0.0 | act_now_repair | 52.2 | 34.5 | 34.3 |
| perfect/different/H3 | learner | probe_now | probe_now | False | zero | 0.0 | act_now_none | 86.2 | 57.0 | 34.4 |
| perfect/different/H6 | learner | probe_now | probe_now | False | zero | 0.0 | act_now_repair | 190.7 | 126.4 | 34.3 |
| perfect/common/H2 | learner | skip_common_repair | skip_common_repair | False | zero | 0.0 | act_now_none | 52.0 | 34.3 | 34.3 |
| perfect/common/H3 | learner | skip_common_repair | skip_common_repair | False | zero | 0.0 | act_now_repair | 52.3 | 34.5 | 34.3 |
| perfect/common/H6 | learner | skip_common_repair | skip_common_repair | False | zero | 0.0 | act_now_none | 52.3 | 34.4 | 34.4 |
| informative/different/H3/learned_gap | learner | probe_now | probe_now | False | positive | 0.317 | probe | 86.2 | 56.9 | 34.0 |
| informative/different/H6/learned_gap | learner | probe_now | probe_now | False | positive | 0.4171 | act_now_none | 191.0 | 126.8 | 34.6 |
| perfect/different/H3/learned_gap | learner | probe_now | probe_now | False | positive | 1.0435 | probe | 86.9 | 57.4 | 34.3 |
| perfect/different/H6/learned_gap | learner | probe_now | probe_now | False | positive | 0.6914 | probe | 190.6 | 126.7 | 34.6 |
| missing/different/H4 | automatic | skip_no_discrimination | router draw | False | none_missing | 0.0 | act_now_none | 122.2 | 80.9 | 34.5 |
| informative/different/H4 | learner | probe_now | probe_now | False | zero | 0.0 | act_now_repair | 122.2 | 81.0 | 34.8 |
| informative/gap_and_slip/H3 | learner | probe_now | probe_now | False | zero | 0.0 | act_now_repair | 87.3 | 57.7 | 34.6 |
| informative/gap_and_slip/H3/learned_gap | learner | probe_now | probe_now | False | zero | 0.0 | act_now_repair | 86.8 | 57.4 | 34.7 |
| informative/exposed/H3 | learner | probe_now | probe_now | False | none_exposed | 0.0 | act_now_none | 87.0 | 57.5 | 34.4 |
| perfect/exposed/H3/learned_gap | learner | probe_now | probe_now | False | none_exposed | 0.0 | act_now_repair | 86.6 | 57.2 | 34.2 |
| not_now/H3 | learner | defer_learner_preference | defer_learner_preference | False | excluded_hard_stop | None | act_now_repair | 29.2 | 0.0 | 34.3 |
| machine_check/H3 | automatic | defer_machine_checks | refused | False | excluded_hard_stop | None | act_now_repair | 29.2 | 0.0 | 34.5 |
| foreign_episode/H3 | learner | blocked_episode_conflict | blocked_episode_conflict | False | excluded_hard_stop | None | act_now_none | 29.5 | 0.0 | 34.6 |
| no_plan/missing/H3 | automatic | skip_no_discrimination | ask_now (no plan) | False | none_missing | 0.0 | act_now_repair | 87.3 | 57.8 | 34.5 |
| no_room/missing/H3 | automatic | skip_no_discrimination | ask_now (no room to wait) | False | none_missing | 0.0 | act_now_repair | 88.0 | 58.2 | 34.7 |
| recent_burden/perfect/H3/learned_gap | learner | defer_recent_burden | defer_recent_burden | False | positive | 0.408 | probe | 87.9 | 58.2 | 34.3 |
| lesson_declined/perfect/H3/learned_gap | automatic | probe_now | router draw | False | none_exposed | 0.0 | act_now_repair | 94.4 | 58.2 | 34.8 |


What the table says: at the seeded priors the successor gives no case any information value (decision 2's
consequence), so it never asks; the gate offers the probe in 13 of 30 learner-lane cases, every one on the separability
proxy. With the illustrative learned `γ_gap`, a perfect or 0.7-informative channel earns information (0.32 to 1.04
use-equivalents) and the successor asks in three of those four cases. Missing and exposed channels earn nothing, by
construction. No room to wait no longer forces the probe (decision 3). The recent-burden rule is gone: its case is
asked. Between identical configurations the acting-now choice (repair or none) flips with the seed: the two are within
the paired precision at 8 draws.

## Measured cost

The report's synthetic journeys (14-day horizon) and a G1-scale run (the same seven topics at the served 90-day
horizon; medians of five warm calls; scratch `cost_g1scale.py`). The predecessor's probe value on the same inputs is
beside each; at 90 days it is G1's own number (G1: 227 ms).

| Inputs | Draws | H | Repairs | Evaluator (ms) | Its probe paths (ms) | Tails | Predecessor probe (ms) | Ratio, all / probe paths | G1's estimate for this H (shared result policies / a rollout per hypothesis) |
|---|---|---|---|---|---|---|---|---|---|
| 14 days | 8 | 2 | 1 | 53.3 | 35.1 | 9 | 34.8 | 1.53 / 1.01 | |
| 14 days | 8 | 3 | 2 | 88.6 | 58.5 | 15 | 35.7 | 2.49 / 1.64 | 1.67× / 3.0× |
| 14 days | 8 | 4 | 3 | 125.5 | 83.1 | 21 | 35.4 | 3.54 / 2.34 | |
| 14 days | 8 | 6 | 5 | 198.2 | 131.3 | 33 | 35.2 | 5.63 / 3.73 | 2.67× / 6.0× |
| 14 days | 8 | 6 | 1 common | 54.1 | 35.7 | 9 | 35.4 | 1.53 / 1.01 | |
| 90 days | 8 | 2 | 1 | 338.0 | 224.7 | 9 | 220.8 | 1.53 / 1.02 | |
| 90 days | 8 | 3 | 2 | 552.7 | 363.6 | 15 | 217.4 | 2.54 / 1.67 | 379 ms / 681 ms |
| 90 days | 8 | 4 | 3 | 770.3 | 514.0 | 21 | 220.3 | 3.50 / 2.33 | 455 ms / 908 ms |
| 90 days | 8 | 6 | 5 | 1,224.9 | 798.1 | 33 | 217.8 | 5.62 / 3.66 | 607 ms / 1,362 ms |
| 90 days | 8 | 6 | 1 common | 326.8 | 216.6 | 9 | 217.6 | 1.50 / 1.00 | |
| 90 days | 16 | 3 | 2 | 562.0 | 372.7 | 15 | 224.3 | 2.51 / 1.66 | |
| 90 days | 16 | 6 | 5 | 1,234.0 | 821.6 | 33 | 223.3 | 5.53 / 3.68 | |

On the report's synthetic journeys (14 days, 8 draws): the evaluator's median 86 ms, p95 191 ms, max 197 ms; its probe
paths median 57 ms, p95 127 ms; the predecessor's probe 34 ms. Warm calls only (one warm-up each); cold first calls and
numeric runtime inside a served decision were not measured.


The cost grows with the number of distinct effect paths (none, plus up to two per repair here), not with the number of
results: 9 tails for one common repair at any H, 33 at H = 6 with five distinct repairs (11 paths, each in the true and
believed worlds with the probe and in the true world without). Sixteen draws add 1-6%. G1's recorded locked sets: 3
hypotheses in 337 of 385, 6 in 5.

## What step 6 needs that is not here

- A gatherer that builds `DiagnosticProbe` from the vault: hypotheses with their cause classes
  (`causal_hypotheses.cause_scope`), the prior or effective posterior (`effective_posterior_as_of`), the repair
  options as executable actions with durations and what each covers (the receipt keeps only the distinct classes), the
  hard stops; for FG1, `MissingChannel("unauthored")` before authoring.
- An existing instrument's complete channel as a `Channel` with the open hypothesis's row (`instrument_conditionals`
  through its slot map); blind-bundle separation is not one.
- A frozen, unrounded `Inputs` and action tree persisted at each post-miss decision, so the report's successor column
  becomes computable on copies (today `not_computable` in every vault row).
- Wiring: the probe candidate valued by `evaluate_probe` inside the numeric policy (`post_miss_choice`'s
  `run_numeric`), the rollouts' refusal kept for every other path, the deadline (checked between candidates, and the
  evaluator is one call of up to about 1.2 s at H = 6 with five repairs at 90 days), decision 3 in `_no_room`, the card,
  the propensity, the tag, the upgrade row and the identity pins (design §3).
- The learner lane's exposure at the decision (judgment call 13).
- The owner's answers to decisions 1 to 3 (each a named input already) and the slip pricing (judgment call 3).

## Net lines

| Step | Production | Script | Tests |
|---|---|---|---|
| 4 | +600 (`diagnostic_payload.py` +278, `diagnostic_value.py` +307, `rollouts.py` +11, `types.py` +6 net) | 0 | +392 (`test_diagnostic_probe_value.py` +374, `test_action_kinds_complete.py` +18 net) |
| 5 | +9 (`diagnostic_value.py`: the cost split and its approach sentences) | +667 (`probe_router_report.py`) | +184 (`test_probe_router_report.py`) |

The cost rule: both steps only add. Step 6 uses the payload and the evaluator; the report is the owner's read before
it. No structure number rose.

## What was run

Every pytest command ran from a script file under the scratch directory at `-n 1` inside a 3 GB scope, one at a time;
none was killed. At the tip `832657145a` unless stated:

| What | Result |
|---|---|
| `scripts/affected_tests.py --files` over the four changed source files: 171 files, more than 150, so filtered by name (`action_kinds\|diagnos\|probe\|router\|objective\|test_ro[0-9]\|rofu\|rospeed\|followup\|ih[0-9]\|test_ih_\|instruct_handoff\|test_sg_\|te3\|teacher_te2\|post_miss\|identity_pins\|plan_determinism\|pinned_draws\|daily_plan\|refusal\|mobile_v2_objective\|mobile_v4_plan\|why_cases\|data_capture\|voi\|carried\|robust\|sampling_points\|forced_withdrawal\|remaining_decision`) to 121, in 4 chunks of at most 40, `-m "not arc_close"` (chunk 1 at `f4048a4f44`, before a docstring-only commit) | 1,193 + 479 + 545 passed, 3 skipped; the fourth chunk (`test_why_cases.py`) in the next row |
| `test_why_cases`, the three added or edited test files, `test_identity_pins`, `test_structure_ratchets`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches`, `test_sqlite_file_copies`, `test_diagnosis_journey_golden`, `test_post_miss_choice`, `test_probe_router_authority` | 510 passed |
| `tests/test_test_layout.py` alone | 3 passed |
| `tests/test_architecture.py` alone | 18 passed |
| `ruff check` | all checks passed |
| `lint-imports --no-cache` | 43 kept, 0 broken |
| `scripts/check_gate_partition.py` | 31,644 collected: landing 31,579 + arc_close 65 |
| After step 4 (`1df93873bb`): identity pins, structure ratchets, post-miss choice, probe router authority; the journey golden | 379 passed; 21 passed |
| The seven mutations (step 4, fail-first) | each failed at least one test; source restored from git |
| The report on the 21 journey vaults (a scratch test file, deleted) and `--synthetic` | the tables above |
| `cost_g1scale.py` (scratch) | the cost table |

Identity pins pass with nothing written; no pin moved. The journey golden, the post-miss grid (`post_miss_choice.json`)
and every other golden pass unchanged. The structure ratchet passes with no number raised.


## Not verified

- The report on the owner's vaults or fresh copies (the orchestrator's: `uv run python scripts/probe_router_report.py
  --vault <copy> [--json]`).
- Any served path: nothing calls the evaluator, so end-to-end Next latency and deadline overshoot are not measured.
- P-draw and P-shadow (nothing served or replayed changed; the rollouts' refusal fires only on a payload).
- The whole suite, durability, `--fresh-connections` and `arc_close`; the 50 affected test files outside the name filter.
- The real instrument channel and the real cause classes on a locked set (synthetic payloads only).

Implementer: one Opus session, no subagents; token use not available to the implementer.
