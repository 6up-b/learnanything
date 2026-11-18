# Refactor E4: trace assembly leaves the chooser

Branch `refactor/e3-e4-chooser`, after E3 (its last source commit `4fa5f05bde`, record `5ec274b8d1`). Step E4 of arc E
(`docs/specs/refactor_strategy_v3.md` §2.7, leak 3). Structure track: no served or persisted value changes. Line numbers
in §1 are at E3's tip, in `src/learnloop/daily_plan/objective_chooser.py`.

## 1. Step 0: the trace's assembly at E3's tip

### What the step moves, its size and its callers

| Definition | Lines | Size | Called by | Reached by tests |
|---|---|---|---|---|
| `_trace` | 834-1025 | 192 | `_decide_objective` (1222), `ObjectiveRestraintGate._mixed` (1501) | — |
| `_offer_trace` | 773-824 | 52 | `_trace` | — |
| `_support_labels` | 692-707 | 16 | `_trace` | — |
| `_goal_dates` | 719-737 | 19 | `_decide_objective` | `test_ro5_codex_review` calls `OC._goal_dates` |
| `_score_note` | 710-716 | 7 | `_trace` | — |
| `_failure_rule_field` | 827-831 | 5 | `_trace`, `_decide_objective`'s record, `_mixed`'s record | `test_ih5_successor` imports and calls it |
| `_serving_switches` | 224-230 | 7 | `_trace` | — |
| `_decide_objective`'s trace assembly after `choose` | 1214-1249 | 36 | — | — |

All of them are pure: no thread, lock, process cache, database or clock. The one read in the write phase is
`J.carried_for` (the carry registry and `router_objective_traces`), which feeds only the trace. `_trace` knows every
kind of option: stop (its label), a lesson offer (its label and its `offer` section, `_offer_trace`), a block (its
label), and IH2's contest (`followup_contest`, in `_decide_objective`).

### Imports the module may not have

`router_objective/trace.py` may not import `daily_plan` (the contract `choose.py` lives under). What the moved code
takes from `daily_plan`:

| Name | Lives in | What the trace module does |
|---|---|---|
| `BlockCandidate` (annotations; `.subtype`, `.learning_object_ids`, `.est_minutes`, `.reading`, `.lane`, `.annotations`, `.item_ids`, `.candidate_id`) | `daily_plan/types.py` | reads the attributes; annotated `Any` |
| `NumericPolicy` (`.evaluation`, `.inputs`, `.sources`, …) | `daily_plan/objective_job.py` | reads the attributes; annotated `Any` |
| `ComponentResult` (`.status`, `.parsed`, `.model`, …) | `daily_plan/router_runtime.py` | reads the attributes; annotated `Any` |
| `STOP_FOR_TODAY` | `daily_plan/types.py` | `stop_coin.STOP` (the same string, already the router objective's) |
| `LESSON_OFFER_SUBTYPE` | `daily_plan/types.py` | repeated, held equal by a test |
| `OI.MISS_CAUSE_SOURCE` | `daily_plan/objective_inputs.py` | repeated, held equal by a test |
| `ANSWERED`, `NOT_READY` | `daily_plan/router_runtime.py` | `choose.py`'s copies (already held equal) |
| `_is_contest` / `FOLLOWUP_CONTEST_NOTE` | `daily_plan` | not needed: the chooser passes the contested ref it already computes |

None of the three types needs to move: the trace reads their attributes and constructs none of them. Where they
should live later: `BlockCandidate` and the plan's string constants belong with the plan (`daily_plan/types.py`), which
the router objective reads but should not import; a small shared `router_objective` types module would hold them if
E6 (an action is one place) gives each action kind its own definition there.

### The trace's fields and where each value comes from

Key order is the serialized order. **C** the `Choice`; **R** a read the chooser holds (the numeric policy's answer
`numeric`, the models' results, the weight, the seed, the LLM's card, the carry registry, the config, the clock's
`now_iso`); **K** a candidate's own fields; **S** the support the chooser built before the choice.

| Field | From |
|---|---|
| `residual` (when the numeric answer has one) | R `numeric.residual`; with it applied, each candidate's terms (`tail_serve.candidate_terms`) over R the evaluation's rows |
| `miss_cause` (when present) | R `numeric.sources["miss_cause"]` |
| `preference` (when present) | R `numeric.preference`, with V_pref at R the evaluation's rows |
| `candidates[ref]` | per option of S: `label` K (kind, subtype, LOs with R titles, minutes, section, lane); `kind`, `main_lo`, `minutes` R the numeric answer's action for it; `sensors` R the numeric inputs' topics and sources, the miss sensor, R the LLM's forecast for it; `terms` R the evaluation's row, `v`, stop's Q̄, the paired SE against the top; `split`, `branches` R the row's extras; `offer` (a lesson offer only) K its `lesson_offer` annotation with R the lesson curve and the row's branch terms |
| `reference`, `v`, `cutoff_days`, `precision` | R the evaluation (and `numeric.tie`) |
| `filtered` | K each feasible candidate outside S (its `reversible` annotation) |
| `stop_in_support` | S |
| `session` | R the numeric inputs (minutes, remembered minutes and source) and the session guard (R config, R remembered minutes) |
| `policies.llm`, `.decider` | R the models' results |
| `policies.numeric` | R the numeric answer |
| `policies.staged` | S staged's ref |
| `mixing` | R the weight (posterior, seeds, note, `w`); C `effective`, `drawn.pi` (μ), `drawn` (chosen, component, propensity, u1, u2); R the mix's seed; R config (ε, the failure rule) |
| `evaluation` | R the numeric answer's uses and baselines, R config (window), R `now_iso` (window close), R the price (c0), R config (the score note) |
| `frontier`, `inputs_sources` | R the numeric answer |
| `versions` | constants (objective, tail, terminal, LLM schema, review draw, AD link); R config (horizon); R the numeric inputs (memory model, learning source, κ, goals); R the card's version; R the switches the numeric answer was computed under |
| `learner_statements` (when the card has them) | R the LLM's card |
| `followup_contest` (IH2) | S the contested ref; K its item ids |
| `goal_dates` | R the numeric answer (dated uses, baselines, goals) |
| `carried_for` (when any) | R the carry registry and `router_objective_traces` |
| `mixing.drawn_chosen`, `.chosen`, `.propensity`, `stop_coin`, `evaluation.score` (under the coin) | C `drawn`, `served`, `coin` |

The router's record (`record.update(...)` after the trace) is built from C and R too; the chooser keeps writing it
(the brief: build the trace, write it, write the record, return the block).
