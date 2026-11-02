---
title: "learnloop.local_embeddings.student_decision"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/local_embeddings/student_decision.py"
source_paths:
  - "src/learnloop/local_embeddings/student_decision.py"
source_commit: "8cba03a7e83a7c265c84d68da164caacb76e4e25"
source_commit_timestamp: "2026-10-26T11:39:57-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.local_embeddings"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.local_embeddings.student_decision module"
  - "src/learnloop/local_embeddings/student_decision.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-local-embeddings"
---

# `learnloop.local_embeddings.student_decision`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.local_embeddings.student_decision` exists within [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] to own the behavior summarized by its module contract: The query student's decisions, as expected utility (spec_local_contextual_retrieval_v1 §9.1, §9.3, §9.5; P2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/local_embeddings/student_decision.py](../../../../../../src/learnloop/local_embeddings/student_decision.py) |
| Source lines | 359 |
| Owning package | [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `8cba03a7e83a7c265c84d68da164caacb76e4e25` |
| Commit timestamp | `2026-10-26T11:39:57-04:00` |

## Public API

- `in_time_probability(start_seconds: Sequence[float], remaining_s: float) -> float` ([source](../../../../../../src/learnloop/local_embeddings/student_decision.py), line 92) — P(a cold start answers within ``remaining_s``), KT-estimated from measured starts.
- `should_wait(start_seconds: Sequence[float], remaining_s: float, weight_share: float) -> tuple[bool, float]` ([source](../../../../../../src/learnloop/local_embeddings/student_decision.py), line 100) — Spec §5.1 item 3: wait for a starting student iff ``P(in time) > 1 / (1 + w)``.
- `late_draws(late: int, total: int, *, draws: int=DRAWS, seed: int=0) -> np.ndarray` ([source](../../../../../../src/learnloop/local_embeddings/student_decision.py), line 114) — Draws of ``p_late`` from measured counts (Jeffreys).
- `class ArmOutcomes` ([source](../../../../../../src/learnloop/local_embeddings/student_decision.py), line 125) — One arm's per-question outcomes on the bank: ``{question: value}``, value 1 (complete evidence in the top 10), 0, a soft label in [0, 1] (a label-noise model's probability), or None (unknown: latent).
- `bank_quality_draws(arm: ArmOutcomes, *, draws: int=DRAWS, seed: int=0) -> np.ndarray` ([source](../../../../../../src/learnloop/local_embeddings/student_decision.py), line 175) — Posterior draws of an arm's population CE@10: family rates partially pooled, unknown labels imputed from their family's posterior, families weighted by their question counts.
- `aggregate_arm(name: str, per_family: Mapping[str, tuple[float, int]]) -> ArmOutcomes` ([source](../../../../../../src/learnloop/local_embeddings/student_decision.py), line 196) — An arm known only by per-family aggregates (rate, n), such as a committed report's table: expanded into soft outcomes so the same model applies (unpaired, wider).
- `dev_quality_draws(agreements: Sequence[float], teacher_quality: np.ndarray, *, seed: int=0) -> np.ndarray` ([source](../../../../../../src/learnloop/local_embeddings/student_decision.py), line 210) — Development quality of a student run: its mean teacher top-10 agreement (a Jeffreys Beta on the soft counts) times the teacher's bank quality draws (:data:`PRIOR_BASIS`).
- `class ExchangeRate` ([source](../../../../../../src/learnloop/local_embeddings/student_decision.py), line 223) — A log-grid posterior over a positive rate (quality per dollar, or per GPU-hour).
  - `grid(self) -> tuple[np.ndarray, np.ndarray]` (line 236; public)
  - `mean(self) -> float` (line 248; public)
  - `draws(self, count: int=DRAWS, *, seed: int=0) -> np.ndarray` (line 252; public)
  - `observe(self, *, dq: float, cost: float, s: float, accepted: bool, what: str='') -> None` (line 256; public)
  - `as_dict(self) -> dict[str, Any]` (line 260; public)
  - `from_dict(cls, value: Mapping[str, Any]) -> 'ExchangeRate'` (line 265; public)
- `seeded_lambda() -> ExchangeRate` ([source](../../../../../../src/learnloop/local_embeddings/student_decision.py), line 270)
- `seeded_nu(mu: float, cap_hours: float, lam: ExchangeRate | None=None) -> ExchangeRate` ([source](../../../../../../src/learnloop/local_embeddings/student_decision.py), line 275)
- `class Action` ([source](../../../../../../src/learnloop/local_embeddings/student_decision.py), line 282) — One action's terms: quality draws plus its measured costs.
- `decide(actions: Sequence[Action], *, lam: np.ndarray | float, mu: np.ndarray | float, nu: np.ndarray | float=0.0) -> dict[str, Any]` ([source](../../../../../../src/learnloop/local_embeddings/student_decision.py), line 293) — ``argmax E[U]`` with ``P(best)``, each action's ``E[U]`` and the expected loss of acting now.
- `difference_sd(a: np.ndarray, b: np.ndarray) -> float` ([source](../../../../../../src/learnloop/local_embeddings/student_decision.py), line 321)
- `next_round_gain(points: Sequence[tuple[int, float, float]], next_budget: int, *, draws: int=DRAWS, seed: int=0) -> np.ndarray` ([source](../../../../../../src/learnloop/local_embeddings/student_decision.py), line 327) — Draws of the agreement gain at ``next_budget`` from ``(budget, mean, se)`` points, log-linear between the last two measured budgets (:data:`PRIOR_BASIS`).
- `continue_training(points: Sequence[tuple[int, float, float]], next_budget: int, *, hours: float, hours_left: float, teacher_quality: float, nu: float, seed: int=0) -> dict[str, Any]` ([source](../../../../../../src/learnloop/local_embeddings/student_decision.py), line 343) — Spec §9.3: train another round iff its expected quality gain beats its GPU-hours, inside the cap.

### Module constants

- `DECISION_VERSION` ([src/learnloop/local_embeddings/student_decision.py](../../../../../../src/learnloop/local_embeddings/student_decision.py), line 44)
- `DRAWS` ([src/learnloop/local_embeddings/student_decision.py](../../../../../../src/learnloop/local_embeddings/student_decision.py), line 47)
- `RATE_GRID_POINTS` ([src/learnloop/local_embeddings/student_decision.py](../../../../../../src/learnloop/local_embeddings/student_decision.py), line 49)
- `RATE_GRID_SPAN_SD` ([src/learnloop/local_embeddings/student_decision.py](../../../../../../src/learnloop/local_embeddings/student_decision.py), line 51)
- `LAMBDA_SEED_DECISIONS` ([src/learnloop/local_embeddings/student_decision.py](../../../../../../src/learnloop/local_embeddings/student_decision.py), line 56)
- `PRIOR_BASIS` ([src/learnloop/local_embeddings/student_decision.py](../../../../../../src/learnloop/local_embeddings/student_decision.py), line 60)

### Explicit exports

`__all__` declares:

- `Action`
- `ArmOutcomes`
- `DECISION_VERSION`
- `DRAWS`
- `ExchangeRate`
- `LAMBDA_SEED_DECISIONS`
- `PRIOR_BASIS`
- `aggregate_arm`
- `bank_quality_draws`
- `continue_training`
- `decide`
- `dev_quality_draws`
- `difference_sd`
- `in_time_probability`
- `late_draws`
- `next_round_gain`
- `seeded_lambda`
- `seeded_nu`
- `should_wait`

## Internal implementation anchors

- `_rng(seed: int) -> np.random.Generator` ([source](../../../../../../src/learnloop/local_embeddings/student_decision.py), line 87)
- `_family_counts(arm: ArmOutcomes) -> dict[str, tuple[float, int, int]]` ([source](../../../../../../src/learnloop/local_embeddings/student_decision.py), line 135) — ``family -> (soft successes, known count, unknown count)``.
- `_pooling(counts: Mapping[str, tuple[float, int, int]]) -> tuple[float, float]` ([source](../../../../../../src/learnloop/local_embeddings/student_decision.py), line 153) — ``(m, kappa)``: the pooled rate and the Beta concentration, by method of moments.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]] — imports `module`; statically calls `Action`, `ArmOutcomes`, `aggregate_arm`, `bank_quality_draws`, `continue_training`, `decide`, `dev_quality_draws`, `difference_sd`, `late_draws`, `seeded_lambda`, `seeded_nu`
- [[Reference/Modules/learnloop/source_retrieval/student_encoder|learnloop.source_retrieval.student_encoder]] — imports `module`; statically calls `should_wait`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `math`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]], [[Reference/Modules/learnloop/source_retrieval/student_encoder|learnloop.source_retrieval.student_encoder]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_query_student.py](../../../../../../tests/test_query_student.py) — direct import
  - `test_lateness_and_money_enter_the_utility_and_the_rates_learn_from_owner_choices`
  - `test_the_bank_posterior_pools_families_and_unknowns_widen_it`
  - `test_the_cold_start_rule_has_no_constant_of_its_own`
  - `test_the_scheduled_candidate_is_recommended_adopted_and_a_lost_reevaluation_recommends_withdrawal`
  - `test_training_continues_only_while_the_expected_gain_beats_the_gpu_hours`

## Modification guidance

- Make changes here when the responsibility remains student decision within learnloop.local_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/local_embeddings/student_decision.py](../../../../../../src/learnloop/local_embeddings/student_decision.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
