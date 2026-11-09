---
title: "learnloop_sidecar.handlers.adaptive_difficulty"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/adaptive_difficulty.py"
source_paths:
  - "src/learnloop_sidecar/handlers/adaptive_difficulty.py"
source_commit: "38ccfa65f8d3889cdb161cd5db0cea3a5d0582f0"
source_commit_timestamp: "2026-11-09T06:12:48-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.handlers.adaptive_difficulty module"
  - "src/learnloop_sidecar/handlers/adaptive_difficulty.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.adaptive_difficulty`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.adaptive_difficulty` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Adaptive difficulty AD2+AD3's desktop RPCs (spec_adaptive_difficulty_v1 §5.12, §9.5, §12).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/adaptive_difficulty.py](../../../../../../src/learnloop_sidecar/handlers/adaptive_difficulty.py) |
| Source lines | 204 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `38ccfa65f8d3889cdb161cd5db0cea3a5d0582f0` |
| Commit timestamp | `2026-11-09T06:12:48-05:00` |

## Public API

- `class ReaderDoseOfferInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/adaptive_difficulty.py), line 34)
- `reader_dose_offer(ctx: SidecarContext, params: ReaderDoseOfferInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/adaptive_difficulty.py), line 48) — The dose arm's draw at a section boundary (§5.12): ``offer`` is the extra to show, or null.
- `class ReaderDoseOfferEventInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/adaptive_difficulty.py), line 116)
- `reader_dose_offer_event(ctx: SidecarContext, params: ReaderDoseOfferEventInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/adaptive_difficulty.py), line 122) — Record that the offer was delivered, not delivered, taken or dismissed.
- `class AdaptiveDifficultyReadinessInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/adaptive_difficulty.py), line 149)
- `adaptive_difficulty_readiness(ctx: SidecarContext, params: AdaptiveDifficultyReadinessInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/adaptive_difficulty.py), line 154) — An LO's readiness lines (predictions; "untested" where it has no answer of its own).
- `class AdaptiveDifficultyWhyItemInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/adaptive_difficulty.py), line 174)
- `adaptive_difficulty_why_item(ctx: SidecarContext, params: AdaptiveDifficultyWhyItemInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/adaptive_difficulty.py), line 179) — "Why this item" (§12): ``{"why": null}`` when no AD draw chose the served item.

### Module constants

- `AD23_RPCS` ([src/learnloop_sidecar/handlers/adaptive_difficulty.py](../../../../../../src/learnloop_sidecar/handlers/adaptive_difficulty.py), line 30)

### Explicit exports

`__all__` declares:

- `AD23_RPCS`

## Internal implementation anchors

- `_dose_offer(vault: Any, repository: Any, params: ReaderDoseOfferInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/adaptive_difficulty.py), line 67)
- `_offered_question(repository: Any, view: Any, question_id: Any) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/adaptive_difficulty.py), line 94)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/dose|learnloop.adaptive_difficulty.dose]] — imports `Boundary`, `UPTAKE`, `decide`, `record_uptake`; calls `Boundary`, `decide`, `record_uptake`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `is_denial`, `optional_operation`; calls `is_denial`, `optional_operation`
- [[Reference/Modules/learnloop/adaptive_difficulty/readiness|learnloop.adaptive_difficulty.readiness]] — imports `NOT_PREDICTED`, `READINESS_VERSION`, `lo_readiness`; calls `lo_readiness`
- [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]] — imports `why_for_presentation`; calls `why_for_presentation`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/phone_reader|learnloop_sidecar.phone_reader]] — imports `once_per_job`; calls `once_per_job`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad_guard.py](../../../../../../tests/test_ad_guard.py) — direct import
  - `test_a_denied_dose_response_rolls_the_draw_back`
- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/adaptive_difficulty.py](../../../../../../src/learnloop_sidecar/handlers/adaptive_difficulty.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
