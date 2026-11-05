---
title: "learnloop.daily_plan.objective_inputs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/objective_inputs.py"
source_paths:
  - "src/learnloop/daily_plan/objective_inputs.py"
source_commit: "workspace/uncommitted @ HEAD 220bb12fda841f33b5a7166e8f8bdd5266a28a25"
source_commit_timestamp: "2026-11-05T04:42:23-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop.daily_plan"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.daily_plan.objective_inputs module"
  - "src/learnloop/daily_plan/objective_inputs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.objective_inputs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.objective_inputs` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: Router objective RO4 (spec §8.1, §8.4-§8.6): the frozen belief one block decision values its candidates on.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/objective_inputs.py](../../../../../../src/learnloop/daily_plan/objective_inputs.py) |
| Source lines | 354 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 220bb12fda841f33b5a7166e8f8bdd5266a28a25` |
| Commit timestamp | `2026-11-05T04:42:23-05:00` |

## Public API

- `plan_minutes(repository: Any, plan_id: str | None) -> tuple[float, str]` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 55) — ``m̄`` and where it came from (the plan's remembered minutes: the learner's choice, carried, or a default).
- `action_for(vault: Any, repository: Any, candidate: BlockCandidate, *, practiced: set[str], spread: float) -> V.Action` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 188) — §8.1's interface for one candidate block.
- `build(vault: Any, repository: Any, *, state: PlanState, support: Sequence[str], candidates: Mapping[str, BlockCandidate], now_iso: str, kappa0: float=0.0, kappa_how: str='unset', sequences: Mapping[str, Sequence[BlockCandidate]] | None=None) -> tuple[V.Inputs, list[V.Action], dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 228) — The decision's frozen inputs, its actions in support order, and the sources the trace records.

### Module constants

- `LOG` ([src/learnloop/daily_plan/objective_inputs.py](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 36)
- `TOPIC_LIMIT` ([src/learnloop/daily_plan/objective_inputs.py](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 39)
- `RETURN_GAP_LIMIT` ([src/learnloop/daily_plan/objective_inputs.py](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 41)
- `DURATION_LIMIT` ([src/learnloop/daily_plan/objective_inputs.py](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 42)
- `_PROBE_MODES` ([src/learnloop/daily_plan/objective_inputs.py](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 43)

### Explicit exports

`__all__` declares:

- `DURATION_LIMIT`
- `RETURN_GAP_LIMIT`
- `TOPIC_LIMIT`
- `action_for`
- `build`
- `plan_minutes`

## Internal implementation anchors

- `_logit(p: float) -> float` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 46)
- `_days(later: datetime, earlier: datetime) -> float` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 51)
- `_goal_uses(vault: Any, repository: Any, now: datetime) -> tuple[dict[str, float], list[V.DatedUse], dict[str, Any], list[str]]` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 67)
- `_practiced(connection: Any, vault: Any) -> tuple[dict[str, list[dict[str, Any]]], list[str]]` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 96)
- `_mastery(connection: Any, los: Sequence[str]) -> dict[str, tuple[float, float]]` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 113)
- `_ad(vault: Any, repository: Any, los: Sequence[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 122)
- `_return_gaps(connection: Any, gap_minutes: float) -> list[float]` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 132)
- `_stop_accept(connection: Any, prior: tuple[float, float]) -> tuple[tuple[float, float], dict[str, int]]` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 144) — §4 row 7: an offered stop the learner took (an end, ``offered_stop_accepted``) or overrode (a ``stop_response``); Beta(a + taken, b + overridden).
- `_duration_spread(connection: Any) -> tuple[float, int]` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 162) — The pooled spread of the learner's own durations on the log scale (none observed: 0, the mean only).
- `_reading_los(vault: Any, repository: Any, candidate: BlockCandidate) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 173)
- `_step(action: V.Action) -> V.Action` ([source](../../../../../../src/learnloop/daily_plan/objective_inputs.py), line 221) — A block as one step of a sequence: a probe step is its observation alone (what follows it in the sequence, then the tail, is what uses the information), never a nested repair bundle.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `build`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/priors|learnloop.adaptive_difficulty.priors]] — imports `COLD_START_VARIANCE`, `DOSE_SCALES`, `GAMMA_PRIOR`, `READING_PRIORS`
- [[Reference/Modules/learnloop/adaptive_difficulty/readiness|learnloop.adaptive_difficulty.readiness]] — imports `decision_state_fields`; calls `decision_state_fields`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/daily_plan/types|learnloop.daily_plan.types]] — imports `BlockCandidate`, `PlanState`, `STOP_FOR_TODAY`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `resolve_goal_scope`; calls `resolve_goal_scope`
- [[Reference/Modules/learnloop/goals/use_weights|learnloop.goals.use_weights]] — imports `for_goal`; calls `for_goal`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `resolve_fsrs_weights`; calls `resolve_fsrs_weights`
- [[Reference/Modules/learnloop/router_objective/memory|learnloop.router_objective.memory]] — imports `module`; calls `Combiner`
- [[Reference/Modules/learnloop/router_objective/price|learnloop.router_objective.price]] — imports `module`; calls `session_active_minutes`
- [[Reference/Modules/learnloop/router_objective/value|learnloop.router_objective.value]] — imports `module`; calls `Action`, `DatedUse`, `Inputs`, `Learning`, `Price`, `Topic`
- [[Reference/Modules/learnloop/section_map|learnloop.section_map]] — imports `learning_objects_for_section`; calls `learning_objects_for_section`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `json`, `logging`, `math`, `statistics`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro4_codex_review.py](../../../../../../tests/test_ro4_codex_review.py) — direct import
  - `test_f8_a_reading_candidate_starts_from_ads_dose_position`

## Modification guidance

- Make changes here when the responsibility remains objective inputs within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/objective_inputs.py](../../../../../../src/learnloop/daily_plan/objective_inputs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
