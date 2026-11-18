# Refactor E3: job control and the clock

Branch `refactor/e3-e4-chooser`, based on `69befd0430` (the tip of E2, `refactor/e2-choice-pure`, not yet on main).
Step E3 of arc E (`docs/specs/refactor_strategy_v3.md` §2.7: problem F2, D1, leaks 1 and 2). Structure track: no
served or persisted value changes. Line numbers in §1 are at the base, in `src/learnloop/daily_plan/objective_chooser.py`
unless another file is named.

## 1. Step 0: the job's control at the base

### What the step moves, its size and its callers

| Definition | Lines | Size | Called by (src) | Reached by tests |
|---|---|---|---|---|
| `numeric_seed` | 166-191 | 26 | `ObjectiveChooser.choose` (1469), `ObjectiveRestraintGate.decide` (1806), `._decide_with_lesson` (1838), `ObjectiveFollowupGate.decide_followup` (2198) | `tests/pinned_draws.py` wraps `objective_chooser.numeric_seed`; `router_model_fakes.never_stop_or_offer_draws` and `ih4_preferences_inform_router_helpers` replace it there; `identity_pins_helpers` calls it (site C3 names `objective_chooser.py::numeric_seed`) |
| `_without_miss_cause` | 194-228 | 35 | `numeric_seed` | — |
| `ObjectiveChooser._seed` (the mix's seed) | 1407-1408 | 2 | `_decide_objective` (1611); `ObjectiveRestraintGate._mixed` repeats its expression inline (1918) | `tests/pinned_draws.py` wraps `router_objective.mix.seed_for`, which it calls |
| `_pooled` | 306-320 | 15 | `_objective_job` | `test_rospeed2_connections` calls `OC._pooled` (3) |
| `NumericPolicy` | 492-523 | 32 | `run_numeric`, `_numeric_answer`, `_defer_carry`, the restraint gate | many tests name `OC.NumericPolicy` |
| `_llm_forecasts` | 790-802 | 13 | `_wait_llm` | — |
| `_objective_job` | 805-927 | 123 | `_start_objective` (as the runtime's job) | `test_rospeed2_connections`, `test_ro6_codex_review` wrap `OC._objective_job` |
| `_with_carried` | 930-948 | 19 | `_decide_objective` | — |
| `_carry_on` | 951-955 | 5 | `run_numeric` (2), `_objective_job`, `choose`, `_decide_objective` | — |
| `_register_carry` | 958-965 | 8 | `_defer_carry` | — |
| `_drain_carry` | 968-989 | 22 | `_objective_job`, `_defer_carry` (its thread's target) | `test_ih4_preferences_inform_router` replaces `OC._drain_carry` |
| `_carried_for` | 992-1025 | 34 | `_decide_objective` | — |
| `_wait_llm` | 1028-1032 | 5 | `_objective_job` (the numeric policy's `forecasts`) | — |
| `_numeric_answer` | 1035-1059 | 25 | `_decide_objective` | — |
| `ObjectiveChooser._defer_carry` | 1508-1533 | 26 | `_decide_objective` | `router_mixture_helpers.join_carried_valuations` wraps it (7 test files use the helper) |
| `choose`'s job control | 1471-1497 | 27 | — | `test_instruct_handoff_ih0` replaces `objective_chooser._await` |
| `_start_objective`'s start | 1573-1578 | 6 | `choose` | `identity_pins_helpers` replaces `_start_objective` on an instance |
| `CARRY_LIMIT`, `_CARRY_LOCK`, `_CARRY`, `NUMERIC`, `PUBLISHED`, `CARRIED` | 108-122 | — | the above | `test_rofu_carried` reads `OC.NUMERIC`, `OC.PUBLISHED` |

Also in the strategy's list: the four `__import__("learnloop.clock", fromlist=["utc_now_iso"]).utc_now_iso(self.clock)`
calls (1799, 1827, 1872, 2165, all in the restraint and follow-up gates) and the two
`entry.__class__.__name__ == "_NoModels"` tests (1526 in `_defer_carry`, 1631 in the choice's inputs).

`run_numeric` (573-778, 206 lines) is the numeric policy end to end. Its "scheduling half" is not a block of its
own: it is the arguments it takes from whoever runs it (`deadline`, `keep_going`, `clock`, `forecasts`, `publish`,
`defer_carried`, `carried_valuation`) and what it does with them (the early publication's `on_complete`, the early
carry, the deferred carried valuation). The values those arguments get are chosen in two places, both job control:
`_objective_job` (the prefetch: the entry's deadline, refinement while the LLM is out and the deadline allows, the
publication into the material, the deferral) and `choose`'s no-model branch (the serve's thread: `router.timeout_seconds`
from now, no refinement, the carry deferred to a thread of its own). The step moves those two call sites; `run_numeric`'s
body stays (it is the numeric policy, E5's ground), and `tests/pinned_draws.py` wraps it where it is.

### State each one touches

| Definition | Threads | Locks | Process state | Database | Clock |
|---|---|---|---|---|---|
| `_objective_job` | runs on the runtime's job thread (`learnloop-router-<key>`, or inline); starts `learnloop-objective-decider` and `-llm`, joins them at the end | `entry.lock` around `started_components`, `components`, `material` | the job's connection pool (`_pooled`: a context variable), `OI.decision_reads()` (the fit read once per job), the carry registry (through `_drain_carry`) | `Repository.attach(sqlite_path)`: reads; the spend guard's receipts are written | `runtime.clock()` for each component's budget, refinement's `keep_going` and the deadline it hands `run_numeric` |
| `_drain_carry` | runs on the job's thread or `learnloop-objective-carried` | `_CARRY_LOCK` | `_CARRY` (marks running, stores each record) | the carried valuation's reads (`V.evaluate`) | the runner's deadline |
| `_register_carry` | — | `_CARRY_LOCK` | `_CARRY` (appends, keeps `CARRY_LIMIT`) | — | — |
| `_carried_for` | serve | `_CARRY_LOCK` | `_CARRY` (drops entries carried in a written trace, marks this decision a carrier) | reads `router_objective_traces` | — |
| `_with_carried`, `_numeric_answer` | serve | `entry.lock` | the job's `material` (`CARRIED`, `PUBLISHED`), `results` mutated to name an early publication answered | — | — |
| `_wait_llm`, `_llm_forecasts` | job thread | — | `entry.events`, `entry.components` | — | waits up to the entry's remaining budget |
| `_defer_carry` | serve; starts `learnloop-objective-carried` for a no-model decision | `_CARRY_LOCK` (through `_register_carry`) | `_CARRY` | — | `runtime.clock() + router.timeout_seconds` (the thread's deadline) |
| `choose`'s job control | serve; `runtime.start` starts the job (a thread, or inline) | the runtime's | the runtime's prefetch cache | the no-model branch's `run_numeric` reads | `_await`: `runtime.clock()` against the entry's deadline, waits up to `router.timeout_seconds`; the no-model deadline |
| `_start_objective` | as above | — | — | the card, the tail snapshot | `router.prefetch_timeout_seconds` (the entry's budget) |
| `_pooled`, `_carry_on` | — | — | — | — | — (config only) |
| `numeric_seed`, `_without_miss_cause`, `_seed` | — | — | — | — | — (pure: hashes of their inputs) |

### The job's life

```
serve or prefetch (choose)
 |  identity -> key, numeric_seed(identity)
 |
 +-- models ready? --no--> run_numeric on THIS thread, deadline = clock + router.timeout_seconds,
 |                         no refinement, carry deferred (defer_carried) -> _NoModels entry
 |                         (the answer carries its own carried valuation: numeric.carried)
 |
 +-- yes: runtime.lookup(key) or _start_objective -> runtime.start(budget = prefetch_timeout_seconds)
 |         |
 |         |  _objective_job (job thread or inline), inside the pool, the spend guard, decision_reads:
 |         |   start DECIDER thread .......................... answers -> components, event set
 |         |   build the LLM card and request, start LLM thread  answers -> components, event set
 |         |   run_numeric(deadline = entry.deadline,
 |         |               keep_going = LLM out and clock < deadline,
 |         |               forecasts = _wait_llm (waits for the LLM up to the deadline),
 |         |               publish -> material[PUBLISHED]   <-- EARLY PUBLICATION (each complete
 |         |                                                    uncorrected answer, before any LLM wait)
 |         |               defer_carried -> deferred[])
 |         |   components[NUMERIC] = final answer; event NUMERIC set   <-- releases the serve's wait
 |         |   carry on?  _drain_carry(deadline = entry.deadline)      <-- DRAIN: earlier decisions' carries
 |         |   else: run deferred -> material[CARRIED]                 <-- this answer's carried valuation
 |         |   join the component threads
 |         |
 |   _await: complete? return; may_defer and before the deadline? raise DecisionPending;
 |           else wait min(router.timeout_seconds, remaining)
 |
 _decide_objective (the serve):
    results = entry.results()   (a component still out is a timeout: a late answer is discarded)
    numeric = _numeric_answer   (no-model answer | the job's final | PUBLISHED as published_uncorrected | status)
    numeric = _with_carried     (CARRIED if the job had it before this serve, else not_valued_before_the_serve)
    decision_id = new_ulid()
    _defer_carry                (CARRY: a pending carried valuation is registered in _CARRY;
                                 no models -> thread learnloop-objective-carried runs _drain_carry now;
                                 with models -> the next boundary's job drains it)
    seed = _seed(key, decision_id)
    ... choose(...) ...
    _carried_for                (earlier carries that drained and are valued go into this trace)
```

### Seeds at the base

| Seed | Where | Depends on |
|---|---|---|
| numeric | `numeric_seed(identity)` in `choose` and the three gates, before any job starts | the boundary identity the prefetch key hashes, less `SEED_NEUTRAL_SWITCHES`, `SEED_NEUTRAL_OBJECTIVE_KEYS`, `SEED_NEUTRAL_IDENTITY_KEYS` and the miss-cause keys: no decision id, so a prefetch and its serve value the boundary on the same draws |
| mix | `ObjectiveChooser._seed(entry.key, decision_id)` (and `_mixed` inline): `runtime.seed` when a runtime pins one, else `mix.seed_for(key, decision_id)` | the boundary key and the decision's fresh id: a new draw per decision, even at one boundary |
| coin | none of its own: `stop_coin.flip` draws `mx.uniform(seed, "stop_coin")` (and `"stop_coin_next"`) from the mix's seed | the mix's seed, under stage names the mix's two uniforms (`"component"`, `"candidate"`) never use |

### Where the job reads the clock at the base

`_objective_job`: `runtime.clock()` per component budget, in `keep_going`, and for the threads' join. `choose`:
`_await` (inside it), the no-model deadline. `_defer_carry`: the thread's deadline. `_start_objective`: the budget
(through `runtime.start`). `_decide_objective`: `wall_now()` (`results_at`) and `runtime.clock() - entry.started`
(`waited_ms`, a record field). The restraint gates: `utc_now_iso(self.clock)` through `__import__` (four places),
and `runtime.clock() + router.timeout_seconds` for their own `run_numeric` calls.

### Import constraint the move must meet

`objective_chooser` sits in an import cycle of ten modules (`engine`, `lesson_offer`, `lesson_suggestion`,
`objective_chooser`, `objective_inputs`, `policy`, `router_card`, `router_teach_back`, `slot_facts`, the sidecar's
daily-plan handler): `objective_chooser -> objective_inputs -> lesson_offer -> policy -> objective_chooser` (the last
edge function-local). A module the chooser imports joins that cycle as soon as it imports anything in it. So the job's
module may import what the chooser imports outside the cycle (`router_runtime`, `router_chooser`, `router.requests`,
`router_objective.*`, `db.*`), and must not import `objective_inputs` or the chooser. `_objective_job` today calls three
things from inside the cycle: `OI.decision_reads()`, `OI.build` (for the LLM's card) and `run_numeric`.

## 2. Plan (from step 0)

- `daily_plan/objective_seeds.py`: `numeric_seed` and `_without_miss_cause` (moved), `mix_seed(runtime, key,
  decision_id)` (the body of `ObjectiveChooser._seed`, used by the chooser and by `_mixed`), and the coin, which has no
  seed of its own, described there.
- `daily_plan/objective_job.py`: the constants, `NumericPolicy` (the job's answer: its `stage` and `carried` are the
  job's), `_pooled`, `_llm_forecasts`, `_wait_llm`, `_objective_job`, the carry registry and its helpers, the serve's
  reads of the job (`_numeric_answer`, `_with_carried`), `_defer_carry`, and three small functions for the chooser:
  start the job, await it, answer now with no models. What the job computes and cannot import (the LLM's request, the
  fit's read scope, the numeric policy) the chooser hands it as arguments.
- The two `_NoModels` class-name tests become an attribute of the entry; the four `__import__` calls a plain import.
