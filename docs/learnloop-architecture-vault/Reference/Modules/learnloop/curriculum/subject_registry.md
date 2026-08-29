---
title: "learnloop.curriculum.subject_registry"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/curriculum/subject_registry.py"
source_paths:
  - "src/learnloop/curriculum/subject_registry.py"
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
  - "learnloop.curriculum.subject_registry module"
  - "src/learnloop/curriculum/subject_registry.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-curriculum"
---

# `learnloop.curriculum.subject_registry`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.curriculum.subject_registry` exists within [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] to own the behavior summarized by its module contract: Registry review (spec_source_ingestion_v2 §5.7; spec_knowledge_model §3.4, §12.2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/curriculum/subject_registry.py](../../../../../../src/learnloop/curriculum/subject_registry.py) |
| Source lines | 231 |
| Owning package | [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class RegistryReviewError(ValueError)` ([source](../../../../../../src/learnloop/curriculum/subject_registry.py), line 24)
  - `__init__(self, code: str, message: str) -> None` (line 25; internal)
- `build_subject_registry(vault, repository, subject_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/subject_registry.py), line 82) — Facet-contract cards + identifiability warnings + lock state (§5.7).
- `propose_facet_merge(vault, repository, *, subject_id: str, retired_facet_id: str, surviving_facet_id: str, rationale: str | None=None, need_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/subject_registry.py), line 138) — Create a pre-lock facet-merge review item (never auto-merge, §12.2).

## Internal implementation anchors

- `_facet_ids_for_subject(vault, subject_id: str) -> list[str]` ([source](../../../../../../src/learnloop/curriculum/subject_registry.py), line 30) — Canonical facet ids exercised by the subject's practice items, plus any facet whose provenance/contract lists the subject — deterministic, sorted.
- `_facet_card(vault, repository, facet, *, lock_result) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/subject_registry.py), line 42)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/registry|learnloop_sidecar.handlers.registry]] — imports `RegistryReviewError`, `build_subject_registry`, `propose_facet_merge`; statically calls `build_subject_registry`, `propose_facet_merge`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/curriculum/curriculum_locks|learnloop.curriculum.curriculum_locks]] — imports `Operation`, `can_apply`; calls `Operation`, `can_apply`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/identifiability|learnloop.learner.identifiability]] — imports `build_registry_view`, `measurement_rank`; calls `build_registry_view`, `measurement_rank`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/registry|learnloop_sidecar.handlers.registry]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_subject_registry.py](../../../../../../tests/test_subject_registry.py) — direct import
  - `test_coarsen_acceptance_resolves_generation_need`
  - `test_propose_facet_merge_creates_review_item_never_auto_merges`
  - `test_propose_facet_merge_rejects_self_merge`
  - `test_propose_merge_refused_when_facet_identity_locked`
  - `test_subject_registry_facet_contract_cards`
  - `test_unknown_subject_raises`

## Modification guidance

- Change subject registry policy here when curriculum owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/curriculum/subject_registry.py](../../../../../../src/learnloop/curriculum/subject_registry.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
