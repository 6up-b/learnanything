---
title: "learnloop.content.facet_identity.span_support"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/facet_identity/span_support.py"
source_paths:
  - "src/learnloop/content/facet_identity/span_support.py"
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
  - "learnloop.content.facet_identity.span_support module"
  - "src/learnloop/content/facet_identity/span_support.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-facet-identity"
---

# `learnloop.content.facet_identity.span_support`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.facet_identity.span_support` exists within [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] to own the behavior summarized by its module contract: The span-support check of a model-proposed facet reword (owner, 2026-10-13).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/facet_identity/span_support.py](../../../../../../../src/learnloop/content/facet_identity/span_support.py) |
| Source lines | 137 |
| Owning package | [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `unchecked(input_hash: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/span_support.py), line 66) — No verdict was asked for this input before the vault lock: the reword waits for the confirm.
- `check(vault: Any, repository: Any, resolver: Any, facet_id: str, after: Mapping[str, Any], citations: Sequence[Any], *, asked: Mapping[str, Mapping[str, Any]] | None=None, record: MutableMapping[str, dict[str, Any]] | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/span_support.py), line 73) — Ask the Decider; the result's ``verdict`` is its top option, or None without an answer.
- `label(connection: Any, record: Mapping[str, Any], *, action: str) -> str | None` ([source](../../../../../../../src/learnloop/content/facet_identity/span_support.py), line 116) — Append the owner's label for the check that held ``record`` (None when no check held it).

### Module constants

- `TASK` ([src/learnloop/content/facet_identity/span_support.py](../../../../../../../src/learnloop/content/facet_identity/span_support.py), line 50)
- `QUESTION` ([src/learnloop/content/facet_identity/span_support.py](../../../../../../../src/learnloop/content/facet_identity/span_support.py), line 51)
- `OWNER_LABELS` ([src/learnloop/content/facet_identity/span_support.py](../../../../../../../src/learnloop/content/facet_identity/span_support.py), line 63)

### Explicit exports

`__all__` declares:

- `OWNER_LABELS`
- `QUESTION`
- `TASK`
- `check`
- `label`
- `unchecked`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]] — imports `module`; statically calls `label`
- [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]] — imports `check`; statically calls `check`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/decisions|learnloop.ai.decisions]] — imports `ChoiceQuestion`; calls `ChoiceQuestion`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]] — imports `authority_meaning`; calls `authority_meaning`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `decide`; calls `decide`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]], [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_facet_span_support.py](../../../../../../../tests/test_facet_span_support.py) — direct import
  - `test_a_check_whose_input_changed_under_the_lock_waits_for_the_confirm`

## Modification guidance

- Change span support policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/facet_identity/span_support.py](../../../../../../../src/learnloop/content/facet_identity/span_support.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
