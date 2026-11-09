---
title: "learnloop.evsi_calibration.multisim"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/evsi_calibration/multisim.py"
source_paths:
  - "src/learnloop/evsi_calibration/multisim.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.evsi_calibration"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.evsi_calibration.multisim module"
  - "src/learnloop/evsi_calibration/multisim.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-evsi-calibration"
---

# `learnloop.evsi_calibration.multisim`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.evsi_calibration.multisim` exists within [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] to own the behavior summarized by its module contract: Diagnostic episodes against any simulator family (stage ``evsi-multisim``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/evsi_calibration/multisim.py](../../../../../../src/learnloop/evsi_calibration/multisim.py) |
| Source lines | 412 |
| Owning package | [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class MultiSimSettings` ([source](../../../../../../src/learnloop/evsi_calibration/multisim.py), line 75)
  - `as_dict(self) -> dict[str, Any]` (line 90; public)
- `class World` ([source](../../../../../../src/learnloop/evsi_calibration/multisim.py), line 98) — A truth family over the bank's scenarios, and the families a system may be.
- `class FamilyLearner` ([source](../../../../../../src/learnloop/evsi_calibration/multisim.py), line 108)
- `draw_family_learners(world: World, settings: MultiSimSettings) -> list[FamilyLearner]` ([source](../../../../../../src/learnloop/evsi_calibration/multisim.py), line 133) — Flagged learners: a family state, then answers until the first wrong one.
- `true_loss(needs: Sequence[str], action: str, *, repair_minutes: float, unresolved: float) -> float` ([source](../../../../../../src/learnloop/evsi_calibration/multisim.py), line 170)
- `run_family_learner(world: World, spec: FamilyLearner, settings: MultiSimSettings, models: _Models) -> tuple[list[CheckRecord], list[EpisodeRecord]]` ([source](../../../../../../src/learnloop/evsi_calibration/multisim.py), line 187)
- `class MultiSimRun` ([source](../../../../../../src/learnloop/evsi_calibration/multisim.py), line 362)
- `run_family_simulation(world: World, settings: MultiSimSettings, *, learners: Sequence[FamilyLearner] | None=None, pool: ProcessPoolExecutor | None=None) -> MultiSimRun` ([source](../../../../../../src/learnloop/evsi_calibration/multisim.py), line 369)
- `with_policy(settings: MultiSimSettings, **changes: Any) -> MultiSimSettings` ([source](../../../../../../src/learnloop/evsi_calibration/multisim.py), line 398)

### Module constants

- `MULTISIM_VERSION` ([src/learnloop/evsi_calibration/multisim.py](../../../../../../src/learnloop/evsi_calibration/multisim.py), line 65)
- `SYSTEM_FAMILY` ([src/learnloop/evsi_calibration/multisim.py](../../../../../../src/learnloop/evsi_calibration/multisim.py), line 66)
- `SYSTEM_HAND_SET` ([src/learnloop/evsi_calibration/multisim.py](../../../../../../src/learnloop/evsi_calibration/multisim.py), line 67)

### Explicit exports

`__all__` declares:

- `MULTISIM_VERSION`
- `FamilyLearner`
- `MultiSimRun`
- `MultiSimSettings`
- `World`
- `draw_family_learners`
- `run_family_simulation`
- `true_loss`
- `with_policy`

## Internal implementation anchors

- `_seed(*parts: Any) -> int` ([source](../../../../../../src/learnloop/evsi_calibration/multisim.py), line 70)
- `class _Models` ([source](../../../../../../src/learnloop/evsi_calibration/multisim.py), line 117) — Per-process cache of scenario models (truth and systems).
- `_mass(belief: Mapping[str, float], needs: Sequence[str]) -> float` ([source](../../../../../../src/learnloop/evsi_calibration/multisim.py), line 183)
- `_run_chunk(payload: tuple[World, Sequence[FamilyLearner], MultiSimSettings]) -> tuple[list[CheckRecord], list[EpisodeRecord]]` ([source](../../../../../../src/learnloop/evsi_calibration/multisim.py), line 349)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/evsi_calibration/multifamily|learnloop.evsi_calibration.multifamily]] — imports `FamilyLearner`, `MULTISIM_VERSION`, `MultiSimRun`, `MultiSimSettings`, `SYSTEM_FAMILY`, `SYSTEM_HAND_SET`, `World`, `_Models`, `_seed`, `draw_family_learners`, `run_family_simulation`, `true_loss`, `with_policy`; statically calls `MultiSimSettings`, `World`, `_Models`, `_seed`, `draw_family_learners`, `run_family_simulation`, `true_loss`, `with_policy`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/diagnosis/robust_composition|learnloop.diagnosis.robust_composition]] — imports `module`; calls `build_ensemble`, `expected_information_gain`, `observed_update`
- [[Reference/Modules/learnloop/evsi_calibration/eedi|learnloop.evsi_calibration.eedi]] — imports `OPTIONS`
- [[Reference/Modules/learnloop/evsi_calibration/families|learnloop.evsi_calibration.families]] — imports `FamilyModel`, `ScenarioModel`
- [[Reference/Modules/learnloop/evsi_calibration/policies|learnloop.evsi_calibration.policies]] — imports `module`; calls `EpisodeState`, `PolicySettings`, `decide`, `identity_channel`, `mixture`
- [[Reference/Modules/learnloop/evsi_calibration/simulate|learnloop.evsi_calibration.simulate]] — imports `CheckRecord`, `EpisodeRecord`, `_member_quantiles`, `loss_table_for`; calls `CheckRecord`, `EpisodeRecord`, `_member_quantiles`, `loss_table_for`
- [[Reference/Modules/learnloop/evsi_calibration/world|learnloop.evsi_calibration.world]] — imports `ACTION_CONTINUE`, `HYP_KNOWS`, `Scenario`, `entropy`, `hand_set_row`, `route_for`; calls `entropy`, `hand_set_row`, `route_for`
- [[Reference/Modules/learnloop/scheduling/evsi|learnloop.scheduling.evsi]] — imports `module`; calls `evsi_for_conditionals`

### Platform and third-party dependencies

- Standard library: `__future__`, `concurrent`, `dataclasses`, `hashlib`, `math`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/evsi_calibration/multifamily|learnloop.evsi_calibration.multifamily]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_evsi_multisim.py](../../../../../../tests/test_evsi_multisim.py) — direct import
  - `test_every_family_and_a_cross_system_run_all_policies`
  - `test_the_family_loop_reproduces_the_single_family_loop_for_the_latent_class_family`
  - `test_the_multi_family_study_runs_every_episode_without_a_count_bound`
  - `test_true_loss_is_the_loss_table_for_one_need_and_charges_each_unaddressed_need`

## Modification guidance

- Make changes here when the responsibility remains multisim within learnloop.evsi_calibration; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/evsi_calibration/multisim.py](../../../../../../src/learnloop/evsi_calibration/multisim.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
