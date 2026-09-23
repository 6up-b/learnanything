---
title: "learnloop.curriculum.depth_envelopes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/curriculum/depth_envelopes.py"
source_paths:
  - "src/learnloop/curriculum/depth_envelopes.py"
source_commit: "05458003f67c22e36f7c5afc327496383a5f0fc2"
source_commit_timestamp: "2026-09-23T12:30:12-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
package: "learnloop.curriculum"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Build a Study Map"
aliases:
  - "learnloop.curriculum.depth_envelopes module"
  - "src/learnloop/curriculum/depth_envelopes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-curriculum"
---

# `learnloop.curriculum.depth_envelopes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.curriculum.depth_envelopes` exists within [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] to own the behavior summarized by its module contract: Reads of a commitment's pinned depth policy and depth envelope versions.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/curriculum/depth_envelopes.py](../../../../../../src/learnloop/curriculum/depth_envelopes.py) |
| Source lines | 32 |
| Owning package | [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `05458003f67c22e36f7c5afc327496383a5f0fc2` |
| Commit timestamp | `2026-09-23T12:30:12-04:00` |

## Public API

- `depth_policy(repository: Repository, policy_version_id: str | None) -> str | None` ([source](../../../../../../src/learnloop/curriculum/depth_envelopes.py), line 11) — The policy name (for example ``auto_within_envelope``) of a depth-policy version.
- `envelope_edges(repository: Repository, envelope_version_id: str | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/curriculum/depth_envelopes.py), line 20) — Every edge recorded on a depth-envelope version, whether or not it was reviewed.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/curriculum/commitment_arcs|learnloop.curriculum.commitment_arcs]] — imports `depth_policy`, `envelope_edges`; statically calls `depth_policy`, `envelope_edges`
- [[Reference/Modules/learnloop/curriculum/depth_transition|learnloop.curriculum.depth_transition]] — imports `depth_policy`, `envelope_edges`; statically calls `depth_policy`, `envelope_edges`
- [[Reference/Modules/learnloop/curriculum/golden_path_restoration|learnloop.curriculum.golden_path_restoration]] — imports `envelope_edges`; statically calls `envelope_edges`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/curriculum/commitment_arcs|learnloop.curriculum.commitment_arcs]], [[Reference/Modules/learnloop/curriculum/depth_transition|learnloop.curriculum.depth_transition]], [[Reference/Modules/learnloop/curriculum/golden_path_restoration|learnloop.curriculum.golden_path_restoration]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_commitment_arcs.py](../../../../../../tests/test_commitment_arcs.py) — imports consumer [[Reference/Modules/learnloop/curriculum/commitment_arcs|learnloop.curriculum.commitment_arcs]]
- [tests/test_p3_journeys.py](../../../../../../tests/test_p3_journeys.py) — imports consumer [[Reference/Modules/learnloop/curriculum/commitment_arcs|learnloop.curriculum.commitment_arcs]]
- [tests/test_depth_transition.py](../../../../../../tests/test_depth_transition.py) — imports consumer [[Reference/Modules/learnloop/curriculum/depth_transition|learnloop.curriculum.depth_transition]]
- [tests/test_golden_path_assessment.py](../../../../../../tests/test_golden_path_assessment.py) — imports consumer [[Reference/Modules/learnloop/curriculum/depth_transition|learnloop.curriculum.depth_transition]]
- [tests/test_journey6.py](../../../../../../tests/test_journey6.py) — imports consumer [[Reference/Modules/learnloop/curriculum/depth_transition|learnloop.curriculum.depth_transition]]
- [tests/test_p2_acceptance.py](../../../../../../tests/test_p2_acceptance.py) — imports consumer [[Reference/Modules/learnloop/curriculum/golden_path_restoration|learnloop.curriculum.golden_path_restoration]]

## Modification guidance

- Change depth envelopes policy here when curriculum owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/curriculum/depth_envelopes.py](../../../../../../src/learnloop/curriculum/depth_envelopes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
