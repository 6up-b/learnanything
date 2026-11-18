# Refactor E5: the objective apart from the rollouts

Branch `refactor/e5-objective-apart`, based on main `d69880ac7b` (E1 to E4 landed). Step E5 of arc E
(`docs/specs/refactor_strategy_v3.md` §2.7, leaks 4 and 5). Structure track: no served or persisted value changes.
Line numbers in §1 are at the base, in `src/learnloop/router_objective/value.py` (1,731 lines) unless another file is
named.

## 1. Step 0: the reference graph of `value.py` at the base

`value.py` holds three things: what is optimized (the terms of one path and their sum, how a candidate's value and
the evaluation are reported), how a block is simulated (the draws, the state, the tail's sessions, the action
interfaces), and the link to adaptive difficulty's predictive. Between them sit the plain types every one of them
reads (a topic, a dated use, the learning parameters, an action, the frozen inputs).

Key to the class column: **O** objective (what is optimized), **R** rollouts (the arithmetic that simulates a
block), **A** the AD link, **T** a shared plain type. "Used inside" lists the module's own top-level names that
reference it; "src users" the four source importers (`objective_chooser`, `objective_inputs`, `objective_job`,
`trace_assembly`); "tests" the number of test files naming it through `V.`.

| Name | Lines | Used inside | src users | tests | Class |
|---|---|---|---|---|---|
| module docstring | 1-62 | — | — | — | R (it describes the rollouts: the cutoff, the tail, one clock, sampling, the action interfaces, the effect correction) |
| `OBJECTIVE_VERSION` | 78 | — | chooser, trace_assembly | 1 | O |
| `TAIL_VERSION` | 79 | — | chooser, trace_assembly | 0 | R |
| `TERMINAL_VERSION` | 80 | — | chooser, trace_assembly | 0 | O |
| `REVIEW`, `NEW_PRACTICE`, `READING`, `PROBE`, `REPAIR`, `TEACH_BACK`, `LESSON`, `STOP`, `SEQUENCE` | 83-93 | `KINDS`, `PRACTICE_KINDS`, `Action`, `_Model` | objective_inputs (all), chooser (`STOP`) | 0-9 each | T |
| `PRACTICE_KINDS` | 94 | `_Model` | — | 0 | T |
| `KINDS` | 95 | `Action` | — | 0 | T |
| `REFERENCE_REF` | 97 | `_Model`, `evaluate` | chooser | 0 | R |
| `MINUTES_PER_DAY` | 98 | `_Model` | — (registered: `router_objective_value:MINUTES_PER_DAY`) | 1 | R |
| `REVIEW_DRAW_VERSION` | 111 | — | trace_assembly | 1 | R |
| `AD_LINK_VERSION` | 113 | `AdLink` | trace_assembly | 1 | A |
| `AdLink` | 124-243 | `Inputs` (annotation) | objective_inputs | 5 | A |
| `_logsumexp` | 246-250 | `AdLink` | — | 0 | A |
| `Topic` | 254-272 | `Inputs` | objective_inputs | 15 | T |
| `DatedUse` | 276-282 | `Inputs`, `cutoff_for`, `_Model` | objective_inputs | 9 | T |
| `LessonCurve` | 286-319 | `Learning` (annotation) | objective_inputs | 1 | A |
| `CauseSplit` | 323-343 | `Learning` (annotation) | objective_inputs | 1 | T |
| `Learning` | 347-357 | `Inputs` | objective_inputs | 5 | T |
| `EffectSlope` | 361-367 | `Inputs` (annotation) | chooser | 1 | T |
| `Price` | 371-377 | `Inputs` (annotation) | objective_inputs | 13 | T |
| `Action` | 381-417 | `_Model`, `evaluate` | chooser, objective_inputs, objective_job | 12 | T |
| `Inputs` | 421-454 | `_Model`, `evaluate`, `baselines`, `gain` | chooser, objective_inputs, objective_job | 13 | T |
| `cutoff_for` | 457-458 | — | — | 1 | T |
| `_seed_int` | 464-465 | `_Streams`, `_Model` | — | 0 | R |
| `_Streams` | 468-491 | `_Model` | — | 0 | R |
| `_beta_draw`, `_betainc` | 494-534 | `_Model`; `_beta_draw` | — | 0 | R |
| `_Theta` | 541-551 | `_Model` | — | 0 | R |
| `_State`, `_STATE_FIELDS` | 555-578 | `_Model`; `_State` | — | 0 | R |
| `_LEDGER_FIELDS` | 581-582 | `_Ledger` | — | 0 | O |
| `_Ledger` | 586-629 | `_Model`, `_terms`, `baselines`, `gain` | — | 1 | O |
| `_Model` | 632-1534 | `evaluate`, `baselines`, `gain` | chooser (`_policy_request`'s reference row) | 12 | R |
| `Valued` | 1541-1553 | `Evaluation`, `evaluate`, `paired_standard_error` | — | 2 | O |
| `Evaluation` | 1557-1573 | `evaluate`, `numeric_choice` | chooser, objective_job | 3 | O |
| `_terms` | 1576-1589 | `_Model.value` (a lesson offer's branch terms), `evaluate` | — | 0 | O |
| `evaluate` | 1592-1648 | — | chooser | 15 | R |
| `paired_standard_error` | 1651-1657 | `numeric_choice` | trace_assembly | 0 | O |
| `numeric_choice` | 1660-1676 | — | chooser | 2 | O |
| `baselines` | 1679-1698 | — | chooser | 2 | R |
| `gain` | 1701-1721 | — | chooser | 5 | R |
| `__all__` | 1724-1731 | — | — | — | one per new module, each naming its own public names |

22 test files and three test helpers import the module as `V` (one, `test_ih2_lessons_compete`, also imports `PROBE`
and `REPAIR` by name); three more source files name it in a docstring (`adaptive_difficulty/priors.py`,
`adaptive_difficulty/readiness.py`, `daily_plan/lesson_offer.py`). Nothing imports it by `importlib` or a string; `params/parameter_registry.py` names its
path in `MODULE_INVENTORY` (`router_objective_value`) and registers `MINUTES_PER_DAY` under it; `pyproject.toml`'s
frozen-cycles contract names the edge `router_objective.value -> scheduling.fsrs`.

### The order the code forces

The rollouts read the objective, not the other way round. `_Model` accumulates every path into a `_Ledger` and,
inside a single candidate's simulation, compares values by the objective's sum `_Ledger.q`: a probe's repair
branch is chosen by `q` in the belief's world (`_probe_choice`), the probe's information and a stop's and an
offer's branches are reported by `q`, and a lesson offer's branch terms are `_terms` (`_Model.value`). So
`rollouts -> objective` is an edge the code already has, and `objective` may not import `rollouts`. `evaluate`,
`baselines` and `gain` each construct a `_Model`, so they cannot sit in `objective.py` without a cycle; they are the
rollouts' entry points (draws, batches, the deadline), and what they report is defined in `objective.py`
(`_Ledger.q`, `_terms`, `Valued.q`, `Evaluation.v`). `evaluate`'s body does not define the value: its one line that
does, `Valued(..., q_draws=ledger.q, terms=_terms(ledger, model), ...)`, builds the objective's row from the
objective's definitions.

### Names whose class is not obvious

| Name | Decision | Reason |
|---|---|---|
| `_Ledger` | objective | Its fields are the terms of one path and its `q`, `terminal` and `after` are the objective's form (`Q = R(t, σ] + V_tail + T_C`). The rollouts write the fields; the meaning is the objective's. |
| `Valued`, `Evaluation` | objective | The value of a candidate (`q` is the mean of its draws) and of the reference row (`v`), reported with the terms; nothing in them simulates. |
| `paired_standard_error`, `numeric_choice` | objective | They read only `Valued` and `Evaluation` (the precision of a difference of values, and `π_Q`'s argmax with its tie rule). Neither simulates; putting them with the rollouts would make the trace and the chooser import the simulation for a statistic of its output. |
| `evaluate`, `baselines`, `gain` | rollouts | Each builds a `_Model` and runs it (above). |
| `TERMINAL_VERSION` | objective | It versions what `T_C` means (the net continuation past the cutoff), a term. |
| `TAIL_VERSION`, `REVIEW_DRAW_VERSION`, `REFERENCE_REF` | rollouts | The tail policy the rollouts simulate, the practice outcome's draw, and the tail's next action's ref (`_Model.tail_action`, `evaluate`'s reference row). |
| `CauseSplit` | shared type | Slip or gap's slopes by the miss's cause: a learning parameter read through `Learning`, not AD's predictive. |
| `EffectSlope`, `Price` | shared type | Fields of `Inputs` (the effect correction's and the attention price's parameters), read by the rollouts; the price's integral itself is `_Model.cost`, rollouts' code. |
| `LessonCurve` | AD link | AD's lesson dose curve as the decision read it (the strategy names it beside `AdLink`); only `Learning` (as a field) and `_Model` (by attribute) read it. |
| `_logsumexp` | AD link | Only `AdLink` calls it. |

### Where `Topic`, `Inputs` and `Action` go

The strategy names "`objective_inputs` types". At this tip that is `daily_plan/objective_inputs.py`, which builds
these values from the vault. The rollouts and the objective live in `router_objective`, which may not import
`daily_plan`: the frozen cross-package cycles contract (`acyclic_siblings` at the package level) holds the edge
`daily_plan -> router_objective` and would break on its reverse, and `objective_inputs` is a member of the chooser's
import cycle (`objective_chooser -> objective_inputs -> lesson_offer -> policy -> objective_chooser`). Measured in
§5 (P5) by adding the edges the rollouts would need. So the shared types go to one small module,
`router_objective/types.py`, with the action kinds, `Topic`, `DatedUse`, `CauseSplit`, `Learning`, `EffectSlope`,
`Price`, `Action`, `Inputs` and `cutoff_for`.

### Import edges each destination would have

| Module | Imports |
|---|---|
| `router_objective/ad_link.py` | numpy, `math`, `dataclasses`, `router_objective.memory` (`sigmoid`) |
| `router_objective/types.py` | `dataclasses`, `typing`, `router_objective.memory` (`Combiner`), `router_objective.ad_link` (`AdLink`, `LessonCurve`, field types of `Inputs` and `Learning`) |
| `router_objective/objective.py` | numpy, `math`, `dataclasses`, `typing`: nothing of LearnLoop |
| `router_objective/rollouts.py` | numpy, `hashlib`, `math`, `time`, `dataclasses`, `router_objective.memory` (`Fsrs`, `logit`, `perform`, `sigmoid`), `scheduling.fsrs` (`retrievability_array`), `router_objective.objective`, `router_objective.types` |

`objective` is a leaf; `ad_link` reads only `memory`; `types` reads `ad_link` and `memory`; `rollouts` reads
`objective`, `types` and `memory`. No edge points back, so the four are acyclic, and none imports anything in an
import cycle (`memory` and `scheduling.fsrs` are in none).

## 2. What changed

Commits, in order (in this worktree, on `refactor/e5-objective-apart`):

1. `a921d2ee27`: step 0 (§1), before any edit.
2. `8ffa840b95`: the split, the importers, the registry and contract entries, and the tests that reached the moved
   names (§6).
3. `ee4e5bee01`: `tests/test_objective_terms.py` (§6).
4. `a016539ec0`: `_terms`'s one comment says why without naming a ruling; the structure golden.
5. `03fd594dd2`: `test_rofu_carried`'s three patches of `OC.V.evaluate`, which the first targeted run found (it
   reached the module through the chooser's alias and never imported it, so the script's pattern missed it).
6. This record, the vault note, the status row; then the regenerated references.

Mechanical edits by script, each exact-pattern and asserted to match: the four modules were written from the base's
exact line ranges of `value.py` (`git show d69880ac7b:...`, every line of it placed once except the docstring, the
imports, one section header and `__all__`, which each module writes anew), under hand-written headers; in the
importers, every `V.<name>` became `<alias>.<name>` by the name's new module (a continuation line aligned under a
bracket the rename moved was moved with it), and each `from learnloop.router_objective import value as V` became the
imports its scope uses. The rest are listed edits (§6) or Edit-tool changes.

### The split

| Module | Lines | Members (lines at the tip) |
|---|---|---|
| `router_objective/objective.py` | 189 | docstring 1-43; `OBJECTIVE_VERSION` 54, `TERMINAL_VERSION` 55; `_LEDGER_FIELDS` 58; `_Ledger` 62-106; `Valued` 109-122; `Evaluation` 125-142; `_terms` 145-158; `paired_standard_error` 161-167; `numeric_choice` 170-186 |
| `router_objective/rollouts.py` | 1,257 | docstring 1-67; `TAIL_VERSION` 97, `REFERENCE_REF` 99, `MINUTES_PER_DAY` 100, `REVIEW_DRAW_VERSION` 113 (with the switch notes for `merged_sessions`, `consistent_review_draw` and `held_ad_link`); `_seed_int`, `_Streams`, `_beta_draw`, `_betainc` 126-196; `_Theta`, `_State`, `_STATE_FIELDS` 202-240; `_Model` 243-1145; `evaluate` 1151-1207; `baselines` 1210-1229; `gain` 1232-1252 |
| `router_objective/ad_link.py` | 190 | docstring 1-7; `AD_LINK_VERSION` 20; `AdLink` 23-143; `_logsumexp` 146-150; `LessonCurve` 153-187 |
| `router_objective/types.py` | 211 | docstring 1-9; the action kinds, `PRACTICE_KINDS`, `KINDS` 21-33; `Topic` 36-55; `DatedUse` 58-65; `CauseSplit` 68-89; `Learning` 92-103; `EffectSlope` 106-113; `Price` 116-123; `Action` 126-163; `Inputs` 166-200; `cutoff_for` 203-204 |

`value.py` (1,731 lines) is gone: no fourth thing with a name was left in it. Git records it as renamed to
`rollouts.py`, which holds most of its lines.

**The import order**, stated in each module's docstring: `rollouts -> objective`, `rollouts -> types`,
`types -> ad_link`, and `ad_link`, `types` and `rollouts` read `memory`. `objective` imports nothing of LearnLoop.
`objective.py`'s docstring states the objective in plain words and gives one entry per term (what it rewards or
charges, its unit, where its inputs come from, and which rollout method accrues it).

**Placement of `evaluate`.** It is in `rollouts.py`, not `objective.py`, because it builds a `_Model`, and the
model must import the objective (§1, "The order the code forces"). What it reports is defined in `objective.py`:
`_Ledger.q` (the value of a path), `_terms` (what the trace records), `Valued.q` and `Evaluation.v`.

### Importers updated

| Where | Files | What |
|---|---|---|
| `src/learnloop/daily_plan` | 4 | `objective_chooser` (OBJ, ROL, OT), `objective_inputs` (ADL, OT), `objective_job` (OBJ, OT); `lesson_offer`'s docstring |
| `src/learnloop/router_objective` | 1 | `trace_assembly` (OBJ, ROL, ADL) |
| `src/learnloop/adaptive_difficulty` | 2 | docstrings naming the lesson interface (`priors`, `readiness`) |
| `src/learnloop/params` | 1 | `parameter_registry`: `MODULE_INVENTORY`'s `router_objective_value` becomes the four modules, and `MINUTES_PER_DAY` is registered as `router_objective_rollouts:MINUTES_PER_DAY` (a structural constant: never projected into a vault's `parameter_registry` rows, which hold decision parameters only) |
| `pyproject.toml` | 1 | the frozen-cycles contract's `router_objective.value -> scheduling.fsrs` becomes `router_objective.rollouts -> scheduling.fsrs` |
| `tests` | 30 | 22 test files and 3 helpers that imported `value as V`, plus `identity_pins_helpers` (one description string), `test_ro2_ad_raw_document_reads` and `test_ih4_preferences_inform_router` (file lists, §6) and the structure golden; `test_objective_terms` is new |

Aliases: `objective as OBJ`, `rollouts as ROL`, `ad_link as ADL`, `types as OT`.

## 3. Bodies that changed

P1 (AST identity of every moved definition against `git show d69880ac7b:src/learnloop/router_objective/value.py`,
scratch `ast_identity.py`): 48 of 49 top-level definitions identical. The one difference:

```
-def _terms(ledger: _Ledger, model: "_Model | None" = None) -> dict[str, float]:
+def _terms(ledger: _Ledger, model: Any = None) -> dict[str, float]:
```

`_terms` reads only `model.unmeasured`; naming `_Model` would make `objective.py` import the rollouts, the cycle §1
rules out. With argument annotations set aside it is identical too. After that, commit 4 rewrote its one comment
(`# RO6's landing ruling R7: ...` to a sentence saying why), which the AST does not see. Nothing else changed: the
moved comments and docstrings are the base's text, but `rollouts.py`'s module docstring, which is the base's module
docstring with its review names dropped and the order paragraph added.

## 4. Adding a term after the split

Take a hypothetical term, a reward for each topic practised during the action (a "practice credit"):

1. `objective.py`: a field in `_Ledger` with its comment, its name in `_LEDGER_FIELDS` (which `zeros`, `copy`, `mix`
   and `select` iterate, so the branch arithmetic needs nothing more), its sign in `_Ledger.q` (and in `after` or
   `terminal` if it accrues after the action), its mean in `_terms`, and a line in the module docstring.
2. `tests/test_objective_terms.py`: its sign in `SIGNS` (the first test fails until the ledger and the table agree),
   and the hand-worked sums.
3. `rollouts.py`: where the quantity accrues, in the `_Model` method that simulates it (`_segment` for the action's
   own interval, `run_tail` or `_session` for the continuation).
4. Nothing else in the router: the trace records `Valued.terms` whole (`trace_assembly.candidate_row`), so the new
   term is in every candidate's row with no change there. The readers that name a term (`stop_coin` and
   `trace.explain` read `kappa_integral`, `tail_data` reads `unmeasured_reward`, the lesson offer's section reads
   the branches' `kappa_integral`) change only if they need it.

A change to an existing term's sign, weight or inclusion in `q`, or to what the trace reports of it, is steps 1 and 2
alone: `objective.py` and its test, the strategy's target. A change in how a quantity is simulated is `rollouts.py`
alone. A term whose arithmetic is a new formula inside the simulation (as `κ`'s integral is `_Model.cost`) is step 3
as well. Moving those formulas into `objective.py` is not a move (each sits inside a masked, vectorized update), so this
step leaves them where they are. Any change that moves a served decision is a successor under
`docs/algorithm-change-playbook.md`.

## 5. Proofs

**P1. AST identity**: §3. 48 of 49 identical; `_terms` differs by one parameter annotation.

**P2. `evaluate` equality on recorded inputs.** How the inputs were recorded: the P-draw harness's ten synthetic
journeys (§5 P3) ran at the base with `value.evaluate`, `baselines` and `gain` wrapped to pickle each call's inputs,
actions and keyword options (no callable) before calling through: 371 calls, 365 distinct (scratch `pdraw.py`'s
record option; the wrapped runs' tables and prompts are byte-equal to the unwrapped base runs, so recording moved
nothing). No owner data. The replay (scratch `p2_replay.py`) takes, per scenario and entry point, three calls spread
over the journey (88 calls), and runs at fixed draws, with `keep_going` true and `max_draws` twice the draws so each
evaluation completes two batches (both recorded through `on_complete`), and a clock fixed at 0:

- each `evaluate` call as recorded; with each of the 8 combinations of `merged_sessions`, `consistent_review_draw`
  and `held_ad_link`, each with and without `unmeasured`; at a carried cutoff (`C − 0.37`, off the day grid); and,
  on one action of every kind and interface (review, new practice, reading, repair, teach-back, a probe with its
  repair, a probe on no valued topic, a lesson offer with delayed checks, a lesson offer whose declined branch is a
  follow-up, a plain offer, a sequence with a probe step, stop), under six input variants (as recorded; no AD link;
  the effect correction with forecasts; a return slope; a lesson curve off its prior with a cause split; dated uses
  crossed during the action and after it), each at three switch combinations;
- each `baselines` and `gain` call as recorded and at the 8 switch combinations.

1,602 cases. The output is every field of every `Evaluation` (both batches and the final one): each row's ref, kind,
choosable, every draw of `q`, the terms in their order, `extra` (branches, branch terms, the probe's choice per
result and its information, the return effect), `Q̄`, `V`, the reference row, the cutoff, the draw count, the seed and
`complete` (not `elapsed_ms`, which is wall time), and the baselines' and gain's dicts, with every float as its exact
hex, key order kept. Rows reached: review 1,710, lesson 1,620, new practice 1,350, probe 1,080, stop 1,044, repair 936,
reading, teach-back and sequence 540 each; `extra` sections: branches 4,284, branch terms 1,620, information 1,080,
return effect 90. Base (`d69880ac7b`'s `src`, a `git archive`) and tip: **byte-equal**, 32,741,316 bytes, sha256
`63fff4d0a70b88e5...f40a` on both.

**P3. P-draw.** E2's harness as E3 extended it (scratch `pdraw.py`, copied into this step's scratch; only its
work path changed, plus the record option P2 uses, off for these runs) on its ten scenarios: `both`, `coin`,
`llm_fails`, `llm_fails_ih5_off`, `no_models`, `guard`, `evidence`, `offers`, `contest`, `early` (31 runs). Base =
`d69880ac7b` (a `git archive` of its `src`, `tests`, `fixtures`, `migrations`); tip = this worktree at `18da825269`
(its code is `03fd594dd2`'s; later commits are documents). The same normalization as E2 to E4 (ULIDs, UUIDs, digests,
wall stamps, `_ms` keys, the code stamp). Every table (`router_objective_traces` with each trace's terms and values,
`router_decisions`, `decision_records`), every LLM prompt, every Decider call's state and questions and
`why <trace> --json`: **byte-equal on all ten**. The run counts and the decision path's connection opens and
statements are equal too (e.g. `both` 57 / 436, `no_models` 74 / 552, `early` 34 / 264), and equal to E4's record.
A second base run (with recording) was byte-equal to the first on `both`, `coin` and `early`.

**P4. Identity pins, pinned draws, router goldens.** `tests/test_identity_pins.py` and `tests/pinned_draws.py` are
unchanged in the diff, and no golden but the structure golden moved. `identity_pins_helpers.py` changed in one
description string only (site C3's consumer now names `router_objective/rollouts.py`); the sites' sources and pins
are untouched, and no pin moved: `tests/test_identity_pins.py` passes with nothing written (§7).

**P5. Structure.** Import cycles measured with untracked files included (`scripts/refactor_measures.py`'s sweep,
the step's `cycle_measure.py`): largest component 84 → 84, modules in any cycle 220 → 220, both member lists
identical at the base and the tip. None of the four modules is in a cycle; their LearnLoop imports are
`objective`: none; `ad_link`: `memory`; `types`: `ad_link`, `memory`; `rollouts`: `memory`, `objective`, `types`,
`scheduling.fsrs`. The placement of the shared types was measured with hypothetical edges (`cycle_whatif.py`, the
same sweep with edges added): at the base, `value -> daily_plan.objective_inputs` grows the chooser's cycle from 10
to 12 modules (modules in any cycle 220 → 223); at the tip, `rollouts -> objective_inputs` 220 → 222 (the cycle 10
→ 11), `types -> objective_inputs` 220 → 224; and either breaks the frozen cross-package contract (`router_objective`
and `daily_plan` are siblings with the edge one way). Largest component stays 84 in each, but modules would join a
cycle, so the types stay in `router_objective`. `tests/test_structure_ratchets.py` passes; the golden was rewritten:
stage-naming comment lines 2,354 → 2,353 (the comment in `_terms`), `value.py`'s 29 now `rollouts.py` 22, `types.py`
4, `objective.py` 1, `ad_link.py` 1. Functions over 200 lines: 71, unchanged. No file ceiling names these files.
`lint-imports --no-cache`: 43 kept, 0 broken.

**P-shadow: not required.** Replay, rebuild and upgrades (`substrate/replay.py`, `substrate/rebuild_orchestrator.py`,
the replayers, `ops/upgrades.py`) import none of the changed modules; P3 shows the tables they read unchanged.

## 6. Tests added and ported

**Added: `tests/test_objective_terms.py`** (13 tests, plain values, no vault or runtime; T3). Ledgers from binary
fractions, every expected number worked by hand: the ledger's fields are exactly the terms in the test's sign table;
each term alone contributes with its sign and only through `q` (`unmeasured` contributes nothing); a two-draw path's
`q`, `terminal` (`T_C`) and `after` (`E[V(x′)]`); `_terms`'s keys, order and means, with `unmeasured_reward` only
when the decision kept it apart; `Valued.q` as the mean of the draws and `Evaluation.v` as the reference row's (0 with
none); `π_Q`'s argmax and its tie rule within the paired precision by support order. Fail-first by mutation: with
`tail_cost` added instead of subtracted in `_Ledger.q`, three tests fail; with `_terms` reporting `terminal` as
`after`, one fails.

**Ported (P6, T4).** No test asserted on `value.py`'s source text by path except two file lists, and no assertion was
changed or loosened. Tests that patched a name of `value` patch it where it now lives; each is a job- or
deadline-shaped test whose port to plain values would be a rewrite, so they are repointed and listed:

| Test | Patched before | Now |
|---|---|---|
| `test_objective_refinement::_job` | `setattr(V, "evaluate", spy)` (the chooser's call, to count refinement batches) | `setattr(ROL, "evaluate", spy)` |
| `test_ro6_landing` (two tests), `test_rofu_carried` (three), `test_rofu_ad_link`, `test_rofu_review_draw`, `test_rofu_speed` | `setattr(OC.V, "evaluate" / name, ...)`, through the chooser's alias | `setattr(OC.ROL, ...)`: the same module attribute the chooser calls |
| `test_rospeed2_connections` (a clock charged per `sigmoid` call) | `sigmoid` in `value` and `memory` | in `rollouts`, `ad_link` and `memory`: `value`'s one global served both `AdLink` and `_Model`, which now each have their own, so both are patched and the charge per call is what it was |
| `test_rospeed_ad_link` (the same clock, with the landing code's helper) | `value`, `memory`, the helper | `rollouts`, `ad_link`, `memory`, the helper |
| `rospeed_ad_link_helpers._landing_code` | `V.AdLink`'s and `V._Model`'s methods replaced by the landing code's | the same classes, named in `ad_link` and `rollouts` |
| `test_ro6_codex_rereview::test_f3_...` | `V.Inputs.cutoff` replaced by a property | `OT.Inputs.cutoff` |
| `test_sg_slip_vs_gap` (no number compared in the split) | `inspect.getsource(V._Model._cause_gain)` | `ROL._Model._cause_gain` |
| `test_ih4_preferences_inform_router::test_...` (no preference read in the objective) | read `value.py`'s text | reads all four modules' text |
| `test_ro2_ad_raw_document_reads` (`ROOTS`, the walk's roots) | `value.py` | the four modules |

Every other test that named `V.<name>` calls the code with plain values already (`V._Model(inputs, ...)`,
`V.evaluate(...)`) and now names the module that defines it.

## 7. Targeted gate

All through the scratch `t.sh`, one command at a time, `-m "not arc_close" -n 3`, inside a 5 GB memory scope.

| Selection | Files | Result |
|---|---|---|
| `scripts/affected_tests.py --files` over the diff's source and test files (336; with `pyproject.toml` and the deleted `value.py` it answers "full suite", so those two were left out: every importer of `value.py` is in the diff), every `tests/test_*.py` whose text names `router_objective.value`, `import value`, `value as `, `evaluate(`, `AdLink`, `LessonCurve` or `_terms` at the base or the new modules at the tip (65), the rules block's files and `test_registry_audit`, `test_pinned_draws`, `test_public_tip_guards`, `test_affected_tests`; seven chunks of at most 60 | 370 | 7,426 passed, 33 skipped, 1 xfailed; 3 failed in the first run, all `test_rofu_carried` (`OC.V.evaluate`, fixed in `03fd594dd2`; the file then 7 passed) |
| After the last source commit: the rules block's gate files, `test_public_tip_guards`, `test_registry_audit`, `test_pinned_draws`, `test_objective_terms`, `test_rofu_carried` | 12 | 472 passed |

- `tests/test_identity_pins.py`: 340 passed, nothing written. `tests/test_structure_ratchets.py`: passes, golden
  rewritten (P5).
- `lint-imports --no-cache`: 43 kept, 0 broken. `ruff check`: all checks passed.
- The four vault validators pass (`db_validate_reference` errors `[]`; `desktop_validate`, `module_validate`,
  `validate_vault`: pass, 2,268 notes, all reachable from Home). `scripts/check_gate_partition.py`: 31,120 collected,
  landing 31,055 + arc_close 65.
- References regenerated after the source commits (notes for the four modules, `value`'s removed by hand: the
  generator does not delete); a second run changed nothing.
- Fail-first: the new test, by mutation (§6). Not run: the whole suite, durability, `--fresh-connections`,
  `arc_close`; the owner lane (no owner-lane test edited).

## 8. Line counts and the stop rule

| File | Base | Tip |
|---|---|---|
| `router_objective/value.py` | 1,731 | — |
| `router_objective/objective.py` | — | 189 |
| `router_objective/rollouts.py` | — | 1,257 |
| `router_objective/ad_link.py` | — | 190 |
| `router_objective/types.py` | — | 211 |

The four modules hold 1,847 lines against 1,731: the definitions moved verbatim (1,598 lines with their comments and
section headers), and the rest are the four module docstrings (126 lines, `objective.py`'s 43 being the objective in
plain words and one entry per term), their imports, `__all__` and blank lines. The other source files changed by 128
lines added and 118 removed (aliases, their imports and the realigned continuation lines; the registry's inventory
names four modules where it named one); the existing tests by 487 and 455, nearly all the same kind of edit.

Implementer: one Opus session, no subagents. Gate count: 370 targeted files once (7,426 tests), 12 gate files after the last source commit, 340 identity pins twice, P-draw at the base twice (20 runs each, one with recording) and at the tip once, and P2 at the base and the tip (1,602 cases each). What moved: every definition of a 1,731-line
module into four; nothing was removed, so the stop rule's cost per line removed does not apply to this step (a
structure step that removes no line). Token use is not visible from inside the session.

## 9. Judgment calls, and what E6 and F2 should know

**Judgment calls.**

1. **`evaluate`, `baselines` and `gain` are in `rollouts.py`, not `objective.py`.** The brief puts `evaluate`'s
   definition of the value in `objective.py`. The rollouts must import the objective (branches inside one
   simulation are compared by `_Ledger.q`, and a lesson offer's branch terms are `_terms`), and `evaluate` builds a
   `_Model`, so in `objective.py` it would close a cycle. What `evaluate` reports is defined in `objective.py`
   (`_Ledger.q`, `_terms`, `Valued`, `Evaluation`); its body stayed identical. The alternative, extracting the one line
   that builds a `Valued` row into an `objective.py` function, would change `evaluate`'s body for no reader's gain.
2. **The term formulas inside the simulation stay in `rollouts.py`.** `κ`'s integral (`_Model.cost`) and the dated
   and undated rewards are expressions inside masked, vectorized updates of `_Model`'s methods; moving them out is a
   restructuring, not a move, and would put F2's arithmetic in two modules. So "change a term is `objective.py` and
   its test" holds for a term's sign, weight, inclusion and report; a new simulated quantity also touches
   `rollouts.py` (§4). `objective.py`'s docstring names, for each term, the method that accrues it.
3. **The shared types are `router_objective/types.py`, not `daily_plan/objective_inputs.py`.** Measured (P5): either
   placement there puts `router_objective` modules into the chooser's cycle and breaks the package-level contract.
   `paired_standard_error` and `numeric_choice` went to `objective.py` (they read only values), and `CauseSplit`,
   `EffectSlope` and `Price` to the types (fields of the inputs), while `LessonCurve` went with `AdLink` as the
   strategy says. The private names `_Ledger` and `_terms` are now imported across modules; renaming them is E9's.

**For E6 (an action is one place).** An action kind's rollout step is in `rollouts.py`: `_Model.apply` (practice,
lesson, reading), `_Model._segment` (a probe observes), `_Model.value` (stop, offers, probes) and `_Model._steps`
(sequences); its kind constant and `Action`'s validation are in `types.py`. The chooser's per-kind code that builds
`Action`s is `daily_plan/objective_inputs.py`. `objective.py` knows no action kind.

**For F2 (the arithmetic).** All of the per-draw arithmetic is `rollouts.py`: `_Model` (the tail's sessions, the
graded attempts, the AD link's reads through `_linked_logit` and `_link_cells`) and the streams; `ad_link.py`'s
`AdLink.quadrature` is the link's own arithmetic. Nothing in `objective.py` runs per draw except the ledger's sums.
P2's harness (§5) is a ready byte-equality check for any change there: recorded inputs from the synthetic journeys,
every switch combination and every action kind, full output with floats in hex.

## 10. Not verified

- The owner's copies: P-draw and P2's inputs come from synthetic vaults (the harness's journeys), as E2 to E4's did.
- The whole suite, durability, `--fresh-connections` and `arc_close`: the orchestrator's gate.
