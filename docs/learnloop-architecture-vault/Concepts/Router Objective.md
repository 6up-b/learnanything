---
title: Router Objective
aliases:
  - Router's Objective
  - Numeric Policy Objective
status: active
doc_version: 1.0.0
implementation_version: mvp-0.60
last_reviewed: 2026-11-18
source_commit: a016539ec01a722c265b16c80a96eb4a75c68a69
source_commit_timestamp: "2026-11-18T09:12:00-05:00"
source_paths:
  - src/learnloop/router_objective/objective.py
  - src/learnloop/router_objective/rollouts.py
  - src/learnloop/router_objective/ad_link.py
  - src/learnloop/router_objective/types.py
  - src/learnloop/daily_plan/objective_inputs.py
  - tests/test_objective_terms.py
  - tests/test_ro4_value.py
tags:
  - learnloop/concept
  - learnloop/scheduling
  - learnloop/policy
---

# Router Objective

The daily plan's block router mixes two policies (see [[Scheduling and Selection#The daily plan's block router]]). One of them, the numeric policy `π_Q`, picks the candidate with the highest estimated value under one objective. This note says what that objective is and where each part of it lives. The decision it feeds is recorded as in [[ADR-017 One decision record, one trace id, one entry point]]. The specification is `docs/specs/spec_router_objective_v1.md` §3 and §8.

## What is optimized

Each candidate is valued by the cold performance it buys at the learner's valued uses, minus the attention it costs. The horizon is one cutoff `C` shared by every candidate: the configured horizon, or the latest goal date if that is further. Past `C`, a further horizon is valued once. Rewards are valued uses: a goal's dated use of a topic, scored at its date, and each topic's undated uses at a constant daily density. The cost is the attention price, which rises with the session's active minutes. Every amount is in use-equivalents.

For one parameter draw, a candidate's value is its path's `q`:

```
q = crossed + undated − κ integral + tail reward − tail cost + terminal reward − terminal cost
```

A candidate's `Q̄` is the mean of `q` over the draws. `V` is the `Q̄` of the reference row, the tail's next action. `π_Q` takes the argmax of `Q̄`. Candidates within the paired standard error of the best are broken by support order.

## The terms

| Term | Rewards or charges | Inputs from | Accrued in |
|---|---|---|---|
| `crossed` | each dated use that falls during the action: its weight times the chance of performing it at its date, on the state before the action's effect | the goals' dated uses; the memory forecast (AD's ability, FSRS's retrievability, the combiner) | `_Model._segment` |
| `undated_action` | undated uses during the action before `C`: each topic's daily density times its chance of performing, times the days the action takes | `Topic.undated_density`; the memory forecast | `_Model._segment` |
| `kappa_action` | the attention price over the action's active minutes before `C`, `κ0·((m+d)² − m²)/(2m̄)` | `Inputs.price` (the day's `κ0`, the remembered minutes `m̄`); the session's minutes | `_Model._segment`, `_Model.cost` |
| `tail_reward` | valued uses, dated and undated, from the action's end to `C`, under the simulated continuation | as the two rewards above | `_Model.run_tail`, `_Model._score_dated` |
| `tail_cost` | the attention price of the continuation's sessions before `C` | as `kappa_action` | `_Model._session` |
| `terminal_reward`, `terminal_cost` | the same reward and price from `C` to `C + H`, including the action's own minutes past `C` (`T_C`) | as above | `_Model._segment`, `_Model.run_tail`, `_Model._session` |

The ledger also keeps `unmeasured`: the share of the undated rewards from topics no randomized check could measure. It is kept apart for the learned tail and is never added to `q`.

## Where each part lives

- **`router_objective/objective.py`**: what is optimized. The ledger's fields and their sum (`_Ledger.q`, `terminal`, `after`), `_terms` (each term's mean, which the trace records per candidate), `Valued`, `Evaluation`, `paired_standard_error` and `numeric_choice`. It imports nothing of LearnLoop.
- **`router_objective/rollouts.py`**: how a block is simulated. The common random numbers, the state, the tail's sessions, each action kind's interface (`_Model`), and the entry points `evaluate`, `baselines` and `gain`. It imports `objective.py`, because branches inside one simulation are compared by `q` (a probe's repair, a stop's and an offer's branches), and `types.py`.
- **`router_objective/ad_link.py`**: adaptive difficulty's predictive (`AdLink`) and its lesson dose curve (`LessonCurve`), as the decision read them.
- **`router_objective/types.py`**: the plain types all of them share: the action kinds, `Action`, `Inputs` and its parts. `daily_plan/objective_inputs.py` builds them from the vault.

## Changing a term

- **A term's sign, weight or inclusion in `q`**, or what the trace reports of it: `objective.py` and `tests/test_objective_terms.py`.
- **A new quantity to simulate**: also `rollouts.py`, where the quantity accrues. A new ledger field enters `_Ledger`, `_LEDGER_FIELDS`, `q` and `_terms`, and the trace records it through `_terms` with no change of its own.
- A change that moves a served decision follows `docs/algorithm-change-playbook.md`.
