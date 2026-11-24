---
title: "learnloop.followup_run.contract_job"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/followup_run/contract_job.py"
source_paths:
  - "src/learnloop/followup_run/contract_job.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.followup_run"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.followup_run.contract_job module"
  - "src/learnloop/followup_run/contract_job.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-followup-run"
---

# `learnloop.followup_run.contract_job`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.followup_run.contract_job` exists within [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] to own the behavior summarized by its module contract: Bind the shared contract step to the workflow's existing durable retry slot.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/followup_run/contract_job.py](../../../../../../src/learnloop/followup_run/contract_job.py) |
| Source lines | 178 |
| Owning package | [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class CorrectionDeferred(AuthoringRejected)` ([source](../../../../../../src/learnloop/followup_run/contract_job.py), line 32) — The shared step recorded an owed correction for the next job lease.
- `correction_receipts(repository: Repository, workflow_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/followup_run/contract_job.py), line 36) — Only this job's completed authoring operations, never physical children.
- `has_saved_correction(repository: Repository, workflow_id: str) -> bool` ([source](../../../../../../src/learnloop/followup_run/contract_job.py), line 49) — Allow a read-only recovery past the lease cap; request() still forbids sends.
- `class JobContract` ([source](../../../../../../src/learnloop/followup_run/contract_job.py), line 68)
  - `stopped(self) -> bool` (line 77; public)
  - `remaining(self) -> float` (line 82; public)
  - `admitted(self) -> bool` (line 85; public)
  - `request(self, client: Any, context: FollowupProbeContext, refs: Mapping[str, str], validate: Callable[[FollowupProbeAuthored], Any]) -> FollowupProbeAuthored` (line 93; public)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]] — imports `CorrectionDeferred`
- [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]] — imports `CorrectionDeferred`, `JobContract`, `has_saved_correction`; statically calls `JobContract`, `has_saved_correction`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInvalidOutput`; calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `ModelCheckpoint`, `content_key`, `model_settings`; calls `ModelCheckpoint`, `content_key`, `model_settings`
- [[Reference/Modules/learnloop/ai/structured_contracts|learnloop.ai.structured_contracts]] — imports `ContractFailure`, `RecoveryAllowance`, `RecoveryState`, `checked_structured_call`, `recover_from_receipts`, `recovery_note`; calls `RecoveryAllowance`, `RecoveryState`, `checked_structured_call`, `recover_from_receipts`, `recovery_note`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/followup_serve|learnloop.db.stores.followup_serve]] — imports `module`; calls `generation_job`
- [[Reference/Modules/learnloop/db/stores/model_calls|learnloop.db.stores.model_calls]] — imports `insert_checkpoint`; calls `insert_checkpoint`
- [[Reference/Modules/learnloop/diagnosis/ai_contracts|learnloop.diagnosis.ai_contracts]] — imports `FollowupProbeAuthored`, `FollowupProbeContext`
- [[Reference/Modules/learnloop/followup_run/authoring|learnloop.followup_run.authoring]] — imports `AUTHORING_PURPOSE`, `AuthoringRejected`, `authoring_contract`, `module`; calls `AuthoringRejected`, `authoring_contract`, `followup_probe_prompt`
- [[Reference/Modules/learnloop/followup_serve/workflow|learnloop.followup_serve.workflow]] — imports `module`; calls `get`, `note`, `noted`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]], [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/ih2_lessons_compete_helpers.py](../../../../../../tests/ih2_lessons_compete_helpers.py) — imports consumer [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]]
- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — imports consumer [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]]
- [tests/test_followup_reserved_only.py](../../../../../../tests/test_followup_reserved_only.py) — imports consumer [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]]
- [tests/followup_rival_factor_helpers.py](../../../../../../tests/followup_rival_factor_helpers.py) — imports consumer [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]]
- [tests/followup_serve_helpers.py](../../../../../../tests/followup_serve_helpers.py) — imports consumer [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]]
- [tests/teacher_te2_probes_helpers.py](../../../../../../tests/teacher_te2_probes_helpers.py) — imports consumer [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]]
- [tests/test_followup_authoring_retry.py](../../../../../../tests/test_followup_authoring_retry.py) — imports consumer [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]]
- [tests/test_followup_contract_recovery.py](../../../../../../tests/test_followup_contract_recovery.py) — imports consumer [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]]
- [tests/test_followup_next_matrix.py](../../../../../../tests/test_followup_next_matrix.py) — imports consumer [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]]
- [tests/test_probe_router.py](../../../../../../tests/test_probe_router.py) — imports consumer [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]]
- [tests/test_probe_router_authority.py](../../../../../../tests/test_probe_router_authority.py) — imports consumer [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]]
- [tests/test_probe_router_decision_integrity.py](../../../../../../tests/test_probe_router_decision_integrity.py) — imports consumer [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]]

## Modification guidance

- Make changes here when the responsibility remains contract job within learnloop.followup_run; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/followup_run/contract_job.py](../../../../../../src/learnloop/followup_run/contract_job.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
