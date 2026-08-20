---
title: "learnloop.diagnosis.guided_redo"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/guided_redo.py"
source_paths:
  - "src/learnloop/diagnosis/guided_redo.py"
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
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.guided_redo module"
  - "src/learnloop/diagnosis/guided_redo.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.guided_redo`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.guided_redo` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Guided partial redo of a failed attempt (owner Fix 3).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/guided_redo.py](../../../../../../src/learnloop/diagnosis/guided_redo.py) |
| Source lines | 353 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class GuidedRedoUnavailable(ValueError)` ([source](../../../../../../src/learnloop/diagnosis/guided_redo.py), line 44) — No guided redo can be offered for this attempt, with a stable reason.
  - `__init__(self, reason: str, message: str) -> None` (line 47; internal)
- `diagnosis_receipt(repository: Repository, attempt_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/guided_redo.py), line 52)
- `selected_repair(receipt: dict[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/guided_redo.py), line 61) — ``repair_selection.selected`` — {repair_class, suggestion, minimality}.
- `guided_redo_available(repository: Repository, attempt_id: str) -> bool` ([source](../../../../../../src/learnloop/diagnosis/guided_redo.py), line 83) — Whether :func:`start_guided_redo` would serve this attempt.
- `item_step_checkpoint_ids(repair_class: dict[str, Any] | None) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/guided_redo.py), line 99)
- `start_guided_redo(vault: LoadedVault, repository: Repository, attempt_id: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/guided_redo.py), line 272) — The redo context for one failed attempt, binding an episode when possible.

## Internal implementation anchors

- `_preserved_prefix(selected: dict[str, Any] | None) -> str` ([source](../../../../../../src/learnloop/diagnosis/guided_redo.py), line 73) — The SELECTED repair's ``learner_work_prefix``, or ``""``.
- `_case_candidates(repository: Repository, attempt_id: str) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/diagnosis/guided_redo.py), line 107) — (case_kind, case_ref) pairs this attempt's diagnosis could bind to.
- `_bind_episode_to_redo(vault: LoadedVault, repository: Repository, *, attempt: dict[str, Any], item: Any, target_checkpoint_ids: tuple[str, ...], clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/guided_redo.py), line 128) — Commit an open, unbound episode to the redo item as its primed surface.
- `_establish_episode(vault: LoadedVault, repository: Repository, *, attempt: dict[str, Any], clock: Clock | None) -> bool` ([source](../../../../../../src/learnloop/diagnosis/guided_redo.py), line 209) — Mint an open episode for the attempt's diagnosed case, where permitted.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]] — imports `guided_redo_available`; statically calls `guided_redo_available`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `diagnosis_receipt`, `selected_repair`; statically calls `diagnosis_receipt`, `selected_repair`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `GuidedRedoUnavailable`, `diagnosis_receipt`, `item_step_checkpoint_ids`, `selected_repair`, `start_guided_redo`; statically calls `diagnosis_receipt`, `item_step_checkpoint_ids`, `selected_repair`, `start_guided_redo`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `guided_redo_available`; statically calls `guided_redo_available`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `RemediationError`, `_rank_items`, `episode_case`, `start_remediation_episode`; calls `_rank_items`, `episode_case`, `start_remediation_episode`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]], [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]], [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]], [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_guided_redo.py](../../../../../../tests/test_guided_redo.py) — direct import
  - `test_feedback_reports_guided_redo_availability`
  - `test_guided_redo_binds_open_episode_and_closes_the_funnel`
  - `test_guided_redo_establishes_diagnosis_episode_from_hypothesis`
  - `test_guided_redo_establishes_episode_without_overlay`
  - `test_guided_redo_never_steals_a_sibling_committed_episode`
  - `test_guided_redo_reports_case_unresolvable`
  - `test_guided_redo_requires_a_repair_selection`
  - `test_guided_redo_serves_prefix_and_instruction`

## Modification guidance

- Change guided redo policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/guided_redo.py](../../../../../../src/learnloop/diagnosis/guided_redo.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
