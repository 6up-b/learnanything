---
title: "learnloop.diagnosis.split.settings"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/split/settings.py"
source_paths:
  - "src/learnloop/diagnosis/split/settings.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.split"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Configure AI Providers"
aliases:
  - "learnloop.diagnosis.split.settings module"
  - "src/learnloop/diagnosis/split/settings.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-split"
---

# `learnloop.diagnosis.split.settings`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.split.settings` exists within [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] to own the behavior summarized by its module contract: Diagnosis history modes and defaults (Slice 1 §5.2, §12).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/split/settings.py](../../../../../../../src/learnloop/diagnosis/split/settings.py) |
| Source lines | 71 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class DiagnosisSettings` ([source](../../../../../../../src/learnloop/diagnosis/split/settings.py), line 24) — §12 ``[diagnosis]`` defaults.
  - `__post_init__(self) -> None` (line 40; internal)
  - `with_mode(self, mode: HistoryMode) -> 'DiagnosisSettings'` (line 60; public)

### Module constants

- `HISTORY_MODES` ([src/learnloop/diagnosis/split/settings.py](../../../../../../../src/learnloop/diagnosis/split/settings.py), line 13)
- `DIAGNOSIS_PROMPT_VERSION` ([src/learnloop/diagnosis/split/settings.py](../../../../../../../src/learnloop/diagnosis/split/settings.py), line 16)
- `DIAGNOSIS_CONTEXT_VERSION` ([src/learnloop/diagnosis/split/settings.py](../../../../../../../src/learnloop/diagnosis/split/settings.py), line 18)
- `DIAGNOSIS_OUTPUT_SCHEMA_VERSION` ([src/learnloop/diagnosis/split/settings.py](../../../../../../../src/learnloop/diagnosis/split/settings.py), line 20)

### Explicit exports

`__all__` declares:

- `DIAGNOSIS_CONTEXT_VERSION`
- `DIAGNOSIS_OUTPUT_SCHEMA_VERSION`
- `DIAGNOSIS_PROMPT_VERSION`
- `HISTORY_MODES`
- `DiagnosisSettings`
- `HistoryMode`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/diagnose|learnloop.cli.diagnose]] — imports `DiagnosisSettings`; statically calls `DiagnosisSettings`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `DIAGNOSIS_PROMPT_VERSION`, `DiagnosisSettings`; statically calls `DiagnosisSettings`
- [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]] — imports `DIAGNOSIS_PROMPT_VERSION`
- [[Reference/Modules/learnloop/diagnosis/split/context|learnloop.diagnosis.split.context]] — imports `DIAGNOSIS_CONTEXT_VERSION`, `DiagnosisSettings`, `HistoryMode`
- [[Reference/Modules/learnloop/diagnosis/split/contract|learnloop.diagnosis.split.contract]] — imports `DIAGNOSIS_PROMPT_VERSION`
- [[Reference/Modules/learnloop/diagnosis/split/diagnoser|learnloop.diagnosis.split.diagnoser]] — imports `DIAGNOSIS_PROMPT_VERSION`, `DiagnosisSettings`, `HistoryMode`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `DIAGNOSIS_PROMPT_VERSION`
- [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]] — imports `DiagnosisSettings`; statically calls `DiagnosisSettings`
- [[Reference/Modules/learnloop/diagnosis/split/reports|learnloop.diagnosis.split.reports]] — imports `DIAGNOSIS_PROMPT_VERSION`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/diagnose|learnloop.cli.diagnose]], [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]], [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]], [[Reference/Modules/learnloop/diagnosis/split/context|learnloop.diagnosis.split.context]], [[Reference/Modules/learnloop/diagnosis/split/contract|learnloop.diagnosis.split.contract]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/learner_blindness_relax_helpers.py](../../../../../../../tests/learner_blindness_relax_helpers.py) — direct import
- [tests/recurrence_fakes.py](../../../../../../../tests/recurrence_fakes.py) — direct import
- [tests/test_chatgpt_plan_workspace.py](../../../../../../../tests/test_chatgpt_plan_workspace.py) — direct import
  - `test_a_snapshot_diagnosis_on_the_plan_records_exactly_what_it_read`
- [tests/test_diagnose_review.py](../../../../../../../tests/test_diagnose_review.py) — direct import
  - `test_a_resume_restores_the_persisted_experiment_and_refuses_changes`
- [tests/test_diagnosis_context.py](../../../../../../../tests/test_diagnosis_context.py) — direct import
  - `test_assembly_and_hash_are_deterministic`
  - `test_current_attempt_renders_last_with_its_blind_grade`
  - `test_exact_mode_selects_neighbourhood_failures_and_successes_as_of`
  - `test_legacy_joint_attempts_are_stripped_of_causal_fields`
  - `test_neighbourhood_and_as_of_prerequisite_status`
  - `test_repair_chain_source_is_visible_to_the_diagnoser`
  - `test_truncation_drops_oldest_first_and_discloses`
- [tests/test_diagnosis_contract.py](../../../../../../../tests/test_diagnosis_contract.py) — direct import
- [tests/test_diagnosis_history_modes.py](../../../../../../../tests/test_diagnosis_history_modes.py) — direct import
  - `test_every_mode_keeps_s3_and_validates_evidence_ids`
  - `test_full_budget_truncates_oldest_attempts_before_any_hypothesis`
  - `test_full_includes_every_neighbour_attempt_chronologically`
  - `test_full_stable_prefix_is_shared_by_consecutive_diagnoses_on_one_lo`
  - `test_hybrid_degrades_to_exact_when_embeddings_fail`
  - `test_hybrid_fuses_exact_and_knn_and_records_provenance`
  - `test_snapshot_is_unavailable_without_the_capability`
  - `test_snapshot_workspace_is_deleted_on_success_and_on_failure`
- [tests/test_followup_fg1c_codex_review.py](../../../../../../../tests/test_followup_fg1c_codex_review.py) — direct import
  - `test_f1_a_rediagnosis_records_the_cause_it_was_shown_through_a_mark`
- [tests/test_learner_blindness_relax.py](../../../../../../../tests/test_learner_blindness_relax.py) — direct import
  - `test_the_live_diagnosis_records_its_arm_and_the_grader_never_sees_it`
  - `test_the_off_arm_is_todays_context_and_the_on_arm_refeeds_earlier_analyses`
- [tests/test_pfc_unassessed_readers.py](../../../../../../../tests/test_pfc_unassessed_readers.py) — direct import
  - `test_a_later_diagnosis_cannot_cite_an_unassessed_shortfall_as_a_recurrence`
- [tests/test_ro1_projection.py](../../../../../../../tests/test_ro1_projection.py) — direct import
- [tests/test_workbench_trace.py](../../../../../../../tests/test_workbench_trace.py) — direct import
  - `test_a_workbench_attempt_carries_its_trace_under_the_suffix_and_never_a_map`
  - `test_every_other_attempt_renders_exactly_as_before`

## Modification guidance

- Change settings policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/split/settings.py](../../../../../../../src/learnloop/diagnosis/split/settings.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
