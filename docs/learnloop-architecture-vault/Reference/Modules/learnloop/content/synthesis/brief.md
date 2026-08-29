---
title: "learnloop.content.synthesis.brief"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/brief.py"
source_paths:
  - "src/learnloop/content/synthesis/brief.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.synthesis"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.synthesis.brief module"
  - "src/learnloop/content/synthesis/brief.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-synthesis"
---

# `learnloop.content.synthesis.brief`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.brief` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: Typed synthesis brief (spec §8 / mvp-0.8 reader-first seeding).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/brief.py](../../../../../../../src/learnloop/content/synthesis/brief.py) |
| Source lines | 140 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class Brief(BaseModel)` ([source](../../../../../../../src/learnloop/content/synthesis/brief.py), line 66) — Known brief fields.
- `class BriefValidationError(ValueError)` ([source](../../../../../../../src/learnloop/content/synthesis/brief.py), line 106)
  - `__init__(self, errors: list[str])` (line 107; internal)
- `validate_brief(raw: dict[str, Any] | None, *, strict: bool=True) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/brief.py), line 112) — Normalize + validate a brief dict, returning a snake_case dict.

### Module constants

- `STARTING_LEVELS` ([src/learnloop/content/synthesis/brief.py](../../../../../../../src/learnloop/content/synthesis/brief.py), line 28)
- `STARTING_LEVEL_CLAIMS` ([src/learnloop/content/synthesis/brief.py](../../../../../../../src/learnloop/content/synthesis/brief.py), line 35)
- `INIT_CLAIM_PSEUDO_COUNT` ([src/learnloop/content/synthesis/brief.py](../../../../../../../src/learnloop/content/synthesis/brief.py), line 42)
- `NARROW_ADJUNCT_SCOPE` ([src/learnloop/content/synthesis/brief.py](../../../../../../../src/learnloop/content/synthesis/brief.py), line 49)
- `_AUTHORING_PRESET_DEFAULTS` ([src/learnloop/content/synthesis/brief.py](../../../../../../../src/learnloop/content/synthesis/brief.py), line 56)
- `_CAMEL_BOUNDARY` ([src/learnloop/content/synthesis/brief.py](../../../../../../../src/learnloop/content/synthesis/brief.py), line 95)

## Internal implementation anchors

- `_snake_name(name: str) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/brief.py), line 98)
- `_snake_keys(raw: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/brief.py), line 102)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/bootstrap|learnloop.bootstrap]] — imports `STARTING_LEVELS`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `BriefValidationError`, `validate_brief`; statically calls `validate_brief`
- [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]] — imports `validate_brief`; statically calls `validate_brief`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `validate_brief`; statically calls `validate_brief`
- [[Reference/Modules/learnloop/learner/learner_profile|learnloop.learner.learner_profile]] — imports `INIT_CLAIM_PSEUDO_COUNT`, `STARTING_LEVELS`, `STARTING_LEVEL_CLAIMS`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `BriefValidationError`, `validate_brief`; statically calls `validate_brief`
- [[Reference/Modules/learnloop_sidecar/handlers/vault|learnloop_sidecar.handlers.vault]] — imports `STARTING_LEVELS`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `re`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/bootstrap|learnloop.bootstrap]], [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]], [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]], [[Reference/Modules/learnloop/learner/learner_profile|learnloop.learner.learner_profile]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_goal_intent.py](../../../../../../../tests/test_goal_intent.py) — direct import
  - `test_narrow_adjunct_preset_expands_defaults_but_allows_explicit_edits`
  - `test_study_map_brief_preserves_camel_case_learner_intent`
  - `test_study_map_brief_preserves_scope_and_explicit_practice_timing`

## Modification guidance

- Change brief policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/brief.py](../../../../../../../src/learnloop/content/synthesis/brief.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
