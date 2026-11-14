---
title: "learnloop.content.facet_identity.views"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/facet_identity/views.py"
source_paths:
  - "src/learnloop/content/facet_identity/views.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.facet_identity"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.facet_identity.views module"
  - "src/learnloop/content/facet_identity/views.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-facet-identity"
---

# `learnloop.content.facet_identity.views`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.facet_identity.views` exists within [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] to own the behavior summarized by its module contract: What the facet-identity judge sees, and what a merge or absorb writes.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/facet_identity/views.py](../../../../../../../src/learnloop/content/facet_identity/views.py) |
| Source lines | 194 |
| Owning package | [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `judge_view(payload: Mapping[str, Any], *, concept_title: str | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/views.py), line 62) — The compact, id-free contract one facet shows the judge.
- `union_payload(survivor: Mapping[str, Any], retired: Sequence[Mapping[str, Any]], *, action: str, absorb_as: str | None=None, alias_ids: Sequence[str]=()) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/views.py), line 121) — The survivor's payload after ``merge``/``absorb`` of ``retired`` into it.
- `comparable_entry(entry: Mapping[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/facet_identity/views.py), line 174) — A facets.yaml entry with the fields a write recomputes removed.

### Module constants

- `UNION_LIST_FIELDS` ([src/learnloop/content/facet_identity/views.py](../../../../../../../src/learnloop/content/facet_identity/views.py), line 30)
- `ABSORB_AS` ([src/learnloop/content/facet_identity/views.py](../../../../../../../src/learnloop/content/facet_identity/views.py), line 41)
- `_TEXT_LIMIT` ([src/learnloop/content/facet_identity/views.py](../../../../../../../src/learnloop/content/facet_identity/views.py), line 42)
- `_SPACE` ([src/learnloop/content/facet_identity/views.py](../../../../../../../src/learnloop/content/facet_identity/views.py), line 43)

### Explicit exports

`__all__` declares:

- `ABSORB_AS`
- `UNION_LIST_FIELDS`
- `comparable_entry`
- `judge_view`
- `union_payload`

## Internal implementation anchors

- `_text(value: Any, limit: int=_TEXT_LIMIT) -> str` ([source](../../../../../../../src/learnloop/content/facet_identity/views.py), line 46)
- `_texts(values: Any, count: int) -> list[str]` ([source](../../../../../../../src/learnloop/content/facet_identity/views.py), line 51)
- `_norm(value: Any) -> str` ([source](../../../../../../../src/learnloop/content/facet_identity/views.py), line 84)
- `_union_strings(base: Sequence[Any], additions: Iterable[Any]) -> list[Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/views.py), line 88)
- `_ref_key(ref: Any) -> str` ([source](../../../../../../../src/learnloop/content/facet_identity/views.py), line 100)
- `_union_refs(base: Sequence[Any], additions: Iterable[Any]) -> list[Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/views.py), line 109)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]] — imports `union_payload`; statically calls `union_payload`
- [[Reference/Modules/learnloop/content/facet_identity/dedupe|learnloop.content.facet_identity.dedupe]] — imports `judge_view`; statically calls `judge_view`
- [[Reference/Modules/learnloop/content/facet_identity/plan|learnloop.content.facet_identity.plan]] — imports `judge_view`, `union_payload`; statically calls `judge_view`, `union_payload`
- [[Reference/Modules/learnloop/content/synthesis/normalize|learnloop.content.synthesis.normalize]] — imports `UNION_LIST_FIELDS`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `copy`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]], [[Reference/Modules/learnloop/content/facet_identity/dedupe|learnloop.content.facet_identity.dedupe]], [[Reference/Modules/learnloop/content/facet_identity/plan|learnloop.content.facet_identity.plan]], [[Reference/Modules/learnloop/content/synthesis/normalize|learnloop.content.synthesis.normalize]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/facet_identity_helpers.py](../../../../../../../tests/facet_identity_helpers.py) — direct import
- [tests/test_facet_identity.py](../../../../../../../tests/test_facet_identity.py) — direct import
  - `test_merge_unions_lists_and_sources_and_absorb_adds_the_claim`

## Modification guidance

- Change views policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/facet_identity/views.py](../../../../../../../src/learnloop/content/facet_identity/views.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
