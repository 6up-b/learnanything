---
title: "learnloop_sidecar.handlers.adjudication"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/adjudication.py"
source_paths:
  - "src/learnloop_sidecar/handlers/adjudication.py"
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
  - "learnloop_sidecar.handlers.adjudication module"
  - "src/learnloop_sidecar/handlers/adjudication.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.adjudication`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.adjudication` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Diagnosis adjudication over the sidecar (spec_diagnostic_augmentation_v1 §2 A4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/adjudication.py](../../../../../../src/learnloop_sidecar/handlers/adjudication.py) |
| Source lines | 501 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class AdjudicationQueueInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/adjudication.py), line 76)
- `class AdjudicatedAnchorInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/adjudication.py), line 82)
- `class AdjudicationRecordInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/adjudication.py), line 91)
- `class AdjudicationScoreboardInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/adjudication.py), line 102)
- `adjudication_queue_handler(ctx: SidecarContext, params: AdjudicationQueueInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/adjudication.py), line 220) — Attempts owed a diagnosis verdict, highest information first (A4).
- `adjudication_record_handler(ctx: SidecarContext, params: AdjudicationRecordInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/adjudication.py), line 312) — Record one considered verdict on one diagnosis, append-only (A4).
- `adjudication_scoreboard_handler(ctx: SidecarContext, params: AdjudicationScoreboardInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/adjudication.py), line 474) — The §3 B5 metrics over the active verdicts.

### Module constants

- `_DECLINED_WORDING` ([src/learnloop_sidecar/handlers/adjudication.py](../../../../../../src/learnloop_sidecar/handlers/adjudication.py), line 45)

## Internal implementation anchors

- `_declined_wording(reason: str) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/adjudication.py), line 57)
- `_learner_facing(vault, repository, attempt_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/adjudication.py), line 111) — What the learner was actually shown about this diagnosis, or ``None``.
- `_repair_class_options(repository, attempt_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/adjudication.py), line 129) — The repair classes this episode offered, with enough to name them.
- `_case(vault, repository, entry) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/adjudication.py), line 158)
- `_outcome(repository, effect) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/adjudication.py), line 264) — The one honest line the overlay may show after a verdict.
- `_counted(values: Mapping[str, Any], key: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/adjudication.py), line 456)
- `_group(group: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/adjudication.py), line 460)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `causal_episode_for_attempt`, `claim_checked_feedback`; calls `causal_episode_for_attempt`, `claim_checked_feedback`
- [[Reference/Modules/learnloop/diagnosis/diagnosis_adjudication|learnloop.diagnosis.diagnosis_adjudication]] — imports `ABSTENTION_VERDICTS`, `ADJUDICATOR_SOURCES`, `ANCHOR_KINDS`, `FILLED_VERDICTS`, `QUEUE_REASONS`, `VERDICTS`, `adjudication_queue`, `append_diagnosis_adjudication`, `diagnosis_adjudication_scoreboard`, `diagnosis_snapshot`; calls `adjudication_queue`, `append_diagnosis_adjudication`, `diagnosis_adjudication_scoreboard`, `diagnosis_snapshot`
- [[Reference/Modules/learnloop/learner/surfaced_beliefs|learnloop.learner.surfaced_beliefs]] — imports `surfaced_belief_corrections`; calls `surfaced_belief_corrections`
- [[Reference/Modules/learnloop/tutor/durable_promotion|learnloop.tutor.durable_promotion]] — imports `apply_adjudicated_belief_effects`; calls `apply_adjudicated_belief_effects`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
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

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_desktop_rpc_contract.py](../../../../../../tests/test_desktop_rpc_contract.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_dialogue_causal_join.py](../../../../../../tests/test_dialogue_causal_join.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_goal_scope_material.py](../../../../../../tests/test_goal_scope_material.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_graph_editor_reads.py](../../../../../../tests/test_graph_editor_reads.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_adjudication.py](../../../../../../tests/test_sidecar_adjudication.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_exams.py](../../../../../../tests/test_sidecar_exams.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_goals.py](../../../../../../tests/test_sidecar_goals.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_item_presentation.py](../../../../../../tests/test_sidecar_item_presentation.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_measurement.py](../../../../../../tests/test_sidecar_measurement.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_trace_and_clarification.py](../../../../../../tests/test_sidecar_trace_and_clarification.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/adjudication.py](../../../../../../src/learnloop_sidecar/handlers/adjudication.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
