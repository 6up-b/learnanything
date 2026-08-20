---
title: "learnloop.learner.recall_calibration"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/recall_calibration.py"
source_paths:
  - "src/learnloop/learner/recall_calibration.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.learner"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Inspect Persistent State"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.learner.recall_calibration module"
  - "src/learnloop/learner/recall_calibration.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.recall_calibration`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps recall calibration behavior inside its owning package, [[Reference/Modules/learnloop/learner/_package|learnloop.learner]]. Its public surface centers on `RecallCalibrationRow`, `run_recall_calibration_harness`, `format_recall_calibration_table`, `assert_recall_calibration_bands`.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/recall_calibration.py](../../../../../../src/learnloop/learner/recall_calibration.py) |
| Source lines | 345 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class RecallCalibrationRow` ([source](../../../../../../src/learnloop/learner/recall_calibration.py), line 29)
  - `as_dict(self) -> dict[str, object]` (line 50; public)
- `run_recall_calibration_harness(work_root: Path | None=None) -> list[RecallCalibrationRow]` ([source](../../../../../../src/learnloop/learner/recall_calibration.py), line 74)
- `format_recall_calibration_table(rows: list[RecallCalibrationRow]) -> str` ([source](../../../../../../src/learnloop/learner/recall_calibration.py), line 83)
- `assert_recall_calibration_bands(rows: list[RecallCalibrationRow]) -> None` ([source](../../../../../../src/learnloop/learner/recall_calibration.py), line 117)

### Module constants

- `CALIBRATION_NOW` ([src/learnloop/learner/recall_calibration.py](../../../../../../src/learnloop/learner/recall_calibration.py), line 21)
- `CALIBRATION_NOW_ISO` ([src/learnloop/learner/recall_calibration.py](../../../../../../src/learnloop/learner/recall_calibration.py), line 22)
- `SEVERITY_EXAMPLES` ([src/learnloop/learner/recall_calibration.py](../../../../../../src/learnloop/learner/recall_calibration.py), line 25)

## Internal implementation anchors

- `_run_scenario(root: Path, scenario: str) -> RecallCalibrationRow` ([source](../../../../../../src/learnloop/learner/recall_calibration.py), line 131)
- `_fresh_calibration_vault(root: Path)` ([source](../../../../../../src/learnloop/learner/recall_calibration.py), line 205)
- `_attempt(repository: Repository, vault, *, points: float, practice_item_id: str='pi_calibration_main', attempt_type: str='independent_attempt', error_type: str | None=None, hints_used: int=0, days: int=0)` ([source](../../../../../../src/learnloop/learner/recall_calibration.py), line 288)
- `_intervention_decision(vault, repository: Repository, result, event: dict, debug: dict) -> FollowupDecision` ([source](../../../../../../src/learnloop/learner/recall_calibration.py), line 314)
- `_intervention_status(decision: FollowupDecision) -> str` ([source](../../../../../../src/learnloop/learner/recall_calibration.py), line 338)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `assert_recall_calibration_bands`, `format_recall_calibration_table`, `run_recall_calibration_harness`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `AttemptDraft`, `SelfGradeInput`, `complete_self_graded_attempt`; calls `AttemptDraft`, `SelfGradeInput`, `complete_self_graded_attempt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `FrozenClock`; calls `FrozenClock`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `SeverityExampleConfig`, `default_severity_examples`; calls `default_severity_examples`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `MasteryState`, `Repository`; calls `MasteryState`, `Repository`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `FollowupDecision`, `evaluate_intervention_followup`; calls `evaluate_intervention_followup`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `facet_recall_state_for_lo`; calls `facet_recall_state_for_lo`
- [[Reference/Modules/learnloop/ops/vault_upgrade|learnloop.ops.vault_upgrade]] — imports `KM_ALGORITHM_VERSION`, `LEGACY_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `sync_vault_state`; calls `sync_vault_state`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `add_subject`, `init_vault`, `load_vault`; calls `add_subject`, `init_vault`, `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `upsert_concept`, `upsert_learning_object`, `upsert_practice_item`; calls `upsert_concept`, `upsert_learning_object`, `upsert_practice_item`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `pathlib`, `re`, `tempfile`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_recall_calibration.py](../../../../../../tests/test_recall_calibration.py) — direct import
  - `test_recall_calibration_cli_json_and_assert_mode`
  - `test_recall_calibration_examples_are_config_backed`
  - `test_recall_calibration_harness_is_deterministic_and_in_band`

## Modification guidance

- Change recall calibration policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/recall_calibration.py](../../../../../../src/learnloop/learner/recall_calibration.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
