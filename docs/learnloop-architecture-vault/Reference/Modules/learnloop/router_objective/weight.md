---
title: "learnloop.router_objective.weight"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/weight.py"
source_paths:
  - "src/learnloop/router_objective/weight.py"
source_commit: "838d8ee1fcee48de3b5b41f59e451f042ec9a690"
source_commit_timestamp: "2026-11-05T04:03:05-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router_objective"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router_objective.weight module"
  - "src/learnloop/router_objective/weight.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.weight`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.weight` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO4 §8.7: learning the weight ``w`` between the two policies from one common return, frozen before the draw.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/weight.py](../../../../../../src/learnloop/router_objective/weight.py) |
| Source lines | 197 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `838d8ee1fcee48de3b5b41f59e451f042ec9a690` |
| Commit timestamp | `2026-11-05T04:03:05-05:00` |

## Public API

- `class Seeds` ([source](../../../../../../src/learnloop/router_objective/weight.py), line 50)
  - `from_config(cls, config: Any) -> 'Seeds'` (line 58; public)
  - `p0(self) -> float` (line 67; public)
  - `m0(self) -> float` (line 71; public)
- `class Use` ([source](../../../../../../src/learnloop/router_objective/weight.py), line 76) — One frozen use of a decision's common return.
- `class Scored` ([source](../../../../../../src/learnloop/router_objective/weight.py), line 90)
- `score(*, d_taken: float, mu_taken: float, uses: Sequence[Use], cost: float, cost_baseline: float) -> float` ([source](../../../../../../src/learnloop/router_objective/weight.py), line 98) — ``D̂_i`` for one decision whose window has closed (module docstring).
- `carries_score(*, uses: Sequence[Use], failed: Sequence[str], d_taken: float, d_all: Mapping[str, float]) -> str | None` ([source](../../../../../../src/learnloop/router_objective/weight.py), line 110) — None when the decision carries a score, else why not (§8.7 "What carries no score").
- `class Posterior` ([source](../../../../../../src/learnloop/router_objective/weight.py), line 123)
  - `as_dict(self) -> dict[str, Any]` (line 132; public)
- `posterior(scores: Iterable[Scored], seeds: Seeds, *, at: str | None=None) -> Posterior` ([source](../../../../../../src/learnloop/router_objective/weight.py), line 141) — The Gaussian posterior over ``Δ`` from the closed scores (those whose window closed before ``at``).
- `unique_assessments(links: Iterable[tuple[str, str]]) -> int` ([source](../../../../../../src/learnloop/router_objective/weight.py), line 181) — The report's count of unique completed assessments: one check linked to several decisions counts once (``links``: ``(assessment id, decision id)``).
- `weight(p: float, seeds: Seeds) -> float` ([source](../../../../../../src/learnloop/router_objective/weight.py), line 188) — ``w_i = ℓ_L + (1 − ℓ_L − ℓ_Q)·p_i``: posterior probability matching at the policy level.

### Module constants

- `WEIGHT_VERSION` ([src/learnloop/router_objective/weight.py](../../../../../../src/learnloop/router_objective/weight.py), line 38)
- `NO_RANDOMIZED_USE` ([src/learnloop/router_objective/weight.py](../../../../../../src/learnloop/router_objective/weight.py), line 40)
- `FALLBACK` ([src/learnloop/router_objective/weight.py](../../../../../../src/learnloop/router_objective/weight.py), line 41)
- `AGREE` ([src/learnloop/router_objective/weight.py](../../../../../../src/learnloop/router_objective/weight.py), line 42)
- `PENDING` ([src/learnloop/router_objective/weight.py](../../../../../../src/learnloop/router_objective/weight.py), line 43)
- `NO_RESULT` ([src/learnloop/router_objective/weight.py](../../../../../../src/learnloop/router_objective/weight.py), line 44)
- `_NORMAL` ([src/learnloop/router_objective/weight.py](../../../../../../src/learnloop/router_objective/weight.py), line 46)

### Explicit exports

`__all__` declares:

- `AGREE`
- `FALLBACK`
- `NO_RANDOMIZED_USE`
- `NO_RESULT`
- `PENDING`
- `Posterior`
- `Scored`
- `Seeds`
- `Use`
- `WEIGHT_VERSION`
- `carries_score`
- `posterior`
- `score`
- `unique_assessments`
- `weight`

## Internal implementation anchors

- `_parse(stamp: str) -> datetime` ([source](../../../../../../src/learnloop/router_objective/weight.py), line 137)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `Scored`, `posterior`, `unique_assessments`, `weight`
- [[Reference/Modules/learnloop/router_objective/calibration_report|learnloop.router_objective.calibration_report]] — imports `module`; statically calls `posterior`, `unique_assessments`, `weight`
- [[Reference/Modules/learnloop/router_objective/scores|learnloop.router_objective.scores]] — imports `module`; statically calls `Scored`, `Use`, `carries_score`, `score`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `math`, `statistics`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]], [[Reference/Modules/learnloop/router_objective/calibration_report|learnloop.router_objective.calibration_report]], [[Reference/Modules/learnloop/router_objective/scores|learnloop.router_objective.scores]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro4_weight.py](../../../../../../tests/test_ro4_weight.py) — direct import
  - `test_a_check_linked_to_ten_decisions_counts_once`
  - `test_the_numeric_policy_gains_nothing_from_a_wrong_critic`
  - `test_the_prior_gives_w_its_seed_and_w_stays_inside_its_minimum_shares`
  - `test_the_scores_mean_matches_a_planted_delta_and_is_zero_under_a_null`
  - `test_w_reads_no_score_from_a_window_still_open_and_needs_two_bins`
  - `test_what_carries_no_score`
- [tests/test_ro5_checks.py](../../../../../../tests/test_ro5_checks.py) — direct import
  - `test_a_coin_forced_decision_a_fallback_and_agreement_carry_no_score`
  - `test_w_moves_off_its_prior_on_closed_scores_in_two_bins`
- [tests/test_ro5_codex_review.py](../../../../../../tests/test_ro5_codex_review.py) — direct import
  - `test_f5_the_check_arm_off_restores_ro4s_weight_after_scores_accumulated`
  - `test_f6_a_fractional_delay_is_scored_on_the_goals_own_date`

## Modification guidance

- Make changes here when the responsibility remains weight within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/weight.py](../../../../../../src/learnloop/router_objective/weight.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
