---
title: "learnloop.curriculum.golden_path_confirm"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/curriculum/golden_path_confirm.py"
source_paths:
  - "src/learnloop/curriculum/golden_path_confirm.py"
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
  - "learnloop.curriculum.golden_path_confirm module"
  - "src/learnloop/curriculum/golden_path_confirm.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-curriculum"
---

# `learnloop.curriculum.golden_path_confirm`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.curriculum.golden_path_confirm` exists within [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] to own the behavior summarized by its module contract: P2 step 2 -- the ONE atomic exemplar confirmation (spec_p2_narrow_golden_path §3.1, §1.2 invariant 2, §12.1, §12.6; migration 082).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/curriculum/golden_path_confirm.py](../../../../../../src/learnloop/curriculum/golden_path_confirm.py) |
| Source lines | 368 |
| Owning package | [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class NotConfirmable(Exception)` ([source](../../../../../../src/learnloop/curriculum/golden_path_confirm.py), line 38) — The proposed contract body is not a confirmable v1 (missing exemplar, reviewed blueprint scope, or baseline milestone) -- spec_p2 §3.1 / §1.1 entry gate.
  - `__init__(self, reason: str)` (line 42; internal)
- `class ConfirmationMismatch(Exception)` ([source](../../../../../../src/learnloop/curriculum/golden_path_confirm.py), line 47) — A re-confirm of an already-confirmed goal differs only in a run-shaping param (e.g.
  - `__init__(self, goal_id: str, *, existing_run_id: str, detail: str)` (line 54; internal)
- `class RunReceipt` ([source](../../../../../../src/learnloop/curriculum/golden_path_confirm.py), line 65) — The result of one atomic confirmation (§3.1).
  - `as_dict(self) -> dict[str, Any]` (line 80; public)
- `confirm_exemplar_and_start(repository: Repository, *, goal_id: str, blueprint_version_id: str, contract_body: Mapping[str, Any], depth_preset: str, source_rev: str, unit_id: str, action: str='select_exemplar', assessment_surface_id: str | None=None, assessment_support_hash: str | None=None, assessment_eligibility: Mapping[str, Any] | None=None, intent_text: str | None=None, interpretation_text: str | None=None, orchestration_policy: Mapping[str, Any] | None=None, decision_param_manifest: Mapping[str, Any] | None=None, visible_caps: Mapping[str, Any] | None=None, author: str='learner', learner_id: str='local', fault_hook: Callable[[str], None] | None=None, clock: Clock | None=None) -> RunReceipt` ([source](../../../../../../src/learnloop/curriculum/golden_path_confirm.py), line 158) — Atomically confirm an exemplar interpretation and start a golden-path run.

## Internal implementation anchors

- `_confirmation_receipt_key(*, goal_id: str, blueprint_version_id: str, contract_content_hash: str, reserved_surface_id: str | None, depth_preset: str, action: str, source_rev: str, unit_id: str) -> str` ([source](../../../../../../src/learnloop/curriculum/golden_path_confirm.py), line 84) — Content identity of the whole confirmation.
- `_assert_reviewed_edges_match_blueprint(repository: Repository, blueprint_version_id: str, reviewed_edges: Sequence[Mapping[str, Any]]) -> None` ([source](../../../../../../src/learnloop/curriculum/golden_path_confirm.py), line 117) — C5: every reviewed edge the contract pins must be a REVIEWED depth_milestone the blueprint version declares (matched by ``edge_id`` and reviewed there).
- `_commitment_targets(contract_body: Mapping[str, Any]) -> list[C.CommitmentTarget]` ([source](../../../../../../src/learnloop/curriculum/golden_path_confirm.py), line 144)
- `_receipt_from_existing(repository: Repository, run_row: Mapping[str, Any], *, minted: bool) -> RunReceipt` ([source](../../../../../../src/learnloop/curriculum/golden_path_confirm.py), line 355)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/curriculum/golden_path_fixture|learnloop.curriculum.golden_path_fixture]] — imports `module`; statically calls `confirm_exemplar_and_start`
- [[Reference/Modules/learnloop_sidecar/handlers/golden_path|learnloop_sidecar.handlers.golden_path]] — imports `module`; statically calls `confirm_exemplar_and_start`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `_coerce_targets`, `_default_depth_body`, `_default_envelope_body`, `_target_row`, `_version_hash`, `target_set_hash`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/goals/goal_contracts|learnloop.goals.goal_contracts]] — imports `module`; calls `_envelope_version`, `canonicalize_body`, `content_hash`, `support_hash`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_hash`, `canonical_json`; calls `canonical_hash`, `canonical_json`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/curriculum/golden_path_fixture|learnloop.curriculum.golden_path_fixture]], [[Reference/Modules/learnloop_sidecar/handlers/golden_path|learnloop_sidecar.handlers.golden_path]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_p2_acceptance.py](../../../../../../tests/test_causal_p2_acceptance.py) — direct import
- [tests/test_controller_cutover.py](../../../../../../tests/test_controller_cutover.py) — direct import
- [tests/test_golden_path_assessment.py](../../../../../../tests/test_golden_path_assessment.py) — direct import
- [tests/test_golden_path_confirm.py](../../../../../../tests/test_golden_path_confirm.py) — direct import
  - `test_missing_baseline_not_confirmable`
  - `test_reconfirm_differing_only_in_depth_preset_raises_mismatch`
  - `test_reviewed_edge_absent_from_blueprint_is_refused`
- [tests/test_golden_path_run.py](../../../../../../tests/test_golden_path_run.py) — direct import
- [tests/test_sidecar_golden_path_assessment.py](../../../../../../tests/test_sidecar_golden_path_assessment.py) — direct import
  - `test_practice_only_assess_open_returns_stable_error`

## Modification guidance

- Change golden path confirm policy here when curriculum owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/curriculum/golden_path_confirm.py](../../../../../../src/learnloop/curriculum/golden_path_confirm.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
