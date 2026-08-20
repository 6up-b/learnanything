---
title: "learnloop.scheduling.progression_policy"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/progression_policy.py"
source_paths:
  - "src/learnloop/scheduling/progression_policy.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.progression_policy module"
  - "src/learnloop/scheduling/progression_policy.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.progression_policy`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.progression_policy` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: P1 step 3 -- the progression-policy object (spec_p1_shared_substrate §3.6; owner decision A.2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/progression_policy.py](../../../../../../src/learnloop/scheduling/progression_policy.py) |
| Source lines | 103 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `default_progression_policy_body(policy_slug: str=DEFAULT_POLICY_SLUG) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/progression_policy.py), line 48) — The canonical progression-policy body (§5.4/§5.5/§4.3), seeded from the registered decision-parameter defaults.
- `register_progression_policy(repository: Repository, *, policy_slug: str, body: Mapping[str, Any], version: int=PROGRESSION_POLICY_SCHEMA_VERSION, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/scheduling/progression_policy.py), line 66) — Register an immutable, content-addressed progression-policy version.
- `ensure_default_progression_policy(repository: Repository, *, policy_slug: str=DEFAULT_POLICY_SLUG, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/scheduling/progression_policy.py), line 86) — Seed / resolve the default progression policy (idempotent).
- `load_progression_policy(repository: Repository, policy_version_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/scheduling/progression_policy.py), line 97)

### Module constants

- `PROGRESSION_POLICY_SCHEMA_VERSION` ([src/learnloop/scheduling/progression_policy.py](../../../../../../src/learnloop/scheduling/progression_policy.py), line 35)
- `SIBLING_SUCCESS_SHRINKAGE` ([src/learnloop/scheduling/progression_policy.py](../../../../../../src/learnloop/scheduling/progression_policy.py), line 39)
- `ORTHOGONAL_NEXT_DELAY_DAYS` ([src/learnloop/scheduling/progression_policy.py](../../../../../../src/learnloop/scheduling/progression_policy.py), line 43)
- `DEFAULT_POLICY_SLUG` ([src/learnloop/scheduling/progression_policy.py](../../../../../../src/learnloop/scheduling/progression_policy.py), line 45)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/scheduling/progression|learnloop.scheduling.progression]] — imports `SIBLING_SUCCESS_SHRINKAGE`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_hash`, `canonical_json`; calls `canonical_hash`, `canonical_json`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/scheduling/progression|learnloop.scheduling.progression]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_activity_contract_extensions.py](../../../../../../tests/test_activity_contract_extensions.py) — direct import
  - `test_progression_policy_is_content_addressed`
  - `test_resolve_progression_policy`
- [tests/test_progression.py](../../../../../../tests/test_progression.py) — direct import
  - `test_next_growth_activity_is_delayed_orthogonal_not_near_clone`

## Modification guidance

- Change progression policy policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/progression_policy.py](../../../../../../src/learnloop/scheduling/progression_policy.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
