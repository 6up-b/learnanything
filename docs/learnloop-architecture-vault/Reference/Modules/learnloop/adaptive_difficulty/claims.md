---
title: "learnloop.adaptive_difficulty.claims"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/claims.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/claims.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.adaptive_difficulty.claims module"
  - "src/learnloop/adaptive_difficulty/claims.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.claims`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.claims` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: One durable, fenced claim per piece of AD paid work (Codex review F5, F6).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/claims.py](../../../../../../src/learnloop/adaptive_difficulty/claims.py) |
| Source lines | 231 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class DispatchStopped(AIInterrupted)` ([source](../../../../../../src/learnloop/adaptive_difficulty/claims.py), line 53) — AD's start receipt could not be written: the request is never dispatched.
- `class ReceiptWriteFailed(DispatchStopped)` ([source](../../../../../../src/learnloop/adaptive_difficulty/claims.py), line 66) — A storage error while writing AD's start receipt (``failed``).
- `class ReceiptLeaseLost(DispatchStopped, LeaseLost)` ([source](../../../../../../src/learnloop/adaptive_difficulty/claims.py), line 70) — The claim's lease (or the vault) was lost at the start receipt (``stale``: the claim's new owner does the work).
- `audit_key(content_hash: str) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/claims.py), line 76)
- `item_forecast_key(content_hash: str) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/claims.py), line 80)
- `presentation_key(presentation_id: str) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/claims.py), line 84)
- `history_key(presentation_id: str) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/claims.py), line 88) — Router objective RO2: ``llm_history_v1``'s claim on one presentation (apart from ``llm_v3``'s).
- `class FencedRepository` ([source](../../../../../../src/learnloop/adaptive_difficulty/claims.py), line 94) — The repository a claimed unit of work writes through (see the module docstring).
  - `__init__(self, repository: Any, claim: Any) -> None` (line 97; internal)
  - `__getattr__(self, name: str) -> Any` (line 101; internal)
  - `base(self) -> Any` (line 105; public)
  - `atomic(self) -> Iterator[None]` (line 109; public)
  - `connection(self) -> Any` (line 113; public)
  - `record_model_event(self, action: str, event: dict[str, Any], *, owner_kind: str, owner_id: str) -> None` (line 116; public)
  - `_start(self, event: dict[str, Any], *, owner_kind: str, owner_id: str) -> None` (line 123; internal) — AD's start receipt, which fails closed (fix round 8).
  - `_close_refused(self, event: dict[str, Any], refusal: BaseException, *, owner_kind: str, owner_id: str) -> None` (line 162; internal)
  - `save_model_checkpoint(self, cache_key: str, *, purpose: str, result: dict[str, Any], usage: dict[str, Any] | None=None) -> None` (line 181; public)
  - `discard_model_checkpoint(self, cache_key: str, *, result: Any=None) -> None` (line 191; public)
- `class Worker` ([source](../../../../../../src/learnloop/adaptive_difficulty/claims.py), line 201) — A held claim: :attr:`repository` writes fenced; :meth:`live` before each request.
  - `__init__(self, repository: Any, claim: Any) -> None` (line 204; internal)
  - `live(self) -> bool` (line 209; public)
  - `require_live(self) -> None` (line 212; public)
- `claimed(repository: Any, key: str, *, fence: Any=None) -> Iterator[Worker | None]` ([source](../../../../../../src/learnloop/adaptive_difficulty/claims.py), line 218) — Hold ``key``'s durable claim for the block (no waiting: None when held elsewhere).

### Module constants

- `LOG` ([src/learnloop/adaptive_difficulty/claims.py](../../../../../../src/learnloop/adaptive_difficulty/claims.py), line 43)
- `CLAIM_TASK` ([src/learnloop/adaptive_difficulty/claims.py](../../../../../../src/learnloop/adaptive_difficulty/claims.py), line 46)
- `PRODUCER` ([src/learnloop/adaptive_difficulty/claims.py](../../../../../../src/learnloop/adaptive_difficulty/claims.py), line 47)

### Explicit exports

`__all__` declares:

- `CLAIM_TASK`
- `DispatchStopped`
- `FencedRepository`
- `LeaseLost`
- `PRODUCER`
- `ReceiptLeaseLost`
- `ReceiptWriteFailed`
- `Worker`
- `audit_key`
- `claimed`
- `history_key`
- `item_forecast_key`
- `presentation_key`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `LeaseLost`, `ReceiptWriteFailed`, `audit_key`, `claimed`; statically calls `audit_key`, `claimed`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_audit|learnloop.adaptive_difficulty.history_audit]] — imports `LeaseLost`, `claimed`, `history_key`; statically calls `claimed`, `history_key`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]] — imports `LeaseLost`, `ReceiptWriteFailed`, `claimed`, `history_key`; statically calls `claimed`, `history_key`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `LeaseLost`, `ReceiptWriteFailed`, `claimed`, `item_forecast_key`, `presentation_key`; statically calls `claimed`, `item_forecast_key`, `presentation_key`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] — imports `LeaseLost`, `ReceiptWriteFailed`, `claimed`; statically calls `claimed`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/logs|learnloop.adaptive_difficulty.logs]] — imports `warn_failure`; calls `warn_failure`
- [[Reference/Modules/learnloop/adaptive_difficulty/sending|learnloop.adaptive_difficulty.sending]] — imports `ProtectedContent`, `before_dispatch`; calls `before_dispatch`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/stores/model_calls|learnloop.db.stores.model_calls]] — imports `delete_checkpoint`, `insert_checkpoint`; calls `delete_checkpoint`, `insert_checkpoint`
- [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] — imports `module`; calls `_alive`, `_claimed`, `_fenced_txn`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `logging`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]], [[Reference/Modules/learnloop/adaptive_difficulty/history_audit|learnloop.adaptive_difficulty.history_audit]], [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]], [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]], [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad1_codex_review_fixes.py](../../../../../../tests/test_ad1_codex_review_fixes.py) — direct import
  - `test_a_claim_held_by_another_process_is_skipped`
- [tests/test_ad1_fix_round6.py](../../../../../../tests/test_ad1_fix_round6.py) — direct import
  - `test_the_last_confirmation_runs_after_the_outer_gate_and_the_receipt`
- [tests/test_ad1_fix_round7.py](../../../../../../tests/test_ad1_fix_round7.py) — direct import
  - `test_a_refusal_at_the_deciders_start_receipt_stops_the_request`

## Modification guidance

- Make changes here when the responsibility remains claims within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/claims.py](../../../../../../src/learnloop/adaptive_difficulty/claims.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
