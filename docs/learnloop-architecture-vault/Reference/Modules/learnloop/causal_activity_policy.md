---
title: "learnloop.causal_activity_policy"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/causal_activity_policy.py"
source_paths:
  - "src/learnloop/causal_activity_policy.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.causal_activity_policy module"
  - "src/learnloop/causal_activity_policy.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.causal_activity_policy`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.causal_activity_policy` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: Dependency-neutral causal activity classification policy primitives.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/causal_activity_policy.py](../../../../../src/learnloop/causal_activity_policy.py) |
| Source lines | 76 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class CausalActivityPolicy` ([source](../../../../../src/learnloop/causal_activity_policy.py), line 27) — Resolved persistence policy for one contamination class.
  - `as_dict(self) -> dict[str, Any]` (line 38; public)
- `policy_for_class(contamination_class: str, *, near_clone: bool=False) -> CausalActivityPolicy` ([source](../../../../../src/learnloop/causal_activity_policy.py), line 52) — Return the versioned matrix row for one contamination class.

### Module constants

- `CAUSAL_ACTIVITY_POLICY_VERSION` ([src/learnloop/causal_activity_policy.py](../../../../../src/learnloop/causal_activity_policy.py), line 14)
- `CONTAMINATION_PRECEDENCE` ([src/learnloop/causal_activity_policy.py](../../../../../src/learnloop/causal_activity_policy.py), line 17)
- `CONTAMINATION_CLASSES` ([src/learnloop/causal_activity_policy.py](../../../../../src/learnloop/causal_activity_policy.py), line 23)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `CAUSAL_ACTIVITY_POLICY_VERSION`, `CONTAMINATION_PRECEDENCE`, `policy_for_class`; statically calls `policy_for_class`
- [[Reference/Modules/learnloop/diagnosis/causal_activity_policy|learnloop.diagnosis.causal_activity_policy]] — imports `CAUSAL_ACTIVITY_POLICY_VERSION`, `CONTAMINATION_CLASSES`, `CONTAMINATION_PRECEDENCE`, `CausalActivityPolicy`, `policy_for_class`; statically calls `CausalActivityPolicy`, `policy_for_class`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/diagnosis/causal_activity_policy|learnloop.diagnosis.causal_activity_policy]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_activity_policy.py](../../../../../tests/test_causal_activity_policy.py) — direct import
  - `test_service_exports_share_the_dependency_neutral_policy_authority`

## Modification guidance

- Make changes here when the responsibility remains causal activity policy within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/causal_activity_policy.py](../../../../../src/learnloop/causal_activity_policy.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
