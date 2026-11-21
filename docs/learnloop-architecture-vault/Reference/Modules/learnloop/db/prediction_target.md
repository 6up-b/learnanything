---
title: "learnloop.db.prediction_target"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/prediction_target.py"
source_paths:
  - "src/learnloop/db/prediction_target.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.prediction_target module"
  - "src/learnloop/db/prediction_target.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db"
---

# `learnloop.db.prediction_target`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/_package|learnloop.db]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.prediction_target` exists within [[Reference/Modules/learnloop/db/_package|learnloop.db]] to own the behavior summarized by its module contract: What a prediction was about: its target, serialized canonically and hashed (EP spec §7.7.2, §7.7.4).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/prediction_target.py](../../../../../../src/learnloop/db/prediction_target.py) |
| Source lines | 160 |
| Owning package | [[Reference/Modules/learnloop/db/_package|learnloop.db]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class TargetMember` ([source](../../../../../../src/learnloop/db/prediction_target.py), line 47) — One member: its kind and id, the revision it was predicted at (an item's content hash), and the source of its identity where that can differ (a surface-group key's: authored, or derived from the item).
  - `__post_init__(self) -> None` (line 56; internal)
  - `sort_key(self) -> tuple[str, str, str, str]` (line 63; public)
  - `to_dict(self) -> dict[str, str | None]` (line 68; public)
  - `from_dict(cls, raw: Mapping[str, Any]) -> 'TargetMember'` (line 72; public)
- `class PredictionTarget` ([source](../../../../../../src/learnloop/db/prediction_target.py), line 77) — What a forecast is about (module docstring).
  - `__post_init__(self) -> None` (line 93; internal)
  - `to_dict(self) -> dict[str, Any]` (line 110; public) — The canonical form: every field, members in canonical order.
  - `canonical_json(self) -> str` (line 125; public) — Sorted keys, compact separators, UTF-8 text kept as is: the bytes ``target_hash`` hashes.
  - `target_hash(self) -> str` (line 130; public) — ``sha256:<hex>`` of :meth:`canonical_json` (a pinned identity, ``tests/identity_pins_helpers.py``).
  - `from_dict(cls, raw: Mapping[str, Any]) -> 'PredictionTarget'` (line 136; public)
  - `from_json(cls, text: str) -> 'PredictionTarget'` (line 156; public)

### Module constants

- `TARGET_SCHEMA` ([src/learnloop/db/prediction_target.py](../../../../../../src/learnloop/db/prediction_target.py), line 24)
- `MEMBER_ITEM` ([src/learnloop/db/prediction_target.py](../../../../../../src/learnloop/db/prediction_target.py), line 27)
- `MEMBER_LEARNING_OBJECT` ([src/learnloop/db/prediction_target.py](../../../../../../src/learnloop/db/prediction_target.py), line 28)
- `MEMBER_FACET` ([src/learnloop/db/prediction_target.py](../../../../../../src/learnloop/db/prediction_target.py), line 29)
- `MEMBER_SURFACE_GROUP` ([src/learnloop/db/prediction_target.py](../../../../../../src/learnloop/db/prediction_target.py), line 30)
- `MEMBER_KINDS` ([src/learnloop/db/prediction_target.py](../../../../../../src/learnloop/db/prediction_target.py), line 31)

### Explicit exports

`__all__` declares:

- `MEMBER_KINDS`
- `PredictionTarget`
- `TARGET_SCHEMA`
- `TargetMember`

## Internal implementation anchors

- `_text(value: Any, name: str, *, optional: bool=True) -> str | None` ([source](../../../../../../src/learnloop/db/prediction_target.py), line 34)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

No live LearnLoop module directly imports this module in the static graph.

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

No live LearnLoop module imports it directly; its current reach is tests, repository tooling, dynamic registration, or explicit manual invocation where documented above.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/identity_pins_helpers.py](../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/test_prediction_target.py](../../../../../../tests/test_prediction_target.py) — direct import
  - `test_a_missing_revision_differs_from_an_empty_one`
  - `test_every_typed_field_moves_the_hash`
  - `test_refusals`
  - `test_round_trip`
  - `test_the_pinned_target_is_the_identity_pins_fixture`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/prediction_target.py](../../../../../../src/learnloop/db/prediction_target.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
