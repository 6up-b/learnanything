---
title: "learnloop.scheduling.kinship_feature"
type: "module-reference"
status: "current"
refactor_status: "DORMANT"
version: "1.0.0"
source_path: "src/learnloop/scheduling/kinship_feature.py"
source_paths:
  - "src/learnloop/scheduling/kinship_feature.py"
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
  []
aliases:
  - "learnloop.scheduling.kinship_feature module"
  - "src/learnloop/scheduling/kinship_feature.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/dormant"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.kinship_feature`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.kinship_feature` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: P4 step 5 (DESCOPED, U-026) -- the heuristic LLM-judged soft-kinship FEATURE behind a planted-learner sim ADMISSION GATE (spec_p4_controller_and_scale §8; design §B step 5, §F).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/kinship_feature.py](../../../../../../src/learnloop/scheduling/kinship_feature.py) |
| Source lines | 526 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `DORMANT` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

> [!warning] Dormant or disabled boundary
> The source explicitly withholds live workflow authority. Its code/tests remain inspectable, but activation is a separate product and evidence decision.

## Public API

- `class KinshipScore` ([source](../../../../../../src/learnloop/scheduling/kinship_feature.py), line 76)
  - `as_dict(self) -> dict[str, Any]` (line 94; public)
- `ensure_model(repository: Repository, *, version: str=DEFAULT_MODEL_VERSION, scope: Mapping[str, Any] | None=None, consent: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/scheduling/kinship_feature.py), line 185) — Create (idempotent) the immutable kernel MODEL artifact row and its opening 'shadow' event.
- `familiarity_kernel_content_hash(version: str) -> str` ([source](../../../../../../src/learnloop/scheduling/kinship_feature.py), line 229)
- `model_row(repository: Repository, model_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/scheduling/kinship_feature.py), line 238)
- `active_model_id(repository: Repository, *, version: str=DEFAULT_MODEL_VERSION) -> str | None` ([source](../../../../../../src/learnloop/scheduling/kinship_feature.py), line 246)
- `score_kinship(repository: Repository, *, subject_surface_id: str, kin_surface_id: str | None, model_id: str | None=None, judge: Judge | None=None, bounds: Mapping[str, Any] | None=None, p1_conservative_discount: float=0.9, clock: Clock | None=None) -> KinshipScore` ([source](../../../../../../src/learnloop/scheduling/kinship_feature.py), line 256) — Compute + cache the kinship feature for one (subject, kin) surface pair.
- `cached_feature(repository: Repository, *, model_id: str, subject_surface_id: str, kin_surface_id: str | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/scheduling/kinship_feature.py), line 355)
- `is_admitted(repository: Repository, *, model_id: str | None=None) -> bool` ([source](../../../../../../src/learnloop/scheduling/kinship_feature.py), line 376) — True iff the kernel model has passed its sim admission gate (status ``simulation_validated``).
- `consulted_discount(repository: Repository, *, subject_surface_id: str, kin_surface_id: str | None, p1_conservative_discount: float, model_id: str | None=None) -> float` ([source](../../../../../../src/learnloop/scheduling/kinship_feature.py), line 389) — The independent-evidence discount a CONSUMER is allowed to act on.
- `class AdmissionOutcome` ([source](../../../../../../src/learnloop/scheduling/kinship_feature.py), line 430)
  - `__bool__(self) -> bool` (line 435; internal)
- `run_admission_gate(repository: Repository, *, model_id: str | None=None, sim_report: Any=None, scenario: Mapping[str, Any] | None=None, clock: Clock | None=None) -> AdmissionOutcome` ([source](../../../../../../src/learnloop/scheduling/kinship_feature.py), line 439) — Consume a planted-learner (repeat-vs-fresh) sim report and, if it shows the feature moves the discount correctly WITHOUT flipping a scheduling/certification decision, admit the model to ``simulation_validated`` (the only status a sim can grant, §8.4).

### Module constants

- `KERNEL_MODEL_KIND` ([src/learnloop/scheduling/kinship_feature.py](../../../../../../src/learnloop/scheduling/kinship_feature.py), line 48)
- `KERNEL_FEATURE_SCHEMA_VERSION` ([src/learnloop/scheduling/kinship_feature.py](../../../../../../src/learnloop/scheduling/kinship_feature.py), line 49)
- `DEFAULT_MODEL_VERSION` ([src/learnloop/scheduling/kinship_feature.py](../../../../../../src/learnloop/scheduling/kinship_feature.py), line 50)
- `ADMISSION_MIN_DISCOUNT_SHIFT` ([src/learnloop/scheduling/kinship_feature.py](../../../../../../src/learnloop/scheduling/kinship_feature.py), line 56)
- `ADMISSION_PARAM_PATH` ([src/learnloop/scheduling/kinship_feature.py](../../../../../../src/learnloop/scheduling/kinship_feature.py), line 57)
- `LIVE_ACTIVATION_ENABLED` ([src/learnloop/scheduling/kinship_feature.py](../../../../../../src/learnloop/scheduling/kinship_feature.py), line 67)
- `DEFAULT_BOUNDS` ([src/learnloop/scheduling/kinship_feature.py](../../../../../../src/learnloop/scheduling/kinship_feature.py), line 112)

## Internal implementation anchors

- `_clamp(value: float, lo: float, hi: float) -> float` ([source](../../../../../../src/learnloop/scheduling/kinship_feature.py), line 119)
- `_default_judge(subject_features: Mapping[str, Any], kin_features: Mapping[str, Any], bounds: Mapping[str, Any]) -> dict[str, float]` ([source](../../../../../../src/learnloop/scheduling/kinship_feature.py), line 123) — Deterministic stub judge: derive kinship from the SHARED strength of the two P1 soft-kinship vectors (element-wise min over the union, exactly P1's pairwise-warmth rule -- both surfaces must strongly exhibit the same feature).
- `_features_for(repository: Repository, surface_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/kinship_feature.py), line 155)
- `_hard_colliding(repository: Repository, subject: str, kin: str) -> bool` ([source](../../../../../../src/learnloop/scheduling/kinship_feature.py), line 162) — The kernel scores only NON-hard-colliding surfaces (§8.1).
- `_cache_feature(repository: Repository, model_id: str, score: KinshipScore, *, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/scheduling/kinship_feature.py), line 338)
- `_append_kernel_event(repository: Repository, model_id: str, kind: str, detail: Mapping[str, Any], *, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/scheduling/kinship_feature.py), line 509)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/scheduling/open_world_gate|learnloop.scheduling.open_world_gate]] — imports `module`; statically calls `is_admitted`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/familiarity|learnloop.learner.familiarity]] — imports `module`; calls `familiarity_projection_v1`, `warmth_score`
- [[Reference/Modules/learnloop/params/sensitivity_certificates|learnloop.params.sensitivity_certificates]] — imports `module`; calls `promote`, `promotion_evidence_from_sweep_report`
- [[Reference/Modules/learnloop/sim/kinship_admission|learnloop.sim.kinship_admission]] — imports `run_admission_sim`; calls `run_admission_sim`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_hash`; calls `canonical_hash`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

No direct learner/operator workflow is assigned. This module is offline, shadow-only, dormant, or a dependency reached only through the static consumers below.

Static participation evidence comes from [[Reference/Modules/learnloop/scheduling/open_world_gate|learnloop.scheduling.open_world_gate]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_kinship_feature.py](../../../../../../tests/test_kinship_feature.py) — direct import
  - `test_admission_emits_u022_promotion_evidence_and_only_reaches_sim_validated`
  - `test_admission_refuses_when_feature_does_not_move_the_discount`
  - `test_feature_conditions_only_on_pre_administration_info`
  - `test_firewall_does_real_work_warm_pair_would_move_discount_if_enabled`
  - `test_firewall_feature_is_consulted_by_nothing_even_after_admission`
  - `test_kernel_cannot_override_a_hard_collision`
  - `test_null_kin_self_feature_is_deduped`
  - `test_out_of_scope_falls_back_to_p1_never_zero`
- [tests/test_open_world_gate.py](../../../../../../tests/test_open_world_gate.py) — direct import
  - `test_condition_six_clears_only_after_kernel_admission`

## Modification guidance

- Change kinship feature policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- This module is explicitly dormant/disabled. Do not grant it live workflow authority without a product decision, activation evidence, and tests for the newly reachable path.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/kinship_feature.py](../../../../../../src/learnloop/scheduling/kinship_feature.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
