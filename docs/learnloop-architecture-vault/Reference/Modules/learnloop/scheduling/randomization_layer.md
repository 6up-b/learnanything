---
title: "learnloop.scheduling.randomization_layer"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/randomization_layer.py"
source_paths:
  - "src/learnloop/scheduling/randomization_layer.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.randomization_layer` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: P4 step 4 -- the single randomization layer (U-024, spec §9.3, design §B step 4).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/randomization_layer.py](../../../../../../src/learnloop/scheduling/randomization_layer.py) |
| Source lines | 303 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class Assignment` ([source](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 57) — The result of one randomization draw (persisted; propensity logged first).
  - `as_dict(self) -> dict[str, Any]` (line 73; public)
- `grade_for(*, reversible: bool, commitment_unit: bool, carryover_modeled: bool) -> str` ([source](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 90) — The experiment grade (§9.3 label enforcement).
- `is_near_equivalent(values: Sequence[float], margin: float=EPSILON_TIE_MARGIN) -> bool` ([source](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 104) — True when the top-2 feasible values fall within ``margin`` fraction of the top (the ε near-equivalence test).
- `epsilon_tiebreak(repository: Repository | None, *, experiment_id: str, refs: Sequence[str], values: Sequence[float], seed: str, decision_id: str | None=None, reversible: bool=True, margin: float=EPSILON_TIE_MARGIN, clock: Clock | None=None) -> Assignment` ([source](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 149) — ε tie-break among feasible candidates (§9.3).
- `micro_randomize(repository: Repository | None, *, experiment_id: str, variants: Sequence[str], seed: str, reversible: bool, decision_id: str | None=None, clock: Clock | None=None) -> Assignment` ([source](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 200) — Micro-randomize among REVERSIBLE near-equivalent variants (MRT, §9.3).
- `commitment_parallel_assign(repository: Repository | None, *, experiment_id: str, commitment_id: str, variants: Sequence[str], seed: str, carryover_modeled: bool, clock: Clock | None=None) -> Assignment` ([source](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 241) — Assign a COMMITMENT to a variant for a durable intervention (§9.3).
- `open_outcome_window(repository: Repository, *, decision_id: str | None, assignment: Assignment | None, card_ref: str | None, commitment_id: str | None=None, candidate_ref: str | None=None, anchor_kind: str='administration_committed', anchor_ref: str | None=None, next_spaced_cold_review_at: str | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 279) — Open a delayed outcome window anchored to the NEXT SPACED COLD REVIEW (§9.3).

### Module constants

- `RANDOMIZATION_LAYER_VERSION` ([src/learnloop/scheduling/randomization_layer.py](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 36)
- `EPSILON_TIE_MARGIN` ([src/learnloop/scheduling/randomization_layer.py](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 42)
- `PROPENSITY_FLOOR` ([src/learnloop/scheduling/randomization_layer.py](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 47)
- `_GRADES` ([src/learnloop/scheduling/randomization_layer.py](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 49)

## Internal implementation anchors

- `_seed_int(seed: str) -> int` ([source](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 52)
- `_tied_set(refs: Sequence[str], values: Sequence[float], margin: float) -> list[str]` ([source](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 118)
- `_clamped_uniform_propensity(repository: Repository | None, n: int, *, floor: float, clock: Clock | None) -> float` ([source](../../../../../../src/learnloop/scheduling/randomization_layer.py), line 132) — Uniform propensity 1/n, guarded by the dormant propensity floor.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]] — imports `module`; statically calls `epsilon_tiebreak`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/params/parameter_registry|learnloop.params.parameter_registry]] — imports `module`; calls `record_bind`
- [[Reference/Modules/learnloop/scheduling/controller_store|learnloop.scheduling.controller_store]] — imports `module`; calls `open_outcome_window`, `persist_experiment_assignment`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `random`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_randomization_layer.py](../../../../../../tests/test_randomization_layer.py) — direct import
  - `test_commitment_parallel_grade_depends_on_carryover_model`
  - `test_epsilon_tiebreak_is_deterministic_for_a_seed`
  - `test_epsilon_tiebreak_is_inert_when_not_near_equivalent`
  - `test_epsilon_tiebreak_randomizes_near_equivalents_with_logged_propensity`
  - `test_grade_for_enforcement`
  - `test_is_near_equivalent_margin`
  - `test_micro_randomize_only_on_reversible`
  - `test_outcome_window_anchored_to_next_spaced_cold_review`
  - `test_propensity_floor_binds_and_is_logged`

## Modification guidance

- Change randomization layer policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/randomization_layer.py](../../../../../../src/learnloop/scheduling/randomization_layer.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
