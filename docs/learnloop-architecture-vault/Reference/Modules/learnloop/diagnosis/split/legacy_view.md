---
title: "learnloop.diagnosis.split.legacy_view"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/split/legacy_view.py"
source_paths:
  - "src/learnloop/diagnosis/split/legacy_view.py"
source_commit: "b71017782b0ebb640e116763383205f72a1826b6"
source_commit_timestamp: "2026-10-12T04:42:11-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.split"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.split.legacy_view module"
  - "src/learnloop/diagnosis/split/legacy_view.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-split"
---

# `learnloop.diagnosis.split.legacy_view`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.split.legacy_view` exists within [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] to own the behavior summarized by its module contract: The stored joint diagnosis, read in the ``DiagnosisProposal`` shape (§6.3).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/split/legacy_view.py](../../../../../../../src/learnloop/diagnosis/split/legacy_view.py) |
| Source lines | 214 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `b71017782b0ebb640e116763383205f72a1826b6` |
| Commit timestamp | `2026-10-12T04:42:11-04:00` |

## Public API

- `legacy_view_from_parts(*, analysis_md: str | None, error_events: Sequence[Mapping[str, Any]], repair_suggestions: Iterable[Mapping[str, Any]], history_attempt_ids: Sequence[str]=(), source: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/legacy_view.py), line 87)
- `legacy_view_from_grading_proposal(proposal: GradingProposal, *, misconception_ids: Sequence[str | None]=(), history_attempt_ids: Sequence[str]=()) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/legacy_view.py), line 124) — The joint grader's fresh output, in the same reverse mapping.
- `stored_legacy_view(repository: Repository, attempt_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/split/legacy_view.py), line 183) — Arm (a): the joint diagnosis exactly as stored, or ``None`` if none exists.

### Module constants

- `LEGACY_VIEW_MODE` ([src/learnloop/diagnosis/split/legacy_view.py](../../../../../../../src/learnloop/diagnosis/split/legacy_view.py), line 19)
- `REVIEW_RECEIPT_OWNER_KIND` ([src/learnloop/diagnosis/split/legacy_view.py](../../../../../../../src/learnloop/diagnosis/split/legacy_view.py), line 21)
- `_CAUSAL_CLASSES` ([src/learnloop/diagnosis/split/legacy_view.py](../../../../../../../src/learnloop/diagnosis/split/legacy_view.py), line 22)
- `_INSTRUCTIONAL_FIELDS` ([src/learnloop/diagnosis/split/legacy_view.py](../../../../../../../src/learnloop/diagnosis/split/legacy_view.py), line 23)

### Explicit exports

`__all__` declares:

- `LEGACY_VIEW_MODE`
- `REVIEW_RECEIPT_OWNER_KIND`
- `legacy_view_from_grading_proposal`
- `legacy_view_from_parts`
- `stored_legacy_view`

## Internal implementation anchors

- `_decode(value: Any, default: Any) -> Any` ([source](../../../../../../../src/learnloop/diagnosis/split/legacy_view.py), line 40)
- `_event_diagnosis(index: int, event: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/legacy_view.py), line 51)
- `_repair(suggestion: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/legacy_view.py), line 77)
- `_stored_joint_analysis(repository: Repository, attempt_id: str) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/split/legacy_view.py), line 158) — The joint call's ``diagnosis_md`` from its model receipt, when kept.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `REVIEW_RECEIPT_OWNER_KIND`, `legacy_view_from_grading_proposal`, `stored_legacy_view`; statically calls `legacy_view_from_grading_proposal`, `stored_legacy_view`
- [[Reference/Modules/learnloop/diagnosis/offline_review/spot_check|learnloop.diagnosis.offline_review.spot_check]] — imports `stored_legacy_view`; statically calls `stored_legacy_view`
- [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]] — imports `LEGACY_VIEW_MODE`, `stored_legacy_view`; statically calls `stored_legacy_view`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/ai_contracts|learnloop.attempts.ai_contracts]] — imports `GradingProposal`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]], [[Reference/Modules/learnloop/diagnosis/offline_review/spot_check|learnloop.diagnosis.offline_review.spot_check]], [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_coordinated_migrations.py](../../../../../../../tests/test_coordinated_migrations.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]]
- [tests/test_diagnose_review.py](../../../../../../../tests/test_diagnose_review.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]]
- [tests/test_diagnosis_isolation.py](../../../../../../../tests/test_diagnosis_isolation.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]]
- [tests/test_teacher_te0_fix_round2.py](../../../../../../../tests/test_teacher_te0_fix_round2.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]]
- [tests/test_teacher_te0_review_fixes.py](../../../../../../../tests/test_teacher_te0_review_fixes.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]]
- [tests/test_tier1_decider.py](../../../../../../../tests/test_tier1_decider.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]]
- [tests/test_ai_compare.py](../../../../../../../tests/test_ai_compare.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]]
- [tests/test_diagnosis_input_provenance.py](../../../../../../../tests/test_diagnosis_input_provenance.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]]
- [tests/test_diagnosis_pipeline.py](../../../../../../../tests/test_diagnosis_pipeline.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]]
- [tests/test_diagnosis_replay.py](../../../../../../../tests/test_diagnosis_replay.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]]
- [tests/test_followup_fg1c_codex_review.py](../../../../../../../tests/test_followup_fg1c_codex_review.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]]
- [tests/test_hypothesis_marks_context.py](../../../../../../../tests/test_hypothesis_marks_context.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]]

## Modification guidance

- Change legacy view policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/split/legacy_view.py](../../../../../../../src/learnloop/diagnosis/split/legacy_view.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
