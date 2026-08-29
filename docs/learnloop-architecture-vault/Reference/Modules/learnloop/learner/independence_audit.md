---
title: "learnloop.learner.independence_audit"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/independence_audit.py"
source_paths:
  - "src/learnloop/learner/independence_audit.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.learner"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Inspect Persistent State"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.learner.independence_audit module"
  - "src/learnloop/learner/independence_audit.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.independence_audit`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.independence_audit` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: Re-check every belief promoted on "independent surface" against the one primitive.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/independence_audit.py](../../../../../../src/learnloop/learner/independence_audit.py) |
| Source lines | 278 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class BeliefIndependenceRow` ([source](../../../../../../src/learnloop/learner/independence_audit.py), line 78) — One promoted belief, re-judged.
  - `should_withdraw(self) -> bool` (line 91; public)
  - `as_dict(self) -> dict[str, Any]` (line 94; public)
- `class IndependenceAuditReport` ([source](../../../../../../src/learnloop/learner/independence_audit.py), line 108)
  - `summary(self) -> dict[str, int]` (line 114; public)
  - `as_dict(self) -> dict[str, Any]` (line 120; public)
- `audit_independent_surface_promotions(vault: LoadedVault, repository: Repository) -> IndependenceAuditReport` ([source](../../../../../../src/learnloop/learner/independence_audit.py), line 149) — Re-judge every durably-promoted belief under the corrected rule.
- `apply_independence_audit(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> IndependenceAuditReport` ([source](../../../../../../src/learnloop/learner/independence_audit.py), line 226) — Withdraw every belief whose independence does not survive recomputation.

### Module constants

- `INDEPENDENT_SURFACE_REASON` ([src/learnloop/learner/independence_audit.py](../../../../../../src/learnloop/learner/independence_audit.py), line 67)
- `WITHDRAWAL_REASON` ([src/learnloop/learner/independence_audit.py](../../../../../../src/learnloop/learner/independence_audit.py), line 72)

## Internal implementation anchors

- `_promoting_item_ids(repository: Repository, belief) -> tuple[str, ...] | None` ([source](../../../../../../src/learnloop/learner/independence_audit.py), line 131) — Item ids of the candidate this belief was promoted from, or None.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `apply_independence_audit`, `audit_independent_surface_promotions`; statically calls `apply_independence_audit`, `audit_independent_surface_promotions`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner/surfaced_beliefs|learnloop.learner.surfaced_beliefs]] — imports `SurfacedBeliefError`, `record_belief_withdrawal`; calls `record_belief_withdrawal`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/tutor/durable_promotion|learnloop.tutor.durable_promotion]] — imports `ANY_BELIEF_STATUS`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_causal_attribution_p1.py](../../../../../../tests/test_causal_attribution_p1.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_causal_trace_consistency_p2.py](../../../../../../tests/test_causal_trace_consistency_p2.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_certification_cold_probe.py](../../../../../../tests/test_certification_cold_probe.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_cli_attempt.py](../../../../../../tests/test_cli_attempt.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_cli_commands.py](../../../../../../tests/test_cli_commands.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_cli_entrypoint.py](../../../../../../tests/test_cli_entrypoint.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_cli_fit.py](../../../../../../tests/test_cli_fit.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_cli_generate_practice.py](../../../../../../tests/test_cli_generate_practice.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_cli_help_snapshot.py](../../../../../../tests/test_cli_help_snapshot.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_cli_ingest.py](../../../../../../tests/test_cli_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_cli_json.py](../../../../../../tests/test_cli_json.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_cli_observations.py](../../../../../../tests/test_cli_observations.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]

## Modification guidance

- Change independence audit policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/independence_audit.py](../../../../../../src/learnloop/learner/independence_audit.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
