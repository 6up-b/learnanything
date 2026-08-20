---
title: "learnloop.diagnosis.causal_selection_audit"
type: "module-reference"
status: "current"
refactor_status: "EVALUATION"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/causal_selection_audit.py"
source_paths:
  - "src/learnloop/diagnosis/causal_selection_audit.py"
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
  - "learnloop.diagnosis.causal_selection_audit module"
  - "src/learnloop/diagnosis/causal_selection_audit.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/evaluation"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.causal_selection_audit`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.causal_selection_audit` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: EVSI-2 — the causal-selection readiness report (decision-value spec WP0/§8 Stage 0).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/causal_selection_audit.py](../../../../../../src/learnloop/diagnosis/causal_selection_audit.py) |
| Source lines | 228 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `EVALUATION` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

> [!note] Evaluation-only authority
> This module computes shadow, audit, or offline evidence. Its outputs do not directly choose learner-facing actions unless a governed promotion path says otherwise.

## Public API

- `causal_selection_readiness(vault: LoadedVault | None, repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_selection_audit.py), line 60) — The WP0 readiness report over one vault.

### Module constants

- `READINESS_REPORT_VERSION` ([src/learnloop/diagnosis/causal_selection_audit.py](../../../../../../src/learnloop/diagnosis/causal_selection_audit.py), line 32)
- `EXPECTATIONS_NOTE` ([src/learnloop/diagnosis/causal_selection_audit.py](../../../../../../src/learnloop/diagnosis/causal_selection_audit.py), line 36)

## Internal implementation anchors

- `_unavailable(reason: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/causal_selection_audit.py), line 45)
- `_concrete_hypothesis_ids(factor: dict[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/causal_selection_audit.py), line 49)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `causal_selection_readiness`; statically calls `causal_selection_readiness`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `causal_selection_readiness`; statically calls `causal_selection_readiness`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_diagnostic_selector|learnloop.diagnosis.causal_diagnostic_selector]] — imports `duration_estimates_for_repair_classes`, `likelihood_regime_for_candidate`; calls `duration_estimates_for_repair_classes`, `likelihood_regime_for_candidate`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `candidate_has_current_blind_input_contract`, `order_probe_candidates`; calls `candidate_has_current_blind_input_contract`, `order_probe_candidates`
- [[Reference/Modules/learnloop/diagnosis/probe_hypotheses|learnloop.diagnosis.probe_hypotheses]] — imports `H_OTHER`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_shadow_selection.py](../../../../../../tests/test_causal_shadow_selection.py) — direct import
  - `test_commissioned_v2_bundles_reach_arm_b_and_the_prior_refusal_passes_through`
  - `test_readiness_report_counts_multiplicity_and_regimes`
  - `test_readiness_report_types_every_empty_denominator`

## Modification guidance

- Change causal selection audit policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Keep this module's shadow/offline outputs decision-inert. Promotion into live policy requires the governed evidence and cutover path documented by its source contract.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/causal_selection_audit.py](../../../../../../src/learnloop/diagnosis/causal_selection_audit.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
