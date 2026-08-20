---
title: "learnloop_sidecar.handlers.remediation"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/remediation.py"
source_paths:
  - "src/learnloop_sidecar/handlers/remediation.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-08-18"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.handlers.remediation module"
  - "src/learnloop_sidecar/handlers/remediation.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.remediation`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps remediation behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]]. Its public surface centers on `MisconceptionInput`, `EpisodeInput`, `start_remediation_handler`, `RepairStatusInput`, `ProbeOfferInput`, `causal_repair_status_handler`, `causal_probe_offer_action_handler`, `causal_probe_defer_handler` and 4 more public symbols.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/remediation.py](../../../../../../src/learnloop_sidecar/handlers/remediation.py) |
| Source lines | 294 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class MisconceptionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/remediation.py), line 31)
- `class EpisodeInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/remediation.py), line 35)
- `start_remediation_handler(ctx: SidecarContext, params: MisconceptionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/remediation.py), line 114)
- `class RepairStatusInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/remediation.py), line 144)
- `class ProbeOfferInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/remediation.py), line 149)
- `causal_repair_status_handler(ctx: SidecarContext, params: RepairStatusInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/remediation.py), line 157) — The single P2 repair-orchestration read (spec §6).
- `causal_probe_offer_action_handler(ctx: SidecarContext, params: ProbeOfferInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/remediation.py), line 184) — "Take the quick check" — enter the factor-aware episode and pin the probe.
- `causal_probe_defer_handler(ctx: SidecarContext, params: ProbeOfferInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/remediation.py), line 201) — "Not now" — persist the decline so the next attempt does not re-offer.
- `causal_teach_me_now_handler(ctx: SidecarContext, params: ProbeOfferInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/remediation.py), line 214) — "Teach me now" — explicit authorisation to repair under ambiguity.
- `prescribe_remediation_handler(ctx: SidecarContext, params: EpisodeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/remediation.py), line 238) — Prescribe the comparison passages AND record their delivery.
- `start_remediation_treatment_handler(ctx: SidecarContext, params: EpisodeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/remediation.py), line 270)
- `get_remediation_handler(ctx: SidecarContext, params: EpisodeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/remediation.py), line 289)

## Internal implementation anchors

- `_optional_case_payload(repository, misconception_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/remediation.py), line 39) — The case payload for either kind, or None when the id resolves to neither.
- `_case_dto(repository, case: Any, *, durable: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/remediation.py), line 59) — The one case shape every remediation RPC returns.
- `_episode_case_payload(repository, episode: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/remediation.py), line 94) — The case a remediation episode repairs, of EITHER kind.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `CausalRepairError`, `accept_probe_offer`, `causal_repair_status`, `defer_probe_offer`, `request_teaching_now`; calls `accept_probe_offer`, `causal_repair_status`, `defer_probe_offer`, `request_teaching_now`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `RemediationBlocked`, `RemediationError`, `case_value`, `episode_case`, `misconception_status_history`, `prescribe_remediation`, `record_prescription_delivery`, `start_remediation_episode`, `start_remediation_treatment`; calls `case_value`, `episode_case`, `misconception_status_history`, `prescribe_remediation`, `record_prescription_delivery`, `start_remediation_episode`, `start_remediation_treatment`
- [[Reference/Modules/learnloop/learner/surfaced_beliefs|learnloop.learner.surfaced_beliefs]] — imports `mark_belief_surfaced`; calls `mark_belief_surfaced`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `practice_item_detail`; calls `practice_item_detail`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_repair_sidecar_rpcs.py](../../../../../../tests/test_causal_repair_sidecar_rpcs.py) — direct import
  - `test_causal_repair_methods_are_registered_and_accept_the_client_payloads`
- [tests/test_coldness_receipt.py](../../../../../../tests/test_coldness_receipt.py) — direct import
  - `test_prescribe_handler_records_the_delivery`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/remediation.py](../../../../../../src/learnloop_sidecar/handlers/remediation.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
