---
title: "learnloop.config.template"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/config/template.py"
source_paths:
  - "src/learnloop/config/template.py"
source_commit: "5862283573210deb4a97f060d7ce2b0b0b0eefcf"
source_commit_timestamp: "2026-09-03T10:49:04-07:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
package: "learnloop.config"
layer: "infrastructure"
concepts:
  - "Configuration"
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.config.template module"
  - "src/learnloop/config/template.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-config"
---

# `learnloop.config.template`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/config/_package|learnloop.config]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.config.template` exists within [[Reference/Modules/learnloop/config/_package|learnloop.config]] to own the behavior summarized by its module contract: Generated configuration text and the effective-defaults snapshot contract.

The authoritative system-level explanation remains in [[Configuration]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/config/template.py](../../../../../../src/learnloop/config/template.py) |
| Source lines | 798 |
| Owning package | [[Reference/Modules/learnloop/config/_package|learnloop.config]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `5862283573210deb4a97f060d7ce2b0b0b0eefcf` |
| Commit timestamp | `2026-09-03T10:49:04-07:00` |

## Public API

- `write_default_config(path: Path) -> None` ([source](../../../../../../src/learnloop/config/template.py), line 762) — Write the decision-only template without replacing an existing file.
- `effective_defaults_fingerprint(config: LearnLoopConfig | None=None) -> str` ([source](../../../../../../src/learnloop/config/template.py), line 770) — Content address of the complete effective defaults for a new vault.

### Module constants

- `LEGACY_DEFAULT_CONFIG_TEXT` ([src/learnloop/config/template.py](../../../../../../src/learnloop/config/template.py), line 17)
- `DEFAULT_CONFIG_TEXT` ([src/learnloop/config/template.py](../../../../../../src/learnloop/config/template.py), line 703)
- `DEFAULTS_SNAPSHOT_BY_ALGORITHM` ([src/learnloop/config/template.py](../../../../../../src/learnloop/config/template.py), line 757)

### Explicit exports

`__all__` declares:

- `DEFAULT_CONFIG_TEXT`
- `DEFAULTS_SNAPSHOT_BY_ALGORITHM`
- `LEGACY_DEFAULT_CONFIG_TEXT`
- `effective_defaults_fingerprint`
- `write_default_config`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `module`
- [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]] — imports `write_default_config`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `LearnLoopConfig`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `json`, `pathlib`, `tomllib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/config/__init__|learnloop.config]], [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_config_refactor.py](../../../../../../tests/test_config_refactor.py) — direct import
  - `test_config_responsibilities_have_canonical_module_owners`

## Modification guidance

- Change configuration behavior in the schema, loader, compatibility normalizer, or template owner that matches the concern; preserve one-way legacy normalization.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/config/template.py](../../../../../../src/learnloop/config/template.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
