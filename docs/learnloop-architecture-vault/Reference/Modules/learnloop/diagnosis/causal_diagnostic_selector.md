---
title: "learnloop.diagnosis.causal_diagnostic_selector"
type: "module-reference"
status: "current"
refactor_status: "EVALUATION"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/causal_diagnostic_selector.py"
source_paths:
  - "src/learnloop/diagnosis/causal_diagnostic_selector.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
aliases:
  - "learnloop.diagnosis.causal_diagnostic_selector module"
  - "src/learnloop/diagnosis/causal_diagnostic_selector.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/evaluation"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.causal_diagnostic_selector`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.causal_diagnostic_selector` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: EVSI-2 — the causal factor → formal-selector adapter, shadow-only.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/causal_diagnostic_selector.py](../../../../../../src/learnloop/diagnosis/causal_diagnostic_selector.py) |
| Source lines | 593 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `EVALUATION` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

> [!note] Evaluation-only authority
> This module computes shadow, audit, or offline evidence. Its outputs do not directly choose learner-facing actions unless a governed promotion path says otherwise.

## Public API

- `duration_estimates_for_repair_classes(repository: Repository, repair_class_ids: Sequence[str]) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/causal_diagnostic_selector.py), line 83) — Minutes per repair class with an honest source label.
- `build_causal_loss_table(repository: Repository, *, repair_class_by_hypothesis: Mapping[str, str | None], duration_overrides: Mapping[str, float] | None=None) -> tuple[AL.LossTable | None, dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/causal_diagnostic_selector.py), line 130) — L(hypothesis, repair_class) for the factor's concrete hypotheses.
- `likelihood_regime_for_candidate(repository: Repository, candidate: Mapping[str, Any] | None, *, concrete_hypothesis_ids: Sequence[str]) -> tuple[str, dict[str, Any], dict[str, dict[str, float]] | None]` ([source](../../../../../../src/learnloop/diagnosis/causal_diagnostic_selector.py), line 195) — Classify the §6.2 arm and, for arm B, build the noiseless member.
- `record_shadow_selection(repository: Repository, *, decision_receipt: Mapping[str, Any], candidates: Sequence[Mapping[str, Any]]=(), chosen_candidate: Mapping[str, Any] | None=None, repair_class_by_hypothesis: Mapping[str, str | None] | None=None, common_repair_class_id: str | None=None, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/causal_diagnostic_selector.py), line 300) — Compute + persist the §6.6 baselines for one live probe decision.

### Module constants

- `SHADOW_POLICY_VERSION` ([src/learnloop/diagnosis/causal_diagnostic_selector.py](../../../../../../src/learnloop/diagnosis/causal_diagnostic_selector.py), line 51)
- `LIKELIHOOD_REGIMES` ([src/learnloop/diagnosis/causal_diagnostic_selector.py](../../../../../../src/learnloop/diagnosis/causal_diagnostic_selector.py), line 54)
- `LOSS_TABLE_REGIME_SHADOW_V1` ([src/learnloop/diagnosis/causal_diagnostic_selector.py](../../../../../../src/learnloop/diagnosis/causal_diagnostic_selector.py), line 63)

## Internal implementation anchors

- `_stable_emission_key(values: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/diagnosis/causal_diagnostic_selector.py), line 66)
- `_unavailable(reason: str, detail: Sequence[str]=()) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_diagnostic_selector.py), line 71)
- `_conditional_concrete_prior(prior: Mapping[str, Any]) -> tuple[dict[str, float], dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/causal_diagnostic_selector.py), line 279) — Strip the open-set arm EXPLICITLY, recording the excluded mass.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `module`; statically calls `record_shadow_selection`
- [[Reference/Modules/learnloop/diagnosis/causal_selection_audit|learnloop.diagnosis.causal_selection_audit]] — imports `duration_estimates_for_repair_classes`, `likelihood_regime_for_candidate`; statically calls `duration_estimates_for_repair_classes`, `likelihood_regime_for_candidate`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `BLIND_INPUT_CONTRACT_VERSION`, `bundle_feature_row_report`; calls `bundle_feature_row_report`
- [[Reference/Modules/learnloop/diagnosis/probe_hypotheses|learnloop.diagnosis.probe_hypotheses]] — imports `H_OTHER`
- [[Reference/Modules/learnloop/scheduling/action_loss|learnloop.scheduling.action_loss]] — imports `module`; calls `build_loss_table`
- [[Reference/Modules/learnloop/scheduling/evsi|learnloop.scheduling.evsi]] — imports `module`; calls `DiagnosticCandidate`, `EVSIInputError`, `evsi_for_conditionals`, `rank_feasible`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]], [[Reference/Modules/learnloop/diagnosis/causal_selection_audit|learnloop.diagnosis.causal_selection_audit]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_shadow_selection.py](../../../../../../tests/test_causal_shadow_selection.py) — direct import
  - `test_duration_estimates_carry_honest_provenance`
  - `test_evpi_skip_bound_licenses_stop_under_a_skewed_supported_prior`
  - `test_no_action_mapping_is_a_typed_abstention_not_a_fabricated_route`
  - `test_stripping_the_h_other_disposition_demotes_arm_b`

## Modification guidance

- Change causal diagnostic selector policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Keep this module's shadow/offline outputs decision-inert. Promotion into live policy requires the governed evidence and cutover path documented by its source contract.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/causal_diagnostic_selector.py](../../../../../../src/learnloop/diagnosis/causal_diagnostic_selector.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
