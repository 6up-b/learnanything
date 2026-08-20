---
title: "learnloop.scheduling.shadow_components"
type: "module-reference"
status: "current"
refactor_status: "EVALUATION"
version: "1.0.0"
source_path: "src/learnloop/scheduling/shadow_components.py"
source_paths:
  - "src/learnloop/scheduling/shadow_components.py"
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
  - "learnloop.scheduling.shadow_components module"
  - "src/learnloop/scheduling/shadow_components.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/evaluation"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.shadow_components`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.shadow_components` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: P4 step 6 (DESCOPED, U-025) -- shadow predictive components + the deferred scored selector (spec_p4_controller_and_scale §7; design §B step 6, §F).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/shadow_components.py](../../../../../../src/learnloop/scheduling/shadow_components.py) |
| Source lines | 308 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `EVALUATION` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

> [!note] Evaluation-only authority
> This module computes shadow, audit, or offline evidence. Its outputs do not directly choose learner-facing actions unless a governed promotion path says otherwise.

## Public API

- `class ComponentPredictions` ([source](../../../../../../src/learnloop/scheduling/shadow_components.py), line 65)
  - `as_map(self) -> dict[str, float]` (line 71; public)
- `predict_components(candidate: Any, *, goal_weight: float=1.0) -> ComponentPredictions` ([source](../../../../../../src/learnloop/scheduling/shadow_components.py), line 79) — Deterministic pre-administration predictions for one candidate.
- `record_shadow_predictions(repository: Repository, *, decision_id: str | None, snapshot_hash: str, predictions: ComponentPredictions, model_version: str='shadow_components_v0', clock: Clock | None=None) -> dict[str, str]` ([source](../../../../../../src/learnloop/scheduling/shadow_components.py), line 101) — Log each predictive component + the composed selector as ZERO-authority shadow predictions.
- `class PromotionOutcome` ([source](../../../../../../src/learnloop/scheduling/shadow_components.py), line 137)
  - `__bool__(self) -> bool` (line 142; internal)
- `promote_component(repository: Repository, *, component: str, report: Any, incumbent_log_loss: float, margin: float=COMPONENT_PROMOTION_MARGIN, clock: Clock | None=None) -> PromotionOutcome` ([source](../../../../../../src/learnloop/scheduling/shadow_components.py), line 146) — Consider one predictive component for promotion.
- `promote_action_chooser(*_args: Any, **_kwargs: Any) -> PromotionOutcome` ([source](../../../../../../src/learnloop/scheduling/shadow_components.py), line 212) — STRUCTURAL GUARD (U-025 §7.4).
- `component_events(repository: Repository, component: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/shadow_components.py), line 242)
- `open_composed_selector_horizon(repository: Repository, *, horizon_days: int=COMPOSED_SELECTOR_TELEMETRY_HORIZON_DAYS, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/scheduling/shadow_components.py), line 257) — Register (idempotent) the time-box after which unpromoted composed-selector telemetry retires.
- `retire_expired_telemetry(repository: Repository, *, clock: Clock | None=None) -> list[str]` ([source](../../../../../../src/learnloop/scheduling/shadow_components.py), line 285) — Retire any open composed-selector horizon whose ``retires_at`` has passed.

### Module constants

- `PREDICTIVE_COMPONENTS` ([src/learnloop/scheduling/shadow_components.py](../../../../../../src/learnloop/scheduling/shadow_components.py), line 37)
- `MONOLITHIC_CHOOSER_PROMOTABLE` ([src/learnloop/scheduling/shadow_components.py](../../../../../../src/learnloop/scheduling/shadow_components.py), line 45)
- `COMPONENT_PROMOTION_MARGIN` ([src/learnloop/scheduling/shadow_components.py](../../../../../../src/learnloop/scheduling/shadow_components.py), line 49)
- `COMPOSED_SELECTOR_TELEMETRY_HORIZON_DAYS` ([src/learnloop/scheduling/shadow_components.py](../../../../../../src/learnloop/scheduling/shadow_components.py), line 53)
- `PROMOTION_EVIDENCE_PATH` ([src/learnloop/scheduling/shadow_components.py](../../../../../../src/learnloop/scheduling/shadow_components.py), line 56)

## Internal implementation anchors

- `_margin_value_hash(margin: float) -> str` ([source](../../../../../../src/learnloop/scheduling/shadow_components.py), line 206)
- `_append_component_event(repository: Repository, component: str, kind: str, detail: Mapping[str, Any], evidence_id: str | None, *, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/scheduling/shadow_components.py), line 222)
- `_parse(iso: str) -> datetime` ([source](../../../../../../src/learnloop/scheduling/shadow_components.py), line 307)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `retire_expired_telemetry`; statically calls `retire_expired_telemetry`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/params/sensitivity_certificates|learnloop.params.sensitivity_certificates]] — imports `module`; calls `PromotionEvidence`, `store_promotion_evidence`
- [[Reference/Modules/learnloop/scheduling/controller_store|learnloop.scheduling.controller_store]] — imports `module`; calls `persist_shadow_prediction`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_hash`; calls `canonical_hash`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

No direct learner/operator workflow is assigned. This module is offline, shadow-only, dormant, or a dependency reached only through the static consumers below.

Static participation evidence comes from [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_shadow_components.py](../../../../../../tests/test_shadow_components.py) — direct import
  - `test_component_promotion_emits_u022_evidence_and_feeds_inputs_only`
  - `test_component_promotion_refuses_when_not_beating_incumbent`
  - `test_component_promotion_refuses_without_enough_evidence`
  - `test_composed_selector_telemetry_is_time_boxed`
  - `test_monolithic_action_chooser_has_no_promotion_path`
  - `test_monolithic_action_chooser_refuses_even_a_wide_margin_report`
  - `test_predictions_use_no_post_administration_or_outcome_feature`
  - `test_shadow_predictions_have_zero_authority`
  - `test_single_open_telemetry_horizon_enforced_at_db`
  - `test_state_sync_retires_expired_telemetry_horizon`

## Modification guidance

- Change shadow components policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Keep this module's shadow/offline outputs decision-inert. Promotion into live policy requires the governed evidence and cutover path documented by its source contract.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/shadow_components.py](../../../../../../src/learnloop/scheduling/shadow_components.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
