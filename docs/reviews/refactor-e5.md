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

`objective` is a leaf; `ad_link` reads only `memory`; `types` reads `ad_link` and `memory`; `rollouts` reads the
other three's two (objective, types). No edge points back, so the four are acyclic, and none imports anything in
an import cycle (`memory` and `scheduling.fsrs` are in none).
