---
title: "learnloop.placement.claim_check"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/placement/claim_check.py"
source_paths:
  - "src/learnloop/placement/claim_check.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.placement"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.placement.claim_check module"
  - "src/learnloop/placement/claim_check.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-placement"
---

# `learnloop.placement.claim_check`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.placement.claim_check` exists within [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] to own the behavior summarized by its module contract: Claim feedback on the review that resolves it (LP-min (a); LPQ9).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/placement/claim_check.py](../../../../../../src/learnloop/placement/claim_check.py) |
| Source lines | 71 |
| Owning package | [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `claim_check(vault: LoadedVault, repository: Repository, attempt_id: str, *, now_iso: str | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/placement/claim_check.py), line 43) — The claim line for the review ``attempt_id``, or None when it resolves no claim.

### Module constants

- `_LEARNER_CLAIM_SOURCE` ([src/learnloop/placement/claim_check.py](../../../../../../src/learnloop/placement/claim_check.py), line 37)
- `_CHECK_WORDS` ([src/learnloop/placement/claim_check.py](../../../../../../src/learnloop/placement/claim_check.py), line 40)

### Explicit exports

`__all__` declares:

- `claim_check`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `claim_check`; statically calls `claim_check`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `claim_fixes_live`; calls `claim_fixes_live`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `load_placement_state`, `placement_active`; calls `load_placement_state`, `placement_active`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_lp_claim_fixes_rereview.py](../../../../../../tests/test_lp_claim_fixes_rereview.py) — direct import
  - `test_f9_a_miss_the_diagnosis_timeout_decides_carries_its_line_reopened_after_the_deadline`
- [tests/test_lp_claim_fixes_review.py](../../../../../../tests/test_lp_claim_fixes_review.py) — direct import
  - `test_f6_off_no_claim_line`
  - `test_f6_the_resolving_review_carries_one_quiet_claim_line_and_no_other_does`

## Modification guidance

- Make changes here when the responsibility remains claim check within learnloop.placement; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/placement/claim_check.py](../../../../../../src/learnloop/placement/claim_check.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
