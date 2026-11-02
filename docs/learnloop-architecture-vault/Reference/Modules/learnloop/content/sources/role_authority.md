---
title: "learnloop.content.sources.role_authority"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/sources/role_authority.py"
source_paths:
  - "src/learnloop/content/sources/role_authority.py"
source_commit: "e63a81c0807f929ac4cc5b77e209a5beace229a1"
source_commit_timestamp: "2026-11-01T13:52:05-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
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
| Source lines | 268 |
| Owning package | [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e63a81c0807f929ac4cc5b77e209a5beace229a1` |
| Commit timestamp | `2026-11-01T13:52:05-05:00` |

## Public API

- `class ManualAuthorityGrant` ([source](../../../../../../../src/learnloop/content/sources/role_authority.py), line 82) — An explicit human override that lifts a fail-closed role (§4.2).
- `class RoleAuthority` ([source](../../../../../../../src/learnloop/content/sources/role_authority.py), line 97) — The resolved authority for a role.
  - `as_dict(self) -> dict[str, object]` (line 108; public)
- `role_authority(role: str | None, *, manual_grant: ManualAuthorityGrant | Mapping[str, object] | None=None) -> RoleAuthority` ([source](../../../../../../../src/learnloop/content/sources/role_authority.py), line 140) — Resolve `{semantic_contract, assessment_alignment}` for a source role (§4.2).
- `default_inventory_profile(role: str | None) -> str` ([source](../../../../../../../src/learnloop/content/sources/role_authority.py), line 188) — The inventory profile a confirmed role implies (§4.2/§7).
- `can_authorize_semantic(role: str | None, *, manual_grant=None) -> bool` ([source](../../../../../../../src/learnloop/content/sources/role_authority.py), line 198) — True iff this role may enter a semantic-contract context (§4.2).
- `can_authorize_assessment(role: str | None, *, manual_grant=None) -> bool` ([source](../../../../../../../src/learnloop/content/sources/role_authority.py), line 207) — True iff this role may contribute assessment alignment (§4.2).
- `is_scope_only_role(role: str | None) -> bool` ([source](../../../../../../../src/learnloop/content/sources/role_authority.py), line 240) — True iff the role's material only scopes a deliverable (``syllabus``, curriculum C3).
- `is_semantic_support(role: str | None, relation: str | None) -> bool` ([source](../../../../../../../src/learnloop/content/sources/role_authority.py), line 246) — True iff a citation with this effective role and relation supports a semantic claim.
- `support_verdict(citations: Iterable[tuple[str | None, str | None]]) -> str` ([source](../../../../../../../src/learnloop/content/sources/role_authority.py), line 252) — Judge a claim's ``(role, relation)`` citations (§4.2).

### Module constants

- `KNOWN_ROLES` ([src/learnloop/content/sources/role_authority.py](../../../../../../../src/learnloop/content/sources/role_authority.py), line 25)
- `_MATRIX` ([src/learnloop/content/sources/role_authority.py](../../../../../../../src/learnloop/content/sources/role_authority.py), line 42)
- `_ROLE_PROFILE` ([src/learnloop/content/sources/role_authority.py](../../../../../../../src/learnloop/content/sources/role_authority.py), line 66)
- `ASSESSMENT_ONLY_ROLES` ([src/learnloop/content/sources/role_authority.py](../../../../../../../src/learnloop/content/sources/role_authority.py), line 223)
- `SCOPE_ONLY_ROLES` ([src/learnloop/content/sources/role_authority.py](../../../../../../../src/learnloop/content/sources/role_authority.py), line 227)
- `SEMANTIC_SUPPORT_RELATIONS` ([src/learnloop/content/sources/role_authority.py](../../../../../../../src/learnloop/content/sources/role_authority.py), line 229)
- `CITATION_RELATIONS` ([src/learnloop/content/sources/role_authority.py](../../../../../../../src/learnloop/content/sources/role_authority.py), line 231)
- `EXPLANATORY` ([src/learnloop/content/sources/role_authority.py](../../../../../../../src/learnloop/content/sources/role_authority.py), line 235)
- `EXAM_UNCORROBORATED` ([src/learnloop/content/sources/role_authority.py](../../../../../../../src/learnloop/content/sources/role_authority.py), line 236)
- `UNSUPPORTED` ([src/learnloop/content/sources/role_authority.py](../../../../../../../src/learnloop/content/sources/role_authority.py), line 237)

## Internal implementation anchors

- `_coerce_grant(grant: ManualAuthorityGrant | Mapping[str, object] | None) -> ManualAuthorityGrant | None` ([source](../../../../../../../src/learnloop/content/sources/role_authority.py), line 121)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]] — imports `ASSESSMENT_ONLY_ROLES`, `CITATION_RELATIONS`, `EXAM_UNCORROBORATED`, `EXPLANATORY`, `can_authorize_semantic`, `is_semantic_support`, `support_verdict`; statically calls `can_authorize_semantic`, `is_semantic_support`, `support_verdict`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `default_inventory_profile`; statically calls `default_inventory_profile`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `ASSESSMENT_ONLY_ROLES`, `is_scope_only_role`
- [[Reference/Modules/learnloop/content/synthesis/source_coverage|learnloop.content.synthesis.source_coverage]] — imports `role_authority`; statically calls `role_authority`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `is_scope_only_role`, `role_authority`; statically calls `is_scope_only_role`, `role_authority`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] — imports `default_inventory_profile`; statically calls `default_inventory_profile`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_selection|learnloop.content.synthesis.source_unit_selection]] — imports `KNOWN_ROLES`
- [[Reference/Modules/learnloop/content/synthesis/synthesis_gates|learnloop.content.synthesis.synthesis_gates]] — imports `ASSESSMENT_ONLY_ROLES`, `EXAM_UNCORROBORATED`, `EXPLANATORY`, `support_verdict`; statically calls `support_verdict`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `KNOWN_ROLES`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `role_authority`; statically calls `role_authority`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `SCOPE_ONLY_ROLES`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `is_scope_only_role`; statically calls `is_scope_only_role`

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

Static participation evidence comes from [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]], [[Reference/Modules/learnloop/content/synthesis/source_coverage|learnloop.content.synthesis.source_coverage]], [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] and 7 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_curriculum_c3_exam_scoping.py](../../../../../../../tests/test_curriculum_c3_exam_scoping.py) — direct import
  - `test_the_syllabus_role_scopes_only_assessment_alignment_never_semantic_never_exam`
- [tests/test_exam_protection_identity.py](../../../../../../../tests/test_exam_protection_identity.py) — direct import
  - `test_the_ledgers_exam_roles_are_the_role_authoritys`
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
