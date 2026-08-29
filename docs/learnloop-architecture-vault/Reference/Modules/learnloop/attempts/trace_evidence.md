---
title: "learnloop.attempts.trace_evidence"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/trace_evidence.py"
source_paths:
  - "src/learnloop/attempts/trace_evidence.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempts.trace_evidence module"
  - "src/learnloop/attempts/trace_evidence.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.trace_evidence`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.trace_evidence` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: A6 opportunistic trace evidence — the elicitation boundary and the reports.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/trace_evidence.py](../../../../../../src/learnloop/attempts/trace_evidence.py) |
| Source lines | 327 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ElicitationDecision` ([source](../../../../../../src/learnloop/attempts/trace_evidence.py), line 70) — Whether to offer the one-line justification field on this item.
  - `as_dict(self) -> dict[str, Any]` (line 77; public)
- `compose_learner_trace(answer_md: str, explanation_md: str | None) -> str` ([source](../../../../../../src/learnloop/attempts/trace_evidence.py), line 106) — Join the answer and the volunteered line into the one trace the grader reads.
- `volunteered_explanation(trace_md: str | None) -> str | None` ([source](../../../../../../src/learnloop/attempts/trace_evidence.py), line 121) — The volunteered line inside a composed trace, or None — the exact inverse.
- `elicited_explanations_in(traces) -> int` ([source](../../../../../../src/learnloop/attempts/trace_evidence.py), line 140) — How many of ``traces`` carry a volunteered explanation.
- `decide_elicitation(item, *, config, elicitations_this_session: int) -> ElicitationDecision` ([source](../../../../../../src/learnloop/attempts/trace_evidence.py), line 159) — Whether to offer a one-line justification alongside ``item``.
- `elicitation_reward(exercised_facets, *, explanation_md: str | None=None, learner_answer_md: str | None=None) -> str | None` ([source](../../../../../../src/learnloop/attempts/trace_evidence.py), line 194) — The visible reward for a volunteered explanation, or None.
- `trace_evidence_report(repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/trace_evidence.py), line 252) — Concentration + volume of A6 observations, and unexercised supporting mass.

### Module constants

- `UNDERDETERMINED_CAPABILITIES` ([src/learnloop/attempts/trace_evidence.py](../../../../../../src/learnloop/attempts/trace_evidence.py), line 56)
- `_DECISION_POINT_PROMPT` ([src/learnloop/attempts/trace_evidence.py](../../../../../../src/learnloop/attempts/trace_evidence.py), line 84)
- `_APPLICABILITY_PROMPT` ([src/learnloop/attempts/trace_evidence.py](../../../../../../src/learnloop/attempts/trace_evidence.py), line 85)
- `ELICITATION_ANSWER_HEADING` ([src/learnloop/attempts/trace_evidence.py](../../../../../../src/learnloop/attempts/trace_evidence.py), line 103)

## Internal implementation anchors

- `_field(row: Any, key: str) -> Any` ([source](../../../../../../src/learnloop/attempts/trace_evidence.py), line 243)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `trace_evidence_report`; statically calls `trace_evidence_report`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `elicitation_reward`; statically calls `elicitation_reward`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `trace_evidence_report`; statically calls `trace_evidence_report`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `compose_learner_trace`, `decide_elicitation`, `elicited_explanations_in`; statically calls `compose_learner_trace`, `decide_elicitation`, `elicited_explanations_in`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/authoring/conjunctive_items|learnloop.content.authoring.conjunctive_items]] — imports `UNEXERCISED_SUPPORTING_TARGET`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]], [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]], [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_conjunctive_instruments.py](../../../../../../tests/test_conjunctive_instruments.py) — direct import
  - `test_a_no_reliable_decomposition_contract_does_not_suppress_elicitation`
  - `test_an_item_with_an_available_trace_contract_is_self_documenting`
  - `test_disabling_elicitation_wins_over_every_other_arm`
  - `test_elicitation_reward_counts_only_opportunistic_observations`
  - `test_elicitation_reward_reads_objects_as_well_as_rows`
  - `test_method_selection_without_a_contract_is_elicited_with_a_decision_prompt`
  - `test_procedure_execution_shows_its_work`
  - `test_schema_interpretation_gets_the_applicability_prompt`
  - `test_the_session_budget_is_hard`
  - `test_trace_evidence_report_surfaces_unexercised_cells_and_abstains_on_concentration`
- [tests/test_sidecar_trace_and_clarification.py](../../../../../../tests/test_sidecar_trace_and_clarification.py) — direct import

## Modification guidance

- Change trace evidence policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/trace_evidence.py](../../../../../../src/learnloop/attempts/trace_evidence.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
