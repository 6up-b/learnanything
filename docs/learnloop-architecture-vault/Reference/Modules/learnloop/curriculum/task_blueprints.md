---
title: "learnloop.curriculum.task_blueprints"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/curriculum/task_blueprints.py"
source_paths:
  - "src/learnloop/curriculum/task_blueprints.py"
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
  - "learnloop.curriculum.task_blueprints module"
  - "src/learnloop/curriculum/task_blueprints.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-curriculum"
---

# `learnloop.curriculum.task_blueprints`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.curriculum.task_blueprints` exists within [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] to own the behavior summarized by its module contract: P2 step 1 -- reviewed, immutable TaskBlueprint versions (spec_p2_narrow_golden_path §3.1, §3.2, §12.1; migration 081).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/curriculum/task_blueprints.py](../../../../../../src/learnloop/curriculum/task_blueprints.py) |
| Source lines | 297 |
| Owning package | [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class InvalidBlueprint(Exception)` ([source](../../../../../../src/learnloop/curriculum/task_blueprints.py), line 33) — A blueprint spec violates the one-chapter/one-family invariant or references a capability outside the closed P1 vocabulary (§1.2 invariant 1, §12.1).
- `class ExemplarCandidate` ([source](../../../../../../src/learnloop/curriculum/task_blueprints.py), line 39) — A source object / inventory exercise proposed as a target exemplar (§3.1).
  - `as_dict(self) -> dict[str, Any]` (line 51; public)
- `class BlueprintVersion` ([source](../../../../../../src/learnloop/curriculum/task_blueprints.py), line 56) — A registered/reviewed/active immutable blueprint version.
  - `as_dict(self) -> dict[str, Any]` (line 69; public)
- `validate_single_unit(spec: Mapping[str, Any]) -> None` ([source](../../../../../../src/learnloop/curriculum/task_blueprints.py), line 77) — Reject a mixed-unit or multi-family blueprint before it can validate (§12.1).
- `discover_exemplar_candidates(candidates: Sequence[Mapping[str, Any]], *, unit_id: str, family_key: str) -> list[ExemplarCandidate]` ([source](../../../../../../src/learnloop/curriculum/task_blueprints.py), line 141) — Project reviewed inventory exercise rows into exemplar candidates within one unit (§3.1).
- `register_blueprint_version(repository: Repository, *, blueprint_slug: str, spec: Mapping[str, Any], authoring_version: str='stub-1', model_version: str | None=None, provenance_version: str='owner-review-1', author: str='owner', clock: Clock | None=None) -> BlueprintVersion` ([source](../../../../../../src/learnloop/curriculum/task_blueprints.py), line 170) — Register an immutable content-addressed draft blueprint version (§3.2).
- `review_blueprint_version(repository: Repository, *, blueprint_version_id: str, checks: Mapping[str, Any] | None=None, author: str='owner', clock: Clock | None=None) -> BlueprintVersion` ([source](../../../../../../src/learnloop/curriculum/task_blueprints.py), line 211) — Owner marks the version reviewed (§3.2 seven checks captured as the artifact).
- `activate_blueprint_version(repository: Repository, *, blueprint_version_id: str, author: str='owner', clock: Clock | None=None) -> BlueprintVersion` ([source](../../../../../../src/learnloop/curriculum/task_blueprints.py), line 232) — Activate a reviewed version.
- `place_reading_question(repository: Repository, *, blueprint_version_id: str, placement: Mapping[str, Any], author: str='owner', clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/curriculum/task_blueprints.py), line 259) — Record an owner-placed reading question at a section boundary as a blueprint review artifact (§7.6, U-033).

### Module constants

- `BLUEPRINT_SPEC_SCHEMA_VERSION` ([src/learnloop/curriculum/task_blueprints.py](../../../../../../src/learnloop/curriculum/task_blueprints.py), line 25)
- `CAPABILITY_VOCAB` ([src/learnloop/curriculum/task_blueprints.py](../../../../../../src/learnloop/curriculum/task_blueprints.py), line 28)

## Internal implementation anchors

- `_canonicalize_spec(spec: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/task_blueprints.py), line 114)
- `_exemplar_rows(spec: Mapping[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/curriculum/task_blueprints.py), line 120)
- `_load_version(repository: Repository, version_id: str, *, minted: bool=True) -> BlueprintVersion` ([source](../../../../../../src/learnloop/curriculum/task_blueprints.py), line 280)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/curriculum/golden_path_fixture|learnloop.curriculum.golden_path_fixture]] — imports `module`; statically calls `place_reading_question`, `register_blueprint_version`, `review_blueprint_version`
- [[Reference/Modules/learnloop_sidecar/handlers/golden_path|learnloop_sidecar.handlers.golden_path]] — imports `module`; statically calls `_load_version`, `register_blueprint_version`, `review_blueprint_version`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
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
  - `test_unreviewed_blueprint_refused`
- [tests/test_golden_path_run.py](../../../../../../tests/test_golden_path_run.py) — direct import
- [tests/test_reader_guidance.py](../../../../../../tests/test_reader_guidance.py) — direct import
- [tests/test_sidecar_golden_path_assessment.py](../../../../../../tests/test_sidecar_golden_path_assessment.py) — direct import
  - `test_practice_only_assess_open_returns_stable_error`
- [tests/test_task_blueprints.py](../../../../../../tests/test_task_blueprints.py) — direct import
  - `test_capability_outside_vocab_rejected`
  - `test_exemplar_anchor_has_zero_held_out_weight`
  - `test_mixed_unit_blueprint_cannot_validate`
  - `test_multi_family_blueprint_cannot_validate`
  - `test_reading_question_placement_is_a_review_artifact`
  - `test_register_is_content_addressed_idempotent`
  - `test_register_review_activate_triad`

## Modification guidance

- Change task blueprints policy here when curriculum owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/curriculum/task_blueprints.py](../../../../../../src/learnloop/curriculum/task_blueprints.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
