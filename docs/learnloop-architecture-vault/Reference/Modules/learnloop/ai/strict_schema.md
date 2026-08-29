---
title: "learnloop.ai.strict_schema"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/strict_schema.py"
source_paths:
  - "src/learnloop/ai/strict_schema.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.ai"
layer: "infrastructure"
concepts:
  - "AI Architecture"
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
  - "Process Model Output"
aliases:
  - "learnloop.ai.strict_schema module"
  - "src/learnloop/ai/strict_schema.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.strict_schema`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.strict_schema` exists within [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] to own the behavior summarized by its module contract: Strict JSON-schema conversion shared by structured transports.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/strict_schema.py](../../../../../../src/learnloop/ai/strict_schema.py) |
| Source lines | 185 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `strict_output_schema(model: type[BaseModel]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ai/strict_schema.py), line 34) — Return a schema accepted by Codex's strict Responses API wrapper.
- `map_typed_schema_paths(model: type[BaseModel]) -> list[str]` ([source](../../../../../../src/learnloop/ai/strict_schema.py), line 124) — Locate open-keyed object fields, which strict output cannot express.

### Module constants

- `_UNSUPPORTED_STRICT_SCHEMA_KEYS` ([src/learnloop/ai/strict_schema.py](../../../../../../src/learnloop/ai/strict_schema.py), line 11)

### Explicit exports

`__all__` declares:

- `_codex_output_schema`
- `_strict_json_schema`
- `map_typed_schema_paths`
- `strict_output_schema`

## Internal implementation anchors

- `_strict_json_schema(value: Any) -> Any` ([source](../../../../../../src/learnloop/ai/strict_schema.py), line 57)
- `_flatten_nested_any_of(schema: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop/ai/strict_schema.py), line 105) — Splice ``anyOf`` members that are themselves a bare ``anyOf`` wrapper.
- `_is_object_schema(schema: dict[str, Any]) -> bool` ([source](../../../../../../src/learnloop/ai/strict_schema.py), line 168)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]] — imports `strict_output_schema`; statically calls `strict_output_schema`
- [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]] — imports `strict_output_schema`; statically calls `strict_output_schema`
- [[Reference/Modules/learnloop/ai/providers/structured_output|learnloop.ai.providers.structured_output]] — imports `strict_output_schema`; statically calls `strict_output_schema`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `strict_output_schema`; statically calls `strict_output_schema`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]], [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]], [[Reference/Modules/learnloop/ai/providers/structured_output|learnloop.ai.providers.structured_output]], [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_attribution_p0.py](../../../../../../tests/test_causal_attribution_p0.py) — direct import
  - `test_grading_schema_is_prose_first`
- [tests/test_codex_output_schema.py](../../../../../../tests/test_codex_output_schema.py) — direct import
  - `test_append_schema_declares_properties_on_bare_restructure_payload`
  - `test_codex_authoring_schema_is_strict_response_format_compatible`
  - `test_codex_grading_schema_is_strict_response_format_compatible`
  - `test_codex_teach_back_authoring_schema_is_strict_response_format_compatible`
  - `test_discriminated_target_ref_is_a_flat_nullable_any_of`
  - `test_every_codex_schema_uses_only_strict_supported_keywords`
  - `test_no_new_open_keyed_map_fields_are_introduced`
  - `test_output_schema_refuses_a_model_outside_the_wire_hierarchy`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/strict_schema.py](../../../../../../src/learnloop/ai/strict_schema.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
