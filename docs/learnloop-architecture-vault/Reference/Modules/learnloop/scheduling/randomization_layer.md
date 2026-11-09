---
title: "learnloop.scheduling.randomization_layer"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/randomization_layer.py"
source_paths:
  - "src/learnloop/scheduling/randomization_layer.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.randomization_layer module"
  - "src/learnloop/scheduling/randomization_layer.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.randomization_layer`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.randomization_layer` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: P4 step 4 -- the single randomization layer (U-024, spec §9.3, design §B step 4).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/randomization_layer.py](../../../../../../src/learnloop/scheduling/randomization_layer.py) |
| Source lines | 421 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Assignment` ([source](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 82) — The result of one randomization draw (persisted; propensity logged first).
  - `as_dict(self) -> dict[str, Any]` (line 100; public)
- `grade_for(*, reversible: bool, commitment_unit: bool, carryover_modeled: bool) -> str` ([source](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 118) — The experiment grade (§9.3 label enforcement).
- `is_near_equivalent(values: Sequence[float], margin: float=EPSILON_TIE_MARGIN) -> bool` ([source](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 132) — True when the top-2 feasible values fall within ``margin`` fraction of the top (the ε near-equivalence test).
- `tied_set(refs: Sequence[str], values: Sequence[float], margin: float=EPSILON_TIE_MARGIN) -> list[str]` ([source](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 160) — The refs :func:`epsilon_tiebreak` randomizes over when the top is near-equivalent (sorted).
- `epsilon_tiebreak(repository: Repository | None, *, experiment_id: str, refs: Sequence[str], values: Sequence[float], seed: str, decision_id: str | None=None, reversible: bool=True, margin: float=EPSILON_TIE_MARGIN, clock: Clock | None=None) -> Assignment` ([source](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 188) — ε tie-break among feasible candidates (§9.3).
- `micro_randomize(repository: Repository | None, *, experiment_id: str, variants: Sequence[str], seed: str, reversible: bool, decision_id: str | None=None, clock: Clock | None=None) -> Assignment` ([source](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 239) — Micro-randomize among REVERSIBLE near-equivalent variants (MRT, §9.3).
- `commitment_parallel_assign(repository: Repository | None, *, experiment_id: str, commitment_id: str, variants: Sequence[str], seed: str, carryover_modeled: bool, clock: Clock | None=None) -> Assignment` ([source](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 280) — Assign a COMMITMENT to a variant for a durable intervention (§9.3).
- `model_mixture(*, experiment_id: str, support: Sequence[str], staged_ref: str, distributions: Mapping[str, Mapping[str, float] | None], weights: Mapping[str, float], epsilon: float, seed: str, decision_id: str | None=None) -> Assignment` ([source](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 318) — The ``model_mixture`` design (router R2b): reversible candidates only.
- `open_outcome_window(repository: Repository, *, decision_id: str | None, assignment: Assignment | None, card_ref: str | None, commitment_id: str | None=None, candidate_ref: str | None=None, anchor_kind: str='administration_committed', anchor_ref: str | None=None, next_spaced_cold_review_at: str | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 351) — Open a delayed outcome window anchored to the NEXT SPACED COLD REVIEW (§9.3).
- `feature_overlap_propensities(refs: Sequence[str], tied: Sequence[str], overlap: Sequence[str], q: float) -> dict[str, float]` ([source](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 380) — ``π(i) = (1 - q)·1[i∈T]/|T| + q·1[i∈O]/|O|`` (``q = 0`` when ``O`` is empty): exact.
- `reading_dose_propensities(feasible: Sequence[str], base: Mapping[str, float], floor: float) -> dict[str, float]` ([source](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 393) — ``π(v) = (1 - k·ε)·base(v) + ε`` over the ``k`` feasible variants (its own floor ``ε``).
- `draw_from(propensities: Mapping[str, float], u: float) -> str` ([source](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 412) — Invert the propensities' CDF over the variants in sorted order.

### Module constants

- `RANDOMIZATION_LAYER_VERSION` ([src/learnloop/scheduling/randomization_layer.py](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 54)
- `EPSILON_TIE_MARGIN` ([src/learnloop/scheduling/randomization_layer.py](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 60)
- `PROPENSITY_FLOOR` ([src/learnloop/scheduling/randomization_layer.py](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 67)
- `_GRADES` ([src/learnloop/scheduling/randomization_layer.py](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 69)
- `MODEL_MIXTURE` ([src/learnloop/scheduling/randomization_layer.py](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 70)
- `FEATURE_OVERLAP` ([src/learnloop/scheduling/randomization_layer.py](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 71)
- `READING_DOSE` ([src/learnloop/scheduling/randomization_layer.py](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 72)
- `ADMISSIBLE_DESIGNS` ([src/learnloop/scheduling/randomization_layer.py](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 73)

## Internal implementation anchors

- `_seed_int(seed: str) -> int` ([source](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 77)
- `_tied_set(refs: Sequence[str], values: Sequence[float], margin: float) -> list[str]` ([source](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 146)
- `_uniform_propensity(repository: Repository | None, n: int, *, floor: float, clock: Clock | None) -> tuple[float, bool]` ([source](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 166) — The uniform draw's true propensity 1/n, and whether it is below the dormant propensity floor: a thin support, bind-logged (U-022), never clamped (data capture A8: every design here draws uniformly over all n, so a clamped number would be false).
- `_thin(detail: dict[str, Any], thin_support: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 184)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/dose|learnloop.adaptive_difficulty.dose]] — imports `READING_DOSE`, `draw_from`, `reading_dose_propensities`; statically calls `draw_from`, `reading_dose_propensities`
- [[Reference/Modules/learnloop/adaptive_difficulty/selection|learnloop.adaptive_difficulty.selection]] — imports `feature_overlap_propensities`; statically calls `feature_overlap_propensities`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `module`; statically calls `epsilon_tiebreak`, `tied_set`
- [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]] — imports `module`; statically calls `epsilon_tiebreak`
- [[Reference/Modules/learnloop/sim/ad_synthetic|learnloop.sim.ad_synthetic]] — imports `draw_from`, `reading_dose_propensities`; statically calls `draw_from`, `reading_dose_propensities`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/params/parameter_registry|learnloop.params.parameter_registry]] — imports `module`; calls `record_bind`
- [[Reference/Modules/learnloop/router/mixture|learnloop.router.mixture]] — imports `module`; calls `component_distributions`, `draw`, `effective_weights`
- [[Reference/Modules/learnloop/scheduling/controller_store|learnloop.scheduling.controller_store]] — imports `module`; calls `open_outcome_window`, `persist_experiment_assignment`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `random`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/dose|learnloop.adaptive_difficulty.dose]], [[Reference/Modules/learnloop/adaptive_difficulty/selection|learnloop.adaptive_difficulty.selection]], [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]], [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]], [[Reference/Modules/learnloop/sim/ad_synthetic|learnloop.sim.ad_synthetic]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad3_dose_arm.py](../../../../../../tests/test_ad3_dose_arm.py) — direct import
  - `test_dose_offer_propensities_exact`
  - `test_draw_frequencies_match_propensities`
- [tests/test_ad_guard.py](../../../../../../tests/test_ad_guard.py) — direct import
  - `test_a_denied_dose_response_rolls_the_draw_back`
- [tests/test_randomization_layer.py](../../../../../../tests/test_randomization_layer.py) — direct import
  - `test_a_thin_support_logs_the_true_propensity_and_is_flagged`
  - `test_an_ordinary_support_is_not_flagged_and_its_receipt_is_unchanged`
  - `test_commitment_parallel_grade_depends_on_carryover_model`
  - `test_epsilon_tiebreak_is_deterministic_for_a_seed`
  - `test_epsilon_tiebreak_is_inert_when_not_near_equivalent`
  - `test_epsilon_tiebreak_randomizes_near_equivalents_with_logged_propensity`
  - `test_grade_for_enforcement`
  - `test_is_near_equivalent_margin`
  - `test_micro_randomize_only_on_reversible`
  - `test_outcome_window_anchored_to_next_spaced_cold_review`
  - `test_the_tie_break_above_twenty_candidates_logs_one_over_n`
- [tests/test_teacher_te1b_rereview_fixes.py](../../../../../../tests/test_teacher_te1b_rereview_fixes.py) — direct import
  - `test_staged_mode_draws_the_target_by_the_epsilon_tiebreak`
  - `test_the_staged_tiebreak_is_deterministic_without_a_near_tie`

## Modification guidance

- Change randomization layer policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/randomization_layer.py](../../../../../../src/learnloop/scheduling/randomization_layer.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
