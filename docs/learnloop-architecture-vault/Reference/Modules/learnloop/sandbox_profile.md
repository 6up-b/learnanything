---
title: "learnloop.sandbox_profile"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/sandbox_profile.py"
source_paths:
  - "src/learnloop/sandbox_profile.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.sandbox_profile module"
  - "src/learnloop/sandbox_profile.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.sandbox_profile`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.sandbox_profile` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: The hardened bubblewrap profile every sandboxed run of untrusted Python shares.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/sandbox_profile.py](../../../../../src/learnloop/sandbox_profile.py) |
| Source lines | 100 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `bwrap_path() -> str | None` ([source](../../../../../src/learnloop/sandbox_profile.py), line 26) — The bubblewrap binary to sandbox with, or None off Linux.
- `executable_mount_roots(executable: str) -> set[str]` ([source](../../../../../src/learnloop/sandbox_profile.py), line 34) — Install roots (``<root>/bin/exe`` → ``<root>``) for an executable and every hop of its symlink chain, so a venv python that links into e.g.
- `sandboxed_command(command: list[str], workdir: Path, bwrap: str, *, hardened: bool=True, unset_env: tuple[str, ...]=(), extra_args: Sequence[str]=()) -> list[str]` ([source](../../../../../src/learnloop/sandbox_profile.py), line 51) — Wrap ``command`` in bubblewrap: every namespace unshared (so no network), system and interpreter mounts read-only, ``workdir`` as the only writable bind, and the sandbox dying with its parent.

### Module constants

- `HARDENED_BWRAP_FLAGS` ([src/learnloop/sandbox_profile.py](../../../../../src/learnloop/sandbox_profile.py), line 23)

### Explicit exports

`__all__` declares:

- `HARDENED_BWRAP_FLAGS`
- `bwrap_path`
- `executable_mount_roots`
- `sandboxed_command`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]] — imports `HARDENED_BWRAP_FLAGS`, `bwrap_path`, `executable_mount_roots`, `sandboxed_command`; statically calls `bwrap_path`, `sandboxed_command`
- [[Reference/Modules/learnloop/notebook_runtime/sandbox|learnloop.notebook_runtime.sandbox]] — imports `bwrap_path`, `sandboxed_command`; statically calls `bwrap_path`, `sandboxed_command`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `os`, `pathlib`, `shutil`, `sys`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]], [[Reference/Modules/learnloop/notebook_runtime/sandbox|learnloop.notebook_runtime.sandbox]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/rich_fixtures.py](../../../../../tests/rich_fixtures.py) — imports consumer [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]]
- [tests/test_concept_animation_service.py](../../../../../tests/test_concept_animation_service.py) — imports consumer [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]]
- [tests/test_concept_animation_validator.py](../../../../../tests/test_concept_animation_validator.py) — imports consumer [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]]
- [tests/test_figure_rich_contract.py](../../../../../tests/test_figure_rich_contract.py) — imports consumer [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]]
- [tests/test_manim_figure_checks.py](../../../../../tests/test_manim_figure_checks.py) — imports consumer [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]]
- [tests/test_manim_sandbox_hostile.py](../../../../../tests/test_manim_sandbox_hostile.py) — imports consumer [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]]
- [tests/test_sidecar_animation.py](../../../../../tests/test_sidecar_animation.py) — imports consumer [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]]
- [tests/test_structured_transport_parity.py](../../../../../tests/test_structured_transport_parity.py) — imports consumer [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]]
- [tests/notebook_runtime_helpers.py](../../../../../tests/notebook_runtime_helpers.py) — imports consumer [[Reference/Modules/learnloop/notebook_runtime/sandbox|learnloop.notebook_runtime.sandbox]]
- [tests/test_notebook_rpcs.py](../../../../../tests/test_notebook_rpcs.py) — imports consumer [[Reference/Modules/learnloop/notebook_runtime/sandbox|learnloop.notebook_runtime.sandbox]]
- [tests/test_notebook_runtime.py](../../../../../tests/test_notebook_runtime.py) — imports consumer [[Reference/Modules/learnloop/notebook_runtime/sandbox|learnloop.notebook_runtime.sandbox]]
- [tests/test_notebook_runtime_sandbox.py](../../../../../tests/test_notebook_runtime_sandbox.py) — imports consumer [[Reference/Modules/learnloop/notebook_runtime/sandbox|learnloop.notebook_runtime.sandbox]]

## Modification guidance

- Make changes here when the responsibility remains sandbox profile within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/sandbox_profile.py](../../../../../src/learnloop/sandbox_profile.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
