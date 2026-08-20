---
title: "learnloop.content.sources.role_authority"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/sources/role_authority.py"
source_paths:
  - "src/learnloop/content/sources/role_authority.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.sources"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.sources.role_authority module"
  - "src/learnloop/content/sources/role_authority.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-sources"
---

# `learnloop.content.sources.role_authority`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.sources.role_authority` exists within [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] to own the behavior summarized by its module contract: Source-role authority (spec_source_ingestion_v2 §4.2, the single normative authority matrix).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/sources/role_authority.py](../../../../../../../src/learnloop/content/sources/role_authority.py) |
| Source lines | 201 |
| Owning package | [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ManualAuthorityGrant` ([source](../../../../../../../src/learnloop/content/sources/role_authority.py), line 73) — An explicit human override that lifts a fail-closed role (§4.2).
- `class RoleAuthority` ([source](../../../../../../../src/learnloop/content/sources/role_authority.py), line 88) — The resolved authority for a role.
  - `as_dict(self) -> dict[str, object]` (line 99; public)
- `role_authority(role: str | None, *, manual_grant: ManualAuthorityGrant | Mapping[str, object] | None=None) -> RoleAuthority` ([source](../../../../../../../src/learnloop/content/sources/role_authority.py), line 131) — Resolve `{semantic_contract, assessment_alignment}` for a source role (§4.2).
- `default_inventory_profile(role: str | None) -> str` ([source](../../../../../../../src/learnloop/content/sources/role_authority.py), line 179) — The inventory profile a confirmed role implies (§4.2/§7).
- `can_authorize_semantic(role: str | None, *, manual_grant=None) -> bool` ([source](../../../../../../../src/learnloop/content/sources/role_authority.py), line 189) — True iff this role may enter a semantic-contract context (§4.2).
- `can_authorize_assessment(role: str | None, *, manual_grant=None) -> bool` ([source](../../../../../../../src/learnloop/content/sources/role_authority.py), line 198) — True iff this role may contribute assessment alignment (§4.2).

### Module constants

- `KNOWN_ROLES` ([src/learnloop/content/sources/role_authority.py](../../../../../../../src/learnloop/content/sources/role_authority.py), line 25)
- `_MATRIX` ([src/learnloop/content/sources/role_authority.py](../../../../../../../src/learnloop/content/sources/role_authority.py), line 41)
- `_ROLE_PROFILE` ([src/learnloop/content/sources/role_authority.py](../../../../../../../src/learnloop/content/sources/role_authority.py), line 60)

## Internal implementation anchors

- `_coerce_grant(grant: ManualAuthorityGrant | Mapping[str, object] | None) -> ManualAuthorityGrant | None` ([source](../../../../../../../src/learnloop/content/sources/role_authority.py), line 112)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `default_inventory_profile`; statically calls `default_inventory_profile`
- [[Reference/Modules/learnloop/content/synthesis/source_coverage|learnloop.content.synthesis.source_coverage]] — imports `role_authority`; statically calls `role_authority`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `role_authority`; statically calls `role_authority`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] — imports `default_inventory_profile`; statically calls `default_inventory_profile`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_selection|learnloop.content.synthesis.source_unit_selection]] — imports `KNOWN_ROLES`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `KNOWN_ROLES`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/content/synthesis/source_coverage|learnloop.content.synthesis.source_coverage]], [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]], [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]], [[Reference/Modules/learnloop/content/synthesis/source_unit_selection|learnloop.content.synthesis.source_unit_selection]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_source_inventory.py](../../../../../../../tests/test_source_inventory.py) — direct import
  - `test_unknown_role_fails_closed_for_authority`
- [tests/test_source_sets.py](../../../../../../../tests/test_source_sets.py) — direct import
  - `test_one_source_two_sets_different_roles`

## Modification guidance

- Change role authority policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/sources/role_authority.py](../../../../../../../src/learnloop/content/sources/role_authority.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
