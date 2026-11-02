---
title: "learnloop.practice_index.tool"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/practice_index/tool.py"
source_paths:
  - "src/learnloop/practice_index/tool.py"
source_commit: "94fdc9e58fcad72de389eb8b5798f42fa91c8886"
source_commit_timestamp: "2026-10-12T01:10:52-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.practice_index"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.practice_index.tool module"
  - "src/learnloop/practice_index/tool.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-practice-index"
---

# `learnloop.practice_index.tool`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.practice_index.tool` exists within [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] to own the behavior summarized by its module contract: ``find_practice`` as an agent tool: a JSON-schema declaration and a dispatcher.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/practice_index/tool.py](../../../../../../src/learnloop/practice_index/tool.py) |
| Source lines | 55 |
| Owning package | [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `94fdc9e58fcad72de389eb8b5798f42fa91c8886` |
| Commit timestamp | `2026-10-12T01:10:52-04:00` |

## Public API

- `class FindPracticeArguments(BaseModel)` ([source](../../../../../../src/learnloop/practice_index/tool.py), line 20)
- `run_find_practice_tool(vault: LoadedVault, repository: Repository, arguments: Mapping[str, Any], **kwargs: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/practice_index/tool.py), line 48)

### Module constants

- `FIND_PRACTICE_TOOL` ([src/learnloop/practice_index/tool.py](../../../../../../src/learnloop/practice_index/tool.py), line 36)

### Explicit exports

`__all__` declares:

- `FIND_PRACTICE_TOOL`
- `FindPracticeArguments`
- `run_find_practice_tool`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/practice_index|learnloop.cli.practice_index]] — imports `FIND_PRACTICE_TOOL`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `PracticeConstraints`, `find_practice`; calls `find_practice`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/practice_index|learnloop.cli.practice_index]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_practice_index_find.py](../../../../../../tests/test_practice_index_find.py) — direct import
  - `test_kill_switch_and_the_agent_tool`
- [tests/test_practice_index_text.py](../../../../../../tests/test_practice_index_text.py) — direct import
  - `test_agent_tool_declares_a_closed_schema`

## Modification guidance

- Make changes here when the responsibility remains tool within learnloop.practice_index; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/practice_index/tool.py](../../../../../../src/learnloop/practice_index/tool.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
