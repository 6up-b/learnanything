---
title: "learnloop.diagnosis.causal_reads"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/causal_reads.py"
source_paths:
  - "src/learnloop/diagnosis/causal_reads.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.causal_reads module"
  - "src/learnloop/diagnosis/causal_reads.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.causal_reads`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.causal_reads` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Factor and diagnosis-receipt reads and deterministic EVSI input summaries.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/causal_reads.py](../../../../../../src/learnloop/diagnosis/causal_reads.py) |
| Source lines | 377 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `open_factors_for_hypothesis(repository: Repository, causal_hypothesis_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/causal_reads.py), line 48) — Open cause factors on this hypothesis' own learning object (§3.9).
- `diagnosis_receipt(repository: Repository, attempt_id: str | None) -> Mapping[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/causal_reads.py), line 153)
- `class DiscriminationInputs` ([source](../../../../../../src/learnloop/diagnosis/causal_reads.py), line 296) — The two EVSI terms plus where each came from (standing constraint 4).
- `class CausalRepairError(ValueError)` ([source](../../../../../../src/learnloop/diagnosis/causal_reads.py), line 375) — The repair case itself is unusable (no such misconception / candidate).

### Module constants

- `CAUSAL_ORCHESTRATOR_FORMULA_VERSION` ([src/learnloop/diagnosis/causal_reads.py](../../../../../../src/learnloop/diagnosis/causal_reads.py), line 15)
- `MACHINE_CHECK_REPAIR_MAPPING` ([src/learnloop/diagnosis/causal_reads.py](../../../../../../src/learnloop/diagnosis/causal_reads.py), line 18)
- `MACHINE_CHECK_INSTRUMENT_COMMISSIONING` ([src/learnloop/diagnosis/causal_reads.py](../../../../../../src/learnloop/diagnosis/causal_reads.py), line 25)
- `PROBE_BLOCKING_MACHINE_CHECK_KINDS` ([src/learnloop/diagnosis/causal_reads.py](../../../../../../src/learnloop/diagnosis/causal_reads.py), line 37)
- `SWEPT_MACHINE_CHECK_KINDS` ([src/learnloop/diagnosis/causal_reads.py](../../../../../../src/learnloop/diagnosis/causal_reads.py), line 43)

## Internal implementation anchors

- `_durable_case_factor(repository: Repository, misconception: Any) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/causal_reads.py), line 71) — The open cause factor a durable misconception's case rides on, if any.
- `_case_repair_class_id(repository: Repository, hypothesis: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/causal_reads.py), line 104) — The repair class a factor-less diagnosis case would cold-verify (G14).
- `_unmapped_case_obligation(hypothesis: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_reads.py), line 125) — The typed mapping obligation for a factor-less unmapped diagnosis case.
- `_receipt_repair_class_id(receipt: Mapping[str, Any] | None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/causal_reads.py), line 166) — The repair class one diagnosis receipt commits to, if any.
- `_repair_class_by_hypothesis(causes: Sequence[Mapping[str, Any]]) -> dict[str, str]` ([source](../../../../../../src/learnloop/diagnosis/causal_reads.py), line 192)
- `_avoided_overteaching_minutes(repository: Repository, *, attempt_id: str | None, repair_class_ids: Sequence[str], default_minutes: float) -> tuple[float, str]` ([source](../../../../../../src/learnloop/diagnosis/causal_reads.py), line 206) — Expected teaching minutes a discriminating answer would save, + provenance.
- `_probe_burden_minutes(repository: Repository, practice_item_id: str | None, default_minutes: float) -> tuple[float, str]` ([source](../../../../../../src/learnloop/diagnosis/causal_reads.py), line 259) — Probe burden from the instrument card's own expected seconds, + provenance.
- `_recent_diagnostic_burden(repository: Repository, learning_object_id: str, window: int) -> int` ([source](../../../../../../src/learnloop/diagnosis/causal_reads.py), line 282)
- `_discrimination_inputs(candidate: Mapping[str, Any] | None, repair_class_by_hypothesis: Mapping[str, str]) -> DiscriminationInputs` ([source](../../../../../../src/learnloop/diagnosis/causal_reads.py), line 307) — ``(expected_information_gain, p(information changes the repair))``.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `MACHINE_CHECK_INSTRUMENT_COMMISSIONING`
- [[Reference/Modules/learnloop/diagnosis/causal_cold_verification|learnloop.diagnosis.causal_cold_verification]] — imports `CAUSAL_ORCHESTRATOR_FORMULA_VERSION`, `_case_repair_class_id`, `_receipt_repair_class_id`, `diagnosis_receipt`, `open_factors_for_hypothesis`; statically calls `_case_repair_class_id`, `_receipt_repair_class_id`, `diagnosis_receipt`, `open_factors_for_hypothesis`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `CAUSAL_ORCHESTRATOR_FORMULA_VERSION`, `CausalRepairError`, `_avoided_overteaching_minutes`, `_case_repair_class_id`, `_discrimination_inputs`, `_durable_case_factor`, `_probe_burden_minutes`, `_recent_diagnostic_burden`, `_repair_class_by_hypothesis`, `_unmapped_case_obligation`, `diagnosis_receipt`, `open_factors_for_hypothesis`; statically calls `CausalRepairError`, `_avoided_overteaching_minutes`, `_case_repair_class_id`, `_discrimination_inputs`, `_durable_case_factor`, `_probe_burden_minutes`, `_recent_diagnostic_burden`, `_repair_class_by_hypothesis`, `_unmapped_case_obligation`, `diagnosis_receipt`, `open_factors_for_hypothesis`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `CausalRepairError`
- [[Reference/Modules/learnloop/diagnosis/machine_checks|learnloop.diagnosis.machine_checks]] — imports `CAUSAL_ORCHESTRATOR_FORMULA_VERSION`, `MACHINE_CHECK_INSTRUMENT_COMMISSIONING`, `MACHINE_CHECK_REPAIR_MAPPING`, `PROBE_BLOCKING_MACHINE_CHECK_KINDS`, `SWEPT_MACHINE_CHECK_KINDS`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `CausalRepairError`
- [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]] — imports `CausalRepairError`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `_normalized`; calls `_normalized`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/diagnosis/causal_cold_verification|learnloop.diagnosis.causal_cold_verification]], [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]], [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]], [[Reference/Modules/learnloop/diagnosis/machine_checks|learnloop.diagnosis.machine_checks]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_orchestrator.py](../../../../../../tests/test_causal_orchestrator.py) — direct import
  - `test_unmapped_hypothesis_defers_the_repair_behind_a_machine_check`
- [tests/test_causal_probe_commissioning.py](../../../../../../tests/test_causal_probe_commissioning.py) — direct import
  - `test_sweep_machine_checks_queues_the_instrument_debt`
- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f9_verify_a_check_on_another_object_or_of_a_non_blocking_kind_refuses_nothing`

## Modification guidance

- Change causal reads policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/causal_reads.py](../../../../../../src/learnloop/diagnosis/causal_reads.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
