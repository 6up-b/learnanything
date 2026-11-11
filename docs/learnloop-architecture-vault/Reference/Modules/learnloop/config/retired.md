---
title: "learnloop.config.retired"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/config/retired.py"
source_paths:
  - "src/learnloop/config/retired.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.config"
layer: "infrastructure"
concepts:
  - "Configuration"
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.config.retired module"
  - "src/learnloop/config/retired.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-config"
---

# `learnloop.config.retired`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/config/_package|learnloop.config]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.config.retired` exists within [[Reference/Modules/learnloop/config/_package|learnloop.config]] to own the behavior summarized by its module contract: Config fields arc C retired, kept only for the identities that hashed them.

The authoritative system-level explanation remains in [[Configuration]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/config/retired.py](../../../../../../src/learnloop/config/retired.py) |
| Source lines | 177 |
| Owning package | [[Reference/Modules/learnloop/config/_package|learnloop.config]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class RetiredField` ([source](../../../../../../src/learnloop/config/retired.py), line 29) — A removed field: the model class it lived on, its path there (two names for a leaf of a removed section), its type and default there, and the arc C step that removed it.
- `class KeepsRetiredFields(BaseModel)` ([source](../../../../../../src/learnloop/config/retired.py), line 87) — A config model some of whose fields arc C retired (:data:`RETIRED_FIELDS`).
  - `_remember_retired_values(cls, data: Any, handler: Any) -> Any` (line 98; internal)
- `remembering(model: _Model, **values: Any) -> _Model` ([source](../../../../../../src/learnloop/config/retired.py), line 108) — ``model``, remembering ``values`` for its retired fields as if its input had set them: a built-in default that set one at construction before arc C (the ``recall_failure`` impact's ``lo_mastery_delta``).
- `identity_dump(model: BaseModel) -> dict[str, Any]` ([source](../../../../../../src/learnloop/config/retired.py), line 119) — ``model.model_dump(mode="json")`` with every retired field under it put back, for a hash that is compared.
- `identity_view(model: BaseModel, fields: tuple[str, ...]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/config/retired.py), line 131) — The named ``fields`` of :func:`identity_dump`: an explicit identity view of a flat config section.

### Module constants

- `RETIRED_FIELDS` ([src/learnloop/config/retired.py](../../../../../../src/learnloop/config/retired.py), line 41)
- `_BY_MODEL` ([src/learnloop/config/retired.py](../../../../../../src/learnloop/config/retired.py), line 56)
- `_MISSING` ([src/learnloop/config/retired.py](../../../../../../src/learnloop/config/retired.py), line 60)

### Explicit exports

`__all__` declares:

- `RETIRED_FIELDS`
- `KeepsRetiredFields`
- `RetiredField`
- `identity_dump`
- `identity_view`
- `remembering`

## Internal implementation anchors

- `_adapter(annotation: Any) -> TypeAdapter[Any]` ([source](../../../../../../src/learnloop/config/retired.py), line 65)
- `_coerce(field: RetiredField, raw: Any) -> Any` ([source](../../../../../../src/learnloop/config/retired.py), line 69) — ``raw`` as the removed field read it (lax pydantic validation of its old type), JSON-safe.
- `_given(data: Any, path: tuple[str, ...]) -> Any` ([source](../../../../../../src/learnloop/config/retired.py), line 79)
- `_put_back(model: BaseModel, dump: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop/config/retired.py), line 148)
- `_descend(value: Any, node: Any) -> None` ([source](../../../../../../src/learnloop/config/retired.py), line 165)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]] — imports `identity_dump`; statically calls `identity_dump`
- [[Reference/Modules/learnloop/cli/success_head|learnloop.cli.success_head]] — imports `identity_dump`; statically calls `identity_dump`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `KeepsRetiredFields`, `remembering`; statically calls `remembering`
- [[Reference/Modules/learnloop/content/facet_identity/judge|learnloop.content.facet_identity.judge]] — imports `identity_view`; statically calls `identity_view`
- [[Reference/Modules/learnloop/content/synthesis/graph_nomination|learnloop.content.synthesis.graph_nomination]] — imports `identity_view`; statically calls `identity_view`
- [[Reference/Modules/learnloop/field/predictors|learnloop.field.predictors]] — imports `identity_dump`; statically calls `identity_dump`
- [[Reference/Modules/learnloop/ops/embedding_compare|learnloop.ops.embedding_compare]] — imports `identity_dump`; statically calls `identity_dump`
- [[Reference/Modules/learnloop/placement/predictor|learnloop.placement.predictor]] — imports `identity_dump`; statically calls `identity_dump`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `functools`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]], [[Reference/Modules/learnloop/cli/success_head|learnloop.cli.success_head]], [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]], [[Reference/Modules/learnloop/content/facet_identity/judge|learnloop.content.facet_identity.judge]], [[Reference/Modules/learnloop/content/synthesis/graph_nomination|learnloop.content.synthesis.graph_nomination]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/identity_pins_helpers.py](../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/test_identity_pins.py](../../../../../../tests/test_identity_pins.py) — direct import
  - `test_an_identity_view_leaves_out_an_added_field_and_refuses_a_removed_one`
- [tests/test_retired_config_identities.py](../../../../../../tests/test_retired_config_identities.py) — direct import
  - `test_retired_fields_stay_off_the_models_and_out_of_every_other_dump`
  - `test_the_config_identity_reproduces_both_recorded_digests`

## Modification guidance

- Change configuration behavior in the schema, loader, compatibility normalizer, or template owner that matches the concern; preserve one-way legacy normalization.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/config/retired.py](../../../../../../src/learnloop/config/retired.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
