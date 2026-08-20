---
title: "learnloop.curriculum.golden_path_restoration"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/curriculum/golden_path_restoration.py"
source_paths:
  - "src/learnloop/curriculum/golden_path_restoration.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.curriculum"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Build a Study Map"
aliases:
  - "learnloop.curriculum.golden_path_restoration module"
  - "src/learnloop/curriculum/golden_path_restoration.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-curriculum"
---

# `learnloop.curriculum.golden_path_restoration`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.curriculum.golden_path_restoration` exists within [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] to own the behavior summarized by its module contract: P2 steps B.9 + B.10 -- post-attempt restoration + boundary diff, and the milestone + one-edge ``suggest_next`` depth invitation (spec_p2_narrow_golden_path §8.4, §7.5; §12.5, §12.3.1; migration 087 artifacts).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/curriculum/golden_path_restoration.py](../../../../../../src/learnloop/curriculum/golden_path_restoration.py) |
| Source lines | 443 |
| Owning package | [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class RestorationReceipt` ([source](../../../../../../src/learnloop/curriculum/golden_path_restoration.py), line 46)
  - `as_dict(self) -> dict[str, Any]` (line 58; public)
- `boundary_diff(repository: Repository, *, run_id: str, result: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/golden_path_restoration.py), line 105) — Diff the demonstrated boundary before/after the cold assessment (§8.4).
- `record_milestone_and_invite(repository: Repository, *, run_id: str, idempotency_key: str, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/curriculum/golden_path_restoration.py), line 166) — On a passed cold assessment, append the milestone fact and evaluate ONE reviewed edge as a ``suggest_next`` invitation (§7.5).
- `restore(repository: Repository, *, run_id: str, idempotency_key: str, clock: Clock | None=None) -> RestorationReceipt` ([source](../../../../../../src/learnloop/curriculum/golden_path_restoration.py), line 242) — Restore source context + boundary diff after the grade is committed (§8.4).
- `accept_depth_invitation(repository: Repository, *, run_id: str, idempotency_key: str, live_activation_enabled: bool | None=None, fork_edit: Mapping[str, Any] | None=None, goal_id: str | None=None, proposed_contract_body: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/golden_path_restoration.py), line 338) — Record the learner's EXPLICIT acceptance of the reviewed depth edge (§7.5).
- `decline_depth_invitation(repository: Repository, *, run_id: str, idempotency_key: str, reason: str | None=None, to_state: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/golden_path_restoration.py), line 412) — Log the learner's explicit decline of the depth invitation (§7.5).

### Module constants

- `RESTORATION_SCHEMA_VERSION` ([src/learnloop/curriculum/golden_path_restoration.py](../../../../../../src/learnloop/curriculum/golden_path_restoration.py), line 42)

## Internal implementation anchors

- `_reviewed_edges(repository: Repository, envelope_version_id: str | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/curriculum/golden_path_restoration.py), line 66)
- `_invited_edge_for_milestone(repository: Repository, run: Mapping[str, Any], milestone: str | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/curriculum/golden_path_restoration.py), line 75) — The one reviewed edge to invite at the ACHIEVED milestone (C6): the edge whose ``predecessor_milestone`` equals the achieved milestone.
- `_blueprint_spec(repository: Repository, run: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/golden_path_restoration.py), line 96)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/reader/reader_restoration|learnloop.reader.reader_restoration]] — imports `module`; statically calls `restore`
- [[Reference/Modules/learnloop_sidecar/handlers/golden_path_assessment|learnloop_sidecar.handlers.golden_path_assessment]] — imports `module`; statically calls `accept_depth_invitation`, `decline_depth_invitation`, `restore`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `record_milestone_reached`
- [[Reference/Modules/learnloop/curriculum/depth_transition|learnloop.curriculum.depth_transition]] — imports `module`; calls `commit_one_edge`
- [[Reference/Modules/learnloop/curriculum/golden_path_assessment|learnloop.curriculum.golden_path_assessment]] — imports `DEMONSTRATED_CLAIM_CERTAINTY`
- [[Reference/Modules/learnloop/curriculum/golden_path_run|learnloop.curriculum.golden_path_run]] — imports `module`; calls `advance`, `project_run`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_pack|learnloop.diagnosis.diagnostic_pack]] — imports `module`; calls `boundary_view`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_json`; calls `canonical_json`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/reader/reader_restoration|learnloop.reader.reader_restoration]], [[Reference/Modules/learnloop_sidecar/handlers/golden_path_assessment|learnloop_sidecar.handlers.golden_path_assessment]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_golden_path_assessment.py](../../../../../../tests/test_golden_path_assessment.py) — direct import
  - `test_accept_records_draft_intent_without_successor`
  - `test_boundary_diff_is_deterministic_and_reliability_aware`
  - `test_decline_logs_decision_and_holds_milestone`
  - `test_harness_activation_activates_exactly_one_edge`
  - `test_kill_resume_across_assessment_boundary`
  - `test_milestone_event_only_and_one_suggest_next_never_activates`
  - `test_restoration_after_measurement_cannot_change_the_observation`
- [tests/test_p2_acceptance.py](../../../../../../tests/test_p2_acceptance.py) — direct import
  - `test_golden_path_ten_step_fixture_journey`

## Modification guidance

- Change golden path restoration policy here when curriculum owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/curriculum/golden_path_restoration.py](../../../../../../src/learnloop/curriculum/golden_path_restoration.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
