---
title: "learnloop_sidecar.handlers.calibration"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/calibration.py"
source_paths:
  - "src/learnloop_sidecar/handlers/calibration.py"
generated: true
generated_at: "2026-11-02"
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
  - "learnloop_sidecar.handlers.calibration module"
  - "src/learnloop_sidecar/handlers/calibration.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.calibration`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.calibration` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Calibration sessions and dialogue microprobes (probe redesign §5.9 / §8.1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/calibration.py](../../../../../../src/learnloop_sidecar/handlers/calibration.py) |
| Source lines | 172 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class StartCalibrationInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/calibration.py), line 26)
- `class CalibrationSessionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/calibration.py), line 33)
- `start_calibration(ctx: SidecarContext, params: StartCalibrationInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/calibration.py), line 38) — Open a §5.9 calibration session over a goal scope or explicit LO list.
- `get_calibration(ctx: SidecarContext, params: CalibrationSessionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/calibration.py), line 77)
- `stop_calibration(ctx: SidecarContext, params: CalibrationSessionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/calibration.py), line 87)
- `class BeginDialogueInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/calibration.py), line 100)
- `class DialogueStateInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/calibration.py), line 104)
- `class DialogueTurnSubmittedInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/calibration.py), line 108)
- `begin_probe_dialogue(ctx: SidecarContext, params: BeginDialogueInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/calibration.py), line 114)
- `next_probe_dialogue_turn(ctx: SidecarContext, params: DialogueStateInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/calibration.py), line 124) — Mint and commit the next dialogue turn (ephemeral instance + presentation).
- `record_probe_dialogue_turn(ctx: SidecarContext, params: DialogueTurnSubmittedInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/calibration.py), line 150)
- `end_probe_dialogue(ctx: SidecarContext, params: DialogueStateInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/calibration.py), line 159) — §5.7 block boundary: runs the ordered block-end hook and returns the released feedback plus the route (typed transition / next block / ordinary practice) so the client can reveal and navigate.

## Internal implementation anchors

- `_progress(vault, repository, calibration_session_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/calibration.py), line 67) — Calibration progress; a quick check (learner field F2) adds its own target, answer count and, once it ends, its results.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/diagnosis/calibration_sessions|learnloop.diagnosis.calibration_sessions]] — imports `CalibrationSessionError`, `start_calibration_session`, `stop_calibration_session`; calls `start_calibration_session`, `stop_calibration_session`
- [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]] — imports `DialogueBlockError`, `DialogueBlockState`, `begin_dialogue_block`, `end_dialogue_block`, `next_dialogue_turn`, `record_turn_submitted`; calls `begin_dialogue_block`, `end_dialogue_block`, `next_dialogue_turn`, `record_turn_submitted`
- [[Reference/Modules/learnloop/diagnosis/quick_check|learnloop.diagnosis.quick_check]] — imports `quick_check_progress`; calls `quick_check_progress`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `ready_grading_provider`; calls `ready_grading_provider`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
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

- [tests/reading_path_fixtures.py](../../../../../../tests/reading_path_fixtures.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/recap_fixtures.py](../../../../../../tests/recap_fixtures.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/rw2b_fix10_base_sequence.py](../../../../../../tests/rw2b_fix10_base_sequence.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/rw2b_fix11_base_sequence.py](../../../../../../tests/rw2b_fix11_base_sequence.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/rw2c_base_sequence.py](../../../../../../tests/rw2c_base_sequence.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/rw2c_state_parity.py](../../../../../../tests/rw2c_state_parity.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_ad1_attempt_columns.py](../../../../../../tests/test_ad1_attempt_columns.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_ad23_fix_review.py](../../../../../../tests/test_ad23_fix_review.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_ad23_intent_compose.py](../../../../../../tests/test_ad23_intent_compose.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_ad23_successor.py](../../../../../../tests/test_ad23_successor.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_ad2_serving.py](../../../../../../tests/test_ad2_serving.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/calibration.py](../../../../../../src/learnloop_sidecar/handlers/calibration.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
