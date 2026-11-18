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


## 2. What changed

Commits, in order (in this worktree, on `refactor/e3-e4-chooser`):

1. `e89e3519bf`: step 0 (§1), before any edit.
2. `13925e8bbf`: the move, the test ports (§6) and the structure golden.
3. `4fa5f05bde`: comments and docstrings only, in the functions whose bodies changed: they say why without naming a
   ruling or a review. Stage-naming comment lines 2,368 to 2,362.
4. This record, the status row, the ledger's D-45 and the vault's router note; then the regenerated references.

Mechanical edits made by script (exact-pattern, each asserted to match once): the new module's moved definitions
were copied from the base's exact line ranges (`git show 69befd0430:...`), the moved ranges deleted from the chooser,
the four `__import__` calls and the `_mixed` seed expression replaced, and `ruff check --fix` removed the imports
the move left unused. Every other change is an Edit.

### `daily_plan/objective_seeds.py` (new, 100 lines)

| Definition | From | Lines | Body |
|---|---|---|---|
| `numeric_seed` | `objective_chooser.py:166-191` | 26 | identical |
| `_without_miss_cause` | `:194-228` | 35 | identical |
| `mix_seed(runtime, boundary_key, decision_id)` | `ObjectiveChooser._seed` (`:1407-1408`) and `_mixed`'s inline copy (`:1918`) | 5 | the same expression with `self.runtime` as a parameter |

The module's docstring says what each seed depends on and why they differ: the numeric seed hashes the boundary
identity only (less the seed-neutral and miss-cause keys), so a prefetch and its serve value a boundary on the same
draws; the mix's seed hashes the boundary key and the decision's fresh id, so each decision draws anew; the coin has
no seed of its own and draws from the mix's under stage names the mix never uses. The chooser imports `numeric_seed`
by name and calls it as its own module attribute, as before, so `tests/pinned_draws.py` (which wraps
`objective_chooser.numeric_seed`) and every test that replaces it there still reach every call; all four callers are
in the chooser. `mix_seed` calls `mix.seed_for` through its module, which `pinned_draws` wraps.

### `daily_plan/objective_job.py` (new, 495 lines)

| Definition | From | Lines | Body |
|---|---|---|---|
| `NUMERIC`, `PUBLISHED`, `CARRIED`, `CARRY_LIMIT`, `_CARRY_LOCK`, `_CARRY` | `:108-122` | 15 | identical |
| `NumericPolicy` | `:491-523` | 33 | identical (the job's answer: `stage` and `carried` are the job's) |
| `pooled` | `_pooled` (`:306-320`) | 15 | identical but its name (tests call it) |
| `_llm_forecasts` | `:790-802` | 13 | identical |
| `_objective_job` | `:805-927` | 101 | changed, below |
| `_with_carried` | `:930-948` | 19 | identical |
| `carry_on` | `_carry_on` (`:951-955`) | 5 | identical but its name |
| `_register_carry` | `:958-965` | 8 | identical |
| `drain_carry` | `_drain_carry` (`:968-989`) | 22 | identical but its name |
| `carried_for` | `_carried_for` (`:992-1025`) | 34 | identical but its name |
| `_wait_llm` | `:1028-1032` | 5 | identical |
| `_numeric_answer` | `:1035-1059` | 25 | identical |
| `job_answers` | `_decide_objective`'s first reads (`:1592-1597`) | 13 | the same statements, returning `(results, results_at, numeric)` |
| `start_job` | `_start_objective`'s `runtime.start(...)` (`:1573-1578`) | 23 | the same call; the budget read from `vault.config` |
| `await_job` | `choose`'s `_await(...)` (`:1480`) | 6 | the same call; `router.timeout_seconds` read here |
| `answer_without_models` | `choose`'s no-model branch (`:1483-1497`) | 23 | changed, below |
| `defer_carry` | `ObjectiveChooser._defer_carry` (`:1508-1533`) | 31 | changed, below |
| `join_carried`, `_CARRY_THREADS` | new | 17 | the carried threads' stop-and-join (§5, D-45) |

Public names are the ones another module calls (the chooser, the shared test helper, tests that call them with plain
values); the job's own helpers stay private.

### `daily_plan/objective_chooser.py`: 2,233 to 1,811 lines

- Removed: the definitions above, `ObjectiveChooser._seed`, `._defer_carry`, and `choose`'s job control.
- Added: `_policy_request(vault, repository, entry)` (31 lines), the LLM policy's request: the eight statements that
  were inside `_objective_job`'s LLM `try`, before its `start(LLM, ...)`, moved unchanged (AST-equal, statement for
  statement), with `material = entry.material`, `config = vault.config` and the `decision_card` import before them and
  `return policy_request` after. It stays in the chooser because it imports `objective_inputs` (the cycle, §1).
- `run_numeric`: `_carry_on(config)` twice becomes `J.carry_on(config)`; nothing else.
- `choose`: `J.await_job(...)` for `_await(...)`; the no-model branch builds the card and calls
  `J.answer_without_models` with `run_numeric` bound to the boundary's inputs (`functools.partial`) and the tail
  snapshot as a thunk.
- `_start_objective`: `J.start_job(..., reads=OI.decision_reads, build_policy_request=_policy_request,
  numeric_policy=run_numeric)` for `self.runtime.start(...)`.
- `_decide_objective`: `J.job_answers(entry, readiness)` for its first six lines; `J.carry_on`, `J.defer_carry(...,
  runtime=, sqlite_path=, config=)`, `mix_seed(self.runtime, ...)`, `isinstance(entry, _NoModels)`, `J.carried_for`.
- The restraint and follow-up gates: `utc_now_iso(self.clock)` for the four `__import__` calls; `_mixed`'s seed through
  `mix_seed`.
- `NUMERIC` and `NumericPolicy` are imported from the job's module, so `objective_chooser.NUMERIC`,
  `.NumericPolicy` and `.numeric_seed` keep their names (`__all__` unchanged).

## 3. Bodies that changed, and why

**`_objective_job`.** It calls three things from inside the chooser's import cycle (§1), which the job's module cannot
import without joining the cycle. The chooser now hands them over: `reads` (`OI.decision_reads`), `build_policy_request`
(`_policy_request`) and `numeric_policy` (`run_numeric`, the attribute `tests/pinned_draws.py` wraps, looked up when the
job starts). The diff, past the three new keyword parameters and the dropped `decision_card` import:

```
-    with _pooled(config), runtime.spend.metered(...), OI.decision_reads():
+    with pooled(config), runtime.spend.metered(...), reads():
...
             try:
-                built, actions, _sources = OI.build(...)
-                ... (eight statements, now _policy_request's body)
-                entry.material["policy_request"] = policy_request
-                start(LLM, policy_request, rq.parse_llm_policy)
+                start(LLM, build_policy_request(vault, repository, entry), rq.parse_llm_policy)
...
-        numeric = run_numeric(
+        numeric = numeric_policy(
-        carry = _carry_on(config)          +        carry = carry_on(config)
-            _drain_carry(sqlite_path, ...) +            drain_carry(sqlite_path, ...)
```

The order is the base's: the Decider's thread, the LLM's card and request (same thread, same reads scope, same
exception handling: a failure fails the LLM component with `card: <type>`), its thread, the numeric policy, the
release, the drain, the deferred valuations, the joins.

**`defer_carry`** (was the method): `self.repository.sqlite_path`, `self.runtime`, `self.vault.config` become the
parameters `sqlite_path`, `runtime`, `config`; `entry.__class__.__name__ == "_NoModels"` becomes
`isinstance(entry, _NoModels)`; the thread it starts is kept in `_CARRY_THREADS` (for `join_carried`). Its docstring
lost its ruling names (commit 3).

**`answer_without_models`** (was inline in `choose`): the same statements in the same order (the card is built first,
in the chooser; then `carry_on`, the deadline `runtime.clock() + router.timeout_seconds`, the tail snapshot, the numeric
policy, the `_NoModels` entry with `runtime.clock()`). The snapshot is a thunk so it is still read after the deadline is
set, as before: a test clock charged per connection (`test_rospeed2_connections`) would otherwise move the deadline.

**`mix_seed`**: `self.runtime` becomes a parameter.

**Why `isinstance` and not an attribute on the entry.** Either replaces the class-name test. An attribute means adding
one to `router_runtime.Prefetch` and `router_chooser._NoModels`; those two modules reach 1,258 of 1,433 test files
through `scripts/affected_tests.py`, against 139 for this step's own diff, for a value that the class already states.
`_NoModels` is the no-model entry's type, defined beside the runtime; the test now reads the type, not its name.

## 4. The KEEP items and what pins each

| Kept | How | Pinned by |
|---|---|---|
| Availability never depends on the LLM (RO4 review F1) | `run_numeric` publishes each complete uncorrected answer before any wait on the LLM (`publish` into `PUBLISHED`, unchanged); `_numeric_answer` serves it as `published_uncorrected` when the job is still out (moved unchanged) | `tests/test_ro4_codex_review.py::test_f1_the_numeric_answer_is_published_before_any_wait_on_the_llm`, `::test_f1_a_slow_llm_leaves_the_numeric_share_in_place`; P-draw `early` (§7) |
| Which numeric answer serves, at every timing | `_numeric_answer` and `_with_carried` moved unchanged; `job_answers` calls them in the base's order | `tests/test_rofu_carried.py::test_an_early_publication_served_keeps_its_carried_valuation` (publication served, its carry deferred, valued later); `test_ro4_codex_review` F1; P-draw `early` and the nine scenarios |
| The carry, including a choice that raises after it is registered | `defer_carry` is called where `_defer_carry` was: in `_decide_objective`, after the id is minted and before the seed and the choice; the registration is in `objective_job._register_carry` (the process-wide `_CARRY`), so a choice that raises leaves exactly the registration it left before | `tests/test_rofu_carried.py`, `tests/test_ro6_landing.py` (the deferred and censored backups), `tests/test_router_failure_records.py` (a planted raise in `mix.draw`, after the registration); P-draw `no_models` and `early` |
| Draw counts at fixed draw settings | the job still passes `keep_going` (the LLM out and the deadline ahead) and the deadline to the numeric policy; `pinned_draws` still replaces `keep_going` on `objective_chooser.run_numeric`, the attribute the job is handed | `tests/test_objective_refinement.py`, `tests/test_rospeed2_connections.py::test_the_pool_completes_more_draws_by_one_deadline_and_switched_off_is_mains`, `tests/test_pinned_draws.py` |
| Every seed's value | `numeric_seed` and `_without_miss_cause` AST-identical; `mix_seed` the same expression | `tests/test_identity_pins.py` (C3 `boundary.*`, C3b, unchanged golden), `tests/test_ih_numeric_seed.py`, `tests/test_pinned_draws.py`; P-draw |

## 5. D-45: the carried threads' stop-and-join

`objective_job.join_carried(timeout=None)` waits for the carried valuations running on threads of their own (a
no-model serve's) and says whether none is left. `tests/router_mixture_helpers.join_carried_valuations` now wraps
`objective_job.defer_carry` and calls it right after the registration, at the point where the old helper joined the
thread it found by name (inside the decision, before `carried_for` reads), so the twins' numbers and P-draw's
`no_models` scenario read the same carries as before. What D-45 still lacks: a host's close calling it (the sidecar's
`SidecarContext.close`) and a real stop (the drain's `V.evaluate` honouring a stop before its deadline, which is the
rollouts' code, E5's). The ledger row says so, with arc E's close as its deadline.

## 6. Tests ported (T4) and test helpers changed

No assertion was changed or loosened. Each port keeps what the test checks and moves only how it reaches the code:

| Test | Reached before | Now |
|---|---|---|
| `router_mixture_helpers.join_carried_valuations` (7 files use it) | wrapped `ObjectiveChooser._defer_carry`, joined the thread it found by name | wraps the job's public `defer_carry` and calls `join_carried()` after it, at the same point in the decision |
| `test_ih4_preferences_inform_router._twins_with_one_slow_carry` | replaced `OC._drain_carry` | replaces the job's public `drain_carry` |
| `test_rospeed2_connections` (three tests) | called `OC._pooled`; wrapped `OC._objective_job` to count a job's connection opens | call the job's public `pooled`; wrap the job each `RouterRuntime.start` is given for an objective boundary (the one with a numeric component) |
| `test_ro6_codex_review::test_f4_...` | wrapped `OC._objective_job` to queue a diagnosis as the job starts | the same through `RouterRuntime.start` |
| `test_instruct_handoff_ih0::test_a_slow_llm_within_the_wait_is_served_and_does_not_fall_back` | replaced `objective_chooser._await` to record its timeout | records `Prefetch.wait`'s timeout: still `[40.0]` (the router's 40 s, below the job's fresh 45 s budget) |
| `test_rofu_carried` | `OC.PUBLISHED` | `objective_job.PUBLISHED` (a public constant; `OC.NUMERIC` still exists) |
| `ih4_preferences_inform_router_helpers._pin`, `test_ro5_stop_coin::test_every_arm_off_at_the_tag_is_mvp_047_exactly`, `test_ro6_serving._pin` | replaced `OC._hash` to drop the version and the plan's id from every hashed identity, which reached the numeric seed's hash while the seed sat in the chooser | the same `_hash` patch for the key, plus `OC.numeric_seed` replaced by the production seed of the identity less the same two keys (the seed's reductions touch neither key, so the twins' seeds are what they were) |
| `identity_pins_helpers` (site C3, C3b) | site C3 named `objective_chooser.py::numeric_seed`; C3b recorded every `OC._hash` call, the last being the seed's inner hash | C3 names `objective_seeds.py::numeric_seed`; C3b records both modules' `_hash`, so the last recorded is again the seed's reduced identity and the pin keeps its bytes (it moved before this, which is how the dependency showed) |

Tests added: none for E3. The moves are proved by AST identity (§7, P5) and the behaviour by the existing tests in §4
and P-draw; `join_carried` is exercised by every user of the shared helper.

## 7. Proofs

**P1. P-draw.** E2's harness (its scratch `pdraw.py`, reused: the paths changed and one scenario added) on its nine
scenarios plus `early`, base = `69befd0430` (a `git archive` of its `src/`, `tests/`, `fixtures/`, `migrations/`),
tip = `13925e8bbf` (the later source commit changes comments and docstrings only). The same normalization as E2's (ULIDs,
UUIDs, digests, wall stamps, `_ms` keys, the code stamp). Every table, every LLM prompt, every Decider call's state and
questions and `why --json`, byte-equal after normalization:

| Scenario | Runs | Base vs tip |
|---|---|---|
| `both`, `coin`, `llm_fails`, `llm_fails_ih5_off`, `no_models`, `guard`, `evidence`, `offers`, `contest` | 3, 6, 3, 3, 3, 3, 3, 3, 2 | identical, each |
| `early` (new) | 2 | identical |

Two base runs of `early` and of `both` are byte-identical to each other, so the timing scenario is deterministic
under the harness. The decision path's cost (connection opens and statements on the deciding thread during
`_decide_objective`) is equal at base and tip on all ten (e.g. `both` 57 / 436, `no_models` 74 / 552, `early` 34 / 264).

`early` is the job's timing, expressed by events, not sleeps: the runtime runs jobs on threads (`inline=False`), the
LLM is held at every serve, the serve's wait ends when the numeric policy's early publication appears (the same patch of
`Prefetch.wait` as `tests/test_rofu_carried.py`), then the LLM is released and every job thread is joined before the next
step. It reaches: an early publication served (`published_uncorrected`, 8 times), the LLM's late answer discarded (a
`timeout` result at each serve), the publication's carried valuation deferred to the next boundary's job
(`deferred_to: next_prefetch`, 6), drained there and recorded in a later trace (`carried_for`, `q_status: valued`, 4).
What it does not reach: a model that has not answered by the prefetch's own deadline (40 s here) when the serve
comes; that path is `Prefetch.results()`'s timeout (in `router_runtime`, unchanged), and on the objective it is pinned
by `tests/test_ro4_codex_review.py::test_f1_a_slow_llm_leaves_the_numeric_share_in_place` (3 s serve wait).

**P2. Pinned draws and the router's goldens.** `tests/pinned_draws.py` unchanged (it still wraps
`objective_chooser.numeric_seed`, `.run_numeric` and `mix.seed_for`, which the chooser and the job still reach);
`tests/test_pinned_draws.py` passes; no golden regenerated except the structure golden (P3).
`tests/test_identity_pins.py`: 340 passed with nothing written (C3b needed the helper change in §6 to keep its bytes).

**P3. Structure.** Import cycles measured with untracked files included (`scripts/refactor_measures.py`'s sweep, E2's
`cycle_measure.py`): largest component 84 → 84, modules in any cycle 220 → 220, both member lists identical;
`daily_plan.objective_job` and `daily_plan.objective_seeds` are in no cycle (the job imports only `router_chooser`,
`router_runtime`, `router.requests` and `router_objective.{price,value}` at module level, and `db.*`,
`router_objective.{tail_serve,tail_data}`, `router_objective_switches` inside functions). `tests/test_structure_ratchets.py`
passes; golden lowered with `--write`: stage-naming comment lines 2,368 → 2,362; the per-file counts
`objective_chooser.py` 36 → 23 and `objective_job.py` 7 (a new key: comments moved with their code, then six
reworded). Functions over 200 lines: 71, unchanged (`run_numeric`, 206, stays in the chooser). `lint-imports --no-cache`:
43 kept, 0 broken.

**P4. Threads.** The job's threads (`learnloop-router-*`, `learnloop-objective-{decider,llm}`,
`learnloop-objective-carried`) are covered by `test_rofu_carried`, `test_ro4_codex_review` (F1's slow LLM),
`test_instruct_handoff_ih0` (a real thread runtime), `test_followup_next_matrix` and `test_pinned_draws` and
`test_ih4_preferences_inform_router` (the no-model carried thread, joined by the helper), `test_objective_refinement`,
`test_ro6_landing`, `test_router_failure_records`, `test_mobile_v2_objective_stop`. Run three times at `-n 3`
(`tests/thread_guard.py` active in every run): see §8.

**P5. AST identity** (scratch `ast_identity.py`, every moved definition against `git show 69befd0430:...`, identifiers
renamed where the move renamed them): 18 identical (`numeric_seed`, `_without_miss_cause`, the six constants,
`NumericPolicy`, `pooled`, `_llm_forecasts`, `_with_carried`, `carry_on`, `_register_carry`, `drain_carry`, `carried_for`,
`_wait_llm`, `_numeric_answer`); 3 changed, each in §3 (`_objective_job`, `defer_carry`, `mix_seed`). `_policy_request`'s
eight statements are AST-equal to the base job's LLM block. P-shadow is not required: replay, rebuild and upgrades import
none of the changed modules, and P1 shows the tables they read unchanged.

## 8. Targeted gate

All through the scratch `t.sh`, one command at a time, `-m "not arc_close" -n 3`, inside a 5 GB memory scope.

| Selection | Files | Result |
|---|---|---|
| `scripts/affected_tests.py --base 69befd0430` over the diff (139), every `tests/test_*.py` naming `objective_chooser`, `ObjectiveChooser`, `objective_job`, `objective_seeds`, `_drain_carry`/`drain_carry`, `run_numeric`, `numeric_seed`, `router_objective.trace`, `_offer_trace` or `plan_log` (37), and the rules block's files (`test_identity_pins`, `test_retired_config_identities`, `test_architecture`, `test_test_layout`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_structure_ratchets`, `test_public_tip_guards`, `test_pinned_draws`), with every edited test file among them; three chunks of at most 50 | 149 | 2,728 passed, 9 skipped, 1 xfailed, 0 failed |
| P4: the job's thread tests (§7), three runs | 10 | 196 passed, three times |

- `tests/test_identity_pins.py`: 340 passed, nothing written. `tests/test_structure_ratchets.py`: passes; golden lowered.
- `lint-imports --no-cache`: 43 kept, 0 broken. `ruff check`: all checks passed.
- The four vault validators pass (`db_validate_reference` errors `[]`; `desktop_validate`, `module_validate`,
  `validate_vault`: pass). `scripts/check_gate_partition.py`: 31,103 collected, landing 31,038 + arc_close 65.
- References regenerated after the source commits (new notes for `objective_job` and `objective_seeds`); a second run
  changed nothing.
- Fail-first: none applies (no behaviour fixed). The one dependency the step uncovered (C3b's helper reading the
  numeric seed's hash through the chooser's `_hash`) failed first, as §6 says, and was kept to its bytes.
- Not run: the whole suite, durability, `--fresh-connections`, `arc_close` (the orchestrator's gate); the owner lane
  (no owner-lane test edited).

## 9. Stop rule (owner, Nov 17)

Implementer: one Opus session (this one), E3 and E4 in sequence, no subagents. Gate count for E3: 149 targeted files
(2,728 tests) once, the 10 thread files three times, 340 identity pins, two P-draw sweeps (20 runs) plus two
determinism reruns. Removed from `objective_chooser.py`: 422 lines (2,233 → 1,811), of which 395 moved verbatim or with
the renames in §2 and 27 are the call sites that became calls into the job. The implementer's token use is not visible
from inside the session; the orchestrator has it.

## 10. Judgment calls, and what E4, E5 and E6 should know

**Judgment calls.**

1. **The job takes three callables from the chooser** (`reads`, `build_policy_request`, `numeric_policy`) rather than
   importing them, because importing `objective_inputs` (or the chooser) would put `objective_job` in the chooser's
   import cycle (§1). The LLM request's build therefore stays in the chooser as `_policy_request`, unchanged, and runs
   on the job's thread exactly where it ran.
2. **`run_numeric` stays whole in the chooser.** Its "scheduling half" is the arguments it is given; the two places
   that choose them (the job and the no-model branch) moved. Splitting its body would have moved the numeric policy's
   own code, which is E5's ground, and `tests/pinned_draws.py` wraps it where it is.
3. **`isinstance(entry, _NoModels)` instead of an attribute on the entry**, to keep `router_runtime` and
   `router_chooser` untouched (they reach almost the whole suite); the restraint gates' job control (`_mixed`'s own
   `run_numeric` deadline, its `_await` and `_NoModels`) is left where it is: E3 named the chooser, and the gates' path is
   the restraint's (E2 left `_mixed` off the core for the same reason).

**For E4.** After the choice, `_decide_objective` holds everything the trace needs: the `Choice`, `numeric`, `results`,
`w`/`weight_record`, `seed`, `policy_card`, and `J.carried_for(...)`, the one read of the write phase.

**For E5 (the objective apart from the rollouts).** `run_numeric` (206 lines) is still in the chooser with `day_price`,
`current_weight`, `generator_now`, `_preference_record`, `_rollout_options` and its switch helpers; the job hands it
`deadline`, `keep_going`, `forecasts`, `clock`, `publish` and `defer_carried`, which is the whole of its scheduling
interface. `NumericPolicy` now lives in `objective_job.py`; if E5 moves the numeric policy into `router_objective`, the
dataclass's `stage` and `carried` stay the job's and the rest is the policy's. A real stop for the carried thread (D-45)
needs `V.evaluate` to honour a stop signal, which is E5's code.

**For E6 (an action is one place).** The job knows no action kind. `_policy_request`, `_offer_option`,
`_contest_option` and `_option` (the LLM's option descriptions) stay in the chooser and are per-kind code E6 will want.

## 11. Not verified

- The owner's copies (P-draw ran on synthetic vaults, as E2's did).
- A sidecar shutting down while a carried thread runs (no host calls `join_carried` yet; D-45 keeps that open).
- The whole suite, durability, `--fresh-connections` and `arc_close`: the orchestrator's gate.
